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

""" Itaka console handling engine """

import config as iconfig

class Console:
    """ Console I/O handler organized by message type. Also handle GUI logging when passed an instance. """

    def __init__(self, ginstance=False):
        """ Init console handler with a GUI instance. """
        if ginstance: self.igui = ginstance
        print "[*] Itaka %s starting up..." % (iconfig.version)

    def __del__(self):
        """ Destructor. """
        print "[*] Itaka shutting down..."

    def msg(self, message, gui=False):
        """ Message handler. """
        # The gui argument is for the FTP method. It couples the console logger with the GUI logger.
        # In the Twisted method, logging is done by its engine.
        # Note the peculiar syntax of the argument you must pass to logger.
        # A dict with the first key being 'message', coupled with a str()'ed tuple'd message.
        print "[*] %s" % (message)
        if gui: self.igui.logger({'message': [str(message)]})

    def warn(self, caller, message, gui=False):
        """ Warning handler. """
        self.array = ".".join(caller)
        print "[*] WARNING: %s: %s" % (self.array, message)
        if gui: self.igui.logger({'message': [str("[*] ERROR: %s: %s" % (self.array, message))]})		

    def debug(self, caller, message, gui=False):
        """ Debug handler. """
        self.array = ".".join(caller)
        print "[*] DEBUG: %s: %s" % (self.array, message)
        if gui: self.igui.logger({'message': [str("[*] ERROR: %s: %s" % (self.array, message))]})

    def error(self, caller, message, gui=False):
        """ Error handler. """
        self.array = ".".join(caller)
        print "[*] ERROR: %s: %s" % (self.array, message)
        if gui: self.igui.logger({'message': [str("[*] ERROR: %s: %s" % (self.array, message))]})
