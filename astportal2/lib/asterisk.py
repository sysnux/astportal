# -*- coding: utf-8 -*-

from astportal2.lib.app_globals import Globals
from time import time
from gevent import sleep
import json
import unicodedata
import logging
log = logging.getLogger(__name__)

from os.path import exists
from unicodedata import normalize
from re import sub as re_sub
from astportal2.model import DBSession, Phone, User, Sound, Record
from astportal2.controllers.callback import callbacks
from tg import config
directory_asterisk = config.get('directory.asterisk')
default_dnis = config.get('default_dnis')
utils_dir = config.get('directory.utils')
sip_type = config.get('asterisk.sip', 'sip')
log.info('Asterisk SIP variant: %s', sip_type)


def asterisk_string(u, no_space=False):
   '''Convert arbitrary unicode string to a string acceptable by Asterisk

   Parameters:
      u: unicode string
      no_space: 
   '''
   u = normalize('NFKD', u).encode('ascii','ignore')
   if no_space:
      u = re_sub(r'\W', '_', u)
   return u

def asterisk_shell(cmd):
   '''Execute a shell command through Asterisk manager

   Need a special context in Asterisk dialplan:
[shell_command]
; Execute an arbitrary shell command passed through manager
; give it a few seconds for completion
exten => s,1,NoOp(Command)
exten => s,n,Answer()
exten => s,n,Wait(10)

   '''
   res = Globals.manager.originate(
      'Local/s@shell_command', # Channel
      application = 'System',
      data = cmd
   )
   log.info('System command <%s>, returns <%s>', cmd, res)
   return res


def asterisk_update_phone(p, old_exten=None, old_dnis=None):
   '''Update Asterisk configuration files

   Parameter: p=Phone object, old_exten=previous phone exten
   Files updated (if needed): sip.conf, voicemail.conf, extensions.conf
   '''

   if p.user_id:
      user = DBSession.query(User).get(p.user_id)
      cidname = user.ascii_name
   else:
      user = None
      cidname = ''

   if sip_type=='sip':
      # SIP.conf
      actions = [
            ('NewCat', p.sip_id),
            ('Append', p.sip_id, 'secret', p.password),
            ('Append', p.sip_id, 'type', 'friend'),
            ('Append', p.sip_id, 'host', 'dynamic'),
            ('Append', p.sip_id, 'context', p.sip_id),
            ]
      if p.callgroups:
         actions.append(('Append', p.sip_id, 'callgroup', p.callgroups))
      if p.pickupgroups:
         actions.append(('Append', p.sip_id, 'pickupgroup', p.pickupgroups))
      cidnum = p.dnis if p.dnis else default_dnis
      if cidname or cidnum:
         actions.append(('Append', p.sip_id, 'callerid', '%s <%s>' % (cidname,cidnum) ))
      if p.user_id and user.voicemail and p.exten:
         actions.append(('Append', p.sip_id, 'mailbox', '%s@astportal' % p.exten))
      # ... then really update (delete + add)
      Globals.manager.update_config(directory_asterisk  + 'sip.conf', 
         None, [('DelCat', p.sip_id)])
      res = Globals.manager.update_config(directory_asterisk  + 'sip.conf', 
         'chan_sip', actions)
      log.debug('Update sip.conf returns %s', res)

   else:
      # PJSIP wizard
      log.debug('Update pjsip %s', p)
      actions = [
            ('NewCat', p.sip_id),
            ('Append', p.sip_id, 'type', 'wizard'),
            ('Append', p.sip_id, 'transport', 'udp'),
            ('Append', p.sip_id, 'accepts_auth', 'yes'),
            ('Append', p.sip_id, 'accepts_registrations', 'yes'),
            ('Append', p.sip_id, 'has_phoneprov', 'no'),
            ('Append', p.sip_id, 'inbound_auth/username', p.sip_id),
            ('Append', p.sip_id, 'inbound_auth/password', p.password),
            ('Append', p.sip_id, 'endpoint/context', p.sip_id),
            ('Append', p.sip_id, 'endpoint/set_var', 'GROUP()=' + p.sip_id),
            ('Append', p.sip_id, 'endpoint/language', 'fr'),
            ('Append', p.sip_id, 'endpoint/direct_media', 'no'),
            ('Append', p.sip_id, 'endpoint/aggregate_mwi', 'yes'),
            ('Append', p.sip_id, 'endpoint/device_state_busy_at', '1'),
            ('Append', p.sip_id, 'endpoint/allow_subscribe', 'yes'),
            ('Append', p.sip_id, 'endpoint/sub_min_expiry', '30'),
            ('Append', p.sip_id, 'aor/max_contacts', '4'),
            ('Append', p.sip_id, 'aor/qualify_frequency', '60'),
            ]

      if p.fax:
         actions.append(('Append', p.sip_id, 'endpoint/allow', 'alaw'))
         actions.append(('Append', p.sip_id, 'endpoint/t38_udptl', 'yes'))
         actions.append(('Append', p.sip_id, 'endpoint/t38_udptl_ec', 'fec'))
         actions.append(('Append', p.sip_id, 'endpoint/t38_udptl_maxdatagram', 400))
      elif p.vendor=='Grandstream' and p.model.startswith('GXP'):
         actions.append(('Append', p.sip_id, 'endpoint/allow', 'alaw'))
