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

""" Itaka console output and logging engine """

import __builtin__

# Global output functions
def print_m(string):
    """
    Print wrapper.

    @type str: str
    @param str: Message
    """
    
    print '[*] %s' % (str(string))

def print_warning(string):
    """
    Print wrapper.

    @type str: str
    @param str: Message
    """

    print_m('WARNING: %s' % (string))

def print_error(string):
    """
    Print wrapper.

    @type str: str
    @param str: Message
    """

    print_m('ERROR: %s' % (string))

def print_debug(string):
    """
    Print wrapper.

    @type str: str
    @param str: Message
    """

    print_m('DEBUG: %s' % (string))

# Register them for global use
__builtin__.print_m = print_m
__builtin__.print_error = print_error
__builtin__.print_warning = print_warning

class BaseMessage:
    """
    Base class for console output.
    """

    def __init__(self, message):
        """
        Constructor.

        @type message: str
        @param message: The message to print on the Console
        """

        self.message = message
        print_m(self.message)

class BaseFailureMessage(BaseMessage):
    """
    Base class for failure messages.
    """

    def __init__(self, debug, caller, message, type):
        """
        Constructor

        @type debug: bool
        @param debug: Whether the L{caller} arguments will be printed

        @type caller: tuple
        @param caller: Specifies the class and method were the failure ocurred

        @type message: str
        @param message: The message to print

        @type type: str
        @param type: The type of failure: 'WARNING', 'ERROR', 'DEBUG'
        """

        self.caller = '.'.join(caller)
        self.message = message
        self.debug = debug
        self.type = type

        if self.debug:
            self.message = ' '.join((self.caller, self.message))

        print '[*] %s: %s' % (str(self.type), str(self.message))
                

class Console:
    """
    Console I/O handler organized by message type. Also handle GUI logging when passed an instance
    """

    def __init__(self, itakaglobals):
        """
        Constructor for console output handler
        
        @type itakaglobals: module
        @param itakaglobals: Configuration module
        """

        self.itakaglobals = itakaglobals
        if self.itakaglobals.output['normal']: 
            BaseMessage(_('Itaka %s starting') % (itakaglobals.version))
            
    def __del__(self):
        """
        Destructor
        """
        
        if self.itakaglobals.output['normal']: 
            BaseMessage(_('Itaka shutting down'))

    def message(self, message):
        """
        Message handler
        
        @type message: str
        @param message: Message to print to the console
        """
        
        if self.itakaglobals.output['normal']:
            BaseMessage(message)

    def failure(self, caller, message, failuretype='ERROR'):
        """
        Failure handler abstract

        @type caller: tuple
        @param caller: Specifies the class and method were the warning ocurred

        @type message: str
        @param message: Message to print to the console

        @type failuretype: str
        @param failuretype: What kind of failure it is, either 'ERROR' (default), 'WARNING' or 'DEBUG'
        """

        if failuretype == 'ERROR':
            if not self.itakaglobals.output['quiet']:
                BaseFailureMessage(self.itakaglobals.output['quiet'], caller, message, failuretype)

        elif failuretype == 'WARNING':
            if self.itakaglobals.output['normal']:
                BaseFailureMessage(self.itakaglobals.output['normal'], caller, message, failuretype)

        elif failuretype == 'DEBUG':
            if self.itakaglobals.output['debug']:
                BaseFailureMessage(self.itakaglobals.output['debug'], caller, message, failuretype)

