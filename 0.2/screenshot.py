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
# Copyright 2003-2009 Marc E.
# http://itaka.jardinpresente.com.ar
#
# $Id$

""" Itaka screenshot engine """

import gc, os, gtk, pygtk, error, traceback
pygtk.require("2.0")

class Screenshot:
    """
    Takes screenshots of windows or screens.
    """

    def __init__(self, guiinstance, scalingmethod=gtk.gdk.INTERP_BILINEAR): 
        """
        Constructor.

        @type scalingmethod: gtk.gdk.INTERP_TYPE
        @param scalingmethod: A type of interpolation for screenshot scaling. U{http://pygtk.org/pygtk2reference/class-gdkpixbuf.html#method-gdkpixbuf--scale-simple}

        @type guiinstance: instance
        @param guiinstance: An instance of our L{Gui} class.
        """

        self.gui = guiinstance
        self.itakaglobals = self.gui.itakaglobals
        self.configuration = self.gui.configuration
        self.console = self.gui.console
        self.scalingmethod = scalingmethod

        #: Whether our current window method failed or not
        self.currentwindowfailed = False

        #: Final absolute path to the screenshot file
        self.shotFile = os.path.join(self.configuration['screenshot']['path'], 'itakashot.%s' % (self.configuration['screenshot']['format']))
        
        self.rootscreen = gtk.gdk.screen_get_default()
        self.rootwindow = gtk.gdk.get_default_root_window()

        self.screenwidth = gtk.gdk.screen_width()
        self.screenheight = gtk.gdk.screen_height()

    def find_current_active_window(self):
        """ 
        Find the current active window through the _NET_ACTIVE_WINDOW hint.

        @rtype: tuple
        @return: (int) window width, (int) window heigth, (int) window position x, (int) window position y.
        """

        if self.rootscreen.supports_net_wm_hint("_NET_ACTIVE_WINDOW") and self.rootscreen.supports_net_wm_hint("_NET_WM_WINDOW_TYPE"):
            self.activewindow = self.rootscreen.get_active_window()

            # Calculate the size of the window including window manager decorations
            self.relativex, self.relativey, self.winw, self.winh, self.d = self.activewindow.get_geometry() 
            self.windowwidth = self.winw + (self.relativex*2)
            self.windowheight = self.winh + (self.relativey+self.relativex)

            # Calculate the position of where the window manager decorations start.
            # get_position() will return the position of the window relative to the WM.
            self.windowpositionx, self.windowpositiony = self.activewindow.get_root_origin()
        else:
            self.currentwindowfailed = True
            raise error.ItakaScreenshotErrorWmHints, 'Window Manager does not support _NET_WM hints'
    
        # We do not want to grab the desktop window
        if self.activewindow.property_get("_NET_WM_WINDOW_TYPE")[-1][0] == '_NET_WM_WINDOW_TYPE_DESKTOP':
            self.currentwindowfailed = True
            raise error.ItakaScreenshotErrorActiveDesktop, 'Active window is desktop'

        return (self.windowwidth, self.windowheight, self.windowpositionx, self.windowpositiony)

    def take_screenshot(self):
        """
        Take a screenshot of the whole screen or a window.

        @rtype: str
        @return: Path to the screenshot (L{self.shotFile})
        """

        # Get up to date configuration values everytime there is a request
        
        self.configuration = self.gui.configuration

        if self.configuration['screenshot']['currentwindow'] and not self.itakaglobals.system == 'nt':
            try:
                self.currentwindow = self.find_current_active_window()
            except error.ItakaScreenshotErrorWmHints:
                self.gui.log.failure(('Screenshot', 'take_screenshot'), ('Can not grab the current window', 'Can not grab the curren window because your window manager does not support NET_WM_* hints'), 'WARNING')
            except error.ItakaScreenshotErrorActiveDesktop:
                self.gui.log.failure(('Screenshot', 'take_screenshot'), ('Not grabing the desktop as the current window', 'Your focus was on the destop when a client requested a screenshot, Itaka instead took a screenshot of the whole screen'), 'WARNING')

            if not self.currentwindowfailed:
                # Make the window size also the screen size for scaling purposes
                self.activewindowwidth = self.currentwindow[0]
                self.activewindowheight = self.currentwindow[1]

                self.screenshot = gtk.gdk.Pixbuf.get_from_drawable(
                        gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.activewindowwidth, self.activewindowheight),
                        self.rootwindow,
                        gtk.gdk.colormap_get_system(),
                        self.currentwindow[2], self.currentwindow[3], 0, 0, self.activewindowwidth, self.activewindowheight)

        if self.currentwindowfailed or not self.configuration['screenshot']['currentwindow'] or self.itakaglobals.system == 'nt': 
            self.screenshot = gtk.gdk.Pixbuf.get_from_drawable(
                    gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.screenwidth, self.screenheight),
                    self.rootwindow,
                    gtk.gdk.colormap_get_system(),
                    0, 0, 0, 0, self.screenwidth, self.screenheight)

        # GTK manages errors this way
        if not hasattr(self, 'screenshot') or self.screenshot is None:
            # Reset the failure flag
            self.currentwindowfailed = False
            self.gui.log.failure(('Screenshot', 'take_screenshot'), ('Could not grab screenshot', 'GTK+ could not grab a screenshot of the screen.'), 'ERROR')
            raise error.ItakaScreenshotError, 'Could not grab screenshot, GTK+ error'

        if self.configuration['screenshot']['scale']:
            # Make it just work, dont bother warning about very rare cases
            if self.configuration['screenshot']['scalepercent'] == 0:
                self.configuration['screenshot']['scalepercent'] = 1

            if self.configuration['screenshot']['currentwindow'] and not self.currentwindowfailed and not self.itakaglobals.system == 'nt':
                self.scalewidth = self.activewindowwidth * int(self.configuration['screenshot']['scalepercent']) / 100
                self.scaleheight = self.activewindowheight * int(self.configuration['screenshot']['scalepercent']) / 100
            else:
                self.scalewidth = self.screenwidth * int(self.configuration['screenshot']['scalepercent']) / 100
                self.scaleheight = self.screenheight * int(self.configuration['screenshot']['scalepercent']) / 100
            self.screenshot = self.screenshot.scale_simple(self.scalewidth, self.scaleheight, self.scalingmethod)

        # Save the screnshot, checking before if to set JPEG quality
        try:
            if self.configuration['screenshot']['format'] == 'jpeg':
                self.screenshot.save(self.shotFile, self.configuration['screenshot']['format'].lower(), {"quality":str(self.configuration['screenshot']['quality'])})
            else:
                self.screenshot.save(self.shotFile, self.configuration['screenshot']['format'].lower())
        except:
            self.gui.log.failure(('Screenshot','take_screenshot'), ('Could not save screenshot', 'Could not save screenshot %s' % (traceback.format_exc())), 'ERROR')
            raise error.ItakaSaveScreenshotError, "Could not save screenshot"

        # Important workaround to avoid a memory leak.
        # http://www.async.com.br/faq/pygtk/index.py?req=show&file=faq08.004.htp
        del self.screenshot
        gc.collect()

        # Reset the failure flag
        self.currentwindowfailed = False

        return self.shotFile