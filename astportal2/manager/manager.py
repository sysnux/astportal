# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 by Holger Schurig
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#


import sys, os, time, socket, asyncore, asynchat # , string

#
# Oh, this beast is complex. In order to be able to comprehend it in
# two months I have to describe it.
#
# Initial connection and login
# ============================
#
#
# When we create the object, __init__() calls do_connect() which
# in turn connects to Asterisk, similar to the telnet session below:
#  $ telnet 127.0.0.1 5038
#  Trying 127.0.0.1...
#  Connected to localhost.localdomain (127.0.0.1).
#  Escape character is '^]'.
# Now we're connected. And Asterisk sends immediately it's header:
#  Asterisk Call Manager/1.0
# All text that we got is coming in via collect_incoming_data() and appended
# to buffer[]. In do_connect() we used set_terminator() to define that our
# chunk of data is finished after an CR/LF sequence. This has the effect
# that now found_terminator() get's called which can operator on buffer[].
#
# It looks for all lines and string-of-lines in buffer[] to see if there is
# an "ActionID: " in it. If yes, we store that in the local 'id' variable.
# If it is, we store all of the data in the dictionary 'action_data'.
#
# In this case, it's not, so we don't store anything.
#
# Instead, we see see that our data is exactly 'Asterisk Call Manager/1.0'.
# So we know that we have to login now. We change the terminator to the
# character sequence that marks an empty line and call call_nowait() with
# the action 'Login' and our login credentials. Therefore we send something
# like this:
#
#  Action: Login
#  ActionID: destar-16384-00000001
#  Username: destar
#  Secret: destar
#
# Assuming that the login was successfully, Asterisk sends something
# back:
#  
#  Response: Success
#  ActionID: destar-16384-00000001
#  Message: Authentication accepted
#
# Again the data ends in chunks in collect_incoming_data(), which put's
# it into buffer[] and once the empty line after the this data has been
# received, the function found_terminator() gets called.
#
# This time, found_terminator() find's an ActionID and therefore stores
# the whole 'data' into action_data[id].
#
# While all of this happens, the do_connect() method was running
# asyncore.poll() in a loop, which makes asyncore call all of the even
# handlers like collect_incoming_data() or found_terminator() for us. This
# polling loop also tests if the the action id 'destar-%d-00000001' is in
# the action_data[]. As soon as it it, the loop terminates.
#
# Now we have the data inside do_connect(), without the use of any not-so-
# easy-to-handle callback function. We now test in data if we find
# "Response: Error" and set 'loggedin' accordingly.
#  
#
# Calls to manager actions
# ========================
#
# Now suppose we're logged in and want to call manager methods. We do this
# by calling call(action, args). For example:
#  mgr.call('Ping')
#  mgr.call('Command', Command='sip show peers')
#
# Now almost the same happens as above, only that our poll-loop is now
# in call(), not in do_connect().
#

conn = None

