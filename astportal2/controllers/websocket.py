# -*- coding: utf-8 -*-
# WebSocket handler

from ws4py.websocket import WebSocket
from ws4py.framing import OPCODE_TEXT

try:
   from tg.predicates import in_group
except ImportError:
   from repoze.what.predicates import in_group

from astportal2.lib.app_globals import Globals

import json
from time import time, sleep
import logging
log = logging.getLogger(__name__)

import threading

def update():
   ''' Send data to connected clients when:
   . new data is available, or
   . new clients has connected, or
   . it is needed to keep connection open through nginwx proxy
   Running in thread started from class below
   '''

   last_update = last_queue_update = last_clients = last_queue_clients = \
      ping = ping_queue = 0
   wait = .5

   while Globals.asterisk is None:
      sleep(3)

   while True:

      if last_update < Globals.asterisk.last_update or \
            ping * wait > 30.0 or \
            last_clients != len(Globals.ws_clients['channels']):
         log.debug(u'Sending WS channels updates')
         ping = 0
         last_clients = len(Globals.ws_clients['channels'])
         last_update = Globals.asterisk.last_update

         for c in Globals.ws_clients['channels']:
            c.send(json.dumps(dict(
               last_update=Globals.asterisk.last_update,
               time=time(),
               channels=Globals.asterisk.channels)))
         log.debug(u'WS channel updates done')

      if last_queue_update < Globals.asterisk.last_queue_update or \
            ping_queue * wait > 30.0 or \
            last_queue_clients != len(Globals.ws_clients['queues']):
         log.debug(u'Sending WS queues updates')
         ping_queue = 0
         last_queue_clients = len(Globals.ws_clients['queues'])
         last_queue_update = Globals.asterisk.last_queue_update

         for c in Globals.ws_clients['queues']:
            c.send(json.dumps(dict(
               last_queue_update=Globals.asterisk.last_queue_update,
               time=time(),
               channels=Globals.asterisk.queues)))
         log.debug(u'WS queue updates done')

      ping += 1
      ping_queue += 1
      sleep(wait)

 
class BroadcastWebSocket(WebSocket):

   allow_only = in_group('admin',
      msg=u'Vous devez être membre du groupe "admin" pour accéder à cette page')

   clients = []
   threading.Thread(target=update).start()

#   heartbeat_freq = 30

#   def __init__(self, sock):
#      self.heartbeat_freq = 30
#      super().__init__()

   def opened(self):

      self.clients.append(self)
      log.warning('New WS client, total %d' % (len(self.clients)))


   def received_message(self, m):
      log.warning('Received_message "%s" (%s, %s)' % (m, m.opcode, type(m)))

      if m.opcode==OPCODE_TEXT:
         if m.data==u'subscribe_channels':
            Globals.ws_clients['channels'].append(self)
            if Globals.asterisk is not None:
               self.send(json.dumps(dict(
                     last_update=Globals.asterisk.last_update,
                     time=time(),
                     channels=Globals.asterisk.channels)))

         elif m.data==u'subscribe_queues':
            Globals.ws_clients['queues'].append(self)
            log.warning('subscribe_queues')
            if Globals.asterisk is not None:
               self.send(json.dumps(dict(
                     last_queue_update=Globals.asterisk.last_queue_update,
                     time=time(),
                     channels=Globals.asterisk.queues)))

         else:
            log.error('unknown message')

   def closed(self, code, reason="Unknown"):
      if self in self.clients:
         self.clients.remove(self)
      if self in Globals.ws_clients['channels']:
         Globals.ws_clients['channels'].remove(self)
      if self in Globals.ws_clients['queues']:
         Globals.ws_clients['queues'].remove(self)
      log.warning('WS closed, code=%s, %d remaining clients' % (code, len(self.clients)))

