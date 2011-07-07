# -*- coding: utf-8 -*-

from tg import config, expose
from tg.controllers import TGController
from tgext.menu import navbar, sidebar, menu

from repoze.what.predicates import in_group

from astportal2.model import DBSession, Phone
from astportal2.lib.app_globals import Globals

from time import sleep

import logging
log = logging.getLogger(__name__)


class CC_Monitor_ctrl(TGController):
 
   allow_only = in_group('admin',msg=u'Veuiller vous connecter pour continuer')

   @sidebar(u'-- Groupes d\'appels || Surveillance', sortorder = 11,
      icon = '/images/astronomy_section.png')
   @expose(template="astportal2.templates.cc_monitor")
   def index(self):
      '''
      '''
      Globals.manager.send_action({'Action': 'QueueStatus'})
      return dict( title=u'Etat des groupes d\'appels', debug='')


   @expose('json')
   def list_exten(self):
      phones = []
      for p in DBSession.query(Phone).order_by(Phone.exten):
         exten = p.exten
         if p.user: exten += ' (%s)' % p.user.display_name
         phones.append([p.phone_id, exten])
      log.info(phones)
      return dict(phones=phones)


   @expose('json')
   def add_member(self, queue, member):
      log.info('Adding member "%s" to queue "%s"', member, queue)
      p = DBSession.query(Phone).get(member)
      if p.sip_id is not None and 'SIP/'+p.sip_id in Globals.asterisk.peers:
         iface = 'SIP/' + p.sip_id
      elif p.exten is not None and 'SIP/'+p.exten in Globals.asterisk.peers:
         iface = 'SIP/' + p.exten
      else:
         log.warning('%s:%s not registered ?' % (p.sip_id, p.exten))
         iface = 'SIP/' + p.sip_id

      Globals.manager.send_action({'Action': 'QueueAdd', 'Queue': queue, 'Interface': iface})
      return dict(res='ok')
#Action: QueueRemove
#Queue: Autor_MIL
#Interface: SIP/jdg



   @expose('json')
   def update_queues(self, last):
      ''' Function called on AJAX request made by template.
      Return when new updates available, or timeout
      '''
      last = float(last) or 0;
      i = 0
      for i in xrange(50):
         sleep(1)
         last_update = float(Globals.asterisk.last_update)
         if last_update > last: break
      log.debug('monitor returns after sleeping %d sec', i)
      log.debug(Globals.asterisk.queues)
      log.debug(Globals.asterisk.members)
      return dict(last_update=last_update,
         queues=Globals.asterisk.queues, members=Globals.asterisk.members)

