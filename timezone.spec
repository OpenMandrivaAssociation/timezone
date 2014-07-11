%define tzdata_version 2014d
%define tzcode_version 2014d

# the zic(8) and zdump(8) manpages are already in man-pages
%define build_manpages 0
%ifarch %mips
%define build_java 0
%else
%define build_java 1
%endif

Summary:	Timezone data
Name:		timezone
Epoch:		7
Version:	2014e
Release:	2
License:	GPL
Group:		System/Base
Source0:	ftp://ftp.iana.org/tz/releases/tzdata%{tzdata_version}.tar.gz
Source1:	ftp://ftp.iana.org/tz/releases/tzcode%{tzcode_version}.tar.gz
Source2:	javazic.tar.gz
Source3:	update-localtime.sh
Patch1:		tzdata-extra-tz-links.patch
Patch2:		javazic-fixup.patch
Patch3:         javazic-exclusion-fix.patch
Provides:	tzdata = %{version}-%{release}
Requires(pre):	coreutils
Requires(pre):	util-linux
Conflicts:     %{name} < 6:2013f-1
BuildRequires:	gawk
BuildRequires:	perl

%description
This package contains data files with rules for various timezones
around the world.

%if %{build_java}
%package java
Summary:	Timezone data for Java
Group:		System/Base
Provides:	tzdata-java = %{version}-%{release}
BuildRequires:	java-rpmbuild
BuildRequires:  java-devel
BuildRequires:	javapackages-tools

%description java
This package contains timezone information for use by Java runtimes.
%endif

%prep
%setup -q -c -a 1
%patch1 -p1 -b .extra-tz-links

%if %{build_java}
mkdir javazic
tar xf %{SOURCE2} -C javazic
pushd javazic
%patch2 -p0 -b .javazic-fixup
%patch3
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

%build

%make TZDIR=%{_datadir}/zoneinfo CFLAGS="%{optflags} -std=gnu99"

grep -v tz-art.htm tz-link.htm > tz-link.html

%if %{build_java}
pushd javazic
%{javac} -source 1.5 -target 1.5 -classpath . `find . -name \*.java`
popd
%{java} -classpath javazic/ rht.tools.javazic.Main -V %{version} \
  -d zoneinfo/java \
  africa antarctica asia australasia europe northamerica pacificnew \
  southamerica backward etcetera systemv \
  javazic/tzdata_jdk/gmt javazic/tzdata_jdk/jdk11_backward
%endif

%install
make TOPDIR=%{buildroot}/usr \
     TZDIR=%{buildroot}%{_datadir}/zoneinfo \
     ETCDIR=%{buildroot}%{_sbindir} \
     install
rm -f %{buildroot}%{_datadir}/zoneinfo-posix
ln -s . %{buildroot}%{_datadir}/zoneinfo/posix
mv %{buildroot}%{_datadir}/zoneinfo-leaps %{buildroot}%{_datadir}/zoneinfo/right

# nuke unpackaged files
rm -f %{buildroot}%{_datadir}/zoneinfo/localtime
rm -f %{buildroot}%{_sbindir}/tzselect
rm -rf %{buildroot}/usr/{lib,man}

%if %{build_java}
cp -a zoneinfo/java %{buildroot}%{_datadir}/javazi
%endif

# install man pages
%if %{build_manpages}
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

%post -p %{_sbindir}/update-localtime

%pre
if [ -e %{_datadir}/zoneinfo/posix -a ! -L %{_datadir}/zoneinfo/posix ]; then
  rm -rf %{_datadir}/zoneinfo/posix
fi

%files
%doc README
%doc Theory
%doc tz-link.html
%{_sbindir}/zdump
%{_sbindir}/zic
%{_sbindir}/update-localtime
%if %{build_manpages}
%{_mandir}/man8/zdump.8*
%{_mandir}/man8/zic.8*
%endif
%dir %{_datadir}/zoneinfo
%{_datadir}/zoneinfo/*

%if %{build_java}
%files java
%{_datadir}/javazi
%endif
