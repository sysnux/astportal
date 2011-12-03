#! /opt/Python-2.6.7/bin/python
# -*- coding: utf-8 -*-
#
# Calcul du coût des appels sortants
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/

from paste.deploy import appconfig
from astportal2.config.environment import load_environment
from astportal2 import model
from sqlalchemy import desc

conf = appconfig('config:/home/astportal21/csb-shell.ini')
load_environment(conf.global_conf, conf.local_conf)

DBSession = model.DBSession
CDR = model.CDR
Phone = model.Phone

# Dictionnaire utilisateur SIP -> utilisateur, département
sip = {}
for p in DBSession.query(Phone):
   u = p.user.user_name if p.user else 'Inconnu'
   d = p.department.name if p.department else 'Inconnu'
#   print p.sip_id, u, d
   sip[p.sip_id] = {'u': u, 'd': d}

# Recherche des appels sortant vers la passerelle Mediatrix, dont le coût n'a 
# pas encore été calculé
cdrs = DBSession.query(CDR).filter(CDR.dstchannel.like('SIP/TOICSB%'))
cdrs = cdrs.filter(CDR.ht==None)
cdrs = cdrs.order_by(desc(CDR.acctid))

for c in cdrs.all():
   # le canal identifie l'utilisateur SIP
   s = c.channel[4:12]
   if s in sip:
      u = sip[s]['u']
      d = sip[s]['d']
   else:
      u = d = 'Canal inconnu'
   print c.src, c.clid, u, d,  c.dst, c.disposition, c.billsec

