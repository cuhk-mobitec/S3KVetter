import logging

from symbolic.cvc_expr.integer import CVCInteger
from symbolic.cvc_expr.string import CVCString
from symbolic.symbolic_types import SymbolicInteger, SymbolicStr, SymbolicBytes
from symbolic.symbolic_types.symbolic_type import SymbolicObject
import utils

import codecs

log = logging.getLogger("se.cvc_expr.exprbuilder")


class ExprBuilder(object):
    def __init__(self, asserts, query, solver):
        self.solver = solver
        self.solver.guards = []
        self.em = self.solver.getExprManager()
        self.cvc_vars = {}
        self.query = self._toCVC(asserts, query)

    def _toCVC(self, asserts, query):
        smt_query = self._predToCVC(query)
        try:
            smt_query = smt_query.not_op()
        except:
            return None
        for p in asserts:
            smt_query &= self._predToCVC(p)
        for guard in self.solver.guards:
            smt_query &= guard
        return smt_query

    def _predToCVC(self, pred, env=None):
        sym_expr = self._astToCVCExpr(pred.symtype, env)
        if env is None:
            if not sym_expr.cvc_expr.getType().isBoolean():
                sym_expr = (sym_expr == CVCInteger.constant(0, self.solver)).not_op()
            if not pred.result:
                sym_expr = sym_expr.not_op()
        else:
            if not pred.result:
                sym_expr = sym_expr.not_op()
        return sym_expr


    def _getVariable(self, symbolic_var):
        name = symbolic_var.name
        if name in self.cvc_vars:
            return self.cvc_vars[name]
        variable = None
        if isinstance(symbolic_var, SymbolicInteger):
            variable = CVCInteger.variable(name, self.solver)
        elif isinstance(symbolic_var, SymbolicStr):
            variable = CVCString.variable(name, self.solver)
        elif isinstance(symbolic_var, SymbolicBytes):
            variable = CVCString.variable(name, self.solver)
        self.cvc_vars[name] = variable
        return variable

    def _wrapIf(self, expr, env):
        if env is None:
            return expr.ite(CVCInteger.constant(1, self.solver), CVCInteger.constant(0, self.solver))
        else:
            return expr
    #expr is the path condition. Normally, it is an symbolic object
    def _astToCVCExpr(self, expr, env=None):
        if isinstance(expr, list):
            op = expr[0]
            args = []
            for a in expr[1:]:
                if isinstance(a, dict):
                    args.append(a)
                else:
                    args.append(self._astToCVCExpr(a, env))
            cvc_l = args[0]
            cvc_r = args[1] if len(args) > 1 else None
            cvc_3 = args[2] if len(args) > 2 else None

            # arithmetical operations
            if op == "+":
                return cvc_l + cvc_r
            elif op == "-":
                return cvc_l - cvc_r
            elif op == "*":
                return cvc_l * cvc_r
            elif op == "//":
                return cvc_l / cvc_r
            elif op == "%":
                return cvc_l % cvc_r

            # bitwise
            elif op == "<<":
                return cvc_l << cvc_r
            elif op == ">>":
                return cvc_l >> cvc_r
            elif op == "^":
                return cvc_l ^ cvc_r
            elif op == "|":
                return cvc_l | cvc_l
            elif op == "&":
                return cvc_l & cvc_r

            # string
            elif op == "str.len":
                return cvc_l.len()
            elif op == "str.find":
                return cvc_l.find(cvc_r, cvc_3)
            elif op == "str.replace":
                return cvc_l.replace(cvc_r, cvc_3)
            elif op == "str.startswith":
                return self._wrapIf(cvc_l.startswith(cvc_r), env)

            # collection operators
            elif op == "getitem":
                return cvc_l[cvc_r]
            elif op == "slice":
                return cvc_l[cvc_r:cvc_3]
            # equality gets coerced to integer
            elif op == "==":
                if cvc_l is None or cvc_r is None:
                    # forces false condition no model contains None
                    return self._wrapIf(self._astToCVCExpr(0, env) !=
                                        self._astToCVCExpr(0, env), env)
                else:
                    return self._wrapIf((cvc_l == cvc_r), env)
            elif op == "!=":
                if cvc_l is None or cvc_r is None:
                    return self._wrapIf(self._astToCVCExpr(0, env) == self._astToCVCExpr(0, env), env)
                else:
                    return self._wrapIf((cvc_l != cvc_r), env)
            elif op == "<":
                return self._wrapIf((cvc_l < cvc_r), env)
            elif op == ">":
                return self._wrapIf((cvc_l > cvc_r), env)
            elif op == "<=":
                return self._wrapIf((cvc_l <= cvc_r), env)
            elif op == ">=":
                return self._wrapIf((cvc_l >= cvc_r), env)
            elif op == "in":
                return self._wrapIf((cvc_l.__contains__(cvc_r)), env)
            #Convert dict_in to str.contains
            elif op  == "dict_in":
                if isinstance(cvc_l, dict):
                    tmpvariable = CVCString.variable('"'+','.join(cvc_l.keys())+'"', self.solver)
                else:
                    tmpvariable = CVCString.variable(str(cvc_l), self.solver)
                cvc_r_str = str(cvc_r).strip('"')
                if isinstance(cvc_l, dict):
                    allKeys = list(cvc_l.keys())
                    if cvc_r_str in allKeys:
                        new_cvc_r_str = []
                        if allKeys.index(cvc_r_str) == 0:
                            new_cvc_r_str.append('')
                        else:
                            new_cvc_r_str.append(',')
                        new_cvc_r_str.append(cvc_r_str)
                        if allKeys.index(cvc_r_str) == len(allKeys)-1:
                            new_cvc_r_str.append('')
                        else:
                            new_cvc_r_str.append(',')
                        cvc_r_str = ''.join(new_cvc_r_str)
                        cvc_r = CVCString.variable('"'+cvc_r_str+'"', self.solver)
                        return self._wrapIf((tmpvariable.__contains__(cvc_r)), env)
                if str(tmpvariable) == '"code"':
                    import pdb;pdb.set_trace()
                return self._wrapIf((tmpvariable == cvc_r), env)
            elif op == "get":
                return cvc_l
            else:
                utils.crash("Unknown BinOp during conversion from ast to CVC (expressions): %s" % op)

        elif isinstance(expr, SymbolicObject):
            if expr.isVariable():
                if env is None:
                    variable = self._getVariable(expr)
                    return variable
                else:
                    return env[expr.name]
            if expr.expr == None and expr.val != None:
                return self._astToCVCExpr(expr.val.decode(), env)
            else:
                return self._astToCVCExpr(expr.expr, env)

        elif isinstance(expr, int) | isinstance(expr, str):
            if env is None:
                if isinstance(expr, int):
                    return CVCInteger.constant(int(expr), self.solver)
                elif isinstance(expr, str):
                    return CVCString.constant(str(expr), self.solver)
            else:
                return expr
        # it seems cvc4 does not support bytes, so let's convert it back to string.
        elif isinstance(expr, bytes):
            try:
                return expr.decode()
            except:
                print("uncaught error")
                return None

        elif expr is None:
            return None
        else:
            return None
            utils.crash("Unknown node during conversion from ast to CVC (expressions): %s" % expr)
    
