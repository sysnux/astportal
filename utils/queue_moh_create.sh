#! /bin/sh
# Create MOH class for Asterisk queue
# $1: Queue class dir (eg. /var/lib/asterisk/moh/astportal/queue_name)
# $2: MOH dir (eg. /var/lib/asterisk/moh/astportal)
# $3: Wav file

if [ ! -d $1 ] ; then 
   mkdir $1
fi

if [ ! -f $1/$3.wav ] ; then
   rm -f $1/* # Remove old file
   cp $2/$3.wav $1
fi

