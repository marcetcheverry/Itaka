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
# $Id$

""" Itaka GTK+ GUI """

import sys, os, datetime, traceback 

try:
    from twisted.internet import gtk2reactor
    gtk2reactor.install()

    from twisted.python import log
    from twisted.web import server, static
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
        # Initiate our Console intance
        try:
            # Init console with a reference to our gui instance
            self.console = iconsole.Console(self)
        except AttributeError:
            print "[*] ERROR: Could not initiate Console engine."
            traceback.print_exc()
            sys.exit(1)

        # Pass a reference of GUI and Console instanceto Screenshot module for its notification handling.
        self.sinstance = iserver.ImageResource(self, self.console)
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
        self.window.set_default_size(420, 1)
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
        #self.preferencesButton.connect("clicked", ipreferences.Preferences().prefwindow, [config, self.configinstance], self, self.icon_pixbuf)
        self.preferencesVBoxhidden = False
        self.expandpreferencesdone = False
        self.preferencesButton.connect("clicked", self.__expandpreferences)

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

        # Once we have all our widgets, get the 'default' real size, for expanding/contracting
        self.window.default_size = self.window.get_size()

    def __contractpreferences(self, params=None):
        """ Callback to contract the window of preferences. """
        # TODO: Add save

        if hasattr(self, 'contracttimeout'):
            self.windowsize = self.window.get_size()
            if self.windowsize[1] > self.window.default_size[1]:
                self.window.resize(self.windowsize[0], self.windowsize[1]-30)
                return True
            # Gobject is buggy and needs this somehow
            gobject.source_remove(self.contracttimeout)
            del self.contracttimeout
            return False

        self.preferencesVBox.hide_all()

        self.expandpreferencesdone = False 
        self.preferencesVBoxhidden = True
        self.preferencesButton.set_sensitive(True)

        self.contracttimeout = gobject.timeout_add(30, self.__contractpreferences)

    def __expandpreferences(self, params=None):
        """ Callback to expand the window for preferences. """
        # We have a race condition here. If GTK cant resize fast enough, then it gets very sluggish
        # See configure-event signal of gtk.Widget
        # start timer, resize, catch configure-notify, set up idle handler, when idle resize to what the size should be at this point of time, repeat
        if self.expandpreferencesdone != True:
            if hasattr(self, 'expandtimeout'):
                self.windowsize = self.window.get_size()

                if self.windowsize[1] <= 270:
                    self.window.resize(self.windowsize[0], self.windowsize[1]+30)
                    self.windowsize = self.window.get_size()
                    return True
                else:
                    # Its done expanding, add our widgets or display it if it has been done already
                    self.expandpreferencesdone = True
                    self.preferencesButton.set_sensitive(False)

                    if self.preferencesVBoxhidden:
                        self.preferencesVBox.show_all()
                    else:
                        self.preferencesVBox = gtk.VBox(False, 0)
                        self.preferencesHBox1 = gtk.HBox(False, 0)
                        self.preferencesHBox2 = gtk.HBox(False, 0)
                        self.preferencesHBox3 = gtk.HBox(False, 0)
                        self.preferencesHBox4 = gtk.HBox(False, 0)
                        self.preferencesHBox5 = gtk.HBox(False, 0)

                        # Hbox4 contains notifications which is only available in some systems
                        if config.system != "posix":
                            self.preferencesHBox4.set_sensitive(False)

                        self.preferencesLabelrestart = gtk.Label("<i>Restart to apply changes</i>")
                        self.preferencesLabelrestart.set_use_markup(True)
                        self.preferencesLabelrestart.set_justify(gtk.JUSTIFY_CENTER)

                        self.preferencesLabelsettings = gtk.Label("<b>Settings</b>")
                        self.preferencesLabelsettings.set_use_markup(True)
                        self.preferencesLabelsettings.set_justify(gtk.JUSTIFY_LEFT)
                        self.preferencesLabelsettings.set_alignment(0.03, 0.50)

                        self.preferencesLabelport = gtk.Label("Port:")
                        self.preferencesLabelport.set_justify(gtk.JUSTIFY_LEFT)
                        self.preferencesLabelport.set_alignment(0, 0.50)

                        self.preferencesLabelquality = gtk.Label("Quality:")
                        self.preferencesLabelquality.set_justify(gtk.JUSTIFY_LEFT)
                        self.preferencesLabelquality.set_alignment(0, 0.50)


                        self.preferencesLabelformat = gtk.Label("Format:")
                        self.preferencesLabelformat.set_justify(gtk.JUSTIFY_LEFT)
                        self.preferencesLabelformat.set_alignment(0, 0.50)

                        self.preferencesLabelnotifications = gtk.Label("Notifications:")
                        self.preferencesLabelnotifications.set_justify(gtk.JUSTIFY_LEFT)
                        self.preferencesLabelnotifications.set_alignment(0, 0.50)

                        # Spinbuttons
                        self.adjustmentport = gtk.Adjustment(float(iconfig['server']['port']), 1024, 65535, 1, 0, 0)
                        self.preferencesSpinport = gtk.SpinButton(self.adjustmentport)
                        self.preferencesSpinport.set_numeric(True)

                        self.adjustmentquality = gtk.Adjustment(float(iconfig['screenshot']['quality']), 0, 100, 1, 0, 0)
                        self.preferencesSpinquality = gtk.SpinButton(self.adjustmentquality)
                        self.preferencesSpinquality.set_numeric(True)

                        # Combos
                        self.preferencesComboformat = gtk.combo_box_new_text()
                        self.preferencesComboformat.append_text("JPEG")
                        self.preferencesComboformat.append_text("PNG")
                        if (iconfig['screenshot']['format'] == "jpeg"):
                            self.preferencesComboformat.set_active(0)
                        else: 
                            self.preferencesComboformat.set_active(1)

                        self.preferencesChecknotifications = gtk.CheckButton()
                        if (iconfig['server']['notify'] == "True"):
                            self.preferencesChecknotifications.set_active(1)
                        else: 
                            self.preferencesChecknotifications.set_active(0)

                        self.preferencesButtonClose = gtk.Button("Close", gtk.STOCK_CLOSE)
                        self.preferencesButtonClose.connect("clicked", lambda wid: self.__contractpreferences())
                        
                        self.preferencesButtonAbout = gtk.Button("About", gtk.STOCK_ABOUT)
                        self.preferencesButtonAbout.connect("clicked", lambda wid: self.about())

                        self.preferencesHBox1.pack_start(self.preferencesLabelport, False, False, 12)
                        self.preferencesHBox2.pack_start(self.preferencesLabelquality, False, False, 12)
                        self.preferencesHBox3.pack_start(self.preferencesLabelformat, False, False, 12)
                        self.preferencesHBox4.pack_start(self.preferencesLabelnotifications, False, False, 12)

                        self.preferencesHBox1.pack_end(self.preferencesSpinport, False, False, 7)
                        self.preferencesHBox2.pack_end(self.preferencesSpinquality, False, False, 7)
                        self.preferencesHBox3.pack_end(self.preferencesComboformat, False, False, 7)
                        self.preferencesHBox4.pack_end(self.preferencesChecknotifications, False, False, 7)
                        self.preferencesHBox5.pack_start(self.preferencesButtonAbout, False, False, 7)
                        self.preferencesHBox5.pack_end(self.preferencesButtonClose, False, False, 7)


                        # Disable notifications for non-posix and non-pynotify
                        self.preferencesHBox4.set_sensitive(False)
                        notifyavailable = True
                        if config.system == "posix" and config.platform != "darwin" and notifyavailable:
                            self.preferencesHBox4.set_sensitive(True)

                        # Add Hboxes to the Vbox
                        self.preferencesVBox.pack_start(self.preferencesLabelsettings, False, False, 4)
                        self.preferencesVBox.pack_start(self.preferencesHBox1, False, False, 0)
                        self.preferencesVBox.pack_start(self.preferencesHBox2, False, False, 0)
                        self.preferencesVBox.pack_start(self.preferencesHBox3, False, False, 0)
                        self.preferencesVBox.pack_start(self.preferencesHBox4, False, False, 0)
                        self.preferencesVBox.pack_start(self.preferencesLabelrestart, False, False, 5)
                        self.preferencesVBox.pack_start(self.preferencesHBox5, False, False, 0)

                        self.vbox.pack_start(self.preferencesVBox, False, False, 0)
                        self.preferencesVBox.show_all()

                    # Gobject is buggy and needs this somehow
                    gobject.source_remove(self.expandtimeout)
                    del self.expandtimeout
                    return False
            else:
                self.expandtimeout = gobject.timeout_add(30, self.__expandpreferences)

    def about(self, data=None):
        """ Create the About dialog. """
        self.aboutdialog = gtk.AboutDialog()
        self.aboutdialog.set_transient_for(self.window)
        self.aboutdialog.set_name('Itaka')
        self.aboutdialog.set_version(config.version)
        self.aboutdialog.set_copyright(u'© 2003-2007 Marc E.')
        self.aboutdialog.set_comments('Screenshooting de mercado.')
        self.aboutdialog.set_authors(['Marc E. <santusmarc@gmail.com>'])
        self.aboutdialog.set_artists(['Marc E. <santusmarc@gmail.com>'])
        self.aboutdialog.set_license('''This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA''')
        self.aboutdialog.set_website('http://itaka.jardinpresente.com.ar')
        self.aboutdialog.set_logo(gtk.gdk.pixbuf_new_from_file(os.path.join(config.image_dir, "itaka-logo.png")))
        self.aboutdialog.set_icon(self.icon_pixbuf)
        self.aboutdialog.run()
        self.aboutdialog.destroy()

    def __expandlogger(self, expander, params):
        """ Callback for the expander widget. """
        if self.expander.get_expanded():
            # Show the debugvbox() and it's subwidgets
            self.debugvbox.show_all()
