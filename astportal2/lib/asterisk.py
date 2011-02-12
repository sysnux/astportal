# -*- coding: utf-8 -*-

from astportal2.lib.app_globals import Globals
from time import time
import logging
log = logging.getLogger(__name__)

class Status(object):
   '''Asterisk Status:
   Keeps track of channels, peers, queues...
   '''

   def __init__(self):
      self.last_update = time()
      self.peers = {}
      self.channels = {}
      self.queues = {}
      self.members = {}

   def handle_shutdown(self, event, manager):
      log.warning('Recieved shutdown event')
      Globals.manager.close()
      # XXX We should analize the event and reconnect here
      
   def handle_event(self, event, manager):
      if 'Event' not in event.headers:
         log.debug('Event without Event ? %s')
         return False

      e = event.headers['Event']
      log.debug('Received event type "%s"' % e)
#      log.debug(event.message)
#      log.debug(event.data)
      if e in ('WaitEventComplete', 'QueueStatusComplete', 'QueueMemberPaused', 
            'MusicOnHold', 'PeerlistComplete', 'FullyBooted', 'StatusComplete' ):
         return
      if e=='Newchannel':
         self._handle_Newchannel(event.headers)
      elif e in ('Newcallerid', 'Newexten', 'Newstate', 'MeetmeJoin', 'MeetmeLeave'):
         self._updateChannels(event.headers)
      elif e=='Hangup':
         self._handle_Hangup(event.headers)
      elif e=='Link':
         self._handle_Link(event.headers)
      elif e=='Unlink':
         self._handle_Unlink(event.headers)
      elif e=='Rename':
         self._handle_Rename(event.headers)
      elif e=='PeerStatus':
         self._handle_PeerStatus(event.headers)
      elif e=='PeerEntry':
         self._handle_PeerEntry(event.headers)
      elif e=='MessageWaiting':
         self._handle_MessageWaiting(event.headers)
      elif e=='Shutdown':
         self._handle_Shutdown(event.headers)
      elif e=='Reload':
         self._handle_Reload(event.headers)
      elif e in ('QueueMember', 'QueueMemberAdded'):
         self._handle_QueueMember(event.headers)
      elif e=='QueueParams':
         self._handle_QueueParams(event.headers)
      elif e=='QueueMember':
         self._handle_QueueMember(event.headers)
      elif e=='AgentConnect':
         self._handle_AgentConnect(event.headers)
      elif e=='QueueMemberStatus':
         self._handle_QueueMemberStatus(event.headers)
      elif e=='QueueMemberRemoved':
         self._handle_QueueMemberRemoved(event.headers)
      elif e=='QueueEntry':
         self._handle_QueueEntry(event.headers)
      elif e=='Join':
         self._handle_Join(event.headers)
      elif e=='QueueCallerAbandon':
         self._handle_QueueCallerAbandon(event.headers)
      elif e=='Leave':
         self._handle_Leave(event.headers)
      elif e == 'CEL':
         self._handle_CEL(event.headers)
      elif e in ('ExtensionStatus', 'Dial'):
         log.debug(' * * * NOT IMPLEMENTED %s' % str(event.headers))
      else:
         log.warning('Event not handled "%s"' % e)

#      log.debug('--- CHANNELS --------------')
#      for c in self.channels:
#         log.debug('%s: %s' % (c, str(self.channels[c])))
#      log.debug('--- PEERS -----------------')
#      for p in self.peers:
#         log.debug('%s: %s' % (p, str(self.peers[p])))
      
      return True

   def _handle_CEL(self, event):
      '''
AccountCode: 
EventTime: 2011-02-06 11:05:51
LinkedID: 1297026348.43
UniqueID: 1297026348.43
AppData: 
CallerIDdnid: 199
Exten: 199
Peer: 
AMAFlags: DOCUMENTATION
CallerIDnum: 100
CallerIDani: 100
EventName: LINKEDID_END
Application: 
Userfield: 
Context: interne
CallerIDname: J-D Girard
Privilege: call,all
CallerIDrdnis: 
Event: CEL
Channel: SIP/100-0000001f
   '''
#      log.debug('CEL:')
#      for k in event.keys():
#         log.debug('\t%s: %s', k, event[k])
      cel_type = event['EventName']
      log.debug('CEL, type: %s' % cel_type)
