# -*- coding: utf-8 -*-

from tg import config, expose, flash
from tg.controllers import TGController
from tgext.menu import navbar, sidebar, menu

from repoze.what.predicates import in_group, in_any_group

from astportal2.model import DBSession, Phone
from astportal2.lib.app_globals import Globals

from time import sleep
import copy
import unicodedata

import logging
log = logging.getLogger(__name__)


class CC_Monitor_ctrl(TGController):
 
   @sidebar(u'-- Groupes d\'appels || Surveillance', sortorder = 11,
      icon = '/images/astronomy_section.png')
   @expose(template="astportal2.templates.cc_monitor")
   def index(self):
      '''
      '''
      Globals.manager.send_action({'Action': 'QueueStatus'})
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
      if not in_any_group(*sv):
         auth = 0
         flash(u'Accès interdit !', 'error')
      else:
         auth=1
      return dict( title=u'\u00C9tat des groupes d\'appels', debug='', auth=auth)


   @expose('json')
   def list_exten(self):
      ''' List exten for adding members to a queue
      '''
      # Refresh Asterisk peers
      Globals.manager.sippeers()

      phones = []
      for p in DBSession.query(Phone).order_by(Phone.exten):
         if p.exten is None: continue
         exten = p.exten
         if p.user: exten += ' (%s)' % p.user.display_name
         phones.append([p.phone_id, exten])
      log.debug(phones)
      return dict(phones=phones)


   @expose('json')
   def add_member(self, queue, member, priority):
      ''' Add a member with given priority to a queue
      '''
      log.info('Adding member "%s" to queue "%s"', member, queue)
      p = DBSession.query(Phone).get(member)

      if p.sip_id is not None and 'SIP/'+p.sip_id in Globals.asterisk.peers:
         iface = 'SIP/' + p.sip_id
      elif p.exten is not None and 'SIP/'+p.exten in Globals.asterisk.peers:
         iface = 'SIP/' + p.exten
      else:
         log.error('%s:%s not registered, not adding member ?' % (p.sip_id, p.exten))
         return dict(res='ko')

      user = p.user.display_name if p.user else p.exten

      Globals.manager.send_action({'Action': 'QueueAdd', 'Queue': queue, 
         'Interface': iface, 'Priority': priority, 
         'MemberName':
         unicodedata.normalize('NFKD', user).encode('ascii', 'ignore')})
      return dict(res='ok')


   @expose('json')
   def remove_member(self, queue, member, iface):
      ''' Remove a member from a queue
      '''
      log.info('Removing member "%s" from queue "%s"', member, queue)
      Globals.manager.send_action({'Action': 'QueueRemove', 
         'Queue': queue, 'Interface': iface})
      return dict(res='ok')


   @expose('json')
   def update_queues(self, last):
      ''' Function called on AJAX request made by template.
      Return when new updates available, or timeout
      '''
      last = float(last) or 0 # Last template refresh (0 -> page loaded)
      i = 0
      change = False
      queues = copy.deepcopy(Globals.asterisk.queues)
      for i in xrange(50):
         last_update = float(Globals.asterisk.last_queue_update)
         if last_update > last:
#            log.debug(Globals.asterisk.queues)
#            log.debug(Globals.asterisk.members)
            if queues != Globals.asterisk.queues or last == 0:
               change = True
               break
            else:
               last = last_update
         sleep(1)
      log.debug(' * * * update_queues returns after sleeping %d sec, change=%s' % (i,change))

      if in_group('admin'):
         queues = Globals.asterisk.queues
      else:
         queues = {}
         for q in Globals.asterisk.queues:
            if in_group('SV ' + q):
               queues[q] = Globals.asterisk.queues[q]

      return dict(last=last_update, change=change, 
            queues=queues, members=Globals.asterisk.members)

