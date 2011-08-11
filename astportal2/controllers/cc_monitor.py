# -*- coding: utf-8 -*-

from tg import config, expose, flash, request
from tg.controllers import TGController
from tgext.menu import navbar, sidebar, menu

from repoze.what.predicates import in_group, in_any_group

from astportal2.model import DBSession, Phone, Record, Queue
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

      if Globals.manager is None:
         flash(u'Vérifier la connexion Asterisk', 'error')
      else:
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
   def add_member(self, queue, member, penality):
      ''' Add a member with given priority to a queue
      '''
      log.info('Adding member "%s" to queue "%s", penality %s' % (member, queue, penality))
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
         'Interface': iface, 'Penalty': penality,
         'MemberName':
         unicodedata.normalize('NFKD', user).encode('ascii', 'ignore')})
      return dict(res='ok')


   @expose('json')
   def remove_member(self, queue, member, iface):
      ''' Remove a member from a queue
      '''
      log.info('Removing member "%s (%s)" from queue "%s"', member, iface, queue)
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
            break
#            log.debug(Globals.asterisk.queues)
#            log.debug(Globals.asterisk.members)
            if queues != Globals.asterisk.queues or last == 0:
               change = True
               break
            else:
               last = last_update
         sleep(1)
      log.debug(' * * * update_queues returns after sleeping %d sec, change=%s' % (i,change))

#      log.debug('QUEUES : %s' % queues)
#      log.debug('MEMBERS : %s' % Globals.asterisk.members)
      if in_group('admin'):
         queues = Globals.asterisk.queues
      else:
         queues = {}
         for q in Globals.asterisk.queues:
            if in_group('SV ' + q):
               queues[q] = Globals.asterisk.queues[q]

      return dict(last=last_update, change=True, # XXX
            queues=queues, members=Globals.asterisk.members)


   @expose('json')
   def listen(self, channel):
      '''Listen queue member

action: originate
channel: SIP/Nn5ydYzs
application: chanspy
data: SIP/Xx83G1ZQ
      '''
      if len(request.identity['user'].phone)<1:
         log.debug('ChanSpy from user %s to %s : no extension' % (
            request.identity['user'], channel))
         return dict(status=2)
      sip = request.identity['user'].phone[0].sip_id
      log.debug('ChanSpy from user %s (%s) to %s' % (
         request.identity['user'], sip, channel))
      res = Globals.manager.originate(
            'SIP/' + sip, # Channel
            sip, # Extension
            application = 'ChanSpy',
            data = channel,
            )
      log.debug(res)
      status = 0 if res=='Success' else 1
      return dict(status=status)


   @expose('json')
   def record(self, channel, queue):
      '''Record a queue member

Action: Monitor
Mix: 1
File: test
Channel: SIP/pEpSNlcv-000001b9
   '''
      for cha in Globals.asterisk.channels.keys():
         if cha.startswith(channel):
            uid = Globals.asterisk.channels[cha]['Uniqueid']
            break
      else:
         log.warning('No active channel for %s ?' % channel)
         return dict(status=0)

      f = 'rec-%s' % uid
      res = Globals.manager.send_action(
            {  'Action': 'Monitor',
               'Mix': 1,
               'Channel': cha,
               'File': f})

      log.info('Record request from user %s to channel %s returns %s' % ( 
         request.identity['user'], cha, res))

      m = DBSession.query(Phone).filter(Phone.sip_id==channel[-8:]).one()
      q = DBSession.query(Queue).filter(Queue.name==queue).one()
      u = DBSession.query(User).filter(User.user_name==request.identity['repoze.who.userid']).one()

      r = Record()
      r.uniqueid = uid
      r.queue_id = q.queue_id
      r.member_id = m.user_id
      r.user_id = u.user_id
      DBSession.add(r)

      status = 0 if res=='Success' else 1
      return dict(status=status)

