%define tzdata_version %{version}
%define tzcode_version %{version}
%bcond_with bootstrap

# the zic(8) and zdump(8) manpages are already in man-pages
%define build_manpages 0
%ifarch %{mipsx} riscv64
%define build_java 0
%else
%define build_java 1
%endif

Summary:	Time Zone Database
Name:		timezone
Epoch:		8
Version:	2021a
Release:	1
License:	GPL
Group:		System/Base
URL:		http://www.iana.org/time-zones
Source0:	ftp://ftp.iana.org/tz/releases/tzdata%{tzdata_version}.tar.gz
Source1:	ftp://ftp.iana.org/tz/releases/tzcode%{tzcode_version}.tar.gz
Source2:	javazic.tar.gz
Patch1:		tzdata-extra-tz-links.patch
Patch2:		javazic-fixup.patch
Patch3:		javazic-exclusion-fix.patch
%if %{with bootstrap}
Provides:	tzdata-java = %{version}-%{release}
%endif
Provides:	tzdata = %{version}-%{release}
Conflicts:	%{name} < 6:2013f-1
BuildRequires:	gawk
BuildRequires:	perl
Provides:	tzdata = %{EVRD}
Provides:	tzcode = %{EVRD}

%description
This package contains data files with rules for various timezones
around the world.

%if %{build_java}
%package java
Summary:	Timezone data for Java
Group:		System/Base
Provides:	tzdata-java = %{version}-%{release}
BuildRequires:	java-devel
BuildRequires:	java-rpmbuild
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
cd javazic
%patch2 -p0 -b .javazic-fixup
%patch3
# Hack alert! sun.tools may be defined and installed in the
# VM. In order to guarantee that we are using IcedTea/OpenJDK
# for creating the zoneinfo files, rebase all the packages
# from "sun." to "rht.". Unfortunately, gcj does not support
# any of the -Xclasspath options, so we must go this route
# to ensure the greatest compatibility.
mv sun rht
for f in $(find . -name '*.java'); do
    sed -i -e 's:sun\.tools\.:rht.tools.:g'\
	-e 's:sun\.util\.:rht.util.:g' $f
done
cd -

# Create zone.info entries for deprecated zone names (#40184)
    chmod +w zone.tab
        printf '%s\n' '# zone info for backward zone names' > zone.tab.new
        while read link cur old x; do
            case $link-${cur+cur}-${old+old}${x:+X} in
                Link-cur-old)
                    awk -v cur="$cur" -v old="$old" \
                            '!/^#/ && $3 == cur { sub(cur,old); print }' \
                                zone.tab || printf '%s\n' 'ERROR' ;;
                    Link-*)
                        printf '%s\n' 'Error processing backward entry for zone.tab'
                        exit 1 ;;
            esac
        done < backward >> zone.tab.new
        if grep -q '^ERROR' zone.tab.new || ! cat zone.tab.new >> zone.tab; then
            printf '%s\n' "Error adding backward entries to zone.tab"
            exit 1
        fi
        rm -f zone.tab.new
%endif

%build
# (tpg) fix build
sed -i -e "s/$(AR) -rc/$(AR) r/g" Makefile*

%make_build TZDIR=%{_datadir}/zoneinfo CFLAGS="%{optflags} -std=gnu99" CC=%{__cc}

%if %{build_java}
cd javazic
%{javac} -source 8 -target 8 -classpath . $(find . -name \*.java)
cd -
%{java} -classpath javazic/ rht.tools.javazic.Main -V %{version} \
  -d zoneinfo/java \
  africa antarctica asia australasia europe northamerica \
  southamerica backward etcetera \
  javazic/tzdata_jdk/gmt javazic/tzdata_jdk/jdk11_backward
%endif

%install
make TOPDIR=%{buildroot} \
     TZDIR=%{buildroot}%{_datadir}/zoneinfo \
     ETCDIR=%{buildroot}%{_sbindir} \
     install

rm -f %{buildroot}%{_datadir}/zoneinfo-posix
ln -s . %{buildroot}%{_datadir}/zoneinfo/posix
mv %{buildroot}%{_datadir}/zoneinfo-leaps %{buildroot}%{_datadir}/zoneinfo/right
mv %{buildroot}%{_bindir}/zdump %{buildroot}%{_sbindir}/zdump

# nuke unpackaged files
rm -f %{buildroot}%{_datadir}/zoneinfo/localtime
rm -f %{buildroot}%{_bindir}/tzselect
rm -f %{buildroot}%{_sysconfdir}/localtime
rm -rf %{buildroot}/usr/{lib,man}

%if !%{build_manpages}
rm -rf %{buildroot}%{_mandir}
%endif

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

%pretrans -p <lua>
-- (tpg) remove this regular file as it needs to be a symlink
zone_file = "/usr/share/zoneinfo/posix"
st = posix.stat(zone_file)

if st and st.type == "regular" then
    os.remove(zone_file)
end

%files
%doc README
%doc theory.html
%doc tz-art.html tz-link.html
%{_sbindir}/zdump
%{_sbindir}/zic
%if %{build_manpages}
%{_mandir}/man3/*
%{_mandir}/man5/*
%{_mandir}/man8/*
%endif
%dir %{_datadir}/zoneinfo
%{_datadir}/zoneinfo/*

%if %{build_java}
%files java
%{_datadir}/javazi
%endif
