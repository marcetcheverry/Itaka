Summary: On-demand screenshooting server
Name: itaka
Version: 0.2.2
Release: 1
License: GPL
Group: Applications/Communications
URL: http://www.jardinpresente.com.ar/trac/itaka/

Packager: Kurt Erickson <psychogenicshk@users.sourceforge.net>

Source: http://internap.dl.sourceforge.net/sourceforge/itaka/itaka-0.2.2.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

Requires: python >= 2.3
Requires: pygtk2 >= 2.10
Requires: python-twisted

%description
Itaka is a on-demand screenshooting server based on the HTTP protocol.
It integrates a specifically coded server to take screenshots on-demand when
your machine is queried through a remote browser.

It features the following:
 * Supports PNG/JPEG (with quality adjustment) image types.
 * Basic HTTP authentication.
 * Simple manipulation of the screenshot through scaling and quality 
   adjustments.
 * Desktop notifications.

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
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc AUTHORS BUGS ChangeLog COPYING COPYRIGHT DOCUMENTATION HACKING README README.Debian README.Windows TODO

%{_prefix}/bin/itaka
%{_prefix}/share/man/man1/itaka.1.gz
%{_prefix}/share/applications/itaka.desktop
%{_prefix}/share/itaka/images/itaka.png
%{_prefix}/share/itaka/images/itaka-take.png
%{_prefix}/share/itaka/images/itaka-secure.png
%{_prefix}/share/itaka/images/itaka-secure-take.png
%{_prefix}/share/itaka/images/itaka16x16-take.png
%{_prefix}/share/itaka/images/itaka16x16-secure-take.png
%{_prefix}/share/itaka/images/itaka64x64.png
%{_prefix}/share/pixmaps/itaka.png
%{_prefix}/lib/itaka/uigtk.py
%{_prefix}/lib/itaka/config.py
%{_prefix}/lib/itaka/error.py
%{_prefix}/lib/itaka/server.py
%{_prefix}/lib/itaka/itaka.py
%{_prefix}/lib/itaka/screenshot.py
%{_prefix}/lib/itaka/console.py
%{_prefix}/lib/itaka/uigtk.pyc
%{_prefix}/lib/itaka/config.pyc
%{_prefix}/lib/itaka/error.pyc
%{_prefix}/lib/itaka/server.pyc
%{_prefix}/lib/itaka/itaka.pyc
%{_prefix}/lib/itaka/screenshot.pyc
%{_prefix}/lib/itaka/console.pyc

%changelog
* Thu Jul 20 2007 Kurt Erickson <psychogenicshk@users.sourceforge.net> - 0.2.1-2
- Removed notify-python dependancy (it's optional).

* Thu Jul 19 2007 Kurt Erickson <psychogenicshk@users.sourceforge.net> - 0.2.1-1
- Pulled 0.2.1 from upstream.

* Wed Jul  4 2007 Kurt Erickson <psychogenicshk@users.sourceforge.net> - 0.2-1
- Initial package release.
