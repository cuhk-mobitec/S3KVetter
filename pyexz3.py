# Copyright: see copyright.txt

import os
import sys
import pdb
import logging
import traceback
from optparse import OptionParser

from symbolic.loader import *
from symbolic.explore import ExplorationEngine
from symbolic.verify import VerifyEngine
from datetime import datetime

timeBegin = datetime.now()

print("PyExZ3 (Python Exploration with Z3)")

sys.path = [os.path.abspath(os.path.join(os.path.dirname(__file__)))] + sys.path
#Solve no module named symbolic issue
sys.path.append('../')

usage = "usage: %prog [options] <path to a *.py file>"
parser = OptionParser(usage=usage)

parser.add_option("-l", "--log", dest="logfile", action="store", help="Save log output to a file", default="")
parser.add_option("-s", "--start", dest="entry", action="store", help="Specify entry point", default="")
parser.add_option("-g", "--graph", dest="dot_graph", action="store_true", help="Generate a DOT graph of execution tree")
parser.add_option("-m", "--max-iters", dest="max_iters", type="int", help="Run specified number of iterations", default=0)
parser.add_option("--cvc", dest="cvc", action="store_true", help="Use the CVC SMT solver instead of Z3", default=False)
parser.add_option("--z3", dest="z3", action="store_false", help="Use the Z3 SMT solver")
parser.add_option("--expected", dest="expected_predicate_file", action="store", help="Verify whether the execution result satisfies the predefined predicate")
parser.add_option("--config", dest="config_json_file", action="store", help="Provide a input file to verify the result")

(options, args) = parser.parse_args()

if not (options.logfile == ""):
	logging.basicConfig(filename=options.logfile,level=logging.DEBUG)

if len(args) == 0 or not os.path.exists(args[0]):
	parser.error("Missing app to execute")
	sys.exit(1)

#Make cvc as the default
solver = "z3" if options.z3 else "cvc"

filename = os.path.abspath(args[0])
	
# Get the object describing the application
app = loaderFactory(filename,options.entry)
if app == None:
	sys.exit(1)

print ("Exploring " + app.getFile() + "." + app.getEntry())

result = None
try:
	# cov = coverage.Coverage(branch = True, include= 'elseif.py')
	# cov.start()
	engine = ExplorationEngine(app.createInvocation(), filename, options.config_json_file, solver=solver)
	generatedInputs, returnVals, path = engine.explore(options.max_iters)
	print('Number of total executions is '+str(engine.numofExecution))
	#check the result
	result = app.executionComplete(returnVals)
	# cov.stop()
	# cov.html_report(directory='covhtml')

	#output DOT graph
	#Render dot file
	if options.dot_graph:
		with open(filename+".dot","w") as f:
			f.write(path.toDot())
		#from graphviz import render; render('dot', 'png', filename+".dot")
	timeEnd = datetime.now()
	delta = timeEnd - timeBegin
	print ("It takes " + str(delta.seconds) + " seconds to explore the program")

	smtLibExprs = path.toSMTLib2(engine.solver)
	
	with open('verify/'+os.path.basename(filename)[:-3]+'.logic', 'w') as logicFile:
		logicFile.write(smtLibExprs)

	if options.expected_predicate_file != None:
		timeBegin = datetime.now()
		verify = VerifyEngine(options.expected_predicate_file, 'verify/'+os.path.basename(filename)[:-3]+'.logic', options.config_json_file)
		#verify.constructSmtCode(generatedInputs)

		if verify.program_logic != None and verify.expected_predicate != None:
			verify.executionVerify(generatedInputs, returnVals)
		timeEnd = datetime.now()
		delta = timeEnd - timeBegin
		print ("It takes " + str(delta.seconds) + " seconds to verify the testing")
except ImportError as e:
	# createInvocation can raise this
	logging.error(e)
	sys.exit(1)

if result == None or result == True:
	sys.exit(0);
else:
	sys.exit(1);	
