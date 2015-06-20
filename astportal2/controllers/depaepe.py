# -*- coding: utf-8 -*-

from tg import expose, request, redirect
from tg.decorators import use_custom_format

from sqlalchemy import or_

from astportal2.model import DBSession, Phonebook, User, Phone
from astportal2.lib.app_globals import Globals
from astportal2.lib.base import BaseController

from tg import config
default_company = config.get('company')
default_cid = config.get('default_cid')

import logging
log = logging.getLogger(__name__)

from time import sleep
default_company = config.get('company')

import re
re_model = re.compile('GXP(\d{4})(.*)$')
re_mac = re.compile('(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})$')
re_db = re.compile(r'(\w*)\s*: (\S*)')
cf_types = dict(CFIM = u'immédiat',
      CFUN = u'sur non réponse',
      CFBS = u'sur occupation',
      CFVM = u'messagerie vocale',
      )


def phone_details():
      ''' Try to find phone model and user from request: user agent, or ip
      '''

#      if Globals.manager is not None:
#         # Refresh Asterisk peers
#         Globals.manager.sippeers()
#         sleep(2) # Give time to sippeers to return data

      mac = model = phone = None
      try:
         m = re_model.search(request.environ['HTTP_USER_AGENT'])
         model, mac = m.groups()
         if mac != '':
            m = re_mac.search(mac)
            mac = ':'.join(m.groups()) if m is not None else None

      except:
         log.error(u'gs_phonebook_xml: could not parse UA from env="%s"' % request.environ)

      if mac is not None:
         try:
            phone = DBSession.query(Phone).filter(Phone.mac==mac).one()
            log.warning(u'mac "%s" -> phone %s)' % ( mac, phone))

         except:
            log.error(u'gs_phonebook_xml: phone or user not found, From "%s" by "%s" @ %s.' % (
                     mac, request.environ['HTTP_USER_AGENT'], request.environ['REMOTE_ADDR']))

      else:
         if phone is None:
            # Some GXPs (2130, 2160) do not send mac address in header, try to find by IP
            ip = request.environ.get('HTTP_X_FORWARDED_FOR', 'xxx')
            for peer in Globals.asterisk.peers:
               if 'Address' in Globals.asterisk.peers[peer] and \
                     ip == Globals.asterisk.peers[peer]['Address']:
                  try:
                     phone = DBSession.query(Phone).filter(Phone.sip_id==peer[4:]).one()
                     log.warning(u'ip %s -> peer %s -> user %s' % (ip, peer, phone))
                  except:
                     log.error(u'gs_phonebook_xml: ip %s found but peer %s does not exist.' % (
                        ip, peer))
                     user = None
                  break

      return phone, model


class Depaepe_ctrl(BaseController):


   @expose()
   def _default(self, *args):

      log.error(u'_default: request=%s' % request.environ)

      return ''


   @expose(content_type='text/xml; charset=utf-8')
   def phonebook(self):
      ''' Export phonebook to Depaepe XML phonebook format
      '''

      phone, model = phone_details()
      log.debug('Depaepe phonebook: model "%s", phone "%s"' % (model, phone))

      xml = '<?xml version="1.0" encoding="utf-8"?>\n<IPPhoneDirectory>\n'

      # Fist, look for entries in phonebook...
      list = DBSession.query(Phonebook). \
         filter( or_(Phonebook.phone1!=None,
               Phonebook.phone2!=None,
               Phonebook.phone3!=None))

      # Check privacy
      if phone is not None and phone.user is not None:
         list = list.filter(or_(Phonebook.user_id==phone.user.user_id,
            Phonebook.private==False))
      else:
         list = list.filter(Phonebook.private==False)

      # Then sort
      list = list.order_by(Phonebook.lastname, Phonebook.firstname)

      total = 0

      for e in list:
         if e.phone1 is None:
            continue

         if e.phone1:
            total +=1
            xml += '''<DirectoryEntry>
<Name>%s %s</Name>
<Telephone>%s</Telephone>''' % (e.lastname, e.firstname, e.phone1)

         if e.phone2:
            xml += '<Telephone2>%s</Telephone2>' % e.phone2

         if e.phone3:
            xml += '<Telephone3>%s</Telephone3>' % e.phone3

         xml += '</DirectoryEntry>'

      # ...then add users
      list = DBSession.query(User).\
         filter(User.phone!=None)
      list = list.order_by(User.lastname)
#         filter(User.phone!=None).\
#         filter(User.display_name!='')
#      list = list.order_by(User.display_name)

      for e in list:
         if e.phone[0].hide_from_phonebook:
            continue
         xml += '''<DirectoryEntry>
<Name>%s %s</Name>
<Telephone>%s</Telephone>
</DirectoryEntry>''' % (e.lastname, e.firstname, e.phone[0].exten)

      xml += '</IPPhoneDirectory>\n'

      return xml.encode('utf-8', 'replace')