#         actions.append(('Append', p.sip_id, 'endpoint/allow', 'g722'))
      else:
         actions.append(('Append', p.sip_id, 'endpoint/allow', 'alaw'))

      if p.callgroups:
         actions.append(('Append', p.sip_id, 'endpoint/call_group', p.callgroups))

      if p.pickupgroups:
         actions.append(('Append', p.sip_id, 'endpoint/pickup_group', p.pickupgroups))

      if p.block_cid_out:
         actions.append(('Append',
                         p.sip_id,
                         'endpoint/callerid',
                         ' <%s>' % (default_dnis) ))
      else:
         actions.append(('Append',
                         p.sip_id, 
                         'endpoint/callerid',
                         '%s <%s>' % (cidname, p.dnis if p.dnis else default_dnis) ))

      if p.user_id and user.email_address and p.exten:
         actions.append(('Append', p.sip_id, 
            'aor/mailboxes', '%s@astportal' % p.exten))
         actions.append(('Append', p.sip_id, 
            'endpoint/mwi_from_user', p.sip_id))

      # ... then really update (delete + add)
      Globals.manager.update_config(directory_asterisk  + 'pjsip_wizard.conf', 
         None, [('DelCat', p.sip_id)])
      res = Globals.manager.update_config(directory_asterisk  + 'pjsip_wizard.conf', 
         'res_pjsip', actions)
      log.debug('Update pjsip_wizard.conf returns %s', res)

   # Update Asterisk exten database: Phone number <=> SIP user
   Globals.manager.send_action({'Action': 'DBdel',
         'Family': 'exten', 'Key': old_exten})
   Globals.manager.send_action({'Action': 'DBdel',
         'Family': 'netxe', 'Key': p.sip_id})
   Globals.manager.send_action({'Action': 'DBdel',
         'Family': 'block_cid_in', 'Key': p.exten})
   Globals.manager.send_action({'Action': 'DBdel',
         'Family': 'priority', 'Key': p.exten})
   Globals.manager.send_action({'Action': 'DBdel',
         'Family': 'fax_reject', 'Key': p.exten})
   if p.exten is not None:
      Globals.manager.send_action({'Action': 'DBput',
         'Family': 'exten', 'Key': p.exten, 'Val': p.sip_id})
      Globals.manager.send_action({'Action': 'DBput',
         'Family': 'netxe', 'Key': p.sip_id, 'Val': p.exten})
   if p.block_cid_in:
      Globals.manager.send_action({'Action': 'DBput',
         'Family': 'block_cid_in', 'Key': p.exten, 'Val': 1})
   if p.priority:
      Globals.manager.send_action({'Action': 'DBput',
         'Family': 'priority', 'Key': p.exten, 'Val': 1})
   if user is not None and not user.fax:
      Globals.manager.send_action({'Action': 'DBput',
         'Family': 'fax_reject', 'Key': p.exten, 'Val': 1})

   # Voicemail.conf: allways delete old_exten (don't care if doesn't exists)
   if old_exten is None:
      old_exten = p.exten
   Globals.manager.update_config(
      directory_asterisk  + 'voicemail.conf', 
      None, [('Delete', 'astportal', old_exten)])
   if user is not None and user.email_address is not None \
         and user.voicemail and user.email_voicemail:
      vm = u'>%s,%s,%s' % (p.exten, cidname, user.email_address)
      actions = [ ('Append', 'astportal', p.exten, vm) ]
      res = Globals.manager.update_config(
         directory_asterisk  + 'voicemail.conf', 
         'app_voicemail', actions)
      log.debug('Update voicemail.conf returns %s', res)

      Globals.manager.send_action({'Action': 'Command',
         'command': 'voicemail reload'})


   # Always delete old outgoing contexts
   Globals.manager.update_config(
         directory_asterisk  + 'extensions.conf', None, [('DelCat', p.sip_id)])
   if p.contexts is not None:
      # Create outgoing contexts
      log.debug('Contexts %s', p.contexts)
      actions = [
         ('NewCat', p.sip_id),
         ('Append', p.sip_id, 'include', '>parkedcalls'),
         ('Append', p.sip_id, 'include', '>hints'),
         ('Append', p.sip_id, 'include', '>SVI_internal'),
         ]
      for c in p.contexts.split(','):
         actions.append(('Append', p.sip_id, 'include', '>%s' % c))
      actions.append(('Append', p.sip_id, 'include', '>nomatch'))

      res = Globals.manager.update_config(
         directory_asterisk  + 'extensions.conf', None, actions)
      log.debug('Update outgoing extensions.conf returns %s', res)

   # Always delete old dnis entry (extensions.conf)
   if old_dnis is not None:
      res = Globals.manager.update_config(
         directory_asterisk  + 'extensions.conf', 
         None, [('Delete', 'dnis', 'exten', None, 
            '%s,1,Gosub(stdexten,%s,1(fromdnis))' % (old_dnis[-4:], old_exten))])
      log.debug('Delete <%s,1,Gosub(stdexten,%s,1(fromdnis))> returns %s',
                old_dnis, p.exten, res)

   if p.dnis is not None:
      # Create dnis entry (extensions.conf)
      res = Globals.manager.update_config(
         directory_asterisk  + 'extensions.conf', 
         None, [('Append', 'dnis', 'exten', '>%s,1,Gosub(stdexten,%s,1(fromdnis))' % \
               (p.dnis[-4:], p.exten) )]
      )
      log.debug('Update dnis extensions.conf returns %s', res)

   # Hints
   if old_exten is not None:
      res = Globals.manager.update_config(
         directory_asterisk  + 'extensions.conf', 
         None, [('Delete', 'hints', 'exten', None, 
            '%s,hint,%s/%s' % \
               (old_exten, 'SIP' if sip_type=='sip' else 'PJSIP', p.sip_id))])
      log.debug('Delete <%s,hint,xxSIP/%s> returns %s', old_exten, p.sip_id,res)

   if p.exten is not None:
      # Create new hint (extensions.conf)
      res = Globals.manager.update_config(
         directory_asterisk  + 'extensions.conf', 
         None, [('Append', 'hints', 'exten', 
            '>%s,hint,%s/%s' % \
               (p.exten, 'SIP' if sip_type=='sip' else 'PJSIP', p.sip_id))])
      log.debug('Update hints extensions.conf returns %s', res)

   # Allways reload dialplan
   Globals.manager.send_action({'Action': 'Command', 'Command': 'dialplan reload'})

