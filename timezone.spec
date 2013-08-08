#define tzdata_version %{version}
%define tzdata_version 2013d
%define tzcode_version 2013d

# the zic(8) and zdump(8) manpages are already in man-pages
%bcond_with manpages
%bcond_without java

Summary:	Timezone data
Name:		timezone
Epoch:		1
Version:	2013d
Release:	1
License:	GPL
Group:		System/Base
Source0:	ftp://ftp.iana.org/tz/releases/tzdata%{tzdata_version}.tar.gz
Source1:	ftp://ftp.iana.org/tz/releases/tzcode%{tzcode_version}.tar.gz
Source2:	javazic.tar.gz
Source3:	update-localtime.sh
Patch0:		tzdata-mdvconfig.patch
Patch1:		tzdata-extra-tz-links.patch
Patch2:		javazic-fixup.patch
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

mv %{buildroot}%{_datadir}/zoneinfo-leaps %{buildroot}%{_datadir}/zoneinfo/right
mv %{buildroot}%{_datadir}/zoneinfo-posix %{buildroot}%{_datadir}/zoneinfo/posix

%if %{with java}
cp -a zoneinfo/java %{buildroot}%{_datadir}/javazi
%endif

# nuke unpackaged files
rm -f %{buildroot}%{_datadir}/zoneinfo/localtime
rm -rf %{buildroot}/usr/{lib,man}
rm -f %{buildroot}%{_sbindir}/tzselect

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

%posttrans
%{_sbindir}/update-localtime

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


%changelog
* Thu Nov 10 2011 Oden Eriksson <oeriksson@mandriva.com> 6:2011m-1.1
- built for updates

* Tue Nov 01 2011 Александр Казанцев <kazancas@mandriva.org> 6:2011m-1mdv2011.0
+ Revision: 709272
- Fiji adopts DST for 2011 (effective Oct 23rd, 2011)
- West Bank changes date for DST end in 2011 to Sep 30th
- Fix DST for:
    Pridnestrovian Moldavian Republic.
    Ukraine.
    Bahia, Brazil.
