# -*- coding: utf-8 -*-
'''
Call Center Monitor controller

Some functionnalities depend on Asterisk configuration

[agent_connect] 
; Called from Queue() when member has accepted call, but before he is bridged
; to the caller:
;  . start monitoring and call AstPortal if needed
;  . send UserEvent so that AstPortal can open customer window (CRM) if needed
;  . give the member a few seconds to check the customer window (CRM) if needed
; On return, the member will actually be bridged to the caller
exten => s,1,Noop(uid=${UNIQUEID} mon=${MASTER_CHANNEL(MONITOR)})
   same => n,GotoIf($[${MASTER_CHANNEL(MONITOR)} != 1]?nomon)
   same => n,MixMonitor(rec-${MASTER_CHANNEL(UNIQUEID)}.wav)
   same => n,Set(mon=${CURL(http://192.168.0.200:8080/cc_monitor/auto_record,name=${MEMBERNAME}&channel=${MASTER_CHANNEL(CHANNEL)}&queue=${QUEUENAME}&uid=${MASTER_CHANNEL(UNIQUEID)}&custom1=${MASTER_CHANNEL(CUSTOM1)}&custom2=${MASTER_CHANNEL(CUSTOM2)})})
   same => n(nomon),UserEvent(AgentWillConnect,Agent: ${MEMBERNAME},HoldTime: ${QEHOLDTIME},PeerChannel: ${MASTER_CHANNEL(CHANNEL)},PeerCallerid: ${MASTER_CHANNEL(CALLERID(all))},PeerUniqueid: ${MASTER_CHANNEL(UNIQUEID)},ConnectURL: ${MASTER_CHANNEL(CONNECTURL)},HangupURL: ${MASTER_CHANNEL(HANGUPURL)},Custom1: ${MASTER_CHANNEL(CUSTOM1)},Custom2: ${MASTER_CHANNEL(CUSTOM2)})
   same => n,Wait(${MASTER_CHANNEL(CONNECTDELAY)})
   same => n,Return
'''

from tg import config, expose, flash, request, redirect
from tg.controllers import TGController
from tgext.menu import navbar, sidebar, menu

try:
   from tg.predicates import in_group, in_any_group
except ImportError:
   from repoze.what.predicates import in_group, in_any_group

from astportal2.model import DBSession, Phone, Record, Queue, User, Group
from astportal2.lib.app_globals import Globals

from time import sleep
import unicodedata

import logging
log = logging.getLogger(__name__)

sip_type = 'SIP/' if config.get('asterisk.sip', 'sip')=='sip' else 'PJSIP/'

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


   @expose(template="astportal2.templates.cc_monitor_atn")
   def atn(self):
      '''
      '''

      if Globals.manager is None:
         flash(u'Vérifier la connexion Asterisk', 'error')
      else:
         Globals.manager.send_action({'Action': 'QueueStatus'})
      return dict( title=u'\u00C9tat des groupes d\'appels', debug='', auth=1)


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
      log.debug('Member phone %s' % (p))

      if p.sip_id is not None:
         if sip_type  + p.sip_id not in Globals.asterisk.peers and \
            p.exten is not None and \
            sip_type + p.exten in Globals.asterisk.peers:
            iface = p.exten
         else:
            iface = p.sip_id
      else:
         log.error('User phone unknown, not adding member' % (p))
         return dict(res='ko')

      user = p.user.ascii_name if p.user else p.exten
      iface = sip_type + iface

      Globals.manager.send_action({'Action': 'QueueAdd', 'Queue': queue, 
         'Interface': iface, 'Penalty': penality,
         'MemberName':
         user})
      return dict(res='ok')


   @expose('json')
   def add_or_remove_all_members(self, add_or_remove):
      ''' Add or remove all agents to / from their queues
      '''

      if add_or_remove not in ('add', 'remove'):
         log.error('Wrong parameter "%s"', add_or_remove)
         return dict(res='ko')

      for q in DBSession.query(Queue):
         g = DBSession.query(Group).filter(Group.group_name=='AG %s' % q.name).one()

         for m in g.users:
            try:
               p = m.phone[0]
            except:
               continue

            if p.sip_id is not None and sip_type + p.sip_id in Globals.asterisk.peers:
               iface = p.sip_id
            elif p.exten is not None and sip_type + p.exten in Globals.asterisk.peers:
               iface = p.exten
            else:
               log.error('%s:%s not registered, not adding member!' % (p.sip_id, p.exten))
               continue

            user = p.user.ascii_name if p.user else p.exten
            iface = sip_type + iface

            if add_or_remove == 'add':
#               Globals.manager.send_action({'Action': 'QueueAdd', 'Queue': q.name, 
#                                            'Interface': iface, 'Penalty': 0,
#                                            'MemberName': user})
               log.debug('Member "%s" added to queue "%s" with phone "%s" (%s)',
                         user, q.name, p.sip_id, p.exten)
            else:
