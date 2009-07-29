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

""" Itaka configuration engine """

__version__ = '0.3'
__revision__ = '$Rev$'

import os
import platform
import sys
import ConfigParser
import shutil
import traceback

#: Availability of libnotify
notify_available = False

try:
    import pynotify
    notify_available = True

    if not pynotify.init('Itaka'):
        print_w(_('Pynotify module is failing, disabling notifications'))
        notify_available = False
except ImportError:
    print_w(_('Pynotify module is missing, disabling notifications'))
    notify_available = False

config_instance = ConfigParser.ConfigParser()
image_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'share/images/')
sound_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'share/sounds/')
system = os.name
# We need something more specific 
platform = platform.system()

#: Minimum screen height to display all panes of Itaka
min_screen_height = 800

#: To be changed on install to specify where the installed files actually are
image_prefix = '/usr/share/itaka/images/'
if os.path.exists(image_prefix):
    image_dir = image_prefix

if not os.path.exists(image_dir):
    print_e(_('Could not find images directory %s' % (image_dir)))
    sys.exit(1)

#: Save path for screenshots (system-specific specified later on)
save_path = os.getcwd()

""" Console output verbosity
'normal' is for all normal operation mesages and warnings (not including errors)
'debug' is for all messages through self.console.debug
'quiet' is to quiet all errors and warnings. (totally quiet is in conjunction 
with 'normal' = False, which quiets normal messages too)
"""
console_verbosity = {'normal': False, 'debug': False, 'quiet': False}

#: Globally acessable configuration values
configuration_values = {}

# Second best choice, TMP/TEMP on most systems
save_path = os.environ.get('TMP') or os.environ.get('TEMP')

# Try APPDATA on Windows or $HOME on POSIX
if (system == 'nt'):
    if os.environ.get('APPDATA'):
                save_path = os.path.join(os.environ.get('APPDATA'), 'itaka')
    elif os.environ.get('HOME'):
                save_path = os.path.join(os.environ.get('HOME'), 'itaka')
else:
    if os.environ.get('HOME'):
        save_path = os.path.join(os.environ.get('HOME'), '.itaka')

