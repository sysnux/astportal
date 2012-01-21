#! /opt/Python-2.5.4/bin/python
# -*- coding: utf-8 -*-
#
# Import lines from Asterisk queue_log to PostgreSQL table
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/

import sys
import getopt
import datetime

import turbogears
# Get conf for database connection
turbogears.update_config(configfile="dev.cfg",
        modulename="astportal.config")

from turbogears.database import session
from astportal.model import Queue_log, Queue_event

def usage():
   print '''
Import lines from Asterisk queue_log to PostgreSQL table
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

class __main__:

   verbose, file = options(sys.argv[1:])

   # Fetch latest queue log from database
   try:
      last = Queue_log.query().order_by(Queue_log.ql_id.desc()).first()
      max_id = last.ql_id
      max_ts = last.timestamp
      max_uniqueid = last.uniqueid
   except:
      sys.stderr.write('WARNING: empty database ?\n')
      max_id = -1
      max_uniqueid = ''
      max_ts = datetime.datetime.fromtimestamp(0)

   if verbose:
      sys.stderr.write('Max: id=%d\n' % max_id)

   lines = inserted = errors = 0

   # Loop over lines
   for line in file:
      lines += 1
      line = line.rstrip('\n')
      if verbose:
         sys.stderr.write('%s => \n' % line)
      data = line.split('|')
      ts = datetime.datetime.fromtimestamp(int(data[0]))
      uniqueid = check_none(data[1])
      queue = check_none(data[2])
      channel = check_none(data[3])
      event = check_none(data[4])
      if (ts<max_ts) or (ts==max_ts and uniqueid==max_uniqueid):
         if verbose:
            sys.stderr.write('\tignored !\n')
         continue

      data1 = data2 = data3 = None
      if len(data)>5 and data[5]!='':
         data1 = data[5]
      if len(data)>6 and data[6]!='':
         data2 = data[6]
      if len(data)>7 and data[7]!='':
         data3 = data[7]

      if verbose:
         sys.stderr.write('\t%s, %s, %s, %s, %s, %s, %s, %s => ' % 
               (ts, uniqueid, queue, channel, event, data1, data2, data3))

      try:
         session.begin()
         ql = Queue_log(timestamp=ts, uniqueid=uniqueid, queue=queue, channel=channel, 
               data1=data1, data2=data2, data3=data3)
         ql.event = Queue_event.query.filter_by(event=event).one()
         session.commit()
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

