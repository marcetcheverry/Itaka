#! /usr/bin/env python
# -*- coding: utf8 -*-
# FTP backend.
import ftplib, threading, time, datetime, os, traceback
import globals as iglobals
import screenshot as iscreenshot

# Local counter
lcounter = 0
class Ftp(threading.Thread):
	""" Threaded FTP uploading method. """
	def __init__(self, ginstance, sinstance):
		""" Set up the threading event (stop/start) handler. """
		# Set up GUI instance (console implied), and ImageResource
		self.igui = ginstance
		self.sinstance = sinstance
		threading.Thread.__init__(self)
		self.stopthread = threading.Event()
		
	def run(self):
		""" Upload code, inside a loop waiting for an event (self.stopthread). """

		# Begin the upload loop.
		while not self.stopthread.isSet():
			
			# Safeguard for canceling ongoing transfers
			self.canceled = False
			
			# Get the Console instance output from the GUI instance.
			self.console = self.igui.console
			self.ftp = ftplib.FTP()
			self.ftp.set_debuglevel(iglobals.ftpdebug)
			
			#ftplib.all_errors: (<class ftplib.Error at 0xb7d285fc>, <class socket.error at 0xb7d289ec>, <class exceptions.IOError at 0xb7d5d47c>, <class exceptions.EOFError at 0xb7d5d53c>)
			try:
				self.ftp.connect(iglobals.ftphost, iglobals.ftport)
			except (ftplib.all_errors, ftplib.error_perm), (self.errormsg):
				self.console.error(['Ftp', 'run'], "%s" % (str(self.errormsg)), True)
				# Call the error handling function
				self.error(self.errormsg)				
			
				break

			self.console.msg("Connecting to %s:%d..." % (iglobals.ftphost, iglobals.ftport), True)
			self.console.msg(self.ftp.getwelcome(), True)
			
			# Login
			try:
				self.ftp.login(iglobals.ftpuser, iglobals.ftpass)
			except (ftplib.all_errors, ftplib.error_perm, AttributeError), (self.errormsg):
				self.console.error(['Ftp', 'run'], "%s" % (self.errormsg), True)
				# Call the error handling function
				self.error(self.errormsg)				
				break
	
			if iglobals.ftpdir:
				try:
					self.ftp.cwd(iglobals.ftpdir)
				except:
					self.console.msg("Creating %s directory..." % (iglobals.ftpdir), True)
					self.ftp.mkd(iglobals.ftpdir)
					self.ftp.cwd(iglobals.ftpdir)

	    		self.console.msg("Currently in: %s." % (self.ftp.pwd()), True)
			
			# Take the screenshot and check for file
			self.ftpscreen = iscreenshot.ImageResource.getScreenshot(self.sinstance)
			
			# Nice output
			self.ftpdirstr = "to"
			if iglobals.ftpdir:	self.ftpdirstr = "to %s on" % (iglobals.ftpdir)
			self.console.msg("Uploading screenshot %s %s server..." % (self.ftpscreen, self.ftpdirstr), True)
			
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
						self.console.msg("Ongoing transfer canceled. Connection terminated.", True)

					except (ftplib.all_errors, ftplib.error_perm), (self.errormsg):
						self.console.error(['Ftp', 'run'], "%s" % (self.errormsg), True)
						# Call the error handling function
						self.error(self.errormsg)				
						break
					
					# Tell the GUI about the success
					if not self.canceled:
						global lcounter
						lcounter += 1
	  	    				self.console.msg("Screenshot " + str(lcounter) + " uploaded",  True)
						self.igui.talk('updateGuiStatus', str(lcounter), None, datetime.datetime.now())
						""" This marks the end of a clean connection, closes the file,
						sets the flag for a clean & finished connection, and sets the
						timer for a new one. """
						self.ftp.quit()
						self.console.msg("Connection to the server terminated.")
						self.finished = True
  						self.file.close()
						time.sleep(iglobals.ftptime)
				# Error handler, print, close, clean and finish.		
				except:
					traceback.print_exc()
 	    				self.file.close()
					self.ftp.quit()
					self.console.msg("Connection to the server terminated.", True)
			# File not found handler. Close the connection.
			else:
				self.ftp.quit()
				self.console.msg("Connection to the server terminated.", True)
				self.console.error(["Ftp", "run"], "Cant find %s" % (screenshot), True)
	def stop(self):
		""" Handles stoping, including cancelling ongoing tranfers. """
		self.stopthread.set()	
		# Unorthodox fix: kill the connection
		self.ftp.close()
	
	def error(self, errorstring):
		""" Handle FTP connection errors. """
		# Stop the thread, connection, and warn the GUI.
		self.console.msg("Connection to the server terminated.", True)
		self.stopthread.set()	
		self.igui.talk('updateFtpStatus', errorstring, None, None)

