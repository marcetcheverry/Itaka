#!/usr/bin/env python
# Itaka web server (Twisted-GTK back)

# Twisted resources
from twisted.python import log
from twisted.web import server, resource, static
from twisted.internet import reactor
from twisted.web.resource import Resource

# Low level resources
import sys, os
import gtk

# Itaka global variables
iversion = 'Devel'
iport = 8000
# Image format
iformat = 'png'

icserved = 0

# Contador de imagen (logica puta de Python)
# Logea twisted debug a stdout.
log.startLogging(sys.stdout)

# Itaka
log.msg('Itaka ' + str(iversion) + ' initiated on port ' + str(iport) + ' TCP. Serving screenshots as ' + iformat.upper() + ' images.')

class ImageResource(Resource):

    # Screenshot counter
    icserved = 0

    def shootScreen(self):
    # This function takes the screenshot with GTK and returns it as a variable for request
       #	os.system('su marccd -c notifyit')

	self.shot = 'image.' + iformat
	w = gtk.gdk.screen_width()
        h = gtk.gdk.screen_height()
        screenshot = gtk.gdk.Pixbuf.get_from_drawable(
                    gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, w, h),
                    gtk.gdk.get_default_root_window(), 
                    gtk.gdk.colormap_get_system(),
                    0, 0, 0, 0, w, h)
        screenshot.save(self.shot, self.shot.split('.')[1])
	
	# Return the shot as a variable
	return self.shot
	#os.system((str('%s image.jpg')) % (application))
    	#os.system('%s image.jpg') % application

    def render_GET(self, request):
    	# Set up basic info vars about the requester (ic = itaka client)
	self.icip = request.getClientIP()
	self.icbrowser = request.getClient()
	
	# This provides the screenshot for the requester as image/png
        request.setHeader("Content-type", "image/png")
	# Call for the screenshot to be taken
	self.shootScreen()
	
	#render_METHOD methods are expected to return a string which will be the rendered page, unless the return value is twisted.web.server.NOT_DONE_YET, in which case it is this class's responsibility to write the results to request.write(data), then call request.finish().
	
	# Logear un mensaje o hacer algo, tmb se puede usar print.
	global icserved
	icserved += 1
	log.msg('Screenshot taken by ' + self.icip + ' (' + self.icbrowser + ')''')
    	os.system('su marccd -c notifyit "' + self.icip + '" "' + str(icserved) + '"')
	
	#print request.getClientIP()

	#print "hola"
	# Llamar a libnotify
	#os.system('notify-send -i /home/marccd/Itaka/itaka.png -u normal "Itaka" "Screenshot served\n 144.32.128.13"')
	
	# Return the taken shot from shootScreen() with read for PutChild to render it.
    	return open(self.shot).read()
# Twisted server set up image, etc
root = static.Data('<html><body><img src="image.png" alt="Screenshot" border="0"></a></body</html>', 'text/html')
root.putChild('image.png', ImageResource())
root.putChild('', root)

# Observar
#log.addObserver(ImageResource().catchLog)
try:
	site = server.Site(root)
	reactor.listenTCP(iport, site)
	reactor.run()
except KeyboardInterrupt:
	# FIXME
	log.msg('Itakaterminated by user')