print save_path
#: Default HTML headers and footers for the server.
# Putting <meta http-equiv="Refresh" content="5; url=/"> is very useful for debugging
head_html = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<link rel="icon" href="/favicon.ico" type="image/x-icon">
<title>Itaka</title>
</head>
<body>
<div id="main">
'''

footer_html = '''
</div>
</body>
</html>'''

class ConfigParser:
    """
    Itaka configuration engine
    """

    def __init__(self, arguments=1):
        """
        Configuration engine constructor. It also handles whether the
        L{console_verbosity} setting is set to debug.

        @type arguments: tuple
        @param arguments: A tuple of sys.argv 
        """

        if len(arguments) > 1 and arguments[-1] in ('-d', '--debug'):
            global console_verbosity
            console_verbosity = {'normal': True, 'debug': True, 'quiet': False}
            print_m(_('Initializing in debug mode'))

        #: Default configuration sections and values
        # WARNING: Don't forget to update configuration_dict in uigtk.py if you change this! 
        self.default_options = ( 
                {'server': (
                    ('port', 8000), ('authentication', False),
                    ('username', 'itaka'), ('password', 'password'),
                    ('notify', notify_available)
                )},

                {'screenshot': (
                    ('format', 'jpeg'), ('quality', 30), ('path', save_path),
                    ('currentwindow', False), ('scale', False),
                    ('scalepercent', 100)
                )},
                
                {'log': (
                    ('logtimeformat', '[%d/%b/%Y %H:%M:%S]'),
                    ('logfile', '~/.itaka/access.log')
                )},
                
                {'html': (
                    ('html', '<img src="screenshot" alt="If you are seeing this message it means there was an error in Itaka or you are using a text-only browser.">'),
                    ('authfailure', '<p><strong>Sorry, but you cannot access this resource without authorization.</strong></p>')
                )}
        )

    def load(self):
        """
        Set up and load configuration

        @rtype: dict
        @return: Dictionary of configuration values.
        """

        self.config_file = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "itaka.conf")

        global configuration_values
        configuration_values = {}

        # Check routine
        if system in ('posix'):
            if not (os.path.exists(os.path.join(os.environ['HOME'], '.itaka/itaka.conf'))):
                self.create(os.path.join(os.environ['HOME'], '.itaka/itaka.conf'))
            else:
                self.config_file = os.path.join(os.environ['HOME'], '.itaka/itaka.conf')
        elif (system == 'nt'):
            if not (os.path.exists(os.path.join(os.environ['APPDATA'], 'Itaka/config.ini'))):
                self.create(os.path.join(os.environ['APPDATA'], 'Itaka/config.ini'))
            else:
                self.config_file = os.path.join(os.environ['APPDATA'], 'Itaka/config.ini')
        else:
            # Generic path
            if not os.path.exists(self.config_file): 
                self.create(self.config_file)

        # Read and assign values from the configuration file 
        try:
            config_instance.read(self.config_file)
            if console_verbosity['normal']: 
                print_m(_('Loaded configuration %s') % (self.config_file))

        except:
            if console_verbosity['normal']: print_e(_('Could not read configuration file (%s)' % (self.config_file)))
            if console_verbosity['debug']: traceback.print_exc()

        # Get values as a dict and return it
        for section in config_instance.sections():
            configuration_values[section] = dict(config_instance.items(section))
            # Convert 'False' and 'True' into booleans, and numbers into ints
            # Add config options that are not there
            for option, value in configuration_values[section].iteritems():
                if value.strip() == 'True':
                    configuration_values[section][option] = True
                elif value.strip() == 'False':
                    configuration_values[section][option] = False
                elif value.isdigit():
                    configuration_values[section][option] = int(value)

        # Compare it to our default configuration set, to see if there is anything missing
        # This is useful for updates, and corrupted files.
        # NOTE: The setting of values[section][key] here is purely pragmatical, so we
        # dont have to reload
        brokenwarning = False
        for configdict in self.default_options:
            for section in configdict:
                if not configuration_values.has_key(section):
                    if not console_verbosity['quiet'] and not brokenwarning: 
                        print_w(_('Upgrading configuration file.'))
                        brokenwarning = True
                    config_instance.add_section(section)
                    configuration_values[section] = {}
                    for keyset in configdict[section]:
                        key, val = keyset
                        self.update(section, key, val)
                        configuration_values[section][key] = val
                else:
                    # Check if all the key:vals are in the section
                    for keyset in configdict[section]:
                        key, val = keyset
                        if not configuration_values[section].has_key(key):
                            if not console_verbosity['quiet'] and not brokenwarning:
                                print_w(_('Detected old or broken configuration file. Fixing'))
                            self.update(section, key, val)
                            configuration_values[section][key] = val
                            brokenwarning = True
        return configuration_values

    def save(self, valuesdict):
        """ 
        Saves a dictionary containing the configuration

        @type valuesdict: dict
        @param valuesdict: Dictionary of configuration
        """

        # Unpack the dict into section, option, value
        for section in valuesdict.keys():
            for key, value in valuesdict[section].items():
                config_instance.set(section, key, value)

        # Save
        try:
            config_instance.write(open(self.config_file, 'w'))
            if console_verbosity['normal']: print_m(_('Saving configuration'))	
        except:		
            if not console_verbosity['quiet']: print_e(_('Could not write configuration file %s' % (self.config_file)))
            if console_verbosity['debug']: traceback.print_exc()

    def update(self, section, key, value):
        """ 
        Update a specific key's value

        @type section: str
        @param section: String of the section of the key to update
        @type key: str
        @param key: String of the key to update
        @type value: str/int/bool
        @param value: Value of the key to update
        """	

        config_instance.set(section, key, value)

        try:
            config_instance.write(open(self.config_file, 'w'))
            if console_verbosity['debug']: print_m(_("Updating configuration key '%(key)s' to '%(value)s'") % {'key': key, 'value': value})
        except:
            if not console_verbosity['quiet']: print_e(_('Could not write configuration file %s' % (self.config_file)))
            if console_verbosity['debug']: traceback.print_exc()

    def create(self, path):
        """
        Create a configuration file from default values

        @type path: str
        @param path: Path to the configuration file
        """

        if console_verbosity['normal']: print_m(_('Creating default configuration'))

        # Set default sections and options
        for configdict in self.default_options:
            for section in configdict:
                config_instance.add_section(section)
                for keyset in configdict[section]:
                    key, val = keyset
                    config_instance.set(section, key, val)

        if not (os.path.exists(os.path.dirname(path))):
            shutil.os.mkdir(os.path.dirname(path))

        try:
            config_instance.write(open(path, 'w'))
        except:
            if not console_verbosity['quiet']: print_e(_('Could not write configuration file %s' % (path)))
            if console_verbosity['debug']: traceback.print_exc()

        self.config_file = path	

