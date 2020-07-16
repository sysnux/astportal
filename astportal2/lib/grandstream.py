# -*- coding: utf-8 -*-
# vim: tabstop=3 expandtab shiftwidth=3 softtabstop=3

import logging
log = logging.getLogger(__name__)
from gevent import sleep
from BeautifulSoup import BeautifulSoup, Tag, BeautifulStoneSoup
from struct import pack, unpack
import os
import re
from hashlib import sha256
from binascii import b2a_hex
from collections import defaultdict
from urllib import urlencode
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
proxies = dict(http=None, https=None) # No HTTpoxy!

from tg import config
default_company = config.get('company')

class Grandstream(object):

   params = dict(
# Admin password for web interface
P2 = 'admin',
# VLAN TAG
#P51 = 1601,
# Authenticate ID
#P36 = '',
# No Key Entry Timeout. Default - 4 seconds.
P85 = 3,
# Use # as Dial Key. 0 - no, 1 - yes
P72 = 0,
# Local RTP port (1024-65535, default 5004)
P39 = 5004,
# Use Random Port. 0 - no, 1 - yes
P78 = 0,
# Keep-alive interval (in seconds. default 20 seconds)
P84 = 20,
#Use RFC3581 Symmetric Routing
P131 = 1,
# Account 1 Ring Tone: 0=system ring tone, N=custom ring tone N
#P104 = 0,
# Firmware Upgrade. 0 - TFTP Upgrade,  1 - HTTP Upgrade,  2 - HTTPS Upgrade.
P212 = 2,
# Publish presence (not supported by *, generates traffic)
P188 = 0,
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
# Automatic Upgrade. 0 - No, 1 - Yes. Default is No. 2=tous les jours
P194 = 2,
P285 = 1, # Heure début mise à jour 
P8459 = 3, # Heure fin mise à jour
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
P332 = 240,
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
# Configuration Via Keypad Menu. 0 - Unrestricted, 1 - Basic settings only, 2 - Constraint mode
P1357 = 2,
# Idle Screen XML Download HTTPS
P340=3,
# HEADSET Key Mode
P1312=1,
# Idle Screen XML Server Path
# P341=172.20.6.1/grandstream/screen,
# Download Screen XML at Boot-up Yes
P1349=1,
# Phonebook key -> local phonebook
P1526=2,
# Web Access Mode. 0 - HTTPS, 1 - HTTP. Default is 1
P1650 = 0,
# Enable Call Features.  0 - No, 1 - Yes. Default is 1
P191 = 0,
# Off-hook Auto Dial
#P71
# Disable SSH. 0 - No, 1 - Yes. Default is 0
P276 = 1,
# Screensaver 0 - No, 1 - Yes. Default is 1
P2918 = 0,
# Dial Plan 0 - Disabled, 1 Enabled
P2382 = 0,
# Secondary SIP server
P2312 = '',
P323 = '0', # Speed dial
P302 = 'Sécurité',
P303 = '3',
P324 = '0',
P305 = 'Support info',
P306 = '8777',
P325 = '0',
P308 = 'Interception',
P309 = '*8#',
P326 = '0',
P311 = 'Annulation renvoi',
P312 = '#21#',
#P327 = '0',
#P314 = 'Ne pas déranger',
#P315 = '*27#',
#P328 = '0',
P317 = 'Annulation ne pas déranger',
P318 = '#27#',
P22119 = '0', # Activation CDP, 0 pour désactiver
P196 = 'Ac3PuM7trq48', # User mot de passe
P2304 = '1', # Transfert sur raccrochement en conférence
)


   def __init__(self, host, mac, pwd='admin'):
      self.vendor = 'Grandstream'
      self.model = None
      self.host = host
      self.mac = mac
      self.pwd = pwd
      self.token = None
      self.token_ts = None
      self.type = 0
      self.sid = None
      self.cj = {}
      self.session = requests.Session()

   def get(self, action, params={}):

      if self.type in (0, 1, 2) and params is not None:
         params['gnkey'] = '0b82' # Seems it *must* be last parameter, or update fails
      elif self.sid is not None:
         params['sid'] = self.sid

      for c in self.cj:
         log.debug('Cookie: %s = %s' % (c.name, c.value))

      for k, v in params.iteritems():
          log.debug('Param "%s" => "%s"', k, v)

      try:
         # Try HTTPS first
         resp = self.session.get('https://' + self.host + '/' + action,
                             proxies=proxies,
                             params=params,
                             verify=False)
      except:
         try:
            # Then HTTP (brand new phone)
            resp = self.session.get('http://' + self.host + '/' + action, 
                             proxies=proxies,
                             params=params)
         except:
            log.warning('GET %s, params %s failed' % (\
               self.host + '/' + action, params))
            return None
      return resp

   def post(self, action, params={}, **kw):

      # Type 3 phones only
      if self.type !=3:
          return None

      if self.sid is not None:
         params['sid'] = self.sid

      try:
         # Try HTTPS first
         log.debug('HTTPS POST(%s, %s, %s)', action, params, kw)
         resp = self.session.post('https://' + self.host + '/' + action,
                                  proxies=proxies,
                                  data=params,
                                  verify=False,
                                  **kw)
      except:
         log.debug('HTTPS POST failed, trying with HTTP')
         try:
            # Then HTTP (brand new phone)
            resp = self.session.post('http://' + self.host + '/' + action,
                                    proxies=proxies,
                                    data=params,
                                    **kw)
         except:
            log.warning('POST %s, params %s failed', self.host + '/' + action, params)
            return None

      return resp

   def post_json(self, action, params={}):
       log.warning('post_json %s %s', self.host, params)
       try:
           # Try HTTPS first
           resp = self.session.post('https://' + self.host + '/' + action,
                                  data = json.dumps(params),
                                  headers = {'Content-Type': 'application/json'},
                                  verify=False)
       except:
           log.warning('POST JSON %s, params %s failed' % (\
                       self.host + '/' + action, params))
           return None

       log.warning('post_json OK %s', self.host)
       return resp

   def login(self, pwd=None):

      if pwd:
         self.pwd = pwd

      resp = self.get('cgi-bin/api.values.get',
                     {'request':  '68:phone_model:password_token:password_token_timestamp',
                      'sid': self.sid})
      try:
         data = resp.json()
      except:
         return False
      self.token = data['body'].get('password_token')
      self.token_ts = data['body'].get('password_token_timestamp')
      self.model = data['body'].get('phone_model')
      self.version = data['body'].get('68')
      log.info('Found %s %s', self.model, self.version)

      params = {'username': 'admin'}

      if self.model.startswith('GXP16'):
         self.type = 3 # Needed for self.post
         r = self.post('cgi-bin/dologin',
                       params={'username': 'admin', 'password': self.pwd},
                       headers={'origin': self.host, 'referrer': self.host})
         if True: #try:
            ret = r.json()
            self.sid = ret['body']['sid']
            log.info('Login correct %s', self.host)
            return True
         else: #except:
            log.warning('ERROR %s, abandon', r.content)
            return False

      # First, try newer method involving cgi-bin/access
      self.type = 3 # Needed for self.post
      sha = sha256()
      sha.update(params['username'])
      log.debug('post access')
      r = self.post('cgi-bin/access',
                    {'access': sha.hexdigest()},
                    headers={'origin': self.host})
      if r.status_code == 200:
          # This is indeed a newer phone / firmware
          try:
              ret = r.json()
              ok = True
          except:
              ok = False
              log.warning('GRP access returns: %s', ret)

          if ok and ret['response'] == 'success':
              sha = sha256()
              sha.update((self.pwd + ret['body']))
              r = self.post('cgi-bin/dologin',
                            {'username': params['username'], 'password': sha.hexdigest()},
                            headers={'origin': self.host})
              try:
                  ret = r.json()
              except:
                  log.warning('GRP dologin returns: %s', ret)
                  return False
              if ret['response'] != 'success':
                  return False
              return True

      # Else, try older methods
      if self.token:
         # Encoded password
         sha = sha256()
         sha.update(self.pwd + self.token)
         sha = sha.digest()
         pw = b2a_hex(sha)
         params['password'] = pw
         params['timestamp'] = self.token_ts
      else:
         params['password'] = self.pwd

      # Newer phones
      resp = self.get('cgi-bin/dologin', params=params)
      if resp is not None and resp.status_code==200:
         log.debug('GXP new firmware: params "%s" returns "%s"', resp.content)
         try:
            data = resp.json()
            if data['response'] == 'success':
               self.sid = data['body']['sid']
               self.type = 3
               log.debug('Logged in GXP2xxx, new firmware, sid=%s' % self.sid)
               return True

         except:
            log.error('new firmware does not return JSON ?')
            pass

      # New firmware
      resp = self.get('cgi-bin/dologin', {'P2': self.pwd})
      if resp is not None and resp.status_code == 200:
            # GXP-2100
            for c in self.cj:
               log.debug('Cookie: %s = %s' % (c.name, c.value))
               if c.name=='session_id':
                  log.debug('Logged in GXP2xxx, old firmware')
                  self.type = 2
                  return True

      # Older phones
      resp = self.get('dologin.htm', {'P2': self.pwd})
      if resp is not None and resp.status_code == 200:
         for c in self.cookies:
            log.debug('Cookie: %s = %s' % (c.name, c.value))
            if c.name=='SessionId':
               log.debug('Logged in GXP1xxx')
               self.type = 1
               return True

      log.warning('Login failed (check password? %s)', pwd)
      return False

   def logout(self):
      if self.type == 3: # GXP-14XX 21XX new firmware
          resp = self.get('cgi-bin/dologout')
          log.info('logout returns %s', resp)
      else:
          log.warnin('logout not implemented for type %s', self.type)

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

      if self.type == 2: # GXP-14XX 21XX
         html = BeautifulSoup(unicode(resp.content))
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
         resp = self.get('cgi-bin/api.values.get',
                        {'request':  '68:phone_model:password_token:password_token_timestamp:67',
                         'sid': self.sid})
         data = resp.json()
         model = data['body']['phone_model']
         soft = data['body']['68']
         self.token = data['body'].get('password_token')
         self.token_ts = data['body'].get('password_token_timestamp')
         if not self.mac:
            mac = data['body'].get('67')
            if mac:
               self.mac = mac

      self.model = model

      log.debug(u'Model <%s>'% model)
      log.debug(u'Version <%s>'% soft)

      return {'model': model.strip(), 'version': soft.strip()}

   def update(self, params):
      log.debug('Update (type %d)...' % self.type)
      if self.type == 1:
         resp = self.get('update.htm', params)
      elif self.type == 2:
         resp = self.get('cgi-bin/update', params)
      elif self.type == 3:
         resp = self.post('cgi-bin/api.values.post', params)
      log.debug('Update returns -> %s', resp.content)
      return resp.content

   def reboot(self):
      '''Reboot phone'''
      log.debug('Reboot (type %d)...' % self.type)
      if self.type == 1:
         resp = self.get('rs.htm')
      elif self.type == 2:
         resp = self.get('cgi-bin/rs')
      elif self.type == 3:
         resp = self.post('cgi-bin/api-sys_operation', {'request': 'REBOOT'})
      return 'OK'

   def configure(self, pwd, tftp_dir, firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None, dns1=None, dns2=None,
         sip_server=None, sip_user=None, sip_display_name=None,
         mwi_subscribe=False, reboot=True, screen_url=None, exten=None,
         sip_server2=None, secretary=None, ringtone=None):

      '''Called from controllers/phone when creating / modifying phone
      '''

      mac = self.mac.replace(':','')
      tftp = config.get('directory.tftp') + 'phones/firmware'
      vlan = config.get('gxp.vlan')
      keypad = config.get('gxp.keypad')
      if not os.path.isdir('%s/%s' % (tftp, mac)):
         os.mkdir('%s/%s' % (tftp, mac))
      try:
         os.unlink('%s/%s/ring1.bin' % (tftp, mac))
      except:
         pass
      if ringtone is not None:
         try:
            ringtone = re.sub(r'\W', '_', ringtone)
            os.symlink('../%s.ring' % ringtone, '%s/%s/ring1.bin' % (tftp, mac))
            self.params['P104'] = 1
         except:
            pass # XXX OSError: [Errno 17] Le fichier existe
      for f in os.listdir(tftp):
         if os.path.isdir('%s/%s' % (tftp, f)):
            continue
         if f.endswith('.ring'):
            # Granstream ringtone
            continue
         try:
            os.symlink('../%s' % f, '%s/%s/%s' % (tftp, mac, f))
         except:
            pass # XXX OSError: [Errno 17] Le fichier existe
      if screen_url is None:
         screen_url = config_url

      #
      really_configure = self.configure_xml if self.model.startswith('GRP') \
                     else self.configure_text

      really_configure(pwd, tftp_dir, firmware_url, config_url, ntp_server,
         phonebook_url, syslog_server, dns1, dns2,
         sip_server, sip_user, sip_display_name,
         mwi_subscribe, reboot, screen_url, exten,
         sip_server2, secretary, ringtone)

   def configure_txt(self, pwd, tftp_dir, firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None, dns1=None, dns2=None,
         sip_server=None, sip_user=None, sip_display_name=None,
         mwi_subscribe=False, reboot=True, screen_url=None, exten=None,
         sip_server2=None, secretary=None, ringtone=None):
      if vlan:
         self.params['P51'] = vlan
      if keypad in ('0', '1', '2'):
         self.params['P1357'] = keypad
      self.params['P2'] = pwd
      if ringtone is not None:
         self.params['P104'] = 1

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
      if self.model.startswith('GXP21'):
         self.params['P270'] += ' - ' + exten
      elif self.model.startswith('GXP162'):
         self.params['P270'] += ' ' + exten
      self.params['P99'] = 1 # XXX if mwi_subscribe else 0
      if sip_server:
         self.params['P47'] = sip_server
         self.params['P35'] = sip_user
         self.params['P36'] = sip_user
         self.params['P34'] = pwd
         self.params['P3'] = sip_display_name
         self.params['P271'] = \
         self.params['P31'] = \
         self.params['P81'] = \
         self.params['P1346'] = \
         self.params['P188'] = \
            1
         if sip_server2 is not None:
            self.params['P2312'] = sip_server2
      else:
         self.params['P47'] = \
         self.params['P35'] = \
         self.params['P36'] = \
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
      self.params['P182'] = \
      self.params['P58'] = \
         0
