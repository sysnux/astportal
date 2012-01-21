#! /bin/env python
# -*- coding: utf-8 -*-
#! /opt/Python-2.6.7/bin/python
#
# Calcul du coût des communications à partir des logs d'asterisk
# Prix d’une communication en local :
#  +--------+------------+--------------+
#  | Tarif  | Vers fixes | Vers mobiles |
#  +--------+------------+--------------+
#  | Plein  | 10,5 F/mn  | 9,45 F/30s   |
#  | Réduit | 6,3 F/mn   | 6,3 F/30s    |
#  +--------+------------+--------------+
# Tarif plein : du lundi au vendredi de 7h à 19h hors jours fériés. 
# voir : http://www.opt.nc/index.php?option=com_content&view=article&id=171&Itemid=219
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/


import sys
import getopt
import csv
import re
import math
import urllib
import datetime

# -----------------------------------------------------------------------------
def usage():
   print '''
Script simple de traitement des données d'appels d'asterisk
Usage: ./cdr.py [options] < Master.csv
Options:
\t-v             mode verbeux
\t-d 100         cours US$
\t-h             aide (cet écran!)
'''
   print "Usage:", sys.argv[0], "[-d] < file"
   sys.exit(1)

def options( argv ):
   try: ( opts, params ) = getopt.getopt( argv, 'hvd:' )
   except: usage()
   v = False
   d = 0
   for o in opts:
      if o[0] == '-h': usage()
      if o[0] == '-v': v = True
   return ( v, d )

import unicodedata
def channel2user_dept():
   '''Return dict: channel -> (user, department)
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

def mobile_normal_reduced(dt):
   '''Check for normal / reduced hours
   Returns True if normal
   '''
   if dt.weekday() in (6,7):
      return False
   if datetime.time(6,0,0) <= dt.time() < datetime.time(18,0,0):
      return True
   return False

def fixed_normal_reduced(dt):
   '''Check for normal / reduced hours
   Returns True if normal
   '''
#   if dt.weekday() in (6,7):
#      return False
   if datetime.time(6,0,0) <= dt.time() < datetime.time(22,0,0):
      return True
   return False

# MAIN ------------------------------------------------------------------------

# Command line options
( verbose, usd2cfp ) = options( sys.argv[1:] )

# Open database connection
sys.path.append('/home/astportal21')
from paste.deploy import appconfig
#conf = appconfig('config:/home/astportal21/csb-shell.ini')
conf = appconfig('config:/home/SysNux/Projets/astportal21/tiare.ini')

from astportal2.config.environment import load_environment
load_environment(conf.global_conf, conf.local_conf)
from astportal2.model import DBSession, CDR, Phone, User

# Dict: channel -> (user, department)
c2ud = channel2user_dept()

# Look for outgoing calls, where ht not computed
q = DBSession.query(CDR). \
      filter(CDR.lastdata.like('Dahdi/g1/%')). \
      filter(CDR.billsec>0). \
      filter(CDR.ht==None)
from math import ceil
for cdr in q:
   user, dept = c2ud.get(cdr.channel[:12], (None, None))

   typ = None

   if len(cdr.dst) in (6, 7): # appel local

      if cdr.dst[0] in ('7', '3'): # Mobile
         if mobile_normal_reduced(cdr.calldate):
            typ = 'mob-nor'
            ut = (cdr.billsec/34 + 1)
         else:
            typ = 'mob-red'
            (cdr.billsec/60 + 1)

      else: # Fixe
         if fixed_normal_reduced(cdr.calldate):
            typ = 'fix-nor'
            ut = (cdr.billsec/240 + 1) 
         else:
            typ = 'fix-red'
            (cdr.billsec/480 + 1)

      ht =  3106 * ut

#   elif cdr.dst.startswith(('19689', '019689')): # Polynésie française
#
#      ut = cdr.billsec/60 + 1
#      if cdr.dst.startswith(('196897', '0196897', '196893', '0196893')): # Mob 37,80
#         ht = 3780 * ut
#
#      else: # Fixe 31,50
#         ht = 3150 * ut

   else:
      typ = 'inc'
      sys.stderr.write('ATTENTION, non traite : %s, %s, %s\n' % 
         (cdr, user, dept))
      ut = ht = 0

   ht = int(ceil(ht))
   ttc = int(ceil(ht*1.1))
   if verbose:
      sys.stderr.write('%s, typ=%s, ut=%d, ht=%d, uid=%s, did=%s\n' % (cdr, typ, ut, ht, user, dept))

   cdr.ut = ut
   cdr.ht = ht
   cdr.ttc = ttc
   cdr.user = user
   cdr.department = dept
   DBSession.flush()

import transaction
transaction.commit()
