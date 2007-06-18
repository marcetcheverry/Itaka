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
# Copyright 2003-2007 Marc E.
# http://itaka.jardinpresente.com.ar
#
# $Id$

""" Itaka GTK+ GUI """

import sys, os, datetime, traceback, copy 

try:
    from twisted.internet import gtk2reactor
    try:
        gtk2reactor.install()
    except Exception, e:
        print "[*] ERROR: Could not initiate GTK modules: %s" % (e)
        sys.exit(1)
    from twisted.internet import reactor
except ImportError:
    print "[*] ERROR: Could not import Twisted Network Framework"
    sys.exit(1)

try:
    import server as iserver
    import error
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
    import gtk, gobject, pango
except ImportError:
    print "[*] ERROR: GTK+ bindings are missing"
    sys.exit(1)

if gtk.gtk_version[1] < 10:
    print "[*] ERROR: Itaka requires GTK+ 2.10, you have %s installed" % (".".join(str(x) for x in gtk.gtk_version))
    sys.exit(1)

class GuiLog:
    """
    GTK+ GUI logging handler.
    """

    def __init__(self, guiinstance, console, configuration):
        """
        Constructor.

        @type guiinstance: instance
        @param guiinstance: Instance of L{Gui}

        @type console: instance
        @param console: Instance of L{Console}

        @type configuration: dict
        @param configuration: Configuration values dictionary from L{ConfigParser}
        """

        self.gui = guiinstance
        self.console = console
        self.configuration = configuration

    def twisted_observer(self, args):
        """
        A log observer for our Twisted server

        @type args: dict
        @param args: dict {'key': [str(message)]]}
        """

        # Handle twisted errors
        # 'isError': 1, 'failure': <twisted.python.failure.Failure <type 'exceptions.AttributeError'>> 
        if args.has_key('isError') and args['isError'] == 1:
            self.msg = str(args['failure'])
        else:
            self.msg = args['message'][0]

        self._write_detailed_log(self.msg, False)

    def message(self, message, icon=None):
        """
        Write normal message on Gui log widgets.

        @type message: str
        @param message: Message to be inserted.

        @type icon: tuple
        @param icon: The first argument is a string of either 'stock' or 'pixbuf', and the second is a string of gtk.STOCK_ICON or a gtk.gdk.pixbuf object (without the 'gtk.' prefix).
        """
        
        self.console.message(message)
        self._write_gui_log(message, None, icon, False)

    def detailed_message(self, message, detailedmessage, icon=None):
        """
        Write detailed message on Gui log widgets.

        @type message: str
        @param message: Message to be inserted in the events log.

        @type detailedmessage: str
        @param detailedmessage: Message to be inserted in the detailed log.

        @type icon: tuple
        @param icon: The first argument is a string of either 'stock' or 'pixbuf', and the second is a string of gtk.STOCK_ICON or a gtk.gdk.pixbuf object (without the 'gtk.' prefix).
        """

        self.console.message(detailedmessage)
        self._write_gui_log(message, detailedmessage, icon, False, False)

    def failure(self, caller, message, failuretype='ERROR'):
        """
        Write failure message on Gui log widgets.

        @type caller: tuple
        @param caller: Specifies the class and method were the warning ocurred.

        @type message: tuple
        @param message: A tuple containing first the simple message to the events log, and then the detailed message for the detailed log.

        @type failuretype: str
        @param failuretype: What kind of failure it is, either 'ERROR' (default), 'WARNING' or 'DEBUG'
        """
        
        self.simplemessage = message[0]
        self.detailedmessage = message[1]

        self.console.failure(caller, self.detailedmessage, failuretype)

        # ERRORS require some more actions
        if failuretype == 'ERROR':
            # Show the window and its widgets, set the status icon blinking timeout
            if not self.gui.window.get_property("visible"):
                self.gui.window.present()
                self.gui.statusicon_blinktimeout()
                self.gui.window.move(self.gui.window_position[0], self.gui.window_position[1])

            self.gui.expander.set_expanded(True)
            self.gui.expander.set_sensitive(True)
            # Stop the server
            if self.gui.server.listening():
                self.gui.stop_server(None, True)

        self._write_gui_log(self.simplemessage, self.detailedmessage, self._get_failure_icon(failuretype), True, True)

    def _get_failure_icon(self, failuretype):
        """
        Return a default stock icon for a failure type.

        @type failuretype: str
        @param failuretype: What kind of failure it is, either 'ERROR' (default), 'WARNING' or 'DEBUG'

        @rtype: tuple
        @return: An GTK+ stock icon definition. ['stock', 'STOCK_ICON']
        """
        # Default icon is always STOCK_DIALOG_ERROR
        icon = ['stock', 'STOCK_DIALOG_ERROR']
        
        if failuretype == "WARNING":
            icon = ['stock', 'STOCK_DIALOG_WARNING']
        elif failuretype == "DEBUG": 
            icon = ['stock', 'STOCK_DIALOG_INFO']

        return icon

    def _write_gui_log(self, message, detailedmessage=None, icon=None, unpauselogger=True, failure=False):
        """
        Private method to write to both Gui logs.

        @type message: str
        @param message: Message to be inserted.

        @type detailedmessage: str
        @param detailedmessage: Optional detailed message if the event log and detailed log messages differ.

        @type icon: tuple
        @param icon: The first argument is a string of either 'stock' or 'pixbuf', and the second is a string of gtk.STOCK_ICON or a gtk.gdk.pixbuf object (without the 'gtk.' prefix).

        @type unpauselogger: bool
        @param unpauselogger: Whether to unpause the GUI Logger.

        @type failure: bool
        @param failure: Whether the message is a failure or not.
        """

        if detailedmessage is None:
            detailedmessage = message

        # Only write messages when the logging is unpaused. Unless we are told otherwise
        if self.gui.log_paused():
            if unpauselogger:
                self.gui.unpause_log(True)
                self._write_events_log(message, icon, failure)
                self._write_detailed_log(detailedmessage)
        else:
            self._write_events_log(message, icon, failure)
            self._write_detailed_log(detailedmessage)

    def _write_events_log(self, message, icon=None, failure=False):
        """
        Private method to write to the events log Gui widget.

        @type message: str
        @param message: Message to be inserted.

        @type icon: tuple
        @param icon: The first argument is a string of either 'stock' or 'pixbuf', and the second is a string of gtk.STOCK_ICON or a gtk.gdk.pixbuf object (without the 'gtk.' prefix) if its stock, or a pixbuf.

        @type failure: bool
        @param failure: Whether the message is a failure or not.
        """

        if icon is not None:
            if icon[0] == "stock":
                self.inserted_iter = self.gui.logeventsstore.append([self.gui.logeventstreeview.render_icon(stock_id=getattr(gtk, icon[1]), size=gtk.ICON_SIZE_MENU, detail=None), message])
                # Select the iter if it's a failure
                if failure:
                    self.selection = self.gui.logeventstreeview.get_selection()
                    self.selection.select_iter(self.inserted_iter)
            else:
                self.inserted_iter = self.gui.logeventsstore.append([icon[1], message])
        else:
            self.inserted_iter = self.gui.logeventsstore.append([icon, message])

        # Scroll
        self.gui.logeventstreeview.scroll_to_cell(self.gui.logeventstreeview.get_model().get_path(self.inserted_iter))

    def _write_detailed_log(self, message, bold=True):
        """
        Private method to write to the detailed log Gui widget.

        @type message: str
        @param message: Message to be inserted.

        @type bold: bool
        @param bold: Whether the text will be inserted as bold.
        """

        message = message + '\r'

        if bold:
            self.gui.logdetailsbuffer.insert_with_tags_by_name(self.gui.logdetailsbuffer.get_end_iter(), message, 'bold-text')
        else:
            self.gui.logdetailsbuffer.insert_at_cursor(message, len(message))

        # Automatically scroll. Use wrap until fix.
        self.gui.logdetailstextview.scroll_mark_onscreen(self.gui.logdetailsbuffer.get_insert())

