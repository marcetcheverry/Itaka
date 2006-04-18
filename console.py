#! /usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka console handling engine """

import config as iconfig

class Console:
	""" Console I/O handler organized by message type. Also handle GUI logging when passed an instance. """

	def __init__(self, ginstance=False):
		""" Init console handler with a GUI instance. """
		if ginstance: self.igui = ginstance
		print "[*] Itaka %s starting up..." % (iconfig.version)
		
	def __del__(self):
		""" Destructor. """
		print "[*] Itaka shutting down..."
		
	def msg(self, message, gui=False):
		""" Message handler. """
		# The gui argument is for the FTP method. It couples the console logger with the GUI logger.
		# In the Twisted method, logging is done by its engine.
		# Note the peculiar syntax of the argument you must pass to logger.
		# A dict with the first key being 'message', coupled with a str()'ed tuple'd message.
		print "[*] %s" % (message)
		if gui: self.igui.logger({'message': [str(message)]})
		
	def warn(self, caller, message, gui=False):
		""" Warning handler. """
		self.array = ".".join(caller)
		print "[*] WARNING: %s: %s" % (self.array, message)
		if gui: self.igui.logger({'message': [str("[*] ERROR: %s: %s" % (self.array, message))]})		
		
	def debug(self, caller, message, gui=False):
		""" Debug handler. """
		self.array = ".".join(caller)
		print "[*] DEBUG: %s: %s" % (self.array, message)
		if gui: self.igui.logger({'message': [str("[*] ERROR: %s: %s" % (self.array, message))]})
		
	def error(self, caller, message, gui=False):
		""" Error handler. """
		self.array = ".".join(caller)
		print "[*] ERROR: %s: %s" % (self.array, message)
		if gui: self.igui.logger({'message': [str("[*] ERROR: %s: %s" % (self.array, message))]})
