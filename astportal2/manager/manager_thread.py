# -*- coding: UTF-8 -*-
"""
Asterisk Manager Thread
"""

import asyncore
from threading import Thread 
from manager import ManagerEvents

from astportal2.lib.app_globals import Globals

import logging
log = logging.getLogger(__name__)

class manager_thread(Thread):


   def __init__ (self, host, user, secret):
      log.debug('init')
      Thread.__init__(self)
      self.host = host
      self.user = user
      self.secret = secret
      self.connected = False

   def run(self):
      log.debug('run')
      Globals.manager = ManagerEvents(self.host, self.user, self.secret)
      Globals.manager.action('Status')
      Globals.manager.action('QueueStatus')
      Globals.manager.action('SIPpeers')
      Globals.manager.action('IAXpeers')
      log.debug('Waiting for events...')
      asyncore.loop()


