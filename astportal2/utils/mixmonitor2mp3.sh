#! /bin/bash
#
# Script de conversion de fichier WAV en MP3, et effacement du fichier WAV
# 
# Paramètre: nom complet du fichier WAV à convertir
#
# Utile pour Asterisk / MixMonitor, par exemple:
# exten => _XXXX,n,MixMonitor(${date:0:4}/${date:4:2}/${date:6:2}/out-${CHANNEL:4:6}-${EXTEN}-${CDR(uniqueid)}.wav,,/usr/lib/asterisk/mixmonitor2mp3.sh ^{MIXMONITOR_FILENAME})
#
# Author: Jean-Denis Girard <jd.girard@sysnux.pf>

/bin/nice -n 20 /usr/bin/lame $1 $(dirname $1)/$(basename $1 .wav).mp3
#/bin/rm -f $1

