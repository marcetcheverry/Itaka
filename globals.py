#! /usr/bin/env python
# -*- coding: utf8 -*-
# Itaka Screenshooting Server (Twisted+GTK2) (Windows/Linux)
# Global variables
import os, sys

# Set up global itaka variables
version = "Devel"
# See what system we are running on posix/nt
system = os.name
# Where itaka images are stored...
image_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "images/")

# Method (ftp, server)
method = "server"

# FTP Variables
ftphost = "ftp.usuarios.lycos.es"
ftport = 21
ftpuser = "cgarcia2003"
ftpass = "infest"
# Up dir (Default: blank)
ftpdir = "/itaka"
# Interval between screenshots
ftptime = 8
# Debug level (From ftplib.set_debuglevel) 0-2
ftpdebug = 0

# TCP port
port = 8000
# Path: where to save the screenshot.
path = '/tmp'
if (system != 'posix'): 
	path = os.environ.get('TEMP') or os.environ.get('TMP') or os.getcwd()

# Image format: 'jpeg' or 'png'
format = 'jpeg'
# Image quality: int 0 to 100.
quality = 70
# Alert on request (bell)
alert = True
# Audio Player support
audio = False
# Libnotify support
notify = False
if (os.name != "nt" ):
	notify = True

# Customization of HTML
if (audio): 
	# This is the Audio HTML.
	audiohtml = '<iframe src="audio" width="100%" height="30" style="border: 0;" border="0">Your browser does not support IFRAME. <a href="audio">Click herek</a></iframe><br />'
else:	audiohtml = '' 

# This is the HTML that will be displayed
html = '<html><body> ' + audiohtml  + ' <img src="screenshot" alt="If you are seeing this message it means there was an error in Itaka or you are using a text-only browser." border="0"></a></body</html>'
