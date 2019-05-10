# Copyright: see copyright.txt

import logging
import pdb

from .predicate import Predicate
from .constraint import Constraint
from .verify import VerifyEngine
import hashlib



log = logging.getLogger("se.pathconstraint")

class PathToConstraint:
	def __init__(self, add):
		self.constraints = {}
		self.add = add
		self.root_constraint = Constraint(None, None)
		self.current_constraint = self.root_constraint
		self.expected_path = None
		
	def reset(self,expected):
		self.current_constraint = self.root_constraint
		if expected==None:
			self.expected_path = None
		else:
			self.expected_path = []
			tmp = expected
			while tmp.predicate is not None:
				self.expected_path.append(tmp.predicate)
				tmp = tmp.parent

	#Build up constraint
	def whichBranch(self, branch, symbolic_type):
		""" This function acts as instrumentation.
		Branch can be either True or False."""
		# self in fact is SymbolicObject.SI, a class variable.
		
		# add both possible predicate outcomes to constraint (tree)
		# the second time: (== out2#hello, hello) (True)

		#if isinstance(symbolic_type.expr, list):
		#For Boolean operator, symbolic_type.expr is None
		if symbolic_type.expr != None:
			for expr in symbolic_type.expr:
				if isinstance(expr, list):
					op = expr[0]
					if op.find('dict') == 0 and len(symbolic_type.expr) ==3:
						symbolic_type.expr = symbolic_type.expr[1]
						branch = symbolic_type.val
						break
					elif op.find('dict') == 0 and len(symbolic_type.expr) !=3:
						print("do not consider this case yet")
						raise ValueError
				else:
					continue
		# remove the outer layer since it is just a dumpy comparison so that we can enter this function 
		p = Predicate(symbolic_type, branch)
		p.negate()
		cneg = self.current_constraint.findChild(p) # check whether the other branch has been reached or not
		p.negate()
		c = self.current_constraint.findChild(p)

		if c is None:
			c = self.current_constraint.addChild(p)
			# we add the new constraint to the queue of the engine for later processing
			log.debug("New constraint: %s" % c)

			self.add(c)
			
		# check for path mismatch
		# IMPORTANT: note that we don't actually check the predicate is the
		# same one, just that the direction taken is the same
		if self.expected_path != None and self.expected_path != []:
			expected = self.expected_path.pop()
			# while not at the end of the path, we expect the same predicate result
			# at the end of the path, we expect a different predicate result
			done = self.expected_path == []
			if ( not done and expected.result != c.predicate.result or \
				done and expected.result == c.predicate.result ):
				print("Replay mismatch (done=",done,")")
				print(expected)
				print(c.predicate)

		if cneg is not None:
			# We've already processed both branches
			cneg.processed = True
			c.processed = True
			log.debug("Processed constraint: %s" % c)

		self.current_constraint = c

	def toDot(self):
		# print the thing into DOT format
		header = "digraph {\n"
		footer = "\n}\n"
		return header + self._toDot(self.root_constraint) + footer

	def _toDot(self,c):
		if (c.parent == None):
			label = "root"
		else:
			label = c.predicate.symtype.toString()
			if not c.predicate.result:
				label = "Not("+label+")"
		node = "C" + str(c.id) + " [ label=\"" + label + "\" ];\n"
		edges = [ "C" + str(c.id) + " -> " + "C" + str(child.id) + ";\n" for child in c.children if not child.hidden ]

		# The final exection path
		if len(c.children) == 0:
			try:
				label = "returnResult("+str(c.returnResult)+")"
				# use hash to generate a unique node id to act the same purpose of c.id
				# On the other hand, it will merge two nodes to one, if they share the same result.
				node_id = int(hashlib.sha256(str(c.returnResult).encode('utf-8')).hexdigest(), 16) % 10**8
				node = node + "C" + str(node_id) + " [ label=\"" + label + "\" ];\n"
				edges = [ "C" + str(c.id) + " -> " + "C" + str(node_id) + ";\n" ]
			except AttributeError as msg:
				print("handing output returnResult error: ", msg)

		return node + "".join(edges) + "".join([ self._toDot(child) for child in c.children if not child.hidden ])

	@staticmethod
	def balanceBracket(s):
		stack=[]
		bracket,close="(",")" 
		for i in s:
			if i in bracket:
				stack.append(i)
			if i in close:
				if len(stack)==0:
					raise TypeError("the bracket is not balanced", s)
				else:   
					stack.pop()
		if len(stack):
			return len(stack) * ")"
		else:
			return None

	def toSMTLib2(self, solver):
		# convert the path to SMT-lib2 format language
		smtLibExprs = self._toSMTLib2(self.root_constraint, solver).split('\n')
		
		BalancedSmtLibExprs = ""
		for smtLibExpr in smtLibExprs:
			addBrackets = self.balanceBracket(smtLibExpr)
			balanceBrackets = addBrackets  +"\n" if addBrackets != None else  "\n"
			smtLibExpr += balanceBrackets
			BalancedSmtLibExprs += smtLibExpr.lstrip(' ')
		return BalancedSmtLibExprs

	def _toSMTLib2(self, c, solver, pre = ""):
		smtLibExpr = pre
		if c.predicate != None:
			c.predicate.negate()
			predicateExpr = solver.findCVCExpr([], c.predicate)
			# we need to negate the result again. Otherwise, the path True and False would be reversed.
			c.predicate.negate()
			smtLibExpr +=  " (and "+ predicateExpr

		if len(c.children) == 0:
			try:
				if isinstance(c.returnResult, int):
					smtLibExpr += " (= returnVal " + str(c.returnResult) +")\n" 
				elif isinstance(c.returnResult, str):
					smtLibExpr += " (= returnVal " + "\"" + str(c.returnResult) + "\"" +")\n"
				elif isinstance(c.returnResult, bytes):
					print("do not fully support bytes type yet")
					smtLibExpr += " (= returnVal " + str(c.returnResult) +")\n" 
				elif isinstance(c.returnResult, bool):
					smtLibExpr += " (= returnVal " + str(c.returnResult) +")\n"
				elif isinstance(c.returnResult, dict):
					flatDict = dict()
					VerifyEngine.flatNestDict(c.returnResult, flatDict)
					for key,value in flatDict.items():
						smtLibExpr += " (= returnVal." + str(key) +" " 
						if isinstance(value, str):
							smtLibExpr += "\"" +value + "\""  +")"
						elif isinstance(value, int) or isinstance(value, bytes) or isinstance(value, bool):
							smtLibExpr += str(value) +")"
						else:
							smtLibExpr += "\"" + str(value) +"\")"
					smtLibExpr += "\n"
				else:
					smtLibExpr += " (= returnVal " + "\"" + str(c.returnResult) + "\"" +")\n" 
			except AttributeError as msg:
				print("handing output returnResult erroro: ", msg)

		return smtLibExpr + "".join([self._toSMTLib2(child, solver, smtLibExpr) for child in c.children if not child.hidden])


