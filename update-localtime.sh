#!/bin/sh

zonedir=@datadir@/zoneinfo
localtime_file=@sysconfdir@/localtime
clock_file=@sysconfdir@/sysconfig/clock

unset ZONE
if [ -f $clock_file ]; then
	. $clock_file
fi

if [ -z "$ZONE" ]; then
	ZONE=UTC
fi

if [ -f $zonedir/$ZONE ]; then
	install -m 0644 $zonedir/$ZONE $localtime_file
fi
