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

""" Itaka GTK+ GUI """

import sys
import os
import datetime
import traceback
import copy

try:
    from twisted.internet import gtk2reactor
    try:
        gtk2reactor.install()
    except Exception, e:
        print_error(_('Could not initiate GTK modules: %s' % (e)))
        sys.exit(1)
    from twisted.internet import reactor
except ImportError:
    print_error(_('Could not import Twisted Network Framework'))
    sys.exit(1)

try:
    import server as iserver
    import error
except ImportError:
    print_error(_('Failed to import Itaka modules'))
    traceback.print_exc()
    sys.exit(1)

try:
    import pygtk
    pygtk.require("2.0")
except ImportError:
    print_warning(_('Pygtk module is missing'))
    pass
try:
    import gtk, gobject, pango
except ImportError:
    print_error(_('GTK+ bindings are missing'))
    sys.exit(1)

if gtk.gtk_version[1] < 10:
    print_error(_('Itaka requires GTK+ 2.10, you have %s installed' % (".".join(str(x) for x in gtk.gtk_version))))
    sys.exit(1)

class GuiLog:
    """
    GTK+ GUI logging handler
    """

    def __init__(self, gui_instance, console, configuration):
        """
        Constructor

        @type gui_instance: instance
        @param gui_instance: Instance of L{Gui}

        @type console: instance
        @param console: Instance of L{Console}

        @type configuration: dict
        @param configuration: Configuration values dictionary from L{ConfigParser}
        """

        self.gui = gui_instance
        self.console = console
        self.configuration = configuration

    def twisted_observer(self, args):
        """
        A log observer for our Twisted server

        @type args: dict
        @param args: dict {'key': [str(message)]}
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
        Write normal message on Gui log widgets

        @type message: str
        @param message: Message to be inserted

        @type icon: tuple
        @param icon: The first argument is a string of either 'stock' or 'pixbuf', and the second is a string of gtk.STOCK_ICON or a gtk.gdk.pixbuf object (without the 'gtk.' prefix)
        """
        
        self.console.message(message)
        self._write_gui_log(message, None, icon, False)

    def verbose_message(self, message, detailed_message, icon=None):
        """
        Write detailed message on Gui log widgets

        @type message: str
        @param message: Message to be inserted in the events log

        @type detailed_message: str
        @param detailed_message: Message to be inserted in the detailed log

        @type icon: tuple
        @param icon: The first argument is a string of either 'stock' or 'pixbuf', and the second is a string of gtk.STOCK_ICON or a gtk.gdk.pixbuf object (without the 'gtk.' prefix)
        """

        self.console.message(detailed_message)
        self._write_gui_log(message, detailed_message, icon, False, False)

    def failure(self, caller, message, failure_type='ERROR'):
        """
        Write failure message on Gui log widgets

        @type caller: tuple
        @param caller: Specifies the class and method were the warning ocurred

        @type message: tuple
        @param message: A tuple containing first the simple message to the events log, and then the detailed message for the detailed log

        @type failure_type: str
        @param failure_type: What kind of failure it is, either 'ERROR' (default), 'WARNING' or 'DEBUG'
        """
        
        self.simple_message = message[0]
        self.detailed_message = message[1]

        self.console.failure(caller, self.detailed_message, failure_type)

        # Errors require some more actions
        if failure_type == 'ERROR':
            # Show the window and its widgets, set the status icon blinking timeout
            if not self.gui.window.get_property("visible"):
                self.gui.window.present()
                self.gui.status_icon_timeout_blink()
                self.gui.window.move(self.gui.window_position[0], self.gui.window_position[1])

            self.gui.expander.set_expanded(True)
            self.gui.expander.set_sensitive(True)
            # Stop the server
            if self.gui.server.listening():
                self.gui.stop_server(None, True)

        self._write_gui_log(self.simple_message, self.detailed_message, self._get_failure_icon(failure_type), True, True)

    def _get_failure_icon(self, failure_type):
        """
        Return a default stock icon for a failure type

        @type failure_type: str
        @param failure_type: What kind of failure it is, either 'ERROR' (default), 'WARNING' or 'DEBUG'

        @rtype: tuple
        @return: An GTK+ stock icon definition. ['stock', 'STOCK_ICON']
        """
        # Default icon is always STOCK_DIALOG_ERROR
        icon = ['stock', 'STOCK_DIALOG_ERROR']
        
        if failure_type == "WARNING":
            icon = ['stock', 'STOCK_DIALOG_WARNING']
        elif failure_type == "DEBUG": 
            icon = ['stock', 'STOCK_DIALOG_INFO']

        return icon

    def _write_gui_log(self, message, detailed_message=None, icon=None, unpause_logger=True, failure=False):
        """
        Private method to write to both Gui logs

        @type message: str
        @param message: Message to be inserted

        @type detailed_message: str
        @param detailed_message: Optional detailed message if the event log and detailed log messages differ

        @type icon: tuple
        @param icon: The first argument is a string of either 'stock' or 'pixbuf', and the second is a string of gtk.STOCK_ICON or a gtk.gdk.pixbuf object (without the 'gtk.' prefix)

        @type unpause_logger: bool
        @param unpause_logger: Whether to unpause the GUI Logger

        @type failure: bool
        @param failure: Whether the message is a failure or not
        """

        if detailed_message is None:
            detailed_message = message

        # Only write messages when the logging is unpaused. Unless we are told otherwise
        if self.gui.log_paused():
            if unpause_logger:
                self.gui.unpause_log(True)
                self._write_events_log(message, icon, failure)
                self._write_detailed_log(detailed_message)
        else:
            self._write_events_log(message, icon, failure)
            self._write_detailed_log(detailed_message)

    def _write_events_log(self, message, icon=None, failure=False):
        """
        Private method to write to the events log Gui widget

        @type message: str
        @param message: Message to be inserted

        @type icon: tuple
        @param icon: The first argument is a string of either 'stock' or 'pixbuf', and the second is a string of gtk.STOCK_ICON or a gtk.gdk.pixbuf object (without the 'gtk.' prefix) if its stock, or a pixbuf

        @type failure: bool
        @param failure: Whether the message is a failure or not
        """

        if icon is not None:
            if icon[0] == "stock":
                self.inserted_iter = self.gui.log_events_store.append([self.gui.log_events_tree_view.render_icon(stock_id=getattr(gtk, icon[1]), size=gtk.ICON_SIZE_MENU, detail=None), message])
                # Select the iter if it's a failure
                if failure:
                    self.selection = self.gui.log_events_tree_view.get_selection()
                    self.selection.select_iter(self.inserted_iter)
            else:
                self.inserted_iter = self.gui.log_events_store.append([icon[1], message])
        else:
            self.inserted_iter = self.gui.log_events_store.append([icon, message])

        # Scroll
        self.gui.log_events_tree_view.scroll_to_cell(self.gui.log_events_tree_view.get_model().get_path(self.inserted_iter))

    def _write_detailed_log(self, message, bold=True):
        """
        Private method to write to the detailed log Gui widget

        @type message: str
        @param message: Message to be inserted

        @type bold: bool
        @param bold: Whether the text will be inserted as bold
        """

        message = message + '\r'

        if bold:
            self.gui.log_details_buffer.insert_with_tags_by_name(self.gui.log_details_buffer.get_end_iter(), message, 'bold-text')
        else:
            self.gui.log_details_buffer.insert_at_cursor(message, len(message))

        # Automatically scroll. Use wrap until fix
        self.gui.log_details_text_view.scroll_mark_onscreen(self.gui.log_details_buffer.get_insert())


