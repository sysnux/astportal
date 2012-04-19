#! /usr/bin/env python
# -*- coding: utf-8 -*-

from asterisk import *

i=0

def handle_event(event, manager):
   global i
   i += 1
   print '\n--------------------------'
   print 'Event %d: %s' % (i,event.name)
   for x in event.headers:
      print x, event.get_header(x)

# Main
m = manager.Manager()
m.connect('localhost',5038)
m.login('astmaster','asterisk')
m.register_event('*', handle_event)

s = m.send_action({'Action':'QueueStatus'})
s = m.send_action({'Action':'IAXpeers'})

import time
time.sleep(5)
m.logoff()
