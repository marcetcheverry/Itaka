Summary: On-demand screenshooting server
Name: itaka
Version: 1.0
Release: 1
License: GPL
Group: Applications/Communications
URL: http://www.jardinpresente.com.ar/trac/itaka/

Packager: Kurt Erickson <psychogenicshk@users.sourceforge.net>

Source: http://internap.dl.sourceforge.net/sourceforge/itaka/itaka-1.0.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

Requires: python >= 2.3
Requires: pygtk2 >= 2.10
Requires: python-twisted
Requires: notify-python

%description
Itaka is a on-demand screenshooting server based on the HTTP protocol.
It integrates a specifically coded server to take screenshots on-demand when
your machine is queried through a remote browser.

It features the following:
 * Supports PNG/JPEG (with quality adjustment) image types.
 * Basic HTTP authentication.
 * Simple manipulation of the screenshot through scaling and quality 
   adjustments.
 * Very polished GUI with notifications using Libnotify.

%prep
%setup -q

%build

%install
make install DESTDIR="$RPM_BUILD_ROOT%{_prefix}"

#make itaka.py symlink relative
rm $RPM_BUILD_ROOT%{_prefix}/bin/itaka
cd $RPM_BUILD_ROOT%{_prefix}/bin
ln -s ../lib/itaka/itaka.py ./itaka

%clean
# Might want to add a make clean, since I've added it.
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc AUTHORS BUGS ChangeLog COPYING COPYRIGHT DOCUMENTATION HACKING README README.Debian README.Windows TODO

%{_prefix}/bin/itaka
%{_prefix}/share/man/man1/itaka.1.gz
%{_prefix}/share/applications/itaka.desktop
%{_prefix}/share/itaka/images/itaka16x16.png
%{_prefix}/share/itaka/images/itaka-take.png
%{_prefix}/share/itaka/images/itaka32x32.png
%{_prefix}/share/itaka/images/itaka-secure-take.png
%{_prefix}/share/itaka/images/itaka64x64-take.png
%{_prefix}/share/itaka/images/itaka16x16-take.png
%{_prefix}/share/itaka/images/itaka512x512-take.png
%{_prefix}/share/itaka/images/itaka-secure.svg
%{_prefix}/share/itaka/images/itaka.psd
%{_prefix}/share/itaka/images/itaka64x64.png
%{_prefix}/share/itaka/images/itaka512x512.png
%{_prefix}/share/itaka/images/itaka.png
%{_prefix}/share/itaka/images/itaka.svg
%{_prefix}/share/itaka/images/itaka-secure.png
%{_prefix}/share/itaka/images/itaka-logo.png
%{_prefix}/share/itaka/images/favicon.ico
%{_prefix}/share/pixmaps/itaka.png
%{_prefix}/lib/itaka/uigtk.py
%{_prefix}/lib/itaka/config.py
%{_prefix}/lib/itaka/error.py
%{_prefix}/lib/itaka/server.py
%{_prefix}/lib/itaka/itaka.py
%{_prefix}/lib/itaka/screenshot.py
%{_prefix}/lib/itaka/console.py

%changelog
* Wed Jul  4 2007 Kurt Erickson <psychogenicshk@users.sourceforge.net> - 1.0-1
- Pulled 1.0 from upstream.