#      self.params['P29'] = 0

      self.params['P1402'] = 0 # Weather service
      self.params['P1404'] = 0 # Currency service
      self.params['P33'] = '*79'
      self.params['P29'] = 0 # Early Dial
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
#         self.params['update'] = 'Mise a jour'

      else: # Old GXP
         # Display Language. 0 - English, 3 - Secondary Language, 2 - Chinese
         self.params['P342'] = 3
         self.params['P399'] = 'french'
         self.params['P330'] = 1 # HTTP phonebook download
         self.params['P331'] = phonebook_url + ':8888/grandtream'
         self.params['P341'] = screen_url + ':8888/grandstream'
         self.params['P340'] = 1 # HTTP Idle Screen XML Download
         self.params['P212'] = 0 # HTTP Firmware Upgrade

      if model.startswith('GXP21') or model.startswith('GXP16'):
         # Dial plan
         self.params['P290'] = \
            '{ x+ | *x+ | *x.# | *xx.*xx.# | *xx.*0xx.# | *xx.*xx.*xx.# | #xx.| #xx.# }'
         self.params['P334'] = 100
         self.params['P335'] = 50
         self.params['P2380'] = 0 # Show account name only
         self.params['P2970'] = 1 # Phonebook management Exact match
         self.params['P2991'] = 25 # Call log on softkey 1
         self.params['P2993'] = 'Historique' # History on softkey 3
         self.params['P8345'] = 0 # Show Label Background
         self.params['P8346'] = 1 # Use Long Label
         self.params['P2916'] = 1 # Wallpaper Source: Download
         self.params['P2917'] = 'https://' + config_url + '/logo60.jpg' # Wallpaper Server Path

      if self.model.startswith('GXP21') and secretary:
         # Filtrage secrétaire
         self.params['P1365'] = 11
         self.params['P1366'] = 0
         self.params['P1467'] = 'Secrétariat'
         self.params['P1468'] = secretary
         self.params['P2987'] = 10
         self.params['P2989'] = 'Filtrage'
         self.params['P2990'] = '*21*%s#' % secretary

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
      self.update({'P212': 2, 'P237': config_url, 'sid': self.sid})
      sleep(6)
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
      params = urlencode(self.params)
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

   def configure_xml(self, pwd, tftp_dir, firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None, dns1=None, dns2=None,
         sip_server=None, sip_user=None, sip_display_name=None,
         mwi_subscribe=False, reboot=True, screen_url=None, exten=None,
         sip_server2=None, secretary=None, ringtone=None):
      '''Parameters: firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None
      '''

      # Create XML document for Grandstream provionning
      xml = BeautifulStoneSoup('''<?xml version='1.0' encoding='utf-8'?>
<gs_provision version="1">
<config version="2">''')
      xml_config = xml.find('config')

      def set_item(key, value):
         '''Create item, set value, insert in XML document'''
         if not key or not value:
            return
         el = Tag(xml, 'item', attrs={'name': key})
         el.string = value
         xml_config.insert(0, el)

      mac = self.mac.replace(':','')
      tftp = config.get('directory.tftp') + 'phones/firmware'
      set_item('network.port.eth.1.vlan.tag', config.get('gxp.vlan'))
      keypad = config.get('gxp.keypad')
      if keypad in ('0', '1', '2'):
		   # Unrestricted, BasicSettingsOnly, ConstraintMode, LockedMode -->
		   set_item('security.configurationViaKeypadMenu',
   		   ('Unrestricted', 'BasicSettingsOnly', 'ConstraintMode')[int(keypad)])


      if not os.path.isdir('%s/%s' % (tftp, mac)):
         # Create firmware directory
         os.mkdir('%s/%s' % (tftp, mac))

      # Remove previous ringtone      
      try:
         os.unlink('%s/%s/ring1.bin' % (tftp, mac))
      except:
         pass

      if ringtone is not None:
         # Add custom ringtone
         try:
            ringtone = re.sub(r'\W', '_', ringtone)
            os.symlink('../%s.ring' % ringtone, '%s/%s/ring1.bin' % (tftp, mac))
            self.params['P104'] = 1
         except:
            pass # XXX OSError: [Errno 17] Le fichier existe

      for f in os.listdir(tftp):
         # Create links to ringones for this phone
         if os.path.isdir('%s/%s' % (tftp, f)):
            continue
         if f.endswith('.ring'):
            # Granstream ringtone
            continue
         try:
            os.symlink('../%s' % f, '%s/%s/%s' % (tftp, mac, f))
         except:
            pass # XXX OSError: [Errno 17] Le fichier existe

      # Main parameters
      set_item('users.admin.password', pwd)
      set_item('users.user.password', 'Ac3PuM7trq48')
      set_item('provisioning.firmware.protocol', 'HTTPS')
      set_item('provisioning.firmware.serverPath', '%s/%s' % (firmware_url, mac))
      set_item('provisioning.config.protocol', 'HTTPS')
      set_item('provisioning.config.serverPath', config_url)
      set_item('phonebook.download.mode', 'EnabledUseHTTPS')
      set_item('phonebook.download.server', phonebook_url + '/grandstream/phonebook')
      set_item('phonebook.download.interval', '120')
      set_item('phonebook.download.removeEditedEntries', 'No')
