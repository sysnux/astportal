#! /opt/Python-2.7.12/bin/python
# -*- coding: utf-8 -*-
#
# Calcul du coût des communications à partir des logs d'asterisk
# Version Air Tahiti
#
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/

import sys

# Connexion base de données AstPortal via SqlAlchemy
sys.path.append('/opt/astportal3')
from paste.deploy import appconfig
from astportal2.config.environment import load_environment
from astportal2.model import DBSession, CDR, Phone, User, \
   Prix, Zone, OptimumTime #, Pays

from sqlalchemy import func
import getopt
from math import ceil
from decimal import Decimal, getcontext
from datetime import date

conf = appconfig('config:/opt/astportal3/airtahiti.ini')
load_environment(conf.global_conf, conf.local_conf)
getcontext().prec = 6
tva = Decimal(1.10)

# -----------------------------------------------------------------------------
def usage():
   print '''
Script simple de traitement des données d'appels d'asterisk
Usage: ./cdr.py [options]
Options:
\t-t 001         préfixe sortie (peut être répété)
\t-v             mode verbeux
\t-h             aide (cet écran!)
'''
   print "Usage:", sys.argv[0], "[-d] < file"
   sys.exit(1)

def options( argv ):
   try: ( opts, params ) = getopt.getopt( argv, 'hvt:' )
   except: usage()
   v = False # Verbose
   t = [] # Trunks
   for o in opts:
      if o[0] == '-h': usage()
      if o[0] == '-v': v = True
      if o[0] == '-t': t.append(o[1])
   if t == []:
      t = ['PJSIP/gwybat-', 'PJSIP/gwyapt-']
   return v, t

import unicodedata
def channel2user_dept():
   '''Return dict: channel -> (user, department)
   '''
   d = dict()
   for p in DBSession.query(Phone):
      uid = p.user.user_id if p.user else None
      did = p.department.dptm_id if p.department else None
      d[p.exten] = (uid, did)
      d['4086' + p.exten] = (uid, did)

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
         self.forfait = typ * Decimal(840.00)

      elif typ in (25, 50, 100, 200, 250):
         self.forfait = typ * Decimal(660.00)

      elif typ in (500, 1000, 2000, 5000, 10000):
         self.forfait = typ * Decimal(540.00)

      else:
         print u'OPTIMUM_%d pas trouvé (forfait) !!!' % typ
         sys.exit(1)

      self.tarif = {}
      try:
         for o in DBSession.query(OptimumTime). \
               filter(OptimumTime.offre=='OPTIMUM_%d' % typ):
            self.tarif[o.destination] = {
               'dans_forfait': o.prix_df,
               'hors_forfait': o.prix_hf}
      except:
         print u'OPTIMUM_%d pas trouvé (base) !!!' % typ
         sys.exit(1)

      f = typ * 60 * int(round(self.tarif['local_intra']['dans_forfait']*tva))
      if self.forfait != f:
         print u'OPTIMUM_%d erreur forfait : %d <> %d!!!' % (
            typ, self.forfait, f)
         sys.exit(1)

      self.forfait /= tva
      print u'Optimum %d initialisé sur canal "%s", forfait : HT=%.2f, TTC=%d' % (
         self.typ, self.channel, self.forfait, int(self.forfait * tva))

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

      print u'Canal %s, mois %s, total %.2f' % (self.channel, self.month, self.tot)

      for z in zones:
         if (cdr.dst[1:].startswith(z)):
            break
      else:
         print '*' * 20, cdr, u'Zone pas trouvée !!!'
         return None

      if zones_data[z]['zone_tarifaire'] == 'Internationale':
         tarif = self.tarif[zones_data[z]['zaa']]

      elif zones_data[z]['zone_tarifaire'] == 'Nationale':
         if zones_data[z]['ile_ou_pays'] == 'TAHITI':
            tarif = self.tarif['local_intra']
         else:
            tarif = self.tarif['local_inter']

      elif zones_data[z]['zone_tarifaire'] == 'Interdit':
         print '*' * 20, cdr, u'interdit !!!'
         return None

      elif zones_data[z]['zone_tarifaire'] == 'Audiotel_3665':
         print '*' * 20, cdr, u'Audiotel_3665 !!!'
         return None

      elif zones_data[z]['zone_tarifaire'] == 'GSM':
         tarif = self.tarif['GSM']

      else: # autre zone ?
         print '*' * 20, cdr, u'Zone inconnue !!!'
         return None

