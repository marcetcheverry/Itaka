#! /usr/bin/env python
# -*- coding: utf8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Copyright 2003-2007 Marc E. <santusmarc_at_gmail.com>.
# http://itaka.jardinpresente.com.ar

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

        self.shotFile = iscreenshot.Screenshot()
        global lcounter
        lcounter += 1
        # TODO: Implement libnotify call with IP (self.icip), and lcounter
        # Check for the os
        if (iconfig['server']['notify'] == "True"): 
            pass

        # Tell the GUI what changed
        self.igui.talk('updateGuiStatus', str(lcounter), str(self.icip), self.time)

        return open(self.shotFile, 'rb').read()		
