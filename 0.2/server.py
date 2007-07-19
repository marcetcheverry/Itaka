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

        # Also we create our unique authentication handler this keeps track if the user authenticated or not
        self.authresource = AuthenticatedResource(self.gui)
        self.root = RootResource(self.gui, self.authresource, self.itakaglobals.headhtml + self.configuration['html']['html'] + self.itakaglobals.footerhtml)
        self.add_child_to_resource('root', '', self.root)
        self.add_child_to_resource('root', 'screenshot', ScreenshotResource(self.gui, self.authresource))
        self.create_site(self.root)

class AuthenticatedResource:
    """
    Helper object to handle authentication for Resources.
    Please read RFC 2617 to understand the HTTP Authentication process
    """

    def __init__(self, gui_instance):
        """ 
        Constructor that inherits code from resource.Resource->static.Data

        @type gui_instance: instance
        @param gui_instance: An instance of our L{Gui} class
        """

        self.gui = gui_instance
        self.configuration = self.gui.configuration
        self.itaka_globals = self.gui.itakaglobals
        self.noauth = self.itaka_globals.headhtml + self.configuration['html']['authfailure'] + self.itaka_globals.footerhtml
        self.request_data_set = False
        self.authenticated = False

    def set_request_data(self, data, size, type, session_end=False):
        """
        Set the information about the data we are handling


        @type data: string
        @param data: The data to be displayed

        @type size: string
        @param size: A string for Content-lenght

        @type type: str
        @param type: The type of data we are serving

        @type session_end: bool
        @param session_end: Whether this request is the last of a session. This deauthenticates the session.
        """

        self.request_data_set = True
        self.data = data
        self.size = size
        self.type = type
        self.session_end = session_end

    def _prompt_auth(self):
        """
        Prompt the authorization dialog on the browser
        """

        self.authenticated = False
        self.request.setHeader('WWW-Authenticate', 'Basic realm="Itaka Screenshot Server"')
        self.request.setResponseCode(http.UNAUTHORIZED)
        self.request.setHeader('Content-Type', 'text/html; charset=UTF-8')
        self.request.setHeader('Content-Length', str(len(self.noauth)))
        self.request.setHeader('Connection', 'close')

    def authenticate(self, request):
        """
        Main handler for authenticated objects.

        @type request: instance
        @param request: twisted.web.server.Request instance

        @rtype: bool
        @return: Whether the user authenticated sucessfully. 
        """

        # Get up to date configuration values everytime there is a request
        self.configuration = self.gui.configuration

        self.request = request
        self._prompt_auth()
        self.username = self.request.getUser()
        self.password = self.request.getPassword()
        self.ip = self.request.getClientIP()
        self.time = datetime.datetime.now()
       
        if not self.username and not self.password:
            self.gui.log.failure(('AuthenticatedResource', 'render'), ('Client provided empty username and password', 'Client %s provided empty username and password' % (self.ip)), 'WARNING')
            self._prompt_auth()
        else:
            if self.username != self.configuration['server']['username'] or self.password != self.configuration['server']['password']:
                self.gui.log.failure(('AuthenticatedResource', 'render'), ('Client provided incorrect username and password', 'Client %s provided incorrect username and password: %s:%s' % (self.ip, self.username, self.password)), 'WARNING')
                self._prompt_auth()
            elif self.username == self.configuration['server']['username'] and self.password == self.configuration['server']['password']:
                self.authenticated = True
        return self.authenticated

    def return_object_data(self):
        """
        Returns the data passed by set_request_data() or the default forbidden string if authentication failed.

        @rtype: str
        @return: self.data or self.noauth
        """

        if self.request_data_set and self.authenticated:
            self.request.setResponseCode(http.OK)
            self.request.setHeader('Content-Type', self.type)
            self.request.setHeader('Content-Length', self.size)
            self.request.setHeader('Connection', 'close')
            # Deauthenticate if it's the screenshot (last object request)
            if self.session_end:
                self.authenticated = False
            self.request_data_set = True
            return self.data
        else:
            # No authentication given
            return self.noauth

