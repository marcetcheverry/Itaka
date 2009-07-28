#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Itaka is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
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
# Copyright 2003-2009 Marc E.
# http://itaka.jardinpresente.com.ar
#
# $Id$

""" Itaka exceptions """

class ItakaError(Exception):
    """
    Base class for all Itaka errors
    """

    def __init__(self, value):
        """
        Constructor

        @type value: str
        @param value: Exception value
        """

        self.value = value

    def __str__(self):
        """
        String representation

        @rtype: str
        @return: String representation of Exception value
        """

        return repr(self.value)


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

