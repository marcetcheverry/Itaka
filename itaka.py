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

""" Itaka core """

import sys, traceback

validarguments = ('-h', '--help', '-v', '--version', '-r', '--revision', '-d', '--debug')
arguments = sys.argv

# Only one option at a time
if len(arguments) >= 2 and ((arguments[-1] not in validarguments) or (arguments[-1] in (validarguments[0], validarguments[1]))):
    print """Usage:
  %s [OPTION...]

  Help Options:
  -h, --help\t\t\t\tShow help options
  -v, --version\t\t\t\tShow Itaka version
  -r, --revision\t\t\tShow Itaka revision

  Application Options:
  -d, --debug\t\t\t\tStart in debug mode""" % arguments[0]
    sys.exit(1)

# Itaka core modules
try:
    # Initiate our Console and Configuration engines
    import console
    import config as itakaglobals
    configinstance = itakaglobals.ConfigParser(arguments)
    configinstance.load()

    try:
        # Initiate console with a reference to our global configuration values
        console = console.Console(itakaglobals)
    except:
        print "[*] ERROR: Could not initiate Console engine"
        traceback.print_exc()
        sys.exit(1)

    import uigtk as igui
except ImportError:
    print "[*] ERROR: Failed to import Itaka modules"
    if itakaglobals.output['debug']:
        traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    if len(arguments) >= 2: 
        if (arguments[-1] in (validarguments[2], validarguments[3])):
            print itakaglobals.version
            sys.exit(0)
        if (arguments[-1] in (validarguments[4], validarguments[5])):
            print itakaglobals.revision
            sys.exit(0)

    try:
        gui = igui.Gui(console, (itakaglobals, configinstance))
        gui.main()
    except Exception, e:
        console.failure(('Itaka', 'core'), "Could not initiate GUI: %s" % (e), 'ERROR')
        if itakaglobals.output['debug']:
            traceback.print_exc()
        sys.exit(1)
