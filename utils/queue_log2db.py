#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Import lines from Asterisk queue_log to astportal database
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/

from paste.deploy import appconfig
#conf = appconfig('config:/home/astportal21/csb-shell.ini')
conf = appconfig('config:/home/SysNux/Projets/astportal21/tiare.ini')

from astportal2.config.environment import load_environment
load_environment(conf.global_conf, conf.local_conf)
from astportal2.model import DBSession, Queue_log, Queue_event, Phone, User

from sqlalchemy import desc
import sys
import getopt
import datetime
import unicodedata


def usage():
   print '''
Import lines from Asterisk queue_log to database
Usage: %s [options] < /var/log/asterisk/queue_log
Options:
\t-v     verbose
\t-f     file
\t-h     help
''' % ( sys.argv[0] )
   sys.exit(1)

def options( argv ):
   v = False;
   f = sys.stdin
   try:
      ( opts, params ) = getopt.getopt( argv, 'hvf:' )
   except:
      usage()
   for o in opts:
      if o[0] == '-h': usage()
      if o[0] == '-v': v = True
      if o[0] == '-f':
	 f = o[1]
	 try:
	    f = open(f)
	 except:
	    print "Open file error:", f
	    sys.exit(1)
   return ( v, f )

def check_none(x):
   if x=='NONE': return None
   else: return x

def event2id():
   '''Event name to event id mapping
   '''
   return dict([(e.event, e.qe_id) for e in DBSession.query(Queue_event)])

def channel2user_dept():
   '''Channel to user, department mapping
   '''
   d = dict()
   for p in DBSession.query(Phone):
      uid = p.user.user_id if p.user else None
      did = p.department.dptm_id if p.department else None
      d['SIP/' + p.sip_id] = (uid, did)
   for u in DBSession.query(User):
      # cidname
      k = unicodedata.normalize('NFKD', u.display_name).encode('ascii','ignore')
      did = None
      if u.phone:
         p = u.phone[0]
         if p.department:
            did = p.department.dptm_id
      d[k] = (u.user_id, did)

   return d

class __main__:

   verbose, file = options(sys.argv[1:])

   # Event -> event_id
   ev2id = event2id()

   # Channel -> (user, department)
   ch2ud = channel2user_dept()
#   for k, v in ch2ud.iteritems():
#      print '%s => %s' % (k, v)
#   sys.exit(0)

   # Fetch latest queue log from database
   try:
      last = DBSession.query(Queue_log).order_by(Queue_log.ql_id.desc()).first()
      max_id = last.ql_id
      max_ts = last.timestamp
      max_uniqueid = last.uniqueid
   except:
      sys.stderr.write('WARNING: empty database ?\n')
      max_id = -1
      max_uniqueid = ''
      max_ts = datetime.datetime.fromtimestamp(0)

   if verbose:
      sys.stderr.write('Max: id=%d, ts=%s, uid=%s\n' % (
         max_id, max_ts, max_uniqueid))

   lines = inserted = errors = 0

   # Loop over lines
   for line in file:
      lines += 1
      line = line[:-1]
      if verbose:
         sys.stderr.write('%s => \n' % line)
      data = line.split('|')
      ts = datetime.datetime.fromtimestamp(int(data[0]))
      uniqueid = check_none(data[1])
      queue = check_none(data[2])
      channel = check_none(data[3])
      event = ev2id.get(data[4])
      if (ts<max_ts) or (ts==max_ts and uniqueid==max_uniqueid):
         if verbose:
            sys.stderr.write('\tignored (already in db) !\n')
         continue

      user, dptm = ch2ud.get(channel, (None, None))

      data1 = data2 = data3 = None
      if len(data)>5 and data[5]!='':
         data1 = data[5]
      if len(data)>6 and data[6]!='':
         data2 = data[6]
      if len(data)>7 and data[7]!='':
         data3 = data[7]

      if verbose:
         sys.stderr.write('\t%s, %s, %s, %s, %d, %s, %s, %s, %s, %s => ' % 
               (ts, uniqueid, queue, channel, event, user, dptm, data1, data2, data3))

#      ql = Queue_log(timestamp=ts, uniqueid=uniqueid, queue=queue, channel=channel, 
#         event=event, data1=data1, data2=data2, data3=data3)
#      ql.event = ev2id[event]
#      DBSession.add(ql)
#      DBSession.flush()
      try:
         ql = Queue_log(timestamp=ts, uniqueid=uniqueid, queue=queue, channel=channel, 
            queue_event_id=event, data1=data1, data2=data2, data3=data3,
            user=user, department=dptm)
         DBSession.add(ql)
         DBSession.flush()
         inserted += 1
         if verbose:
            sys.stderr.write('OK !\n')
      except:
         errors += 1
         if verbose:
            sys.stderr.write('ERROR !\n')
         else:
            sys.stderr.write('ERROR: %s !\n' % line)

   # /loop
   if verbose:
      sys.stderr.write('Finished: %d lines processed, %d records inserted into database, %d errors\n'
            % (lines, inserted, errors) )

# Normal end
import transaction
transaction.commit()
