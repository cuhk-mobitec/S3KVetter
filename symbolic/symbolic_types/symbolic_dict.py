import ast
import sys
from . symbolic_type import SymbolicObject

import inspect
import functools

#from .symbolic_int import SymbolicInteger
#from .symbolic_str import SymbolicStr
#from .symbolic_type import SymbolicType

# SymbolicDict: the key and values will both be SymbolicType for full generality

# keys of dictionary must be immutable
# values in dictionary may be mutable


class SymbolicDict(SymbolicObject,dict):
	def __new__(cls, name, *args, **kwargs):
		self = dict.__new__(cls,args,kwargs)
		return self

	def __init__(self, name, kwargs, expr = None):
		# since we only symbolize the elements in the dict, we need to remember the operation on the whole dict, e.g., get, set, etc. Currently, the self.expr by default should be None.
		# Use self.expr to keep track of this.
		SymbolicObject.__init__(self, name, expr)
		dict.__init__(self, kwargs)
		
		self.val = kwargs

		self = self.SymbolicValue()

		self = self.SymbolicKey()


	def unwrap(self):
		if self.isVariable():
			return (self.getConcrValue2(),self.getConcrValue2())
		else:
			return (self.getConcrValue2(),self.expr)


	def SymbolicKey(self, SI=None):
		from . __init__ import getSymbolic

		for key in self.keys():
			if isinstance(key, SymbolicObject) == False:
				st = getSymbolic(key)
				if (st == None):
					print("Error at argument " + key + " : no corresponding symbolic type found for type " + str(type(value)))
					raise ImportError()
				if hasattr(key, 'val'):
					symbolic_key = st(key, key.val)
					value = self.pop(key)
					self[symbolic_key] = value
				else:
					symbolic_key = st(key, key)
					value = self.pop(key)
					self[symbolic_key] = value
		return self

	def SymbolicValue(self, SI=None):
		from . __init__ import getSymbolic

		for key in self.keys():
			value = self[key]
			if isinstance(value, dict) == False:
				if isinstance(value, SymbolicObject) == False:
					st = getSymbolic(value)
					if (st == None):
						print("Error at argument " + key + " : no corresponding symbolic type found for type " + str(type(value)))
						raise ImportError()
					if hasattr(value, 'val'):
						self[key] = st(key, value.val)
					else:
						self[key] = st(key, value)
			else:
				'''This is a nested dict, we need to recursively symbolicize it
				'''
				if isinstance(self[key], SymbolicDict):
					self[key] = self[key].SymbolicValue(SI)
				elif isinstance(value, dict):
					self[key] = SymbolicDict(key, self[key])
				
		return self


	def getConcrValue(self):
		return self

	def getConcrValue2(self):
		return self.val

	def wrap(conc, sym):
		return SymbolicDict("se", conc, sym)

	# wrap only wrap the entire dict
	def _do_sexpr(self,args,fun,op):
		unwrapped = [ (a.unwrap() if isinstance(a,SymbolicObject) else (a,a)) for a in args ]
		args = zip(inspect.getargspec(fun).args, [ c for (c,s) in unwrapped ])
		concrete = fun(**dict([a for a in args]))
		symbolic = [ op ] + [ s for c,s in unwrapped ]

		# generate a new dict to remember the expr
		# why self = SymbolicDict.wrap does not work
		# refer to http://stackoverflow.com/questions/575196/in-python-why-can-a-function-modify-some-arguments-as-perceived-by-the-caller
		self.expr = symbolic
		return concrete

	def __bool__(self):
		return bool(len(self))

	def get(self, key, default=None):
		concrete = self._do_sexpr([self, key], lambda x, y: dict(x).get(y), 'get')
		return concrete

	def getSym(self, key, default=None):
		for k in self.keys():
			if type(key)(k) == key:
				return self[key]
		return default

	def __eq__(self, other):
		if isinstance(self,SymbolicDict) and isinstance(other,SymbolicDict):
			self_keys = set(self.keys())
			other_keys = set(other.keys())
			intersect_keys = self_keys.intersection(other_keys)
			if len(intersection_keys) != len(self_keys):
				return False
			same = set(o for o in intersect_keys if self[o] == other[o])
			if len(same)!=len(self_keys):
				return False
		else:
			return False

	def _do_sexpr2(self,args,fun,op,wrap):
		unwrapped = [ (a.unwrap() if isinstance(a,SymbolicObject) else (a,a)) for a in args ]
		args = zip(inspect.getargspec(fun).args, [ c for (c,s) in unwrapped ])
		concrete = fun(**dict([a for a in args]))
		symbolic = [ op ] + [ s for c,s in unwrapped ]

		# generate a new dict to remember the expr
		# why self = SymbolicDict.wrap does not work
		# refer to http://stackoverflow.com/questions/575196/in-python-why-can-a-function-modify-some-arguments-as-perceived-by-the-caller
		return wrap(concrete,symbolic)

	def __contains__(self,key):
		# k is symbolicized
		# add special expr to k.expr
		
		from symbolic.symbolic_types.symbolic_int import SymbolicInteger

		wrapped = self._do_sexpr2([self, key], lambda x, y: y in dict(x), 'dict_in', SymbolicInteger.wrap)

		# The only purpose of this condition is to add the predicate into the tree.
		if wrapped == 1:
			return wrapped.val