def asterisk_update_queue(q):
   '''Update Asterisk configuration files

   Parameter: q=Queue object
   File updated: queues.conf
   '''


   # Always delete old queue and MOH class
   moh_class = asterisk_string(q.name, no_space=True)
   moh_dir = '/var/lib/asterisk/moh/fr/astportal/%s' % moh_class
   res = Globals.manager.update_config(
         directory_asterisk  + 'queues.conf', None, [('DelCat', moh_class)])
   log.debug('Delete queue "%s" returns %s', moh_class, res)
   asterisk_shell('rm -rf "%s"' % moh_dir)
   res = Globals.manager.update_config(
      directory_asterisk  + 'musiconhold.conf', None, [('DelCat', moh_class)])
   log.debug('Delete queue MOH class "%s" returns %s', moh_class, res)

   holdtime = 'yes' if q.announce_holdtime==1 else 'no'
   position = 'yes' if q.announce_position==1 else 'no'
   actions = [
            ('NewCat', moh_class),
            ('Append', moh_class, 'timeout', 60),
            ('Append', moh_class, 'strategy', q.strategy),
            ('Append', moh_class, 'wrapuptime', q.wrapuptime),
            ('Append', moh_class, 'announce-frequency', q.announce_frequency),
            ('Append', moh_class, 'min-announce-frequency', q.min_announce_frequency),
            ('Append', moh_class, 'announce-holdtime', holdtime),
            ('Append', moh_class, 'announce-position', position),
            ('Append', moh_class, 'ringinuse', 'no'),
            ('Append', moh_class, 'setqueuevar', 'yes'),
            ('Append', moh_class, 'setinterfacevar', 'yes'),
            ('Append', moh_class, 'setqueueentryvar', 'yes'),
            ('Append', moh_class, 'weight', q.priority),
            ('Append', moh_class, 'announce',
               'astportal/' + DBSession.query(Sound).get(q.announce_id).name \
                  if q.announce_id is not None else ''
            )
         ]

   if q.music_id is not None:
      # Queue music on hold is actually a music class, need to create it
      log.debug('Queue music_id <%d>', q.music_id)
      music = DBSession.query(Sound).get(q.music_id).name
      src_dir = '/var/lib/asterisk/moh/fr/astportal'
      asterisk_shell('%s/queue_moh_create.sh "%s" "%s" "%s"' % (
         utils_dir, moh_dir, src_dir, music))
      sleep(2)
      actions.append(('Append', moh_class, 'musicclass', moh_class))
      # Create moh class
      res = Globals.manager.update_config(
         directory_asterisk  + 'musiconhold.conf', None, [
         ('NewCat', moh_class),
         ('Append', moh_class, 'mode', 'files'),
         ('Append', moh_class, 'directory', moh_dir),
         ])
      log.debug('Create moh class "%s" returns %s' % (moh_class, res))

   # Create queue
   res = Globals.manager.update_config(
         directory_asterisk  + 'queues.conf', None, actions)
   log.debug('Create queue "%s", actions "%s"', q.name, actions)
   log.debug('Create queue "%s" returns %s', q.name, res)

   # Allways reload queues
   Globals.manager.send_action({'Action': 'QueueReload'})
   Globals.manager.send_action({'Action': 'Command', 'command': 'moh reload'})


class Status(object):
   '''Asterisk Status:
   Keeps track of channels, peers, queues...
   '''

   def __init__(self):
      self.reset()

   def reset(self):
      self.last_update = time()
      self.last_queue_update = time() - 600
      self.last_peers_update = time() - 600 
      self.peers = {}
      self.channels = {}
      self.bridges = {} # List of bridged channels
      self.astp_vars = {}
      self.queues = {}
      self.members = {}
#     members data structure: (see also app_queue.c)
# 'Girard Jean-Denis': 
#     {'Status': '1', 'LastUpdate': 1322092618.9852581, 'Outgoing': False, 
#        'InBegin': 1322092618.9852619, 'ConnBegin': 1322092618.9852581, 'CallsOut': 0, 
#        'Queues': {
#              'Groupe 2': {'Penalty': '1', 'InTotal': 0, 'CallsTaken': 0, 
#                    'InBegin': 1322092627.0398171}, 
#              'Groupe 1': {'Penalty': '0', 'InTotal': 0, 'CallsTaken': 0, 
#                    'InBegin': 1322092618.985265}}, 
#        'Recorded': False, 'Paused': '0', 'LastCall': '0', 'Membership': 'dynamic', 
#        'Location': 'SIP/mtvF81Tx', 'Spied': False, 
#        'OutTotal': 0, 'OutBegin': 1322092618.9852591, 
#        'InTotal': 0}}

   def handle_shutdown(self, event, manager):
      log.warning('Received shutdown event')
      Globals.manager.close()
      # XXX We should analize the event and reconnect here

   def normalize_member(self, member):
      return member

   def handle_event(self, event, manager):

      if 'Event' not in event.headers:
         log.warning('Event without Event ? %s', event.headers)
         return False

      previous_update = self.last_update
      e = event.headers['Event']

      if e in ('WaitEventComplete', 'QueueStatusComplete',
            'MusicOnHold', 'PeerlistComplete', 'FullyBooted', 'StatusComplete',
            'DTMF', 'RTCPReceived', 'RTCPSent', 'ExtensionStatus', 'Dial',
            'MessageWaiting', 'Shutdown', 'Reload', 'JabberEvent', 'JabberStatus',
            'Registry', 'NewAccountCode', 'NewCallerid', 'CEL',
            'OriginateResponse', 'Status', 'Masquerade', 'HangupRequest',
            'DialEnd', 'NewConnectedLine', 'DeviceStateListComplete',
            'SoftHangupRequest', 'ChannelUpdate', 'LocalBridge',
            'ChallengeSent', 'SuccessfulAuth', 'ChallengeResponseFailed',
            'InvalidAccountID', 'Unhold', 'Pickup',
            'AOC-E', 'DAHDIChannel', 'JitterBufStats', 'ChannelReload',
            'Hold', 'MusicOnHoldStart', 'MusicOnHoldStop',
            'AgentComplete', 'AgentCalled', 'DialState',
            'DTMFBegin', 'DTMFEnd', 'ContactStatus'):
         log.warning('Event ignored %s', str(event.headers))
         return

      if e=='Newexten':
         self._Newexten(event.headers)
      elif e=='VarSet':
         self._handle_VarSet(event.headers)
      elif e=='Newchannel':
         self._handle_Newchannel(event.headers)
      elif e in ('Newcallerid', 'Newstate', 'MeetmeJoin', 'MeetmeLeave'):
         self._updateChannels(event.headers)
      elif e=='DialBegin':
         self._handle_DialBegin(event.headers)
      elif e=='Hangup':
         self._handle_Hangup(event.headers)
      elif e in ('Link', 'Bridge'):
         self._handle_Link(event.headers)
      elif e=='Unlink':
         self._handle_Unlink(event.headers)
      elif e=='BridgeCreate':
         self._handle_BridgeCreate(event.headers)
      elif e=='BridgeDestroy':
         self._handle_BridgeDestroy(event.headers)
      elif e=='BridgeEnter':
         self._handle_BridgeEnter(event.headers)
      elif e=='BridgeLeave':
         self._handle_BridgeLeave(event.headers)
      elif e=='Rename':
         self._handle_Rename(event.headers)
      elif e.startswith('ContactStatus'):
         self._handle_ContactStatus(event.headers)
      elif e=='DeviceStateChange':
         self._handle_DeviceStateChange(event.headers)
      elif e=='PeerStatus':
         self._handle_PeerStatus(event.headers)
      elif e=='PeerEntry':
         self._handle_PeerEntry(event.headers)
      elif e in ('QueueMember', 'QueueMemberAdded'):
         self._handle_QueueMember(event.headers)
      elif e=='QueueParams':
         self._handle_QueueParams(event.headers)
      elif e=='AgentConnect':
         self._handle_AgentConnect(event.headers)
      elif e=='QueueMemberStatus':
         self._handle_QueueMemberStatus(event.headers)
      elif e in ('QueueMemberPause', 'QueueMemberUnpaused'):
         self._handle_QueueMemberPaused(event.headers)
      elif e=='QueueMemberRemoved':
         self._handle_QueueMemberRemoved(event.headers)
      elif e=='QueueEntry':
         self._handle_QueueEntry(event.headers)
      elif e=='QueueCallerJoin':
         self._handle_QueueCallerJoin(event.headers)
      elif e=='Join':
         self._handle_Join(event.headers)
      elif e=='QueueCallerAbandon':
         self._handle_QueueCallerAbandon(event.headers)
      elif e in ('Leave', 'QueueCallerLeave'):
         self._handle_Leave(event.headers)
      elif e == 'UserEvent':
         self._handle_UserEvent(event.headers)
      elif e=='ParkedCall':
         self._handle_ParkedCall(event.headers)
      elif e=='UnParkedCall':
         self._handle_UnParkedCall(event.headers)
      elif e=='ParkedCallTimeOut':
         self._handle_ParkedCallTimeOut(event.headers)
      elif e=='ParkedCallGiveUp':
         self._handle_ParkedCallGiveUp(event.headers)
      elif e == 'RequestBadFormat':
         log.error('%s: %s', e, event.headers)
      elif e in ('Transfer', 'BlindTransfer', 'AttendedTransfer'):
         self._handle_Transfer(event.headers)
      else:
         log.warning('Event not handled "%s"', e)

      if previous_update != self.last_update:
         # State has changed
         log.debug('--- BEGIN STATE DUMP --------------')
         for c in self.channels:
            log.debug('CHANNEL %s, outgoing %s, context %s, prio %s, link %s, park %s',
                      c, self.channels[c]['Outgoing'],
                      self.channels[c]['Context'],
                      self.channels[c]['Priority'],
                      self.channels[c]['Link'],
                      self.channels[c].get('Park') )
         for b in self.bridges:
            log.debug('BRIDGE %s, channels: %s', b, self.bridges[b])
