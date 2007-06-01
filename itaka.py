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
#
# $Id$ 

""" Itaka main loader core """

import sys, os, traceback 

# Itaka core modules
try:
    # Initiate the configuration engine.
    import config as iconfig
    configinstance = iconfig.ConfigParser()
    configinstance.load()

    import uigtk as igui
except ImportError:
    print "[*] ERROR: Failed to import Itaka modules."
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    try:
        gui = igui.Gui(configinstance)
        gui.main()
    except AttributeError:
        print "[*] ERROR: Could not initiate GUI."
        traceback.print_exc()
        sys.exit(1)
