#! /usr/bin/env python
# -*- coding: utf8 -*-
# Itaka Preferences dialog

import globals as iglobals
# Import GTK+
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
	def prefwindow(self, widget, icon):
		""" Set up the preferences window. """
	        self.icon_pixbuf = icon	
		self.preferences = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.preferences.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		self.preferences.connect("destroy", lambda call: self.preferences.hide())
		self.preferences.set_title("Preferences")
		self.preferences.set_icon(self.icon_pixbuf)
		self.preferences.set_border_width(12)
		self.preferencesVBox = gtk.VBox(False, 0)

		# Create the nine hboxes of the apocalypse.
		self.preferencesHBox1 = gtk.HBox(False, 0)
		self.preferencesHBox2 = gtk.HBox(False, 0)
		self.preferencesHBox3 = gtk.HBox(False, 0)
		self.preferencesHBox4 = gtk.HBox(False, 0)
		self.preferencesHBox5 = gtk.HBox(False, 0)
		self.preferencesHBox6 = gtk.HBox(False, 0)
		self.preferencesHBox7 = gtk.HBox(False, 0)
		self.preferencesHBox8 = gtk.HBox(False, 0)
		self.preferencesHBox9 = gtk.HBox(False, 0)

		# Widgets
		# Section labels
		self.preferencesLabelbackbend = gtk.Label("<b>Backbend</b>")
		self.preferencesLabelbackbend.set_use_markup(True)
		self.preferencesLabelbackbend.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabelbackbend.set_alignment(0.03, 0.50)
		
		self.preferencesLabelscreenshots = gtk.Label("<b>Screenshooting method</b>")
		self.preferencesLabelscreenshots.set_use_markup(True)
		self.preferencesLabelscreenshots.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabelscreenshots.set_alignment(0.03, 0.50)
		# Labels for input
		self.preferencesLabeltype = gtk.Label("Type:")
		self.preferencesLabeltype.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabeltype.set_alignment(0, 0.50)
		self.preferencesLabelport = gtk.Label("Port:")
		# Return the image
		self.preferencesLabelport.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabelport.set_alignment(0, 0.50)
		self.preferencesLabelhost = gtk.Label("Host:")
		self.preferencesLabelhost.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabelhost.set_alignment(0, 0.50)
		self.preferencesLabelusername = gtk.Label("Username:")
		self.preferencesLabelusername.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabelusername.set_alignment(0, 0.50)
		self.preferencesLabelpassword = gtk.Label("Password:")
		self.preferencesLabelpassword.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabelpassword.set_alignment(0, 0.50)
		self.preferencesLabeltime = gtk.Label("Time:")
		self.preferencesLabeltime.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabeltime.set_alignment(0, 0.50)
		self.preferencesLabelseconds = gtk.Label("seconds")
		self.preferencesLabelamount = gtk.Label("Amount:")
		self.preferencesLabelamount.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabelamount.set_alignment(0, 0.50)
		self.preferencesLabelmethod = gtk.Label("Method:")
		self.preferencesLabelmethod.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabelmethod.set_alignment(0, 0.50)
		self.preferencesLabelapplication = gtk.Label("Application:")
		self.preferencesLabelapplication.set_justify(gtk.JUSTIFY_LEFT)
		self.preferencesLabelapplication.set_alignment(0, 0.50)

		# Entries
		self.preferencesEntryhost = gtk.Entry()
		self.preferencesEntryusername = gtk.Entry()
		self.preferencesEntrypassword = gtk.Entry()
		self.preferencesEntrypassword.set_visibility(False)
		self.preferencesEntryapplication = gtk.Entry()

		# Spinbuttons (FIXME)
		self.preferencesSpinport = gtk.SpinButton()
		self.preferencesSpinport.set_value(8000)
		#self.preferencesSpinport.set_range(1, 65550)
		self.preferencesSpintime = gtk.SpinButton()
		self.preferencesSpintime.set_value(5)
		#self.preferencesSpintime.set_range(1, 65550)
		self.preferencesSpinamount = gtk.SpinButton()
		#self.preferencesSpinamount.set_range(1, 65550)

		# Combos
		# Using simple method http://www.pygtk.org/pygtk2tutorial/sec-ComboBoxAndComboboxEntry.html
		self.preferencesCombotype = gtk.combo_box_new_text()
		self.preferencesCombotype.append_text("Itaka")
		self.preferencesCombotype.append_text("FTP")
		self.preferencesCombotype.set_active(0)
		self.preferencesCombotype.connect("changed", self.__preferencesComboHandler, "Type")

		self.preferencesCombomethod = gtk.combo_box_new_text()
		self.preferencesCombomethod.append_text("GTK+")
		self.preferencesCombomethod.append_text("External")
		self.preferencesCombomethod.set_active(0)
		self.preferencesCombomethod.connect("changed", self.__preferencesComboHandler, "Method")
		
		# Close button
		self.preferencesButtonclose = gtk.Button("Close", gtk.STOCK_CLOSE)
		self.preferencesButtonclose.connect("clicked", lambda wid: self.preferences.hide())

		# Add labels to hboxes
		self.preferencesHBox1.pack_start(self.preferencesLabeltype, False, False, 12)
		self.preferencesHBox2.pack_start(self.preferencesLabelport, False, False, 12)
		self.preferencesHBox3.pack_start(self.preferencesLabelhost, False, False, 12)
		self.preferencesHBox4.pack_start(self.preferencesLabelusername, False, False, 12)
		self.preferencesHBox5.pack_start(self.preferencesLabelpassword, False, False, 12)
		self.preferencesHBox6.pack_start(self.preferencesLabeltime, False, False, 12)
		self.preferencesHBox6.pack_end(self.preferencesLabelseconds, False, False, 12)
		self.preferencesHBox7.pack_start(self.preferencesLabelamount, False, False, 12)
		self.preferencesHBox8.pack_start(self.preferencesLabelmethod, False, False, 12)
		self.preferencesHBox9.pack_start(self.preferencesLabelapplication, False, False, 12)

		# Add entries
		self.preferencesHBox3.pack_start(self.preferencesEntryhost, False, False, 0)
		self.preferencesHBox4.pack_start(self.preferencesEntryusername, False, False, 0)
		self.preferencesHBox5.pack_start(self.preferencesEntrypassword, False, False, 0)
		self.preferencesHBox9.pack_start(self.preferencesEntryapplication, False, False, 0)

		# Add SpinButton
		self.preferencesHBox2.pack_start(self.preferencesSpinport, False, False, 0)
		self.preferencesHBox6.pack_start(self.preferencesSpintime, False, False, 0)
		self.preferencesHBox7.pack_start(self.preferencesSpinamount, False, False, 0)

		# Add combos
		self.preferencesHBox1.pack_start(self.preferencesCombotype, False, False, 0)
		self.preferencesHBox8.pack_start(self.preferencesCombomethod, False, False, 0)

		# Add Hboxes to the Vbox
		self.preferencesVBox.pack_start(self.preferencesLabelbackbend, False, False, 4)
		self.preferencesVBox.pack_start(self.preferencesHBox1, False, False, 0)
		self.preferencesVBox.pack_start(self.preferencesHBox2, False, False, 0)
		self.preferencesVBox.pack_start(self.preferencesHBox3, False, False, 0)
		self.preferencesVBox.pack_start(self.preferencesHBox4, False, False, 0)
		self.preferencesVBox.pack_start(self.preferencesHBox5, False, False, 0)
		self.preferencesVBox.pack_start(self.preferencesHBox6, False, False, 0)
		self.preferencesVBox.pack_start(self.preferencesHBox7, False, False, 0)
		self.preferencesVBox.pack_start(self.preferencesLabelscreenshots, False, False, 4)
		self.preferencesVBox.pack_start(self.preferencesHBox8, False, False, 0)
		self.preferencesVBox.pack_start(self.preferencesHBox9, False, False, 0)

		# Add button
		self.preferencesVBox.pack_end(self.preferencesButtonclose, False, False, 5)

		# Add vbox
		self.preferences.add(self.preferencesVBox)
		self.preferences.show_all()

		# Hide HBoxes that should appear when preferencesComboHandler() tells them to

		self.preferencesHBox9.hide_all()
		self.preferencesHBox3.hide_all()
		self.preferencesHBox4.hide_all()
		self.preferencesHBox5.hide_all()
		self.preferencesHBox6.hide_all()
		self.preferencesHBox7.hide_all()


	def __preferencesComboHandler(self, widget, who):   
		""" Callback for the ComboBoxes in preferences. """
		# See what it sent us
		if ( who == "Type"):
		# The following codes handles showing the extra boxes
		 if ( self.preferencesCombotype.get_active_text() == "FTP"):
	 	 	self.preferencesHBox3.show_all()
		 	self.preferencesHBox4.show_all()
		 	self.preferencesHBox5.show_all()
	 		self.preferencesHBox6.show_all()
		 	self.preferencesHBox7.show_all()
		 else:
			self.preferencesHBox3.hide_all()
			self.preferencesHBox4.hide_all()
			self.preferencesHBox5.hide_all()
			self.preferencesHBox6.hide_all()
			self.preferencesHBox7.hide_all()
		elif ( who == "Method"):
		 if ( self.preferencesCombomethod.get_active_text() == "External"):
		 	self.preferencesHBox9.show_all()
		 else:
			self.preferencesHBox9.hide_all()
