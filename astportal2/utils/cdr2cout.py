#! /opt/tg22env/bin/python
# -*- coding: utf-8 -*-
#
# Calcul du coût des communications à partir des logs d'asterisk
#
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/

import sys

# Connexion base de données AstPortal via SqlAlchemy
sys.path.insert(0, '/home/SysNux/Projets/astportal21')
from paste.deploy import appconfig
from astportal2.config.environment import load_environment
from astportal2.model import DBSession, CDR, Phone, User, \
   Prix, Zone, OptimumTime #, Pays

from sqlalchemy import func
import getopt
from math import ceil
from decimal import Decimal, getcontext

conf = appconfig('config:/opt/astportal21/socredo.ini')
load_environment(conf.global_conf, conf.local_conf)
getcontext().prec = 6
tva = Decimal('1.13')

# -----------------------------------------------------------------------------
def usage():
   print '''
Script simple de traitement des données d'appels d'asterisk
Usage: ./cdr.py [options]
Options:
\t-v             mode verbeux
\t-h             aide (cet écran!)
'''
   print "Usage:", sys.argv[0], "[-d] < file"
   sys.exit(1)

def options( argv ):
   try: ( opts, params ) = getopt.getopt( argv, 'hv:' )
   except: usage()
   v = False # Verbose
   t = [] # Trunks
   for o in opts:
      if o[0] == '-h': usage()
      if o[0] == '-v': v = True
   return v

import unicodedata
def channel2user_dept():
   '''Return dict: channel -> (user, department)
   '''
   d = dict()
   for p in DBSession.query(Phone):
      uid = p.user.user_id if p.user else None
      did = p.department.dptm_id if p.department else None
      d[p.exten] = (uid, did)

   return d


class Optimum(object):
   ''' Objet appelable tarif Optimum
   L'objet est nécessaire pour garder la mémoire du total du mois et des tarifs.
   Le calcul est basé sur la destination et la durée à la seconde, sauf première
   minute indivisible. Le coût est différent selon que le forfait mensuel est
   dépassé ou non.
   '''

   def __init__(self, typ, chan):
      ''' A l'initialisation, le type de forfait est passé, les tarifs 
      par destination sont chargés à partir de la base de données.
      '''
      self.typ = typ
      self.tot = 0
      self.month = None
      self.channel = chan

      if typ in (1, 2, 4, 8, 16):
         self.forfait = typ * 840

      elif typ in (25, 50, 100, 200, 250):
         self.forfait = typ * 660

      elif typ in (500, 1000, 2000, 5000, 10000):
         self.forfait = typ * 540

      else:
         print u'OPTIMUM_%d pas trouvé (forfait) !!!' % typ
         sys.exit(1)

      self.tarif = {}
      try:
         for o in DBSession.query(OptimumTime). \
               filter(OptimumTime.offre=='OPTIMUM_%d' % typ):
            self.tarif[o.destination] = {
               'dans_forfait': o.prix_df*tva,
               'hors_forfait': o.prix_hf*tva}
      except:
         print u'OPTIMUM_%d pas trouvé (base) !!!' % typ
         sys.exit(1)

      f = typ * 60 * int(round(self.tarif['local_intra']['dans_forfait']))
      if self.forfait != f:
         print u'OPTIMUM_%d erreur forfait : %d <> %d!!!' % (
            typ, self.forfait, f)
         sys.exit(1)

      print u'Optimum %d initialisé sur canal "%s", forfait : TTC=%d, HT=%d' % (
         self.typ, self.channel, self.forfait, int(self.forfait / tva))

   def __call__(self, cdr):
      ''' Calcul du coût pour un appel représenté par un CDR.
      Paramètre: objet CDR
      Renvoie: (None, None) si erreur, (TTC, HT) sinon
      '''

      if self.month is None or self.month != cdr.calldate.strftime('%Y%m'): 
         # Premier appel, ou changement de mois, il faut chercher le total du
         # mois déjà facturé
         print u'Canal %s, nouveau mois : %s -> %s' % (
            self.channel, self.month, cdr.calldate.strftime('%Y%m'))
         self.month = cdr.calldate.strftime('%Y%m')
         tot, = DBSession.query(func.sum(CDR.billsec)). \
            filter(func.to_char(cdr.calldate, 'YYYYMM')==self.month). \
            filter(CDR.calldate<cdr.calldate). \
            filter(CDR.dstchannel==self.channel). \
            filter(CDR.ht!=None).one()
         self.tot = tot if tot is not None else 0

      print u'Canal %s, mois %s, total %d' % (self.channel, self.month, self.tot)

      for z in zones:
         if (cdr.dst[2:].startswith(z)):
            break
      else:
         print '*' * 20, cdr, u'Zone pas trouvée !!!'
         return None, None

      if zones_data[z]['zone_tarifaire'] == 'Internationale':
         tarif = self.tarif[zones_data[z]['zaa']]

      elif zones_data[z]['zone_tarifaire'] == 'Nationale':
         if zones_data[z]['ile_ou_pays'] == 'TAHITI':
            tarif = self.tarif['local_intra']
         else:
            tarif = self.tarif['local_inter']

      elif zones_data[z]['zone_tarifaire'] == 'Interdit':
         print '*' * 20, cdr, u'interdit !!!'
         return None, None

      elif zones_data[z]['zone_tarifaire'] == 'Audiotel_3665':
         print '*' * 20, cdr, u'Audiotel_3665 !!!'
         return None, None

      elif zones_data[z]['zone_tarifaire'] == 'GSM':
         tarif = self.tarif['GSM']

      else: # autre zone ?
         print '*' * 20, cdr, u'Zone inconnue !!!'
         return None, None

