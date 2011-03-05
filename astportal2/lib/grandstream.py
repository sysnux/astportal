# -*- coding: utf-8 -*-

import logging
log = logging.getLogger(__name__)
from time import time, sleep
from os import system, popen #, rename
import cookielib, urllib, urllib2
from BeautifulSoup import BeautifulSoup
from struct import pack, unpack

class Grandstream:

   cj = cookielib.CookieJar()
   opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
   params = dict(
# Admin password for web interface
P2 = 'admin',
# No Key Entry Timeout. Default - 4 seconds.
P85 = 3,
# Use # as Dial Key. 0 - no, 1 - yes
P72 = 1,
# Local RTP port (1024-65535, default 5004)
P39 = 5004,
# Use Random Port. 0 - no, 1 - yes
P78 = 0,
# Keep-alive interval (in seconds. default 20 seconds)
P84 = 20,
# Firmware Upgrade. 0 - TFTP Upgrade,  1 - HTTP Upgrade.
P212 = 0,
# Firmware Server Path
P192 = '',
# Config Server Path
P237 = '',
# Firmware File Prefix
P232 = '',
# Firmware File Postfix
P233 = '',
# Config File Prefix
P234 = 'gs-',
# Config File Postfix
P235 = '.cfg',
# Automatic Upgrade. 0 - No, 1 - Yes. Default is No.
P194 = 1,
# Check for new firmware every () minutes, unit is in minute, minimnu 60 minutes, default is 7 days.
P193 = 1440,
# Use firmware pre/postfix to determine if f/w is required
# 0 = Always Check for New Firmware 
# 1 = Check New Firmware only when F/W pre/suffix changes
# 2 = Always Skip the Firmware Check
P238 = 0,
# Authenticate Conf File. 0 - No, 1 - Yes. Default is No.
P240 = 0,
#----------------------------------------
# XML Phonebook
#----------------------------------------
# Enable Phonebook XML Download
# 0 = No
# 1 = YES, HTTP
# 2 = YES, TFTP
P330 = 1,

# Phonebook XML Server Path
# This is a string of up to 128 characters that should contain a path to the XML file.  
# It MUST be in the host/path format. For example: "directory.grandstream.com/engineering"
P331 = '',
# Phonebook Download Interval
# This is an integer variable in hours.  
# Valid value range is 0-720 (default 0), and greater values will default to 720
P332 = 1,
# Remove Manually-edited entries on Download
# 0 - No, 1 - Yes, other values ignored
P333 = 0,
# Syslog Server (name of the server, max length is 64 charactors)
P207 = '',
# Syslog Level (Default setting is NONE)
# 0 - NONE, 1 - DEBUG, 2 - INFO, 3 - WARNING, 4 - ERROR
P208 = 3,
# NTP Server
P30 = '',
# Display Language. 0 - English, 3 - Secondary Language, 2 - Chinese
P342 = 3,
# language file postfix
P399 = 'french',
)

   def __init__(self, host, mac, pwd='admin'):
      self.host = host
      self.mac = mac
      self.pwd = pwd
      self.type = 0
      self.url = 'http://%s/' % host

   def get(self, action, params=None):
      if params:
         params = urllib.urlencode(params)
         params += '&gnkey=0b82' # Seems it *must* be last parameter, or update fails
      req = urllib2.Request(self.url + action, params)
      try:
         resp = self.opener.open(req)
      except:
         return None
      return resp

   def login(self, pwd=None):
      if pwd:
         self.pwd = pwd
      # Login
      logged_in = False
      if self.get('dologin.htm', {'P2': self.pwd}) == None:
         log.debug('Login error, GXP-2xxx?')
         if self.get('/cgi-bin/dologin', \
               {'P2': self.pwd}) != None:
            # GXP-2100
            for c in self.cj:
               log.debug('Cookie: %s = %s' % (c.name, c.value))
               if c.name=='session_id':
                  logged_in = True
                  self.type = 2
      else:
         for c in self.cj:
            log.debug('Cookie: %s = %s' % (c.name, c.value))
            if c.name=='SessionId':
               logged_in = True
               self.type = 1
      if not logged_in:
         log.warning('Login failed (check password? %s)', pwd)
         return False
      return True

   def infos(self):
      resp = self.get('index.htm')

      buffer = ''
      for l in resp.readlines():
         buffer += unicode(l,'ISO-8859-1')
      html = BeautifulSoup(buffer)
      try:
         tables = html.findAll('table')
         tr = tables[-1].findAll('tr')
         td = tr[2].findAll('td')
         model = td[1].contents[0].replace('&nbsp; ','')
         td = tr[4].findAll('td')
         soft = td[1].contents[0].replace('&nbsp; ','')
         soft = soft.replace('&nbsp;','')
      except:
         return None
      return {'model': model.strip(), 'version': soft.strip()}

   def update(self, params):
      log.debug('Update...')
      resp = self.get('update.htm',params)
      log.debug('Update -> %s', resp.msg)
      return resp.msg

   def reboot(self):
      # Reboot
      log.debug('Reboot...')
      t1 = time()
      resp = self.get('rs.htm')

      # While rebooting, phone is reachable, then unreachable, then reachable again
      reachable = True
      for wait in xrange(60):
         try:
            resp = urllib2.urlopen(self.url, timeout=1)
            if not reachable: break
         except:
            reachable = False
         sleep(1)
      t2 = time()
      log.debug('Reboot done in %.1f seconds !' % (t2-t1))
      return resp.msg

   def configure(self, pwd, tftp_dir, firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None, dns1=None, dns2=None,
         sip_server=None, sip_user=None, sip_display_name=None,
         mwi_subscribe=False):
      '''Parameters: firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None
      '''

      self.params['P2'] = pwd
      self.params['P192'] = firmware_url
      self.params['P237'] = config_url
      self.params['P331'] = phonebook_url
      self.params['P30'] = ntp_server
      self.params['P64'] = 120
      self.params['P207'] = syslog_server
      self.params['P207'] = syslog_server
      if dns1:
         (self.params['P21'], self.params['P22'], self.params['P23'],
            self.params['P24']) = dns1.split('.')
      if dns2:
         (self.params['P25'], self.params['P26'], self.params['P27'],
            self.params['P28']) = dns2.split('.')

      self.params['P270'] = 'Asterisk'
      self.params['P99'] = 1 if mwi_subscribe else 0
      if sip_server:
         self.params['P47'] = sip_server
         self.params['P35'] = sip_user
         self.params['P34'] = pwd
         self.params['P3'] = sip_display_name
         self.params['P271'] = \
         self.params['P31'] = \
         self.params['P81'] = \
         self.params['P1346'] = \
         self.params['P188'] = \
            1
      else:
         self.params['P47'] = \
         self.params['P35'] = \
         self.params['P34'] = \
         self.params['P3'] = \
            ''
         self.params['P271'] = \
         self.params['P31'] = \
         self.params['P81'] = \
         self.params['P1346'] = \
         self.params['P188'] = \
            0
      self.params['P48'] = ''
      self.params['P78'] = ''
      self.params['P52'] = \
      self.params['P29'] = \
      self.params['P182'] = \
      self.params['P58'] = \
         0
      self.params['P33'] = '*79'
      self.params['P73'] = 1
      self.params['P1347'] = '**'
      self.params['P57'] = 8

      # Generate conf files (text and binary)
      name = tftp_dir + '/phones/config/gs-cfg%s' % self.mac.replace(':','')
      try:
         txt = open(name + '.txt', 'w')
         for k in self.params.keys():
            txt.write('%s=%s\n' % (k, self.params[k]))
         txt.close()
      except:
         log.debug('ERROR: write text config file')

      bin = self.encode()

      try:
         cfg2 = open(name + '.cfg', 'w')
         for x in bin:
            cfg2.write(chr(x))
         cfg2.close()
      except:
         log.debug('ERROR: write binary config file')

      # Update and reboot phone
      self.update(self.params)
      self.reboot()

   def encode(self):
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
      cfg[6:12] = [int(h,16) for h in self.mac.split(':')]
      params = urllib.urlencode(self.params)
      params += '&gnkey=0b82' # Seems it must be the *last* parameter, or update fails
      if len(params) % 2:
         params += chr(0) # Padding
      cfg[16:] = params
      cfg[2] = (len(cfg) / 2) / 256
      cfg[3] = (len(cfg) / 2) % 256
      cfg[4:6] = self.checksum(cfg)
      return cfg

   def checksum(self, bytes):
      '''16 bit checksum of bytearray
      '''
      sum = 0
      for i in xrange(0, len(bytes), 2):
         sum += (bytes[i] << 8) + bytes[i+1]
         sum &= 0xFFFF
      sum = 0x10000 - sum
      return (sum >> 8, sum & 0xFF)

