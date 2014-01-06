#define tzdata_version %{version}
%define tzdata_version 2013g
%define tzcode_version 2013g

# the zic(8) and zdump(8) manpages are already in man-pages
%bcond_with manpages
%ifarch %{ix86} x86_64 %arm
%bcond_without java
%endif

Summary:	Timezone data
Name:		timezone
Epoch:		7
Version:	2013g
Release:	5
License:	GPL
Group:		System/Base
Source0:	ftp://ftp.iana.org/tz/releases/tzdata%{tzdata_version}.tar.gz
Source1:	ftp://ftp.iana.org/tz/releases/tzcode%{tzcode_version}.tar.gz
Source2:	javazic.tar.gz
Source3:	update-localtime.sh
Patch0:		tzdata-mdvconfig.patch
Patch1:		tzdata-extra-tz-links.patch
Patch2:		javazic-fixup.patch
Patch3:		timezone-data-2013f-makefile.patch
BuildRequires:	gawk
BuildRequires:	perl
Provides:	tzdata = %{version}-%{release}

%description
This package contains data files with rules for various timezones
around the world.

%if %{with java}
%package java
Summary:	Timezone data for Java
Group:		System/Base
Provides:	tzdata-java = %{version}-%{release}
# We use gcj instead of OpenJDK to avoid a circular build dependency.
# OpenJDK requires tzdata-java to be installed.
#BuildRequires:	java-1.5.0-gcj-devel gcj-tools libgcj13
BuildRequires:	java-rpmbuild

%description java
This package contains timezone information for use by Java runtimes.
%endif

%prep
%setup -q -c -a 1
%patch1 -p1 -b .extra-tz-links

%if %{with java}
mkdir javazic
tar xf %{SOURCE2} -C javazic
pushd javazic
%patch2 -p0 -b .javazic-fixup

# Hack alert! sun.tools may be defined and installed in the
# VM. In order to guarantee that we are using IcedTea/OpenJDK
# for creating the zoneinfo files, rebase all the packages
# from "sun." to "rht.". Unfortunately, gcj does not support
# any of the -Xclasspath options, so we must go this route
# to ensure the greatest compatibility.
mv sun rht
for f in `find . -name '*.java'`; do
        sed -i -e 's:sun\.tools\.:rht.tools.:g'\
               -e 's:sun\.util\.:rht.util.:g' $f
done
popd

# Create zone.info entries for deprecated zone names (#40184)
	chmod +w zone.tab
	echo '# zone info for backward zone names' > zone.tab.new
	while read link cur old x; do
		case $link-${cur+cur}-${old+old}${x:+X} in
		Link-cur-old)
			awk -v cur="$cur" -v old="$old" \
				'!/^#/ && $3 == cur { sub(cur,old); print }' \
				zone.tab || echo ERROR ;;
		Link-*)
			echo 'Error processing backward entry for zone.tab'
			exit 1 ;;
		esac
	done < backward >> zone.tab.new
	if grep -q '^ERROR' zone.tab.new || ! cat zone.tab.new >> zone.tab; then
		echo "Error adding backward entries to zone.tab"
		exit 1
	fi
	rm -f zone.tab.new
%endif
%patch3 -p1

%build
%make TZDIR=%{_datadir}/zoneinfo CFLAGS="%{optflags} -std=gnu99" LDFLAGS="%{ldflags}"
grep -v tz-art.htm tz-link.htm > tz-link.html

%if %{with java}
pushd javazic
%{javac} -source 1.5 -target 1.5 -classpath . `find . -name \*.java`
popd
%{java} -classpath javazic/ rht.tools.javazic.Main -V %{version} \
 -d zoneinfo/java \
 africa antarctica asia australasia europe northamerica pacificnew \
 southamerica backward etcetera solar87 solar88 solar89 systemv \
 javazic/tzdata_jdk/gmt javazic/tzdata_jdk/jdk11_backward
%endif

%install
make TOPDIR="%{buildroot}/usr" \
    TZDIR=%{buildroot}%{_datadir}/zoneinfo \
    ETCDIR=%{buildroot}%{_sbindir} \
    install

%if %{with java}
cp -a zoneinfo/java %{buildroot}%{_datadir}/javazi
%endif

# nuke unpackaged files
rm -f %{buildroot}%{_datadir}/zoneinfo/localtime
rm -rf %{buildroot}/usr/{lib,man}
rm -f %{buildroot}%{_bindir}/tzselect
rm -f %{buildroot}%{_mandir}/man3/new*.3*

# install man pages
%if %{with manpages}
mkdir -p %{buildroot}%{_mandir}/man8
for f in zic zdump; do
install -m 644 $f.8 %{buildroot}%{_mandir}/man8/
done
%endif

# install update-localtime script
mkdir -p %{buildroot}%{_sbindir}
install -m 755 %{SOURCE3} %{buildroot}%{_sbindir}/update-localtime
perl -pi -e 's|\@datadir\@|%{_datadir}|;' \
	 -e 's|\@sysconfdir\@|%{_sysconfdir}|' \
	%{buildroot}%{_sbindir}/update-localtime

%pretrans
# This is being replaced with a symlink to .
if [ ! -L %{_datadir}/zoneinfo/posix ]; then
  rm -rf %{_datadir}/zoneinfo/posix
fi

%posttrans -p %{_sbindir}/update-localtime

%files
%doc README
%doc Theory
%doc tz-link.html
%{_sbindir}/zdump
%{_sbindir}/zic
%{_sbindir}/update-localtime
%if %{with manpages}
%{_mandir}/man8/zdump.8*
%{_mandir}/man8/zic.8*
%endif
%dir %{_datadir}/zoneinfo
%{_datadir}/zoneinfo/*

%if %{with java}
%files java
%{_datadir}/javazi
%endif
