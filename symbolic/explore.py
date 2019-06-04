# Copyright: see copyright.txt

from collections import deque
import logging
import os, sys, pdb, traceback
import codecs, utils, functools, copy, re, json
from termcolor import colored

from .z3_wrap import Z3Wrapper
from .path_to_constraint import PathToConstraint
from .invocation import FunctionInvocation
from .symbolic_types import symbolic_type, SymbolicType, getSymbolic, SymbolicDict
from .predicate import Predicate
from .constraint import Constraint

from bdb import BdbQuit


log = logging.getLogger("se.conc")

class ExplorationEngine:
	def __init__(self, funcinv, filename, configPath, solver="z3"):
		self.invocation = funcinv
		# the input to the function
		self.symbolic_inputs = {}  # string -> SymbolicType
		# initialize	
		for n in funcinv.getNames():
			self.symbolic_inputs[n] = funcinv.createArgumentValue(n)

		self._fileName = filename

		self.constraints_to_solve = deque([])
		self.num_processed_constraints = 0

		self.path = PathToConstraint(lambda c : self.addConstraint(c))
		# link up SymbolicObject to PathToConstraint in order to intercept control-flow
		symbolic_type.SymbolicObject.SI = self.path
		if symbolic_type.SymbolicObject.SI == None:
			print("symbolic_type.SymbolicObject.SI is none")

		if solver == "z3":
			self.solver = Z3Wrapper()
		elif solver == "cvc":
			from .cvc_wrap import CVCWrapper
			self.solver = CVCWrapper()
		else:
			raise Exception("Unknown solver %s" % solver)

		# outputs
		self.generated_inputs = []
		self.execution_return_values = []

		self.numofExecution = 0
		self.configPath = configPath
		self.exploreDone = False
		if configPath and os.path.isfile(configPath):
			self.hookFuncs(configPath)

	def hookFuncs(self, configPath):
		with open(configPath) as f:
			configJson = json.load(f)
			for item in configJson['hookedFunc']:
				module = item['module']
				className = item['class']
				api = item['api']
				location = item['location']
				symbolicvar = item['symbolicvar']
				replacedvar = item['replacedvar']
				if (len(symbolicvar) != len(replacedvar)) or (location[0] != 'args' and location[0] != 'kwargs' and location[0] != 'returnVal'):
					print('Incorrect configuration parameters!')
				if item['class'] == '':
					code  = "import %s\n" % module
				else:
					code  = "from %s import %s\n" % (module, className)

				code += "%s = self.processhookFuncs(%s, %s, %s, %s)" % (api, api, location, symbolicvar,replacedvar)
				exec(code)
			return
    	
		#import hashlib
		#hashlib.sha256 = self._hookComplexFuncs(hashlib.sha256, self.gethookPaths, 'hexdigest', 'in2')
		#return

	def processhookFuncs(self, function, location, symbolicvar, replacedvar):
		@functools.wraps(function)
		def run(*args, **kwargs):
			returnVal = function(*args, **kwargs)
			if location[0] == 'args':
				target = tuple(args)[location[1]]
			elif location[0] == 'kwargs':
				target = kwargs[location[1]]
			elif location[0] == 'returnVal':
				if isinstance(returnVal, tuple):
					target = copy.deepcopy(returnVal[location[1]])
				else:
					target = copy.deepcopy(returnVal)

			for index in range(len(replacedvar)):
				try:
					if isinstance(target, dict):
						target[replacedvar[index]] = dict(self.symbolic_inputs)[symbolicvar[index]] 
					elif replacedvar[index] in dir(target):
						setattr(target, replacedvar[index], dict(self.symbolic_inputs)[symbolicvar[index]])
					else:
						print('Replaced parameter ' + replacedvar[index] + ' not found!')
				except:
					print('Replaced parameter ' + replacedvar[index] + ' not found!')
			
			if location[0] == 'returnVal':
				return target
			else:
				return returnVal
		return run

	def hookComplexFuncs(self, configPath):
		with open(configPath) as f:
			configJson = json.load(f)
			try:
				if configJson['complexfunc']['module'] == '' or configJson['complexfunc']['api'] == '' or configJson['complexfunc']['symbolicvar'] == '':
					return
			except:
				return
			code  = "import %s\n" % configJson['complexfunc']['module']
			code += "%s = self._hookComplexFuncs(%s, self.gethookPaths, '%s', '%s', '%s')" % (configJson['complexfunc']['api'], configJson['complexfunc']['api'], configJson['complexfunc']['api'], configJson['complexfunc']['property'], configJson['complexfunc']['symbolicvar'])
			exec(code)
			return

	def _hookComplexFuncs(self, function, prefixFunc, funcName, prop, inputVar):
		@functools.wraps(function)
		def run(*args, **kwargs):
			prefixFunc(function(*args, **kwargs), inputVar, prop, funcName)
			return function(*args, **kwargs)
		return run

	def gethookPaths(self, funcObj, inputVar, prop, func):
		if self.exploreDone:
			return
		inputVals = dict(self.symbolic_inputs)
		if inputVar not in inputVals:
			return

		if prop != None:
			prop_to_call = getattr(funcObj, prop)
			returnVal = prop_to_call()
		else:
			returnVal = funcObj
		
		conrVal = inputVals[inputVar].getConcrValue()

		noConfig = False
		if not (self.configPath and os.path.isfile(self.configPath)):
			noConfig = True
		else:
			with open(self.configPath) as f:
				configJson = json.load(f)
				if 'complexfunc' in configJson and 'symbolicvarVal' in configJson['complexfunc'] and 'symbolicvar' in configJson['complexfunc']:
					if conrVal not in configJson['complexfunc']['symbolicvarVal']:
						return
				else:
					noConfig = True
		if noConfig:
			return

		
		st = getSymbolic(conrVal)
		tmpS = st(inputVar, conrVal, ['==', st(inputVar, conrVal), conrVal])
		
		p = Predicate(tmpS, True)
		c = self.path.current_constraint.findChild(p)
		if c == None:
			c = self.path.current_constraint.addChild(p)
		
		self.path.current_constraint = c

		st = getSymbolic('stringval')
		tmpS = st(inputVar+'_'+re.sub(r'[^A-Za-z0-9\-_]', '_', func), returnVal, ['==', st(inputVar+'_'+re.sub(r'[^A-Za-z0-9\-_]', '_', func), returnVal), returnVal])
		c = self.path.current_constraint.findChild(Predicate(tmpS, True))
		if c == None:
			c = self.path.current_constraint.addChild(Predicate(tmpS, True))
		self.path.current_constraint = c
		return

	def printInputsConstraintsToSolve(self):
		for constraint in self.constraints_to_solve:
			if constraint.processed == True:
				continue
			print("constraint is: ", constraint)
			print("the input of the constraint is: ", constraint.inputs)

	def addConstraint(self, constraint):
		#if it's dict, delete the path with leaf node as ==, key#key, key
		if constraint.getLength() > 1:
			asserts, query = constraint.getDirectAssertAndQuery()
			if len(query.getVars()) > 0:
				queryVarName = query.getVars()[0]
				asserts = asserts.getVarStr()
				if asserts == '(== '+queryVarName+'#'+queryVarName+', '+queryVarName+')' and \
					query.getVarStr() != '(== '+queryVarName+'#'+queryVarName+', '+queryVarName+')':
					delPath = None
					for constr in self.constraints_to_solve:
						tmpasserts, tmpquery = constr.getDirectAssertAndQuery()
						if tmpquery.getVarStr() == '(== '+queryVarName+'#'+queryVarName+', '+queryVarName+')':
							delPath = constr
							break
					if delPath:
						self.constraints_to_solve.remove(delPath)
					constraint.removeDirectPartent()

		self.constraints_to_solve.append(constraint)
		# make sure to remember the input that led to this constraint
		constraint.inputs = self._getInputs()
		return

	def explore(self, max_iterations=0):
		self.exploreDone = False
		
		if self.configPath and os.path.isfile(self.configPath):
			with open(self.configPath) as f:
				configJson = json.load(f)
				if 'complexfunc' in configJson and 'symbolicvarVal' in configJson['complexfunc'] and 'symbolicvar' in configJson['complexfunc']:
					oldVal = self.symbolic_inputs.copy()
					for symVal in configJson['complexfunc']['symbolicvarVal']:
						updateFlag = self._updateSymbolicParameter(configJson['complexfunc']['symbolicvar'], symVal)
						self._oneExecution()
		
					self.symbolic_inputs = oldVal
		self._oneExecution()

		iterations = 1
		#When user press c after choosing option 2
		if max_iterations == -1:
			if not (self.configPath and os.path.isfile(self.configPath)):
				self.configPath = os.path.join(os.path.dirname(self._fileName), 'config.json')
			if os.path.isfile(self.configPath):
				with open(self.configPath) as f:
					configJson = json.load(f)
					if 'modify_hist' in configJson and configJson['modify_hist'][-1]['opr'] == 'bp':
						with open(configJson['modify_hist'][-1]['path']) as f:
							codeCont = f.readlines()
						del codeCont[configJson['modify_hist'][-1]['line']-1]
						with open(configJson['modify_hist'][-1]['path'], 'w') as f:
							f.write(''.join(codeCont))
						del configJson['modify_hist'][-1]
						json.dump(configJson, open(self.configPath, 'w'))
			sys.exit(1)
		elif max_iterations != 0 and iterations >= max_iterations:
			log.debug("Maximum number of iterations reached, terminating")
			self.exploreDone = True
			return self.generated_inputs, self.execution_return_values, self.path

		while not self._isExplorationComplete():
			selected = self.constraints_to_solve.popleft()
			if selected.processed:
				continue
			
			self._setInputs(selected.inputs)

			log.info("Selected constraint %s" % selected)
			#Get parents and last predicts
			asserts, query = selected.getAssertsAndQuery()

			model = None
			model = self.check_dict(asserts,query)
			cvc_expr = ''
			
			try:
				if model == None and str(type(self.solver)).find('CVCWrapper') != -1:
					model, cvc_expr = self.solver.findCounterexample(asserts, query)
				elif model == None:
					model = self.solver.findCounterexample(asserts, query)
					cvc_expr = None
			except:
				print("unexpected error occured when finding counterexample")
				log.critical("unexpected error occured when finding counterexample")
				model = None
			
			if model == None:
				continue
			else:
				updateFlag = False
				for name in model.keys():
					updateFlag = self._updateSymbolicParameter(name,model[name])
					if not updateFlag:
						continue
				if not updateFlag:
					continue
			self._oneExecution(selected, cvc_expr)

			iterations += 1
			self.num_processed_constraints += 1

			if max_iterations != 0 and iterations >= max_iterations:
				log.info("Maximum number of iterations reached, terminating")
				break

		self.exploreDone = True
		return self.generated_inputs, self.execution_return_values, self.path

	def print_dict(self, v, name, prefix=''):
		if isinstance(v, dict):
			for k, v2 in v.items():
				p2 = "{}['{}']".format(prefix, k)
				if name == 'None':
					target = open('prefix.txt', 'w')
					target.write(p2)
					target.close()

					return 
				self.print_dict(v2, name, p2)
		elif isinstance(v, list):
			for i, v2 in enumerate(v):
				p2 = "{}[{}]".format(prefix, i)
		else:
			if str(name) in prefix:
				target = open('prefix.txt', 'w')
				target.write(prefix)
				target.close()
				return 
	
	def update_nested_dict(self, in_dict, key_list, value, key_to_insert= None):
		if len(key_list) == 1:
			if type(value) == str and value == 'dict_action pop':
				in_dict.pop(key_list[0])
			elif type(value) == str and value.find('dict_action push')==0:
				if key_to_insert == 'expires_in':
					in_dict[key_to_insert] = 3600
				if key_to_insert == 'expires_at':
					in_dict[key_to_insert] = 3600
				else:
					in_dict[key_to_insert] = '3600'
			else:
				in_dict[key_list[0]] = value
			return 
		else:
			self.update_nested_dict(in_dict[key_list[0]], key_list[1:],value)

	def get_dict(self, expr):
		if isinstance(expr, dict):
			return expr
		elif isinstance(expr, list):
			for subexpr in expr:
				if not isinstance(subexpr, list) and not isinstance(subexpr, dict):
					continue
				return self.get_dict(subexpr)

	def check_dict(self, asserts, query):
		model = dict()
		#Boolean variable is None
		if query.symtype.expr == None:
			return None
		if len(query.symtype.expr) != 3:
			print('do not consider the case where len(query.symbolic_type.expr)!=3 '+ query.symtype.toString())
			raise ValueError
		else:
			op = query.symtype.expr[0]
			if op.find('dict') == 0:
				if op == 'dict_in':
					#negate query
					if query.result == True:
						model[query.symtype.expr[2]] = 'dict_action pop'
					else:
						dict_to_update = self.get_dict(query.symtype.expr[1])
						try:
							first_key = list(dict_to_update.keys())[0]
						except IndexError:
							first_key = None
						model[query.symtype.expr[2]] ='dict_action push siblingkey '+ str(first_key)
					return model
			else:
				return None

	# ---- private ---- #
	def _iter_dicts(self, iter_dict, name, val, keypath=""):
		# Another way is to use self.symbolic_inputs[name].expr to understand the operations on the dict
		for key, value in iter_dict.items():
			if isinstance(value, dict):
				return self._iter_dicts(value, name, val, keypath+"_."+str(key))
			elif key == name:
					st = getSymbolic(val)
					val = st(name,val)
					iter_dict[key] = val
					keypath = keypath +"_."+str(key)
					return keypath
					break
			else:
				continue

	def _updateSymbolicParameter(self, name, val):
		try:
			self.symbolic_inputs[name] = self.invocation.createArgumentValue(name,val)
			return True
		except KeyError:
			prefix = ''
			if type(val) == str and val.find('dict_action push') == 0:
				# Name is not in the dict. We use its siblingkey instead.
				siblingkey = val.split(' ')[-1]
				if siblingkey == 'None':
					self.print_dict(self.symbolic_inputs, 'None' , prefix)
				else:
					self.print_dict(self.symbolic_inputs, siblingkey, prefix)
			else:
				self.print_dict(self.symbolic_inputs, name, prefix)

			try:
				with open ("prefix.txt", "r") as myfile:
					prefix=myfile.readline()
				import os
				os.remove("prefix.txt")
			except FileNotFoundError:
				print("cannot find %s and %s", str(name), str(val))
				return False

			prefix = prefix.split(']')
			ordered_key_list = list()
			for item in prefix:
				if len(item) > 0:
					ordered_key_list.append(item.strip('[').strip('\''))

			import copy
			tmp =self.symbolic_inputs[ordered_key_list[0]].getConcrValue2()
			tmp_symbolic_inputs = copy.deepcopy(tmp)
			try:
				self.update_nested_dict(tmp_symbolic_inputs, ordered_key_list[1:], val, name)
			except IndexError:
				# empty dict
				self.update_nested_dict(tmp_symbolic_inputs, ordered_key_list[0:], val, name)

			name = ordered_key_list[0]
			val = tmp_symbolic_inputs

			if isinstance(self.symbolic_inputs[name], dict):
				self.symbolic_inputs[name].SymbolicValue()

			self.symbolic_inputs[name] = self.invocation.createArgumentValue(name,val)
			return True

	def _getInputs(self):
		return self.symbolic_inputs.copy()

	def _setInputs(self,d):
		self.symbolic_inputs = d

	def _isExplorationComplete(self):
		num_constr = len(self.constraints_to_solve)
		if num_constr == 0:
			log.info("Exploration complete")
			return True
		else:
			log.info("%d constraints yet to solve (total: %d, already solved: %d)" % (num_constr, self.num_processed_constraints + num_constr, self.num_processed_constraints))
			return False

	def _getConcrValue(self,v):
		if isinstance(v,SymbolicType):
			return v.getConcrValue()
		else:
			return v

	def _recordInputs(self):
		args = self.symbolic_inputs
		inputs = [ (k,self._getConcrValue(args[k])) for k in args ]
		self.generated_inputs.append(inputs)
		if self.numofExecution == 1:
			print("Initial inputs to the program are:")
			print(inputs)
		else:
			print("Inputs to the program are:")
			print(inputs)
		
	def _oneExecution(self, expected_path=None, cvc_expr = ""):
		self.numofExecution += 1
		self._recordInputs()
		
		self.path.reset(expected_path)

		try:
			ret = self.invocation.callFunction(self.symbolic_inputs)
		except BdbQuit as e:
			#When user press q after choosing option 2
			if not (self.configPath and os.path.isfile(self.configPath)):
				self.configPath = os.path.join(os.path.dirname(self._fileName), 'config.json')
			if os.path.isfile(self.configPath):
				with open(self.configPath) as f:
					configJson = json.load(f)
					if 'modify_hist' in configJson and configJson['modify_hist'][-1]['opr'] == 'bp':
						with open(configJson['modify_hist'][-1]['path']) as f:
							codeCont = f.readlines()
						del codeCont[configJson['modify_hist'][-1]['line']-1]
						with open(configJson['modify_hist'][-1]['path'], 'w') as f:
							f.write(''.join(codeCont))
						del configJson['modify_hist'][-1]
						json.dump(configJson, open(self.configPath, 'w'))
			sys.exit(1)
		except Exception as e:
			trackTrace = []
			for frame in traceback.extract_tb(sys.exc_info()[2]):
				codefname,codelineno,codefn,codemtext = frame
				trackTrace.append(codefname+'['+str(codelineno)+']: Function '+codefn+' '+codemtext)
			print(colored('Exception raised at the following localtion \n%s' % trackTrace[-1], 'red'))
			
			userChoice = self._askForChoice(trackTrace)

			if userChoice == '1':
				if not (self.configPath and os.path.isfile(self.configPath)):
					self.configPath = os.path.join(os.path.dirname(self._fileName), 'config.json')
				if not os.path.isfile(self.configPath):
					configJson = {}
				else:
					with open(self.configPath) as f:
						configJson = json.load(f)

				if 'modify_hist' not in configJson:
					configJson['modify_hist'] = []
				#Start changing the code
				with open(codefname) as f:
					codeCont = f.readlines()
				
				targetLine = re.split(r'([^\s])', codeCont[codelineno-1], maxsplit=1)
				codeCont[codelineno-1] = targetLine[0]+'#'+targetLine[1]+''.join(targetLine[2:])
				codeCont.insert(codelineno, targetLine[0]+'pass\n')
				configJson['modify_hist'].append({'path':codefname, 'line':codelineno, 'opr':'modify', 'orig':''.join(targetLine), 'new':codeCont[codelineno-1]})
				configJson['modify_hist'].append({'path':codefname, 'line':codelineno+1, 'opr':'add', 'orig':'', 'new':codeCont[codelineno]})
				print(colored('The following modification has been deployed:\nIn File %s \nChange line[%d] %s to %s\nIn File %s \nAdd line[%d] %s' % (codefname, codelineno, ''.join(targetLine), codeCont[codelineno-1], codefname, codelineno+1, codeCont[codelineno])))
				json.dump(configJson, open(self.configPath, 'w'))
				with open(codefname, 'w') as f:
					f.write(''.join(codeCont))

				print('Restart testing ... ')
				os.execl(sys.executable, sys.executable, *sys.argv)
			elif userChoice == '2':
				if not (self.configPath and os.path.isfile(self.configPath)):
					self.configPath = os.path.join(os.path.dirname(self._fileName), 'config.json')
				if not os.path.isfile(self.configPath):
					configJson = {}
				else:
					with open(self.configPath) as f:
						configJson = json.load(f)

				if 'modify_hist' not in configJson:
					configJson['modify_hist'] = []

				with open(codefname) as f:
					codeCont = f.readlines()
				loopline = codelineno
				childIndent = re.split(r'([^\s])', codeCont[loopline-1], maxsplit=1)[0]
				#get parent indent and insert a breakpoint
				loopline -= 1
				parentLine = None
				while loopline > 0:
					parentIndent = re.split(r'([^\s])', codeCont[loopline-1], maxsplit=1)[0]
					if len(parentIndent) < len(childIndent):
						parentLine = loopline
						break
					loopline -= 1
				if parentLine == None:
					print(colored('Can not locate its parent block', 'red'))
					return
				#Insert a breakpoint above its parent
				codeCont.insert(parentLine-1, parentIndent+'import pdb; pdb.set_trace()\n')
				with open(codefname, 'w') as f:
					f.write(''.join(codeCont))

				configJson['modify_hist'].append({'path':codefname, 'line':parentLine, 'opr':'bp', 'orig':'', 'new':parentIndent+'import pdb; pdb.set_trace()\n'})
				json.dump(configJson, open(self.configPath, 'w'))
				if '-m' not in sys.argv:
					sys.argv.append('-m')
					sys.argv.append('-1')
				else:
					sys.argv[sys.argv.index('-m')+1] = '-1'
				os.execl(sys.executable, sys.executable, *sys.argv)
			elif userChoice == '4':
				ret = None		
			elif userChoice == '5':
				sys.exit(0)
				return

		print('Function return %s \n************************************************************' % ret)
		self.execution_return_values.append(ret)
		if self.path.current_constraint.returnResult == None:
			self.path.current_constraint.returnResult = ret


	def _askForChoice(self, callTrace):
		while True:
			userChoice = input('You have the following options: \n1: Suppress this exception for later execution and rerun the program; \n2: Run with normal input and show me the correct value; \n3: Show me the function call stack;\n4: Return None and continue the execution;\n5: Quit now and I will manually change the code;\nPlease choose number 1, 2, 3, 4 or 5: ')
			userChoice = userChoice.strip()
			if userChoice == '3':
				print(colored('\n'.join(callTrace), 'green'))
			elif userChoice in ['1', '2', '4', '5']:
				return userChoice
