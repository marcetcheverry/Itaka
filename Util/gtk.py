import time, thread
import pygtk

pygtk.require('2.0')
import gtk

def loop(string, sleeptime):
	while(True):
		print "Pasaron dos"
		time.sleep(3)
def destroy(widget, data=None):
	gtk.threads_enter()
	gtk.main_quit()
	gtk.threads_leave()
	
def whatever(blah, blahs2):
	thread.start_new_thread(loop,("Threaduno",2))

def main():
	gtk.threads_enter()
	window = gtk.Window(gtk.WINDOW_TOPLEVEL)
	window.connect("destroy", destroy)
	button = gtk.Button("Loop")
	button.connect("clicked", whatever, None)
	window.add(button)
	
	window.show_all()
	gtk.main()
	gtk.threads_leave()

main()
while True: pass

