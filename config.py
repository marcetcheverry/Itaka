#!/usr/bin/env python
# -*- coding: utf8 -*-
# Itaka Configuration Parser

import ConfigParser, os, sys, traceback

# Set up instance
config = ConfigParser.ConfigParser()

# Set up specific variables
os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "config.xml")

#: Version (do not change)

version = "Devel"

#: Check system or specify per os.name standard
system = os.name

#: Itaka images/ directory
image_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "images/")

#: Local configuration file
local_config = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "config.xml")

#: Save path for screenshots (system-specific)
save_path = os.getcwd()
if (system == 'posix'): save_path = "/tmp"
elif (system == 'nt'): path = os.environ.get('TEMP') or os.environ.get('TMP')


#: Location of the Configfile (search home first, then in this directory).
configfile = None

def load():
	""" Check and read values from the configuration file. """
	if (system == "posix"):
		if (os.path.exists(os.path.join(os.environ['HOME'], "itaka/config.xml"))):
			configfile = os.path.join(os.environ['HOME'], "itaka/config.xml")
		elif (os.path.exists(local_config)):
			configfile = local_config
		else:
			# Create the config
			create(local_config)
	elif (system == "nt"): 
		if (os.path.exists(os.path.join(os.environ['APPDATA'], "itaka/config.xml"))):
				configfile = os.path.join(os.environ['APPDATA'], "itaka/config.xml")
		elif (os.path.exists(local_config)):
				configfile = local_config
		else:
			# Create the config
			create(local_config)
	else:
		# Generic system/values	
		if (os.path.exists(local_config)): 
			configfile = local_config
		else:	
			# Create the config
			create(local_config)
	
	# Read and assign values from the configuration file 
	try:
		config.read(configfile)
		print "[*] Read configuration (%s)" % (configfile)
	except:
		print "[*] ERROR: Could not read config! (%s)" % (configfile)
		traceback.print_exc()
		
	values = {}
	mydict = {}	
	# Get values as a dict and return it
	for section in config.sections():
			values[section] = dict(config.items(section))

	return values

def save(values):
	""" Saves a dict containing the configuration. """
	
	print "[*] Saving configuration... "
	# Unpack the dict into section, option, value
	for section in lista.keys():
		for item, value in lista[section].items():
			config.set(section, key, value)
			
def update(section, key, value):
	""" Update a specific key's value """
	config.set(section, key, value)

def create(path):
	""" Create a configuration file from default values. """
	# Create sections
	for section in ('itaka', 'screenshot', 'ftp', 'server', 'html'): config.add_section(section)
	
	print "[*] Creating default configuration..."
	# Set default values
	config.set("itaka", "method", "server")
	config.set("itaka", "alert", True)
	config.set("itaka", "audio", False)
	config.set("itaka", "notify", False)
	
	config.set("screenshot", "format", "jpeg")
	config.set("screenshot", "quality", 80)
	config.set("screenshot", "path", save_path)
	config.set("screenshot", "time", 8)
	
	config.set("ftp", "host", "ftp.host.com")
	config.set("ftp", "port", 21)
	config.set("ftp", "user", "user")
	config.set("ftp", "pass", "pass")
	config.set("ftp", "dir", "/itaka")
	config.set("ftp", "debug", 0)
	
	config.set("server", "port", 8000)

	# FIXME: Audio
	config.set("html", "audio", '<iframe src="audio" width="100%" height="30" style="border: 0;" border="0">Your browser does not support IFRAME. <a href="audio">Click here</a></iframe><br />')
	config.set("html", "html", '<html><body><img src="screenshot" alt="If you are seeing this message it means there was an error in Itaka or you are using a text-only browser." border="0"></a></body</html>')

	# Write it
	try:
		config.write(open(path, 'w'))
	except:
		print "[*] ERROR: Could not write configuration file %s" % (path)
		traceback.print_exc()
load()
