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

import sys
import os
import traceback
import gettext
import locale
import __builtin__

locale.setlocale(locale.LC_ALL, '')
__builtin__._ = gettext.gettext

# Itaka modules
try:
    import console
    import config as itaka_globals
    import uigtk as igui
except ImportError:
    print '[*] ERROR: Failed to import Itaka modules'
    traceback.print_exc()
    sys.exit(1)

#: Locales directory
locale_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'locale/')

#: To be changed on install to specify where the installed files actually are
locale_prefix = "/usr/share/locale/"

if os.path.exists(locale_prefix):
    locale_dir = locale_prefix

# See if our locales are there before starting
if not os.path.exists(locale_dir):
    print_warning(_('Could not find locale directory %s, not using locales.' % (locale_dir)))
else: 
    gettext.bindtextdomain('itaka', locale_dir)
    gettext.textdomain('itaka')

valid_arguments = ('-help', '-debug')
arguments = sys.argv

# Only one option at a time
if len(arguments) > 2 or (len(arguments) == 2 and arguments[-1] \
        not in valid_arguments or arguments[-1] == valid_arguments[0]):
    print _('Usage: %s (-debug|-help)') % (arguments[0])
    sys.exit(1)
elif len(arguments) == 1:
    arguments = None

try:
    # Initiate our Console and Configuration engines
    config_instance = itaka_globals.ConfigParser(arguments)
    config_instance.load()

    try:
        # Initiate console with a reference to our global configuration values,
        # not the user's configuration
        console_instance = console.Console(itaka_globals)
    except:
        print_error(_('Could not initiate Console engine'))
        traceback.print_exc()
        sys.exit(1)
except:
    print_error(_('Could not initiate Configuration engine'))
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    try:
        gui = igui.Gui(console_instance, (itaka_globals, config_instance))
        gui.main()
    except Exception, e:
        console_instance.failure(('Itaka', 'core'), _('Could not initiate GUI: %s') % (e), 'ERROR')
        if itaka_globals.console_verbosity['debug']:
            traceback.print_exc()
        sys.exit(1)
