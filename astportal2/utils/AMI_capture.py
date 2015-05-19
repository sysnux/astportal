#! /bin/env python
# -*- coding: utf-8 -*-
#
# AMI events capture to file (format JSON)
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/

from os import SEEK_END
from datetime import datetime
from time import sleep
from sys import stderr
printerr = stderr.write

#from tg import config
from astportal2.pyst import manager
import json


def trace(event, manager):
   # event.headers is a dict
   global compte
   t = datetime.now()
   td = float((t-orig).seconds) + float((t-orig).microseconds) / 1000000
   printerr('Received event %d type %s\n' % (1+compte, event.headers['Event']))
   fichier.write('[%f, ' % (td))
   json.dump(event.headers, fichier, indent=2)
   fichier.write('],\n')
   fichier.flush()
   compte += 1


compte = 0
fichier = open('/tmp/ami_events.json', mode='w')
fichier.write('[\n')
orig = datetime.now()
#conf = eval(config.get('asterisk.manager'))
#printerr('%s\n' % (conf[0]))
man = manager.Manager()
printerr('Connect to AMI... ')
#man.connect(conf[0][0])
man.connect('localhost')
printerr('OK!\n')

printerr('Login... ')
#man.login(conf[0][1], conf[0][2])
man.login('astman', 'astmaster')
printerr('OK!\n')

printerr('Register events callback... ')
man.register_event('*', trace)
printerr('OK!\n')

printerr('Request status... ')
man.status()
printerr('OK!\n')

# Do nothing, just capture AMI events
while True:
   try:
      sleep(60)
   except:
      break

printerr('Logoff from AMI... ')
man.logoff()
printerr('OK!\n')

# XXX delete last ','
#fichier.seek(-1, SEEK_END)
#fichier.truncate()
fichier.write(']\n') 
fichier.close()

