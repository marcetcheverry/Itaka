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
# Copyright 2003-2007 Marc E.
# http://itaka.jardinpresente.com.ar
#
# $Id$

""" Itaka server engine """

import datetime, os, traceback, sys

try:
    import screenshot
    import error
except ImportError:
    print "[*] ERROR: Failed to import Itaka modules"
    traceback.print_exc()
    sys.exit(1)

try:
    from twisted.python import log
    from twisted.web import server, static, http, resource
    from twisted.internet import reactor
    import twisted.internet.error
except ImportError:
    print "[*] ERROR: Could not import Twisted Network Framework"
    traceback.print_exc()
    sys.exit(1)

class BaseHTTPServer:
    """
    Base HTTP Server.
    """

    def __init__(self):
        """
        Constructor.
        """

        self.server_listening = False

    def add_static_resource(self, name, data, type='text/html; charset=UTF-8'):
        """
        Create a static.Data Twisted resource.Resource.

        @type name: str
        @param name: Name of the resource.

        @type data: str
        @param data: Data in memory to add to the resource, typically HTML.

        @type type: str
        @param type: The type of data we are serving.

        @rtype: resource.Resource
        @return: The instance of the resource created.
        """

        setattr(self, name, static.Data(data, type))
        return getattr(self, name)

    def add_child_to_resource(self, name, path, resource):
        """
        Add a static child resource to a Twisted resource.Resource.

        @type name: str
        @param name: The name of the Twisted resource.Resource.  

        @type path: str
        @param path: The path name (i.e http://www.site.com/PATH) of the Resource. You almost certainly don't want '/' in your path. If you intended to have the root of a folder, e.g. /foo/, you want path to be ''.

        @type resource: instance
        @param resource: A Twisted Resource.
        """

        getattr(self, name).putChild(path, resource)

    def create_site(self, resource):
        """
        Creates a Twisted.server.Site with a Twisted Resource.

        @type resource: instance
        @param resource: An instance of a Twisted resource created with L{add_static_resource}.
        """

        self.site = server.Site(resource)

    def start_server(self, port):
        """
        Start the server.

        @type port: int
        @param port: Port number to listen on.
        """

        try:
            self.server = reactor.listenTCP(port, self.site)
        except twisted.internet.error.CannotListenError, e:
            raise error.ItakaServerErrorCannotListen, e

        self.server_listening = True
    
    def stop_server(self):
        """
        Stop the server.
        """

        self.server.stopListening()
        self.server_listening = False

    def listening(self):
        """
        Whether the server is listening or not.

        @rtype: bool
        @return: True if it's listening or False if it is not.
        """

        return self.server_listening

    def add_log_observer(self, observer):
        """
        Add a twisted.log observer.
        
        @type observer: method
        @param observer: A method to send the logs to.
        """

        self.log_observer = observer
        log.addObserver(observer)

    def remove_log_observer(self, observer=False):
        """
        Remove a twisted.log observer.
        
        @type observer: method
        @param observer: The name of the method specified in add_log_observer. If False, the last known log observer added will be removed.
        """

        if observer:
            log.removeObserver(observer)
        else:
            log.removeObserver(self.log_observer)

    def get_listening_information(self):
        """
        Returns the information of the current listening server.

        @rtype: twisted.internet.interfaces.IAddress
        @return: The current server's networking information.
        """

        if self.server_listening:
            return self.server.getHost()

class ScreenshotServer(BaseHTTPServer):
    """
    Screenshot server that builds upon BaseHTTPServer.
    """

    def __init__(self, guiinstance):
        """
        Constructor. Overrides BaseHTTPServer's __init__ to create our resources on-the-fly.

        @type guiinstance: instance
        @param guiinstance: An instance of our L{Gui} class.
        """

        self.gui = guiinstance
        self.itakaglobals = self.gui.itakaglobals
        self.configuration = self.gui.configuration
        self.console = self.gui.console

        self.server_listening = False

        # Here we use our own static.Data special child resource because we need Authentication handling.
        # Otherwise we would just use our own self.add_static_resource.
        self.root = RootResource(self.gui, self.itakaglobals.headhtml + self.configuration['html']['html'] + self.itakaglobals.footerhtml)
        self.add_child_to_resource('root', '', self.root)
        self.add_child_to_resource('root', 'screenshot', ScreenshotResource(self.gui))
        self.create_site(self.root)

