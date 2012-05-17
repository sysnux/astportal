#! /bin/env python
# -*- coding: utf-8 -*-
#! /opt/Python-2.6.7/bin/python
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/


import sys
import getopt
import datetime
import psycopg2

# MAIN ------------------------------------------------------------------------


# Open database connection
sys.path.append('/home/SysNux/Projets/astportal21')
from paste.deploy import appconfig
conf = appconfig('config:/home/SysNux/Projets/astportal21/tiare-sqlite.ini')

from astportal2.config.environment import load_environment
load_environment(conf.global_conf, conf.local_conf)

from astportal2.model import DBSession, CDR
import transaction

import psycopg2
conn = psycopg2.connect('dbname=astportal2 user=postgres')
curs = conn.cursor()
curs.execute('''SELECT acctid, calldate, clid, src, dst, dcontext, channel, 
   dstchannel, lastapp, lastdata, duration, billsec, disposition,
   amaflags, accountcode, uniqueid, userfield, ut, ht, ttc, department, user
   FROM cdr''')

i = err = 0
for d in curs.fetchall():
   i += 1
   c = CDR()
   c.calldate = d[1]
   c.clid = d[2]
   c.src = d[3]
   c.dst = d[4]
   c.dcontext = d[5]
   c.channel = d[6]
   c.dstchannel = d[7]
   c.lastapp = d[8]
   c.lastdata = d[9]
   c.duration = d[10]
   c.billsec = d[11]
   c.disposition = d[12]
   c.amaflags = d[13]
   c.accountcode = d[14]
   c.uniqueid = d[15]
   c.userfield = d[16]
   c.ut = d[17]
   c.ht = d[18]
   c.ttc = d[19]
   c.department = d[20]
   c.user= d[21]
   DBSession.add(c)
   try:
      DBSession.flush()
   except:
      err += 1
      print i, d[0], c
      sys.exit(1)

transaction.commit()
print i, 'inserts', err, 'erreurs'