class ManagerClient(asynchat.async_chat):

   def __init__(self, host, username, password):
      asynchat.async_chat.__init__(self)
      self.address = (socket.gethostbyname(host),5038)
      self.buffer = []
      self.action_data = {}
      self.loggedin = False
      self.reconnect = False
      self.username = username
      self.password = password
      self.host = host
      self.manager_version = None
      res = self.do_connect()


   def do_connect(self):
      """Tries to connect, and implicitly to login. If that does
      work, we set self.loggedin to True."""

      #print "do_connect()"
      self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
      self.set_terminator('\r\n')
      self.connect(self.address)

      self.seq = 0
      self.loggedin = False
      id = 'destar-%d-%08x' % (os.getpid(), 1)
      n = 0
      while not self.closing and n<20:
         if id in self.action_data and self.action_data[id]:
            #print "do_connect() id", id, "found in action_data"
            break
         #print "do_connect() sleep, id:", id, "action_data:", self.action_data
         asyncore.poll(0.5, asyncore.socket_map)
         n = n + 1
      #print "do_connect() done with while"
      if id in self.action_data:
         self.loggedin = self.action_data[id][0].find("Response: Success") != -1
         #print "do_connect(), loggedin:", self.loggedin
      

   def close(self):
      """Close event callback from asyncore/asynchat."""

      #print "close()"
      asynchat.async_chat.close(self)
      self.loggedin = False
      if self.reconnect:
         #print "close(), about to reconnect"
         self.do_connect()


   def handle_connect(self):
      """Connect callback from asyncore/asynchat."""
   
      #print "handleconnected()"
      pass


   def handle_error(self):
      """Exception callback from asyncore/asynchat."""

      self.closing = True
      t, v, tb = sys.exc_info()
      #print "handle_error(), t:",t
      #print "handle_error(), v:",v
      #print "handle_error(), tb:",tb
      #while tb:
      #  #print tb.tb_frame.f_code.co_filename, tb.tb_frame.f_code.co_name, tb.tb_lineno
      #  tb = tb.next
      if t != socket.error:
         asynchat.async_chat.handle_error(self)


   def collect_incoming_data(self, data):
      """Data callback from asyncore."""

      #print "incoming_data(), data:", data
      self.buffer.append(data)


   def handle_event(self, data):
      #print "handle_event()", "-"*40
      for l in data:
      #  print l
         continue
      #print


   def found_terminator(self):
      """Data completed callback from asyncore."""

      id = None
      data = []
      for l in self.buffer:
         for ll in l.split('\n'):
            data.append(ll.strip())
            #print "found_terminator(), ll:", ll
            if ll.startswith("ActionID: "):
               id = ll[10:].strip()
               #print "found_terminator(), id:", id
      self.buffer = []

      #print "found_terminator()", "-"*40
      #for l in data: print l
      #print

      if data[0].startswith("Event: "):
         self.handle_event(data)

      if id in self.action_data:
         self.action_data[id] = data

      if data[0][0:22]=="Asterisk Call Manager/":
         self.manager_version = data[0][-3:]
         print 'Connected to Asterisk Call Manager version', self.manager_version
         self.set_terminator('\r\n\r\n')
         self.call_nowait('Login', Username=self.username, Secret=self.password)


   def call_nowait(self, action, **args):
      """This calls an Asterisk management command. It does not wait for any
      response, therefore it assumes that some other code calls asyncore.loop()
      or asyncore.poll() to keep the event callbacks happening."""

      self.seq = self.seq + 1
      id = 'destar-%d-%08x' % (os.getpid(), self.seq)
      #print "call_nowait(), id", id, "to None"
      self.action_data[id] = None
      self.push('Action: %s\r\n' % action)
      self.push('ActionID: %s\r\n' % id)
      for k in args:
         self.push('%s: %s\r\n' % (k,args[k]))
      self.push('\r\n')
      return id


   def call(self, action, **args):
      """Executes a manager action, wait's until completion and
      returns the result as an array of strings."""

      id = self.call_nowait(action,**args)
      while not self.action_data[id]:
         #print "call(), sleep"
         asyncore.poll(0.1,asyncore.socket_map)
      res = self.action_data[id]
      #print "call(), delete",id,"in action_data"
      del self.action_data[id]
      return res


   def action(self, act, **args):
      """Like call, but strips unneeded strings from the array."""

      #res = map(string.strip, self.call(act,**args).split('\n'))
      res = self.call(act, **args)
      print "action(), res:", res
      if res[1].startswith('ActionID:'):
         del res[1]
      if res[0]=='Response: Follows':
         del res[0]
         del res[-1]
      elif res[0].startswith('Response: '):
         res[0] = res[0][10:]
      return res
      


def normalizeChannel(val):
   #print "normalizeChannel() with", val, type(val)
   if val.startswith('CAPI'):
      i = val.index('/')
      j = val.index(']')
      channel = "CAPI/%s.%s" % (val[i+1:j], val[j+2:])
   if val.startswith('IAX2'):
      i = val.find(':')
      channel = val[:i]
   else:
      channel = val[:-5]
   return channel

def normalize_member(m):
   n = m.find('/')
   return m[0:n].upper() + m[n:]

channels = {}
registry = {}
messages = {}
queues   = {}
members  = {}
last_update = time.time()

class ManagerEvents(ManagerClient):

   def handle_event(self, data):
      # First we convert the array into a dict:

      dict = {}
      #print "handle_event(), data:", data
      for s in data:
         if not s: continue
         #print "handle_event(), s: '%s'" % s
         # We can't use s.split(':') because of "Channel: IAX2/65.39.205.121:4569/1"
         i = s.find(':')
         if i==-1:
            key = s
            val = ""
         else:
            key = s[:i]
            val = s[i+1:].strip()
         dict[key] = val.strip()
      if 'Event' not in dict:
         print ' * * * ERROR: event without event ?', dict
         return
      e = dict['Event']
      #print e, dict
   
      # When we look if we have a handler function
