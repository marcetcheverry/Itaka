# -*- coding: utf8 -*-
""" ItakaX Cocoa+FTP (2006 Marc E.)
    Dependencies: Python >=2.3, PyObjC
    References: http://guides.macrumors.com/screencapture
               http://docs.python.org/lib/ftp-objects.html
	       http://pydoc.org/2.4.1/os.html
	       http://svn.red-bean.com/pyobjc/trunk/pyobjc/Examples/Scripts/HelloWorld.py
"""
import sys, os, time, ftplib, traceback

import objc
from Foundation import *
from AppKit import *
from PyObjCTools import AppHelper

# Set up FTP options
ihost = "host"
iport = 21
iuser = "user"
ipasswd = "pass"
# FTP directory where to upload 
# the screenshot (*must exist*)
iupdir = "/"
# Where the temp screenshot will be saved
iscreenshot = "/tmp/screen.png"
# Time between screenshots
itime = 8

# Handle actions
class AppDelegate (NSObject):
	def applicationDidFinishLaunching_(self, aNotification):
		""" FIXME: I do not know what this event
		does or when it does it. """
		print "[*] ItakaX Cocoa+FTP"
		
	def takeshot(self):
		""" Takethe screenshot. """
		print "[*] Taking screenshot to %s " % (iscreenshot)
		os.system("screencapture -S %s" % (iscreenshot))
	
	def upload(self, host, port, username, password, updir):
		""" Call self.takeshot() and upload iscreenshot. """
		ftp = ftplib.FTP()
		ftp.connect(host, port)
		print "[*] Connecting to %s:%s..." % (host, port)
		print "[*} %s" % (ftp.getwelcome())
		try:
	  	  try:
	    	        ftp.login(username, password)
	    		# FIXME: Add a check to see 
			# if updir exists, then ftp.mkd()
			if updir:
	    			ftp.cwd(updir)
			print "[*] Currently in:", ftp.pwd()
			print "[*] Uploading: %s..." % (iscreenshot)
			self.takeshot()
	    		if (os.path.exists(iscreenshot)):
				file = open(iscreenshot, "rb")
				try:
					""" The second argument is the name of 
					the file on the server. """
	    				ftp.storbinary('STOR ' + iscreenshot.split('/')[2], file)
  	    				print "[*] Success!"
				except:
					""" Print traceback since we do not do
					error handling yet. """
					traceback.print_exc()
 	    			file.close()
			else:
	    			print "[*] %s doesnt exist. It wasnt taken." % (iscreenshot)
		  finally:
		        print "[*] Quitting..."
			ftp.quit()
        	except:
			ftp.quit()
 	  		traceback.print_exc()

	def start_(self, sender):
		print "[*] %s: Starting infinite upload loop..." % (sender)
		self.run = True
		while(self.run):
			# TODO: Add countdown with for and range()
			time.sleep(itime)
			self.upload(ihost, iport, iuser, ipasswd, iupdir)

	def stop_(self, sender):
		print "[*] %s: Stop() called..." % (sender)
		self.run = False

def main():
	""" Set up the main cocoa gui """
	app = NSApplication.sharedApplication()
	delegate = AppDelegate.alloc().init()
	NSApp().setDelegate_(delegate)

	window = NSWindow.alloc()
	frame = ((200.0, 300.0), (250.0, 100.0))
    	window.initWithContentRect_styleMask_backing_defer_ (frame, 15, 2, 0)
    	window.setTitle_ ('Itaka')
   	window.setLevel_ (3)                   # floating window
	
	startbutton = NSButton.alloc().initWithFrame_ (((10.0, 10.0), (80.0, 80.0)))
    	window.contentView().addSubview_ (startbutton)
    	startbutton.setBezelStyle_( 4 )
    	startbutton.setTitle_( 'Start' )
    	startbutton.setTarget_( app.delegate() )
    	startbutton.setAction_( "start:" )
        
	beep = NSSound.alloc()
    	beep.initWithContentsOfFile_byReference_( '/System/Library/Sounds/Tink.Aiff', 1 )
    	startbutton.setSound_( beep )

	# Esto seria el boton para parar.
        bye = NSButton.alloc().initWithFrame_ (((100.0, 10.0), (80.0, 80.0)))
    	window.contentView().addSubview_ (bye)
    	bye.setBezelStyle_( 4 )
    	bye.setTarget_ (app)
    	bye.setAction_ ('stop:')
    	bye.setEnabled_ ( 1 )
    	bye.setTitle_( 'Stop' )

    	adios = NSSound.alloc()
    	adios.initWithContentsOfFile_byReference_(  '/System/Library/Sounds/Basso.aiff', 1 )
    	bye.setSound_( adios )

    	window.display()
    	window.orderFrontRegardless()          ## but this one does

    	AppHelper.runEventLoop()
	
if __name__ == '__main__' : main()
