#! /usr/bin/env python
# -*- coding: utf8 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Copyright 2003-2007 Marc E. <santusmarc_at_gmail.com>.
# http://itaka.jardinpresente.com.ar

""" Itaka GTK+ GUI """

import sys, os, datetime, traceback 

try:
    from twisted.internet import gtk2reactor
    gtk2reactor.install()

    from twisted.python import log
    from twisted.web import server, static
    from twisted.web.resource import Resource
    from twisted.internet import reactor
except ImportError:
    print "[*] Warning: Twisted Network Framework is missing, quitting."
    sys.exit(1)

try:
    import config as iconfig
    # Read the configuration (loaded by the core)
    config = iconfig
    iconfig = iconfig.values
    import console as iconsole

    import server as iserver

    import uigtk_preferences as ipreferences
except ImportError:
    print "[*] ERROR: Failed to import Itaka modules."
    traceback.print_exc()
    sys.exit(1)

try:
    import pygtk
    pygtk.require("2.0")
except ImportError:
    print "[*] WARNING: Pygtk module is missing."
    pass
try:
    import gtk, gobject
except ImportError:
    print "[*] ERROR: GTK+ bindings are missing."
    sys.exit(1)

class Gui:
    """ GTK GUI """
    def __init__(self, configinstance):
        # Pas a reference of GUI to Screenshot module for its notification handling.
        self.sinstance = iserver.ImageResource(self)
        # Get a reference of the configuration instance
        self.configinstance = configinstance

        # Set up Server variables, if needed.
        self.root = static.Data(iconfig['html']['html'], 'text/html; charset=UTF-8')
        # Registers an identitiy (resource, file).
        self.root.putChild('screenshot', self.sinstance)
        self.root.putChild('', self.root)

        # Start defining widget
        self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(config.image_dir, "itaka.png"))
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", self.destroy)
        self.window.set_title("Itaka")
        self.window.set_icon(self.icon_pixbuf)
        self.window.set_border_width(6)
        self.window.resize(500, 1)
        self.window.set_position(gtk.WIN_POS_CENTER)

        # Boxes, images, and buttons
        self.vbox = gtk.VBox(False, 6)
        self.box = gtk.HBox(False, 0)

        self.itakaLogo = gtk.Image()
        self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka.png"))
        self.itakaLogo.show()

        # Add hbox and buttons and image
        self.box.pack_start(self.itakaLogo, True, True, 4)

        self.ibox = gtk.HBox(False, 0)
        self.buttonStartstop = gtk.ToggleButton("Start", gtk.STOCK_PREFERENCES)
        self.startstopimage = gtk.Image()

        self.startstopimage.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
        self.buttonStartstop.set_image(self.startstopimage)
        self.buttonStartstop.connect("toggled", self.startstop, "Start/Stop button")
        self.ibox.pack_start(self.buttonStartstop, True, True, 8)

        # Preferences button
        self.preferencesButton = gtk.Button("Preferences", gtk.STOCK_PREFERENCES)
        self.preferencesButton.connect("clicked", ipreferences.Preferences().prefwindow, self.configinstance, self, self.icon_pixbuf)

        self.ibox.pack_start(self.preferencesButton, True, True, 4)

        self.box.pack_start(self.ibox, True, True, 0)
        self.vbox.pack_start(self.box, False, False, 0)

        # Another Hbox and Labels
        self.statusBox = gtk.HBox(False, 0)
        self.labelServed = gtk.Label()
        self.labelLastip = gtk.Label()
        self.labelTime = gtk.Label()

        self.statusBox.pack_start(self.labelLastip, True, False, 0)
        self.statusBox.pack_start(self.labelTime, True, False, 0)
        self.statusBox.pack_start(self.labelServed, True, False, 0)

        # Logger widget (displayed when expanded)
        self.debugvbox = gtk.VBox(False, 0)
        self.debugscroll = gtk.ScrolledWindow()
        self.debugscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.debugscroll.set_shadow_type(gtk.SHADOW_IN)
        self.debugview = gtk.TextView()
        self.debugview.set_wrap_mode(gtk.WRAP_WORD)
        self.debugview.set_editable(False)
        self.debugview.set_size_request(-1, 160)
        self.debugbuffer = self.debugview.get_buffer()
        self.debugscroll.add(self.debugview)

        # Buttons
        self.debughbox = gtk.HBox(False, 0)
        self.debugclearbutton = gtk.Button("Clear")
        self.debugclearbuttonimage = gtk.Image()
        self.debugclearbuttonimage.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
        self.debugclearbutton.set_image(self.debugclearbuttonimage)
        self.debugclearbutton.connect("clicked", self.clearlogger)

        self.debugpausebutton = gtk.ToggleButton("Pause")
        self.debugpausebuttonimage = gtk.Image()
        self.debugpausebuttonimage.set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
        self.debugpausebutton.set_image(self.debugpausebuttonimage)
        self.debugpausebutton.connect("toggled", self.pauselogger)

        # Reverse
        self.debughbox.pack_end(self.debugclearbutton, False, False, 4)
        self.debughbox.pack_end(self.debugpausebutton, False, False, 4)

        # Pack it into vbox
        self.debugvbox.pack_start(self.debugscroll, False, False, 4)
        self.debugvbox.pack_start(self.debughbox, False, False, 4)

        # Label for the expander
        self.debugboxLabel = gtk.Label("<b>Detailed log</b>")
        self.debugboxLabel.set_use_markup(True)

        # Expander
        self.expander = gtk.Expander(None)
        self.expander.set_label_widget(self.debugboxLabel)
        self.expander.connect('notify::expanded', self.__expandlogger)

        # Log to the self.logger function, which sets the buffer for self.debubuffer
        log.addObserver(self.logger)

        # Add to main vbox
        self.vbox.pack_start(self.statusBox, False, False, 4)
        self.vbox.pack_start(self.expander, False, False, 0)
        self.expander.set_sensitive(False)
        # Add vbox to window (parent adds all)
        self.window.add(self.vbox)

        # Show window
        self.window.show_all()

    def __expandlogger(self, expander, params):
        """ Callback for the expander widget. """
        if self.expander.get_expanded():
            # Show the debugvbox() and it's subwidgets
            self.debugvbox.show_all()
            self.expander.add(self.debugvbox)
        else:
            self.expander.remove(self.expander.child)
            self.window.resize(500, 1)
        return

    def logger(self, args):
        """ Handle logging in the GUI. Arguments: dict[(tuple($msg)), key: str($msg)]. """
        # We just care about the first tuple
        self.ioutput = args['message'][0]
        # Write out the server log and stdout to the GUI	
        self.debugbuffer.insert_at_cursor("\r" +self.ioutput,len("\r" + self.ioutput))
        # Automatically scroll. Use wrap until fix.
        self.debugview.scroll_mark_onscreen(self.debugbuffer.get_insert())

    def clearlogger(self, args):
        """ Callback to clear the log. """
        self.debugbuffer.set_text("")

    def pauselogger(self, widget, data=None):
        """ Callback to pause log output. """
        # FIXME: Does this pause Console too?
        if widget.get_active():
            log.msg("Logging paused.")
            log.removeObserver(self.logger)
        else:
            log.addObserver(self.logger)
            log.msg("Logging started.")

    def main(self):
        """ Main init function. Starts the GUI reactors."""
        # GTK Reactor and Console Handling
        try:
            # Init console with a reference to our gui instance
            self.console = iconsole.Console(self)
        except AttributeError:
            print "[*] ERROR: Could not initiate Console engine."
            traceback.print_exc()
            sys.exit(1)

        # Server reactor (interacts with the Twisted reactor)	
        self.sreact = reactor.run()

    def about(self, data=None):
        """ Create the About dialog. """
        self.about = gtk.AboutDialog()
        self.about.set_name('Itaka')
        self.about.set_version(config.version.version)
        self.about.set_copyright(u'© 2003-2007 Marc E.')
        self.about.set_comments('Screenshooting de mercado.')
        self.about.set_authors(['Marc E. <santusmarc@gmail.com>'])
        self.about.set_website('http://itaka.jardinpresente.com.ar')
        self.about.set_logo(gtk.gdk.pixbuf_new_from_file(os.path.join(config.image_dir, "itaka.png")))
        self.about.set_icon(self.icon_pixbuf)
        self.about.show()

    def __checkwidget(self, widget):
        """ Workaround to save code on menu/main startstop. """
        if hasattr(widget, 'get_active'):
            return widget.get_active()
        else:
            return False

    def startstop(self, widget, data=None):
        """ Start or stop the screenshooting/ftp server from window or menu. """
        # FIXME: Rewrite this function to something decent.
        # Use an abstraction layer from the Tray if necessary.

        if ( self.__checkwidget(widget) or data == "Start"):
            """Workaround to avoid collision between
            setting startstopbutton.set_active and 
            already started server from the menu and viceversa."""
            if (hasattr(self, 'ilistener')): return True

            # Set up the twisted site
            self.site = server.Site(self.root)
            # Start the server. Make an instance to distinguish from self.sreactor().
            self.ilistener = reactor.listenTCP(int(iconfig['server']['port']), self.site)
            if (data):
                self.buttonStartstop.set_active(True)

            # Announce on log & console stdout
            self.console.msg('Server listening on port %s TCP. Serving screenshots as %s images with %s%% quality.' % (iconfig['server']['port'], iconfig['screenshot']['format'].upper(), iconfig['screenshot']['quality']), True)

            # Change buttons
            self.buttonStartstop.set_label("Stop")
            self.startstopimage.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
            self.buttonStartstop.set_image(self.startstopimage)

            # Close the expander
            self.expander.set_sensitive(True)
            if (iconfig['server']['notify'] == "True"):
                    self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka-take.png"))

        else:
            if hasattr(self, 'ilistener'):
                log.msg('Itaka shutting down...')
                self.console.msg('Server shutting down...')
                self.ilistener.stopListening()
                del self.ilistener
                # Stop the g_timeout
                if hasattr(self, 'iagotimer'):
                        gobject.source_remove(self.iagotimer)
                if (data):
                        self.buttonStartstop.set_active(False)
                self.startstopimage.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
                self.buttonStartstop.set_image(self.startstopimage)
                self.buttonStartstop.set_label("Start")

                # Change the labels and expander
                self.labelLastip.set_text('')
                self.labelTime.set_text('')
                self.labelServed.set_text('')
                self.expander.set_expanded(False)				
                self.expander.set_sensitive(False)
                self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka.png"))
            else:
                pass

    def destroy(self, *args):
        # FIXME: Cleanup stale screenshot file
        """ Callback for the main window's destroy. """
        # Stop server(s). Check so it does not complain if close while not running.
        if hasattr(self, 'ilistener'):
            self.console.msg("Shutting down server...", True)
            #self.ilistener.stopListening()
            del self.console
        else:
            # Console goodbye!
            if hasattr(self, 'console'):	del self.console
        gtk.main_quit()

    def __calcsince(self, dtime):
        """ Function to calculate the time difference from the last request to 
        the current time. Express a datetime.timedelta using a
        phrase such as "1 hour, 20 minutes". """

        # Create a timedelta from the datetime.datetime and the current time
        # (you can create your own timedeltas with datetime.timedelta(5, (650 *
        # 60) * 2, 12) for testing.
        self.td = datetime.datetime.now() - dtime

        self.pieces = []
        if self.td.days:
                self.pieces.append(self.__plural(self.td.days, 'day'))

        self.minutes, self.seconds = divmod(self.td.seconds, 60)
        self.hours, self.minutes = divmod(self.minutes, 60)
        if self.hours:
            self.pieces.append(self.__plural(self.hours, 'hour'))
        if self.minutes or len(self.pieces) == 0:
            self.pieces.append(self.__plural(self.minutes, 'minute'))

        # "Time: " + ", ".join(self.pieces[:-1]) + "and" + self.pieces[-1] + " ago" 

        self.labelTime.set_text("Time: " + ", ".join(self.pieces) + " ago")

        # Need this so it runs more than once. Weird.
        return True

    def __plural(self, count, singular):
        """ This is a helper function for __calcsince that handles
        english plural translations """

        # This is the simplest version; a more general version
        # should handle -y -> -ies, child -> children, etc.
        return '%d %s%s' % (count, singular, ("", 's')[count != 1])

    def notify(self):
        """ Change the image on the main screen, for notification purpose. """
        self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka.png"))
        # Only run this event once
        return False

    def talk(self, action, data1=False, data2=False, data3=False):
        """ Handler for communcations between the server backend, and the GUI. """
        # FIXME: Cleanup

        self.console.msg("Screenshot " + str(data1) + " served to: " + str(data2))

        if ( action == "updateGuiStatus" ):
            # Update labels
            self.labelServed.set_text("Served: " + str(data1))
            if (data2):
                    self.labelLastip.set_text("IP: " + str(data2))
            else:
                    self.labelLastip.set_text("Uploaded to FTP")
            self.labelServed.set_text("Served: " + str(data1))

            # Call the update timer function, and add a timer
            self.__calcsince(data3)
            # Delete the timer if its Not False
            # so we dont get duplicates
            if hasattr(self, 'iagotimer'): gobject.source_remove(self.iagotimer)
            self.iagotimer = gobject.timeout_add(60000, self.__calcsince, data3)

            # Notify the main interface
            if (iconfig['screenshot']['notify'] == "True"):
                self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka-take.png"))
                # Call Inotify
                self.notifyimg = gobject.timeout_add(2000, self.notify)

        # Handler for Preferences signal to reload the config
        elif ( action == "updateConfig"):
            self.cout.msg("Updating configuration...")
            global iconfig
            iconfig = self.configinstance.load()
