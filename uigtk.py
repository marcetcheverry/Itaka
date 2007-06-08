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

""" Itaka GTK+ GUI """

import sys, os, datetime, traceback, copy 

try:
    from twisted.internet import gtk2reactor
    gtk2reactor.install()

    from twisted.python import log
    from twisted.web import server, static
    from twisted.internet import reactor
    import twisted.internet.error
except ImportError:
    print "[*] Warning: Twisted Network Framework is missing, quitting"
    sys.exit(1)

try:
    import server as iserver
    import screenshot
except ImportError:
    print "[*] ERROR: Failed to import Itaka modules"
    traceback.print_exc()
    sys.exit(1)

try:
    import pygtk
    pygtk.require("2.0")
except ImportError:
    print "[*] WARNING: Pygtk module is missing"
    pass
try:
    import gtk, gobject
except ImportError:
    print "[*] ERROR: GTK+ bindings are missing"
    sys.exit(1)

if gtk.gtk_version[1] < 10:
    print "[*] ERROR: Itaka requires GTK+ 2.10, you have %s installed" % (".".join(str(x) for x in gtk.gtk_version))
    sys.exit(1)

class Gui:
    """
    GTK+ GUI
    """
    def __init__(self, consoleinstance, configuration):
        """
        @type consoleinstance: instance
        @param consoleinstance: An instance of the L{Console} class.
        @type configuration: tuple
        @param configuration: A tuple of configuration globals and an instance of L{ConfigParser}
        """

        #: Server status
        self.server_listening = False

        # Load our configuration and console instances and values
        self.console = consoleinstance
        self.itakaglobals = configuration[0]
        # The configuration instance has the user's preferences already loaded.
        self.configinstance = configuration[1]
        self.configuration = self.itakaglobals.values

        # Start defining widgets
        self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(self.itakaglobals.image_dir, "itaka.png"))
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", self.destroy)
        self.window.connect("size-allocate", self.__windowsizechanged)
        self.window.set_title("Itaka")
        self.window.set_icon(self.icon_pixbuf)
        self.window.set_border_width(6)
        self.window.set_default_size(400, 1)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window_position = self.window.get_position()

        # Create our tray icon
        self.statusIcon = gtk.StatusIcon()
        self.statusmenu = gtk.Menu()
        self.statusIcon.set_from_pixbuf(self.icon_pixbuf)
        self.statusIcon.set_tooltip("Itaka")
        self.statusIcon.set_visible(True)
        self.statusIcon.connect('activate', self.__statusicon_activate)
        self.statusIcon.connect('popup-menu', self.__statusicon_menu, self.statusmenu)

        self.startimage = gtk.Image()
        self.startimage.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)

        self.stopimage = gtk.Image()
        self.stopimage.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_MENU)

 	self.menuitemstart = gtk.ImageMenuItem("Start") 
        self.menuitemstart.set_image(self.startimage)
        self.menuitemstart.connect('activate', self.startstop, "start")
 	self.menuitemstop = gtk.ImageMenuItem("Stop") 
        self.menuitemstop.set_image(self.stopimage)
        self.menuitemstop.connect('activate', self.startstop, "stop")
        self.menuitemstop.set_sensitive(False)

        if self.itakaglobals.notifyavailable: 
            self.menuitemnotifications = gtk.CheckMenuItem("Show Notifications")
            if (self.configuration['server']['notify']):
                self.menuitemnotifications.set_active(True)
            self.menuitemnotifications.connect('toggled', self.__statusicon_notify)

        self.menuitemseparator = gtk.SeparatorMenuItem()
        self.menuitemseparator1 = gtk.SeparatorMenuItem()
        self.menuitemabout = gtk.ImageMenuItem(gtk.STOCK_ABOUT) 
        self.menuitemabout.connect('activate', self.about)
 	self.menuitemquit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.menuitemquit.connect('activate', self.destroy)

        self.statusmenu.append(self.menuitemstart)
        self.statusmenu.append(self.menuitemstop)
        if self.itakaglobals.notifyavailable: 
            self.statusmenu.append(self.menuitemseparator)
            self.statusmenu.append(self.menuitemnotifications)
        self.statusmenu.append(self.menuitemseparator1)
        self.statusmenu.append(self.menuitemabout)
        self.statusmenu.append(self.menuitemquit)

        self.vbox = gtk.VBox(False, 6)
        self.box = gtk.HBox(False, 0)

        self.itakaLogo = gtk.Image()
        self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, "itaka.png"))
        self.itakaLogo.show()

        self.box.pack_start(self.itakaLogo, True, True, 4)

        self.ibox = gtk.HBox(False, 0)
        self.buttonStartstop = gtk.ToggleButton("Start", gtk.STOCK_PREFERENCES)
        self.startstopimage = gtk.Image()

        self.startstopimage.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
        self.buttonStartstop.set_image(self.startstopimage)
        self.buttonStartstop.connect("toggled", self.startstop, "Start/Stop button")
        self.ibox.pack_start(self.buttonStartstop, True, True, 8)

        self.preferencesButton = gtk.Button("Preferences", gtk.STOCK_PREFERENCES)
        self.preferencesButton.connect("clicked", self.__expandpreferences)
        #self.preferencesButton.connect("clicked", ipreferences.Preferences().prefwindow, [config, self.configinstance], self, self.icon_pixbuf)

        # Set up some variables for our timeouts/animations
        self.preferenceshidden = False
        self.preferencesexpanded = False
        self.contracttimeout = None
        self.expandtimeout = None
        self.blinktimeout = None

        self.ibox.pack_start(self.preferencesButton, True, True, 4)

        self.box.pack_start(self.ibox, True, True, 0)
        self.vbox.pack_start(self.box, False, False, 0)

        self.statusBox = gtk.HBox(False, 0)
        self.labelServed = gtk.Label()
        self.labelLastip = gtk.Label()
        self.labelTime = gtk.Label()

        self.statusBox.pack_start(self.labelLastip, True, False, 0)
        self.statusBox.pack_start(self.labelTime, True, False, 0)
        self.statusBox.pack_start(self.labelServed, True, False, 0)

        # Logger widget (displayed when expanded)
        self.logvbox = gtk.VBox(False, 0)
        self.lognotebook = gtk.Notebook()
        self.lognotebook.set_tab_pos(gtk.POS_BOTTOM)

        self.logeventslabel = gtk.Label("Events")
        self.logdetailslabel = gtk.Label("Details")

        self.logeventsscroll = gtk.ScrolledWindow()
        self.logeventsscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.logeventsscroll.set_shadow_type(gtk.SHADOW_NONE)

        self.logeventsstore = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.logeventstreeview = gtk.TreeView(self.logeventsstore)
        self.logeventstreeview.set_property("headers-visible", False)
        self.logeventstreeview.set_property("rules-hint", True)

        self.logeventscolumnicon = gtk.TreeViewColumn()
        self.logeventscolumntext = gtk.TreeViewColumn()
        self.logeventstreeview.append_column(self.logeventscolumnicon)
        self.logeventstreeview.append_column(self.logeventscolumntext)

        self.logeventscellpixbuf = gtk.CellRendererPixbuf()
        self.logeventscolumnicon.pack_start(self.logeventscellpixbuf)
        self.logeventscolumnicon.add_attribute(self.logeventscellpixbuf, 'pixbuf', 0)

        self.logeventscelltext = gtk.CellRendererText()
        self.logeventscolumntext.pack_start(self.logeventscelltext, True)
        self.logeventscolumntext.add_attribute(self.logeventscelltext, 'text', 1)
        self.logeventsscroll.add(self.logeventstreeview)

        self.logdetailsscroll = gtk.ScrolledWindow()
        self.logdetailsscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.logdetailsscroll.set_shadow_type(gtk.SHADOW_NONE)
        self.logdetailstextview = gtk.TextView()
        self.logdetailstextview.set_wrap_mode(gtk.WRAP_WORD)
        self.logdetailstextview.set_editable(False)
        self.logdetailstextview.set_size_request(-1, 160)
        self.logdetailsbuffer = self.logdetailstextview.get_buffer()
        self.logdetailsscroll.add(self.logdetailstextview)

        self.lognotebook.append_page(self.logeventsscroll, self.logeventslabel)
        self.lognotebook.append_page(self.logdetailsscroll, self.logdetailslabel)

        self.loghbox = gtk.HBox(False, 0)
        self.logclearbutton = gtk.Button("Clear")
        self.logclearbuttonimage = gtk.Image()
        self.logclearbuttonimage.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
        self.logclearbutton.set_image(self.logclearbuttonimage)
        self.logclearbutton.connect("clicked", self.clearlogger)

        self.logpausebutton = gtk.ToggleButton("Pause")
        self.logpausebuttonimage = gtk.Image()
        self.logpausebuttonimage.set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
        self.logpausebutton.set_image(self.logpausebuttonimage)
        self.logpausebutton.connect("toggled", self.pauselogger)

        self.loghbox.pack_end(self.logclearbutton, False, False, 4)
        self.loghbox.pack_end(self.logpausebutton, False, False, 4)

        self.logvbox.pack_start(self.lognotebook, False, False, 4)
        self.logvbox.pack_start(self.loghbox, False, False, 4)

        self.logboxLabel = gtk.Label("<b>Server log</b>")
        self.logboxLabel.set_use_markup(True)

        # Expander
        self.expander_size_finalized = False
        self.expander = gtk.Expander(None)
        self.expander.set_label_widget(self.logboxLabel)
        self.expander.connect('notify::expanded', self.__expandlogger)

        # Log to the self.logger function, which sets the buffer for self.debubuffer
        log.addObserver(self.logger)

        self.vbox.pack_start(self.statusBox, False, False, 4)
        self.vbox.pack_start(self.expander, False, False, 0)
        self.expander.set_sensitive(False)

        # This is are the preference widgets that are going to be added and shown later
        self.preferencesVBox = gtk.VBox(False, 7)
        self.preferencesVBoxitems = gtk.VBox(False, 5)
        self.preferencesVBoxitems.set_border_width(2)
        self.preferencesHBox1 = gtk.HBox(False, 0)
        self.preferencesHBox2 = gtk.HBox(False, 0)
        self.preferencesHBox3 = gtk.HBox(False, 0)
        self.preferencesHBox4 = gtk.HBox(False, 0)
        self.preferencesHBox5 = gtk.HBox(False, 0)

        self.preferencesFramesettings = gtk.Frame()
        self.preferencesSettingslabel = gtk.Label("<b>Preferences</b>")
        self.preferencesSettingslabel.set_use_markup(True)
        self.preferencesFramesettings.set_label_widget(self.preferencesSettingslabel)

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
        self.adjustmentport = gtk.Adjustment(float(self.configuration['server']['port']), 1024, 65535, 1, 0, 0)
        self.preferencesSpinport = gtk.SpinButton(self.adjustmentport)
        self.preferencesSpinport.set_numeric(True)

        self.adjustmentquality = gtk.Adjustment(float(self.configuration['screenshot']['quality']), 0, 100, 1, 0, 0)
        self.preferencesSpinquality = gtk.SpinButton(self.adjustmentquality)
        self.preferencesSpinquality.set_numeric(True)

        # Combos
        self.preferencesComboformat = gtk.combo_box_new_text()
        self.preferencesComboformat.connect('changed', self.__preferencesComboChanged)
        self.preferencesComboformat.append_text("JPG")
        self.preferencesComboformat.append_text("PNG")
        if (self.configuration['screenshot']['format'] == "jpeg"):
            self.preferencesComboformat.set_active(0)
        else: 
            self.preferencesComboformat.set_active(1)
            self.preferencesHBox3.set_sensitive(False)

        self.preferencesChecknotifications = gtk.CheckButton()
        if (self.configuration['server']['notify'] == "True"):
            self.preferencesChecknotifications.set_active(1)
        else: 
            self.preferencesChecknotifications.set_active(0)

        self.preferencesButtonClose = gtk.Button("Close", gtk.STOCK_CLOSE)
        self.preferencesButtonClose.connect("clicked", lambda wid: self.__contractpreferences())
        
        self.preferencesButtonAbout = gtk.Button("About", gtk.STOCK_ABOUT)
        self.preferencesButtonAbout.connect("clicked", lambda wid: self.about())

        self.preferencesHBox1.pack_start(self.preferencesLabelport, False, False, 12)
        self.preferencesHBox2.pack_start(self.preferencesLabelformat, False, False, 12)
        self.preferencesHBox3.pack_start(self.preferencesLabelquality, False, False, 12)
        self.preferencesHBox4.pack_start(self.preferencesLabelnotifications, False, False, 12)

        self.preferencesHBox1.pack_end(self.preferencesSpinport, False, False, 7)
        self.preferencesHBox2.pack_end(self.preferencesComboformat, False, False, 7)
        self.preferencesHBox3.pack_end(self.preferencesSpinquality, False, False, 7)
        self.preferencesHBox4.pack_end(self.preferencesChecknotifications, False, False, 7)
        self.preferencesHBox5.pack_start(self.preferencesButtonAbout, False, False, 7)
        self.preferencesHBox5.pack_end(self.preferencesButtonClose, False, False, 7)

        # Hbox4 contains notifications which is only available in some systems
        if not self.itakaglobals.notifyavailable: 
            self.preferencesHBox4.set_sensitive(False)

        # Add Hboxes to the Vbox
        self.preferencesVBoxitems.pack_start(self.preferencesHBox1, False, False, 0)
        self.preferencesVBoxitems.pack_start(self.preferencesHBox2, False, False, 0)
        self.preferencesVBoxitems.pack_start(self.preferencesHBox3, False, False, 0)
        self.preferencesVBoxitems.pack_start(self.preferencesHBox4, False, False, 0)

        self.preferencesFramesettings.add(self.preferencesVBoxitems)
        self.preferencesVBox.pack_start(self.preferencesFramesettings, False, False, 0)
        self.preferencesVBox.pack_start(self.preferencesHBox5, False, False, 4)

        self.window.add(self.vbox)
        self.window.show_all()

        # Once we have all our widgets shown, get the 'initial' real size, for expanding/contracting
        self.window.initial_size = self.window.get_size()

    def save_preferences(self):
        """ Save and hide the preferences dialog """
        # So we can mess with the values in the running one and not mess up our comparison
        self.currentconfiguration = copy.deepcopy(self.configuration)

        # Switch to the proper values
        formatvalue = str(self.preferencesComboformat.get_active_text())
        if formatvalue == "PNG":
            formatvalue = "png"
            self.configuration['screenshot']['format'] = 'png'
        else:
            formatvalue = "jpeg"
            self.configuration['screenshot']['format'] = 'jpeg'

        if self.itakaglobals.notifyavailable:
            notifyvalue = self.preferencesChecknotifications.get_active()
            if notifyvalue:
                notifyvalue = 'True'
                self.menuitemnotifications.set_active(True)
                self.configuration['server']['notify'] = True
            else:
                notifyvalue = 'False'
                self.menuitemnotifications.set_active(False)
                self.configuration['server']['notify'] = False
        else:
            notifyvalue = 'False'
            self.configuration['server']['notify'] = False

        # Build a configuration dictionary to send to the configuration engine's
        # save method. Redundant values must be included for the comparison
        self.configurationdict = {
            'html':
                {'html': '<html><body><img src="screenshot" alt="If you are seeing this message it means there was an error in Itaka or you are using a text-only browser." border="0"></a></body</html>'},

            'screenshot': 
                {'path': '/tmp', 
                'format': formatvalue,
                'quality': str(self.preferencesSpinquality.get_value_as_int())},

            'server': 
                {'port': str(self.preferencesSpinport.get_value_as_int()),
                'notify': notifyvalue}
            }

        # Set them for local use now
        if self.configuration['screenshot']['quality'] != str(self.preferencesSpinquality.get_value_as_int()):
            self.configuration['screenshot']['quality'] = str(self.preferencesSpinquality.get_value_as_int())

        if self.configuration['server']['port'] !=  str(self.preferencesSpinport.get_value_as_int()):
            self.configuration['server']['port'] =  str(self.preferencesSpinport.get_value_as_int())
            self.restart_server()

        # Check if the configuration changed
        if (self.configurationdict != self.currentconfiguration):
            try:
                self.configinstance.save(self.configurationdict)
            except:
                self.console.error(['Gui', 'save'], "Could not save preferences")

    def __expandpreferences(self, params=None):
        """ Callback to expand the window for preferences. """
        # We have a race condition here. If GTK cant resize fast enough, then it gets very sluggish
        # See configure-event signal of gtk.Widget
        # start timer, resize, catch configure-notify, set up idle handler, when idle resize to what the size should be at this point of time, repeat
        if self.preferencesexpanded != True:
            if self.expandtimeout is not None:
                """NOTE: GTK+ GtkWidget.size_request() method can give you the amount of size a widget will take.
                however, it has to be show()ned before. For our little hack, we show the preferencesVBox widgets
                but not itself, which should yield a close enough calculation."""
                self.preferencesFramesettings.show_all()
                self.preferencesHBox5.show_all()

                """If the logger is expanded, use that as the initial size. 
                _expander_size is set by our GtkWindow resize callback
                but we also set a expander_size_finalized variable here
                so that __windowsizechanged doesnt set the new expanded_size over 
                again as our window is expanding here."""
                
                self.expander_size_finalized = False
                if self.expander.get_expanded():
                    self.window.normal_size = self.expander_size
                    self.expander_size_finalized = True
                else:
                    self.window.normal_size = self.window.initial_size

                self.increment = 33
                if self.window.current_size[1] < self.window.normal_size[1]+self.preferencesVBox.size_request()[1]:
                    # Avoid overexpanding our calculation
                    if self.window.current_size[1]+self.increment > self.window.normal_size[1]+self.preferencesVBox.size_request()[1]: 
                        self.increment = (self.window.normal_size[1]+self.preferencesVBox.size_request()[1] - self.window.current_size[1]) 

                    self.window.resize(self.window.current_size[0], self.window.current_size[1]+self.increment)
                    return True
                else:
                    # Its done expanding, add our widgets or display it if it has been done already
                    self.preferencesButton.set_sensitive(False)
                    self.preferencesexpanded = True

                    # Reload our configuration and show the preferences
                    self.configuration = self.configinstance.load(False)
                    if self.preferenceshidden:
                        self.preferencesVBox.show_all()
                    else:
                        self.vbox.pack_start(self.preferencesVBox, False, False, 0)
                        self.preferencesVBox.show_all()
                    
                    self.expandtimeout = None
                    return False
            else:
                self.expandtimeout = gobject.timeout_add(30, self.__expandpreferences)

    def __contractpreferences(self, params=None):
        """ Callback to contract the window of preferences. """
        # TODO: Add save

        if self.contracttimeout is not None:
            # If you dont use the normal_size proxy to our window sizes,
            # it generates a nice effect of doing the animation when closing the expander also. 
            # While sexy, it's inconsistent, and most definately a resource hungry bug.
            if self.expander.get_expanded():
                self.window.normal_size = self.expander_size
                self.expander_size_finalized = True
            else:
                self.window.normal_size = self.window.initial_size
           
            if self.preferencesVBox.get_property("visible"):
                self.preferencesVBox.hide_all()

            if self.window.current_size[1] > self.window.normal_size[1]:
                self.window.resize(self.window.current_size[0], self.window.current_size[1]-self.increment)
                return True
            else:
                # Done, set some variables and stop our timer
                self.preferencesexpanded = False 
                self.preferenceshidden = True
                self.expander.size_finalized = False
                self.preferencesButton.set_sensitive(True)
                
                # Save our settings 
                self.save_preferences()

                self.contracttimeout = None
                return False
        else:
            self.contracttimeout = gobject.timeout_add(30, self.__contractpreferences)

    def __windowsizechanged(self, widget=None, data=None):
        """ This is a callback to always have the latest window size  """
        self.window.current_size = self.window.get_size()
        
        # If the logger is expanded, give them a new size unless our preferences expander is working
        if self.expander.get_expanded() and not self.expander_size_finalized:
            self.expander_size = self.window.current_size
            # If the preferences were expanded before the logger
            if self.preferencesexpanded:
                # Cant assign tuple items
                self.expander_size = [self.expander_size[0], self.expander_size[1] - self.preferencesVBox.size_request()[1]]

    def __statusicon_menu(self, widget, button, time, menu):
        """ Callback to display the menu on the status icon """
        if button == 3:
            if menu:
                menu.show_all()
                menu.popup(None, None, None, 3, time)
            pass

    def statusicon_blinktimeout(self, time=3000):
        """ Callback to set timeout in miliseconds to blink and stop blinking the status icon """
        if self.blinktimeout is None:
            self.statusIcon.set_blinking(True)
            self.blinktimeout = gobject.timeout_add(time, self.statusicon_blinktimeout)
        else:
            self.statusIcon.set_blinking(False)
            self.blinktimeout = None
            return False
 
    def __statusicon_activate(self, widget):
        """ Callback to toggle the window visibility from the status icon """
        if self.window.get_property("visible"):
            # Save it for when we undock because of errors
            self.window_position = self.window.get_position()
            self.window.hide()
        else:
            self.window.show()

    def __statusicon_notify(self, widget):
        """ Callback to disable or enable notifications on the fly from the status icon. 'active' is a boolean for the checkbox """
        if self.menuitemnotifications.get_active():
            self.configuration['server']['notify'] = True
        else:
            self.configuration['server']['notify'] = False

    def about(self, data=None):
        """ Create the About dialog. """
        self.aboutdialog = gtk.AboutDialog()
        self.aboutdialog.set_transient_for(self.window)
        self.aboutdialog.set_name('Itaka')
        self.aboutdialog.set_version(self.itakaglobals.version)
        self.aboutdialog.set_copyright(u'© 2003-2007 Marc E.')
        self.aboutdialog.set_comments('Screenshooting de mercado.')
        self.aboutdialog.set_authors(['Marc E. <santusmarc@gmail.com>'])
        self.aboutdialog.set_artists(['Marc E. <santusmarc@gmail.com>', 'Tango Project (http://tango.freedesktop.org)'])
        self.aboutdialog.set_license('''Itaka is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
any later version.

Itaka is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Itaka; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA''')
        self.aboutdialog.set_website('http://itaka.jardinpresente.com.ar')
        self.aboutdialog.set_logo(gtk.gdk.pixbuf_new_from_file(os.path.join(self.itakaglobals.image_dir, "itaka64x64.png")))
        self.aboutdialog.set_icon(self.icon_pixbuf)
        self.aboutdialog.run()
        self.aboutdialog.destroy()

    def __expandlogger(self, expander, params):
        """ Callback for the expander widget. """
        if self.expander.get_expanded():
            # Show the debugvbox() and it's subwidgets
            self.logvbox.show_all()

            self.expander.add(self.logvbox)
        else:
            self.expander.remove(self.expander.child)
            self.window.resize(self.window.initial_size[0], self.window.initial_size[1])
        return

    def logger(self, args, failure=False, failuretype=None, eventslog=False, detailedmessage=False, icon=None):
        """ Handle logging in the GUI. Arguments: 'args' is a dict { 'key': [str(msg)]], however, when handling failures the message tuple contains an extra item containing a detailed message for separation in the GUI log viewers. 'failure' is a boolean specifying whether we are logging an error. 'failuretype' is a string specyfing what kind of failure it is, either 'error', 'warning' or 'debug'. 'eventslog' is a boolean to specify if the log message will go to the events log. 'eventslog' is a boolean to spcecify if the log message will go to the events log. 'icon' is tuple, the first argument is a string of either 'stock' or 'pixbuf', and the second is a string of gtk.STOCK_ICON or a gtk.gdk.pixbuf object. It is used for the event log in the GUI """

        # Handle twisted errors
        # 'isError': 1, 'failure': <twisted.python.failure.Failure <type 'exceptions.AttributeError'>> 
        if args.has_key('isError') and args['isError'] == 1:
            self.message = str(args['failure'])
        else:
            self.message = args['message'][0]

        # The detailed log gets the detailed mesage on failures
        if failure or detailedmessage:
            self.message = args['message'][1]
    
        # Write out the message to the detailed GUI	
        self.logdetailsbuffer.insert_at_cursor("\r" +self.message,len("\r" + self.message))
        # Automatically scroll. Use wrap until fix.
        self.logdetailstextview.scroll_mark_onscreen(self.logdetailsbuffer.get_insert())

        if eventslog or failure:
            # Use the non-detailed mesage
            self.message = args['message'][0]
            # The event log
            if failure:
                # Failures can not set icons, we set them.
                if failuretype == "error":
                    icon = ['stock', 'STOCK_DIALOG_ERROR']
                elif failuretype == "warning":
                    icon = ['stock', 'STOCK_DIALOG_WARNING']
                elif failuretype == "debug": 
                    icon = ['stock', 'STOCK_DIALOG_INFO']

            if icon is not None:
                if icon[0] == "stock":
                    self.insertediter = self.logeventsstore.append([self.logeventstreeview.render_icon(stock_id=getattr(gtk, icon[1]), size=gtk.ICON_SIZE_MENU, detail=None), self.message])
                    # Select the item if its a failure
                    if failure:
                        self.selection = self.logeventstreeview.get_selection()
                        self.selection.select_iter(self.insertediter)

                else:
                    self.logeventsstore.append([icon[1], self.message])
            else:
                self.logeventsstore.append([None, self.message])

    def clearlogger(self, args):
        """ Callback to clear the log """
        self.logeventsstore.clear()
        self.logdetailsbuffer.set_text("")

    def pauselogger(self, widget, data=None):
        """ Callback to pause log output. """
        if widget.get_active():
            # It would be nice if we could set a center background image to our textview.
            # However, GTK makes that very hard.
            """
            self.logprepausetext = self.logdetailsbuffer.get_text(self.logdetailsbuffer.get_start_iter(), self.logdetailsbuffer.get_end_iter())
            self.logdetailsbuffer.set_text("")

            self.logdetailsbuffer.create_tag ('center-image', justification = gtk.JUSTIFY_CENTER)
            self.logdetailsimageiter = self.logdetailsbuffer.get_iter_at_offset(0)
            self.logdetailsbuffer.insert_pixbuf(self.logdetailsimageiter, self.logdetailstextview.render_icon(stock_id=getattr(gtk, 'STOCK_MEDIA_PAUSE'), size=gtk.ICON_SIZE_DIALOG, detail=None))
            self.logdetailsbuffer.apply_tag_by_name('center-image', self.logdetailsbuffer.get_iter_at_offset(0), self.logdetailsimageiter)

            """
            self.logeventsstore.append([self.logeventstreeview.render_icon(stock_id=getattr(gtk, 'STOCK_MEDIA_PAUSE'), size=gtk.ICON_SIZE_MENU, detail=None), "Logging paused"])
            
            self.logeventstreeview.set_sensitive(False)
            self.logdetailstextview.set_sensitive(False)

            log.removeObserver(self.logger)
        else:
            log.addObserver(self.logger)
            self.logdetailstextview.set_sensitive(True)
            self.logeventstreeview.set_sensitive(True)

            self.logeventsstore.append([self.logeventstreeview.render_icon(stock_id=getattr(gtk, 'STOCK_MEDIA_PLAY'), size=gtk.ICON_SIZE_MENU, detail=None), "Logging resumed"])

    def main(self):
        """ Main init function. Starts the GUI reactors."""

        # Server reactor (interacts with the Twisted reactor)	
        self.sreact = reactor.run()

    def __preferencesComboChanged(self, widget):
        """ Callback for when a preferenes gtk.combo_box is changed """
        if self.preferencesComboformat.get_active_text() == "PNG":
            self.preferencesHBox3.set_sensitive(False)
        else:
            self.preferencesHBox3.set_sensitive(True)

    def __checkwidget(self, widget):
        """ Check the status of the toggle button """
        if hasattr(widget, 'get_active'):
            return widget.get_active()
        else:
            return False

    def startstop(self, widget, traydata=None, dontexpandlogger = False):
        """ Start or stop the screenshooting server. 'traydata' is a string either 'start' or 'stop' to be used from the Status tray icon or error handling. 'dontexpandlogger' handles whether the logger is expanded or not by default when changing status. """
        if (self.__checkwidget(widget) or traydata == "start"):
            if self.server_listening: return
            # NOTE: Twisted doesnt support hot-restarting as stopListening()/startListening(), just use the old one again

            # Set up the twisted site
            # Pass a reference of GUI and Console instance to Screenshot module for its notification handling.
            self.sinstance = iserver.ImageResource(self, self.console)
            self.root = static.Data(self.configuration['html']['html'], 'text/html; charset=UTF-8')
            self.root.putChild('screenshot', self.sinstance)
            self.root.putChild('', self.root)
            self.site = server.Site(self.root)

            # Start the server. Make an instance to distinguish from self.sreactor().
            try:
                self.ilistener = reactor.listenTCP(self.configuration['server']['port'], self.site)
                self.server_listening = True
            except twisted.internet.error.CannotListenError:
                self.console.error(('Gui', 'startstop'), 'Failed to start server, port %d is already in use' % (self.configuration['server']['port']), self)
                # NOTE: This actually calls startstop to stop the server again, acts as a click
                self.buttonStartstop.set_active(False)
                return

            # Announce on log & console stdout
            if self.configuration['screenshot']['format'] == "jpeg":
                self.console.msg(['Server started on port %d' % (self.configuration['server']['port']), 'Server started on port %s TCP. Serving %s images with %d%% quality.' % (self.configuration['server']['port'], self.configuration['screenshot']['format'].upper(), self.configuration['screenshot']['quality'])], self, True, True, ['stock', 'STOCK_CONNECT'])
            else:
                self.console.msg(['Server started on port %d' % (self.configuration['server']['port']), 'Server started on port %s TCP. Serving %s images.' % (self.configuration['server']['port'], self.configuration['screenshot']['format'].upper())], self, True, True, ['stock', 'STOCK_CONNECT'])

            # Change buttons
            self.buttonStartstop.set_active(True)
            self.buttonStartstop.set_label("Stop")
            self.startstopimage.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
            self.buttonStartstop.set_image(self.startstopimage)

            self.statusIcon.set_tooltip("Itaka - Server running")
            self.menuitemstart.set_sensitive(False)
            self.menuitemstop.set_sensitive(True)

            # Close the expander
            self.expander.set_sensitive(True)
        else:
            if self.server_listening:
                self.console.msg("Server stopped", self, True, False, ['stock', 'STOCK_DISCONNECT'])


                self.ilistener.stopListening()
                self.server_listening = False
                # Stop the g_timeout
                if hasattr(self, 'iagotimer'):
                    gobject.source_remove(self.iagotimer)

                # Change GUI elements
                if (traydata):
                    self.buttonStartstop.set_active(False)

                self.statusIcon.set_tooltip("Itaka")
                self.startstopimage.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
                self.buttonStartstop.set_image(self.startstopimage)
                self.buttonStartstop.set_label("Start")
                self.labelLastip.set_text('')
                self.labelTime.set_text('')
                self.labelServed.set_text('')
                if not dontexpandlogger:
                    self.expander.set_expanded(False)				
                    self.expander.set_sensitive(False)
                self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, "itaka.png"))
                self.menuitemstart.set_sensitive(True)
                self.menuitemstop.set_sensitive(False)

    def restart_server(self):
        if self.server_listening:
            self.console.msg("Restarting the server to listen on port %d" % (self.configuration['server']['port']), self, True, False, ['stock', 'STOCK_REFRESH'])
            self.startstop(None, "stop")
            self.startstop(None, "start")

    def destroy(self, *args):
        """ Callback for the main window's destroy. """
        # Stop server.
        if self.server_listening:
            self.console.msg("Shutting down server...")
            self.ilistener.stopListening()
            del self.console
        else:
            # Console goodbye!
            if hasattr(self, 'console'):
                del self.console

        # Remove stale screenshot and quit
        if os.path.exists(os.path.join(self.configuration['screenshot']['path'], 'itakashot.%s' % (self.configuration['screenshot']['format']))): 
            os.remove(os.path.join(self.configuration['screenshot']['path'], 'itakashot.%s' % (self.configuration['screenshot']['format'])))

        # Windows needs this...
        del self.statusIcon

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

        self.labelTime.set_text("<b>When</b>: " + ", ".join(self.pieces) + " ago")
        self.labelTime.set_use_markup(True)

        # Need this so it runs more than once. Weird.
        return True

    def __plural(self, count, singular):
        """ 
        Helper method to handle simple english plural translations.
        
        @type count: int
        @param count: Number.
        @type singular: str
        @param singular: Singular version of the word to pluralize.
        """

        # This is the simplest version; a more general version
        # should handle -y -> -ies, child -> children, etc.
        return '%d %s%s' % (count, singular, ("", 's')[count != 1])

    def notify(self):
        """ Change the image on the main screen, for notification purpose. """
        self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, "itaka.png"))
        self.statusIcon.set_from_pixbuf(self.icon_pixbuf)
        # Only run this event once
        return False

    def update_gui(self, counter=False, ip=False, time=False):
        """ 
        Updates the GUI on request from the server.
        
        @type counter: int
        @param counter: Total number of server hits.
        @type ip: str
        @param ip: IP address of the client.
        @type time: datetime.datetime
        @param time: Time of the request.
        
        """

        self.counter = counter
        self.ip = ip
        self.time = time

        self.console.msg("Screenshot number %d served to %s" % (self.counter, self.ip), self, True, False, ['pixbuf', gtk.gdk.pixbuf_new_from_file(os.path.join(self.itakaglobals.image_dir, "itaka16x16-take.png"))])

        self.labelServed.set_text("<b>Served</b>: %d" % (self.counter))
        self.labelServed.set_use_markup(True)
        self.labelLastip.set_text("<b>Client</b>: %s " % (self.ip))
        self.labelLastip.set_use_markup(True)
        self.statusIcon.set_tooltip("Itaka - %s served" % (self.__plural(self.counter, 'screenshot')))

        # Show the camera image on tray and interface for 1.5 seconds
        self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, "itaka-take.png"))
        self.statusIcon.set_from_file(os.path.join(self.itakaglobals.image_dir, "itaka-take.png"))
        self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, "itaka-take.png"))
        self.notifyimg = gobject.timeout_add(1500, self.notify)

        # Call the update timer function, and add a timer to update the GUI of its
        # "Last screenshot taken" time
        self.__calcsince(time)
        if hasattr(self, 'iagotimer'): gobject.source_remove(self.iagotimer)
        self.iagotimer = gobject.timeout_add(60000, self.__calcsince, time)
