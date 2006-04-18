#! /usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka core """

import sys, os, traceback 

# Itaka core modules
try:
	# Initiate the Configuration engine.
	import config as iconfig
	iconfig.ConfigParser().load()

	# Import our GUI toolkit 
	if (iconfig.system == 'posix' or 'nt'): import uigtk as igui
	elif (iconfig.system == 'darwin'): import uicocoa as igui
except ImportError:
	print "[*] ERROR: Failed to import Itaka modules."
	traceback.print_exc()
	sys.exit(1)
	
if __name__ == "__main__":
	try:
		gui = igui.Gui()
		gui.main()
	except AttributeError:
		print "[*] ERROR: Could not initiate GUI."
		traceback.print_exc()
		sys.exit(1)
