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

""" Itaka screenshot engine """

import gc
import os
import gtk
import pygtk
pygtk.require("2.0")
import error
import traceback

class Screenshot:
    """
    Takes screenshots of windows or screens
    """

    def __init__(self, gui_instance, scaling_method=gtk.gdk.INTERP_BILINEAR): 
        """
        Constructor

        @type scaling_method: gtk.gdk.INTERP_TYPE
        @param scaling_method: A type of interpolation for screenshot scaling. U{http://pygtk.org/pygtk2reference/class-gdkpixbuf.html#method-gdkpixbuf--scale-simple}

        @type gui_instance: instance
        @param gui_instance: An instance of our L{Gui} class
        """

        self.gui = gui_instance
        self.itaka_globals = self.gui.itaka_globals
        self.configuration = self.gui.configuration
        self.console = self.gui.console
        self.scaling_method = scaling_method

        #: Whether our current window method failed or not
        self.current_window_failed = False

        #: Final absolute path to the screenshot file
        self.shot_file = os.path.join(self.configuration['screenshot']['path'], 'itakashot.%s' % (self.configuration['screenshot']['format']))
        
        self.root_screen = gtk.gdk.screen_get_default()
        self.root_window = gtk.gdk.get_default_root_window()

        self.screen_width = gtk.gdk.screen_width()
        self.screen_height = gtk.gdk.screen_height()

    def find_current_active_window(self):
        """ 
        Find the current active window through the _NET_ACTIVE_WINDOW hint

        @rtype: tuple
        @return: (int) window width, (int) window heigth, (int) window position x, (int) window position y
        """

        if self.root_screen.supports_net_wm_hint("_NET_ACTIVE_WINDOW") and \
            self.root_screen.supports_net_wm_hint("_NET_WM_WINDOW_TYPE"):
            self.active_window = self.root_screen.get_active_window()

            # Calculate the size of the window including window manager decorations
            self.relativex, self.relativey, self.winw, self.winh, self.d = self.active_window.get_geometry() 
            self.window_width = self.winw + (self.relativex*2)
            self.window_height = self.winh + (self.relativey+self.relativex)

            # Calculate the position of where the window manager decorations start
            # get_position() will return the position of the window relative to the WM
            self.window_positionx, self.window_positiony = self.active_window.get_root_origin()
        else:
            self.current_window_failed = True
            raise error.ItakaScreenshotErrorWmHints, _('Window Manager does not support _NET_WM hints')
    
        # We do not want to grab the desktop window
        if self.active_window.property_get("_NET_WM_WINDOW_TYPE")[-1][0] == '_NET_WM_WINDOW_TYPE_DESKTOP':
            self.current_window_failed = True
            raise error.ItakaScreenshotErrorActiveDesktop, _('Active window is desktop')

        return (self.window_width, self.window_height, self.window_positionx, self.window_positiony)

    def take_screenshot(self):
        """
        Take a screenshot of the whole screen or a window

        @rtype: str
        @return: Path to the screenshot (L{self.shot_file})
        """

        # Get up to date configuration values everytime there is a request
        
        self.configuration = self.gui.configuration

        if self.configuration['screenshot']['currentwindow'] and not self.itaka_globals.system == 'nt':
            try:
                self.current_window = self.find_current_active_window()
            except error.ItakaScreenshotErrorWmHints:
                self.gui.log.failure(('Screenshot', 'take_screenshot'), (_('Can not grab the current window'), _('Can not grab the current window because your window manager does not support NET_WM_* hints')), 'WARNING')
            except error.ItakaScreenshotErrorActiveDesktop:
                self.gui.log.failure(('Screenshot', 'take_screenshot'), (_('Not grabing the desktop as the current window'), _('Your focus was on the destop when a client requested a screenshot, Itaka instead took a screenshot of the whole screen')), 'WARNING')

            if not self.current_window_failed:
                # Make the window size also the screen size for scaling purposes
                self.active_windowwidth = self.current_window[0]
                self.active_windowheight = self.current_window[1]

                self.screenshot = gtk.gdk.Pixbuf.get_from_drawable(
                        gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.active_windowwidth, self.active_windowheight),
                        self.root_window,
                        gtk.gdk.colormap_get_system(),
                        self.current_window[2], self.current_window[3], 0, 0, self.active_windowwidth, self.active_windowheight)

        if self.current_window_failed or not self.configuration['screenshot']['currentwindow'] or self.itaka_globals.system == 'nt': 
            self.screenshot = gtk.gdk.Pixbuf.get_from_drawable(
                    gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, self.screen_width, self.screen_height),
                    self.root_window,
                    gtk.gdk.colormap_get_system(),
                    0, 0, 0, 0, self.screen_width, self.screen_height)

        # GTK manages errors this way
        if not hasattr(self, 'screenshot') or self.screenshot is None:
            # Reset the failure flag
            self.current_window_failed = False
            self.gui.log.failure(('Screenshot', 'take_screenshot'), (_('Could not grab screenshot'), _('GTK+ could not grab a screenshot of the screen')), 'ERROR')
            raise error.ItakaScreenshotError, _('Could not grab screenshot, GTK+ error')

        if self.configuration['screenshot']['scale']:
            # Make it just work, dont bother warning about very rare cases
            if self.configuration['screenshot']['scalepercent'] == 0:
                self.configuration['screenshot']['scalepercent'] = 1

            if self.configuration['screenshot']['currentwindow'] and not self.current_window_failed and not self.itaka_globals.system == 'nt':
                self.scale_width = self.active_windowwidth * int(self.configuration['screenshot']['scalepercent']) / 100
                self.scale_height = self.active_windowheight * int(self.configuration['screenshot']['scalepercent']) / 100
            else:
                self.scale_width = self.screen_width * int(self.configuration['screenshot']['scalepercent']) / 100
                self.scale_height = self.screen_height * int(self.configuration['screenshot']['scalepercent']) / 100
            self.screenshot = self.screenshot.scale_simple(self.scale_width, self.scale_height, self.scaling_method)

        # Save the screnshot, checking before if to set JPEG quality
        try:
            if self.configuration['screenshot']['format'] == 'jpeg':
                self.screenshot.save(self.shot_file, self.configuration['screenshot']['format'].lower(), {"quality":str(self.configuration['screenshot']['quality'])})
            else:
                self.screenshot.save(self.shot_file, self.configuration['screenshot']['format'].lower())
        except:
            self.gui.log.failure(('Screenshot','take_screenshot'), (_('Could not save screenshot'), _('Could not save screenshot %s') % (traceback.format_exc())), 'ERROR')
            raise error.ItakaSaveScreenshotError, _('Could not save screenshot')

        # Important workaround to avoid a memory leak
        # http://www.async.com.br/faq/pygtk/index.py?req=show&file=faq08.004.htp
        del self.screenshot
        gc.collect()

        # Reset the failure flag
        self.current_window_failed = False

        return self.shot_file

