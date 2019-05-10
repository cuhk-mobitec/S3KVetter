import logging
import os, re
import json, copy
from subprocess import Popen, PIPE
from termcolor import colored
from .symbolic_types import SymbolicType

log = logging.getLogger("se.conc")

class VerifyEngine:
	# Only support CVC4 to verify the predicate

	def __init__(self, expected_predicate_path, program_logic_path, config_json_path=None):
		self.fileName = os.path.basename(program_logic_path)[:-6]
		self.smtCode = None
		self.smt_op = ['=', '=>', '>', '<', '>=', '<=', 'and', 'or', 'not', 'xor', '+','-','*', '/', 'to_real' , 'div', 'mod', 'rem', 'ite', 'forall', 'exists', 'bvadd', 'bvsub', 'bvneg', 'bvmul', 'bvurem', 'bvsrem', 'bvsmod', 'bvsh1', 'bvlshr', 'bvashr', 'bvor', 'bvand', 'bvnot', 'bvnand', 'bvnor', 'bvxnor', 'str.len', 'str.indexof', 'strat', 'str.contains', 'str.prefixof', 'str.suffixof', 'str.replace', 'str.to.int', 'int.to.str' ]
		if expected_predicate_path and os.path.isfile(expected_predicate_path):
			with open (expected_predicate_path, "r") as expectedFile:
				self.expected_predicate = expectedFile.readlines() 
		else:
			self.expected_predicate = None

		if program_logic_path and os.path.isfile(program_logic_path):
			with open (program_logic_path, "r") as ProgramLogicFile:
				self.program_logic = ProgramLogicFile.readlines() 
		else:
			self.program_logic = None

		if config_json_path and os.path.isfile(config_json_path):
			self.config_json = json.load(open(config_json_path, "r"))
		else:
			self.config_json = None

		self.variables = dict()

	def MapTypeToSMT(self, value):
		# treat it as zero
		if isinstance(value, SymbolicType):
			value = value.val

		if value == None:
			print(colored("be carefull that value is None when mapping type to SMT type", 'yellow'))
			return "String"

		if isinstance(value, int):
			return "Int"
		if isinstance(value, str):
			return "String"
		if isinstance(value, bool):
			return "Bool"
		if isinstance(value, float):
			# In fact, Real in CVC4 is infinitely precise. 
			# Strictly speaking, float does not equal to Real
			return "Real"
		if isinstance(value, dict):
			flatDict = dict()
			TypeList = list()
			self.flatNestDict(value, flatDict)
			for key, vvalue in flatDict.items():
				TypeList.append((key, self.MapTypeToSMT(vvalue)))
			return TypeList
		if isinstance(value, list):
			raise TypeError('SMT-Lib2 does not support list type')
		if isinstance(value, bytes):
			raise TypeError('SMT-Lib2 does not support bytes type')
		else:
			print(colored("be carefull that value is unknown type when mapping type to SMT type", 'red'))
			print(type(value))
			return "String"
 
	def getValue(self):
		# unsat can only be called if check-sat returns sat or unknown. For unsat, it will report error and exit
		# SMT-Lib2 currently does not support dynamically call get-value.
		# One tradeoff is to use cvc4's option --dump-models
		smt_code = "(get-value ("
		for variable in self.variables.keys():
			smt_code += str(variable)+" "
		smt_code += "))\n"
		return smt_code

	def extractVarPredicate(self, orgexpr, varList, inputs, returnVal):
		expr = copy.deepcopy(orgexpr)
		out_expr = expr
		if isinstance(expr, str):
			expr = expr.rstrip('\n')
			exprWordList = expr.split()
			for wordID in range(len(exprWordList)):
				word = exprWordList[wordID]
				word = word.lstrip('(').rstrip(')')
				if word in self.smt_op or re.match(r'^".*"$', word):
					continue
				#Convert Variable to Value
				elif word == 'None':
					exprWordList[wordID] = exprWordList[wordID].replace(word, '"None"')
				elif re.match(r'^\[.*\]$', word):
					key = word.rstrip(']').lstrip('[')
					varList.add(key)
					if re.match(r'^returnVal\..*$', key):
						flatDict = dict()
						self.flatNestDict(returnVal, flatDict)
						key = key.split('returnVal.')[-1]
						if key in flatDict:
							exprWordList[wordID] = '"'+str(flatDict[key])+'"'
					else:
						for variable in inputs:
							if variable[0] == key:
								exprWordList[wordID] = '"'+str(variable[1])+'"'
								break
				else:
					try:
						int_word = int(word)
						if int_word < 0:
							# this is a negative constant
							exprWordList[wordID] = "(- " + word[1:]+")"
					except ValueError:
						# this is not an integer. Instead it should be a variable name
						# We assume the expected predicate can contain int or str
						varList.add(word)
			expr = ' '.join(exprWordList)
			return expr

		else:
			print("unexpected format")
			return 

	def constructSmtCode(self, one_input, returnVal, raw_expected_predicate):
		expected_predicate = copy.deepcopy(raw_expected_predicate)
		# inputs helps to identify the type of input 
		#so that we can declare constant accordingly		
		smt_code = "(set-option :print-success false)\n"
		smt_code += "(set-option :produce-models true)\n"
		smt_code += "(set-option :produce-assertions true)\n"
		smt_code += "(set-logic ALL_SUPPORTED)\n"

		#Init variable pool
		for var in self.variables:
			self.variables[var] = {'type':'String', 'value':'None'}

		for variable in one_input:
			#variable is a tuple in the form of (variableName, Value)
			variableType = self.MapTypeToSMT(variable[1])
			if isinstance(variableType, list):
				flatDict = dict()
				if isinstance(variable[1], SymbolicType):
					self.flatNestDict(variable[1].val, flatDict)
				else:
					self.flatNestDict(variable[1], flatDict)
				# The variable type should be flattened
				for innerVariableType in variableType:
					tmpVal = flatDict[innerVariableType[0]]
					self.variables[innerVariableType[0]] = {'type':innerVariableType[1], 'value':tmpVal}
			else:
				if isinstance(variable[1], SymbolicType):
					tmpVal = tmpVal.val
				else:
					tmpVal = variable[1]
				self.variables[variable[0]] = {'type':variableType, 'value':tmpVal}
	
		#Read from user input
		if self.config_json:
			for smtStr in self.config_json['smt']['declare']:
				smt_code += smtStr+"\n"

		#declare returnVals
		#It is normal that returnVal is a complicated data structrue, e.g., dict.
		#In this case, we can only reason about the subtype.
		#Here, returnVals also can be nested data types
		if returnVal == None:
			returnVal = 'None'
		elif isinstance(returnVal, dict):
			for key in returnVal:
				if returnVal[key] == None:
					returnVal[key] = 'None'
		returnType = self.MapTypeToSMT(returnVal)
		if isinstance(returnType, list):
			for innerType in returnType:
				if isinstance(returnVal[innerType[0]], SymbolicType):
					tmpVal = returnVal[innerType[0]].val
				else:
					tmpVal = returnVal[innerType[0]]
				self.variables["returnVal."+str(innerType[0])] = {'type': innerType[1], 'value':tmpVal}
		else:
			tmpVal = returnVal
			if isinstance(tmpVal, SymbolicType):
				tmpVal = tmpVal.val
			self.variables["returnVal"] = {'type': returnType, 'value':tmpVal}
		
		for var in self.variables:
			smt_code += "(declare-const "+var+" "+ str(self.variables[var]['type'])+")\n"

		# or is to concate every possible path in the program
		smt_code += "(assert (and "
		#Add input value
		#for var in self.variables:
			#if 'returnVal.' not in var and 'returnVal' not in var:
		#	if isinstance(self.variables[var]['value'], str):
		#		smt_code += '(= '+var+' "'+str(self.variables[var]['value'])+'")' + ' '
		#	else:
		#		smt_code += '(= '+var+' '+str(self.variables[var]['value'])+')' + ' '

		smt_code += " (or "
		for program_logic in self.program_logic:
			# we need to carefully process the first predicate (i.e., None)
			# One solution is to use the concret value to represent the predicate
			# Make the changes in the explore.py file.
			varSet = set()
			program_logic = self.extractVarPredicate(program_logic, varSet, one_input, returnVal)
			smt_code += program_logic.rstrip('\n') + ' '

		smt_code += ") ))\n"

		varSet = set()
		expected_predicate = self.extractVarPredicate(expected_predicate, varSet, one_input, returnVal)

		# If the variable is not defined in the inputs, we do not query smt sovler, since the latter always outputs error.
		if not varSet.issubset(self.variables):
			output = ""
			for s in varSet.difference(self.variables):
				output+=str(s)
			print(colored("variable in expected precidate are not defined in the inputs: "+output, 'red'))
			self.smtCode = None
			return

		expected_predicate = expected_predicate.rstrip('\n')
		smt_code += "(push 1)\n"
		expected_predicate = '(not ' + expected_predicate +')'
		smt_code += "(assert " + expected_predicate + ")\n"
		smt_code += "(check-sat)\n"
		smt_code += "(pop 1)\n"

		smt_code += "(exit) "

		self.smtCode = smt_code
		return

	@staticmethod
	def flatNestDict(nestedDict, flatDict):
		stack = list(nestedDict.items())
		while stack:
			k, v = stack.pop()
			if isinstance(v, dict):
				# Note v can also be SymbolicDict
				stack.extend(dict(v).items())
			else:
				flatDict[k] = v

	def filterInput(self, inputs):
		# Before constructing the smt formula, we first check whether the preconditons can be preprocessed here.

		#Read preconditions if has
		preconditions = list()
		for expected_predicate in self.expected_predicate:
			if expected_predicate.find('@precondition:')==0:
				preconditions.append(expected_predicate[len("@precondition:"):].rstrip('\n'))
		if len(preconditions) == 0:
			return True

		#Convert inputs to dict
		dict_input = dict(inputs[0])
		flatDict = dict()
		self.flatNestDict(dict_input, flatDict)

		for precondition in preconditions:
			expr = precondition.rstrip(')').lstrip('(').split(' ')
			op = expr[0]
			arg_l = expr[1]
			arg_r = expr[2] if len(expr) > 2 else None
			arg_3 = expr[3] if len(expr) > 3 else None
	
			if op == "in":
				return arg_l in flatDict

	def filterOutput(self, output):
		models = output.decode().split('unsat')
		if len(models) ==0:
			return
		counterExample = []
		rawCounter = []
		for model in models:
			for modelline in model.split('\n'):
				modelline = modelline.strip()
				if modelline != '':
					rawCounter.append(modelline)
				if 'define-fun' in modelline:
					varName = modelline.split('define-fun ')[1].split(' (')[0]
					varType = modelline.split(') ')[1].split(' ')[0]
					varVal = modelline.split(' ')[-1].rstrip(')')
					counterExample.append(varName+'('+varType+'): '+varVal)
		
		with open("verify/"+self.fileName+'.result',"a+") as resultFile:
			if len(rawCounter) > 0:
				resultFile.write("found violations of security rules " + '\n'.join(rawCounter) + '\n')
			else:
				resultFile.write("Congratulations! The program under test is secure\n")
		return '\n'.join(counterExample)

	def mapExpectedNameToImplementation(self, inputs):
		# Map variable names in specification to that in source code 
		# This can be done via the comparison between inputs and specification file
		pass

	def executionVerify(self, inputs, returnVals):
		print("Verifying the program...")

		self.mapExpectedNameToImplementation(inputs)

		#check the preconditions
		#Only to check if input has certain variables
		if not self.filterInput(inputs):
			resultFile = open("verify/"+self.fileName+'.result',"w")
			resultFile.write("the precondition is not satified\n")
			resultFile.close()

			print(colored("the precondition is not satified", "red"))

		assert(len(inputs) == len(returnVals))
		allCounters = []
		for index in range(len(inputs)):
			#Loop through each defined condition
			for expected_predicate in self.expected_predicate:
				#filter out preconditions and comments
				if expected_predicate.find("@precondition:") == 0 or expected_predicate.find(";") == 0 or expected_predicate.strip() == '':
					continue

				self.constructSmtCode(inputs[index], returnVals[index], expected_predicate)
				if self.smtCode == None:
					continue
				with open ("verify/"+self.fileName+'.smt', "w") as smtFile:
					smtFile.write(self.smtCode)

				p = Popen(['cvc4', '--lang', 'smt', '--incremental', '--dump-models', "--strings-exp", "verify/"+self.fileName+'.smt'], stdout=PIPE, stderr=PIPE, stdin=PIPE)
				output = p.stdout.read()

				counterExm = self.filterOutput(output)
				if counterExm.strip() != '':
					print(colored('Following inputs violate security rule: '+expected_predicate, 'red'))
					print(colored(counterExm.strip()+'\n', 'red'))
					allCounters.append(counterExm.strip())
			break

		if len(allCounters) == 0:
			print(colored('Congratulations! The program under test is secure', 'green'))


