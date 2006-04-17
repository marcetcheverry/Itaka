#! /usr/bin/env python
# -*- coding: utf8 -*-
""" Itaka GUI and Core """

# Import general modules
import sys, os, datetime, traceback 

try:
	from twisted.internet import gtk2reactor
	gtk2reactor.install()

	from twisted.python import log
	from twisted.web import server, static
	from twisted.web.resource import Resource
	from twisted.internet import reactor
except ImportError:
	print "[*] ERROR: Failed to initialize Twisted."
	sys.exit(1)
	
# Import GTK+
try:
	import pygtk
	pygtk.require("2.0")
except ImportError:
	print "[*] WARNING: Pygtk module is missing."
        pass
try:
        import gtk, gobject
except ImportError:
	print "[*] ERROR: GTK+ Python bindings are missing."
	sys.exit(1)

try:
	from egg import trayicon
	trayiconSupport = True
except ImportError:
	print "[*] WARNING: GTK+ Python TrayIcon bindings are missing, disabling trayicon."
	trayiconSupport = False
	pass

# Itaka modules
try:
	import config
	iconfig = config.ConfigParser().load()

	import console as iconsole
	import preferences as ipreferences
	import server as iserver
	if (iconfig['itaka']['audio'] == "True"): import audio as iaudio
	import ftp as iftp
except:
	print "[*] ERROR: Failed to import Itaka modules."
	traceback.print_exc()
	sys.exit(1)
	
