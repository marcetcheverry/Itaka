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

import datetime, os, traceback, sys

try:
    import screenshot
    import error
except ImportError:
    print "[*] ERROR: Failed to import Itaka screenshot module"
    traceback.print_exc()
    sys.exit(1)

try:
    from twisted.python import log
    from twisted.web import server, static
    from twisted.internet import reactor
    import twisted.internet.error
    from twisted.web.resource import Resource
except ImportError:
    print "[*] ERROR: Could not import Twisted Network Framework"
    sys.exit(1)

class ImageResource(Resource):
    """ 
    Handle server requests and call for a screenshot.
    """

    def __init__(self, guiinstance):
        """ 
        Constructor.

        @type guiinstance: instance
        @param guiinstance: An instance of our L{Gui} class.
        """

        self.gui = guiinstance
        self.console = self.gui.console
        self.itakaglobals = self.gui.itakaglobals
        self.screenshot = screenshot.Screenshot(self.gui)
        
        #: Server hits counter
        self.counter = 0

    def render_GET(self, request):
        """
        Handle GET requests for screenshot.

        @type request: instance
        @param request: twisted.web.server.Request instance.

        @rtype: str
        @return: Screenshot image.
        """

        # Get up to date configuration values everytime there is a request
        self.configuration = self.gui.configuration

        self.request = request

        if (self.request.uri == "/screenshot"):
            self.request.setHeader("Content-type", "image/" + self.configuration['screenshot']['format'])
            self.request.setHeader("Connection", "close")

            self.ip = self.request.getClientIP()
            self.time = datetime.datetime.now()

            try:
                self.shotFile = self.screenshot.take_screenshot()
            except error.ItakaScreenshotError:
                return

            self.counter += 1

            if self.configuration['server']['notify'] and self.itakaglobals.notifyavailable:
                import pynotify

                uri = "file://" + (os.path.join(self.itakaglobals.image_dir, "itaka-take.png")) 

                n = pynotify.Notification("Screenshot taken", 
                "%s requested screenshot number %d"
                % (self.ip, self.counter), uri)

                n.set_timeout(1500)
                n.attach_to_status_icon(self.gui.statusIcon)
                n.show()

            # Tell the GUI what changed
            self.gui.update_gui(self.counter, self.ip, self.time)

            return open(self.shotFile, 'rb').read()		

class ScreenshotServer:
    """
    Screenshot server.
    """
    def __init__(self, guiinstance):
        """
        Constructor.

        @type guiinstance: instance
        @param guiinstance: An instance of our L{Gui} class.
        """

        self.gui = guiinstance
        self.configuration = self.gui.configuration
        self.console = self.gui.console

        self.server_listening = False

        # Set up the twisted site
        self.root = static.Data(self.configuration['html']['html'], 'text/html; charset=UTF-8')
        self.root.putChild('', self.root)
        # Pass a reference of GUI and Console instance to Screenshot module for its notification handling.
        self.root.putChild('screenshot', ImageResource(self.gui))
        self.site = server.Site(self.root)

    def start(self):
        """
        Start the server.
        """

        # Get a newer configuration
        self.configuration = self.gui.configuration

        try:
            self.server = reactor.listenTCP(self.configuration['server']['port'], self.site)
        except twisted.internet.error.CannotListenError, e:
            raise error.ItakaServerErrorCannotListen, e

        self.server_listening = True
        # Log to the Gui Logger instance
        log.addObserver(self.gui.log.twisted_observer)
    
    def stop(self):
        """
        Stop the server.
        """

        self.server.stopListening()
        self.server_listening = False
        log.removeObserver(self.gui.log.twisted_observer)

    def listening(self):
        """
        Whether the server is listening or not.

        @rtype: bool
        @return: True if it's listening or False if it is not.
        """

        return self.server_listening