#      if e=='CEL':
#         print ' * * * CEL ', dict, '* ' * 20
#         return
      if e in ('WaitEventComplete', 'QueueStatusComplete', 'QueueMemberPaused', 
            'MusicOnHold', 'PeerlistComplete', 'FullyBooted', 'StatusComplete' ):
         return
      if e=='Newchannel':
         self.handle_Newchannel(dict)
      elif e in ('Newcallerid', 'Newexten', 'Newstate', 'MeetmeJoin', 'MeetmeLeave'):
         self.updateChannels(dict)
      elif e=='Hangup':
         self.handle_Hangup(dict)
      elif e=='Link':
         self.handle_Link(dict)
      elif e=='Unlink':
         self.handle_Unlink(dict)
      elif e=='Rename':
         self.handle_Rename(dict)
      elif e=='PeerStatus':
         self.handle_PeerStatus(dict)
      elif e=='PeerEntry':
         self.handle_PeerEntry(dict)
      elif e=='MessageWaiting':
         self.handle_MessageWaiting(dict)
      elif e=='Shutdown':
         self.handle_Shutdown(dict)
      elif e=='Reload':
         self.handle_Reload(dict)
      elif e in ('QueueMember', 'QueueMemberAdded'):
         self.handle_QueueMember(dict)
      elif e=='QueueParams':
         self.handle_QueueParams(dict)
      elif e=='QueueMember':
         self.handle_QueueMember(dict)
      elif e=='AgentConnect':
         self.handle_AgentConnect(dict)
      elif e=='QueueMemberStatus':
         self.handle_QueueMemberStatus(dict)
      elif e=='QueueMemberRemoved':
         self.handle_QueueMemberRemoved(dict)
      elif e=='QueueEntry':
         self.handle_QueueEntry(dict)
      elif e=='Join':
         self.handle_Join(dict)
      elif e=='QueueCallerAbandon':
         self.handle_QueueCallerAbandon(dict)
      elif e=='Leave':
         self.handle_Leave(dict)
      elif e in ('ExtensionStatus', 'Dial'):
         print ' * * * NOT IMPLEMENTED', dict, '* ' * 20
         return
      else:
         print ' * * * UNKNOWN', e, dict, '* ' * 20
         return

      print '-' * 40
      print "CHANNELS:"
      for c, d in channels.iteritems():
         print '\t', c, d
      print "REGISTRY:"
      for r, d in registry.iteritems():
         print '\t', r, d
      print "MESSAGES:"
      for m, d in messages.iteritems():
         print '\t', m, d
      print "QUEUES:"
      for q, d in queues.iteritems():
         print '\t', q, d
      print "MEMBERS:"
      for m, d in members.iteritems():
         print '\t', m, d
      print '-' * 40
      global last_update
      last_update = time.time()

   def updateQueues(self, dict):
      pass

   def handle_QueueParams(self, dict):
      print dict
      global queues
      queues[dict['Queue']] = {
         'ServicelevelPerf': dict['ServicelevelPerf'], 'Abandoned': int(dict['Abandoned']),
         'Calls': int(dict['Calls']), 'Max': int(dict['Max']), 'Completed': int(dict['Completed']), 
         'ServiceLevel': dict['ServiceLevel'], 'Strategy': dict['Strategy'], 
         'Weight': dict['Weight'], 'Holdtime': dict['Holdtime'], 
         'Members': [], 'Wait': [], 'LastUpdate': time.time()}

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
      print dict
      global queues, members
      q = dict['Queue']
      m = normalize_member(dict['Name'])
      queues[q]['Members'].append(m)
      if m in members:
         members[m]['Queues'].append(q)
      else:
         members[m] = {'Status': dict['Status'], 'Begin': time.time(),
            'CallsTaken': int(dict['CallsTaken']), 'Penalty': dict['Penalty'],
            'Membership': dict['Membership'], 'Location': dict['Location'],
            'LastCall': dict['LastCall'], 'Paused': dict['Paused'],
            'LastUpdate': time.time(), 'Queues': [q,] }

   def handle_AgentConnect(self, dict):
      print dict
      global queues, members
      q = dict['Queue']
      m = normalize_member(dict['Member'])
      members[m]['Begin'] = time.time()
      members[m]['Queue'] = dict['Queue']
      members[m]['Channel'] = dict['Channel']
      members[m]['BridgedChannel'] = dict['BridgedChannel']
      members[m]['MemberName'] = dict['MemberName']
      members[m]['Holdtime'] = dict['Holdtime']
      members[m]['Uniqueid'] = dict['Uniqueid']
      members[m]['LastUpdate'] = time.time()

   def handle_QueueMemberStatus(self, dict):
      print dict
      global queues, members
      m = normalize_member(dict['MemberName'])
      s = dict['Status']
      if s in (2, 6):
         members[m]['Begin'] = time.time()
         members[m]['Recording'] = False
      members[m]['Status'] = dict['Status']
      members[m]['CallsTaken'] = int(dict['CallsTaken'])
      members[m]['LastCall'] = dict['LastCall']
      members[m]['Paused'] = dict['Paused']
      members[m]['LastUpdate'] = time.time()

   def handle_QueueMemberRemoved(self, dict):
      print dict
      global queues, members
      q = dict['Queue']
      m = normalize_member(dict['Member'])
      queues[q]['Members'].remove(m)
      del members[m]

   def handle_QueueEntry(self, dict):