#      print u'%s : préfixe %s, zone %s, destination %s, tarifs (%s) %s' % (
#         cdr.dst[1:], z, zones_data[z]['zaa'], zones_data[z]['ile_ou_pays'],
#         self.typ, tarif)

      forfait_min = '?'

      if self.tot > self.forfait:
         # Hors forfait
         if cdr.billsec > 60:
            # Taxation à la seconde
            ht = cdr.billsec * tarif['hors_forfait'] / Decimal(60.0)
            forfait_min = 'HORS sec'
         else:
            # Première minute indivisible
            ht = tarif['hors_forfait']
            forfait_min = 'HORS 1 min'
      else:
         # Forfait pas épuisé
         if cdr.billsec > 60:
            # Taxation à la seconde
            ht = cdr.billsec * tarif['dans_forfait'] / Decimal(60.0)
            forfait_min = 'FORFAIT sec'
         else:
            # Première minute indivisible
            ht = tarif['dans_forfait']
            forfait_min = 'FORFAIT 1 min'

      self.tot += ht

      if verbose:
         print '%s : %s -> %s %d sec -> %.2f F.HT (Optimum_%s forfait=%s, hors=%s, %s)' % (
            cdr.calldate, cdr.src, cdr.dst[1:], cdr.billsec, ht, self.typ,
            tarif['dans_forfait'], tarif['hors_forfait'], forfait_min)

      return ht


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
            'ht_normal': p.prix_hp,
            'ht_reduit': p.prix_hc}

   def __call__(self, cdr):
      ''' Calcul du coût d'un appel classique
      Paramètre: objet CDR
      Renvoie: (None, None) si erreur, (TTC, HT) sinon
      '''

      for z in zones:
         if (cdr.dst[1:].startswith(z)):
            break
      else:
         print '*' * 20, cdr, u'zone pas trouvée !!!'
         return None

      if zones_data[z]['zone_tarifaire'] == 'Internationale':

         tarif = self.tarif[zones_data[z]['zaa']]

         if cdr.calldate.hour < 6 or cdr.calldate.hour > 22: # Tarif réduit
            ut =  tarif['ut_reduit']
            ht = tarif['ht_reduit']
         else: # Tarif normal
            ut =  tarif['ut_normal']
            ht = tarif['ht_normal']

      elif zones_data[z]['zone_tarifaire'] == 'Nationale':

         if zones_data[z]['ile_ou_pays'] == 'TAHITI':
            tarif = self.tarif['local_intra']
         else:
            tarif = self.tarif['local_inter']

         if cdr.calldate.hour < 6 or cdr.calldate.hour > 22: # Tarif réduit
            ut =  tarif['ut_reduit']
            ht = tarif['ht_reduit']
         else: # Tarif normal
            ut =  tarif['ut_normal']
            ht = tarif['ht_normal']

      elif zones_data[z]['zone_tarifaire'] == 'Interdit':
         print '*' * 20, cdr, u'interdit !!!'
         return None

      elif zones_data[z]['zone_tarifaire'] == 'Audiotel_3665':
         print '*' * 20, cdr, u'Audiotel_3665 !!!'
         return None

      elif zones_data[z]['zone_tarifaire'] == 'GSM':

         if cdr.calldate.weekday() in (5, 6) or \
               cdr.calldate.hour < 6 or cdr.calldate.hour > 17: # Tarif réduit
            ut =  self.tarif['GSM']['ut_reduit']
            ht = self.tarif['GSM']['ht_reduit']
         else: # Tarif normal
            ut =  self.tarif['GSM']['ut_normal']
            ht = self.tarif['GSM']['ht_normal']

      else: # autre zone ?
         print '*' * 20, cdr, u'Zone inconnue !!!'
         return None

      ht *= int(ceil(cdr.billsec / ut)) # Minute supérieure

      if verbose:
         print u'%s : préfixe %s, zone %s, destination %s, heure %d, duree %d -> ut %d, ht %.2f' % (
            cdr.dst[1:], z, zones_data[z]['zaa'], zones_data[z]['ile_ou_pays'],
            cdr.calldate.hour, cdr.billsec, ut, ht)

      return ht

# MAIN ------------------------------------------------------------------------

# Command line options
verbose, trunks = options( sys.argv[1:] )
if verbose:
   print u'Sorties sélectionnées: %s' % trunks

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
   cmp=lambda x,y: cmp(len(x), len(y)), reverse=True)

# Définitions abonnements
optimum_aero = Optimum(500, '003')
optimum_bat = Optimum(500, '001')
classic = Classic()

nouveau = erreur = 0

# Pour tous les appels sortants facturés dont le coût n'a pas encore été calculé
for cdr in DBSession.query(CDR). \
      filter(func.substr(CDR.dstchannel, 0, 13).in_(trunks)). \
      filter(CDR.billsec>0). \
      filter(CDR.ht==None). \
      order_by(CDR.calldate):

   nouveau += 1

   if cdr.dst is None or cdr.dst[0] != '0':
      # Pas un appel vers l'extérieur !
      continue

   user, dept = c2ud.get(cdr.src, (None, None))

   if cdr.dstchannel.startswith('PJSIP/gwybat-'):
      # T2 bâtiment Optimum 500
      typ = u'Optimum bâtiment'
      ht = optimum_bat(cdr)

   elif cdr.dstchannel.startswith('PJSIP/gwyapt-'):
      # T2 aéroport Optimum 500
      typ = u'Optimum aéroport'
      ht = optimum_aero(cdr)

   if ht is None:
      erreur += 1
      continue

   # Calcul TTC
   if cdr.calldate.date() < date(2013,10,1): # Avant le 1er octobre 2013
      ttc = float(ht * Decimal(1.10))
   else:
      ttc = float(ht * Decimal(1.13))

   if verbose:
      sys.stderr.write('%s, typ=%s, ht=%.2f, ttc=%.2f, uid=%s, did=%s\n' % \
         (cdr, typ, ht, ttc, user, dept))

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

