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
# $Id$

""" Itaka web server engine """

import config as iconfig
image_dir = iconfig.image_dir
system = iconfig.system
platform = iconfig.platform
iconfig = iconfig.values
import screenshot as iscreenshot

from twisted.web.resource import Resource

import datetime, os

import pygtk
pygtk.require("2.0")

import gtk, gobject

# Use notifications where libnotify is available
notifyavailable = False
if iconfig['server']['notify'] == "True" and system == "posix" and platform != "darwin":
    try:
        import pynotify
        notifyavailable = True

        if not pynotify.init("Itaka"):
            print "[*] WARNING: Pynotify module is missing, disabling."
            notifyavailable = False
    except ImportError:
        print "[*] WARNING: Pynotify module is missing, disabling."
        notifyavailable = False

#: Local iteration counter
lcounter = 0

# Set up the screenshooter server
class ImageResource(Resource):
    """ Take the screenshot code and handle the requests. """

    def __init__(self, ginstance, cinstance):
        """ Intialize inherited GUI and Console instances """
        self.igui = ginstance

    def render_GET(self, request):
        """ Handle GET requests for screenshot. """

        if (request.uri == "/screenshot"):

            request.setHeader("Content-type", "image/" + iconfig['screenshot']['format'])
            request.setHeader("Connection", "close")

            self.icip = request.getClientIP()
            self.time = datetime.datetime.now()
            # self.icbrowser = request.getClient()

            self.shotFile = iscreenshot.Screenshot()
            global lcounter
            lcounter += 1

            # Call libnotify
            if (iconfig['server']['notify'] == "True") and notifyavailable != False:
                uri = "file://" + (os.path.join(image_dir, "itaka-take.png")) 

                n = pynotify.Notification("Screenshot taken!", "%s took screenshot number %d" % (self.icip, lcounter), uri)
                if not n.show():
                    pass

            # Tell the GUI what changed
            self.igui.talk('updateGuiStatus', str(lcounter), str(self.icip), self.time)

            return open(self.shotFile, 'rb').read()		
