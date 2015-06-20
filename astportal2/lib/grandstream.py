# -*- coding: utf-8 -*-

import logging
log = logging.getLogger(__name__)
from time import time, sleep
from os import system, popen #, rename
import cookielib, urllib, urllib2, json
from BeautifulSoup import BeautifulSoup
from struct import pack, unpack
import os

from tg import config
default_company = config.get('company')

class Grandstream(object):

   cj = cookielib.CookieJar()
   opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
   params = dict(
# Admin password for web interface
P2 = 'admin',
# VLAN TAG
#P51 = 1601,

# No Key Entry Timeout. Default - 4 seconds.
P85 = 2,
# Use # as Dial Key. 0 - no, 1 - yes
P72 = 1,
# Local RTP port (1024-65535, default 5004)
P39 = 5004,
# Use Random Port. 0 - no, 1 - yes
P78 = 0,
# Keep-alive interval (in seconds. default 20 seconds)
P84 = 20,
#Use RFC3581 Symmetric Routing
P131 = 1,
# Account 1 Ring Tone: 0=system ring tone, N=custom ring tone N
P104 = 1,
# Firmware Upgrade. 0 - TFTP Upgrade,  1 - HTTP Upgrade,  2 - HTTPS Upgrade.
P212 = 2,
# Firmware Server Path
P192 = '',
# Config Server Path
P237 = '',
# Firmware File Prefix
P232 = '',
# Firmware File Postfix
P233 = '',
# Config File Prefix
P234 = '',
# Config File Postfix
P235 = '',
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
# 3 = YES, HTTPS
P330 = 3,

# Phonebook XML Server Path
# This is a string of up to 128 characters that should contain a path to the XML file.  
# It MUST be in the host/path format. For example: "directory.grandstream.com/engineering"
P331 = '',
# Phonebook Download Interval
# This is an integer variable in hours.  
# Valid value range is 5-720 (default 0), and greater values will default to 720
P332 = 10,
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
# LCD Backlight Brightness. (0-8, where 0 is off and 8 is brightest) Active
#P334 = 100, # GXP21xx
P334 = 8,
# LCD Backlight Brightness. (0-8, where 0 is off and 8 is brightest) Idle
#P335 = 50, # GXP21xx
P335 = 0,
# Configuration Via Keypad Menu. 0 - Unrestricted, 1 - Basic settings only, 2 - Constrai nt mode
P1357 = 0,
# Idle Screen XML Download HTTPS
P340=3,
# Idle Screen XML Server Path
# P341=172.20.6.1/grandstream/screen,
# Download Screen XML at Boot-up Yes
P1349=1,
# Web Access Mode. 0 - HTTPS, 1 - HTTP. Default is 1
P1650 = 0,
# Enable Call Features.  0 - No, 1 - Yes. Default is 1
P191 = 0,
# Off-hook Auto Dial
#P71
# Disable SSH. 0 - No, 1 - Yes. Default is 0
P276 = 1,
# Dial Plan 0 - Disabled, 1 Enabled
P2382 = 0,
)


   def __init__(self, host, mac, pwd='admin'):
      self.vendor = 'Grandstream'
      self.model = None
      self.host = host
      self.mac = mac
      self.pwd = pwd
      self.type = 0
      self.sid = None
      self.url = 'http://%s/' % host

   def get(self, action, params=None):
      if params:
         params = urllib.urlencode(params)
      if self.type in (0, 1, 2) and params is not None:
         params += '&gnkey=0b82' # Seems it *must* be last parameter, or update fails
      elif self.sid is not None:
         params += '&sid=' + self.sid
      for c in self.cj:
         log.debug('Cookie: %s = %s' % (c.name, c.value))
      req = urllib2.Request(self.url + action, params)
      try:
         resp = self.opener.open(req)
         log.debug('Request %s, params %s returns %s (%s)' % (\
               self.url + action, params, resp.msg, resp.code))
      except:
         log.warning('Request %s, params %s failed' % (\
               self.url + action, params))
         return None
      return resp

   def login(self, pwd=None):
      if pwd:
         self.pwd = pwd
      # Login
      logged_in = False
      if self.get('dologin.htm', {'P2': self.pwd}) == None:
         log.debug('Login error, GXP-2xxx?')
         if self.get('cgi-bin/dologin', {'P2': self.pwd}) != None:
            # GXP-2100
            for c in self.cj:
               log.debug('Cookie: %s = %s' % (c.name, c.value))
               if c.name=='session_id':
                  log.debug('Logged in GXP2xxx, old firmware')
                  logged_in = True
                  self.type = 2
            if not logged_in:
               resp = self.get('cgi-bin/dologin', {'password': self.pwd})
               if resp != None:
                  r = resp.readline()
                  log.debug('GXP new firmware returns %s' % r)
                  try:
                     data = json.loads(r)
                     if data['response'] == 'success':
                        self.sid = data['body']['sid']
                        logged_in = True
                        self.type = 3
                        log.debug('Logged in GXP2xxx, new firmware')
                  except:
                     log.error('new firmware does not return JSON ?')
                     pass
         else:
            log.warning('GXP-2xxx login failed!')
      else:
         for c in self.cj:
            log.debug('Cookie: %s = %s' % (c.name, c.value))
            if c.name=='SessionId':
               log.debug('Logged in GXP1xxx')
               logged_in = True
               self.type = 1
      if not logged_in:
         log.warning('Login failed (check password? %s)', pwd)
         return False
      
      log.debug('GXP login ok!')
      return True

   def infos(self):

      if self.type == 1: # Old GXP
         resp = self.get('index.htm')
         buffer = ''
         if resp is None:
            log.error('infos failed, no data')
            return None
         for l in resp.readlines():
            buffer += unicode(l,'ISO-8859-1')
         html = BeautifulSoup(buffer)
         try:
            content = html('table')[-1]
            model = ((content('tr')[2])('td')[1]).text.replace('&nbsp; ','').strip()
            soft = ((content('tr')[4])('td')[1]).text.replace('&nbsp; ','').strip()
         except:
            log.error('infos failed, html=----\n%s\n----' % html)
            return None

      elif self.type == 2: # GXP-14XX 21XX
         resp = self.get('cgi-bin/index')
         buffer = ''
         for l in resp.readlines():
            buffer += unicode(l,'UTF-8')
         html = BeautifulSoup(buffer)
         content = model = soft = ''
         try:
            content = html('table')[2]
            model = (content('tr')[3])('td')[1].text.strip()
            soft = (content('tr')[9])('td')[1].text.strip()
         except:
            pass
         if model == '' or soft == '':
            try:
               # Since 1.0.4.23 at least
               content = html('table')[2]
               model = (content('tr')[5])('td')[1].text.strip()
               soft = (content('tr')[11])('td')[1].text.strip()
            except:
               pass
         if (model == '' or soft == '') \
               and 'DP715' in (html('table')[1])('tr')[3].text:
            model = 'DP715'
            soft = (html('table')[1])('tr')[3].text.split('\n')[8].strip()
         if (model == '' or soft == '') \
               and 'HT701' in (html('table')[1])('tr')[3].text:
            model = 'HT701'
            soft = (html('table')[1])('tr')[3].text.split('\n')[7].strip()
         if model == '' or soft == '':
            log.error('GXP type 2 not recognized, html=\n%s\n' % (html))
            return None

      elif self.type == 3: # GXP-14XX 21XX new firmware
         resp = self.get('cgi-bin/api.values.get', {'request': 'phone_model:68'})
         data = json.loads(resp.readlines()[-1])
         model = data['body']['phone_model']
         soft = data['body']['68']

      self.model = model

      log.debug(u'Model <%s>'% model)
      log.debug(u'Version <%s>'% soft)

      if model.startswith('GXP21'):
         self.params['P334'] = 100
         self.params['P335'] = 50

      return {'model': model.strip(), 'version': soft.strip()}

   def update(self, params):
      log.debug('Update (type %d)...' % self.type)
      if self.type == 1:
         resp = self.get('update.htm', params)
      elif self.type == 2:
         resp = self.get('cgi-bin/update', params)
      elif self.type == 3:
         resp = self.get('cgi-bin/api.values.post', params)
      log.debug('Update returns -> %s', resp.msg)
      return resp.msg

   def reboot(self):
      # Reboot
      log.debug('Reboot (type %d)...' % self.type)
      t1 = time()

      if self.type == 1:
         resp = self.get('rs.htm')
      elif self.type == 2:
         resp = self.get('cgi-bin/rs')
      elif self.type == 3:
         resp = self.get('cgi-bin/api-sys_operation', {'request': 'REBOOT'})
      return 'OK'
