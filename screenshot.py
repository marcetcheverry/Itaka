#! /usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka screenshot engine """

import gc, os

# Itaka core modules
import config as iconfig
config = iconfig
iconfig = iconfig.values

import pygtk
pygtk.require("2.0")
import gtk 

# Final absolute path to the screenshot file
shotFile = os.path.join(iconfig['screenshot']['path'], 'itakashot.%s' % (iconfig['screenshot']['format']))

def Screenshot():
    """ Returns a screenshot file. """
    # GTK Screenshooting code.
    w = gtk.gdk.screen_width()
    h = gtk.gdk.screen_height()
    screenshot = gtk.gdk.Pixbuf.get_from_drawable(
            gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h),
            gtk.gdk.get_default_root_window(),
            gtk.gdk.colormap_get_system(),
            0, 0, 0, 0, w, h)
    shotFile = os.path.join(iconfig['screenshot']['path'], 'itakashot.%s' % (iconfig['screenshot']['format']))

    # Save the screnshot, checking before if to set JPEG quality
    if iconfig['screenshot']['format'] == 'jpeg':
        screenshot.save(shotFile, iconfig['screenshot']['format'].lower(), {"quality":str(iconfig['screenshot']['quality'])})
    else:
        screenshot.save(shotFile, iconfig['screenshot']['format'].lower())

    # Important workaround to avoid a memory leak.
    # http://www.async.com.br/faq/pygtk/index.py?req=show&file=faq08.004.htp
    del screenshot
    gc.collect()

    return shotFile
