# -*- coding: utf-8 -*-
# API controller!

from tg import expose, flash, redirect, tmpl_context
from tgext.menu import sidebar

import logging
log = logging.getLogger(__name__)
import re

from astportal2.lib.app_globals import Globals
from astportal2.lib.base import BaseController
from astportal2.controllers.application import generate_dialplan

re_db = re.compile(r'(\w*)\s*: (\S*)')

class API_ctrl(BaseController):


   @expose('json')
   def index(self, **kw):
      ''' 
      '''
      return {'erreur': 'route', 'params': kw}

   @expose('json')
   def click_to_call(self, exten, dst, **kw):
      ''' API click to call
      '''

      try:
         phone = DBSession.query(Phone).filter(Phone.exten == exten).one()
      except:
         return {'erreur': 'exten', 'exten': exten, 'dst': dst}
      log.debug('Call from %s to %s', phone, dst)
      channel = phone.sip_id.encode('iso-8859-1')
      res = Globals.manager.originate('PJSIP/' + channel, # Channel
                                      dst.encode('iso-8859-1'), # Extension
                                      context=channel,
                                      priority='1',
                                      caller_id=exten)
      log.debug('Originate returns %s', res)
      return {'erreur': res, 'exten': exten, 'dst': dst}

   @expose()
   def update_svi(self):
      res = generate_dialplan()
      Globals.manager.send_action({'Action': 'Command', 'Command': 'dialplan reload'})
      return str(res)
