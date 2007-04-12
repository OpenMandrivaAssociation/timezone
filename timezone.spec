# RH 2007c-1.fc6
%define name	timezone
%define epoch	6
%define version	2007c
%define release	%mkrel 2

%define tzdata_version %{version}
%define tzcode_version %{version}

# the zic(8) and zdump(8) manpages are already in man-pages
%define build_manpages 0

# don't use new TZ format yet (zic & zdump from glibc 2.4.90)
# XXX update after 2007.1 release, for all past releases too?
%define new_format 0
%if %{mdkversion} > 200710
%define new_format 1
%endif

# define glibc mininmal version which drops /etc/localtime
# XXX update for older distributions here
%if %{mdkversion} >= 200710
%define glibc_min_version 6:2.4-%{mkrel 8}
%endif

Summary:	Timezone data
Name:		%{name}
Epoch:		%{epoch}
Version:	%{version}
Release:	%{release}
License:	GPL
Group:		System/Base
Conflicts:	glibc < 6:2.2.5-6mdk
Source0:	tzdata-base-0.tar.bz2
Source1:	ftp://elsie.nci.nih.gov/pub/tzdata%{tzdata_version}.tar.gz
Source2:	ftp://elsie.nci.nih.gov/pub/tzcode%{tzcode_version}.tar.gz
Source3:	update-localtime.sh
Patch0:		tzdata-mdvconfig.patch
Patch1:		tzdata-extra-tz-links.patch
Patch2:		tzdata-tzcode2006a.patch
BuildRequires:	gawk, perl
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
This package contains data files with rules for various timezones
around the world.

%prep
%setup -q -n tzdata
mkdir tzdata%{tzdata_version}
tar xzf %{SOURCE1} -C tzdata%{tzdata_version}
mkdir tzcode%{tzcode_version}
tar xzf %{SOURCE2} -C tzcode%{tzcode_version}

%patch0 -p1 -b .mdvconfig
%patch1 -p1 -b .extra-tz-links
%if ! %{new_format}
cd tzcode%{tzcode_version}
%patch2 -p2 -b .tzcode2006a
cd ..
%endif

ln -s Makeconfig.in Makeconfig
cat > config.mk << EOF
objpfx = `pwd`/obj/
sbindir = %{_sbindir}
datadir = %{_datadir}
install_root = %{buildroot}
sysdep-CFLAGS = %{optflags}
EOF

%build
%make
grep -v tz-art.htm tzcode%{tzcode_version}/tz-link.htm > tzcode%{tzcode_version}/tz-link.html

%install
rm -rf $RPM_BUILD_ROOT

make install

# nuke unpackaged files
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/localtime

# install man pages
%if %{build_manpages}
mkdir -p $RPM_BUILD_ROOT%{_mandir}/man8
for f in zic zdump; do
install -m 644 tzcode*/$f.8 $RPM_BUILD_ROOT%{_mandir}/man8/
done
%endif

# install update-localtime script
mkdir -p $RPM_BUILD_ROOT%{_sbindir}
install -m 755 %{SOURCE3} $RPM_BUILD_ROOT%{_sbindir}/update-localtime
perl -pi -e 's|\@datadir\@|%{_datadir}|;' \
	 -e 's|\@sysconfdir\@|%{_sysconfdir}|' \
	$RPM_BUILD_ROOT%{_sbindir}/update-localtime

%check
echo ====================TESTING=========================
make check
echo ====================TESTING END=====================

%post -p %{_sbindir}/update-localtime

# XXX next glibc updates are expected to remove /etc/localtime
%triggerpostun -- glibc %{?glibc_min_version:< %{glibc_min_version}}
if [ ! -f %{_sysconfdir}/localtime ]; then
  %{_sbindir}/update-localtime
fi

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc tzcode%{tzcode_version}/README
%doc tzcode%{tzcode_version}/Theory
%doc tzcode%{tzcode_version}/tz-link.html
%{_sbindir}/zdump
%{_sbindir}/zic
%{_sbindir}/update-localtime
%if %{build_manpages}
%{_mandir}/man8/zdump.8*
%{_mandir}/man8/zic.8*
%endif
%dir %{_datadir}/zoneinfo
%{_datadir}/zoneinfo/*


