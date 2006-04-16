#! /usr/bin/env python
# -*- coding: utf8 -*-
# Itaka Screenshooting Server (Twisted+GTK2) (Windows/Linux)
# Global variables
import os, sys

#: Version (do not change)
version = "Devel"
#: Check system or specify per os.name standard
system = os.name
#: Itaka images/ directory
image_dir = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "images/")

#: Method (ftp, server)
method = "server"

# FTP Variables
#: FTP host
ftphost = "ftp.usuarios.lycos.es"
#: FTP port
ftport = 21
#: FTP username
ftpuser = "cgarcia2003"
#: FTP password
ftpass = "pass"
#: FTP directory (default: blank)
ftpdir = "/itaka"
#: FTP Interval between uploads
ftptime = 8
# Debug level (From ftplib.set_debuglevel) 0-2
ftpdebug = 0

#: Server TCP port
port = 8000
#: Save path for screenshot.
path = '/tmp'
if (system != 'posix'): 
	path = os.environ.get('TEMP') or os.environ.get('TMP') or os.getcwd()

#: Screenshot format (jpeg, png)
format = 'jpeg'
#: ScreScreenshott quality (0-100)
quality = 70
#: Alert on request (Bell)
alert = True
#: Audio Player support
audio = False
#: GUI notification support
notify = False

# Customization of HTML
if (audio): 
	#: Audio HTML of Server
	audiohtml = '<iframe src="audio" width="100%" height="30" style="border: 0;" border="0">Your browser does not support IFRAME. <a href="audio">Click herek</a></iframe><br />'
else:	audiohtml = '' 

#: HTML of Server
html = '<html><body> ' + audiohtml  + ' <img src="screenshot" alt="If you are seeing this message it means there was an error in Itaka or you are using a text-only browser." border="0"></a></body</html>'
