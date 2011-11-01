%define name	timezone
%define epoch	6
%define version	2011m
%define release	%mkrel 1

#define tzdata_version %{version}
%define tzdata_version 2011m
%define tzcode_version 2011i

# the zic(8) and zdump(8) manpages are already in man-pages
%define build_manpages 0
%ifarch %mips
%define build_java 0
%else
%define build_java 1
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
Source1:	ftp://ftp.iana.org/tz/releases/tzdata%{tzdata_version}.tar.gz
Source2:	ftp://ftp.iana.org/tz/releases/tzcode%{tzcode_version}.tar.gz
Source3:	javazic.tar.gz
Source4:	update-localtime.sh
Patch0:		tzdata-mdvconfig.patch
Patch1:		tzdata-extra-tz-links.patch
Patch2:		javazic-fixup.patch
Provides:	tzdata = %{version}-%{release}
BuildRequires:	gawk, perl
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root

%description
This package contains data files with rules for various timezones
around the world.

%if %{build_java}
%package java
Summary:	Timezone data for Java
Group:		System/Base
Provides:	tzdata-java = %{version}-%{release}
BuildRequires:	java-rpmbuild

%description java
This package contains timezone information for use by Java runtimes.
%endif

%prep
%setup -q -n tzdata
mkdir tzdata%{tzdata_version}
tar xzf %{SOURCE1} -C tzdata%{tzdata_version}
mkdir tzcode%{tzcode_version}
tar xzf %{SOURCE2} -C tzcode%{tzcode_version}

%patch0 -p1 -b .mdvconfig
pushd tzdata%{tzdata_version}
%patch1 -p2 -b .extra-tz-links
popd

ln -s Makeconfig.in Makeconfig
cat > config.mk << EOF
objpfx = `pwd`/obj/
sbindir = %{_sbindir}
datadir = %{_datadir}
install_root = %{buildroot}
sysdep-CFLAGS = %{optflags}
EOF

%if %{build_java}
mkdir javazic
tar xf %{SOURCE3} -C javazic
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
pushd tzdata%{tzdata_version}
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
popd
%endif

%build
%make
grep -v tz-art.htm tzcode%{tzcode_version}/tz-link.htm > tzcode%{tzcode_version}/tz-link.html

%if %{build_java}
pushd javazic
%{javac} -source 1.5 -target 1.5 -classpath . `find . -name \*.java`
popd
pushd tzdata%{tzdata_version}
%{java} -classpath ../javazic/ rht.tools.javazic.Main -V %{version} \
  -d ../zoneinfo/java \
  africa antarctica asia australasia europe northamerica pacificnew \
  southamerica backward etcetera solar87 solar88 solar89 systemv \
  ../javazic/tzdata_jdk/gmt ../javazic/tzdata_jdk/jdk11_backward
popd
%endif

%install
rm -rf %{buildroot}

make install

%if %{build_java}
cp -a zoneinfo/java $RPM_BUILD_ROOT%{_datadir}/javazi
%endif

# nuke unpackaged files
rm -f %{buildroot}%{_sysconfdir}/localtime

# install man pages
%if %{build_manpages}
mkdir -p %{buildroot}%{_mandir}/man8
for f in zic zdump; do
install -m 644 tzcode*/$f.8 %{buildroot}%{_mandir}/man8/
done
%endif

# install update-localtime script
mkdir -p %{buildroot}%{_sbindir}
install -m 755 %{SOURCE4} %{buildroot}%{_sbindir}/update-localtime
perl -pi -e 's|\@datadir\@|%{_datadir}|;' \
	 -e 's|\@sysconfdir\@|%{_sysconfdir}|' \
	%{buildroot}%{_sbindir}/update-localtime

%check
echo ====================TESTING=========================
make check
echo ====================TESTING END=====================

# XXX next glibc updates are expected to remove /etc/localtime
%triggerpostun -- glibc < 6:2.4-8mdv2007.1
if [ ! -f %{_sysconfdir}/localtime ]; then
  %{_sbindir}/update-localtime
fi

%post
%{_sbindir}/update-localtime

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

%if %{build_java}
%files java
%defattr(-,root,root)
%{_datadir}/javazi
%endif