class Gui:
    """
    GTK+ GUI
    """

    def __init__(self, consoleinstance, configuration):
        """
        Constructor.

        @type consoleinstance: instance
        @param consoleinstance: An instance of the L{Console} class.

        @type configuration: tuple
        @param configuration: A tuple of configuration globals and an instance of L{ConfigParser}
        """

        # Load our configuration and console instances and values
        self.console = consoleinstance
        self.itakaglobals = configuration[0]

        # The configuration instance has the user's preferences already loaded.
        self.configinstance = configuration[1]
        self.configuration = self.itakaglobals.values

        # Instances of our Gui Logging class and Screenshot Server
        self.server = iserver.ScreenshotServer(self)
        self.log = GuiLog(self, self.console, self.configuration)
        self.logpaused = False

        # Start defining widgets
        self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(self.itakaglobals.image_dir, 'itaka.png'))
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect('destroy', self.destroy)
        self.window.connect('size-allocate', self.windowsizechanged)
        self.window.set_title('Itaka')
        self.window.set_icon(self.icon_pixbuf)
        self.window.set_border_width(6)
        self.window.set_default_size(370, 1)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window_position = self.window.get_position()

        # Create our tray icon
        self.statusIcon = gtk.StatusIcon()
        self.statusmenu = gtk.Menu()
        if self.configuration['server']['authentication']:
            self.statusIcon.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(os.path.join(self.itakaglobals.image_dir, 'itaka-secure.png')))
        else:
            self.statusIcon.set_from_pixbuf(self.icon_pixbuf)
        self.statusIcon.set_tooltip('Itaka')
        self.statusIcon.set_visible(True)
        self.statusIcon.connect('activate', self.statusicon_activate)
        self.statusIcon.connect('popup-menu', self.statusicon_menu, self.statusmenu)

        self.startimage = gtk.Image()
        self.startimage.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)

        self.stopimage = gtk.Image()
        self.stopimage.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_MENU)
        self.menuitemstart = gtk.ImageMenuItem('Start') 
        self.menuitemstart.set_image(self.startimage)
        self.menuitemstart.connect('activate', self.start_server, True)
        self.menuitemstop = gtk.ImageMenuItem('Stop') 
        self.menuitemstop.set_image(self.stopimage)
        self.menuitemstop.connect('activate', self.stop_server, True)
        self.menuitemstop.set_sensitive(False)

        if self.itakaglobals.notifyavailable: 
            self.menuitemnotifications = gtk.CheckMenuItem('Show Notifications')
            if self.configuration['server']['notify']:
                self.menuitemnotifications.set_active(True)
            self.menuitemnotifications.connect('toggled', self.statusicon_notify)

        self.menuitemseparator = gtk.SeparatorMenuItem()
        self.menuitemseparator1 = gtk.SeparatorMenuItem()
        self.menuitemquit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.menuitemquit.connect('activate', self.destroy)

        self.statusmenu.append(self.menuitemstart)
        self.statusmenu.append(self.menuitemstop)
        if self.itakaglobals.notifyavailable: 
            self.statusmenu.append(self.menuitemseparator)
            self.statusmenu.append(self.menuitemnotifications)
        self.statusmenu.append(self.menuitemseparator1)
        self.statusmenu.append(self.menuitemquit)

        self.vbox = gtk.VBox(False, 6)
        self.box = gtk.HBox(False, 0)

        self.itakaLogo = gtk.Image()
        if self.configuration['server']['authentication']:
            self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, 'itaka-secure.png'))
        else:
            self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, 'itaka.png'))
        self.itakaLogo.show()

        self.box.pack_start(self.itakaLogo, False, False, 35)

        self.buttonStartstop = gtk.ToggleButton('Start', gtk.STOCK_PREFERENCES)
        self.startstopimage = gtk.Image()

        self.startstopimage.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
        self.buttonStartstop.set_image(self.startstopimage)
        self.buttonStartstop.connect('toggled', self.button_start_server)

        self.preferencesButton = gtk.Button('Preferences', gtk.STOCK_PREFERENCES)
        self.preferencesButton.connect('clicked', self.expandpreferences)

        # Set up some variables for our timeouts/animations
        self.preferenceshidden = False
        self.preferencesexpanded = False
        self.contracttimeout = None
        self.expandtimeout = None
        self.blinktimeout = None

        self.box.pack_start(self.buttonStartstop, True, True, 5)
        self.box.pack_start(self.preferencesButton, True, True, 8)

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

        self.logeventslabel = gtk.Label('Events')
        self.logdetailslabel = gtk.Label('Details')

        self.logeventsscroll = gtk.ScrolledWindow()
        self.logeventsscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.logeventsscroll.set_shadow_type(gtk.SHADOW_NONE)

        self.logeventsstore = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.logeventstreeview = gtk.TreeView(self.logeventsstore)
        self.logeventstreeview.set_property('headers-visible', False)
        self.logeventstreeview.set_property('rules-hint', True)

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
        self.logdetailsbuffer.create_tag ('bold-text', weight = pango.WEIGHT_BOLD)
        self.logdetailsscroll.add(self.logdetailstextview)

        self.lognotebook.append_page(self.logeventsscroll, self.logeventslabel)
        self.lognotebook.append_page(self.logdetailsscroll, self.logdetailslabel)

        self.loghbox = gtk.HBox(False, 0)
        self.logclearbutton = gtk.Button('Clear')
        self.logclearbuttonimage = gtk.Image()
        self.logclearbuttonimage.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
        self.logclearbutton.set_image(self.logclearbuttonimage)
        self.logclearbutton.connect('clicked', self.clearlogger)

        self.logpausebutton = gtk.ToggleButton('Pause')
        self.logpausebuttonimage = gtk.Image()
        self.logpausebuttonimage.set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
        self.logpausebutton.set_image(self.logpausebuttonimage)
        self.logpausebutton.connect('toggled', self.button_pause_log)

        self.loghbox.pack_end(self.logclearbutton, False, False, 4)
        self.loghbox.pack_end(self.logpausebutton, False, False, 4)

        self.logvbox.pack_start(self.lognotebook, False, False, 4)
        self.logvbox.pack_start(self.loghbox, False, False, 4)

        self.logboxLabel = gtk.Label('<b>Server log</b>')
        self.logboxLabel.set_use_markup(True)

        self.expander_size_finalized = False
        self.expander = gtk.Expander(None)
        self.expander.set_label_widget(self.logboxLabel)
        self.expander.connect('notify::expanded', self.expandlogger)

        self.vbox.pack_start(self.statusBox, False, False, 4)
        self.vbox.pack_start(self.expander, False, False, 0)
        self.expander.set_sensitive(False)

        # This is are the preference widgets that are going to be added and shown later
        self.preferencesVBox = gtk.VBox(False, 7)
        self.preferencesVBoxitems = gtk.VBox(False, 5)
        self.preferencesVBoxitems.set_border_width(2)
        
        # Create our Hboxes
        for n in xrange(1, 10+1):
            setattr(self, 'preferencesHBox%d' % (n), gtk.HBox(False, 0))

        self.preferencesFramesettings = gtk.Frame()
        self.preferencesSettingslabel = gtk.Label('<b>Preferences</b>')
        self.preferencesSettingslabel.set_use_markup(True)
        self.preferencesFramesettings.set_label_widget(self.preferencesSettingslabel)

        self.preferencesLabelport = gtk.Label('Port  ')
        self.preferencesLabelport.set_justify(gtk.JUSTIFY_LEFT)
        self.preferencesLabelport.set_alignment(0, 0.60)

        self.preferencesLabelauth = gtk.Label('Authentication   ')
        self.preferencesLabelauth.set_justify(gtk.JUSTIFY_LEFT)
        self.preferencesLabelauth.set_alignment(0, 0.60)

        self.preferencesLabeluser = gtk.Label('Username ')
        self.preferencesLabeluser.set_justify(gtk.JUSTIFY_LEFT)
        self.preferencesLabeluser.set_alignment(0, 0.60)

        self.preferencesLabelpass = gtk.Label('Password  ')
        self.preferencesLabelpass.set_justify(gtk.JUSTIFY_LEFT)
        self.preferencesLabelpass.set_alignment(0, 0.60)

        self.preferencesLabelformat = gtk.Label('Format  ')
        self.preferencesLabelformat.set_justify(gtk.JUSTIFY_LEFT)
        self.preferencesLabelformat.set_alignment(0, 0.50)

        self.preferencesLabelquality = gtk.Label('Quality  ')
        self.preferencesLabelquality.set_justify(gtk.JUSTIFY_LEFT)
        self.preferencesLabelquality.set_alignment(0, 0.50)

        self.preferencesLabelscale = gtk.Label('Scale  ')
        self.preferencesLabelscale.set_justify(gtk.JUSTIFY_LEFT)
        self.preferencesLabelscale.set_alignment(0, 0.50)

        if not self.itakaglobals.system == 'nt':
            self.preferencesLabelscreenshot = gtk.Label('Screenshot window  ')
            self.preferencesLabelscreenshot.set_justify(gtk.JUSTIFY_LEFT)
            self.preferencesLabelscreenshot.set_alignment(0, 0.50)

        if self.itakaglobals.notifyavailable: 
            self.preferencesLabelnotifications = gtk.Label('Notifications  ')
            self.preferencesLabelnotifications.set_justify(gtk.JUSTIFY_LEFT)
            self.preferencesLabelnotifications.set_alignment(0, 0.50)

        self.adjustmentport = gtk.Adjustment(float(self.configuration['server']['port']), 1024, 65535, 1, 0, 0)
        self.preferencesSpinport = gtk.SpinButton(self.adjustmentport)
        self.preferencesSpinport.set_numeric(True)

        self.preferencesEntryuser = gtk.Entry()
        self.preferencesEntryuser.set_width_chars(11)
        self.preferencesEntryuser.set_text(self.configuration['server']['username'])

        self.preferencesEntrypass = gtk.Entry()
        self.preferencesEntrypass.set_width_chars(11)
        if self.itakaglobals.system == 'nt':
            char = '*'
        else:
            char = u'\u25cf'

        self.preferencesEntrypass.set_invisible_char(char)
        self.preferencesEntrypass.set_visibility(False)
        self.preferencesEntrypass.set_text(self.configuration['server']['password'])

        self.preferencesCheckauth = gtk.CheckButton()
        self.preferencesCheckauth.connect('toggled', self._preferences_authentication_toggled)
        if self.configuration['server']['authentication']:
            self.preferencesCheckauth.set_active(1)
        else: 
            self.preferencesCheckauth.set_active(0)

        if not self.configuration['server']['authentication']:
            self.preferencesEntryuser.set_sensitive(False)
            self.preferencesEntrypass.set_sensitive(False)

        self.adjustmentquality = gtk.Adjustment(float(self.configuration['screenshot']['quality']), 0, 100, 1, 0, 0)
        self.preferencesSpinquality = gtk.SpinButton(self.adjustmentquality)
        self.preferencesSpinquality.set_numeric(True)

        self.adjustmentscale = gtk.Adjustment(float(self.configuration['screenshot']['scalepercent']), 1, 100, 1, 0, 0)
        self.preferencesSpinscale = gtk.SpinButton(self.adjustmentscale)
        self.preferencesSpinscale.set_numeric(True)

        self.preferencesComboformat = gtk.combo_box_new_text()
        self.preferencesComboformat.connect('changed', self._preferences_combo_changed)
        self.preferencesComboformat.append_text('JPG')
        self.preferencesComboformat.append_text('PNG')
        if self.configuration['screenshot']['format'] == 'jpeg':
            self.preferencesComboformat.set_active(0)
        else: 
            self.preferencesComboformat.set_active(1)
            self.preferencesHBox3.set_sensitive(False)

        if self.itakaglobals.notifyavailable: 
            self.preferencesChecknotifications = gtk.CheckButton()
            if self.configuration['server']['notify']:
                self.preferencesChecknotifications.set_active(1)
            else: 
                self.preferencesChecknotifications.set_active(0)

        if not self.itakaglobals.system == 'nt':
            self.preferencesComboscreenshot = gtk.combo_box_new_text()
            self.preferencesComboscreenshot.append_text('Fullscreen')
            self.preferencesComboscreenshot.append_text('Active window')
            if self.configuration['screenshot']['currentwindow']:
                self.preferencesComboscreenshot.set_active(1)
            else: 
                self.preferencesComboscreenshot.set_active(0)

        self.preferencesButtonClose = gtk.Button('Close', gtk.STOCK_CLOSE)
        self.preferencesButtonClose.connect('clicked', lambda wid: self.contractpreferences())
        
        self.preferencesButtonAbout = gtk.Button('About', gtk.STOCK_ABOUT)
        self.preferencesButtonAbout.connect('clicked', lambda wid: self.about())

        self.preferencesHBox1.pack_start(self.preferencesLabelport, False, False, 12)
        self.preferencesHBox1.pack_end(self.preferencesSpinport, False, False, 7)
        self.preferencesHBox2.pack_start(self.preferencesLabelauth, False, False, 12)
        self.preferencesHBox3.pack_start(self.preferencesLabeluser, False, False, 12)
        self.preferencesHBox4.pack_end(self.preferencesEntrypass, False, False, 7)
        self.preferencesHBox4.pack_start(self.preferencesLabelpass, False, False, 12)
        self.preferencesHBox3.pack_end(self.preferencesEntryuser, False, False, 7)
        self.preferencesHBox2.pack_end(self.preferencesCheckauth, False, False, 7)
        self.preferencesHBox5.pack_start(self.preferencesLabelformat, False, False, 12)
        self.preferencesHBox5.pack_end(self.preferencesComboformat, False, False, 7)
        self.preferencesHBox6.pack_start(self.preferencesLabelquality, False, False, 12)
        self.preferencesHBox6.pack_end(self.preferencesSpinquality, False, False, 7)
        if not self.itakaglobals.system == 'nt':
            self.preferencesHBox7.pack_start(self.preferencesLabelscreenshot, False, False, 12)
            self.preferencesHBox7.pack_end(self.preferencesComboscreenshot, False, False, 7)
        self.preferencesHBox8.pack_start(self.preferencesLabelscale, False, False, 12)
        self.preferencesHBox8.pack_end(self.preferencesSpinscale, False, False, 7)
        if self.itakaglobals.notifyavailable: 
            self.preferencesHBox9.pack_start(self.preferencesLabelnotifications, False, False, 12)
            self.preferencesHBox9.pack_end(self.preferencesChecknotifications, False, False, 7)
        self.preferencesHBox10.pack_start(self.preferencesButtonAbout, False, False, 7)
        self.preferencesHBox10.pack_end(self.preferencesButtonClose, False, False, 7)

        self.preferencesVBoxitems.pack_start(self.preferencesHBox1, False, False, 0)
        self.preferencesVBoxitems.pack_start(self.preferencesHBox2, False, False, 0)
        self.preferencesVBoxitems.pack_start(self.preferencesHBox3, False, False, 0)
        self.preferencesVBoxitems.pack_start(self.preferencesHBox4, False, False, 0)
        self.preferencesVBoxitems.pack_start(self.preferencesHBox5, False, False, 0)
        if not self.itakaglobals.system == 'nt':
            self.preferencesVBoxitems.pack_start(self.preferencesHBox7, False, False, 0)
        self.preferencesVBoxitems.pack_start(self.preferencesHBox8, False, False, 0)
        if self.itakaglobals.notifyavailable: 
            self.preferencesVBoxitems.pack_start(self.preferencesHBox9, False, False, 0)

        self.preferencesFramesettings.add(self.preferencesVBoxitems)
        self.preferencesVBox.pack_start(self.preferencesFramesettings, False, False, 0)
        self.preferencesVBox.pack_start(self.preferencesHBox10, False, False, 4)

        self.window.add(self.vbox)
        self.window.show_all()

        # Once we have all our widgets shown, get the 'initial' real size, for expanding/contracting
        self.window.initial_size = self.window.get_size()

    def save_preferences(self):
        """
        Saves and hides the preferences dialog.
        """
        
        # So we can mess with the values in the running one and not mess up our comparison
        self.currentconfiguration = copy.deepcopy(self.configuration)

        # Switch to the proper values
        formatvalue = str(self.preferencesComboformat.get_active_text())
        if formatvalue == 'PNG':
            formatvalue = 'png'
            self.configuration['screenshot']['format'] = 'png'
        else:
            formatvalue = 'jpeg'
            self.configuration['screenshot']['format'] = 'jpeg'

        if self.itakaglobals.notifyavailable:
            notifyvalue = self.preferencesChecknotifications.get_active()
            if notifyvalue:
                notifyvalue = True
                self.menuitemnotifications.set_active(True)
                self.configuration['server']['notify'] = True
            else:
                notifyvalue = False
                self.menuitemnotifications.set_active(False)
                self.configuration['server']['notify'] = False
        else:
            notifyvalue = False
            self.configuration['server']['notify'] = False

        if not self.itakaglobals.system == 'nt':
            if self.preferencesComboscreenshot.get_active_text() == 'Active window':
                self.configuration['screenshot']['currentwindow'] = True
                screenshotvalue = True
            else:
                self.configuration['screenshot']['currentwindow'] = False
                screenshotvalue = False
        else:
            screenshotvalue = False
            self.configuration['screenshot']['currentwindow'] = False

        scale = [self.preferencesSpinscale.get_value_as_int()]
        if scale[0] == 100:
            self.configuration['screenshot']['scale'] = False
            scale.append(False)
        else:
            self.configuration['screenshot']['scale'] = True
            scale.append(True)

        if self.configuration['screenshot']['scalepercent'] != scale[0]:
            self.configuration['screenshot']['scalepercent'] = scale[0]
        
        # Build a configuration dictionary to send to the configuration engine's
        # save method. Redundant values must be included for the comparison
        self.configurationdict = {
            'html':
                {'html': '<html><body><img src="screenshot" alt="If you are seeing this message it means there was an error in Itaka or you are using a text-only browser." border="0"></a></body</html>'},

            'screenshot': 
                {'path': self.configuration['screenshot']['path'],
                'format': formatvalue,
                'quality': self.preferencesSpinquality.get_value_as_int(),
                'currentwindow': screenshotvalue,
                'scale': scale[1],
                'scalepercent': scale[0]},

            'server': 
                {'username': self.preferencesEntryuser.get_text(),
                'authentication': self.preferencesCheckauth.get_active(),
                'notify': notifyvalue,
                'password': self.preferencesEntrypass.get_text(),
                'port': self.preferencesSpinport.get_value_as_int()}
            }

        # Set them for local use now
        if self.configuration['screenshot']['quality'] != self.preferencesSpinquality.get_value_as_int():
            self.configuration['screenshot']['quality'] = self.preferencesSpinquality.get_value_as_int()

        if self.configuration['server']['port'] !=  self.preferencesSpinport.get_value_as_int():
            self.configuration['server']['port'] =  self.preferencesSpinport.get_value_as_int()
            self.restart_server()

        if self.configuration['server']['authentication'] is not self.preferencesCheckauth.get_active():
            self.configuration['server']['authentication'] = self.preferencesCheckauth.get_active()

        if self.configuration['server']['username'] != self.preferencesEntryuser.get_text():
            self.configuration['server']['username'] = self.preferencesEntryuser.get_text()

        if self.configuration['server']['password'] != self.preferencesEntrypass.get_text():
            self.configuration['server']['password'] = self.preferencesEntrypass.get_text()

        # Check if the configuration changed
        if (self.configurationdict != self.currentconfiguration):

            # Update the needed keys.
            try:
                # self.configinstance.save(self.configurationdict)
                for section in self.configurationdict:
                    [self.configinstance.update(section, key, value) for key, value in self.configurationdict[section].iteritems() if key not in self.currentconfiguration[section] or self.currentconfiguration[section][key] != value]
            except:
                self.log.failure(('Gui', 'save_preferences'), "Could not save preferences", 'ERROR')

    def expandpreferences(self, *args):
        """
        Expands the window for preferences.
        """

        # We have a race condition here. If GTK cant resize fast enough, then it gets very sluggish
        # See configure-event signal of gtk.Widget
        # start timer, resize, catch configure-notify, set up idle handler, when idle resize to what the size should be at this point of time, repeat
        if not self.preferencesexpanded:
            if self.expandtimeout is not None:
                """NOTE: GTK+ GtkWidget.size_request() method can give you the amount of size a widget will take.
                however, it has to be show()ned before. For our little hack, we show the preferencesVBox widgets
                but not itself, which should yield a close enough calculation."""
                self.preferencesFramesettings.show_all()
                self.preferencesHBox10.show_all()

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
                    self.configuration = self.configinstance.load()
                    if self.preferenceshidden:
                        self.preferencesVBox.show_all()
                    else:
                        self.vbox.pack_start(self.preferencesVBox, False, False, 0)
                        self.preferencesVBox.show_all()
                    
                    self.expandtimeout = None
                    return False
            else:
                self.expandtimeout = gobject.timeout_add(30, self.expandpreferences)

    def contractpreferences(self, *args):
        """
        Contracts the window of preferences.
        """

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
            self.contracttimeout = gobject.timeout_add(30, self.contractpreferences)

    def windowsizechanged(self, widget=None, data=None):
        """
        Report the window size on change.
        
        @type widget: instance
        @param widget: gtk.Widget.

        @type data: unknown
        @param data: Unknown.
        """
        
        self.window.current_size = self.window.get_size()
        
        # If the logger is expanded, give them a new size unless our preferences expander is working
        if self.expander.get_expanded() and not self.expander_size_finalized:
            self.expander_size = self.window.current_size
            # If the preferences were expanded before the logger
            if self.preferencesexpanded:
                # Cant assign tuple items
                self.expander_size = [self.expander_size[0], self.expander_size[1] - self.preferencesVBox.size_request()[1]]

    def statusicon_menu(self, widget, button, time, menu):
        """
        Display the menu on the status icon.
        
        @type widget: instance
        @param widget: gtk.Widget.

        @type button: int
        @param button: The button pressed..

        @type time: unknown
        @param time: Unknown.

        @type menu: instance
        @param menu: A gtk.Menu instance.
        """

        if button == 3:
            if menu:
                menu.show_all()
                menu.popup(None, None, None, 3, time)
            pass

    def statusicon_blinktimeout(self, time=3000):
        """
        Sets the timeout in miliseconds to blink and stop blinking the status icon.
        
        @type time: int
        @param time: Time in milliseconds to blink the status icon
        """

        if self.blinktimeout is None:
            self.statusIcon.set_blinking(True)
            self.blinktimeout = gobject.timeout_add(time, self.statusicon_blinktimeout)
        else:
            self.statusIcon.set_blinking(False)
            self.blinktimeout = None
            return False
 
    def statusicon_activate(self, widget):
        """
        Toggle the window visibility from the status icon when clicked.
        
        @type widget: instance
        @param widget: gtk.Widget.
        """

        if self.window.get_property("visible"):
            # Save it for when we undock because of errors
            self.window_position = self.window.get_position()
            self.window.hide()
        else:
            self.window.show()

    def statusicon_notify(self, widget):
        """
        Disable or enable notifications on the fly from the status icon.
        
        @type widget: instance
        @param widget: gtk.Widget.
        """

        if self.checkwidget(self.menuitemnotifications):
            self.configuration['server']['notify'] = True
        else:
            self.configuration['server']['notify'] = False

    def about(self, *args):
        """
        Creates the About dialog.
        """

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

    def expandlogger(self, expander, params):
        """
        Expand or contract the logger.
        
        @type expander: instance
        @param expander: gtk.Expander instance

        @type params: unknown
        @param params: Unknown.
        """

        if self.expander.get_expanded():
            # Show the debugvbox() and it's subwidgets
            self.logvbox.show_all()

            self.expander.add(self.logvbox)
        else:
            self.expander.remove(self.expander.child)
            self.window.resize(self.window.initial_size[0], self.window.initial_size[1])
        return

    def clearlogger(self, *args):
        """
        Clear the log.
        """

        self.logeventsstore.clear()
        self.logdetailsbuffer.set_text("")

    def button_pause_log(self, widget):
        """
        Interface to pause or unpause the Gui logger by checking the status of a gtk.ToggleButton
        
        @type widget: instance
        @param widget: gtk.Widget.
        """

        if self.checkwidget(widget):
            if not self.log_paused():
                self.pause_log()
        else:
            if self.log_paused():
                self.unpause_log()

    def pause_log(self):
        """
        Pause Gui log output.
        """

        # It would be nice if we could set a center background image to our textview.
        # However, GTK makes that very hard.
        """
        self.logprepausetext = self.logdetailsbuffer.get_text(self.logdetailsbuffer.get_start_iter(), self.logdetailsbuffer.get_end_iter())
        self.logdetailsbuffer.set_text("")

        self.logdetailsbuffer.create_tag ('center-image', justification = gtk.JUSTIFY_CENTER)
        self.logdetailsimageiter = self.logdetailsbuffer.get_iter_at_offset(0)
        self.logdetailsbuffer.insert_pixbuf(self.logdetailsimageiter, self.logdetailstextview.render_icon(stock_id=gtk.STOCK_MEDIA_PAUSE, size=gtk.ICON_SIZE_DIALOG, detail=None))
        self.logdetailsbuffer.apply_tag_by_name('center-image', self.logdetailsbuffer.get_iter_at_offset(0), self.logdetailsimageiter)

        """
        self.logeventsstore.append([self.logeventstreeview.render_icon(stock_id=gtk.STOCK_MEDIA_PAUSE, size=gtk.ICON_SIZE_MENU, detail=None), "Logging paused"])
        
        self.logeventstreeview.set_sensitive(False)
        self.logdetailstextview.set_sensitive(False)

        self.server.remove_log_observer()
        self.logpaused = True

    def unpause_log(self, foreign=False):
        """
        Unpause Gui log output.

        @type foreign: bool
        @param foreign: Whether the caller of this method is not the Gui gtk.ToggleButton.
        """

        self.server.add_log_observer(self.log.twisted_observer)
        if (foreign):
            self.logpausebutton.set_active(False)
        self.logdetailstextview.set_sensitive(True)
        self.logeventstreeview.set_sensitive(True)

        self.logeventsstore.append([self.logeventstreeview.render_icon(stock_id=gtk.STOCK_MEDIA_PLAY, size=gtk.ICON_SIZE_MENU, detail=None), "Logging resumed"])

        self.logpaused = False

    def log_paused(self):
        """
        Whether the Gui log is paused.

        @rtype: bool
        @return: True if the Gui log is paused. False otherwise
        """
        
        return self.logpaused

    def main(self):
        """
        Main initiation function. Starts the Twisted GUI reactors.
        """

        # Server reactor (interacts with the Twisted reactor)	
        self.sreact = reactor.run()

    def _preferences_combo_changed(self, widget):
        """
        Callback for preferenes gtk.ComboBox widget

        @type widget: instance
        @param widget: gtk.Widget.
        """
        
        if self.preferencesComboformat.get_active_text() == "PNG":
            self.preferencesHBox3.set_sensitive(False)
        else:
            self.preferencesHBox3.set_sensitive(True)

    def _preferences_authentication_toggled(self, widget):
        """
        Callback for preferences gtk.CheckButton widget.

        @type widget: instance
        @param widget: gtk.Widget.
        """

        if self.checkwidget(widget):
            self.preferencesEntryuser.set_sensitive(True)
            self.preferencesEntrypass.set_sensitive(True)
            self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, "itaka-secure.png"))
            self.statusIcon.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(os.path.join(self.itakaglobals.image_dir, "itaka-secure.png")))
        else:
            self.preferencesEntryuser.set_sensitive(False)
            self.preferencesEntrypass.set_sensitive(False)
            self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, "itaka.png"))
            self.statusIcon.set_from_pixbuf(self.icon_pixbuf)


    def checkwidget(self, widget):
        """
        Checks if a gtk.Widget is active.

        @type widget: instance
        @param widget: gtk.Widget.
        """

        if hasattr(widget, 'get_active') and callable(getattr(widget, 'get_active')):
            return widget.get_active()
        else:
            return False

    def button_start_server(self, widget):
        """
        Interface to start or stop the server by checking the status of a gtk.ToggleButton
        
        @type widget: instance
        @param widget: gtk.Widget.
        """
        if self.checkwidget(widget):
            self.start_server()
        else:
            self.stop_server()

    def start_server(self, widget=None, foreign=False):
        """
        Starts the Twisted server.

        @type widget: instance
        @param widget: gtk.Widget.

        @type foreign: bool
        @param foreign: Whether the caller of this method is not self.buttonStartstop.

        """

        if self.server.listening(): return

        try:
            self.server.start_server(self.configuration['server']['port'])
        except error.ItakaServerErrorCannotListen, e:
            self.log.failure(('Gui', 'start_server'), ('Failed to start server', 'Failed to start server: %s' % (e)), 'ERROR')
            self.buttonStartstop.set_active(False)
            return

        self.server.add_log_observer(self.log.twisted_observer)

        if self.configuration['server']['authentication']:
            serverstock = 'STOCK_DIALOG_AUTHENTICATION'
            serverstring = 'Secure server'
        else:
            serverstock = 'STOCK_CONNECT'
            serverstring = 'Server'

        if self.configuration['screenshot']['format'] == "jpeg":
            self.log.detailed_message('%s started on port %d' % (serverstring, self.configuration['server']['port']), '%s started on port %s TCP. Serving %s images with %d%% quality' % (serverstring, self.configuration['server']['port'], self.configuration['screenshot']['format'].upper(), self.configuration['screenshot']['quality']), ['stock', serverstock])
        else:
            self.log.detailed_message('%s started on port %d' % (serverstring, self.configuration['server']['port']), '%s started on port %s TCP. Serving %s images' % (serverstring, self.configuration['server']['port'], self.configuration['screenshot']['format'].upper()), ['stock', serverstock])

        # Change buttons
        if foreign:
            self.buttonStartstop.set_active(True)
        self.buttonStartstop.set_label('Stop')
        self.startstopimage.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
        self.buttonStartstop.set_image(self.startstopimage)

        self.statusIcon.set_tooltip('Itaka - Server running')
        self.menuitemstart.set_sensitive(False)
        self.menuitemstop.set_sensitive(True)

        if not self.expander.get_property("sensitive"):
            self.expander.set_sensitive(True)

    def stop_server(self, widget=None, foreign=False):
        """
        Stops the Twisted server.

        @type widget: instance
        @param widget: gtk.Widget.

        @type foreign: bool
        @param foreign: Whether the caller of this method is not self.buttonStartstop.
        """

        if self.server.listening():
            self.log.message('Server stopped', ['stock', 'STOCK_DISCONNECT'])

            self.server.stop_server()
            self.server.remove_log_observer()

            # Stop the g_timeout
            if hasattr(self, 'iagotimer'):
                gobject.source_remove(self.iagotimer)

            # Change GUI elements
            if (foreign):
                self.buttonStartstop.set_active(False)

            self.statusIcon.set_tooltip("Itaka")
            self.startstopimage.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
            self.buttonStartstop.set_image(self.startstopimage)
            self.buttonStartstop.set_label("Start")
            self.labelLastip.set_text('')
            self.labelTime.set_text('')
            self.labelServed.set_text('')
            self.menuitemstart.set_sensitive(True)
            self.menuitemstop.set_sensitive(False)

    def restart_server(self):
        """
        Restarts the Twisted server.
        """

        if self.server.listening():
            self.log.message('Restarting the server to listen on port %d' % (self.configuration['server']['port']), ['stock', 'STOCK_REFRESH'])
            self.stop_server(None, True)
            self.start_server(None, True)

    def destroy(self, *args):
        """
        Main window destroy event.
        """

        if self.server.listening():
            self.console.message('Shutting down server')
            self.server.stop_server()
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

    def literal_time_difference(self, dtime):
        """
        Calculates the time difference from the last server request to 
        the current time. Expresses a datetime.timedelta using a
        string such as "1 hour, 20 minutes".
        
        @type dtime: datetime.datetime
        @param dtime: A starting datetime.datetime object.
        """

        # Create a timedelta from the datetime.datetime and the current time
        # (you can create your own timedeltas with datetime.timedelta(5, (650 *
        # 60) * 2, 12) for testing.
        self.td = datetime.datetime.now() - dtime

        self.pieces = []
        if self.td.days:
                self.pieces.append(self.plural(self.td.days, 'day'))

        self.minutes, self.seconds = divmod(self.td.seconds, 60)
        self.hours, self.minutes = divmod(self.minutes, 60)
        if self.hours:
            self.pieces.append(self.plural(self.hours, 'hour'))
        if self.minutes or len(self.pieces) == 0:
            self.pieces.append(self.plural(self.minutes, 'minute'))

        self.labelTime.set_text("<b>When</b>: " + ", ".join(self.pieces) + " ago")
        self.labelTime.set_use_markup(True)

        # Need this so it runs more than once.
        return True

    def plural(self, count, singular):
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

    def set_standard_images(self):
        """
        Changes the logo on the main window.
        """
        
        if self.configuration['server']['authentication']:
            self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, "itaka-secure.png"))            
        else:
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

        self.log.detailed_message('Screenshot served to %s' % (self.ip), 'Screenshot number %d served to %s' % (self.counter, self.ip), ['pixbuf', gtk.gdk.pixbuf_new_from_file(os.path.join(self.itakaglobals.image_dir, "itaka16x16-take.png"))])

        self.labelServed.set_text('<b>Served</b>: %d' % (self.counter))
        self.labelServed.set_use_markup(True)
        self.labelLastip.set_text('<b>Client</b>: %s' % (self.ip))
        self.labelLastip.set_use_markup(True)
        self.statusIcon.set_tooltip('Itaka - %s served' % (self.plural(self.counter, 'screenshot')))

        # Show the camera image on tray and interface for 1.5 seconds
        if self.configuration['server']['authentication']:
            self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, 'itaka-secure-take.png'))
        else:
            self.itakaLogo.set_from_file(os.path.join(self.itakaglobals.image_dir, 'itaka-take.png'))
        self.statusIcon.set_from_file(os.path.join(self.itakaglobals.image_dir, 'itaka-take.png'))
        gobject.timeout_add(1500, self.set_standard_images)

        # Call the update timer function, and add a timer to update the GUI of its
        # "Last screenshot taken" time
        self.literal_time_difference(time)
        if hasattr(self, 'iagotimer'): 
            gobject.source_remove(self.iagotimer)
        self.iagotimer = gobject.timeout_add(60000, self.literal_time_difference, time)
