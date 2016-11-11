# -*- coding: utf-8 -*-

import logging
log = logging.getLogger(__name__)
from time import time, sleep
from os import system, popen #, rename

import urllib, json
import xml.etree.ElementTree as ET
from struct import pack, unpack

from tg import config
default_company = config.get('company')

class Cisco(object):


   def __init__(self, host, mac, pwd='admin'):
      self.host = host
      self.mac = mac
      self.pwd = pwd
      self.type = 0
      self.sid = None
      self.url = 'http://%s/' % host
      self.vendor = 'Cisco'
      self.model = None
      self.ip = None
      self.netmask = None
      self.gateway = None
      self.dns1 = None
      self.dns2 = None
      self.ntp1 = None
      self.ntp2 = None

   def get(self, action, params=None):
      if params:
         params = urllib.urlencode(params)

      try:
         resp = urllib.urlopen(self.url + action, params)
         log.debug('Request %s, params %s returns code %s' % (\
               self.url + action, params, resp.getcode()))
      except:
         log.warning('Request %s, params %s failed' % (\
               self.url + action, params))
         return None
      return resp.read()

   def login(self, pwd=None):
      return True

   def infos(self):
      spacfg = ET.fromstring(self.get('admin/spacfg.xml'))
      model = spacfg.find('Product_Name').text
      soft = spacfg.find('Software_Version').text
      self.model = model
      log.debug(u'Model <%s>'% model)
      log.debug(u'Version <%s>'% soft)

      self.ip = spacfg.find('Current_IP').text
      self.netmask = spacfg.find('Current_Netmask').text
      self.gateway = spacfg.find('Current_Gateway').text
      self.dns1 = spacfg.find('Primary__DNS').text
      self.dns2 = spacfg.find('Secondary__DNS').text
      self.ntp1 = spacfg.find('Primary_NTP_Server').text
      self.ntp2 = spacfg.find('Secondary_NTP_Server').text

      return {'model': model, 'version': soft}

   def configure(self, pwd, tftp_dir, firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None, dns1=None, dns2=None,
         sip_server=None, sip_user=None, sip_display_name=None,
         mwi_subscribe=False, reboot=True, screen_url=None, exten=None):
      '''Parameters: firmware_url, config_url, ntp_server,
         phonebook_url=None, syslog_server=None
      '''

      log.debug('company=%s, sip_display_name=%s, exten=%s' % (default_company, sip_display_name, exten))
      self.config_url = config_url
      ET.register_namespace('', 'http://www.sipura.net/xsd/SPA50x-30x-SIP')
      xml = ET.parse('/opt/astportal3/astportal2/templates/spa504g-v7.5.5.xml')
