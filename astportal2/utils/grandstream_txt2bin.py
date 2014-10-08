#! /opt/tg22env/bin/python
# -*- coding: utf-8 -*-

from sys import argv, stderr, exit
import urllib
import re
re_mac = re.compile('cfg000[bB]82([a-fA-F0-9]{2})([a-fA-F0-9]{2})([a-fA-F0-9]{2})\.txt')

def encode(params, mac):
      '''Create a configuration file suitable for phone

From http://www.voip-info.org/wiki/view/Grandstream+Configuration+Tool
The parameters are strung together without whitespace, ie:
"P30=time.nist.gov&P63=1&P31=1"

A "key" parameter ("&gnkey=0b82") is then added to the parameter string. ie:
"P30=time.nist.gov&P63=1&P31=1&gnkey=0b82"

If the length of this parameter string is not even, a zero byte is added 
to the string,

A 16 byte "header" that is prepended to the resulting configuration string.

The header consists of:
Byte 0x00: 0x00
Byte 0x01: 0x00
Byte 0x02: high byte of (length of parameter string) divided by 2
Byte 0x03: low byte of (length of parameter string) divided by 2
Byte 0x04: 0x00 (replaced by high byte of checksum)
Byte 0x05: 0x00 (replaced by low bytes of checksum)
Byte 0x06: first byte of device MAC address
Byte 0x07: second byte of device MAC address
Byte 0x08: third byte of device MAC address
Byte 0x09: fourth byte of device MAC address
Byte 0x0A: fifth byte of device MAC address
Byte 0x0B: sixth byte of device MAC address
Byte 0x0C: carriage return ( 0x0C )
Byte 0x0D: line feed (0x0A)
Byte 0x0E: carriage return ( 0x0C )
Byte 0x0F: line feed (0x0A)

This results in a configuration string of:
16 bytes header + (configuration parameters) + (&gnkey=0b82) + (Padding byte 
if length is not even)

You then compute a 16 bit checksum (initial value 0x0000 - adding the value 
of each individual byte) of the entire confguration string. This value is 
the subtracted from 0x10000 and placed in bytes 4 and 5 of the header, then 
the header and parameter strings are written to a binary file.
'''
 
      cfg = bytearray((0,0,0,0,0,0,0,0,0,0,0,0,13,10,13,10)) # Header
      cfg[6:12] = [int(h,16) for h in mac]
      params = urllib.urlencode(params)
      params += '&gnkey=0b82' # Seems it must be the *last* parameter, or update fails
      if len(params) % 2:
         params += chr(0) # Padding
      cfg[16:] = params
      cfg[2] = (len(cfg) / 2) / 256
      cfg[3] = (len(cfg) / 2) % 256
      cfg[4:6] = checksum(cfg)
      return cfg

def checksum(bytes):
      '''16 bit checksum of bytearray
      '''
      sum = 0
      for i in xrange(0, len(bytes), 2):
         sum += (bytes[i] << 8) + bytes[i+1]
         sum &= 0xFFFF
      sum = 0x10000 - sum
      return (sum >> 8, sum & 0xFF)

try:
   ftxt = argv[1]
   mac = re_mac.search(ftxt).groups()
except:
   stderr.write(
'''Usage: %s fichier_configuration_texte adresse_MAC\n
Nom de fichier au format cfg000b82012345.txt,
avec 00:0b:82:01:23:45 adresse MAC du telephone
''' % argv[0])
   exit(1)

try:
   txt = open(ftxt)
except:
   stderr.write('Erreur: lecture fichier texte %s\n' % ftxt)
   exit(2)

try:
   bin = open(ftxt[:-4], 'w')
except:
   stderr.write('Erreur: ecriture fichier binaire %s\n' % ftxt[:-4])
   exit(2)

params = dict()
lines = txt.readlines()
for l in lines:
   k, v = l[:-1].split('=')
   params[k] = v

txt.close()

cfg = encode(params, ['00', '0b', '82'] + list(mac))
bin.write(cfg)
bin.close()

