# -*- coding: utf-8 -*-

from tg import config, expose, flash, request, redirect
from tg.controllers import TGController
from tgext.menu import navbar, sidebar, menu

from repoze.what.predicates import in_group, in_any_group

from astportal2.model import DBSession, Phone, Record, Queue, User, Group
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
         sv.append('AG ' + q)
      if not in_any_group(*sv):
         auth = 0
         flash(u'Accès interdit !', 'error')
         redirect('/')
      else:
         auth=1
      return dict( title=u'\u00C9tat des groupes d\'appels', debug='', auth=auth)


   @expose('json')
   def list_exten(self, queue):
      ''' List users for adding members to a queue
      Users must belong to special group "AG queue_name" to be listed
      '''
      # Refresh Asterisk peers
      Globals.manager.sippeers()

      phones = []
#      if queue=='__ALL__':
#         users = set(DBSession.query(User).all())
#         for g in DBSession.query(Group).filter(Group.group_name.like('AG %')):
#            users = users & g.users
#            log.debug(u'Users & %s: %s' % (g.group_name, users))

      try:
         g = DBSession.query(Group).filter(Group.group_name=='AG %s' % queue).one()
         for u in g.users:
            for p in u.phone:
               phones.append([p.phone_id, '%s (%s)' % (u.display_name, p.exten)])
      except:
         log.warning('Queue %s not found?' % queue)

      log.debug('Member of queue %s : %s' % (queue, phones))
      return dict(phones=phones)


   @expose('json')
   def add_member(self, queue, member, penality):
      ''' Add a member with given priority to a queue
      '''
      log.info('Adding member "%s" to queue "%s", penality %s' % (member, queue, penality))
      p = DBSession.query(Phone).get(member)

      if p.sip_id is not None and 'SIP/'+p.sip_id in Globals.asterisk.peers:
         iface = p.sip_id
      elif p.exten is not None and 'SIP/'+p.exten in Globals.asterisk.peers:
         iface = p.exten
      else:
         log.error('%s:%s not registered, not adding member ?' % (p.sip_id, p.exten))
         return dict(res='ko')

      user = p.user.display_name if p.user else p.exten
      iface = 'SIP/%s' % iface

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
   def update_queues(self, last=0):
      ''' Function called on AJAX request made by template.
      Return when new updates available, or timeout
      '''
      last = int(last) # Last template refresh (0 -> page just loaded)
      change = False
      queues = copy.deepcopy(Globals.asterisk.queues)
      members = copy.deepcopy(Globals.asterisk.members)
#      log.debug('Q BEFORE %s' % Globals.asterisk.queues)
#      log.debug('M BEFORE %s' % Globals.asterisk.members)
      for i in xrange(50):
         last_update = int(Globals.asterisk.last_queue_update)
         if last_update > last:
            break
            if queues != Globals.asterisk.queues or \
                  members != Globals.asterisk.members or last == 0:
               change = True
               break
            else:
               last = last_update
         sleep(1)
      log.debug(' * * * update_queues returns after sleeping %d sec, change=%s' % (i,change))

      admin = False
      if in_group('admin'):
         queues = Globals.asterisk.queues
         admin = True
      else:
         queues = {}
         for q in Globals.asterisk.queues:
            if in_group('SV ' + q):
               queues[q] = Globals.asterisk.queues[q]
               admin = True
            elif in_group('AG ' + q):
               queues[q] = Globals.asterisk.queues[q]

      log.debug('Q AFTER %s' % Globals.asterisk.queues)
      log.debug('M AFTER %s' % Globals.asterisk.members)

      me = unicodedata.normalize('NFKD', request.identity['user'].display_name).encode('ascii', 'ignore')

#      qq = [(k, queues[k]) for k in sorted(queues, key=lambda x: int(queues[x]['Weight']), reverse=True)]
      return dict(last=last_update, change=True, # XXX
            queues=queues, members=Globals.asterisk.members, me=me, admin=admin)


   @expose('json')
   def update_queues2(self, last=0):
      ''' Function called on AJAX request made by template.
      Return when new updates available, or timeout
      '''
      last = int(last) # Last template refresh (0 -> page just loaded)
      log.debug('New request, last=%d' % last)
      change = False
      queues = copy.deepcopy(Globals.asterisk.queues)
      for i in xrange(50):
         last_update = float(Globals.asterisk.last_queue_update)
         if int(last_update*100) > last:
            break
            if queues != Globals.asterisk.queues or last == 0:
               change = True
               break
            else:
               last = last_update
         sleep(1)
      log.debug('Sending response, last=%s' % last_update)
      last_update = int(last_update*100)
      return dict(last=last_update, change=True, # XXX
            queues=Globals.asterisk.queues)


   @expose('json')
   def spy(self, name, channel):
      '''Listen queue member

action: originate
channel: SIP/Nn5ydYzs
application: chanspy
data: SIP/Xx83G1ZQ
      '''
      log.debug('Listen %s (%s)' % (name, channel))
      phones = DBSession.query(User).filter(User.user_name==request.identity['repoze.who.userid']).one().phone
      if len(phones)<1:
         log.debug('ChanSpy from user %s to %s : no extension' % (
            request.identity['user'], channel))
         return dict(status=2)

      sip = phones[0].sip_id
      log.debug('ChanSpy from user %s (%s) to %s' % (
         request.identity['user'], sip, channel))
      res = Globals.manager.originate(
            'SIP/' + sip, # Channel
            sip, # Extension
            application = 'ChanSpy',
            data = channel,
            )

      if res.get_header('Response')=='Success':
         status = 0
         Globals.asterisk.members[name]['Spied'] = True
      else:
         status = 1
      return dict(status=status)


   @expose('json')
   def record(self, name, channel, queue):
      '''Record a queue member

Action: Monitor
Mix: 1
File: test
Channel: SIP/pEpSNlcv-000001b9
   '''
      log.debug('Record %s (%s)' % (name, channel))
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

      log.info('Record request from user "%s" to channel %s returns "%s"' % ( 
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

      if res.get_header('Response')=='Success':
         status = 0
         Globals.asterisk.members[name]['Recorded'] = True
         log.debug(Globals.asterisk.members)
      else:
         status = 1
      return dict(status=status)

