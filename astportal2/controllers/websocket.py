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
from time import time
import logging
log = logging.getLogger(__name__)

 
class BroadcastWebSocket(WebSocket):

   allow_only = in_group('admin',
      msg=u'Vous devez être membre du groupe "admin" pour accéder à cette page')

   clients = []
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
            log.warning('subscribe_channels: %s' % Globals.asterisk.channels)
            self.send(json.dumps(dict(
                     last_update=Globals.asterisk.last_update,
                     time=time(),
                     channels=Globals.asterisk.channels)))

         elif m.data==u'subscribe_queues':
            Globals.ws_clients['queues'].append(self)
            log.warning('subscribe_queues')

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

