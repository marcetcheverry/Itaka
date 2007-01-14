#! /usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka screenshot engine """

import gc, os

# Itaka core modules
import config as iconfig
config = iconfig
iconfig = iconfig.values


if (config.system == 'darwin'):
	import objc
	from Foundation import *
        from AppKit import *
else:
	import pygtk
	pygtk.require("2.0")
	import gtk 

#: Final absolute path to the screenshot file
shotFile = os.path.join(iconfig['screenshot']['path'], 'itakashot.%s' % (iconfig['screenshot']['format']))

if (config.system == 'darwin'):
	class CocoaScreenshot(NSObject):
		""" NSObject wrapper for the Cocoa screenshooting code """

		#: Cocoa filetype representation mapping dictionary
		fileRepresentationMapping = {
		'.png': NSPNGFileType,
		'.gif': NSGIFFileType,
		'.jpg': NSJPEGFileType,
		'.jpeg': NSJPEGFileType,
		'.bmp': NSBMPFileType,
		'.tif': NSTIFFFileType,
		'.tiff': NSTIFFFileType,
		}

		def init(self):
			""" Initializer class for NSObject """
			self = super(CocoaScreenshot, self).init()
			if self is None: return None
			return self

		def _getFileRepresentationType(self):
			""" Cocoa filetype representation function to mach the filetype with the _fileRepresentationMapping dictionary"""
			base, ext = os.path.splitext(shotFile)
			return self.fileRepresentationMapping[ext.lower()]

		def Screenshot(self):
			""" Cocoa screenshot implementation """
			# FIXME: See http://www.cocoadev.com/index.pl?NSImageToJPEG for JPEG compressiom
			# http://www.paulhammond.org/2005/08/webkit2png/webkit2png-0.4.txt

			# Initialize screen frame and allocate image in memory
			rect = NSScreen.mainScreen().frame()
			image = NSImage.alloc().initWithSize_((rect.size.width, rect.size.height))
			# Create a transparent fullsize window
			window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
							rect, 
							NSBorderlessWindowMask, 
							NSBackingStoreNonretained, 
							False)

			view = NSView.alloc().initWithFrame_(rect)
			window.setLevel_(NSScreenSaverWindowLevel + 100)
			window.setHasShadow_(False)
			window.setAlphaValue_(0.0)
			window.setContentView_(view)
			# Send the window to the front, focus NSView to execute an action action with 
			window.orderFront_(self)
			# Threadsafe needed?
			view.lockFocusIfCanDraw()
			# Create a Bitmap representation of the focused screen frame and make it an image
			screenRep = NSBitmapImageRep.alloc().initWithFocusedViewRect_(rect)
			image.addRepresentation_(screenRep)
			view.unlockFocus()
			window.orderOut_(self)
			window.close()

			# Determine filetype, and create a representation (export to filetype)
			representation = self._getFileRepresentationType()

			# JPEG quality support
			if iconfig['screenshot']['format'] in ('jpeg', 'png', 'JPEG', 'JPG'):
				# liquality = int(iconfig['screenshot']['quality'])/100.0 ValueError: depythonifying 'int', got 'str' of 14
				# FIXME	
				data = screenRep.representationUsingType_properties_(NSJPEGFileType, None)
				#data = screenRep.representationUsingType_properties_(representation, {'NSImageCompressionFactor': 0.7})
			else:
				data = screenRep.representationUsingType_properties_(representation, None)

			data.writeToFile_atomically_(shotFile, False)
		
			return shotFile

def Screenshot():
	""" Returns a screenshot file. """
	if (config.system != 'darwin'):
		# GTK Screenshooting code.
		w = gtk.gdk.screen_width()
		h = gtk.gdk.screen_height()
		screenshot = gtk.gdk.Pixbuf.get_from_drawable(
			gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h),
			gtk.gdk.get_default_root_window(),
			gtk.gdk.colormap_get_system(),
			0, 0, 0, 0, w, h)
		shotFile = os.path.join(iconfig['screenshot']['path'], 'itakashot.%s' % (iconfig['screenshot']['format']))

		# Save the screnshot, checking before if to set JPEG quality
		if iconfig['screenshot']['format'] == 'jpeg':
			screenshot.save(shotFile, iconfig['screenshot']['format'].lower(), {"quality":str(iconfig['screenshot']['quality'])})
		else:
			screenshot.save(shotFile, iconfig['screenshot']['format'].lower())

		# Important workaround to avoid a memory leak.
		# http://www.async.com.br/faq/pygtk/index.py?req=show&file=faq08.004.htp
		del screenshot
		gc.collect()

		return shotFile
	else:
		cscreenshot = CocoaScreenshot.new()
		return cscreenshot.Screenshot()
		
		#os.popen2("screencapture -S %s" % (shotFile))