#      if cel_type == 'CHAN_START':
#         self.channels[event['Channel']] = event
#      elif cel_type == 'CHAN_END':
#         del self.channels[event['Channel']]
#      last_update = time()


   def _handle_PeerStatus(self,dict):
      
      peer = dict['Peer']
      if peer in self.peers:
         log.debug('Update peer status %s' % peer)
         self.peers[peer]['PeerStatus'] = dict['PeerStatus']
         self.peers[peer]['LastUpdate'] = time()
      else:
         log.debug('New peer status %s' % peer)
         self.peers[peer] = {'PeerStatus': dict['PeerStatus'],
            'LastUpdate': time()}

      if 'Address' in dict:
         self.peers[peer]['Address'] = dict['Address']

      if self.peers[peer]['PeerStatus']=='Registered':
         res = Globals.manager.sipshowpeer(peer[4:])
         self.peers[peer]['UserAgent'] = res.get_header('SIP-Useragent')

      self.last_update = time()


   def _handle_PeerEntry(self,dict):
      '''
      '''
      log.debug(dict)
      peer = dict['Channeltype'] + '/' + dict['ObjectName']
      status = 'Registered' if dict['Status'].startswith('OK ') else dict['Status']
      addr = None if dict['IPaddress']=='-none-' else dict['IPaddress']
      if peer in self.peers:
         log.debug('Update peer entry %s' % peer)
         self.peers[peer]['PeerStatus'] = status
         self.peers[peer]['LastUpdate'] = time()
         self.peers[peer]['Address'] = addr
      else:
         log.debug('New peer entry %s' % peer)
         self.peers[peer] = {
            'PeerStatus': status,
            'LastUpdate': time(),
            'Address': addr
            }

      self.last_update = time()

   def _updateQueues(self, dict):
      pass

   def _handle_QueueParams(self, dict):
      self.queues[dict['Queue']] = {
         'ServicelevelPerf': dict['ServicelevelPerf'], 'Abandoned': int(dict['Abandoned']),
         'Calls': int(dict['Calls']), 'Max': int(dict['Max']), 'Completed': int(dict['Completed']), 
         'ServiceLevel': dict['ServiceLevel'], 'Strategy': dict['Strategy'], 
         'Weight': dict['Weight'], 'Holdtime': dict['Holdtime'], 
         'Members': [], 'Wait': [], 'LastUpdate': time()}
      self.last_update = time()

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
   def handle_QueueMember(self, dict):
      q = dict['Queue']
      m = normalize_member(dict['Name'])
      self.queues[q]['Members'].append(m)
      if m in self.members:
         self.members[m]['Queues'].append(q)
      else:
         self.members[m] = {'Status': dict['Status'], 'Begin': time(),
            'CallsTaken': int(dict['CallsTaken']), 'Penalty': dict['Penalty'],
            'Membership': dict['Membership'], 'Location': dict['Location'],
            'LastCall': dict['LastCall'], 'Paused': dict['Paused'],
            'LastUpdate': time(), 'Queues': [q,] }
      self.last_update = time()

   def _handle_AgentConnect(self, dict):
      q = dict['Queue']
      m = normalize_member(dict['Member'])
      self.members[m]['Begin'] = time()
      self.members[m]['Queue'] = dict['Queue']
      self.members[m]['Channel'] = dict['Channel']
      self.members[m]['BridgedChannel'] = dict['BridgedChannel']
      self.members[m]['MemberName'] = dict['MemberName']
      self.members[m]['Holdtime'] = dict['Holdtime']
      self.members[m]['Uniqueid'] = dict['Uniqueid']
      self.members[m]['LastUpdate'] = time()
      self.last_update = time()

   def _handle_QueueMemberStatus(self, dict):
      m = normalize_member(dict['MemberName'])
      s = dict['Status']
      if s in (2, 6):
         self.members[m]['Begin'] = time()
         self.members[m]['Recording'] = False
      self.members[m]['Status'] = dict['Status']
      self.members[m]['CallsTaken'] = int(dict['CallsTaken'])
      self.members[m]['LastCall'] = dict['LastCall']
      self.members[m]['Paused'] = dict['Paused']
      self.members[m]['LastUpdate'] = time()
      self.last_update = time()

   def _handle_QueueMemberRemoved(self, dict):
      q = dict['Queue']
      m = normalize_member(dict['Member'])
      self.queues[q]['Members'].remove(m)
      del self.members[m]
      self.last_update = time()

   def _handle_QueueEntry(self, dict):