#        for p in self.peers:
#           log.debug('PEER %s: %s', p, self.peers[p])
         log.debug('--- END STATE DUMP --------------')
         log.debug('')
         log.debug('')

      return True

   def _handle_DialBegin(self, data):
      src = data.get('Channel')
      dst = data['DestChannel']
      log.debug('Dial %s -> %s' % (src, dst))
      if src in self.channels:
         self.channels[src]['Outgoing'] = True
         self.channels[src]['LastUpdate'] = self.last_update = time()
         if dst in self.channels:
            self.channels[dst]['From'] = src
      if dst in self.channels:
         self.channels[dst]['Outgoing'] = False
         self.channels[dst]['LastUpdate'] = self.last_update = time()

   def _handle_PeerStatus(self,data):
      
      peer = data['Peer']
      log.debug('Peerstatus %s', data)
      if peer in self.peers:
         log.debug('Update peer status %s', peer)
         self.peers[peer]['PeerStatus'] = data['PeerStatus']
         self.peers[peer]['LastUpdate'] = time()
      else:
         log.debug('New peer status %s: %s', peer, data)
         self.peers[peer] = {'PeerStatus': data['PeerStatus'],
            'LastUpdate': time()}

      if 'Address' in data:
         self.peers[peer]['Address'] = data['Address']

#      if self.peers[peer]['PeerStatus']=='Registered':
#         res = Globals.manager.sipshowpeer(peer[4:])
#         self.peers[peer]['UserAgent'] = res.get_header('SIP-Useragent')

      self.last_peers_update = time()


   def _handle_PeerEntry(self,data):
      '''
      '''
      log.debug('PeerEntry <%s>', data)
      peer = data['Channeltype'] + '/' + data['ObjectName']
      status = 'Registered' if data['Status'].startswith('OK ') else data['Status']
      addr = None if data['IPaddress']=='-none-' else data['IPaddress']
      if peer in self.peers:
         log.debug('Update peer entry %s', peer)
         self.peers[peer]['PeerStatus'] = status
         self.peers[peer]['LastUpdate'] = time()
         self.peers[peer]['Address'] = addr
      else:
         log.debug('New peer entry %s', peer)
         self.peers[peer] = {
            'PeerStatus': status,
            'LastUpdate': time(),
            'Address': addr
            }
      self.last_peers_update = time()

   def _handle_ContactStatus(self,data):
      peer = 'PJSIP/' + data['EndpointName'] # or data['AOR'] ?
      status = data['ContactStatus']
      if peer in self.peers:
         log.info('Update peer state "%s" is now "%s"', peer, status)
         self.peers[peer]['State'] = status
         self.peers[peer]['LastUpdate'] = time()
      else:
         log.info('New peer state "%s" is now "%s"', peer, status)
         self.peers[peer] = {'State': status,
            'LastUpdate': time()}
      self.last_peers_update = time()


   def _handle_DeviceStateChange(self,data):
      peer = data['Device']
      log.debug('DeviceStateChange %s', data)
      if peer in self.peers:
         log.debug('Update peer state %s', peer)
         self.peers[peer]['State'] = data['State']
         self.peers[peer]['LastUpdate'] = time()
      else:
         log.debug('New peer state %s: %s', peer, data)
         self.peers[peer] = {'State': data['State'],
                             'LastUpdate': time()}
      self.last_peers_update = time()


   def _updateQueues(self, data):
      pass

   def _handle_QueueParams(self, data):
      # Wait{Uniqueid] = (time, CallerIDName, CallerIDNum)
      self.queues[data['Queue']] = {
         'ServicelevelPerf': data['ServicelevelPerf'], 
         'Abandoned': int(data['Abandoned']),
         'Calls': int(data['Calls']), 
         'Max': int(data['Max']), 'Completed': int(data['Completed']), 
         'ServiceLevel': data['ServiceLevel'], 'Strategy': data['Strategy'], 
         'Weight': data['Weight'], 'Holdtime': data['Holdtime'], 
         'Members': [], 'Wait': {}, 'LastUpdate': time()}
      self.last_queue_update = time()