- fix source path to iana.org
- drop fixed in upstream patches

  + Alexander Barakin <abarakin@mandriva.org>
    - %post -p is not executed during installation (# 64446)

* Fri Oct 07 2011 Александр Казанцев <kazancas@mandriva.org> 6:2011k-1
+ Revision: 703457
- Proposed upstream 2011k (but not source, as ftp archive is dead):
- Belarus and Ukraine adopt permanent DST in 2011 - fix for 2011j
- Palestine suspends DST during Ramadan in 2011
- Gaza and West Bank split in 2011.  West Bank is tracked in the timezone Asia/Hebron.  zone.tab update accordingly.

* Thu Oct 06 2011 Александр Казанцев <kazancas@mandriva.org> 6:2011j-1
+ Revision: 703363
- tzdata 2011i, tzcode 2011j
- add patch for GB and China timezone
- fix droped "winter time" for Russia

  + Paulo Andrade <pcpa@mandriva.com.br>
    - Assume a working java on arm

* Sun May 01 2011 Funda Wang <fwang@mandriva.org> 6:2011g-1
+ Revision: 661156
- new version 2011g

* Thu Apr 21 2011 Funda Wang <fwang@mandriva.org> 6:2011f-1
+ Revision: 656373
- new version 2011f

* Wed Nov 03 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010o-1mdv2011.0
+ Revision: 592967
- Updated tzdata to 2010o release.

* Mon Oct 25 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010n-1mdv2011.0
+ Revision: 589280
- Updated tzcode/tzdata to 2010n release.

* Wed Oct 20 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010m-1mdv2011.0
+ Revision: 587025
- Updated tzcode/tzdata to 2010m release.

* Mon Aug 16 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010l-1mdv2011.0
+ Revision: 570643
- Updated tzcode/tzdata to 2010l release.

* Thu Aug 05 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010k-1mdv2011.0
+ Revision: 566062
- Updated tzcode/tzdata to 2010k release.

* Tue Apr 20 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010i-1mdv2010.1
+ Revision: 537099
- Updated tzdata to 2010i release.

* Mon Apr 05 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010h-1mdv2010.1
+ Revision: 531771
- Updated tzdata to 2010h release.

* Mon Mar 29 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010g-1mdv2010.1
+ Revision: 528808
- Updated tzdata to 2010g release.

* Thu Mar 25 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010f-1mdv2010.1
+ Revision: 527491
- Updated tzcode/tzdata to 2010f release.

* Wed Mar 10 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010e-1mdv2010.1
+ Revision: 517405
- Updated tzdata to 2010e release.

* Thu Mar 04 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010c-1mdv2010.1
+ Revision: 514317
- Updated tzcode/tzdata to 2010c release.

* Wed Feb 17 2010 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2010b-1mdv2010.1
+ Revision: 507212
- Updated tzcode to 2010a release.
- Updated tzdata to 2010b release.

* Fri Jan 15 2010 Anssi Hannula <anssi@mandriva.org> 6:2009u-2mdv2010.1
+ Revision: 491853
- default to UTC instead of US Eastern time when no timezone is set

* Mon Dec 28 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009u-1mdv2010.1
+ Revision: 483101
- Updated tzdata to 2009u release.

* Wed Dec 23 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009t-1mdv2010.1
+ Revision: 481877
- Updated tzcode/tzdata to 2009t release.

* Tue Nov 17 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009s-1mdv2010.1
+ Revision: 466966
- Updated tzdata to 2009s release.

* Mon Nov 09 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009r-1mdv2010.1
+ Revision: 463621
- Updated tzcode/tzdata to 2009r release.

* Mon Sep 28 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009n-1mdv2010.0
+ Revision: 450624
- Updated tzdata to 2009n release.

* Mon Sep 28 2009 Olivier Blin <blino@mandriva.org> 6:2009m-2mdv2010.0
+ Revision: 450397
- do not build java on arm & mips (from Arnaud Patard)

* Thu Sep 10 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009m-1mdv2010.0
+ Revision: 437224
- Updated tzdata to 2009m release.

* Mon Aug 17 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009l-1mdv2010.0
+ Revision: 417350
- Updated tzdata to 2009l release.

* Tue Jul 28 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009k-1mdv2010.0
+ Revision: 402530
- Updated tzcode/tzdata to 2009k release.

* Thu Jun 18 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009j-1mdv2010.0
+ Revision: 387182
- Updated tzdata to 2009j release.

* Fri Jun 12 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009i-1mdv2010.0
+ Revision: 385372
- Updated tzdata/tzcode to 2009i release.

* Tue May 26 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009h-1mdv2010.0
+ Revision: 379963
- Updated tzdata/tzcode to 2009h release.

* Wed May 06 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009g-1mdv2010.0
+ Revision: 372611
- Updated tzdata to 2009g release.

* Fri Apr 17 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009f-1mdv2009.1
+ Revision: 367824
- Updated tzdata to 2009f release.

* Mon Apr 06 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009e-1mdv2009.1
+ Revision: 364522
- Updated tzcode/tzdata to 2009e release.

* Mon Mar 16 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009c-1mdv2009.1
+ Revision: 355928
- Updated tzdata to 2009c release.

* Tue Feb 10 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009b-1mdv2009.1
+ Revision: 339137
- Updated tzcode/tzdata to 2009b release.

* Mon Jan 26 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009a-2mdv2009.1
+ Revision: 333708
- Restore original sysdep-CFLAGS setting in config.mk with optflags.

* Fri Jan 23 2009 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2009a-1mdv2009.1
+ Revision: 333118
- Updated tzcode/tzdata to 2009a
- Removed workaround for #41246, new tzcode has a fix for it.

* Tue Oct 28 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2008i-1mdv2009.1
+ Revision: 297924
- Updated tzdata to 2008i release.

* Tue Oct 14 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2008h-1mdv2009.1
+ Revision: 293757
- Updated tzcode/tzdata to 2008h release.
- Removed already applied tzdata-brazil-decree-6558.patch

* Thu Sep 18 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2008f-1mdv2009.0
+ Revision: 285579
- Updated tzdata to 2008f
- Use now fixed Brazil rule for daylight savings time (decree 6558),
  patch based on a previous one by Frederico A. C. Neves

* Mon Jul 28 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2008e-1mdv2009.0
+ Revision: 251783
- Updated tzcode/tzdata to 2008e release.

* Mon Jul 07 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2008d-1mdv2009.0
+ Revision: 232519
- tzdata update (2008d)
- Workaround gcc 4.3 bug, don't use -O2 optimization flag (#41246).
- Make sure we don't add blank lines to zone.tab to prevent bad parsers
  from crashing (also it isn't clear if blank lines is really allowed),
  as example see bug #41218.

* Wed May 28 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2008c-1mdv2009.0
+ Revision: 212165
- Rediffed tzdata-extra-tz-links patch.
- Added enhanced script to create zone.info entries for deprecated zone
  names (mdv bug #40184), contributed by Ken Pizzini.
- Updated to 2008c.

* Tue Apr 29 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2008b-2mdv2009.0
+ Revision: 199328
- Create zone.info entries for deprecated zone names (#40184).

* Wed Mar 26 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2008b-1mdv2008.1
+ Revision: 190201
- Updated to 2008b.

* Mon Mar 10 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2008a-1mdv2008.1
+ Revision: 183773
- Updated to 2008a.

* Thu Jan 10 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2007k-3mdv2008.1
+ Revision: 147456
- tzdata-base-0.tar.bz2: update tst-timezone.c with the one from
  glibc 2.7
- update-localtime.sh: make sure /etc/localtime has the right
  permissions after copy using install -m (#30045).

* Wed Jan 02 2008 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2007k-2mdv2008.1
+ Revision: 140418
- Updated to 2007k.
- Removed BuildRequires for java-devel-gcj, doesn't seems to be required
  when using java-rpmbuild.

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Sun Dec 16 2007 Anssi Hannula <anssi@mandriva.org> 6:2007j-2mdv2008.1
+ Revision: 121034
- buildrequire java-rpmbuild, i.e. build with icedtea on x86(_64)

* Thu Dec 06 2007 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2007j-1mdv2008.1
+ Revision: 115994
- Updated to 2007j.

* Mon Nov 05 2007 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2007i-1mdv2008.1
+ Revision: 106148
- Updated to 2007i.
- More cleanups of uneeded spec code and minor define fix.
- Don't place comment inside post -p.

* Fri Oct 12 2007 David Walluck <walluck@mandriva.org> 6:2007h-2mdv2008.1
+ Revision: 97801
- add java sources
- readd java support (this does not force java on the main package)
- Provides: tzdata = %%{version}-%%{release} for Fedora compat
- add Java support (from Fedora) and Provides: tzdata-java = %%{version}-%%{release}

  + Herton Ronaldo Krzesinski <herton@mandriva.com.br>
    - Revert previous change, timezone java stuff now has a new entry on
      svn, named timezone-java.

* Mon Oct 01 2007 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2007h-1mdv2008.0
+ Revision: 94275
- Updated to 2007h.
- Removed already applied 2007-2008 Brazil tzdata update.

* Fri Sep 21 2007 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2007g-2mdv2008.0
+ Revision: 91947
- Updated daylight savings time definitions for Brazil (2007/2008). As
  always they keep changing this every year...

* Mon Sep 17 2007 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2007g-1mdv2008.0
+ Revision: 89289
- Updated to 2007g.
- Rediff tzdata-extra-tz-links patch.

* Wed Aug 08 2007 Herton Ronaldo Krzesinski <herton@mandriva.com.br> 6:2007f-2mdv2008.0
+ Revision: 60013
- Cleanup: remove tzdata-tzcode2006a.patch, not needed anymore.

* Wed Jul 18 2007 Tomasz Pawel Gajc <tpg@mandriva.org> 6:2007f-1mdv2008.0
+ Revision: 53155
- spec file clean
- new version
- rediff patch1


* Wed Mar 14 2007 Gwenole Beauchesne <gbeauchesne@mandriva.com> 2007c-2mdv2007.1
+ Revision: 143844
- fix triggers

* Wed Mar 07 2007 Gwenole Beauchesne <gbeauchesne@mandriva.com> 6:2007c-1mdv2007.1
+ Revision: 134361
- use upstream tz{data,code} 2007c

* Wed Mar 07 2007 Gwenole Beauchesne <gbeauchesne@mandriva.com> 2007c-1mdv
- use upstream tz{data,code} 2007c

