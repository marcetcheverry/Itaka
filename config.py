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
# Copyright 2003-2007 Marc E. <santusmarc_at_gmail.com>.
# http://itaka.jardinpresente.com.ar
#
# $Id$

""" Itaka Configuration Parser and Engine """

# It works by the core initiating the main instance, and the
# modules accessing the global values variables set up by the initation.

import ConfigParser, os, sys, shutil, traceback

# Set up instance
config = ConfigParser.ConfigParser()

# Set up global variables
local_config = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "itaka.conf")

# Version (do not change)
version = "0.1.1"
revision = "$Rev$"

# Check system or specify per os.name standard
system = os.name

# Support darwin specific stuff
platform = None
if (sys.platform.startswith("darwin")): platform = "darwin"

# Itaka images/ directory
# prefix will be changed on install to specify where the installed files are
image_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "share/images/")
prefix = "/usr/share/itaka/images/"
if os.path.exists(prefix):
    image_dir = prefix

# See if our images are there before starting
if not os.path.exists(image_dir):
    print "[*] ERROR: Could not find images directory '%s'" % (image_dir)
    sys.exit(1)

#: Save path for screenshots (system-specific specified later on)
save_path = os.getcwd()

if os.environ.get('HOME') is not None:
    save_path = os.path.join(os.environ.get('HOME'), ".itaka")
else:
    save_path = os.environ.get('TMP') or os.environ.get('TEMP')

# Use notifications where libnotify is available
notifyavailable = False
if system == "posix" and platform != "darwin":
    try:
        import pynotify
        notifyavailable = True

        if not pynotify.init("Itaka"):
            print "[*] WARNING: Pynotify module is failing, disabling notifications"
            notifyavailable = False
    except ImportError:
        print "[*] WARNING: Pynotify module is missing, disabling notifications"
        notifyavailable = False

#: Console output setting
# 'normal' is for all normal operation mesages and warnings (not including errors)
# 'debug' is for all messages through self.console.debug
# 'quiet' is to quiet all errors. (totally quiet is in conjunction with 'normal')
output = {'normal': False, 'debug': False, 'quiet': False}

#: User's configuration values 
values = {}

class ConfigParser:
    """
    Itaka configuration engine.
    """
    def __init__(self, arguments=None):
        """
        Configuration engine initiation. It also handles whether the L{output} setting is set to print everything to the console.

        @type arguments: tuple
        @param arguments: A tuple of sys.argv 
        """
        if arguments is not None and len(arguments) > 1 and arguments[-1] == "-debug":
            global output
            output = {'normal': True, 'debug': True, 'quiet': False}
            print "[*] Initializing in debug mode..."

    def load(self):
        """
        Set up and load configuration

        @rtype: dict
        @return: Dictionary of configuration values.
        """

        self.configfile = None

        # Check routine
        if system in ("posix"):
            if not (os.path.exists(os.path.join(os.environ['HOME'], ".itaka/itaka.conf"))):
                self.create(os.path.join(os.environ['HOME'], ".itaka/itaka.conf"))
            else:
                self.configfile = os.path.join(os.environ['HOME'], ".itaka/itaka.conf")
        elif (system == "nt"):
            if not (os.path.exists(os.path.join(os.environ['APPDATA'], "itaka/itaka.ini"))):
                self.create(os.path.join(os.environ['APPDATA'], "itaka/itaka.ini"))
            else:
                self.configfile = os.path.join(os.environ['APPDATA'], "itaka/itaka.ini")
        else:
            # Generic system/paths (using local)	
            if (os.path.exists(local_config)): 
                self.configfile = local_config
            else:	
                self.create(local_config)
        # Read and assign values from the configuration file 
        try:
            config.read(self.configfile)
            if output['normal']: print "[*] Read configuration (%s)" % (self.configfile)

        except:
            if output['normal']: print "[*] ERROR: Could not read configuration file (%s)" % (self.configfile)
            if output['debug']: traceback.print_exc()

        """ Retrieve values and return them as a dict."""
        global values
        values = {}
        # Get values as a dict and return it
        for section in config.sections():
            values[section] = dict(config.items(section))
            # Convert 'False' and 'True' into booleans, and numbers into ints
            for option, value in values[section].iteritems():
                if value.strip() == "True":
                    values[section][option] = True
                elif value.strip() == "False":
                    values[section][option] = False
                elif value.isdigit():
                    values[section][option] = int(value)
        return values

    def save(self, valuesdict):
        """ 
        Saves a dictionary containing the configuration.

        @type valuesdict: dict
        @param valuesdict: Dictionary of configuration.
        """

        # Unpack the dict into section, option, value
        for section in valuesdict.keys():
            for key, value in valuesdict[section].items():
                config.set(section, key, value)

        # Save
        try:
            config.write(open(self.configfile, 'w'))
            if output['normal']: print "[*] Saving configuration... "	
        except:		
            if not output['quiet']: print "[*] ERROR: Could not write configuration file %s" % (self.configfile)
            if output['debug']: traceback.print_exc()

    def update(self, section, key, value):
        """ 
        Update a specific key's value.
        
        @type section: str
        @param section: String of the section of the key to update.
        @type key: str
        @param key: String of the key to update.
        @type value: str/int/bool
        @param value: Value of the key to update.
        """	
        
        config.set(section, key, value)
        
        try:
            config.write(open(self.configfile, 'w'))
            if output['normal']: print "[*] Updating configuration key %s to %s" % (key, value)	
        except:
            if not output['quiet']: print "[*] ERROR: Could not write configuration file %s" % (self.configfile)
            if output['debug']: traceback.print_exc()

    def create(self, path):
        """
        Create a configuration file from default values.
        
        @type path: str
        @param path: Path to the configuration file.
        """
        
        # Create sections
        for section in ('server', 'screenshot', 'html'): config.add_section(section)

        if output['normal']: print "[*] Creating default configuration..."
        # Set default values
        config.set("server", "port", 8000)
        config.set("server", "notify", notifyavailable)

        config.set("screenshot", "format", "jpeg")
        config.set("screenshot", "quality", 30)
        config.set("screenshot", "path", save_path)
        config.set("screenshot", "currentwindow", False)
        config.set("screenshot", "scale", False)
        config.set("screenshot", "scalepercent", 50)

	config.set("html", "html", '<html><body><img src="screenshot" alt="If you are seeing this message it means there was an error in Itaka or you are using a text-only browser." border="0"></a></body</html>')

        # Check if the directory exists, if not create it
        # and write the config file with its variables
        if not (os.path.exists(os.path.dirname(path))):
            shutil.os.mkdir(os.path.dirname(path))

        try:
            config.write(open(path, 'w'))
        except:
            if not output['quiet']: print "[*] ERROR: Could not write configuration file %s" % (path)
            if output['debug']: traceback.print_exc()

        self.configfile = path		
