#!/usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka Cocoa GUI """

import sys, os, traceback 

# Itaka core modules
try:
	import config as iconfig
	# Global values
	config = iconfig
	iconfig = iconfig.values
	import console as iconsole

	import ftp as iftp
except ImportError:
	print "[*] ERROR: Failed to import Itaka modules."
	traceback.print_exc()
	sys.exit(1)
	
# PyObjC
try:
	import objc
	from Foundation import *
	from AppKit import *
	from PyObjCTools import AppHelper
except ImportError:
	print "[*] ERROR: PyObjC bindings are missing."
	sys.exit(1)

# Set up global console instance

class AppDelegate (NSObject):
	def applicationDidFinishLaunching_(self, aNotification):
		self.console = iconsole.Console(self)

	def start_(self, sender):
		self.console.msg("Starting FTP upload sequence every %s to %s:%s..." % (iconfig['screenshot']['time'], iconfig['ftp']['host'], iconfig['ftp']['port']))
		# Start a ftp instance with a console instance
		self.ftprunning = iftp.Ftp(self, self.console, False)
		self.ftprunning.start()

	def stop_(self, sender):
		self.console.msg("Stopping FTP sequence...")
		self.ftprunning.stop()

def main():
	""" Set up the GUI """
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