#/* Event: QueueEntry
#Queue: jp
#Position: 1
#Channel: SIP/snom-f4009868
#CallerIDNum: snom
#CallerIDName: Tiare
#Wait: 12 */
      print dict
      global queues
      queues[dict['Queue']]['Wait'][dict['Position']] = time.time() - dict['Wait']

   def handle_Join(self, dict):
      print dict
      global queues
      queues[dict['Queue']]['Calls'] += 1
      queues[dict['Queue']]['Wait'].append(time.time())


#-----------------------------------------------------
#               q = g[i].getAttribute('queue');
#               p = g[i].getAttribute('position');
#               o = g[i].getAttribute('originalposition');
#               for (var j=p+1; j<queues[q]['calls']; j++)
#                  queues[q]['wait'][j-1] = queues[q]['wait'][j];
#               display++;
#               break;
   def handle_QueueCallerAbandon(self, dict):
      print dict
      global queues
      del(queues[dict['Queue']]['Wait'][int(dict['Position'])-1])

   def handle_Leave(self, dict):
      global queues
      queues[dict['Queue']]['Calls'] = int(dict['Count'])
#-----------------------------------------------------

   def updateChannels(self, dict):
      c = dict['Channel']
      global channels
      if c not in channels: return
      channels[c]['LastUpdate'] = time.time()
      for k, v in dict.iteritems():
         if k in ('State', 'ChannelStateDesc', 'Channel', 'Uniqueid', 'Privilege'): continue
         channels[c][k] = v

      new_state = None
      if 'State' in dict:
         # manager_version=='1.0':
         new_state = dict['State']
      elif 'ChannelStateDesc' in dict:
         # manager_version=='1.1':
         new_state = dict['ChannelStateDesc']
      else:
         print 'UPDATE CHANNEL ?', dict

      if new_state and channels[dict['Channel']]['State'] != new_state:
         channels[dict['Channel']]['State'] = new_state
         if new_state=='Up':
            channels[dict['Channel']]['Begin'] = time.time()

   def handle_Newchannel(self,dict):
      global channels
      channels[dict['Channel']] = {'CallerIDNum': dict['CallerIDNum'], 
            'CallerIDName': dict['CallerIDName'], 'Uniqueid': dict['Uniqueid'],
            'Begin': 0}
      if self.manager_version=='1.0':
         channels[dict['Channel']]['State'] = dict['State']
      elif self.manager_version=='1.1':
         channels[dict['Channel']]['State'] = dict['ChannelStateDesc']

   def handle_Hangup(self, dict):
      c = dict['Channel']
      global channels
      if c not in channels:
         print 'HANGUP', c, 'DOES NOT EXIST'
         return
      del channels[c]

   def handle_Link(self, dict):
      # Event: Link
      # Channel1: SIP/dnarotam-3533
      # Channel2: SIP/Doorphone-5180
      # Uniqueid1: 1091803550.81
      # Uniqueid2: 1091803550.82

      global channels
      c1 = dict['Channel1']
      c2 = dict['Channel2']
      channels[c1]['Link'] = c2
      channels[c2]['Link'] = c1
      channels[c1]['LastUpdate'] = time.time()
      channels[c2]['LastUpdate'] = time.time()


   def handle_Unlink(self, dict):
      # Event: Unlink
      # Channel1: SIP/dnarotam-3533
      # Channel2: SIP/Doorphone-5180
      # Uniqueid1: 1091803550.81
      # Uniqueid2: 1091803550.82

      global channels
      c1 = dict['Channel1']
      c2 = dict['Channel2']
      try:
         del channels[dict['Channel1']]['Link']
         del channels[dict['Channel2']]['Link']
         channels[c1]['LastUpdate'] = time.time()
         channels[c2]['LastUpdate'] = time.time()
      except KeyError:
         # This can happen when we start while Asterisk has connections
         pass


   def handle_Rename(self, dict):
      #  Event: Rename
      #  Oldname: SIP/Doorphone-985e
      #  Newname: SIP/Doorphone-985e<MASQ>

      global channels
      old = dict['Oldname']
      new = dict['Newname']
      channels[old]['LastUpdate'] = time.time()

      # We can't rename, so we have to do an add/delete operation
      channels[new] = channels[old]
      del channels[old]

      # Rename the links as well:
      try:
         linked = channels[new]['Link']
         channels[linked]['Link'] = new
         channels[linked]['LastUpdate'] = time.time()
      except:
         pass


   def handle_PeerStatus(self,dict):
      global registry
      peer = dict['Peer']
      if peer in registry:
         registry[peer]['PeerStatus'] = dict['PeerStatus']
         registry[peer]['LastUpdate'] = time.time()
      else:
         registry[peer] = {'PeerStatus': dict['PeerStatus'],
            'LastUpdate': time.time()}
      if 'Address' in dict:
         registry[dict['Peer']]['Address'] = dict['Address']
      peer_data = self.action('SIPshowPeer', Peer=peer[4:].encode('iso-8859-1'))
      for x in peer_data:
         if x.startswith('SIP-Useragent: '):
            registry[peer]['UserAgent'] = x.replace('SIP-Useragent: ','')
            break


   def handle_PeerEntry(self,dict):
      '''
      '''
      global registry
      peer = dict['Channeltype'] + '/' + dict['ObjectName']
      status = 'Registered' if dict['Status'].startswith('OK ') else dict['Status']
      addr = None if dict['IPaddress']=='-none-' else dict['IPaddress']
      if peer in registry:
         registry[peer]['PeerStatus'] = status
         registry[peer]['LastUpdate'] = time.time()
         registry[peer]['Address'] = addr
      else:
         registry[peer] = {
            'PeerStatus': status,
            'LastUpdate': time.time(),
            'Address': addr
            }

   def handle_MessageWaiting(self, dict):
      # Event: MessageWaiting
      # Mailbox: 23@default
      # Waiting: 1

      global messages
      messages[dict['Mailbox']] = {'Wainting': dict['Waiting'],
            'LastUpdate': time.time()}

   def handle_Shutdown(self, dict):
      # Event: Shutdown
      # Shutdown: Cleanly
      # Restart: False

      global channels
      channels = {}
      global registy
      registry = {}
      global messages
      messages = {}

      #self.close()
      #self.do_connect()
      self.reconnect = True


   def handle_Reload(self, dict):
      # Event: Reload
      # Message: Reload Requested

      pass

   def originateCallExt(self,channel,context,extension,priority,callerid):
      return self.action('Originate', Channel=channel, Context=context, Exten=extension, Priority=priority, CallerID=callerid)

   def originateCallApp(self, channel,application,data):
      print ' * * * * * ORIGINATE ', channel, application
      return self.action('Originate', Channel=channel, Application=application)