#      for e in xml.getiterator():
#         log.debug('%s -> %s' % (e.tag, e.attrib))
      ns = '{http://www.sipura.net/xsd/SPA50x-30x-SIP}'

      # SIP settings
      xml.find(ns + 'Proxy_1_').text = sip_server
      xml.find(ns + 'User_ID_1_').text = sip_user
      xml.find(ns + 'Auth_ID_1_').text = sip_user
      xml.find(ns + 'Password_1_').text = pwd
      xml.find(ns + 'Display_Name_1_').text = sip_display_name
      xml.find(ns + 'Default_Character_Encoding').text = 'UTF-8'
      xml.find(ns + 'Locale').text = 'fr-FR'
      xml.find(ns + 'Language_Selection').text = 'French'
      xml.find(ns + 'Dictionary_Server_Script').text = 'Dictionary_Server_Scriptua="na"serv=http://192.168.0.1/language/;d0=English;x0=spa50x_30x_en_v754.xml;d1=French;x1=spa50x_30x_fr_v754.xml;/Dictionary_Server_Script'
      xml.find(ns + 'Time_Zone').text = 'GMT-10:00'
      xml.find(ns + 'Time_Format').text = '24hr'
      xml.find(ns + 'Date_Format').text = 'day/month'
      xml.find(ns + 'Station_Display_Name').text = default_company
      xml.find(ns + 'Text_Logo').text = sip_display_name
      xml.find(ns + 'Select_Background_Picture').text = 'Text Logo'
      xml.find(ns + 'Block_ANC_Serv').text = 'no'
      xml.find(ns + 'Block_CID_Serv').text = 'no'
      xml.find(ns + 'Group_Paging_Script').text = ''
      xml.find(ns + 'Voice_Mail_Number').text = '*79'

      # LDAP configuration
      xml.find(ns + 'LDAP_Dir_Enable').text = 'Yes'
      xml.find(ns + 'LDAP_Corp_Dir_Name').text = 'MYLDAP'
      xml.find(ns + 'LDAP_Server').text = '192.168.0.2'
      xml.find(ns + 'LDAP_Auth_Method').text = 'Simple'
      xml.find(ns + 'LDAP_Client_DN').text ='CN=Users,DC=SYSNUX,DC=PF'
      xml.find(ns + 'LDAP_Username').text = ''
      xml.find(ns + 'LDAP_Password').text = ''
      xml.find(ns + 'LDAP_Search_Base').text = 'ou=SYSNUX,DC=SYSNUX,DC=PF'
      xml.find(ns + 'LDAP_Last_Name_Filter').text = 'sn:(sn=*$VALUE*)'
      xml.find(ns + 'LDAP_First_Name_Filter').text = 'cn:(cn=*$VALUE*)'
      xml.find(ns + 'LDAP_Display_Attrs').text = 'a=cn;a=sn;a=telephoneNumber,t=p;'
      xml.find(ns + 'Group_Paging_Script').text = ''
      xml.find(ns + 'DNS_Server_Order').text = 'DHCP,Manual'
      xml.find(ns + 'DNS_Query_Mode').text = 'Sequential'

      # Static IP configuration
      xml.find(ns + 'Connection_Type').text = 'Static IP'
      xml.find(ns + 'Static_IP').text = self.ip
      xml.find(ns + 'NetMask').text = self.netmask
      xml.find(ns + 'Gateway').text = self.gateway
      xml.find(ns + 'Primary_DNS').text = self.dns1
      xml.find(ns + 'Secondary_DNS').text = self.dns2
      xml.find(ns + 'Primary_NTP_Server').text = self.ntp1
      xml.find(ns + 'Secondary_NTP_Server').text = self.ntp2

      if exten is not None:
         xml.find(ns + 'Short_Name_1_').text = exten
         xml.find(ns + 'Short_Name_2_').text = exten
         xml.find(ns + 'Short_Name_3_').text = exten
         xml.find(ns + 'Short_Name_4_').text = exten
      '''
<BMP_Picture_Download_URL group="Phone/General">http://192.168.0.1/images/ying-yang.bmp</BMP_Picture_Download_URL>
<Select_Logo group="Phone/General">Text Logo</Select_Logo>
<Select_Background_Picture group="Phone/General">BMP Picture</Select_Background_Picture>
      root = xml.getroot()
      root.remove(xml.find(ns + 'Connection_Type'))
      root.remove(xml.find(ns + 'Use_Backup_IP'))
      root.remove(xml.find(ns + 'Static_IP'))
      root.remove(xml.find(ns + 'NetMask'))
      root.remove(xml.find(ns + 'Gateway'))
      root.remove(xml.find(ns + 'Primary_DNS'))
      root.remove(xml.find(ns + 'Secondary_DNS'))
      root.remove(xml.find(ns + 'Primary_NTP_Server'))
      root.remove(xml.find(ns + 'Secondary_NTP_Server'))
      '''

      name = tftp_dir + '/phones/config/SEP%s.cnf.xml' % self.mac.replace(':','').upper()
      try:
         xml.write(name)
         log.debug('XML file written to "%s"' % name)
      except:
         log.error('ERROR: write text config file "%s"' % name)

      # Reboot phone
      sleep(3)
      self.reboot()

   def reboot(self):
      # Reboot
      # http://ip_spa/admin/resync?tftp://ip_server/phones/config/SEP1CDF0F4B0616.cnf.xml
      mac = self.mac.replace(':','').upper()
      self.get('admin/resync?tftp://%s/SEP%s.cnf.xml' % (self.config_url, mac))
      log.debug('Reboot (%s -> %s)...' % (self.config_url, mac))
      return 'OK'

