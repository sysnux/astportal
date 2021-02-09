# -*- coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

# Mitel / Aastra phones
# Defautl login : admin / 22222
# MAC      Vendor
# 00:10:BC Aastra Telecom
# 00:08:5D Aastra
# 08:00:0F MITEL CORPORATION



import logging
log = logging.getLogger(__name__)
from gevent import sleep
#from os import system, popen #, rename
from copy import deepcopy

import requests, json
from urllib import urlencode
from requests.auth import HTTPBasicAuth
from BeautifulSoup import BeautifulSoup
import xml.etree.ElementTree as ET

from tg import config
default_company = config.get('company')

class Mitel(object):

   global_sip_settings = {
             'screenName': 'first_line',
             'screenName2': 'second_line',
             'userName': '',
             'dispName': '',
             'authName': '',
             'blaName': '',       
             'mode': '0',
             'callWaiting': '1',
             'proxyIp': 'sip_server',
             'proxyPort': '0',
             'backupProxyIp': '0.0.0.0',
             'backupProxyPort': '0',
             'outboundProxy': 'sip_server',
             'outboundProxyPort': '0',
             'backupOutboundProxy': '0.0.0.0',
             'backupOutboundProxyPort': '0',
             'regIp': 'sip_server',
             'regPort': '0',
             'backupRegIp': '0.0.0.0',
             'backupRegPort': '0',
             'registrationPeriod': '0',
             'explicitMWISubscription': '1',
             'explicitMWISubscriptionPeriod': '10',
             'AFESubscriptionPeriod': '3600',
             'sessionTimer': '0',
             't1Timer': '0',
             't2Timer': '0',
             'transTimer': '4000',
             'transportProtocol': '1',
             'sipLocalPort': '5060',
             'sipLocalTLSPort': '5061',
             'regRetry': '1800',
             'regTimeout': '120',
             'regRenewal': '15',
             'blfPeriod': '3600',
             'acdPeriod': '3600',
             'blaPeriod': '300',
             'blacklistDur': '300',
             'rtpPort': '3000',
             'useNTE': '1',
             'dtmfMethod': '0',
             'srtpMode': '0',
             'codec1': '-3',
             'codec2': '-1',
             'codec3': '-1',
             'codec4': '-1',
             'codec5': '-1',
             'codec6': '-1',
             'codec7': '-1',
             'codec8': '-1',
             'codec9': '-1',
             'codec10': '-1',
             'ptime': '30',
             'silenceSuppression': '1',
             'adTimeout': '0',
             }

   def __init__(self, host, mac, pwd='22222'):
      self.host = host
      self.mac = mac
      self.pwd = pwd
      self.url = 'http://%s/' % host
      self.vendor = 'Mitel'
      self.model = None
      self.auth = HTTPBasicAuth('admin', pwd)

   def get(self, action, params=None, method='get'):
