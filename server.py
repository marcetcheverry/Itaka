#! /usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka web server engine """

import config as iconfig
iconfig = iconfig.values
import screenshot as iscreenshot

from twisted.web.resource import Resource

import datetime

import pygtk
pygtk.require("2.0")

import gtk, gobject

#: Local iteration counter
lcounter = 0

# Set up the screenshooter server
class ImageResource(Resource):
	""" Take the screenshot code and handle the requests. """

	def __init__(self, ginstance):
		""" Intialize inherited GUI instance """
		self.igui = ginstance

	def render_GET(self, request):
		""" Handle GET requests for screenshot. """
		request.setHeader("Content-type", "image/" + iconfig['screenshot']['format'])
		self.icip = request.getClientIP()
		self.time = datetime.datetime.now()
		# self.icbrowser = request.getClient()

		self.shotFile = iscreenshot.getScreenshot()
		global lcounter
		lcounter += 1
		# Call libnotify manually FIXME
		if (iconfig['itaka']['notify']): 
			self.notifyseq = ["notifyit", str(self.icip), str(lcounter)]
			self.notifyinstance = gobject.spawn_async(self.notifyseq, flags=gobject.SPAWN_SEARCH_PATH)
				
		# Tell the GUI what changed
		self.igui.talk('updateGuiStatus', str(lcounter), str(self.icip), self.time)

		return open(self.shotFile, 'rb').read()		