class Gui:
    """
    GTK+ GUI
    """

    def __init__(self, console_instance, configuration):
        """
        Constructor

        @type console_instance: instance
        @param console_instance: An instance of the L{Console} class

        @type configuration: tuple
        @param configuration: A tuple of configuration globals and an instance of L{ConfigParser}
        """

        # Load our configuration and console instances and values
        self.console = console_instance
        self.itaka_globals = configuration[0]

        # The configuration instance has the user's preferences already loaded
        self.config_instance = configuration[1]
        self.configuration = self.itaka_globals.configuration_values

        # Instances of our Gui Logging class and Screenshot Server
        self.server = iserver.ScreenshotServer(self)
        self.log = GuiLog(self, self.console, self.configuration)
        self.log_is_paused = False

        # Start defining widgets
        self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(self.itaka_globals.image_dir, 'itaka.png'))
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect('destroy', self.destroy)
        self.window.connect('size-allocate', self._window_size_changed)
        self.window.set_title('Itaka')
        self.window.set_icon(self.icon_pixbuf)
        self.window.set_border_width(6)
        self.window.set_default_size(370, 1)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window_position = self.window.get_position()

        # Create our tray icon
        self.status_icon = gtk.StatusIcon()
        self.status_menu = gtk.Menu()

        if self.configuration['server']['authentication']:
            self.status_icon.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(os.path.join(self.itaka_globals.image_dir, 'itaka-secure.png')))
        else:
            self.status_icon.set_from_pixbuf(self.icon_pixbuf)

        self.status_icon.set_tooltip('Itaka')
        self.status_icon.set_visible(True)
        self.status_icon.connect('activate', self.status_icon_activate)
        self.status_icon.connect('popup-menu', self.status_icon_menu, self.status_menu)

        self.start_image = gtk.Image()
        self.start_image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_MENU)

        self.stop_image = gtk.Image()
        self.stop_image.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_MENU)
        self.menu_item_start = gtk.ImageMenuItem(_('St_art')) 
        self.menu_item_start.set_image(self.start_image)
        self.menu_item_start.connect('activate', self.start_server, True)
        self.menu_item_stop = gtk.ImageMenuItem(_('St_op')) 
        self.menu_item_stop.set_image(self.stop_image)
        self.menu_item_stop.connect('activate', self.stop_server, True)
        self.menu_item_stop.set_sensitive(False)

        if self.itaka_globals.notify_available: 
            self.menu_item_notifications = gtk.CheckMenuItem(_('Show _Notifications'))
            if self.configuration['server']['notify']:
                self.menu_item_notifications.set_active(True)
            self.menu_item_notifications.connect('toggled', self.status_icon_notify)

        self.menu_item_separator = gtk.SeparatorMenuItem()
        self.menu_item_separator1 = gtk.SeparatorMenuItem()
        self.menu_item_quit = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        self.menu_item_quit.connect('activate', self.destroy)

        self.status_menu.append(self.menu_item_start)
        self.status_menu.append(self.menu_item_stop)

        if self.itaka_globals.notify_available: 
            self.status_menu.append(self.menu_item_separator)
            self.status_menu.append(self.menu_item_notifications)

        self.status_menu.append(self.menu_item_separator1)
        self.status_menu.append(self.menu_item_quit)

        self.vbox = gtk.VBox(False, 6)
        self.box = gtk.HBox(False, 0)

        self.itaka_logo = gtk.Image()

        if self.configuration['server']['authentication']:
            self.itaka_logo.set_from_file(os.path.join(self.itaka_globals.image_dir, 'itaka-secure.png'))
        else:
            self.itaka_logo.set_from_file(os.path.join(self.itaka_globals.image_dir, 'itaka.png'))

        self.itaka_logo.show()

        self.box.pack_start(self.itaka_logo, False, False, 35)

        self.button_start_stop = gtk.ToggleButton(_('Start'), gtk.STOCK_PREFERENCES)
        self.start_stop_image = gtk.Image()

        self.start_stop_image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
        self.button_start_stop.set_image(self.start_stop_image)
        self.button_start_stop.connect('toggled', self.button_start_server)

        self.button_preferences = gtk.Button('Preferences', gtk.STOCK_PREFERENCES)
        self.button_preferences.connect('clicked', self.expand_preferences)

        # Set up some variables for our timeouts/animations
        self.preferences_hidden = False
        self.preferences_expanded = False
        self.timeout_contract = None
        self.timeout_expand = None
        self.timeout_blink = None

        self.box.pack_start(self.button_start_stop, True, True, 5)
        self.box.pack_start(self.button_preferences, True, True, 8)

        self.vbox.pack_start(self.box, False, False, 0)

        self.hbox_status = gtk.HBox(False, 0)
        self.label_served = gtk.Label()
        self.label_last_ip = gtk.Label()
        self.label_time = gtk.Label()

        self.hbox_status.pack_start(self.label_last_ip, True, False, 0)
        self.hbox_status.pack_start(self.label_time, True, False, 0)
        self.hbox_status.pack_start(self.label_served, True, False, 0)

        # Logger widget (displayed when expanded)
        self.vbox_log = gtk.VBox(False, 0)
        self.notebook_log = gtk.Notebook()
        self.notebook_log.set_tab_pos(gtk.POS_BOTTOM)

        self.label_log_events = gtk.Label(_('Events'))
        self.label_log_details = gtk.Label(_('Details'))

        self.scroll_log_events = gtk.ScrolledWindow()
        self.scroll_log_events.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll_log_events.set_shadow_type(gtk.SHADOW_NONE)

        self.log_events_store = gtk.ListStore(gtk.gdk.Pixbuf, str)
        self.log_events_tree_view = gtk.TreeView(self.log_events_store)
        self.log_events_tree_view.set_property('headers-visible', False)
        self.log_events_tree_view.set_property('rules-hint', True)

        self.column_log_events_icon = gtk.TreeViewColumn()
        self.column_log_events = gtk.TreeViewColumn()
        self.log_events_tree_view.append_column(self.column_log_events_icon)
        self.log_events_tree_view.append_column(self.column_log_events)

        self.cell_pixbuf_log_events = gtk.CellRendererPixbuf()
        self.column_log_events_icon.pack_start(self.cell_pixbuf_log_events)
        self.column_log_events_icon.add_attribute(self.cell_pixbuf_log_events, 'pixbuf', 0)

        self.cell_text_log_events = gtk.CellRendererText()
        self.column_log_events.pack_start(self.cell_text_log_events, True)
        self.column_log_events.add_attribute(self.cell_text_log_events, 'text', 1)
        self.scroll_log_events.add(self.log_events_tree_view)

        self.scroll_log_details = gtk.ScrolledWindow()
        self.scroll_log_details.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scroll_log_details.set_shadow_type(gtk.SHADOW_NONE)
        self.log_details_text_view = gtk.TextView()
        self.log_details_text_view.set_wrap_mode(gtk.WRAP_WORD)
        self.log_details_text_view.set_editable(False)
        self.log_details_text_view.set_size_request(-1, 160)
        self.log_details_buffer = self.log_details_text_view.get_buffer()
        self.log_details_buffer.create_tag ('bold-text', weight = pango.WEIGHT_BOLD)
        self.scroll_log_details.add(self.log_details_text_view)

        self.notebook_log.append_page(self.scroll_log_events, self.label_log_events)
        self.notebook_log.append_page(self.scroll_log_details, self.label_log_details)

        self.hbox_log = gtk.HBox(False, 0)
        self.button_log_clear = gtk.Button(_('Clear'))
        self.button_log_clear_image = gtk.Image()
        self.button_log_clear_image.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
        self.button_log_clear.set_image(self.button_log_clear_image)
        self.button_log_clear.connect('clicked', self.clear_logger)

        self.button_log_pause = gtk.ToggleButton(_('Pause'))
        self.button_log_pause_image = gtk.Image()
        self.button_log_pause_image.set_from_stock(gtk.STOCK_MEDIA_PAUSE, gtk.ICON_SIZE_BUTTON)
        self.button_log_pause.set_image(self.button_log_pause_image)
        self.button_log_pause.connect('toggled', self.button_pause_log)

        self.hbox_log.pack_end(self.button_log_clear, False, False, 4)
        self.hbox_log.pack_end(self.button_log_pause, False, False, 4)

        self.vbox_log.pack_start(self.notebook_log, False, False, 4)
        self.vbox_log.pack_start(self.hbox_log, False, False, 4)

        self.label_log_box = gtk.Label(_('<b>Server log</b>'))
        self.label_log_box.set_use_markup(True)

        self.expander_size_finalized = False
        self.expander = gtk.Expander(None)
        self.expander.set_label_widget(self.label_log_box)
        self.expander.connect('notify::expanded', self.expand_logger)

        self.vbox.pack_start(self.hbox_status, False, False, 4)
        self.vbox.pack_start(self.expander, False, False, 0)
        self.expander.set_sensitive(False)

        # This is are the preference widgets that are going to be added and shown later
        self.vbox_preferences = gtk.VBox(False, 7)
        self.vbox_preferences_items = gtk.VBox(False, 5)
        self.vbox_preferences_items.set_border_width(2)
        
        # Create our Hboxes
        for n in xrange(1, 10+1):
            setattr(self, 'hbox_preferences_%d' % (n), gtk.HBox(False, 0))

        self.frame_preference_settings = gtk.Frame()
        self.label_preferences_settings = gtk.Label(_('<b>Preferences</b>'))
        self.label_preferences_settings.set_use_markup(True)
        self.frame_preference_settings.set_label_widget(self.label_preferences_settings)
        self.frame_preference_settings.set_label_align(0.5, 0.5)

        self.label_preferences_port = gtk.Label(_('Port'))
        self.label_preferences_port.set_justify(gtk.JUSTIFY_LEFT)
        self.label_preferences_port.set_alignment(0, 0.60)

        self.label_preferences_auth = gtk.Label(_('Authentication'))
        self.label_preferences_auth.set_justify(gtk.JUSTIFY_LEFT)
        self.label_preferences_auth.set_alignment(0, 0.60)

        self.label_preferences_user = gtk.Label(_('Username'))
        self.label_preferences_user.set_justify(gtk.JUSTIFY_LEFT)
        self.label_preferences_user.set_alignment(0, 0.60)

        self.label_preferences_pass = gtk.Label(_('Password'))
        self.label_preferences_pass.set_justify(gtk.JUSTIFY_LEFT)
        self.label_preferences_pass.set_alignment(0, 0.60)

        self.label_preferences_format = gtk.Label(_('Format'))
        self.label_preferences_format.set_justify(gtk.JUSTIFY_LEFT)
        self.label_preferences_format.set_alignment(0, 0.50)

        self.label_preferences_quality = gtk.Label(_('Quality'))
        self.label_preferences_quality.set_justify(gtk.JUSTIFY_LEFT)
        self.label_preferences_quality.set_alignment(0, 0.50)

        self.label_preferences_scale = gtk.Label(_('Scale'))
        self.label_preferences_scale.set_justify(gtk.JUSTIFY_LEFT)
        self.label_preferences_scale.set_alignment(0, 0.50)

        if not self.itaka_globals.system == 'nt':
            self.label_preferences_screenshot = gtk.Label(_('Window'))
            self.label_preferences_screenshot.set_justify(gtk.JUSTIFY_LEFT)
            self.label_preferences_screenshot.set_alignment(0, 0.50)

        if self.itaka_globals.notify_available: 
            self.label_preferences_notifications = gtk.Label(_('Notifications'))
            self.label_preferences_notifications.set_justify(gtk.JUSTIFY_LEFT)
            self.label_preferences_notifications.set_alignment(0, 0.50)

        self.adjustment_preferences_port = gtk.Adjustment(float(self.configuration['server']['port']), 1024, 65535, 1, 0, 0)
        self.spin_preferences_port = gtk.SpinButton(self.adjustment_preferences_port)
        self.spin_preferences_port.set_numeric(True)

        self.entry_preferences_user = gtk.Entry()
        self.entry_preferences_user.set_width_chars(11)
        self.entry_preferences_user.set_text(self.configuration['server']['username'])

        self.entry_preferences_pass = gtk.Entry()
        self.entry_preferences_pass.set_width_chars(11)

        char = u'\u25cf'
        if self.itaka_globals.system == 'nt':
            char = '*'

        self.entry_preferences_pass.set_invisible_char(char)
        self.entry_preferences_pass.set_visibility(False)
        self.entry_preferences_pass.set_text(self.configuration['server']['password'])

        self.check_preferences_auth = gtk.CheckButton()
        self.check_preferences_auth.connect('toggled', self._preferences_authentication_toggled)

        if self.configuration['server']['authentication']:
            self.check_preferences_auth.set_active(1)
        else: 
            self.check_preferences_auth.set_active(0)

        if not self.configuration['server']['authentication']:
            self.entry_preferences_user.set_sensitive(False)
            self.entry_preferences_pass.set_sensitive(False)

        self.adjustment_preferences_quality = gtk.Adjustment(float(self.configuration['screenshot']['quality']), 0, 100, 1, 0, 0)
        self.spin_preferences_quality = gtk.SpinButton(self.adjustment_preferences_quality)
        self.spin_preferences_quality.set_numeric(True)

        self.adjustment_preferences_scale = gtk.Adjustment(float(self.configuration['screenshot']['scalepercent']), 1, 100, 1, 0, 0)
        self.spin_preferences_scale = gtk.SpinButton(self.adjustment_preferences_scale)
        self.spin_preferences_scale.set_numeric(True)

        self.combo_preferences_format = gtk.combo_box_new_text()
        self.combo_preferences_format.connect('changed', self._preferences_combo_changed)
        self.combo_preferences_format.append_text('JPG')
        self.combo_preferences_format.append_text('PNG')

        if self.configuration['screenshot']['format'] == 'jpeg':
            self.combo_preferences_format.set_active(0)
        else: 
            self.combo_preferences_format.set_active(1)
            self.hbox_preferences_6.set_sensitive(False)

        if self.itaka_globals.notify_available: 
            self.check_preferences_notifications = gtk.CheckButton()
            if self.configuration['server']['notify']:
                self.check_preferences_notifications.set_active(1)
            else: 
                self.check_preferences_notifications.set_active(0)

        if not self.itaka_globals.system == 'nt':
            self.combo_preferences_screenshot = gtk.combo_box_new_text()
            self.combo_preferences_screenshot.append_text(_('Fullscreen'))
            self.combo_preferences_screenshot.append_text(_('Active window'))
            if self.configuration['screenshot']['currentwindow']:
                self.combo_preferences_screenshot.set_active(1)
            else: 
                self.combo_preferences_screenshot.set_active(0)

        self.button_preferences_close = gtk.Button('Close', gtk.STOCK_SAVE)
        self.button_preferences_close.connect('clicked', self.contractpreferences)
        
        self.button_preferences_about = gtk.Button('About', gtk.STOCK_ABOUT)
        self.button_preferences_about.connect('clicked', self.about)

        self.hbox_preferences_1.pack_start(self.label_preferences_port, False, False, 12)
        self.hbox_preferences_1.pack_end(self.spin_preferences_port, False, False, 7)
        self.hbox_preferences_2.pack_start(self.label_preferences_auth, False, False, 12)
        self.hbox_preferences_3.pack_start(self.label_preferences_user, False, False, 12)
        self.hbox_preferences_4.pack_end(self.entry_preferences_pass, False, False, 7)
        self.hbox_preferences_4.pack_start(self.label_preferences_pass, False, False, 12)
        self.hbox_preferences_3.pack_end(self.entry_preferences_user, False, False, 7)
        self.hbox_preferences_2.pack_end(self.check_preferences_auth, False, False, 7)
        self.hbox_preferences_5.pack_start(self.label_preferences_format, False, False, 12)
        self.hbox_preferences_5.pack_end(self.combo_preferences_format, False, False, 7)
        self.hbox_preferences_6.pack_start(self.label_preferences_quality, False, False, 12)
        self.hbox_preferences_6.pack_end(self.spin_preferences_quality, False, False, 7)

        if not self.itaka_globals.system == 'nt':
            self.hbox_preferences_7.pack_start(self.label_preferences_screenshot, False, False, 12)
            self.hbox_preferences_7.pack_end(self.combo_preferences_screenshot, False, False, 7)

        self.hbox_preferences_8.pack_start(self.label_preferences_scale, False, False, 12)
        self.hbox_preferences_8.pack_end(self.spin_preferences_scale, False, False, 7)

        if self.itaka_globals.notify_available: 
            self.hbox_preferences_9.pack_start(self.label_preferences_notifications, False, False, 12)
            self.hbox_preferences_9.pack_end(self.check_preferences_notifications, False, False, 7)

        self.hbox_preferences_10.pack_start(self.button_preferences_about, False, False, 7)
        self.hbox_preferences_10.pack_end(self.button_preferences_close, False, False, 7)

        self.vbox_preferences_items.pack_start(self.hbox_preferences_1, False, False, 0)
        self.vbox_preferences_items.pack_start(self.hbox_preferences_2, False, False, 0)
        self.vbox_preferences_items.pack_start(self.hbox_preferences_3, False, False, 0)
        self.vbox_preferences_items.pack_start(self.hbox_preferences_4, False, False, 0)
        self.vbox_preferences_items.pack_start(self.hbox_preferences_5, False, False, 0)
        self.vbox_preferences_items.pack_start(self.hbox_preferences_6, False, False, 0)

        if not self.itaka_globals.system == 'nt':
            self.vbox_preferences_items.pack_start(self.hbox_preferences_7, False, False, 0)

        self.vbox_preferences_items.pack_start(self.hbox_preferences_8, False, False, 0)

        if self.itaka_globals.notify_available: 
            self.vbox_preferences_items.pack_start(self.hbox_preferences_9, False, False, 0)

        self.frame_preference_settings.add(self.vbox_preferences_items)
        self.vbox_preferences.pack_start(self.frame_preference_settings, False, False, 0)
        self.vbox_preferences.pack_start(self.hbox_preferences_10, False, False, 4)

        self.window.add(self.vbox)
        self.window.show_all()

        # Once we have all our widgets shown, get the 'initial' real size, for expanding/contracting
        self.window.initial_size = self.window.get_size()

    def _save_preferences(self):
        """
        Saves and hides the preferences dialog
        """
        
        # So we can mess with the values in the running one and not mess up our comparison
        self.current_configuration = copy.deepcopy(self.configuration)

        # Switch to the proper values
        self.format_value = str(self.combo_preferences_format.get_active_text())

        if self.format_value == 'PNG':
            self.format_value = 'png'
            self.configuration['screenshot']['format'] = 'png'
        else:
            self.format_value = 'jpeg'
            self.configuration['screenshot']['format'] = 'jpeg'

        if self.itaka_globals.notify_available:
            self.notify_value = self.check_preferences_notifications.get_active()

            if self.notify_value:
                self.notify_value = True
                self.menu_item_notifications.set_active(True)
                self.configuration['server']['notify'] = True
            else:
                self.notify_value = False
                self.menu_item_notifications.set_active(False)
                self.configuration['server']['notify'] = False
        else:
            self.notify_value = False
            self.configuration['server']['notify'] = False

        if not self.itaka_globals.system == 'nt':
            if self.combo_preferences_screenshot.get_active_text() == _('Active window'):
                self.configuration['screenshot']['currentwindow'] = True
                self.screenshot_value = True
            else:
                self.configuration['screenshot']['currentwindow'] = False
                self.screenshot_value = False
        else:
            self.screenshot_value = False
            self.configuration['screenshot']['currentwindow'] = False

        self.scale_value = [self.spin_preferences_scale.get_value_as_int()]

        if self.scale_value[0] == 100:
            self.configuration['screenshot']['scale'] = False
            self.scale_value.append(False)
        else:
            self.configuration['screenshot']['scale'] = True
            self.scale_value.append(True)

        if self.configuration['screenshot']['scalepercent'] != self.scale_value[0]:
            self.configuration['screenshot']['scalepercent'] = self.scale_value[0]
        
        # Build a configuration dictionary to send to the configuration engine's
        # save method. Redundant values must be included for the comparison
        self.configurationdict = {
            'html':
                {'html': '<img src="screenshot" alt="If you are seeing this message it means there was an error in Itaka or you are using a text-only browser.">',
                'authfailure': '<p><strong>Sorry, but you cannot access this resource without authorization.</strong></p>'},
                
            'screenshot': 
                {'path': self.configuration['screenshot']['path'],
                'format': self.format_value,
                'quality': self.spin_preferences_quality.get_value_as_int(),
                'currentwindow': self.screenshot_value,
                'scale': self.scale_value[1],
                'scalepercent': self.scale_value[0]},

            'server': 
                {'username': self.entry_preferences_user.get_text(),
                'authentication': self.check_preferences_auth.get_active(),
                'notify': self.notify_value,
                'password': self.entry_preferences_pass.get_text(),
                'port': self.spin_preferences_port.get_value_as_int()}
            }

        # Set them for local use now
        if self.configuration['screenshot']['quality'] != self.spin_preferences_quality.get_value_as_int():
            self.configuration['screenshot']['quality'] = self.spin_preferences_quality.get_value_as_int()

        if self.configuration['server']['port'] !=  self.spin_preferences_port.get_value_as_int():
            self.configuration['server']['port'] =  self.spin_preferences_port.get_value_as_int()
            self.restart_server()

        if self.configuration['server']['authentication'] is not self.check_preferences_auth.get_active():
            self.configuration['server']['authentication'] = self.check_preferences_auth.get_active()

        if self.configuration['server']['username'] != self.entry_preferences_user.get_text():
            self.configuration['server']['username'] = self.entry_preferences_user.get_text()

        if self.configuration['server']['password'] != self.entry_preferences_pass.get_text():
            self.configuration['server']['password'] = self.entry_preferences_pass.get_text()

        # Check if the configuration changed
        if (self.configurationdict != self.current_configuration):

            # Update the needed keys
            try:
                # self.config_instance.save(self.configurationdict)
                for section in self.configurationdict:
                    [self.config_instance.update(section, key, value) for key, value in self.configurationdict[section].iteritems() if key not in self.current_configuration[section] or self.current_configuration[section][key] != value]
            except:
                self.log.failure(('Gui', '_save_preferences'), _('Could not save preferences'), 'ERROR')

    def expand_preferences(self, *args):
        """
        Expands the window for preferences
        """

        # We have a race condition here. If GTK cant resize fast enough, then it gets very sluggish
        # See configure-event signal of gtk.Widget
        # start timer, resize, catch configure-notify, set up idle handler, when idle resize to what the size should be at this point of time, repeat
        if not self.preferences_expanded:
            if self.timeout_expand is not None:
                """NOTE: GTK+ GtkWidget.size_request() method can give you the amount of size a widget will take
                however, it has to be show()ned before. For our little hack, we show the vbox_preferences widgets
                but not itself, which should yield a close enough calculation."""
                self.frame_preference_settings.show_all()
                self.hbox_preferences_10.show_all()

                """If the logger is expanded, use that as the initial size. 
                _expander_size is set by our GtkWindow resize callback
                but we also set a expander_size_finalized variable here
                so that _window_size_changed doesnt set the new expanded_size over 
                again as our window is expanding here."""
                
                self.expander_size_finalized = False
                if self.expander.get_expanded():
                    self.window.normal_size = self.expander_size
                    self.expander_size_finalized = True
                else:
                    self.window.normal_size = self.window.initial_size

                self.increment = 33
                if self.window.current_size[1] < self.window.normal_size[1]+self.vbox_preferences.size_request()[1]:
                    # Avoid overexpanding our calculation
                    if self.window.current_size[1]+self.increment > self.window.normal_size[1]+self.vbox_preferences.size_request()[1]: 
                        self.increment = (self.window.normal_size[1]+self.vbox_preferences.size_request()[1] - self.window.current_size[1]) 

                    self.window.resize(self.window.current_size[0], self.window.current_size[1]+self.increment)
                    return True
                else:
                    # Its done expanding, add our widgets or display it if it has been done already
                    self.button_preferences.set_sensitive(False)
                    self.preferences_expanded = True

                    # Reload our configuration and show the preferences
                    self.configuration = self.config_instance.load()
                    if self.preferences_hidden:
                        self.vbox_preferences.show_all()
                    else:
                        self.vbox.pack_start(self.vbox_preferences, False, False, 0)
                        self.vbox_preferences.show_all()
                    
                    self.timeout_expand = None
                    return False
            else:
                self.timeout_expand = gobject.timeout_add(30, self.expand_preferences)

    def contractpreferences(self, *args):
        """
        Contracts the window of preferences
        """

        if self.timeout_contract is not None:
            # If you dont use the normal_size proxy to our window sizes,
            # it generates a nice effect of doing the animation when closing the expander also. 
            # While sexy, it's inconsistent, and most definately a resource hungry bug
            if self.expander.get_expanded():
                self.window.normal_size = self.expander_size
                self.expander_size_finalized = True
            else:
                self.window.normal_size = self.window.initial_size
           
            if self.vbox_preferences.get_property("visible"):
                self.vbox_preferences.hide_all()

            if self.window.current_size[1] > self.window.normal_size[1]:
                self.window.resize(self.window.current_size[0], self.window.current_size[1]-self.increment)
                return True
            else:
                # Done, set some variables and stop our timer
                self.preferences_expanded = False 
                self.preferences_hidden = True
                self.expander.size_finalized = False
                self.button_preferences.set_sensitive(True)
                
                # Save our settings 
                self._save_preferences()

                self.timeout_contract = None
                return False
        else:
            self.timeout_contract = gobject.timeout_add(30, self.contractpreferences)

    def _window_size_changed(self, widget=None, data=None):
        """
        Report the window size on change
        
        @type widget: instance
        @param widget: gtk.Widget

        @type data: unknown
        @param data: Unknown
        """
        
        self.window.current_size = self.window.get_size()
        
        # If the logger is expanded, give them a new size unless our preferences expander is working
        if self.expander.get_expanded() and not self.expander_size_finalized:
            self.expander_size = self.window.current_size
            # If the preferences were expanded before the logger
            if self.preferences_expanded:
                # Cant assign tuple items
                self.expander_size = [self.expander_size[0], self.expander_size[1] - self.vbox_preferences.size_request()[1]]

    def status_icon_menu(self, widget, button, time, menu):
        """
        Display the menu on the status icon
        
        @type widget: instance
        @SAVE widget: gtk.Widget

        @type button: int
        @SAVE button: The button pressed.

        @type time: unknown
        @param time: Unknown

        @type menu: instance
        @param menu: A gtk.Menu instance
        """

        if button == 3:
            if menu:
                menu.show_all()
                menu.popup(None, None, None, 3, time)

    def status_icon_timeout_blink(self, time=3000):
        """
        Sets the timeout in miliseconds to blink and stop blinking the status icon
        
        @type time: int
        @param time: Time in milliseconds to blink the status icon
        """

        if self.timeout_blink is None:
            self.status_icon.set_blinking(True)
            self.timeout_blink = gobject.timeout_add(time, self.status_icon_timeout_blink)
        else:
            self.status_icon.set_blinking(False)
            self.timeout_blink = None
            return False
 
    def status_icon_activate(self, widget):
        """
        Toggle the window visibility from the status icon when clicked
        
        @type widget: instance
        @param widget: gtk.Widget
        """

        if self.window.get_property("visible"):
            # Save it for when we undock because of errors
            self.window_position = self.window.get_position()
            self.window.hide()
        else:
            self.window.show()

    def status_icon_notify(self, widget):
        """
        Disable or enable notifications on the fly from the status icon
        
        @type widget: instance
        @param widget: gtk.Widget
        """

        if self.check_widget(self.menu_item_notifications):
            self.configuration['server']['notify'] = True
        else:
            self.configuration['server']['notify'] = False

    def about(self, *args):
        """
        Creates the about dialog
        """

        self.about_dialog = gtk.AboutDialog()
        self.about_dialog.set_transient_for(self.window)
        self.about_dialog.set_name('Itaka')
        self.about_dialog.set_version(self.itaka_globals.__version__)
        self.about_dialog.set_copyright(u'© 2003-2007 Marc E.')
        self.about_dialog.set_comments('Screenshooting de mercado.')
        self.about_dialog.set_authors(['Marc E. <santusmarc@users.sourceforge.net>', 'Kurt Erickson <psychogenicshk@users.sourceforge.net>'])
        self.about_dialog.set_artists(['Marc E. <santusmarc@users.sourceforge.net>', 'Tango Project (http://tango.freedesktop.org)'])
        self.about_dialog.set_license('''Itaka is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
any later version.

Itaka is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Itaka; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA''')
        self.about_dialog.set_website('http://itaka.jardinpresente.com.ar')
        self.about_dialog.set_website_label('Itaka website')
        gtk.about_dialog_set_url_hook(None)
        self.about_dialog.set_logo(gtk.gdk.pixbuf_new_from_file(os.path.join(self.itaka_globals.image_dir, "itaka64x64.png")))
        self.about_dialog.set_icon(self.icon_pixbuf)
        self.about_dialog.run()
        self.about_dialog.destroy()

    def expand_logger(self, expander, params):
        """
        Expand or contract the logger
        
        @type expander: instance
        @param expander: gtk.Expander instance

        @type params: unknown
        @param params: Unknown
        """

        if self.expander.get_expanded():
            # Show the debugvbox() and it's subwidgets
            self.vbox_log.show_all()

            self.expander.add(self.vbox_log)
        else:
            self.expander.remove(self.expander.child)
            self.window.resize(self.window.initial_size[0], self.window.initial_size[1])
        return

    def clear_logger(self, *args):
        """
        Clear the log
        """

        self.log_events_store.clear()
        self.log_details_buffer.set_text("")

    def button_pause_log(self, widget):
        """
        Interface to pause or unpause the Gui logger by checking the status of a gtk.ToggleButton
        
        @type widget: instance
        @param widget: gtk.Widget
        """

        if self.check_widget(widget):
            if not self.log_paused():
                self.pause_log()
        else:
            if self.log_paused():
                self.unpause_log()

    def pause_log(self):
        """
        Pause Gui log output
        """

        self.log_events_store.append([self.log_events_tree_view.render_icon(stock_id=gtk.STOCK_MEDIA_PAUSE, size=gtk.ICON_SIZE_MENU, detail=None), _('Logging paused')])
        
        self.log_events_tree_view.set_sensitive(False)
        self.log_details_text_view.set_sensitive(False)

        self.server.remove_log_observer()
        self.log_is_paused = True

    def unpause_log(self, foreign=False):
        """
        Unpause Gui log output

        @type foreign: bool
        @param foreign: Whether the caller of this method is not the Gui gtk.ToggleButton
        """

        self.server.add_log_observer(self.log.twisted_observer)
        if (foreign):
            self.button_log_pause.set_active(False)
        self.log_details_text_view.set_sensitive(True)
        self.log_events_tree_view.set_sensitive(True)

        self.log_events_store.append([self.log_events_tree_view.render_icon(stock_id=gtk.STOCK_MEDIA_PLAY, size=gtk.ICON_SIZE_MENU, detail=None), _('Logging resumed')])

        self.log_is_paused = False

    def log_paused(self):
        """
        Whether the Gui log is paused

        @rtype: bool
        @return: True if the Gui log is paused
        """
        
        return self.log_is_paused

    def main(self):
        """
        Main initiation function. Starts the Twisted GUI reactors
        """

        # Server reactor (interacts with the Twisted reactor)	
        self.sreact = reactor.run()

    def _preferences_combo_changed(self, widget):
        """
        Callback for preferenes gtk.ComboBox widget

        @type widget: instance
        @param widget: gtk.Widget
        """
        
        if self.combo_preferences_format.get_active_text() == 'PNG':
            self.hbox_preferences_6.set_sensitive(False)
        else:
            self.hbox_preferences_6.set_sensitive(True)

    def _preferences_authentication_toggled(self, widget):
        """
        Callback for preferences gtk.CheckButton widget

        @type widget: instance
        @param widget: gtk.Widget
        """

        if self.check_widget(widget):
            self.entry_preferences_user.set_sensitive(True)
            self.entry_preferences_pass.set_sensitive(True)
            self.itaka_logo.set_from_file(os.path.join(self.itaka_globals.image_dir, "itaka-secure.png"))
            self.status_icon.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(os.path.join(self.itaka_globals.image_dir, "itaka-secure.png")))
        else:
            self.entry_preferences_user.set_sensitive(False)
            self.entry_preferences_pass.set_sensitive(False)
            self.itaka_logo.set_from_file(os.path.join(self.itaka_globals.image_dir, "itaka.png"))
            self.status_icon.set_from_pixbuf(self.icon_pixbuf)


    def check_widget(self, widget):
        """
        Checks if a gtk.Widget is active

        @type widget: instance
        @param widget: gtk.Widget
        """

        if hasattr(widget, 'get_active') and callable(getattr(widget, 'get_active')):
            return widget.get_active()
        else:
            return False

    def button_start_server(self, widget):
        """
        Interface to start or stop the server by checking the status of a gtk.ToggleButton
        
        @type widget: instance
        @param widget: gtk.Widget
        """

        if self.check_widget(widget):
            self.start_server()
        else:
            self.stop_server()

    def start_server(self, widget=None, foreign=False):
        """
        Starts the Twisted server

        @type widget: instance
        @param widget: gtk.Widget

        @type foreign: bool
        @param foreign: Whether the caller of this method is not self.button_start_stop

        """

        if self.server.listening(): return

        try:
            self.server.start_server(self.configuration['server']['port'])
        except error.ItakaServerErrorCannotListen, e:
            self.log.failure(('Gui', 'start_server'), (_('Failed to start server'), _('Failed to start server: %s') % (e)), 'ERROR')
            self.button_start_stop.set_active(False)
            return

        self.server.add_log_observer(self.log.twisted_observer)

        if self.configuration['server']['authentication']:
            serverstock = 'STOCK_DIALOG_AUTHENTICATION'
            serverstring = _('Secure server')
        else:
            serverstock = 'STOCK_CONNECT'
            serverstring = _('Server')

        if self.configuration['screenshot']['format'] == "jpeg":
            self.log.verbose_message(_('%s started on port %d') % (serverstring, self.configuration['server']['port']), _('%s started on port %s TCP. Serving %s images with %d%% quality') % (serverstring, self.configuration['server']['port'], self.configuration['screenshot']['format'].upper(), self.configuration['screenshot']['quality']), ['stock', serverstock])
        else:
            self.log.verbose_message(_('%s started on port %d') % (serverstring, self.configuration['server']['port']), _('%s started on port %s TCP. Serving %s images') % (serverstring, self.configuration['server']['port'], self.configuration['screenshot']['format'].upper()), ['stock', serverstock])

        # Change buttons
        if foreign:
            self.button_start_stop.set_active(True)
        self.button_start_stop.set_label(_('Stop'))
        self.start_stop_image.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
        self.button_start_stop.set_image(self.start_stop_image)

        self.status_icon.set_tooltip(_('Itaka - Server running'))
        self.menu_item_start.set_sensitive(False)
        self.menu_item_stop.set_sensitive(True)

        if not self.expander.get_property("sensitive"):
            self.expander.set_sensitive(True)

    def stop_server(self, widget=None, foreign=False):
        """
        Stops the Twisted server

        @type widget: instance
        @param widget: gtk.Widget

        @type foreign: bool
        @param foreign: Whether the caller of this method is not self.button_start_stop
        """

        if self.server.listening():
            self.log.message(_('Server stopped'), ['stock', 'STOCK_DISCONNECT'])

            self.server.stop_server()
            self.server.remove_log_observer()

            # Stop the g_timeout
            if hasattr(self, 'iagotimer'):
                gobject.source_remove(self.iagotimer)

            # Change GUI elements
            if foreign:
                self.button_start_stop.set_active(False)

            self.status_icon.set_tooltip('Itaka')
            self.start_stop_image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
            self.button_start_stop.set_image(self.start_stop_image)
            self.button_start_stop.set_label(_('Start'))
            if not foreign:
                self.label_last_ip.set_text('')
                self.label_time.set_text('')
                self.label_served.set_text('')
            self.menu_item_start.set_sensitive(True)
            self.menu_item_stop.set_sensitive(False)

    def restart_server(self):
        """
        Restarts the Twisted server
        """

        if self.server.listening():
            self.log.message(_('Restarting the server to listen on port %d') % (self.configuration['server']['port']), ['stock', 'STOCK_REFRESH'])
            self.stop_server(None, True)
            self.start_server(None, True)

    def destroy(self, *args):
        """
        Main window destroy event
        """

        if self.server.listening():
            self.server.stop_server()

        # Remove stale screenshot and quit
        if os.path.exists(os.path.join(self.configuration['screenshot']['path'], 'itakashot.%s' % (self.configuration['screenshot']['format']))): 
            os.remove(os.path.join(self.configuration['screenshot']['path'], 'itakashot.%s' % (self.configuration['screenshot']['format'])))

        # Windows fix
        del self.status_icon

        self.console.message(_('Itaka shutting down'))
        gtk.main_quit()

    def _literal_time_difference(self, dtime):
        """
        Calculates the time difference from the last server request to 
        the current time. Expresses a datetime.timedelta using a
        string such as "1 hour, 20 minutes"
        
        @type dtime: datetime.datetime
        @param dtime: A starting datetime.datetime object
        """

        # Create a timedelta from the datetime.datetime and the current time
        # (you can create your own timedeltas with datetime.timedelta(5, (650 *
        # 60) * 2, 12) for testing
        self.td = datetime.datetime.now() - dtime

        self.pieces = []
        if self.td.days:
                self.pieces.append(self.plural(self.td.days, _('day')))

        self.minutes, self.seconds = divmod(self.td.seconds, 60)
        self.hours, self.minutes = divmod(self.minutes, 60)
        if self.hours:
            self.pieces.append(self.plural(self.hours, _('hour')))
        if self.minutes or len(self.pieces) == 0:
            self.pieces.append(self.plural(self.minutes, _('minute')))

        self.label_time.set_text(_('<b>When</b>: ') + ', '.join(self.pieces) + _(' ago'))
        self.label_time.set_use_markup(True)

        # Need this so it runs more than once
        return True

    def plural(self, count, singular):
        """ 
        Helper method to handle simple english plural translations
        
        @type count: int
        @param count: Number

        @type singular: str
        @param singular: Singular version of the word to pluralize
        """

        # This is the simplest version; a more general version
        # should handle -y -> -ies, child -> children, etc
        return '%d %s%s' % (count, singular, ("", 's')[count != 1])

    def set_standard_images(self):
        """
        Changes the logo on the main window
        """
        
        if self.configuration['server']['authentication']:
            self.itaka_logo.set_from_file(os.path.join(self.itaka_globals.image_dir, "itaka-secure.png"))            
        else:
            self.itaka_logo.set_from_file(os.path.join(self.itaka_globals.image_dir, "itaka.png"))

        self.status_icon.set_from_pixbuf(self.icon_pixbuf)
        # Only run this event once
        return False

    def update_gui(self, counter, ip, time):
        """ 
        Updates the GUI on request from the server
        
        @type counter: int
        @param counter: Total number of server hits

        @type ip: str
        @param ip: IP address of the client

        @type time: datetime.datetime
        @param time: Time of the request
        """

        self.log.verbose_message(_('Screenshot served to %s') % ip, _('Screenshot number %d served to %s') % (counter, self.ip), ['pixbuf', gtk.gdk.pixbuf_new_from_file(os.path.join(self.itaka_globals.image_dir, "itaka16x16-take.png"))])

        self.label_served.set_text(_('<b>Served</b>: %d') % (counter))
        self.label_served.set_use_markup(True)
        self.label_last_ip.set_text(_('<b>Client</b>: %s') % (ip))
        self.label_last_ip.set_use_markup(True)
        self.status_icon.set_tooltip(_('Itaka - %s served') % (self.plural(counter, _('screenshot'))))

        # Show the camera image on tray and interface for 1.5 seconds
        if self.configuration['server']['authentication']:
            self.itaka_logo.set_from_file(os.path.join(self.itaka_globals.image_dir, 'itaka-secure-take.png'))
        else:
            self.itaka_logo.set_from_file(os.path.join(self.itaka_globals.image_dir, 'itaka-take.png'))

        self.status_icon.set_from_file(os.path.join(self.itaka_globals.image_dir, 'itaka-take.png'))
        gobject.timeout_add(1500, self.set_standard_images)

        # Add a timer to update the interface
        self._literal_time_difference(time)

        if hasattr(self, 'iagotimer'): 
            gobject.source_remove(self.iagotimer)

        self.iagotimer = gobject.timeout_add(60000, self._literal_time_difference, time)

