PYTHON ?= python2.4
INSTALL ?= install
RM ?= rm
MSGFMT ?= msgfmt
MSGMERGE ?= msgmerge
XGETTEXT ?= xgettext
FIND ?= find

# autodetect GNOME prefix, change this if you want it elsewhere
#PREFIX ?= `pkg-config libgnome-2.0 --variable=prefix || echo /usr`
PREFIX = /usr
DESTDIR = #debian/itaka
DESTDIR = $(PREFIX)

LIBDIR = $(DESTDIR)$(PREFIX)/lib/itaka
BINDIR = $(DESTDIR)$(PREFIX)/bin
DATADIR = $(DESTDIR)$(PREFIX)/share/itaka
IMAGESDIR = $(DATADIR)/images
APPLICATIONSDIR = $(DESTDIR)$(PREFIX)/share/applications
ICONDIR = $(DESTDIR)$(PREFIX)/share/pixmaps

PYFILES := $(shell $(FIND) . -name "*.py" -print)

install: 
	mv config.py config.py.old
	sed -e "s|/usr/share/itaka/images/|$(IMAGESDIR)|g" config.py.old > config.py
	$(INSTALL) -m 755 -d $(BINDIR) $(DATADIR) $(LIBDIR) $(IMAGESDIR) $(APPLICATIONSDIR) $(ICONDIR) 
	$(INSTALL) -m 755 *.py $(LIBDIR)
	$(INSTALL) -m 644 share/images/* $(IMAGESDIR)
	$(INSTALL) -m 644 share/images/itaka.png $(ICONDIR)
	$(INSTALL) -m 644 share/itaka.desktop $(APPLICATIONSDIR)
	if test -f $(BINDIR)/itaka; then rm $(BINDIR)/itaka; fi	
	ln -s  $(DATADIR)/itaka.py $(BINDIR)/itaka
	echo $( ls $(BINDIR)/itaka )
	chmod +x $(BINDIR)/itaka
	mv config.py.old config.py
uninstall:
	rm -r $(BINDIR)/itaka $(DATADIR) $(LIBDIR) $(ICONDIR)/itaka.png $(APPLICATIONSDIR)/itaka.desktop
