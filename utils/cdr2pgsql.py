#! /usr/bin/env python
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
conn = psycopg2.connect('dbname=druid user=druid password=OqEibl4gbM')
curs = conn.cursor()

#print verbose, begin, end, file
old_date  = ''
calls = calls_answ = call_max = call_mean = 0
insert = """
INSERT INTO 
cdr	(calldate, clid, src, dst, dcontext, channel, dstchannel, lastapp, 
	lastdata, duration, billsec, disposition, amaflags, accountcode,
	uniqueid, userfield) 
VALUES 	( '%s',  '%s','%s','%s',     '%s',    '%s',        '%s',   '%s',
	    '%s',       %d,      %d,        '%s',        3,          '',
	    '%s',      '') """
# Loop over CDR data
for line in sys.stdin:
	line = line.replace( '"', '' )
	# Extract data
	try:
		( accountcode, src, dst, dcontext, clid, channel, dstchannel, lastapp, lastdata, start,
		answer, end, duration, billsec, disposition, amaflags, uniqueid, cr ) = line.split(',')
		# Format data
		date, time = start.split( ' ' )
		billsec  = int( billsec )
		duration = int( duration )
		curs.execute( insert % (  start,  clid, src,  dst, dcontext, channel,  dstchannel, lastapp, lastdata, duration, billsec, disposition, uniqueid)) # , userfield) )
	except:
		print 'ERREUR:',  line.split(',')

conn.commit()
