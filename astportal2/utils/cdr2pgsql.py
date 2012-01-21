#! /opt/Python-2.5.5/bin/python
# -*- coding: utf-8 -*-
#
# Simple script to process asterisk CDR logs
# Jean-Denis Girard <jd.girard@sysnux.pf>

import sys
import getopt
import re
import psycopg2

# From asterisk-1.0.2/doc/README.cdr 2004-01-17/v0.7.1
#   1. accountcode: What account number to use, (string, 20 characters)
#   2. src: Caller*ID number (string, 80 characters)
#   3. dst: Destination extension (string, 80 characters)
#   4. dcontext: Destination context (string, 80 characters)
#   5. clid: Caller*ID with text (80 characters)
#   6. channel: Channel used (80 characters)
#   7. dstchannel: Destination channel if appropriate (80 characters)
#   8. lastapp: Last application if appropriate (80 characters)
#   9. lastdata: Last application data (arguments) (80 characters)
#  10. start: Start of call (date/time)
#  11. answer: Answer of call (date/time)
#  12. end: End of call (date/time)
#  13. duration: Total time in system, in seconds (integer), from dial to hangup
#  14. billsec: Total time call is up, in seconds (integer), from answer to hangup
#  15. disposition: What happened to the call: ANSWERED, NO ANSWER, BUSY
#  16. amaflags: What flags to use: DOCUMENTATION, BILL, IGNORE etc, 
#      specified on a per channel basis like accountcode.
#  17. user field: A user-defined field, maximum 255 characters 

# Open database connection
conn = psycopg2.connect('dbname=astportal2 user=postgres')
curs = conn.cursor()

#print verbose, begin, end, file
old_date  = ''
calls = calls_answ = call_max = call_mean = 0
insert = '''
INSERT INTO 
cdr	(calldate, clid, src, dst, dcontext, channel, dstchannel, lastapp, 
	lastdata, duration, billsec, disposition, uniqueid)
VALUES 	(   %s,   %s,  %s,  %s,       %s,      %s,         %s,      %s,
	      %s,       %s,      %s,          %s,       %s)'''

# Loop over CDR data
import csv
#data = csv.reader(open(args.csv_file,'rb'), delimiter=',')
for line in csv.reader(sys.stdin, delimiter=','):

# ['', '500300', 'poste1', 'default', '500300', 
#  'SIP/7209-095d4d28', 'SIP/poste3-095e39e0', 
#  'Dial', 'SIP/poste1&SIP/poste3', 
#  '2011-11-21 17:37:07', '2011-11-21 17:37:07', '2011-11-21 17:38:01', 
#  '54', '54', 'ANSWERED', 'DOCUMENTATION', '1321897027.0', '']

	# Extract data
	try:
		( accountcode, src, dst, dcontext, clid, 
			channel, dstchannel, 
			lastapp, lastdata, 
			start, answer, end, 
			duration, billsec, disposition, amaflags, uniqueid, x ) = line
		# Format data
		date, time = start.split( ' ' )
		billsec  = int( billsec )
		duration = int( duration )
		curs.execute( insert, (  start,  clid, src,  dst, dcontext, channel,  
         dstchannel, lastapp, lastdata, duration, billsec, disposition, uniqueid))
	except:
		print 'ERREUR:', sys.exc_info()[0]
		print 'Ligne', line
		print 'Données:', start,  clid, src,  dst, dcontext, channel,  dstchannel, lastapp, lastdata, duration, billsec, disposition
		sys.exit(1)

conn.commit()
