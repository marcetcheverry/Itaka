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

""" Itaka console output and logging engine """

class Console:
    """ Console I/O handler organized by message type. Also handle GUI logging when passed an instance """

    def __init__(self, itakaglobals):
        """ Initiate console handler with configuration globals """
        self.itakaglobals = itakaglobals
        if self.itakaglobals.output['normal']: print "[*] Itaka %s starting..." % (itakaglobals.version)

    def __del__(self):
        """ Quitting message """
        if self.itakaglobals.output['normal']: print "[*] Itaka shutting down..."

    def msg(self, message, gui=False, eventslog=True, detailedmessage=False, icon=None):
        """ Message handler. 'gui' is an instance of the 'Gui' class for logging purposes. 'eventslog' is a boolean to spcecify if the log message will go to the events log. 'detailedmessage' is to specify that only the simple mesage will go to the events log. 'icon' is gtk.stock_icon string for the gui event log """
        if self.itakaglobals.output['normal']: 
            if detailedmessage:
                print "[*] %s" % (message[1])
            else:
                print "[*] %s" % (message)

        # twisted takes a dict with the first key being 'message', coupled with a str()'ed tuple'd message.
        if gui: 
            if detailedmessage:
                gui.logger({'message': [message[0], message[1]]}, False, None, eventslog, detailedmessage, icon)
            else:
                gui.logger({'message': [message]}, False, None, eventslog, detailedmessage, icon)

    def warn(self, caller, message, gui=False, eventslog=False, icon=None):
        """ Warning handler. 'caller' is a list or tuple specifying the class and method were the event ocurred. Arguments are inherited from msg() """
        self.array = ".".join(caller)
        if self.itakaglobals.output['normal']: 
            print "[*] WARNING: %s: %s" % (self.array, message)
        if gui: 
            gui.logger({'message': [str(message), str("WARNING: %s: %s" % (self.array, message))]}, True, 'warning', eventslog, False, icon)		

    def error(self, caller, message, gui=False, eventslog=False, icon=None):
        """ Error handler. 'caller' is a list or tuple specifying the class and method were the event ocurred. Arguments are inherited from msg() """
        self.array = ".".join(caller)
        if not self.itakaglobals.output['quiet']:
            print "[*] ERROR: %s: %s" % (self.array, message)
        if gui:
            # Show the window and its widgets, set the status icon blinking timeout
            if not gui.window.get_property("visible"):
                gui.window.present()
                gui.statusicon_blinktimeout()
                gui.window.move(gui.window_position[0], gui.window_position[1])

            gui.expander.set_expanded(True)
            gui.expander.set_sensitive(True)
            # Stop the server
            if gui.server_listening:
                gui.startstop(None, "stop", True)

            gui.logger({'message': [str(message), str("ERROR: %s: %s" % (self.array, message))]}, True, 'error', eventslog, False, icon)

    def debug(self, caller, message, gui=False, eventslog=False, icon=None):
        """ Debug handler. 'caller' is a list or tuple specifying the class and method were the event ocurred. Arguments are inherited from msg() """
        self.array = ".".join(caller)
        if self.itakaglobals.output['debug']: 
            print "[*] DEBUG: %s: %s" % (self.array, message)
        if gui: 
            gui.logger({'message': [str(message), str("DEBUG: %s: %s" % (self.array, message))]}, True, 'debug', eventslog, False, icon)
