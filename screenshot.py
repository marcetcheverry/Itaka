#! /usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka screenshot engine """

import gc, os

import config as iconfig
config = iconfig
iconfig = iconfig.values


if (config.system != 'darwin'):
	import pygtk
	pygtk.require("2.0")
	import gtk 

def Screenshot():
	""" Returns a screenshot file. """
	if (config.system != 'darwin'):
		shot = 'itakashot.' + iconfig['screenshot']['format']
		w = gtk.gdk.screen_width()
		h = gtk.gdk.screen_height()
		screenshot = gtk.gdk.Pixbuf.get_from_drawable(
			gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h),
			gtk.gdk.get_default_root_window(),
			gtk.gdk.colormap_get_system(),
			0, 0, 0, 0, w, h)
		shotFile = os.path.join(iconfig['screenshot']['path'],shot)
		screenshot.save(shotFile, shot.split('.')[1], {"quality":str(iconfig['screenshot']['quality'])})

		# Important workaround to avoid a memory leak.
		# http://www.async.com.br/faq/pygtk/index.py?req=show&file=faq08.004.htp
		del screenshot
		gc.collect()
	else:
		# FIXME: Preliminary darwin support
		shotFile = os.path.join(iconfig['screenshot']['path'], "itakashot.png")
		os.system("screencapture -S %s" % (shotFile))
	
	return shotFile
