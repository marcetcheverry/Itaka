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
        """ Initiate console handler with  configuration globals """
        print "[*] Itaka %s starting..." % (itakaglobals.version)

    def __del__(self):
        """ Quitting message """
        print "[*] Itaka shutting down..."

    def msg(self, message, gui=False):
        """ Message handler. 'gui' is an instance of the 'Gui' class for logging purposes """
        print "[*] %s" % (message)

        # Twisted takes a dict with the first key being 'message', coupled with a str()'ed tuple'd message.
        if gui: gui.logger({'message': [str(message)]})

    def warn(self, caller, message, gui=False):
        """ Warning handler. 'caller' is a list or tuple specifying the class and method were the event ocurred """
        self.array = ".".join(caller)
        print "[*] WARNING: %s: %s" % (self.array, message)
        if gui: gui.logger({'message': [str("[*] ERROR: %s: %s" % (self.array, message))]})		

    def error(self, caller, message, gui=False):
        """ Error handler. 'caller' is a list or tuple specifying the class and method were the event ocurred """
        self.array = ".".join(caller)
        print "[*] ERROR: %s: %s" % (self.array, message)
        if gui: gui.logger({'message': [str("[*] ERROR: %s: %s" % (self.array, message))]})

    def debug(self, caller, message, gui=False):
        """ Debug handler. 'caller' is a list or tuple specifying the class and method were the event ocurred """
        self.array = ".".join(caller)
        print "[*] DEBUG: %s: %s" % (self.array, message)
        if gui: gui.logger({'message': [str("[*] ERROR: %s: %s" % (self.array, message))]})