#               Globals.manager.send_action({'Action': 'QueueRemove', 
#                                            'Queue': q.name,
#                                            'Interface': iface}
               log.debug('Member "%s" removed from queue "%s" with phone "%s" (%s)',
                         user, q.name, p.sip_id, p.exten)

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
      u = DBSession.query(User).filter(User.user_name==request.identity['repoze.who.userid']).one()
      try:
         phone = u.phone[0].phone_id
      except:
         phone = None
      log.debug('User %s, phone_id=%s' % (u, phone))
      for i in xrange(50):
         last_update = int(Globals.asterisk.last_queue_update)
         if last_update > last:
            break
         sleep(1)
      log.debug('update_queues returns after sleeping %d sec, last=%f' % (i, last_update))

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


      qq = [{'name': k,
         'params': queues[k]
         } for k in sorted(queues, 
               key=lambda x: int(queues[x]['Weight']), 
               reverse=True)
         ]
      return dict(last=last_update, change=True, # XXX
            queues=qq, members=Globals.asterisk.members, admin=admin,
            my_name=u.ascii_name, my_phone=phone,
            my_groups=[g.group_name for g in u.groups])


   @expose('json')
   def update_queues2(self, last=0):
      ''' Function called on AJAX request made by template.
      Return when new updates available, or timeout
      '''
      last = float(last) # Last template refresh (0 -> page just loaded)
      log.debug('update_queues2 new request, last=%f' % last)

      for i in xrange(51):
         last_update = Globals.asterisk.last_queue_update
         if last_update > last:
            break
         sleep(1)
      log.debug('update_queues2 returns after sleeping %d sec, last=%f' % (i, last_update))

      qq = [{'name': k,
         'params': Globals.asterisk.queues[k]
         } for k in sorted(Globals.asterisk.queues, 
               key=lambda x: int(Globals.asterisk.queues[x]['Weight']), 
               reverse=True)
         ]
      return dict(last=last_update, change=True, # XXX
            queues=qq)


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
            sip_type + sip, # Channel
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


   @expose()
   def auto_record(self, name, channel, queue, uid, custom1, custom2):
      ''' Auto record
      Called from Asterisk dialplan / func_curl
      '''

      log.debug('auto_record: name %s, channel %s, queue %s, uid %s, custom1 %s, custom2 %s' % (
         name, channel, queue, uid, custom1, custom2))
      # Check channel exists, else abort
      for cha in Globals.asterisk.channels.keys():
         if cha.startswith(channel):
            unique_id = Globals.asterisk.channels[cha]['Uniqueid']
            break
      else:
         log.warning('auto_record: no active channel for %s ?' % channel)
         return '1'

      # Poor man's authentification!
      if uid!=unique_id: 
         log.warning('auto_record: unique_id "%s" != "%s"' % (unique_id, uid))
         return '1'

      # Set "recorded" flag on member
      Globals.asterisk.members[name]['Recorded'] = True

      # Insert record info into database
      r = Record()
      r.user_id = -2 # Auto_record pseudo-user!
      r.uniqueid = unique_id
      r.queue_id = DBSession.query(Queue).filter(
            Queue.name==queue).one().queue_id
      try:
         u = DBSession.query(User).filter(User.ascii_name==name).first()
         log.debug(u' * * * %s' % u)
         r.member_id = u.user_id
      except:
         r.member_id = 1
         log.error('user "%s" not found' % name)
      r.custom1 = custom1
      r.custom2 = custom2
      DBSession.add(r)

      return '0'


   @expose('json')
   def record(self, name, channel, queue, custom1=None, custom2=None):
      '''Record a queue member
         Called from call center monitor web page

Action: Monitor
Mix: 1
File: test
Channel: SIP/pEpSNlcv-000001b9
   '''
      log.debug('Record request "%s" (%s) on "%s"' % (name, channel, queue))

      # Check channel exists, else abort
      for cha in Globals.asterisk.channels.keys():
         if cha.startswith(channel):
            unique_id = Globals.asterisk.channels[cha]['Uniqueid']
            break
      else:
         log.warning('No active channel for %s ?' % channel)
         return dict(status=0)

      # XXX Authentification

      # Gather data from database
      user_id = DBSession.query(User).filter(
         User.user_name==request.identity['repoze.who.userid']).one().user_id
      member_id = DBSession.query(Phone).filter(
         Phone.sip_id==channel[-8:]).one().user_id
      queue_id = DBSession.query(Queue).filter(
            Queue.name==queue).one().queue_id

      # Create filename and send record action to Asterisk via manager
      f = 'rec-%s' % unique_id
      res = Globals.manager.send_action(
            {  'Action': 'Monitor',
               'Mix': 1,
               'Channel': cha,
               'File': f})
      log.info('Record request from userid "%s" to channel %s returns "%s"' % ( 
         user_id, cha, res))

      if res.get_header('Response')=='Success':
         status = 0
         # Set "recorded" flag on member
         Globals.asterisk.members[name]['Recorded'] = True
         # Insert record info into database
         r = Record()
         r.uniqueid = unique_id
         r.queue_id = queue_id
         r.member_id = member_id
         r.user_id = user_id
         r.custom1 = custom1
         r.custom2 = custom2
         DBSession.add(r)

      else:
         status = 1

      return dict(status=status)


   @expose(template="astportal2.templates.test_connect")
   def test_connect(self, **kw):
      ''' Function to test URL load on member answer
      '''
      return kw


   @expose(template="astportal2.templates.test_hangup")
   def test_hangup(self, **kw):
      ''' Function to test URL load on hangup
      '''
      return kw