class RootResource(static.Data):
    """
    Main resource with authentication support.

    Please read RFC 2617 to understand the HTTP Authentication process.
    """

    def __init__(self, guiinstance, data, type='text/html; charset=UTF-8'):

        """ 
        Constructor that inherits code from resource.Resource->static.Data.

        @type guiinstance: instance
        @param guiinstance: An instance of our L{Gui} class.

        @type html: string
        @param html: The HTML to be displayed.

        @type type: str
        @param type: The type of data we are serving.
        """

        self.gui = guiinstance
        self.console = self.gui.console
        self.itakaglobals = self.gui.itakaglobals
        self.configuration = self.gui.configuration

        # Inherited from the actual code of Twisted's static.Data
        self.children = {}
        self.data = data
        self.type = type

        self.noauth = self.itakaglobals.headhtml + self.configuration['html']['authfailure'] + self.itakaglobals.footerhtml

    def _promptAuth(self):
        """
        Prompt the authorization dialog on the browser.
        """

        self.request.setHeader('WWW-Authenticate', 'Basic realm="Itaka Screenshot Server"')
        self.request.setResponseCode(http.UNAUTHORIZED)
        self.request.setHeader('Content-Type', self.type)
        self.request.setHeader('Connection', 'close')
        self.request.setHeader('Content-Length', str(len(self.noauth)))

    def render(self, request):
        """
        Override twisted.static.Data render method. Render our static HTML.

        @type request: instance
        @param request: twisted.web.server.Request instance.
        """
        
        # Get up to date configuration values everytime there is a request
        self.configuration = self.gui.configuration

        self.request = request
        self.ip = self.request.getClientIP()
        self.time = datetime.datetime.now()

        if self.configuration['server']['authentication']:
            self._promptAuth()
            self.username = self.request.getUser()
            self.password = self.request.getPassword()
           
            if not self.username and not self.password:
                self.gui.log.failure(('RootResource', 'render'), ('Client provided empty username and password', 'Client %s provided empty username and password' % (self.ip)), 'WARNING')
                self._promptAuth()
            else:
                if self.username != self.configuration['server']['username'] or self.password != self.configuration['server']['password']:
                    self.gui.log.failure(('RootResource', 'render'), ('Client provided incorrect username and password', 'Client %s provided incorrect username and password: %s:%s' % (self.ip, self.username, self.password)), 'WARNING')
                    self._promptAuth()
                elif self.username == self.configuration['server']['username'] and self.password == self.configuration['server']['password']:
                    self.request.setResponseCode(http.OK)
                    self.request.setHeader('Content-Type', self.type)
                    self.request.setHeader('Connection', 'close')
                    self.request.setHeader('Content-Length', str(len(self.data)))
                    return self.data
        else:
            self.request.setHeader('Content-Type', self.type)
            self.request.setHeader('Connection', 'close')
            self.request.setHeader('Content-Length', str(len(self.data)))
            return self.data

        # No auth given
        return self.noauth

class ScreenshotResource(resource.Resource):
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
        self.ip = self.request.getClientIP()
        self.time = datetime.datetime.now()

        if (self.request.uri == "/screenshot"):
            try:
                self.shotFile = self.screenshot.take_screenshot()
            except error.ItakaScreenshotError:
                return
            
            self.request.setHeader('Content-Type', "image/" + self.configuration['screenshot']['format'])
            self.request.setHeader('Content-Length', str(len(self.shotFile)))
            self.request.setHeader('Connection', 'close')

            self.counter += 1

            if self.configuration['server']['notify'] and self.itakaglobals.notifyavailable:
                import pynotify
                uri = "file://" + (os.path.join(self.itakaglobals.image_dir, "itaka-take.png")) 

                n = pynotify.Notification("Screenshot taken", 
                "%s requested screenshot"
                % (self.ip, self.counter), uri)

                n.set_timeout(1500)
                n.attach_to_status_icon(self.gui.statusIcon)
                n.show()

            self.gui.update_gui(self.counter, self.ip, self.time)

            return open(self.shotFile, 'rb').read()