# Agents' status: from include/asterisk/devicestate.h
# Device is valid but channel didn't know state #define AST_DEVICE_UNKNOWN	0
# Device is not used #define AST_DEVICE_NOT_INUSE	1
# Device is in use #define AST_DEVICE_INUSE	2
# Device is busy #define AST_DEVICE_BUSY		3
# Device is invalid #define AST_DEVICE_INVALID	4
# Device is unavailable #define AST_DEVICE_UNAVAILABLE	5
# Device is ringing #define AST_DEVICE_RINGING	6
# Device is ringing *and* in use #define AST_DEVICE_RINGINUSE	7
# Device is on hold #define AST_DEVICE_ONHOLD	8
#Event: QueueMemberAdded
#Privilege: agent,all
#Queue: test
#Membership: dynamic
#MemberName: Girard Michael
#LastCall: 0
#Paused: 0
#Status: 4
#Interface: SIP/igHJ9CNh
#StateInterface: SIP/igHJ9CNh
#Penalty: 0
#CallsTaken: 0
#Ringinuse: 0
   def _handle_QueueMember(self, data):
      q = data['Queue']
      if 'Name' in data:
         m = self.normalize_member(data['Name'])
      elif 'MemberName' in data:
         m = self.normalize_member(data['MemberName'])
      else:
         log.error('QueueMember without name %s', data)
         return
      if q not in self.queues:
         log.error('Queue does not exist %s', q)
         return

      self.queues[q]['Members'].append(m)

      if m in self.members: # Known member, update his info
         log.debug('Update member "%s"', m)
         self.members[m]['Queues'][q] = {
               'CallsTaken': int(data['CallsTaken']),
               'InBegin': time(), 'InTotal': 0, 'Penalty': data['Penalty']}

      else: # New member
         log.debug('New member "%s"', m)
         loc = data['Location'] if 'Location' in data else data['Interface']
         self.members[m] = {'Status': data['Status'],
            'Membership': data['Membership'], 'Location': loc,
            'LastCall': data['LastCall'], 'Paused': data['Paused'],
            'Paused': 'Pause' if data['Paused'] == '1' else '0',
            'PauseBegin': time(),
            'LastUpdate': time(),# 'Queues': [q,],
            'ConnBegin': time(), # Connection time
            # Counters for outgoing calls
            'Outgoing': False, 'CallsOut': 0, 'OutBegin': time(), 'OutTotal': 0,
            # Counters for incoming calls
            'InBegin': time(), 'InTotal': 0,
            'Spied': False, 'Recorded': False}
         if 'Queues' not in self.members[m].keys():
            self.members[m]['Queues'] = {}
         self.members[m]['Queues'][q] = {
               'CallsTaken': int(data['CallsTaken']),
               'InBegin': time(), 'InTotal': 0, 'Penalty': data['Penalty']}

      log.debug('handle_QueueMember => %s', self.members)
      self.last_queue_update = time()

   def _handle_AgentConnect(self, data):
      q = data['Queue']
      m = self.normalize_member(data['MemberName'])
      self.members[m]['ConnBegin'] = time()
      self.members[m]['Queue'] = data['Queue']
      self.members[m]['Channel'] = data['Channel']
#      self.members[m]['BridgedChannel'] = data['BridgedChannel']
      self.members[m]['MemberName'] = data['MemberName']
      if 'Holdtime' in data:
         self.members[m]['Holdtime'] = data['Holdtime']
      else: # Asterisk-13
         self.members[m]['Holdtime'] = data['HoldTime']
      self.members[m]['Uniqueid'] = data['Uniqueid']
      self.members[m]['LastUpdate'] = self.last_queue_update = time()

   def _handle_QueueMemberPaused(self, data):
      m = self.normalize_member(data['MemberName'])
      log.debug('Paused %s => %s', m, data)
      if m not in self.members.keys():
         log.error('Pause: member "%s" does not exist ?' % m)
         return

      if data['Paused'] == '1':
         self.members[m]['Paused'] = data['Reason'] if 'Reason' in data else 'Pause'
         self.members[m]['PauseBegin'] = time()
      else:
         self.members[m]['Paused'] = '0'
         self.members[m]['PauseBegin'] = 0

      self.last_queue_update = time()

   def _handle_QueueMemberStatus(self, data):
      m = self.normalize_member(data['MemberName'])
      if m not in self.members.keys():
         log.error('Member "%s" does not exist ?' % m)
         return
      s = data['Status']
      log.debug('QueueMemberStatus %s -> %s' % (m, s))
      if s in ('2', '3', '6'): # AST_DEVICE_INUSE AST_DEVICE_BUSY AST_DEVICE_RINGING
         self.members[m]['InBegin'] = time()
      elif s == '6':
         self.members[m]['Outgoing'] = False
      elif s == '7': # AST_DEVICE_RINGINUSE
         self.members[m]['Outgoing'] = False
      self.members[m]['Status'] = s
      self.members[m]['Queues'][data['Queue']]['CallsTaken'] = int(data['CallsTaken'])
      self.members[m]['LastCall'] = data['LastCall']
      self.members[m]['LastUpdate'] = time()
      self.last_queue_update = time()

   def _handle_QueueMemberRemoved(self, data):
      if data['Queue'] not in self.queues:
         log.error('Queue "%s not found', data['Queue'])
         return
      q = data['Queue']
      if 'Member' in data:
         m = self.normalize_member(data['Member'])
      elif 'MemberName' in data:
         m = self.normalize_member(data['MemberName'])
      else:
         log.error('QueueMemberRemoved %s', data)
         return
      self.queues[q]['Members'].remove(m) # Remove from this queue
      for q,v in self.queues.iteritems(): # Check if member belongs to other queue
         if m in v['Members']:
            break
      else:
         del self.members[m] # ...else remove member
      log.debug('handle_QueueMemberRemoved => %s', self.members)
      self.last_queue_update = time()

   def _handle_QueueCallerJoin(self, data):
      '''
Event: QueueCallerJoin
Privilege: agent,all
Channel: PJSIP/DyQmiIIi-0000005f
ChannelState: 4
ChannelStateDesc: Ring
CallerIDNum: DyQmiIIi
CallerIDName: SysNux
ConnectedLineNum: <unknown>
ConnectedLineName: <unknown>
Language: fr
AccountCode: 2
Context: App_2_Entrant
Exten: s
Priority: 4
Uniqueid: 1433865700.163
Queue: test
Position: 1
Count: 1
      '''
      log.debug('QueueCallerJoin %s', data)
      if data['Queue'] not in self.queues:
         log.error('Queue "%s not found', data['Queue'])
         return
      self.queues[data['Queue']]['Wait'][data['Uniqueid']] = (
         time(), data['CallerIDName'], data['CallerIDNum'], data['Position'], data['Count'])
      self.last_queue_update = time()

   def _handle_QueueEntry(self, data):
      log.debug('QueueEntry %s', data)
      if data['Queue'] not in self.queues:
         log.error('Queue "%s not found', data['Queue'])
         return
      self.queues[data['Queue']]['Wait'][data['Uniqueid']] = (time() - float(data['Wait']),
         data['CallerIDName'], data['CallerIDNum'])
      self.last_queue_update = time()

   def _handle_Join(self, data):
      log.debug('Join %s', data)
      if data['Queue'] not in self.queues:
         log.error('Queue "%s not found', data['Queue'])
         return
      self.queues[data['Queue']]['Calls'] += 1
      self.queues[data['Queue']]['Wait'][data['Uniqueid']] = (time(),
         data['CallerIDName'], data['CallerIDNum'])
      self.last_queue_update = time()