class Gui:
    """ GUI Class. """
    def __init__(self):
	# Workaround: pass a reference of GUI to Screenshot module for its notification handling.
	self.sinstance = iserver.ImageResource(self)
	
	# Set up Server variables, if needed.
	if (iconfig['itaka']['method'] == 'server'):
		self.root = static.Data(iconfig['html']['html'], 'text/html; charset=UTF-8')
		# Registers an identitiy (resource, file).
		if (iconfig['itaka']['audio'] == "True"): self.root.putChild('audio', iaudio.AudioResource())	
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

	# TrayIcon, if needed.
	if (trayiconSupport):
        	# Set up TrayIcon
		self.menu = gtk.Menu()
        	self.itray = trayicon.TrayIcon("Itaka")
        	self.itraylogobox = gtk.EventBox()
		# Build the menu FIXME: Add icons.
		self.menu = gtk.Menu()
		self.menuabout = gtk.MenuItem("About")
		self.menuprefs = gtk.MenuItem("Preferences")
		self.menustop = gtk.MenuItem("Stop")
		self.menustart = gtk.MenuItem("Start")
		self.menuquit = gtk.MenuItem("Quit")

		for f in (self.menuabout, self.menuprefs, self.menustop, self.menustart, self.menuquit): self.menu.append(f)
		
		# Connect
		self.menustart.connect("activate", self.startstop, "Start")
		self.menustop.connect("activate", self.startstop, "Stop")
		self.menuprefs.connect("activate", ipreferences.Preferences().prefwindow, self.icon_pixbuf)
		self.menuabout.connect("activate", self.about)
		self.menuquit.connect("activate", self.destroy)
		
		for f in (self.menuquit, self.menustop, self.menustart, self.menuprefs, self.menuabout):	f.show()

      		self.itraylogo = gtk.Image()
       		self.itraylogo.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(os.path.join(config.image_dir, "itaka.png")).scale_simple(20, 20,gtk.gdk.INTERP_BILINEAR))
        	self.itraylogobox.add(self.itraylogo)
       		self.itraylogobox.connect("button_press_event", self.__trayclicked)

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
        self.preferencesButton.connect("clicked", ipreferences.Preferences().prefwindow, self.icon_pixbuf)
	
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

        # Show window & tray.
        self.window.show_all()
	if (trayiconSupport):
		self.itray.add(self.itraylogobox)
        	self.itray.show_all()

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
	# This function is disabled on FTP mode
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
        	self.console = iconsole.Console(self)
	except AttributeError:
		print "[*] ERROR: Console()"
		traceback.print_exc()
		sys.exit(1)
		
        self.greact = reactor.run()

    def about(self, data=None):
	""" Create the About dialog. """
	self.about = gtk.AboutDialog()
	self.about.set_name('Itaka')
	self.about.set_version(config.version.version)
	self.about.set_copyright(u'© 2003-2006 Marc Etcheverry')
	self.about.set_comments('Screenshooting de mercado.')
	self.about.set_authors(['Marc Etcheverry <m4rccd@yahoo.com>'])
	self.about.set_website('http://itaka.sourceforge.net')
	self.about.set_logo(gtk.gdk.pixbuf_new_from_file(os.path.join(config.image_dir, "itaka.png")))
	self.about.set_icon(self.icon_pixbuf)
	self.about.show()

    def __trayclicked(self, widget, event):
        """ Handle the clicks on the trayicon. """
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            if (self.window.get_property("visible")):
                self.window.hide()
            else:
                self.window.show()
                self.window.set_position(gtk.WIN_POS_CENTER)
	elif event.button == 3:
            # Create menu
	    self.menu.popup(None,None,None,event.button,event.time)
	
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
	    if (iconfig['itaka']['method'] == 'server'):
	    	if (hasattr(self, 'ilistener')):	return True
	    else:
	    	if (hasattr(self, 'ftprunning')):	pass
		    
	    if (iconfig['itaka']['method'] == 'server'):
            		# Start up the twisted site
            		self.site = server.Site(self.root)
            		# Start Server reactor. Make an instance to distinguish from self.greactor().
            		self.ilistener = reactor.listenTCP(int(iconfig['server']['port']), self.site)
			if (data):
		    		self.buttonStartstop.set_active(True)
	    else:
			# Start up the FTP thread, with a GUI and ImageResource instance
			self.ftprunning = iftp.Ftp(self, self.sinstance)
			self.ftprunning.start()
			
			# Tell the user that we are uploading
			self.labelLastip.set_text('Uploading to FTP %s:%s' % (iconfig['ftp']['host'], iconfig['ftp']['port']))
		
			# Pause does not work on FTP.
			self.debugpausebutton.set_sensitive(False)
	   	 	# If called from tray, set the main button active
	    		if (data):
		    		self.buttonStartstop.set_active(True)
	    
            # Announce on log y console stdout
	    if (iconfig['itaka']['method'] == 'server'):
	            	self.console.msg('Server listening on port %s TCP. Serving screenshots as %s images with %s%% quality.' % (iconfig['server']['port'], iconfig['screenshot']['format'].upper(), iconfig['screenshot']['quality']), True)
	    else:
			self.console.msg('FTP upload sequence to %s:%s started every %s seconds. Uploading screenshots as %s images with %s%% quality.' % (str(iconfig['ftp']['host']), iconfig['ftp']['port'], iconfig['screenshot']['time'], iconfig['screenshot']['format'].upper(), iconfig['screenshot']['quality']), True)
			
			
            # Change buttons
            self.buttonStartstop.set_label("Stop")
            self.startstopimage.set_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON)
            self.buttonStartstop.set_image(self.startstopimage)
            	
	    # Close the expander
	    self.expander.set_sensitive(True)
	    if (iconfig['itaka']['notify'] == "True"):
		    self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka-take.png"))

        else:
	    if (iconfig['itaka']['method'] == 'server'):
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
	    else:
		if hasattr(self, 'ftprunning'):
            		self.console.msg('Stopping FTP sequence...', True)
			self.ftprunning.stop()
			ftpdemandstop = True
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
	    pass

    def destroy(self, *args):
	# FIXME: Cleanup stale screenshot file
	# FIXME closing FTP bug
        """ Callback for the main window's destroy. """
        # Stop server(s). Check so it does not complain if close while not running.
        if hasattr(self, 'ilistener'):
            self.console.msg("Shutting down server...", True)
            #self.ilistener.stopListening()
	    del self.console
	if hasattr(self, 'ftprunning'):
            self.console.msg("Shutting down FTP backend...", True)
	    self.ftprunning.stop()
	    del self.ftprunning
        else:
	    # Console goodbye!
	    if hasattr(self, 'console'):	del self.console
	gtk.main_quit()

    def __calcsince(self, stime):
	""" Function to calculate the time difference from the last request to 
	the current time."""

	""" Handles all dates well, although if the last request was done a month
	or year ago it will display it as numbers of days. Did not bother to add 
	a check for it, but it should be trivial (compare the number of days to
	the current months, divide it. If > 365, divide also. """
	
	# Change now() for a date tuple to test the date parser
	self.isetdiff = datetime.datetime.now() - stime
	
	# Lets make it a string and split it for easier manipulation
	self.idiff = str(self.isetdiff).split(':')
	
	# Set up singular/plural checks
	self.hour = "hours"
	self.min = "minutes"

	# If an hour passed already
	if ("0" not in self.idiff[0]):
		if (self.idiff[0] == "1"): self.hour = "hour"
		# Remove the 0 prefix
		if ("0" in self.idiff[1][:1]): self.idiff[1] = self.idiff[1][1:]
		if (self.idiff[1] == "1"): self.min = "minute"
		self.labelTime.set_text("Time: %s %s, %s %s ago" % (self.idiff[0], self.hour, self.idiff[1], self.min))
		
	else:
		# Instance as minutes
		self.idiff = self.idiff[1]
		# Remove the 0 prefix
		if ("0" in self.idiff[:1]): self.idiff = self.idiff[1:]
		if (self.idiff == "1"):	self.min = "minute"
        	self.labelTime.set_text("Time: %s %s ago" % (self.idiff, self.min))

	# Need this so it runs more than once. Weird.
	return True

    def notify(self):
	""" Change the image on the main screen, for notification purpose. """
	self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka.png"))
	# Only run this event once
	return False

    def talk(self, action, data1=False, data2=False, data3=False):
        """ Handler for communcations between the server, FTP backend, and the GUI. """
	# FIXME: Cleanup
	
	# Set up alert string and console output
        if (iconfig['itaka']['alert'] == "True"): self.astring = "\a"
	if (iconfig['itaka']['method'] == 'server'):
		self.console.msg(self.astring + "Screenshot " + str(data1) + " served to: " + str(data2))
		
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
	    if (iconfig['itaka']['notify'] == "True"):
	    	self.itakaLogo.set_from_file(os.path.join(config.image_dir, "itaka-take.png"))
		# Call Inotify
		self.notifyimg = gobject.timeout_add(2000, self.notify)
		
	# Handler for FTP errors
	elif ( action == "updateFtpStatus"):
		    	# This toggles the button, which in itself calls startstop()
		    	self.buttonStartstop.set_active(False)	
			self.labelLastip.set_text('Error: %s' % (str(data1)))

if __name__ == "__main__":
	# Start the GTK reactor
	try:
		igui = Gui()
		igui.main()
	except AttributeError:
		print "[*] ERROR: Gui()"
		traceback.print_exc()
		sys.exit(1)