#      if params:
#         params = urlencode(params)

      method = method.lower()
      if method not in ('get', 'post'):
         log.error('Method "%s" not spported', method)
         return None

      try:
         if method == 'get':
            log.debug('GET(%s, auth=%s, params=%s)', 
                       self.url + action, self.auth, params)
            resp = requests.get(self.url + action, auth=self.auth, params=params, timeout=30)
         elif method == 'post':
            log.debug('POST(%s, auth=%s, data=%s)', 
                       self.url + action, self.auth, params)
            resp = requests.post(self.url + action, auth=self.auth, data=params, timeout=30)
      except:
         log.warning('Request %s, params %s failed' % (\
               self.url + action, params))
         return None

      if resp.status_code != 200:
         log.warning('Request %s, params %s returns %s' % (\
               self.url + action, params, resp))
         return None

      log.debug('Request %s, params %s returns code %s',
                 self.url + action, params, resp)
      return resp

   def login(self, pwd=None):
      return True

   def infos(self):
      r = self.get('sysinfo.html')
      if r is None:
          return None
      soup = BeautifulSoup(unicode(r.content))
      model = version = None
      for td in soup.findAll('td'):
         if td.text == 'Platform':
            model = td.findNext().text
         if td.text == 'Firmware Version':
            version = td.findNext().text
            break
      return {'model': model, 'version': version}

   def configure(self, pwd, tftp_dir, firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None, dns1=None, dns2=None,
         sip_server=None, sip_user=None, sip_display_name=None,
         mwi_subscribe=False, reboot=True, screen_url=None, exten=None,
         sip_server2=None, secretary=None, ringtone=None):
      '''Parameters: firmware_url, config_url, ntp_server,

Global SIP 
curl 'http://192.168.10.150/globalSIPsettings.html' 
      -H 'User-Agent: Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0' 
      -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' 
      -H 'Accept-Language: fr-FR,fr;q=0.8,en;q=0.5,en-US;q=0.3' 
      --compressed 
      -H 'Referer: http://192.168.10.150/globalSIPsettings.html' 
      -H 'Content-Type: application/x-www-form-urlencoded' 
      -H 'DNT: 1' 
      -H 'Authorization: Basic QWRtaW46MjIyMjI=' 
      -H 'Connection: keep-alive' 
      -H 'Upgrade-Insecure-Requests: 1' 
      --data 'screenName=&screenName2=&userName=&dispName=&authName=&password=&blaName=&mode=0&callWaiting=1&proxyIp=tiare.sysnux.pf&proxyPort=0&backupProxyIp=0.0.0.0&backupProxyPort=0&outboundProxy=tiare.sysnux.pf&outboundProxyPort=0&backupOutboundProxy=0.0.0.0&backupOutboundProxyPort=0&regIp=tiare.sysnux.pf&regPort=0&backupRegIp=0.0.0.0&backupRegPort=0&registrationPeriod=0&centraconf=&explicitMWISubscription=1&explicitMWISubscriptionPeriod=10&AFESubscriptionPeriod=3600&sessionTimer=0&t1Timer=0&t2Timer=0&transTimer=4000&transportProtocol=1&sipLocalPort=5060&sipLocalTLSPort=5061&regRetry=1800&regTimeout=120&regRenewal=15&blfPeriod=3600&acdPeriod=3600&blaPeriod=300&blacklistDur=300&park+pickup+config=&rtpPort=3000&useNTE=1&dtmfMethod=0&srtpMode=0&codec1=-3&codec2=-1&codec3=-1&codec4=-1&codec5=-1&codec6=-1&codec7=-1&codec8=-1&codec9=-1&codec10=-1&ptime=30&silenceSuppression=1&adNumber=&adTimeout=0'

   phonebook_url=None, syslog_server=None
      '''

      log.debug('company=%s, sip_display_name=%s, exten=%s' % (default_company, sip_display_name, exten))
      self.config_url = config_url

      screen_name = default_company
      if exten:
        screen_name += ' ' + exten
      data = deepcopy(self.global_sip_settings)
      for k, v in (('screenName', screen_name),
                   ('screenName2', sip_display_name),
                   ('userName', sip_user),
                   ('dispName', exten),
                   ('authName', sip_user),
                   ('password', pwd),
                   ('proxyIp', sip_server),
                   ('outboundProxy', sip_server),
                   ('regIp', sip_server),
                   ('registrationPeriod', 60),
                   ('regRetry', 30),
                   ('regTimeout', 120),
                   ('regRenewal', 15)):
            data[k] = v
      self.get('globalSIPsettings.html', params=data, method='POST')
      log.debug('Global SIP settings configured on %s (%s)', sip_user, exten)

      # Reboot phone
      sleep(2)
      self.reboot()
      log.debug('Phone "%s" configured on %s', sip_user, exten)

   def reboot(self):
      '''Reboot
curl 'http://192.168.10.150/reset.html'
    -H 'User-Agent: Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'
    -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    -H 'Accept-Language: fr-FR,fr;q=0.8,en;q=0.5,en-US;q=0.3'
    --compressed
    -H 'Referer: http://192.168.10.150/reset.html'
    -H 'Content-Type: application/x-www-form-urlencoded'
    -H 'DNT: 1'
    -H 'Authorization: Basic QWRtaW46MjIyMjI='
    -H 'Connection: keep-alive'
    -H 'Upgrade-Insecure-Requests: 1' 
    --data 'resetOption=0'
'''
      self.get('reset.html', params={'resetOption': 0}, method='POST')
      mac = self.mac.replace(':','').upper()
      log.debug('%s should be rebooting...',  mac)
      return 'OK'

