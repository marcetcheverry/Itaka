#! /usr/bin/env python
# -*- coding: utf8 -*-
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
# Copyright 2003-2007 Marc E.
# http://itaka.jardinpresente.com.ar
#
# $Id$ 

""" Itaka core """

import sys, traceback, gettext, locale, __builtin__
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain('itaka', 'i18n/')
gettext.textdomain('itaka')

__builtin__._ = gettext.gettext

validarguments = ('-help', '-debug')
arguments = sys.argv

# Only one option at a time
if len(arguments) > 2 or (len(arguments) == 2 and arguments[-1] not in validarguments or arguments[-1] == validarguments[0]):
    print _('Usage: %s (-debug|-help)') % (arguments[0])
    sys.exit(1)
elif len(arguments) == 1:
    arguments = None

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
        print_error(_('Could not initiate Console engine'))
        traceback.print_exc()
        sys.exit(1)

    import uigtk as igui
except ImportError:
    print_error(_('Failed to import Itaka modules'))
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    try:
        gui = igui.Gui(console, (itakaglobals, configinstance))
        gui.main()
    except Exception, e:
        console.failure(('Itaka', 'core'), _('Could not initiate GUI: %s') % (e), 'ERROR')
        if itakaglobals.output['debug']:
            traceback.print_exc()
        sys.exit(1)