#      print u'%s : préfixe %s, zone %s, destination %s, tarifs (%s) %s' % (
#         cdr.dst[2:], z, zones_data[z]['zaa'], zones_data[z]['ile_ou_pays'],
#         self.typ, tarif)

      forfait_min = '?'

      if self.tot > self.forfait:
         # Hors forfait
         if cdr.billsec > 60:
            # Taxation à la seconde
            ttc = int(ceil(cdr.billsec * tarif['hors_forfait'] / Decimal(60.0)))
            forfait_min = 'HORS sec'
         else:
            # Première minute indivisible
            ttc = tarif['hors_forfait']
            forfait_min = 'HORS 1 min'
      else:
         # Forfait pas épuisé
         if cdr.billsec > 60:
            # Taxation à la seconde
            ttc = int(ceil(cdr.billsec * tarif['dans_forfait'] / Decimal(60.0)))
            forfait_min = 'FORFAIT sec'
         else:
            # Première minute indivisible
            ttc = tarif['dans_forfait']
            forfait_min = 'FORFAIT 1 min'

      self.tot += ttc

      if verbose:
         print '%s : %s -> %s %d sec -> %d F.TTC (Optimum_%s forfait=%s, hors=%s, %s)' % (
            cdr.calldate, cdr.src, cdr.dst[2:], cdr.billsec, ttc, self.typ,
            tarif['dans_forfait'], tarif['hors_forfait'], forfait_min)

      return  ttc, int(round(ttc / tva))


