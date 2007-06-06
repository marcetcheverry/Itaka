#! /usr/bin/env python
# -*- coding: utf8 -*-
#
# Itaka is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
# 
# Itaka is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Itaka; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Copyright 2003-2007 Marc E. <santusmarc_at_gmail.com>.
# http://itaka.jardinpresente.com.ar
#
# $Id$

""" Itaka web server engine """

from twisted.web.resource import Resource
import datetime, os, traceback, sys

try:
    import screenshot as iscreenshot
except ImportError:
    print "[*] ERROR: Failed to import Itaka screenshot module."
    traceback.print_exc()
    sys.exit(1)
    
# Server hit iteration counter
lcounter = 0

class ImageResource(Resource):
    """ Take the screenshot code and handle the requests. """

    def __init__(self, guiinstance, consoleinstance):
        """ Intialize inherited GUI, Console and global Configuration (through GUI instance) values """
        self.gui = guiinstance
        self.console = consoleinstance
        self.itakaglobals = self.gui.itakaglobals

    def render_GET(self, request):
        """ Handle GET requests for screenshot. """

        # Get up to date configuration values
        self.configuration = self.gui.configuration

        if (request.uri == "/screenshot"):
            request.setHeader("Content-type", "image/" + self.configuration['screenshot']['format'])
            request.setHeader("Connection", "close")

            self.icip = request.getClientIP()
            self.time = datetime.datetime.now()
            # self.icbrowser = request.getClient()

            # This takes the screenshot
            self.shotFile = iscreenshot.Screenshot(self.gui)

            if self.shotFile is not False:
                global lcounter
                lcounter += 1

                # Call libnotify
                if (self.configuration['server']['notify'] == "True") and self.itakaglobals.notifyavailable != False:
                    import pynotify

                    uri = "file://" + (os.path.join(self.itakaglobals.image_dir, "itaka-take.png")) 

                    n = pynotify.Notification("Itaka Screenshot taken", "%s took screenshot number %d" % (self.icip, lcounter), uri)
                    if not n.show():
                        pass

                # Tell the GUI what changed
                self.gui.talk('updateGuiStatus', str(lcounter), str(self.icip), self.time)

                return open(self.shotFile, 'rb').read()		
