# -*- coding: UTF-8 -*-
"""
Asterisk Manager Thread
"""

import asyncore
from threading import Thread 
from manager import ManagerClient, ManagerEvents

astman = { 'id': 0, 'data': [], 'len': 10  }

class manager_thread(Thread):


   def __init__ (self, host, user, secret):
      print 'manager_thread:: init'
      Thread.__init__(self)
      self.host = host
      self.user = user
      self.secret = secret
      self.connected = False

   def run(self):
      print 'manager_thread:: run'
      me = ManagerEvents(self.host, self.user, self.secret)
      me.action('QueueStatus')
      print "Waiting for events ...\n"
      asyncore.loop()


