#! /bin/env python
# -*- coding: utf-8 -*-
#
# Script to compute the number of concurrent (simultaneous) calls on an 
# Asterisk system, based on CDR data.
#
# To determine the concurrent number of calls, we need to know when a new
# call arrives in the system, and when a call ends (two events). Beginning 
# and end of two or more calls can obviously be interleaved, eg.:
#  +-----------+-----+-----------------+
#  | Beginning | End | Number of calls |
#  +-----------+-----+-----------------+
#  |           |     |        0        |
#  |     #1    |     |        1        |
#  |     #2    |     |        2        |
#  |     #3    |     |        3        |
#  |           |  #1 |        2        |
#  |     #4    |     |        3        |
#  |           |  #3 |        2        |
#  |           |  #4 |        1        |
#  |           |  #2 |        0        |
#  +-----------+-----+-----------------+
#
# But Asterisk (usually) records only one CDR per call, after hangup:
#  . 'calldate' is the beginning of the call, stored as timestamp.
#  . 'duration' is stored as an integer (number of seconds)
#
# So we create two rows from one CDR:
#  . one at the beginning of the call, so it is one more call in the system
#  . one at the end of the call, so it is one less call in the system
#
# End of call is "begin_of_call + duration", converted to timestamp by the formula: 
#  calldate + duration * interval '1 second'
#
# Then, by ordering by timestamp, we obtain an ordered list of +1 call, -1 call.
# So following this list, and adding +1, +1, +1, -1, +1, ... we know the number
# of calls at each step.
#
# Jean-Denis Girard <jd.girard@sysnux.pf>


# Open database connection
#import psycopg2
#conn = psycopg2.connect('dbname=astportal2 user=postgres')
#curs = conn.cursor()

from paste.deploy import appconfig
from astportal2.config.environment import load_environment
from astportal2.model import DBSession, CDR
from sqlalchemy import desc, text

# One CDR row -> two events row (+1 call at the beginning, -1 at the end)
sql = '''SELECT id, ts, step FROM (
   (SELECT acctid AS id, calldate as ts, 1 as step 
   FROM cdr 
   WHERE billsec>0)
UNION 
   (SELECT acctid AS id, calldate+duration * interval '1 second' as ts, -1 as step
   FROM cdr 
   WHERE billsec>0)
) AS y 
ORDER BY ts, step DESC
'''
#curs.execute(sql)

ccalls = max = 0
#for id, ts, x in curs.fetchall():
for id, ts, x in DBSession.query(CDR):
   ccalls += x
   if ccalls > max: max = ccalls
   warning = ' ******' if ccalls<0 else '' # Something wrong !
   print u'%d, %s (%2d) %d%s' % (id, ts, x, ccalls, warning)

print 'Max number of concurrent calls: %d' % max

