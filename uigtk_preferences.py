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

""" Itaka preferences dialog """

try:
    import pygtk
    pygtk.require("2.0")
except ImportError:
    print "[*] WARNING: Pygtk module is missing."
    pass
try:
    import gtk
except ImportError:
    print "[*] ERROR: GTK+ Python bindings are missing."
    sys.exit(1)

class Preferences:
    def prefwindow(self, widget, configinstance, guiinstance, icon):
        # Initate our configuration and gui instances
        self.system = configinstance[0]
        self.config = configinstance[1]

        self.gui = guiinstance

        # Reload the configuration each time the window pops up
        self.vconfig = configinstance[1].load(False)

        """ Set up the preferences window. """
        self.icon_pixbuf = icon	
        self.preferences = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.preferences.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.preferences.connect("destroy", lambda call: self.preferences.hide())
        self.preferences.set_title("Preferences")
        self.preferences.set_icon(self.icon_pixbuf)
        self.preferences.set_border_width(12)

        self.preferencesVBox = gtk.VBox(False, 0)
        self.preferencesHBox1 = gtk.HBox(False, 0)
        self.preferencesHBox2 = gtk.HBox(False, 0)
        self.preferencesHBox3 = gtk.HBox(False, 0)
        self.preferencesHBox4 = gtk.HBox(False, 0)

        # Hbox4 contains notifications which is only available in some systems
        if self.system != "posix":
            self.preferencesHBox4.set_sensitive(False)

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
        self.adjustmentport = gtk.Adjustment(float(self.vconfig['server']['port']), 1024, 65535, 1, 0, 0)
        self.preferencesSpinport = gtk.SpinButton(self.adjustmentport)
        self.preferencesSpinport.set_numeric(True)

        self.adjustmentquality = gtk.Adjustment(float(self.vconfig['screenshot']['quality']), 0, 100, 1, 0, 0)
        self.preferencesSpinquality = gtk.SpinButton(self.adjustmentquality)
        self.preferencesSpinquality.set_numeric(True)


        # Combos
        self.preferencesComboformat = gtk.combo_box_new_text()
        self.preferencesComboformat.append_text("JPEG")
        self.preferencesComboformat.append_text("PNG")
        if (self.vconfig['screenshot']['format'] == "jpeg"):
            self.preferencesComboformat.set_active(0)
        else: 
            self.preferencesComboformat.set_active(1)

        self.preferencesChecknotifications = gtk.CheckButton()
        if (self.vconfig['server']['notify'] == "True"):
            self.preferencesChecknotifications.set_active(1)
        else: 
            self.preferencesChecknotifications.set_active(0)

        # Close button
        self.preferencesButtonclose = gtk.Button("Close", gtk.STOCK_CLOSE)
        self.preferencesButtonclose.connect("clicked", lambda wid: self.save())

        # Add labels to hboxes
        self.preferencesHBox1.pack_start(self.preferencesLabelport, False, False, 12)
        self.preferencesHBox2.pack_start(self.preferencesLabelquality, False, False, 12)
        self.preferencesHBox3.pack_start(self.preferencesLabelformat, False, False, 12)
        self.preferencesHBox4.pack_start(self.preferencesLabelnotifications, False, False, 12)

        self.preferencesHBox1.pack_end(self.preferencesSpinport, False, False, 7)
        self.preferencesHBox2.pack_end(self.preferencesSpinquality, False, False, 7)
        self.preferencesHBox3.pack_end(self.preferencesComboformat, False, False, 7)
        self.preferencesHBox4.pack_end(self.preferencesChecknotifications, False, False, 7)

        # Add Hboxes to the Vbox
        self.preferencesVBox.pack_start(self.preferencesLabelsettings, False, False, 4)
        self.preferencesVBox.pack_start(self.preferencesHBox1, False, False, 0)
        self.preferencesVBox.pack_start(self.preferencesHBox2, False, False, 0)
        self.preferencesVBox.pack_start(self.preferencesHBox3, False, False, 0)
        self.preferencesVBox.pack_start(self.preferencesHBox4, False, False, 0)
        self.preferencesVBox.pack_end(self.preferencesButtonclose, False, False, 5)

        # Add vbox
        self.preferences.add(self.preferencesVBox)
        self.preferences.show_all()

    def save(self):
        """ Save and hide the preferences dialog """
        # Determine the method
        self.configurationmethod = "server"


        # Switch to the proper values
        formatvalue = str(self.preferencesComboformat.get_active_text())
        if formatvalue == "PNG":
            formatvalue = "png"
        else:
            formatvalue = "jpeg"

        notifyvalue = self.preferencesChecknotifications.get_active()
        if notifyvalue:
            notifyvalue = 'True'
        else:
            notifyvalue = 'False'

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

        # Check if the configuration changed
        if (self.configurationdict != self.vconfig):
            self.config.save(self.configurationdict)
            #self.gui.talk(self.gui, "updateConfig")	
        self.preferences.hide()