class Classic(object):
   ''' Objet appelable tarif Classique
   L'objet permet de charger les tarifs une seule fois à l'initialisation.
   Le coût est basé sur la destination et l'heure de l'appel. La durée est 
   calculée par rapport à une unité indivisible exprimée en seconde (ut).
   '''

   def __init__(self):
      ''' Chargement des tarifs
      '''
      self.tarif = {}
      for p in DBSession.query(Prix):
         self.tarif[p.zone_destination] = {
            'ut_normal': p.step_hp, 'ut_reduit': p.step_hc,
            'ttc_normal': int(round(p.prix_hp*tva)),
            'ttc_reduit': int(round(p.prix_hc*tva))}

   def __call__(self, cdr):
      ''' Calcul du coût d'un appel classique
      Paramètre: objet CDR
      Renvoie: (None, None) si erreur, (TTC, HT) sinon
      '''

      for z in zones:
         if (cdr.dst[2:].startswith(z)):
            break
      else:
         print '*' * 20, cdr, u'zone pas trouvée !!!'
         return None, None

      if zones_data[z]['zone_tarifaire'] == 'Internationale':

         tarif = self.tarif[zones_data[z]['zaa']]

         if cdr.calldate.hour < 6 or cdr.calldate.hour > 22: # Tarif réduit
            ut =  tarif['ut_reduit']
            ttc = tarif['ttc_reduit']
         else: # Tarif normal
            ut =  tarif['ut_normal']
            ttc = tarif['ttc_normal']

      elif zones_data[z]['zone_tarifaire'] == 'Nationale':

         if zones_data[z]['ile_ou_pays'] == 'TAHITI':
            tarif = self.tarif['local_intra']
         else:
            tarif = self.tarif['local_inter']

         if cdr.calldate.hour < 6 or cdr.calldate.hour > 22: # Tarif réduit
            ut =  tarif['ut_reduit']
            ttc = tarif['ttc_reduit']
         else: # Tarif normal
            ut =  tarif['ut_normal']
            ttc = tarif['ttc_normal']

      elif zones_data[z]['zone_tarifaire'] == 'Interdit':
         print '*' * 20, cdr, u'interdit !!!'
         return None, None

      elif zones_data[z]['zone_tarifaire'] == 'Audiotel_3665':
         print '*' * 20, cdr, u'Audiotel_3665 !!!'
         return None, None

      elif zones_data[z]['zone_tarifaire'] == 'GSM':

         if cdr.calldate.weekday() in (5, 6) or \
               cdr.calldate.hour < 6 or cdr.calldate.hour > 17: # Tarif réduit
            ut =  self.tarif['GSM']['ut_reduit']
            ttc = self.tarif['GSM']['ttc_reduit']
         else: # Tarif normal
            ut =  self.tarif['GSM']['ut_normal']
            ttc = self.tarif['GSM']['ttc_normal']

      else: # autre zone ?
         print '*' * 20, cdr, u'Zone inconnue !!!'
         return None, None

      ttc = int(ceil(cdr.billsec / ut)) * ttc

      if verbose:
         print u'%s : préfixe %s, zone %s, destination %s, heure %d, duree %d -> ut %d, ttc %d' % (
            cdr.dst[2:], z, zones_data[z]['zaa'], zones_data[z]['ile_ou_pays'],
            cdr.calldate.hour, cdr.billsec, ut, ttc)

      return  ttc, int(round(ttc / tva))

# MAIN ------------------------------------------------------------------------

# Command line options
verbose = options( sys.argv[1:] )

# Dict: channel -> (user, department)
c2ud = channel2user_dept()

# Chargement du dictionnaire zones : clé = préfixe
zones_data = {}
for z in DBSession.query(Zone):
   zones_data[z.prefixe] = {
      'code_geo': z.code_geo, 'zone_tarifaire': z.zone_tarifaire,
      'zaa': z.zaa, 'zam': z.zam, 'zna': z.zna,
      'ile_ou_pays': z.ile_ou_pays, 'surtaxe_pcv': z.surtaxe_pcv}

# Préfixes triés dans l'ordre inverse de leur longueur, afin de faire 
# correspondre la destination au préfixe le plus pertinent
zones = sorted(zones_data.keys(),
   cmp = lambda x,y: cmp(len(x), len(y)), reverse=True)

# Définition(s) abonnement(s)
optimum_soc = Optimum(500, '1')

nouveau = erreur = 0

# Pour tous les appels sortants facturés dont le coût n'a pas encore été calculé
for cdr in DBSession.query(CDR). \
      filter(func.substr(CDR.dstchannel, 0, 10)=='DAHDI/i1/'). \
      filter(CDR.billsec>0). \
      filter(CDR.ht==None). \
      order_by(CDR.calldate):

   nouveau += 1

   user, dept = c2ud.get(cdr.src, (None, None))

   typ = u'Optimum bâtiment'
   ttc, ht = optimum_soc(cdr)

   if ht is None:
      erreur += 1
      continue

   if verbose:
      sys.stderr.write('%s, typ=%s, ht=%d, uid=%s, did=%s\n' % \
         (cdr, typ, ht, user, dept))

   # Mise à jour coût
   cdr.ht = ht
   cdr.ttc = ttc
   cdr.user = user
   cdr.department = dept
   DBSession.flush()

import transaction
transaction.commit()

print u'Traitement terminé : %d nouveaux appels sortants, %d non traités.' % \
   (nouveau, erreur)