#      self.params['P341'] = screen_url + '/grandstream/screen'
#      self.params['P64'] = 120
      set_item('maintain.syslog.server', syslog_server)
      set_item('dateTime.ntp.server.1', ntp_server)
      set_item('network.internetProtocol', 'IPv4Only')
      set_item('language.gui', 'fr')
      set_item('dateTime.override.dhcp.allowOption42', 'Yes')
      set_item('dateTime.timezone', 'HAW10')
      set_item('dateTime.override.dhcp.allowOption2', 'Yes')
      set_item('dateTime.format.date', 'dd-mm-yyyy')
      set_item('dateTime.format.time', '24Hour')

      if dns1:
         dns11, dns12, dns13, dns14 = dns1.split('.')
         set_item('network.dns.1.ip1', dns11)
         set_item('network.dns.1.ip2', dns12)
         set_item('network.dns.1.ip3', dns13)
         set_item('network.dns.1.ip4', dns14)

      if dns2:
         dns21, dns22, dns23, dns24 = dns2.split('.')
         set_item('network.dns.2.ip1', dns21)
         set_item('network.dns.2.ip2', dns22)
         set_item('network.dns.2.ip3', dns23)
         set_item('network.dns.2.ip4', dns24)

      if sip_server:
         set_item('account.1.enable', 'Yes')
         set_item('account.1.call.transferOnConferenceHangup', 'Yes')
         set_item('account.1.name', default_company + ' - ' + exten)
         set_item('account.1.sip.server.1.address', sip_server)
         set_item('account.1.sip.userid', sip_user)
         set_item('account.1.sip.subscriber.userid', sip_user)
         set_item('account.1.sip.subscriber.password', pwd)
         set_item('account.1.sip.subscriber.name', sip_display_name)
         set_item('account.1.sip.voicemail.number', '*79')
         set_item('account.1.call.earlyDial', 'No')
         set_item('account.1.sip.subscribe.forMwi', 'Yes')
         set_item('account.1.sip.keepAlive.enable', 'Yes')
         set_item('account.1.sip.unregisterOnReboot', 'All')
         set_item('account.1.sip.header.xGrandstream', 'No')
         set_item('account.1.sip.server.2.address', sip_server2)

		#  Settings/Programmable Keys/Virtual Multi-Purpose Keys
      set_item('pks.vpk.6.keyMode', '0')
      set_item('pks.vpk.6.account', '0')
      set_item('pks.vpk.6.description', u'Sécurité')
      set_item('pks.vpk.6.value', '3')
      set_item('pks.vpk.7.keyMode', '0')
      set_item('pks.vpk.7.account', '0')
      set_item('pks.vpk.7.description', u'Support info.')
      set_item('pks.vpk.7.value', '8777')
      set_item('pks.vpk.8.keyMode', '0')
      set_item('pks.vpk.8.account', '0')
      set_item('pks.vpk.8.description', u'Interception')
      set_item('pks.vpk.8.value', '*8#')
      set_item('pks.vpk.9.keyMode', '0')
      set_item('pks.vpk.9.account', '0')
      set_item('pks.vpk.9.description', u'Annul. renvoi')
      set_item('pks.vpk.9.value', '#21#')
      set_item('pks.vpk.10.keyMode', '0')
      set_item('pks.vpk.10.account', '0')
      set_item('pks.vpk.10.description', u'Annul. ne pas déranger')
      set_item('pks.vpk.10.value', '#27#')
      set_item('network.cdp', 'No')

