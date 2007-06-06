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

""" Itaka screenshot engine """

import gc, os, gtk, pygtk
pygtk.require("2.0")


def Screenshot(guiinstance, configuration):
    """ Returns a screenshot file. 'configuration' is configuration values """

    # Final absolute path to the screenshot file
    shotFile = os.path.join(configuration['screenshot']['path'], 'itakashot.%s' % (configuration['screenshot']['format']))
    
    w = gtk.gdk.screen_width()
    h = gtk.gdk.screen_height()
    screenshot = gtk.gdk.Pixbuf.get_from_drawable(
            gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h),
            gtk.gdk.get_default_root_window(),
            gtk.gdk.colormap_get_system(),
            0, 0, 0, 0, w, h)

    # Save the screnshot, checking before if to set JPEG quality
    try:
        if configuration['screenshot']['format'] == 'jpeg':
            screenshot.save(shotFile, configuration['screenshot']['format'].lower(), {"quality":str(configuration['screenshot']['quality'])})
        else:
            screenshot.save(shotFile, configuration['screenshot']['format'].lower())
    except:
        self.console.error(['ImageResource','screenshot'], "Could not save screenshot", guiinstance)

    # Important workaround to avoid a memory leak.
    # http://www.async.com.br/faq/pygtk/index.py?req=show&file=faq08.004.htp
    del screenshot
    gc.collect()

    return shotFile