#      # While rebooting, phone is reachable, then unreachable, then reachable again
#      reachable = True
#      for wait in xrange(60):
#         try:
#            resp = urllib2.urlopen(self.url, timeout=1)
#            if not reachable: break
#         except:
#            return 'ok'
#            reachable = False
#         sleep(1)
#      t2 = time()
#      log.debug('Reboot done in %.1f seconds !' % (t2-t1))
#      return resp.msg

   def configure(self, pwd, tftp_dir, firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None, dns1=None, dns2=None,
         sip_server=None, sip_user=None, sip_display_name=None,
         mwi_subscribe=False, reboot=True, screen_url=None, exten=None):
      '''Parameters: firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None
      '''

      mac = self.mac.replace(':','')
      tftp = config.get('directory.tftp') + 'phones/firmware'
      vlan = config.get('gxp.vlan')
      if vlan:
         self.params['P51'] = vlan
      keypad = config.get('gxp.keypad')
      if keypad in ('0', '1', '2'):
         self.params['P1357'] = keypad
      self.params['P2'] = pwd
      if not os.path.isdir('%s/%s' % (tftp, mac)):
         os.mkdir('%s/%s' % (tftp, mac))
      for f in os.listdir(tftp):
         if os.path.isdir('%s/%s' % (tftp, f)): continue
         try:
            os.symlink('../%s' % f, '%s/%s/%s' % (tftp, mac, f))
         except:
            pass # XXX OSError: [Errno 17] Le fichier existe
      self.params['P192'] = '%s/%s' % (firmware_url, mac)
      self.params['P237'] = config_url
      self.params['P331'] = phonebook_url + '/grandstream/phonebook'
      self.params['P341'] = screen_url + '/grandstream/screen'
      self.params['P30'] = ntp_server
      self.params['P64'] = 120
      self.params['P207'] = syslog_server
      if dns1:
         (self.params['P21'], self.params['P22'], self.params['P23'],
            self.params['P24']) = dns1.split('.')
      if dns2:
         (self.params['P25'], self.params['P26'], self.params['P27'],
            self.params['P28']) = dns2.split('.')

      self.params['P270'] = default_company
      self.params['P99'] = 1 # XXX if mwi_subscribe else 0
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
      self.params['P1347'] = '**' # BLF Call-pickup Prefix
      self.params['P57'] = 8
      self.params['P102'] = 2 # dd-mm-yyyy
      self.params['P122'] = 1 # 24 hours

      if self.type in (2, 3): # Newer GXP
         self.params['P64'] = 'HAW10' # GMT-10
         self.params['P143'] = 0 # No DHCP option 2
         self.params['P1379'] = 'c' # celsius degrees
         self.params['P1362'] = 'fr' # language
         self.params['update'] = 'Mise a jour'

      else: # Old GXP
         # Display Language. 0 - English, 3 - Secondary Language, 2 - Chinese
         self.params['P342'] = 3
         self.params['P399'] = 'french'
         self.params['P330'] = 1 # HTTP phonebook download
         self.params['P331'] = phonebook_url + ':8888/grandtream'
         self.params['P341'] = screen_url + ':8888/grandstream'
         self.params['P340'] = 1 # HTTP Idle Screen XML Download
         self.params['P212'] = 0 # HTTP Firmware Upgrade

      # Generate conf files (text and binary)
      name = tftp_dir + '/phones/config/cfg%s' % self.mac.replace(':','')
      try:
         txt = open(name + '.txt', 'w')
         for k in self.params.keys():
            txt.write('%s=%s\n' % (k, self.params[k]))
         txt.close()
         log.debug('Config file written (text)')
      except:
         log.error('ERROR: write text config file')

      bin = self.encode()

      try:
         cfg2 = open(name, 'w')
         for x in bin:
            cfg2.write(chr(x))
         cfg2.close()
         log.debug('Config file written (bin)')
      except:
         log.error('ERROR: write binary config file')

      # Update and reboot phone
      self.update(self.params)
      if reboot:
         sleep(3)
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