#-----------------------------------------------------
#               q = g[i].getAttribute('queue');
#               p = g[i].getAttribute('position');
#               o = g[i].getAttribute('originalposition');
#               for (var j=p+1; j<self.queues[q]['calls']; j++)
#                  self.queues[q]['wait'][j-1] = self.queues[q]['wait'][j];
#               display++;
#               break;
   def _handle_QueueCallerAbandon(self, data):
      log.debug('CallerAbandon %s', data)
      pos = -999
      try:
         del self.queues[data['Queue']]['Wait'][data['Uniqueid']]
      except:
         log.warning('CallerAbandon, Uniqueid %s does not exist in queue %s?',
                     data['Uniqueid'], self.queues[data['Queue']])

      self.last_queue_update = time()


   def _handle_Leave(self, data):
      log.debug('Leave data %s', data)
      if data['Queue'] not in self.queues:
         log.error('Queue "%s not found', data['Queue'])
         return
      try:
         self.queues[data['Queue']]['Calls'] = int(data['Count'])
         del self.queues[data['Queue']]['Wait'][data['Uniqueid']]
      except:
         log.warning('Leave, Position %s does not exist in queue %s?',
                     data['Uniqueid'], self.queues[data['Queue']])

      self.last_queue_update = time()
#-----------------------------------------------------

   def normalize_channel(self, c):
      '''atxfer creates Local/103@ngqckJos-00000017;1 and 
      Local/103@ngqckJos-00000017;2, remove ';x' ?
      '''
      return c if c[-2]!=';' else c[:-2]

   def _Newexten(self, data):
      # There are tons of Newexten events, this should be fast!
      c = self.normalize_channel(data['Channel'])
      if c not in self.channels: return
      self.channels[c]['AppData'] = data.get('AppData')
      self.channels[c]['Context'] = data['Context']
      self.channels[c]['Extension'] = data['Extension']
      self.channels[c]['Priority'] = data['Priority']
      self.channels[c]['Application'] = data.get('Application')
      self.channels[c]['LastUpdate'] = self.last_update = time()


   def _updateChannels(self, data):
      c = self.normalize_channel(data['Channel'])
      if c not in self.channels: return
      self.channels[c]['LastUpdate'] = time()
      # Keys eventually received from event:
      # CallerIDName, CallerIDNum, ChannelState, ConnectedLineName, ConnectedLineNum, 
      # Context, Event, Extension, Priority, Application, AppData,
      # LastUpdate, State, Uniqueid, Begin
      for k in ('Application', 'AppData', 'Begin', 'Uniqueid',
         'CallerIDName', 'CallerIDNum',
         'Context', 'Extension', 'Priority', 'LastUpdate'):
         if k in data:
            self.channels[c][k] = data[k]

      new_state = None
      if 'State' in data:
         # manager_version=='1.0':
         new_state = data['State']
      elif 'ChannelStateDesc' in data:
         # manager_version=='1.1':
         new_state = data['ChannelStateDesc']

      if new_state and self.channels[c]['State'] != new_state:
         self.channels[c]['State'] = new_state
         if new_state=='Up':
            self.channels[c]['Begin'] = time()

         new_state = data.get('ChannelState')
