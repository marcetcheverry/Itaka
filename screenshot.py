#! /usr/bin/env python
# -*- coding: utf8 -*-
# Screenshot Twisted/GTK+ engine

import globals as iglobals

from twisted.web.resource import Resource
import gc, sys, os, datetime
# Import GTK+
try:
	import pygtk
	pygtk.require("2.0")
except ImportError:
	print "[*] WARNING: Pygtk module is missing."
        pass
try:
        import gtk, gobject
except ImportError:
	print "[*] ERROR: GTK+ Python bindings are missing."
	sys.exit(1)

# Local counter
lcounter = 0

# Set up the screenshooter server
class ImageResource(Resource):
	""" Take the screenshot code and handle the requests. """

	def __init__(self, ginstance):
		""" Intialize inherited GUI instance """
		self.igui = ginstance

	# Screenshot request handler
	def getScreenshot(self):
		""" Takes a screenshot and returns it. """
		self.shot = 'itakashot.' + iglobals.format
		w = gtk.gdk.screen_width()
		h = gtk.gdk.screen_height()
		screenshot = gtk.gdk.Pixbuf.get_from_drawable(
			gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h),
			gtk.gdk.get_default_root_window(),
			gtk.gdk.colormap_get_system(),
			0, 0, 0, 0, w, h)
		self.shotFile = os.path.join(iglobals.path,self.shot)
        	screenshot.save(self.shotFile, self.shot.split('.')[1], {"quality":str(iglobals.quality)})

		# Important workaround to avoid a memory leak.
		# http://www.async.com.br/faq/pygtk/index.py?req=show&file=faq08.004.htp
		del screenshot
		gc.collect()

		return self.shotFile
	
	def render_GET(self, request):
		""" Handle GET requests for screenshot. """
		request.setHeader("Content-type", "image/" + iglobals.format)
		self.icip = request.getClientIP()
		self.time = datetime.datetime.now()
		# self.icbrowser = request.getClient()

		self.getScreenshot()
		global lcounter
		lcounter += 1
		# Call libnotify manually FIXME
		if (iglobals.notify): 
			self.notifyseq = ["notifyit", str(self.icip), str(lcounter)]
			self.notifyinstance = gobject.spawn_async(self.notifyseq, flags=gobject.SPAWN_SEARCH_PATH)
				
		# Tell the GUI what changed
		self.igui.talk('updateGuiStatus', str(lcounter), str(self.icip), self.time)

		return open(self.shotFile, 'rb').read()		
