#! /usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka FTP engine """

import ftplib, threading, time, datetime, os, traceback

# Itaka core modules
import config as iconfig
config = iconfig
iconfig = iconfig.values

# Cocoa modules for Threading
if (config.system == 'darwin'):
	import objc
	from Foundation import *

#: Local iteration counter
lcounter = 0

# Temporary fix for Cocoa GUI
notifygui = True
if (config.system == 'darwin'):
	notifygui = False

class Ftp(threading.Thread):
	""" Threaded FTP uploading method. """
	def __init__(self, ginstance=False, sinstance=False):
		""" Set up the threading event (stop/start) handler. """
		if (config.system != 'darwin'):
			# Set up GUI instance (console implied), and ImageResource
			self.igui = ginstance
			self.sinstance = sinstance
		else:
			self.console = ginstance

		threading.Thread.__init__(self)
			
		self.stopthread = threading.Event()
		
	def run(self):
		""" Upload code, inside a loop waiting for an event (self.stopthread). """
		
		# Use PyObjC threading
		if (config.system == "darwin"):
			#: Create a Pool since we are outside the Main Application Thread
			self.pool = NSAutoreleasePool.new()	
			# See NSRunLoop for better memory management
		
		# Begin the upload loop.
		while not self.stopthread.isSet():
			
			# Safeguard for canceling ongoing transfers
			self.canceled = False

			if (config.system != 'darwin'):
				self.console = self.igui.console

			self.ftp = ftplib.FTP()

			# Set debug 
			if (int(iconfig['ftp']['debug']) > 0):
				self.ftp.set_debuglevel(iconfig['ftp']['debug'])
			
			#ftplib.all_errors: (<class ftplib.Error at 0xb7d285fc>, <class socket.error at 0xb7d289ec>, <class exceptions.IOError at 0xb7d5d47c>, <class exceptions.EOFError at 0xb7d5d53c>)
			try:
				self.ftp.connect(iconfig['ftp']['host'], iconfig['ftp']['port'])
			except (ftplib.all_errors, ftplib.error_perm), (self.errormsg):
				self.console.error(['Ftp', 'run'], "%s" % (str(self.errormsg)))
				# Call the error handling function
				self.error(self.errormsg)		
				break

			self.console.msg("Connecting to %s:%s..." % (iconfig['ftp']['host'], iconfig['ftp']['port']), notifygui)

			self.console.msg(self.ftp.getwelcome(), notifygui)
			
			# Login
			try:
				self.ftp.login(iconfig['ftp']['user'], iconfig['ftp']['pass'])
			except (ftplib.all_errors, ftplib.error_perm, AttributeError), (self.errormsg):
				self.console.error(['Ftp', 'run'], "%s" % (self.errormsg), notifygui)
				# Call the error handling function
				self.error(self.errormsg)				
				break
	
			if iconfig['ftp']['dir']:
				try:
					self.ftp.cwd(iconfig['ftp']['dir'])
				except:
					self.console.msg("Creating %s directory..." % (iconfig['ftp']['dir']), notifygui)
					self.ftp.mkd(iconfig['ftp']['dir'])
					self.ftp.cwd(iconfig['ftp']['dir'])

	    		self.console.msg("Currently in: %s." % (self.ftp.pwd()), notifygui)
			

			# Take the screenshot and check for file
			self.ftpscreen = iscreenshot.Screenshot()
			
			# Nice output
			self.ftpdirstr = "to"
			if iconfig['ftp']['dir']:	self.ftpdirstr = "to %s on" % (iconfig['ftp']['dir'])
			self.console.msg("Uploading screenshot %s %s server..." % (self.ftpscreen, self.ftpdirstr), notifygui)
			
	    		if (os.path.exists(self.ftpscreen)):
	    			self.file = open(self.ftpscreen, "rb")
				# Upload the file
				try:
					# Safeguard for when canceling ongoing transfers
					# Ftplib will raise an AttributeError since it can't read anymore.
					# The other exceptions are normal error handling
					try: 
						self.ftp.storbinary('STOR ' + str(self.ftpscreen).split('/')[-1], self.file)
					except AttributeError, self.error:
						# FIXME/WARNING: This is very risky, since it could give false positives.
						# Warning is displayed on the console
						self.canceled = True
						self.console.warn(['Ftp', 'run'], str(self.error))
						self.console.msg("Ongoing transfer canceled. Connection terminated.")

					except (ftplib.all_errors, ftplib.error_perm), (self.errormsg):
						self.console.error(['Ftp', 'run'], "%s" % (self.errormsg))
						# Call the error handling function
						self.error(self.errormsg)				
						break
					
					# Tell the GUI about the success
					if not self.canceled:
						global lcounter
						lcounter += 1
	  	    				self.console.msg("Screenshot " + str(lcounter) + " uploaded", notifygui)
						if (notifygui):
							self.igui.talk('updateGuiStatus', str(lcounter), None, datetime.datetime.now())
						""" This marks the end of a clean connection, closes the file,
						sets the flag for a clean & finished connection, and sets the
						timer for a new one. """
						
						# FIXME: Add checking if connection is alive
						self.ftp.quit()

						self.console.msg("Connection to the server terminated.", notifygui)
						self.finished = True
  						self.file.close()
						time.sleep(int(iconfig['screenshot']['time']))
				# Error handler, print, close, clean and finish.		
				except:
					traceback.print_exc()
 	    				self.file.close()
					self.ftp.quit()
					self.console.msg("Connection to the server terminated.", notifygui)
			# File not found handler. Close the connection.
			else:
				self.ftp.quit()
				self.console.msg("Error taking screenshot. Connection to the server terminated.", notifygui)
				self.console.error(["Ftp", "run"], "Cant find %s" % (screenshot))
	def stop(self):
		""" Handles stoping, including cancelling ongoing tranfers. """
		self.stopthread.set()
		# Cocoa threading
		if (config.system == "darwin"):
			del self.pool
	
		try:
			self.ftp.quit()
			self.ftp.close()
		except:
			self.ftp.close()
			pass
		# Unorthodox fix: kill the connection
	
	def error(self, errorstring):
		""" Handle FTP connection errors. """
		# Stop the thread, connection, and warn the GUI.
		self.console.msg("Connection to the server terminated.")
		self.stopthread.set()
		if (notifygui):
			self.igui.talk('updateFtpStatus', errorstring, None, None)