# 20150613        if new_state == '4':
#            self.channels[c]['Outgoing'] = False
#         elif new_state == '5':
#            self.channels[c]['Outgoing'] = True

      self.last_update = time()

   def _handle_Newchannel(self,data):
      
      if 'State' in data:
         state = data['State']
      elif 'ChannelStateDesc' in data:
         state = data['ChannelStateDesc']
      else:
         state = 'Down'

      c = self.normalize_channel(data['Channel'])

      self.channels[c] = {'CallerIDNum': data['CallerIDNum'], 
            'CallerIDName': data['CallerIDName'], 'Uniqueid': data['Uniqueid'],
            'Context': None, 'Priority': None,
            'State': state, 'Begin': time(), 'Link': None}
      if data['ChannelState'] == '4': # Ring
         self.channels[c]['Outgoing'] = True
      else:
         self.channels[c]['Outgoing'] = False
      # Check if channel belongs to a queue member
      loc = data['Channel'][:data['Channel'].find('-')] # SIP/100-000000a6 -> SIP/100
      for m in self.members:
         if self.members[m]['Location'] == loc:
            self.members[m]['Outgoing'] = self.channels[c]['Outgoing']
            self.members[m]['OutBegin'] = time()
            self.last_queue_update = time()
            break

      self.last_update = time()


   def _handle_Hangup(self, data):
      c = self.normalize_channel(data['Channel'])

      if c not in self.channels:
         if c[-8:] == '<ZOMBIE>' and c[:-8] in self.channels:
            # Redirected or transferred channel
            c = c[:-8]
         else:
            log.warning('Hangup: channel "%s" does not exist...', c)
            for chan in self.channels:
               if chan in c:
                  log.warning('Hangup: "%s" -> destroy %s', c, chan)
                  c = chan
                  break
            else:
               log.warning('Hangup: "%s" no channel to destroy', c)
               return

      # Check if channel belongs to a queue member
      loc = c[:c.find('-')] # SIP/100-000000a6 -> SIP/100
      for m in self.members:
         if self.members[m]['Location'] == loc: # and self.members[m]['Status'] == '2':
            log.debug('Hangup: member "%s"', self.members[m])
            if self.members[m]['Outgoing']:
               self.members[m]['Outgoing'] = False
               self.members[m]['CallsOut'] += 1
               self.members[m]['OutTotal'] += time() - self.members[m]['OutBegin']
            elif self.members[m]['Status'] in ('2', '3'): # AST_DEVICE_INUSE AST_DEVICE_BUSY
               # XXX attention ne pas compter s'il n'y a pas eu de réponse XXX
               self.members[m]['InTotal'] += time() - self.members[m]['InBegin']

            # Reset members properties, but not Uniqueid, HangupURL, 
            # Custom... or hangup window will not work
            self.members[m]['Spied'] = False
            self.members[m]['Recorded'] = False
            self.last_queue_update = time()
            break

      if c in self.astp_vars:
      	del self.astp_vars[c]

      if c in self.channels:
         del self.channels[c]
      self.last_update = time()

   def _handle_BridgeCreate(self, data):
      self.bridges[data['BridgeUniqueid']] = []

   def _handle_BridgeDestroy(self, data):
      log.debug('BridgeDestroy %s', data['BridgeUniqueid'])
      if data['BridgeUniqueid'] in self.bridges:
         del self.bridges[data['BridgeUniqueid']]
      else:
         log.warning('BridgeDestroy %s does not exist', data['BridgeUniqueid'])


   def _handle_BridgeEnter(self, data):

      b = data['BridgeUniqueid']
      if b not in self.bridges:
         # We may have missed BridgeCreate event: for example parking bridges are
         # permanent, so if we restart astportal without restarting asterisk, there
         # is no BridgeCreate event.
         log.warning('BridgeEnter: bridge %s does not exist, creating now.', b)
         self.bridges[b] = []

      c = self.normalize_channel(data['Channel'])
      log.debug('Channel %s enters bridge %s (%s users)', c, b, self.bridges[b])
      self.bridges[b].append(c)
      if len(self.bridges[b])==2:
         c1 = self.normalize_channel(self.bridges[b][0])
         c2 = self.normalize_channel(self.bridges[b][1])
         try:
            self.channels[c1]['Link'] = c2
            self.channels[c1]['LastUpdate'] = time()
         except:
            log.warning('Link: channel "%s" doesn\'t exist ?', c1)
         try:
            self.channels[c2]['Link'] = c1
            self.channels[c2]['LastUpdate'] = time()
         except:
            log.warning('Link: channel "%s" doesn\'t exist ?', c2)

         # Check if channel belongs to a queue member
         loc = c2[:c2.find('-')] # SIP/100-000000a6 -> SIP/100
         for m in self.members:
            if self.members[m]['Location'] == loc:
               log.debug('Link member "%s" to channel "%s" (%s)',
                  m, data['Channel'], data['Uniqueid'])
               self.members[m]['Uniqueid'] = data['Uniqueid']
               self.members[m]['PeerChannel'] = data['Channel']
               self.last_queue_update = time()
               break

      self.last_update = time()

   def _handle_BridgeLeave(self, data):

      c = self.normalize_channel(data['Channel'])
      bid = data['BridgeUniqueid']
      log.debug('Channel %s leaves bridge %s', c, bid)
      try:
         self.channels[data['Channel']]['Link'] = None
         self.channels[c]['LastUpdate'] = time()
         self.bridges[bid].remove(c)
      except KeyError:
         # This can happen when we start while Asterisk has connections
         pass

      self.last_update = time()

   def _handle_Link(self, data):

      if data['Bridgestate'] == 'Unlink':
         self._handle_Unlink(data)
         return

      c1 = self.normalize_channel(data['Channel1'])
      c2 = self.normalize_channel(data['Channel2'])
      try:
         self.channels[c1]['Link'] = c2
         self.channels[c1]['Outgoing'] = False
         self.channels[c2]['Link'] = c1
         self.channels[c2]['Outgoing'] = True
         self.channels[c1]['LastUpdate'] = time()
         self.channels[c2]['LastUpdate'] = time()
      except:
         log.warning('Link: channel "%s" doesn\'t exist ?', c1)

      # Check if channel belongs to a queue member
      loc = c2[:c2.find('-')] # SIP/100-000000a6 -> SIP/100
      for m in self.members:
         if self.members[m]['Location'] == loc:
            log.debug('Link member "%s" to channel "%s" (%s)',
                      m, data['Channel1'], data['Uniqueid1'])
            self.members[m]['Uniqueid'] = data['Uniqueid1']
            self.members[m]['PeerChannel'] = data['Channel1']
            self.last_queue_update = time()
            break

      self.last_update = time()


   def _handle_Unlink(self, data):
      # Event: Unlink
      # Channel1: SIP/dnarotam-3533
      # Channel2: SIP/Doorphone-5180
      # Uniqueid1: 1091803550.81
      # Uniqueid2: 1091803550.82

      c1 = self.normalize_channel(data['Channel1'])
      c2 = self.normalize_channel(data['Channel2'])
      try:
         del self.channels[data['Channel1']]['Link']
         del self.channels[data['Channel2']]['Link']
         self.channels[c1]['LastUpdate'] = time()
         self.channels[c2]['LastUpdate'] = time()
      except KeyError:
         # This can happen when we start while Asterisk has connections
         pass
      self.last_update = time()


   def _handle_Rename(self, data):
      #  Event: Rename
      #  Oldname: SIP/Doorphone-985e
      #  Newname: SIP/Doorphone-985e<MASQ>

      if 'Oldname' not in data.keys():
         return
      old = data['Oldname']
      new = data['Newname']
      self.channels[old]['LastUpdate'] = time()

      # We can't rename, so we have to do an add/delete operation
      self.channels[new] = self.channels[old]
      del self.channels[old]

      # Rename the links as well:
      try:
         linked = self.channels[new]['Link']
         self.channels[linked]['Link'] = new
         self.channels[linked]['LastUpdate'] = time()
      except:
         pass
      self.last_update = time()

   def _handle_VarSet(self, data):
      if not data['Variable'].startswith('ASTP_'):
         return
      if data['Channel'] not in self.astp_vars.keys():
      	self.astp_vars[data['Channel']] = {}
      self.astp_vars[data['Channel']][data['Variable']] = data['Value']
      log.debug('New astp_vars %s', self.astp_vars)
      self.last_update = time() # XXX nécessaire ou non ?
      self.last_queue_update = time()

   def _handle_UserEvent(self, data):
