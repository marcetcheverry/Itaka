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
# Copyright 2003-2007 Marc E. <santusmarc@gmail.com>.
# http://itaka.jardinpresente.com.ar
#
# $Id: itaka.py 124 2007-06-06 05:39:18Z marc $ 

""" Itaka main loader core """

import sys, traceback

# Itaka core modules
try:
    # Initiate our Console and Configuration engines
    import console
    import config as itakaglobals
    configinstance = itakaglobals.ConfigParser()
    configinstance.load()

    try:
        # Initiate console with a reference to our global configuration values
        console = console.Console(itakaglobals)
    except AttributeError:
        print "[*] ERROR: Could not initiate Console engine."
        traceback.print_exc()
        sys.exit(1)

    import uigtk as igui

except ImportError:
    print "[*] ERROR: Failed to import Itaka modules."
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    try:
        gui = igui.Gui(console, (itakaglobals, configinstance))
        gui.main()
    except AttributeError:
        console.error(('Itaka', 'core'), "Could not initiate GUI")
        traceback.print_exc()
        sys.exit(1)