class RootResource(static.Data):
    """
    Main resource with authentication support.

    Please read RFC 2617 to understand the HTTP Authentication process.
    """

    def __init__(self, guiinstance, auth_instance, data, type='text/html; charset=UTF-8'):

        """ 
        Constructor that inherits code from resource.Resource->static.Data.

        @type guiinstance: instance
        @param guiinstance: An instance of our L{Gui} class.

        @type auth_instance: AuthenticatedResource
        @param auth_instance: An instance of our L{AuthenticatedResource} class

        @type html: string
        @param html: The HTML to be displayed.

        @type type: str
        @param type: The type of data we are serving.
        """

        self.gui = guiinstance
        self.auth = auth_instance
        self.console = self.gui.console
        self.itakaglobals = self.gui.itakaglobals
        self.configuration = self.gui.configuration

        # Inherited from the actual code of Twisted's static.Data
        self.children = {}
        self.data = data
        self.size = str(len(self.data))
        self.type = type

    def render(self, request):
        """
        Override twisted.static.Data render method. Render our static HTML.

        @type request: instance
        @param request: twisted.web.server.Request instance.
        """
        
        # Get up to date configuration values everytime there is a request
        self.configuration = self.gui.configuration
        self.request = request

        if self.configuration['server']['authentication']:
            if self.auth.authenticate(self.request):
                self.auth.set_request_data(self.data, self.size, self.type)
            return self.auth.return_object_data()
        else:
            self.request.setHeader('Content-Type', self.type)
            self.request.setHeader('Content-Length', self.size)
            self.request.setHeader('Connection', 'close')
            return self.data

class ScreenshotResource(resource.Resource):
    """ 
    Handle server requests and call for a screenshot.
    """

    def __init__(self, guiinstance, auth_instance):
        """ 
        Constructor.

        @type guiinstance: instance
        @param guiinstance: An instance of our L{Gui} class.

        @type auth_instance: AuthenticatedResource
        @param auth_instance: An instance of our L{AuthenticatedResource} class
        """

        self.gui = guiinstance
        self.auth = auth_instance
        self.console = self.gui.console
        self.itakaglobals = self.gui.itakaglobals
        self.screenshot = screenshot.Screenshot(self.gui)
        
        #: Server hits counter
        self.counter = 0

    def get_screenshot(self):
        """
        Takes a screenshot and notifies the GUI.
        """

        self.ip = self.request.getClientIP()
        self.time = datetime.datetime.now()

        try:
            self.shot_file = self.screenshot.take_screenshot()
        except error.ItakaScreenshotError, e:
            raise error.ItakaScreenshotError, e

        self.data = open(self.shot_file, 'rb').read()
        self.size = len(self.data)
        print self.size
        self.counter += 1

        if self.configuration['server']['notify'] and self.itaka_globals.notify_available:
            import pynotify
            uri = "file://" + (os.path.join(self.itaka_globals.image_dir, "itaka-take.png")) 

            n = pynotify.Notification('Screenshot taken', '%s requested screenshot' % (self.ip), uri)

            n.set_timeout(1500)
            n.attach_to_status_icon(self.gui.statusIcon)
            n.show()
        self.gui.update_gui(self.counter, self.ip, self.time)

    def render_GET(self, request):
        """
        Handle GET requests for screenshot

        @type request: instance
        @param request: twisted.web.server.Request instance
        """

        # Get up to date configuration values everytime there is a request
        self.configuration = self.gui.configuration
        self.request = request
        self.type = "image/" + self.configuration['screenshot']['format']

        if self.configuration['server']['authentication']:
            if self.auth.authenticated or self.auth.authenticate(self.request):
                try:
                    self.get_screenshot()
                except error.ItakaScreenshotError:
                    return
                self.auth.set_request_data(self.data, self.size, self.type, True)
            return self.auth.return_object_data()
        else:
            try:
                self.get_screenshot()
            except error.ItakaScreenshotError:
                return
            self.request.setHeader('Content-Type', self.type)
            self.request.setHeader('Content-Length', self.size)
            self.request.setHeader('Connection', 'close')
            return self.data