# data={'ConnectedLineNum': '<unknown>', 'Linkedid': '1479603120.158', 'Uniqueid': '1479603120.158', 'Language': 'fr', 'AccountCode': '', 'ChannelState': '6', 'Exten': '5', 'CallerIDNum': '40501040', 'Priority': '2', 'UserEvent': 'Callback', 'ConnectedLineName': '<unknown>', 'Context': 'vm_or_cb', 'CallerIDName': 'Girard Jean-Denis', 'Privilege': 'user,all', 'Event': 'UserEvent', 'Channel': 'PJSIP/fqygGSWm-0000009c', 'ChannelStateDesc': 'Up'}

      if data['UserEvent']=='AgentWillConnect':
         if data['Agent'] not in self.members:
            # Happens when agent logged off before receiving call
            log.error('_handle_UserEvent: agent "%s" does not exist', data['Agent'])
            return
         log.debug('Agent "%s" will connect to channel "%s" (%s)',
                   data['Agent'], data['PeerChannel'], data['PeerUniqueid'])
         self.members[data['Agent']]['PeerChannel'] = data['PeerChannel']
         self.members[data['Agent']]['PeerCallerid'] = data['PeerCallerid']
         self.members[data['Agent']]['HoldTime'] = data['HoldTime']
         self.members[data['Agent']]['Uniqueid'] = data['PeerUniqueid']
         self.members[data['Agent']]['ConnectURL'] = data.get('ConnectURL', '')
         self.members[data['Agent']]['HangupURL'] = data.get('HangupURL', '')
         self.members[data['Agent']]['Custom1'] = data.get('Custom1', '')
         self.members[data['Agent']]['Custom2'] = data.get('Custom2', '')
         #self.last_update = time() # XXX nécessaire ou non ?
         self.last_queue_update = time()

      elif data['UserEvent']=='Callback':
         # Queue a callback to an busy extension
         # Will be triggered by scheduler (lib/app_globals + controllers/callback)
         src = data['src']
         dstchan = data['dstchan']
         dstexten = data['dstexten']
         uid = data['Uniqueid']
         log.info('New callback %s -> %s:%s (%s)', src, dstchan, dstexten, uid)
         callbacks.put_nowait((src, dstchan, dstexten, uid))

      elif data['UserEvent']=='AutoRecord':
         # Set "recorded" flag on member
         Globals.asterisk.members[data['name']]['Recorded'] = True

         # Insert record info into database
         r = Record()
         r.user_id = -2 # Auto_record pseudo-user!
         r.uniqueid = data['Uniqueid']
         r.queue_id = DBSession.query(Queue).filter(
            Queue.name==data['queue']).one().queue_id
         try:
            u = DBSession.query(User).filter(User.ascii_name==data['name']).first()
            r.member_id = u.user_id
         except:
            r.member_id = 1
            log.error('user "%s" not found', name)
         r.custom1 = data['custom1']
         r.custom2 = data['custom2']
         DBSession.add(r)

      elif data['UserEvent']=='NotifyPhones':
         phones = data['phones'].split('&')
         log.info('NotifyPhones phones=%s', phones)
         for phone in phones:
            if phone == '':
                continue
            try:
                p = DBSession.query(Phone).filter(Phone.sip_id==phone).one()
            except:
               log.error('NotifyPhones: phone %s not found!', phone)
               return
            log.info('Found phone %s, exten=%s, vendor=%s', 
                      p.phone_id, p.exten, p.vendor)
      
            peer = 'PJSIP/' + p.sip_id
            if 'Address' in Globals.asterisk.peers[peer] and \
               Globals.asterisk.peers[peer]['Address'] is not None:
               ip = (Globals.asterisk.peers[peer]['Address']).split(':')[0]
            else:
               log.error('Phone %s, no IP address!', p.phone_id)
               return

            if p.vendor == 'Grandstream':
               from astportal2.lib.grandstream import Grandstream
               gs = Grandstream(ip, p.mac)
               gs.notify(p)

            else:
               log.warning('Notify not implemented for %s', self.vendor)

      elif data['UserEvent']=='TestEvent':
         log.info('TestEvent data=%s', data)

      else:
         log.error('Unkown UserEvent <%s>', data)


   def _handle_ParkedCall(self, data):
      log.debug('ParkedCall %s', data)
      self.channels[data['ParkeeChannel']]['Park'] = data['ParkingSpace']

   def _handle_UnParkedCall(self, data):
      log.debug('UnParkedCall %s', data)
      self.channels[data['ParkeeChannel']]['Park'] = None

   def _handle_ParkedCallTimeOut(self, data):
      log.debug('ParkedCallTimeOut %s', data)
      self.channels[data['ParkeeChannel']]['Park'] = None

   def _handle_ParkedCallGiveUp(self, data):
      log.debug('ParkedCallGiveUp %s' % data)
      self.channels[data['ParkeeChannel']]['Park'] = None

   def _handle_Transfer(self, data):
      log.debug('Transfer %s', data)