#      if self.model.startswith('GXP21'):
#         # Dial plan
#         self.params['P290'] = \
#            '{ x+ | *x+ | *x.# | *xx.*xx.# | *xx.*0xx.# | *xx.*xx.*xx.# | #xx.| #xx.# }'
#         self.params['P334'] = 100
#         self.params['P335'] = 50
#         self.params['P2380'] = 0 # Show account name only
#         self.params['P2970'] = 1 # Phonebook management Exact match
#         self.params['P2991'] = 25 # Call log on softkey 1
#         self.params['P2993'] = 'Historique' # History on softkey 3
#         self.params['P8345'] = 0 # Show Label Background
#         self.params['P8346'] = 1 # Use Long Label
#         self.params['P2916'] = 1 # Wallpaper Source: Download
#         self.params['P2917'] = 'https://' + config_url + '/logo60.jpg' # Wallpaper Server Path

#      if self.model.startswith('GXP21') and secretary:
#         # Filtrage secrétaire
#         self.params['P1365'] = 11
#         self.params['P1366'] = 0
#         self.params['P1467'] = 'Secrétariat'
#         self.params['P1468'] = secretary
#         self.params['P2987'] = 10
#         self.params['P2989'] = 'Filtrage'
#         self.params['P2990'] = '*21*%s#' % secretary

      # Generate XML conf file
      name = tftp_dir + '/phones/config/cfg%s.xml' % mac
      try:
         with open(name, 'w') as xml_file:
            xml_file.write(str(xml).replace('><', '>\n<'))
      except:
         log.error('Could not write XML config file "%s"', name)

      # Update config URL: the phone will apply and load XML file
      self.update({'P212': 2, 'P237': config_url, 'sid': self.sid}) # self.params)
      sleep(3)

   def notify(self, phone):
      log.info('Notify phone %s @%s', phone.sip_id, self.host)

      if phone.model.startswith('GXP'):
         gxp_actions.put_nowait((phone, self.host))
         gxp_in_actions_queue.append(phone)
         for p in DBSession.query(Phone) \
                           .filter(Phone.phone_id!=phone.phone_id) \
                           .filter(or_(Phone.secretary==phone.exten,
                                       Phone.exten==phone.secretary)):
            if p in gxp_in_actions_queue:
                continue
            log.info('%s => boss or secretary %s', phone, p)
            peer = 'PJSIP/' + p.sip_id
            if 'Address' in Globals.asterisk.peers[peer] and \
               Globals.asterisk.peers[peer]['Address'] is not None:
               ip = (Globals.asterisk.peers[peer]['Address']).split(':')[0]
            else:
               log.error('Phone %s, no IP address!', p.phone_id)
               return
            if p.vendor == 'Grandstream':
               gs = Grandstream(ip, p.mac)
               gs.notify(p)

      else:
         # Send SIP notify to refresh screen XXX
         log.error('NOTIFY NOT IMPLEMENTED for %s!', phone.model)


   def update_screen(self, phone, ip):

      log.info('update_screen %s @%s', phone, ip)

      # Leave import here to avoid circular import troubles
      from astportal2.controllers.grandstream import check_call_forwards

      # Update all secretaries
      secretaries = defaultdict(list)
      for boss in DBSession.query(Phone) \
                           .filter(Phone.secretary != None) \
                           .order_by(Phone.exten):
         if boss.secretary.startswith('g('):
            # The secretary is a queue, we must look for phones of 
            # indivdual members in this queue
            q, n = boss.secretary[2:-1].split(',')
            for m in Globals.asterisk.queues[q]['Members']:
               sip = Globals.asterisk.members[m]['Location'][-8:]
               p = DBSession.query(Phone) \
                             .filter(Phone.sip_id == sip) \
                             .one()
               secretaries[p].append(boss)
               log.info('Added secretary %s from queue "%s" for boss %s',
                         p, q, boss)
         else:
            p = DBSession.query(Phone) \
                             .filter(Phone.exten == boss.secretary) \
                             .one()
            secretaries[p].append(boss)
            log.info('Added secretary %s from exten "%s" for boss %s',
                     p, boss.secretary, boss)

      log.info('Secretaries %s', secretaries)
      for secretary, bosses in secretaries.iteritems():
         log.info('Updating secretary %s for bosses %s', secretary, bosses)
         params = {}
         mpk = []
         i = 0
         for boss in bosses:
             # This GXP belongs to a secretary, configure keys on extension
             cfs_out, cfs_in, dnd = check_call_forwards(boss)
             log.info('boss %s cfs_in=%s cf_out=%s', boss, cfs_in, cfs_out)
             desc = boss.user.display_name if boss.user else boss.exten
             # First key is BLF
             mpk.append({'VKID': 17+i,
                         'ValueName': boss.exten,
                         'Description': desc,
                         'Account': 0,
                         'TypeMode': 3,
                         'Priority': 2000+i})
             params['P23%03d' % (5*i)] = 1 # Mode BLF
             params['P23%03d' % (5*i+2)] = desc # Description
             params['P23%03d' % (5*i+3)] = boss.exten # Description
             i += 1 # Next key is direct call
             mpk.append({'VKID': 17+i,
                         'ValueName': boss.exten,
                         'Description': 'Direct ' + desc,
                         'Account': 0,
                         'TypeMode': 6,
                         'Priority': 2000+i})
             params['P23%03d' % (5*i)] = 0 # Mode Speed Dial
             params['P23%03d' % (5*i+2)] = 'Direct ' # + desc # Description
             params['P23%03d' % (5*i+3)] = 'DIR' + boss.exten # Value
             i += 1 # Next key is enable / disable filtering
             params['P23%03d' % (5*i)] = 0 # Mode Speed Dial
             if cfs_out:
                params['P23%03d' % (5*i+2)] = 'Filtré !' # + desc # Description
                params['P23%03d' % (5*i+3)] = '*70' + boss.exten # Value annulation renvoi autre poste
                mpk.append({'VKID': 17+i,
                            'ValueName': '*70' + boss.exten,
                            'Description': 'Filtré !',
                            'Account': 0,
                            'TypeMode': 6,
                            'Priority': 2000+i})
             else:
                params['P23%03d' % (5*i+2)] = 'Filtrage' # + desc # Description
                if boss.secretary.startswith('g('):
                   forward = '*72' + boss.exten + boss.secretary[2:-1].split(',')[1]
                else:
                   forward = '*71' + boss.exten
                params['P23%03d' % (5*i+3)] = forward  # *71 : renvoi immédiat d'un autre poste vers celui-ci
                mpk.append({'VKID': 17+i,
                            'ValueName': forward,
                            'Description': 'Filtrage',
                            'Account': 0,
                            'TypeMode': 6,
                            'Priority': 2000+i})
             i += 2 # One blank key

         peer = 'PJSIP/' + secretary.sip_id
         if 'Address' in Globals.asterisk.peers[peer] and \
               Globals.asterisk.peers[peer]['Address'] is not None:
               ip = (Globals.asterisk.peers[peer]['Address']).split(':')[0]
         else:
               log.error('Phone %s, no IP address!', secretary.phone_id)
               continue

         if secretary.vendor != 'Grandstream':
             continue

         gs = Grandstream(ip, secretary.mac)
         if gs.login(secretary.password):

             infos = gs.infos()
             if not infos['model'].startswith('GXP21'):
                 log.error('Found unknown phone (%s), cancel', infos)
                 continue

             ret = gs.post_json('cgi-bin/api-save_mpk', mpk)
             if not ret.ok:
                ret = gs.post('cgi-bin/api.values.post', params)
                if not ret.ok:
                    log.error('cgi-bin/api.values.post %s returns %s', params, ret)

                try:
                    result = json.loads(ret.text.split('\r\n')[-1])
                except:
                    log.error('JSON \n%s\n%s', ret.text)

                try:
                    if result['response'] != 'success':
                        log.error('Respons %s', ret.text)
                        if infos['model'] != secretary.model:
                            log.warning('Update phone model "%s" for %s', infos['model'], secretary)
                            secretary.model = infos['model']
                except:
                    log.error('ret.text = %s', ret.text)
            
             gs.logout()

         else:
              log.error('Login failed %s', secretary)
      # End for secretary

      # Now update the actual phone
      if phone.model == 'GXP1165':
         # Send SIP notify to refresh screen
         Globals.manager.send_action({'Action': 'PJSIPNotify', 
                                      'Endpoint': phone.sip_id,
                                      'Variable': 'Event=x-gs-screen'})
         log.info('Sent SIP NOTIFY to GXP1165 %s!', phone.phone_id)

      else:
          if not self.login(phone.password):
              log.error('Login failed %s', phone)
              return

          infos = self.infos()
          if not infos['model'].startswith('GXP'):
             log.error('Found unknown phone (%s), cancel', infos)
             return

          params = {}
          mpk = []
          # MPK TypeMode: speed dial = 2, BLF = 3, Speed dial via active account = 6
          if phone.secretary:
             # GXP belongs to a boss, configure filtering
             if phone.secretary.startswith('g('):
                sec = phone.secretary.split(',')[1][:-1]
                params['P1365'] = 10 # Speed dial
             else:
                sec = phone.secretary
                params['P1365'] = 11 # BLF
             cfs_out, cfs_in, dnd = check_call_forwards(phone)
             # Second account key
             params['P1366'] = 0
             params['P1467'] = u'Secrétariat'
             params['P1468'] = sec
             mpk.append({'VKID': 2,
                         'ValueName': sec,
                         'Description': u'Secrétariat',
                         'Account': 0,
                         'TypeMode': 3,
                         'Priority': 1,
                         'Locked': 0})

             if 'CFIM' in [x[0] for x in cfs_out]:
                # Second soft key
                params['P2987'] = 10
                params['P2989'] = u'Filtré !'
                params['P2990'] = u'#21#'
                mpk.append({'VKID': 178,
                            'ValueName': u'#21#',
                            'Description': u'Filtré !',
                            'Account': 0,
                            'TypeMode': 2,
                            'Priority': 3001})
             else:
                # Second soft key
                params['P2987'] = 10
                params['P2989'] = u'Filtrage'
                params['P2990'] = u'*21*%s#' % sec
                mpk.append({'VKID': 178,
                            'ValueName': u'*21*%s#' % sec,
                            'Description': u'Filtrage',
                            'Account': 0,
                            'TypeMode': 2, # Speed dial via active account
                            'Priority': 3001})
 
             ret = self.post_json('cgi-bin/api-save_mpk', mpk)
             result = {}
             if not ret.ok:
                ret = self.post('cgi-bin/api.values.post', params)
                if not ret.ok:
                    log.error('Configuration returns %s', ret)

                try:
                    result = json.loads(ret.text.split('\r\n')[-1])
                except:
                    log.error('JSON \n%s\n%s', ret.text)

             else:
                try:
                    result = json.loads(ret.text.split('\r\n')[-1])
                except:
                    log.error('JSON \n%s\n%s', ret.text)

             if result.get('response', None) != 'success':
                 log.error('Respons %s', ret.text)
                 if infos['model'] != phone.model:
                      log.warning('Update phone model "%s" for %s',
                                  infos['model'], phone)
                      phone.model = infos['model']

             self.logout()

      log.info('Screen updated for %s', phone)
       

from astportal2.lib.app_globals import Globals
from astportal2.model import DBSession, Phone
from sqlalchemy import or_
from Queue import Queue
import json
# Queue of actions tuples (Phone, ip_addr) to signal GXP phones
gxp_actions = Queue()
gxp_in_actions_queue = []

def do_gxp_actions():
   '''
   Called from scheduler (lib/app_globals)
   '''

   busy = [chan[-17:-9] for chan in Globals.asterisk.channels.keys()]
   requeue = []

   while not gxp_actions.empty():
      phone, ip = gxp_actions.get_nowait()
      gxp_in_actions_queue.remove(phone)

      if phone.sip_id in busy:
         requeue.append((phone, ip))
         continue

      log.info('gxp_action %s @%s', phone, ip)
      gs = Grandstream(ip, phone.mac)
      gs.update_screen(phone, ip)

      # End while

   # Requeue
   for phone, ip in requeue:
      gxp_actions.put_nowait((phone, ip))
      gxp_in_actions_queue.append(phone)