def connect(username=None,password=None):
   global conn
   if conn and conn.loggedin: return

   # determine credentials to use for login
   if not username and not password:
      # We couldn't log in
      print "***** manager cant login"
      return

   conn = ManagerEvents(username,password)
   if not conn.loggedin:
      conn.close()
      conn = None


def isConnected():
   global conn
   return conn and conn.connected


def isLoggedIn():
   global conn
   return isConnected() and conn.loggedin


def getVar(family, key, default):
   for s in conn.action('Command', Command='database get %s %s' % (family,key)):
      if s.startswith('Value: '):
         return s[7:]
   return default

def setVar(family, key, val):
   if val:
      conn.action('Command', Command='database put %s %s %s' % (family,key,val))
   else:
      conn.action('Command', Command='database del %s %s' % (family,key))


def getVarFamily(family):
   varlist = []
   for s in conn.action('Command', Command='database show %s' % family):
      if s.startswith("/%s" % family):
         varlist.append(s[len(family)+2:])
   return varlist
   
def getSIPPeers():
   return conn.action('Command', Command='sip show peers')


def checkMailBox(ext):
   vmstate = {}
   for s in conn.action('MailboxCount', Mailbox=ext):
      if s.startswith('NewMessages: '):
         vmstate['New'] = s[13:]
      if s.startswith('OldMessages: '):
         vmstate['Old'] = s[13:]
   return vmstate
   
