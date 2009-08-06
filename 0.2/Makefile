INSTALL ?= install
RM ?= rm
MSGFMT ?= msgfmt
MSGMERGE ?= msgmerge
XGETTEXT ?= xgettext
FIND ?= find

PREFIX = /usr/local
# When debian builds it, it passes its own DESTDIR
DESTDIR = $(PREFIX)

LIBDIR = $(DESTDIR)/lib/itaka
BINDIR = $(DESTDIR)/bin
DATADIR = $(DESTDIR)/share/itaka
IMAGESDIR = $(DATADIR)/images
APPLICATIONSDIR = $(DESTDIR)/share/applications
ICONDIR = $(DESTDIR)/share/pixmaps
MANDIR = $(DESTDIR)/share/man/man1

# For debian compatibility, these are hardcoded
REPLACEIMAGESDIR = $(PREFIX)/share/itaka/images/

PYFILES := $(shell $(FIND) . -name "*.py" -print)

install: 
	# Replace images directory
	mv config.py config.py.old
	sed "s|/usr/local/share/itaka/images/|$(REPLACEIMAGESDIR)|g" config.py.old > config.py

	gzip -9 -c share/itaka.1 > share/itaka.1.gz

	$(INSTALL) -m 755 -d $(BINDIR) $(DATADIR) $(LIBDIR) $(IMAGESDIR) $(APPLICATIONSDIR) $(ICONDIR) $(MANDIR)
	$(INSTALL) -m 755 *.py $(LIBDIR)

	# We only need a few images
	$(INSTALL) -m 644 share/images/itaka.png $(IMAGESDIR)
	$(INSTALL) -m 644 share/images/itaka-take.png $(IMAGESDIR)
	$(INSTALL) -m 644 share/images/itaka-secure.png $(IMAGESDIR)
	$(INSTALL) -m 644 share/images/itaka-secure-take.png $(IMAGESDIR)
	$(INSTALL) -m 644 share/images/itaka16x16-take.png $(IMAGESDIR)
	$(INSTALL) -m 644 share/images/itaka16x16-secure-take.png $(IMAGESDIR)
	$(INSTALL) -m 644 share/images/itaka64x64.png $(IMAGESDIR)

	ln -sf $(IMAGESDIR)/itaka.png $(ICONDIR)/itaka.png

	$(INSTALL) -m 644 share/itaka.desktop $(APPLICATIONSDIR)
	$(INSTALL) -m 644 share/itaka.1.gz $(MANDIR)
	if test -f $(BINDIR)/itaka; then rm $(BINDIR)/itaka; fi	

	# Create our binary directory for the symlink
	if test ! -d $(BINDIR); then mkdir $(BINDIR); fi
	ln -sf  $(LIBDIR)/itaka.py $(BINDIR)/itaka

	#echo $( ls $(BINDIR)/itaka )
	chmod +x $(BINDIR)/itaka
	
	# Clean up
	# Get our pre-modified config.py back
	mv config.py.old config.py

uninstall:
	rm -r $(BINDIR)/itaka $(DATADIR) $(LIBDIR) $(ICONDIR)/itaka.png $(APPLICATIONSDIR)/itaka.desktop $(MANDIR)/itaka.1.gz

clean:
	find . -type f  \( -regex '.+\.py[co]' -o -name 'itaka.1.gz' \) -exec rm -f {} \;

help:
	@echo Usage:
	@echo make install              - install binaries into the official directories
	@echo make clean                - delete built modules and object files
	@echo make uninstall            - uninstall binaries from the official directories
	@echo make help                 - prints this help
	@echo

