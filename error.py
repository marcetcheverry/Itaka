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

""" Itaka error handling exception definitions """

class ItakaError(Exception):
    """
    Base class for all Itaka Errors
    """

    def __init__(self, message):
        """
        Constructor

        @type message: str
        @param message: Exception message
        """

        self.message = message

    def __str__(self):
        """
        String representation

        @rtype: str
        @return: String representation of Exception message
        """

        return repr(self.message)

class ItakaServerError(ItakaError):
    """
    Exception raised by server methods
    """
    pass

class ItakaServerErrorCannotListen(ItakaServerError):
    """
    Exception raised by server methods
    """
    pass

class ItakaScreenshotError(ItakaError):
    """
    Exception raised by screenshooting methods
    """
    pass

class ItakaScreenshotErrorWmHints(ItakaScreenshotError):
    """
    Exception raised by screenshooting methods
    """
    pass

class ItakaScreenshotErrorActiveDesktop(ItakaScreenshotError):
    """
    Exception raised by screenshooting methods
    """
    pass
    
class ItakaSaveScreenshotError(ItakaScreenshotError):
    """
    Exception raised by screenshooting methods
    """
    pass