def reloadAsterisk():
   return conn.action('Command', Command='reload')

def reloadMoH():
   return conn.action('Command', Command='moh reload')

if __name__ == '__main__':
   connect()
   if not isConnected():
      print "Not connected"
   else:
      res = []

      ############################ manager.c:

      # Action:     Ping
      # Parameters: none
      #res = conn.action('Ping')

      # Action:     ListCommands
      # Parameters: none
      #res = conn.action('ListCommands')

      # Action:     Events
      # Parameters: EventMask (on, off, system,call,log etc)
      #res = conn.action('Events', EventMask='off'

      # Action:     Logoff
      # Parameters: none
      #res = conn.action('Logoff')

      # Action:     Hangup
      # Parameters: Channel
      #res = conn.action('Hangup', ...)

      # Action:     SetVar
      # Parameter:  Channel, Variable, Value
      #res = conn.action('SetVar', ...)

      # Action:     GetVar
      # Parameter:  Channel, Variable
      #res = conn.action('GetVar', ...)

      # Action:     Status
      # Parameter:  Channel
      #res = conn.action('Status', Channel=...)

      # Action:     Redirect
      # Parameters: Channel, ExtraChannel, Exten, Context, Priority
      #res = conn.action('Redirect', ...)

      # Action:     Command
      # Parameters: Command
      res = conn.action('Command', Command='core show channels concise')

      # Action:     Originate
      # Parameters: Channel, Exten, Context, Priority, Timeout (in ms),
      #             CallerID, Variable, Account, Application, Data, Async
      #res = conn.action('Originate', Channel='SIP/dnarotam', Application='Milliwatt')

      # Action:     MailboxStatus
      # Parameters: Mailbox
      #res = conn.action('MailboxStatus', Mailbox='1234')

      # Action:     MailboxCount
      # Parameters: Mailbox
      #res = conn.action('MailboxCount', Mailbox='1234')

      # Action:     ExtenstionState
      # Parameters: Exten, Context
      #res = conn.action('ExtensionState', Exten='26', Context='default')

      # Action:     Timeout
      # Parameters: Channel, Timeout (in ms?)
      #res = conn.action('Timeout', Timeout=30)


      ############################ apps/app_queue.c:

      # Action:     Queues
      # Parameters: none
      #res = conn.action('Queues')

      # Action:     QueueStatus
      # Parameters: none
      #res = conn.action('QueueStatus')


      ############################ apps/app_setcdruserfield.c:

      # Action:     SetCDRUserField
      # Parameters: Channel, UserField, Append


      ############################ channels/chan_iax.c:

      # Action:     IAX1peers
      # Parameters: none


      ############################ channels/chan_iax2.c:

      # Action:     IAXpeers
      # Parameters: none


      ############################ channels/chan_zap.c:

      # Action:     ZapTransfer
      # Parameters: ZapChannel

      # Action:     ZapHangup
      # Parameters: ZapChannel

      # Action:     ZapDialOffhook
      # Parameters: ZapChannel

      # Action:     ZapDNDon
      # Parameters: ZapChannel

      # Action:     ZapDNDoff
      # Parameters: ZapChannel

      # Action:     ZapShowChannels
      # Parameters: none


      ############################ res/res_monitor.c

      # Action:     Monitor
      # Parameters: Channel, File, Format, Mix

      # Action:     StopMonitor
      # Parameters: Channel

      # Action:     ChangeMonitor
      # Parameters: Channel, File


      ############################ res/res_features.c:

      # Action:     ParkedCalls
      # Parameters: none


      ############################ app_valetparking.c:

      # Action:     ValetparkedCalls
      # Parameters: none


      for s in res:
         print s

      print "Waiting for events ...\n"
      try:
         asyncore.loop()
      except KeyboardInterrupt:
         pass
