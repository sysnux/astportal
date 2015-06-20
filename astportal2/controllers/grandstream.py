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


def check_call_forwards(phone):
      ''' Phone should indicate if it is forwarded.
      Phone could display who is forwarded to it.
      '''

      exten = phone.exten
      sip = phone.sip_id
      cfs_out = []
      cfs_in = []

      man = Globals.manager.command('database show CFIM')
      for i,r in enumerate(man.response[3:-2]):
         log.debug(u'[%d] %s' % (i, r))
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            if k==sip:
               cfs_out.append(('CFIM', v))
            if v==exten:
               cfs_in.append(('CFIM', k))

#      man = Globals.manager.command('database show CFBS')
#      for i,r in enumerate(man.response[3:-2]):
#         match = re_db.search(r)
#         if match:
#            k, v = match.groups()
#            if k in sip2ext.keys():
#               cfs.append((sip2ext[k], 'CFBS', v))
#      man = Globals.manager.command('database show CFUN')
#      for i,r in enumerate(man.response[3:-2]):
#         match = re_db.search(r)
#         if match:
#            k, v = match.groups()
#            if k in sip2ext.keys():
#               cfs.append((sip2ext[k], 'CFUN', v))
#      man = Globals.manager.command('database show CFVM')
#      for i,r in enumerate(man.response[3:-2]):
#         match = re_db.search(r)
#         if match:
#            k, v = match.groups()
#            if k in sip2ext.keys():
#               cfs.append((sip2ext[k], 'CFVM', v))

      return cfs_out, cfs_in # XXX


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
         log.error(u'Could not parse UA from env="%s"' % request.environ)

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


class Grandstream_ctrl(BaseController):


   @expose()
   def _default(self, *args):

      if request.environ['PATH_INFO'].startswith('/grandstream/phonebook/'):
         redirect('/grandstream/gs_phonebook')

      elif request.environ['PATH_INFO'].startswith('/grandstream/screen/'):
         redirect('/grandstream/gs_screen')

      else:
         log.error(u'_default: request=%s' % request.environ)
         log.error(args)

      return ''


   @expose(content_type='text/xml; charset=utf-8', 
      custom_format='gxp2120',
      template='mako:astportal2.templates.2120idle_screen')
   @expose(content_type='text/xml; charset=utf-8', 
      custom_format='gxp1450',
      template='mako:astportal2.templates.1450idle_screen')
   @expose(content_type='text/xml; charset=utf-8', 
      custom_format='gxp116x',
      template='mako:astportal2.templates.116xidle_screen')
   @expose(content_type='text/xml; charset=utf-8', 
      custom_format='gxp2000',
      template='mako:astportal2.templates.2000idle_screen')
   def gs_screen(self):
      ''' XML idle screen

      Generate custom XML idle screen for GXP phones.
      Reload from phone can be forced with SIP notification, e.g:
         sudo asterisk -rx 'sip notify grandstream-idle-screen-refresh ugeHE96B'
      /etc/asterisk/sip_notify.conf should include:
         [grandstream-idle-screen-refresh]
         Event=>x-gs-screen
      '''

      phone, model = phone_details()
      if model is None:
         log.error(u'Grandstream screen: not a Grandstream phone?')
         return ''

      log.debug('Grandstream screen: model "%s", phone "%s"' % (model, phone))

      if model == '2120':
         use_custom_format(self.gs_screen, 'gxp2120')

      if model == '2000':
         use_custom_format(self.gs_screen, 'gxp2000')

      elif model =='1450':
         use_custom_format(self.gs_screen, 'gxp1450')

      elif model.startswith('116'):
         use_custom_format(self.gs_screen, 'gxp116x')

      else:
         log.error(u'Grandstream screen: unknown model "%s"' % (model))
         return ''

      if phone is not None:
         exten = phone.exten if phone.exten is not None else '?'
         if phone.user is not None:
            ascii_name = phone.user.ascii_name
            display_name = phone.user.display_name
         else:
            ascii_name = display_name = ''
         cfs_out, cfs_in = check_call_forwards(phone)
         if cfs_out:
            log.debug('Call forward out: %s' % cfs_out)
            exten += ' > ' + ', '.join([x[1] for x in cfs_out])
         else:
            cfs_out = u''

         if cfs_in:
            phones_in = DBSession.query(Phone). \
               filter(Phone.sip_id.in_([x[1] for x in cfs_in])).all()
            log.debug('Call forward in: %s' % phones_in)
            cfs_in = u' < '
#            if phones_in.count() > 1:
#               cfs_in = u'Renvoyés : '
#            else:
#               cfs_in = u'Renvoyé : '
            cfs_in += u', '.join([p.exten for p in phones_in])
         else:
            cfs_in = u''

      else:
         exten = name = '?'
         cfs_in = u''
         cfs_out = []

      return dict(
         a=exten, # Compte
         A='$A', # Key labels
         f='$f', T='$T', # Date / time
         b='%s %s%s' % (default_company, exten, cfs_in),
         CFS_IN = cfs_in,
         I = display_name, ascii_name = ascii_name, display_name = display_name,
         exten=exten,
         c='$c', # missed calls
         G='GGG', Stock='SSS', Currency='CCC',
         j='JJJ', v='vvv', L='LLL', S='SSS', g='ggg', w='www', x='xxx' )
#      return dict(a='101', A='$A', f='$f', T='$T', b='$b', I='$I', j='JJJ', c='$c', v='$v', 
#         L='$L', S='$S', g='$g', w='$w', x='$x' )


   @expose(content_type='text/xml; charset=utf-8')
   def gs_phonebook(self):
      ''' Export phonebook to Grandstream XML phonebook format
      '''

      phone, model = phone_details()
      log.debug('Grandstream phonebook: model "%s", phone "%s"' % (model, phone))

      xml = '<?xml version="1.0" encoding="utf-8"?>\n<AddressBook>\n'

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
         if e.phone1:
            total +=1
#            if model=='1200' and total >= 100:
#               break
            xml += '''<Contact>
<LastName>%s</LastName>
<FirstName>%s</FirstName>
  <Phone>
   <phonenumber>%s</phonenumber>
   <accountindex>0</accountindex>
  </Phone>
</Contact>''' % (e.lastname, e.firstname, e.phone1)

         if e.phone2:
            total +=1
            if model=='1200' and total >= 100:
               break
            xml += '''<Contact>
<LastName>%s</LastName>
<FirstName>%s</FirstName>
  <Phone>
   <phonenumber>%s</phonenumber>
   <accountindex>0</accountindex>
  </Phone>
</Contact>''' % (e.lastname, e.firstname, e.phone2)

         if e.phone3:
            total +=1
            if model=='1200' and total >= 100:
               break
            xml += '''<Contact>
<LastName>%s</LastName>
<FirstName>%s</FirstName>
  <Phone>
   <phonenumber>%s</phonenumber>
   <accountindex>0</accountindex>
  </Phone>
</Contact>''' % (e.lastname, e.firstname, e.phone3)


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
         total +=1
#         if model=='1200' and total >= 100:
#            break
         xml += '''<Contact>
<LastName>%s</LastName>
<FirstName>%s</FirstName>
  <Phone>
   <phonenumber>%s</phonenumber>
   <accountindex>0</accountindex>
  </Phone>
</Contact>''' % (e.lastname, e.firstname, e.phone[0].exten)

      xml += '</AddressBook>\n'

      return xml.encode('utf-8', 'replace')

