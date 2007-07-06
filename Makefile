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
DESTDIR = $(PREFIX)

LIBDIR = $(DESTDIR)/lib/itaka
BINDIR = $(DESTDIR)/bin
DATADIR = $(DESTDIR)/share/itaka
IMAGESDIR = $(DATADIR)/images
# For debian compatibility
REPLACEIMAGESDIR = $(PREFIX)/share/itaka/images
APPLICATIONSDIR = $(DESTDIR)/share/applications
ICONDIR = $(DESTDIR)/share/pixmaps
MANDIR = $(DESTDIR)/share/man/man1

PYFILES := $(shell $(FIND) . -name "*.py" -print)

install: 
	mv config.py config.py.old
	sed -e "s|/usr/share/itaka/images/|$(REPLACEIMAGESDIR)|g" config.py.old > config.py
	$(INSTALL) -m 755 -d $(BINDIR) $(DATADIR) $(LIBDIR) $(IMAGESDIR) $(APPLICATIONSDIR) $(ICONDIR) $(MANDIR)
	$(INSTALL) -m 755 *.py $(LIBDIR)
	$(INSTALL) -m 644 share/images/* $(IMAGESDIR)
	$(INSTALL) -m 644 share/images/itaka.png $(ICONDIR)
	$(INSTALL) -m 644 share/itaka.desktop $(APPLICATIONSDIR)
	gzip -9 -c share/itaka.1 > share/itaka.1.gz
	$(INSTALL) -m 644 share/itaka.1.gz $(MANDIR)
	if test -f $(BINDIR)/itaka; then rm $(BINDIR)/itaka; fi	
	ln -sf  $(LIBDIR)/itaka.py $(BINDIR)/itaka
	echo $( ls $(BINDIR)/itaka )
	chmod +x $(BINDIR)/itaka
	mv config.py.old config.py
	rm share/itaka.1.gz
	for lang in i18n/*; do for pofile in $lang/LC_MESSAGES/*.po; do msgfmt $pofile -o $lang/LC_MESSAGES/itaka.mo; done; done
uninstall:
	rm -r $(BINDIR)/itaka $(DATADIR) $(LIBDIR) $(ICONDIR)/itaka.png $(APPLICATIONSDIR)/itaka.desktop $(MANDIR)/itaka.1.gz