#/* Event: QueueEntry
#Queue: jp
#Position: 1
#Channel: SIP/snom-f4009868
#CallerIDNum: snom
#CallerIDName: Tiare
#Wait: 12 */
      print dict
      self.queues[dict['Queue']]['Wait'][dict['Position']] = time() - dict['Wait']
      self.last_update = time()

   def _handle_Join(self, dict):
      print dict
      self.queues[dict['Queue']]['Calls'] += 1
      self.queues[dict['Queue']]['Wait'].append(time())
      self.last_update = time()


#-----------------------------------------------------
#               q = g[i].getAttribute('queue');
#               p = g[i].getAttribute('position');
#               o = g[i].getAttribute('originalposition');
#               for (var j=p+1; j<self.queues[q]['calls']; j++)
#                  self.queues[q]['wait'][j-1] = self.queues[q]['wait'][j];
#               display++;
#               break;
   def _handle_QueueCallerAbandon(self, dict):
      print dict
      del self.queues[dict['Queue']]['Wait'][int(dict['Position'])-1]
      self.last_update = time()

   def _handle_Leave(self, dict):
      self.queues[dict['Queue']]['Calls'] = int(dict['Count'])
      self.last_update = time()
#-----------------------------------------------------

   def _updateChannels(self, dict):
      c = dict['Channel']
      if c not in self.channels: return
      self.channels[c]['LastUpdate'] = time()
      for k, v in dict.iteritems():
         if k in ('State', 'ChannelStateDesc', 'Channel', 'Uniqueid', 'Privilege'): continue
         self.channels[c][k] = v

      new_state = None
      if 'State' in dict:
         # manager_version=='1.0':
         new_state = dict['State']
      elif 'ChannelStateDesc' in dict:
         # manager_version=='1.1':
         new_state = dict['ChannelStateDesc']

      if new_state and 'State' in self.channels[c] and self.channels[c]['State'] != new_state:
         self.channels[c]['State'] = new_state
         if new_state=='Up':
            self.channels[c]['Begin'] = time()
      self.last_update = time()

   def _handle_Newchannel(self,dict):
      if 'State' in dict:
         state = dict['State']
      elif 'ChannelStateDesc' in dict:
         state = dict['ChannelStateDesc']
      else:
         state = 'New'
      self.channels[dict['Channel']] = {'CallerIDNum': dict['CallerIDNum'], 
            'CallerIDName': dict['CallerIDName'], 'Uniqueid': dict['Uniqueid'],
            'State': state, 'Begin': time()}
      self.last_update = time()

   def _handle_Hangup(self, dict):
      c = dict['Channel']
      if c not in self.channels:
         log.warning('Hangup: channel "%s" does not exit..' % c)
         return
      del self.channels[c]
      self.last_update = time()

   def _handle_Link(self, dict):
      # Event: Link
      # Channel1: SIP/dnarotam-3533
      # Channel2: SIP/Doorphone-5180
      # Uniqueid1: 1091803550.81
      # Uniqueid2: 1091803550.82

      c1 = dict['Channel1']
      c2 = dict['Channel2']
      self.channels[c1]['Link'] = c2
      self.channels[c2]['Link'] = c1
      self.channels[c1]['LastUpdate'] = time()
      self.channels[c2]['LastUpdate'] = time()
      self.last_update = time()


   def _handle_Unlink(self, dict):
      # Event: Unlink
      # Channel1: SIP/dnarotam-3533
      # Channel2: SIP/Doorphone-5180
      # Uniqueid1: 1091803550.81
      # Uniqueid2: 1091803550.82

      c1 = dict['Channel1']
      c2 = dict['Channel2']
      try:
         del self.channels[dict['Channel1']]['Link']
         del self.channels[dict['Channel2']]['Link']
         self.channels[c1]['LastUpdate'] = time()
         self.channels[c2]['LastUpdate'] = time()
      except KeyError:
         # This can happen when we start while Asterisk has connections
         pass
      self.last_update = time()


   def _handle_Rename(self, dict):
      #  Event: Rename
      #  Oldname: SIP/Doorphone-985e
      #  Newname: SIP/Doorphone-985e<MASQ>

      old = dict['Oldname']
      new = dict['Newname']
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
