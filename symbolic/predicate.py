# Copyright - see copyright.txt
import codecs
import collections

class Predicate:
	"""Predicate is one specific ``if'' encountered during the program execution.
	   """
	def __init__(self, st, result):
		# symtype means the symbolic type (object). It stores an symbolic object. To get the path condition, you can print symtype.toString()
		self.symtype = st
		# boolean value, i.e., whether the path is true or false
		self.result = result

	def getVars(self):
		return self.symtype.getVars()

	def getVarStr(self):
		return self.symtype.toString()

	def __eq__(self, other):
		if isinstance(other, Predicate):
			if self.result != other.result:
				return False
			else:
				#Boolean variable is None
				if other.symtype.expr != None and other.symtype.expr[0].find('dict_in') == 0:
					return self.symtype.expr[2] == other.symtype.expr[2]
				else:
					return self.symtype.symbolicEq(other.symtype)
		else:
			return False

	def __hash__(self):
		return hash(self.symtype)

	def __str__(self):
		return self.symtype.toString() + " (%s)" % (self.result)

	def __repr__(self):
		return self.__str__()

	def negate(self):
		"""Negates the current predicate"""
		assert(self.result is not None)
		self.result = not self.result

	def isbom(self, expr):
		if isinstance(expr, list):
			for subexpr in expr:
				return self.isbom(subexpr)
		elif isinstance(expr, str):
			if expr.startswith(codecs.BOM_UTF8.decode('utf-8')):
				return True