#            tv = gtk.TextView()
#            self.debugvbox.pack_end(tv, False, False, 0)
#            tv.show()
#            tv_win = tv.get_window(gtk.TEXT_WINDOW_TEXT)
#            print tv_win
#            self.debugbackwindow = self.debugview.get_window(gtk.TEXT_WINDOW_TEXT)
#            self.debugbackwindow.set_back_pixmap(self.icon_pixbuf, gtk.FALSE)

            self.expander.add(self.debugvbox)
        else:
            self.expander.remove(self.expander.child)
            self.window.resize(420, 1)
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
        if widget.get_active():
            log.msg("Logging paused")
            self.debugscroll.set_sensitive(False)
            log.removeObserver(self.logger)
        else:
            log.addObserver(self.logger)
            self.debugscroll.set_sensitive(True)
            log.msg("Logging resumed")

    def main(self):
        """ Main init function. Starts the GUI reactors."""

        # Server reactor (interacts with the Twisted reactor)	
        self.sreact = reactor.run()

    def __checkwidget(self, widget):
        """ Check the status of the toggle button. """
        if hasattr(widget, 'get_active'):
            return widget.get_active()
        else:
            return False

    def startstop(self, widget, data=None):
        """ Start or stop the screenshooting server. """
        if (self.__checkwidget(widget)):

            # Twisted doesnt support hot-restarting as stopListening()/startListening(), just use the old one again

            # Set up the twisted site
            self.site = server.Site(self.root)
            # Start the server. Make an instance to distinguish from self.sreactor().
            self.ilistener = reactor.listenTCP(int(iconfig['server']['port']), self.site)

            # Announce on log & console stdout
            if iconfig['screenshot']['quality'] == "jpeg":
                self.console.msg('Server listening on port %s TCP. Serving screenshots as %s images with %s%% quality.' % (iconfig['server']['port'], iconfig['screenshot']['format'].upper(), iconfig['screenshot']['quality']), True)
            else:
                self.console.msg('Server listening on port %s TCP. Serving screenshots as %s images.' % (iconfig['server']['port'], iconfig['screenshot']['format'].upper()), True)

            # Change buttons
            self.buttonStartstop.set_active(True)
            self.buttonStartstop.set_label("Stop")
            self.startstopimage.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
            self.buttonStartstop.set_image(self.startstopimage)

            # Close the expander
            self.expander.set_sensitive(True)

            # I am not sure about this, notification
            # if (iconfig['server']['notify'] == "True"):
            #        self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka-take.png"))

        else:
            if hasattr(self, 'ilistener'):
                self.console.msg("Stopping server", True)

                self.ilistener.stopListening()

                # Stop the g_timeout
                if hasattr(self, 'iagotimer'):
                    gobject.source_remove(self.iagotimer)

                # Change GUI elements
                self.buttonStartstop.set_active(False)
                self.startstopimage.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
                self.buttonStartstop.set_image(self.startstopimage)
                self.buttonStartstop.set_label("Start")
                self.labelLastip.set_text('')
                self.labelTime.set_text('')
                self.labelServed.set_text('')
                self.expander.set_expanded(False)				
                self.expander.set_sensitive(False)
                self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka.png"))
            else:
                pass
                print "puta pario"

    def destroy(self, *args):
        """ Callback for the main window's destroy. """
        # Stop server.
        if hasattr(self, 'ilistener'):
            self.console.msg("Shutting down server...", True)
            self.ilistener.stopListening()
            del self.console
        else:
            # Console goodbye!
            if hasattr(self, 'console'):
                del self.console

        # Remove stale screenshot and quit
        if os.path.exists(os.path.join(iconfig['screenshot']['path'], 'itakashot.%s' % (iconfig['screenshot']['format']))): 
            os.remove(os.path.join(iconfig['screenshot']['path'], 'itakashot.%s' % (iconfig['screenshot']['format'])))

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

    def talk(self, action, number=False, ip=False, time=False):
        """ Handler for communcations between the server backend, and the GUI. """
        if (action == "updateGuiStatus" ):
            self.console.msg("Screenshot " + str(number) + " served to: " + str(ip))
            self.labelServed.set_text("Served: " + str(number))
            self.labelLastip.set_text("IP: " + str(ip))

            if (iconfig['server']['notify'] == "True"):
                self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka-take.png"))
                self.notifyimg = gobject.timeout_add(2000, self.notify)

            # Call the update timer function, and add a timer to update the GUI of its
            # "Last screenshot taken" time
            self.__calcsince(time)
            if hasattr(self, 'iagotimer'): gobject.source_remove(self.iagotimer)
            self.iagotimer = gobject.timeout_add(60000, self.__calcsince, time)

        # Handler for Preferences signal to reload the config
        elif ( action == "updateConfig"):
            # TODO: Implement dynamic preferences
            # global iconfig
            # iconfig = self.configinstance.load()
            pass
