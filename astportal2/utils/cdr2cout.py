#! /bin/env python
# -*- coding: utf-8 -*-
#! /opt/Python-2.7.3/bin/python
#
# Calcul du coût des communications à partir des logs d'asterisk
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


# Numéros particuliers, îles
# Cabines publiques Tahiti ; 889
# Cabines publiques Iles ; 88^9
# AHE ; 96
# AMANU ; 88
# ANAA ; 98
# APATAKI ; 96 
# ARATIKA ; 88
# ARUTUA ; 96
# BORA BORA ; 67 - 60 - 66
# FAAITE ; 98
# FAKAHINA ; 97
# FAKARAVA ; 98 - 93
# FANGATAU ; 97
# FATU HIVA ; 92
# HAO ; 93 - 97
# HIKUERU ; 96
# HIVA OA ; 92
# HUAHINE ; 68 - 60 - 66 - 67
# KATIU ; 96
# KAUEHI ; 96
# KAUKURA ; 96
# MAIAO ; 56
# MAKATEA ; 96
# MAKEMO ; 98
# MANGAREVA ; 97
# MANIHI ; 96 - 93
# MAROKAU ; 96
# MARUTEA SUD ; 96
# MATAIVA ; 96
# MAUPITI ; 67 - 60
# MOOREA ; 56 - 55
# NAPUKA ;  97
# NIAU ; 96
# NUKU HIVA ; 92 - 91
# NUKUTAVAKE ; 98
# PUKA-PUKA ; 97
# PUKARUA ; 96
# RAIATEA ; 66 - 60 - 67 - 65
# RAIVAVE ; 95
# RANGIROA ; 96 - 93
# RAPA ; 95
# RARAKA ; 96
# RAROIA ; 96
# REAO ; 96
# RIMATARA ; 94
# RURUTU ; 94
# TAENGA ; 96
# TAHAA ; 65 - 60 - 66
# TAHUATA ; 92
# TAKAPOTO ; 98
# TAKAROA ; 98
# TAKUME ; 96
# TATAKOTO ; 97
# TEPOTO NORD ; 88
# TIKEHAU ; 96
# TOAU ; 96
# TUBUAI ; 95 - 93
# TUREIA; 98
# UA-HUKA ; 92
# UA POU ; 92
# VAHITAHI ; 96
# VAIRAATEA 96
iles = [ '55', '56', '60', '65', '66', '67', '68',
'91', '92', '93', '94', '95', '96', '97', '98' ]

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
      if o[0] == '-d': d = float(o[1])
   if d==0:
      # Si cours pas fixé, on interrog la Banque de Tahiti
      try:
         page = urllib.urlopen('https://secure.banque-tahiti.pf/cours/corps.html')
         # On cherche la ligne /&nbsp;Dollar am ricain (Vente de Billets)   79.963 F.CFP</td>/
         r = re.compile('Dollar am.ricain \(Vente de Billets\)\s+(\d+\.\d+) F.CFP</td>')
         for l in page:
            m = r.search(l)
            if m:
               d, = m.groups(1)
               d = 100.0 * float(d)
               break
      except:
         sys.stderr.write('ERREUR: accès site Banque de Tahiti impossible\n')
         d = 10000.00 # Conversion US$ => F.CFP
         sys.stderr.write('Attention, utilisation du cours US$ par défaut: %.2f\n' % (d) )
   return ( v, d )

# -----------------------------------------------------------------------------
# Lecture du fichier Teliax teliax_rates.csv
# http://media.teliax.com/rates.csv
def teliax(fich):
   try:
      f = open(fich)
   except:
      sys.stderr.write('Open file error: ' + fich)
      sys.exit(1)
   f.readline() # Ignore entête
   codes = { '1': (0.02,re.compile('1')) } # Etats Unis pas inclus dans la liste Teliax !
   r = re.compile('^(.*),(\d+),(\d*\.\d*)')
   for line in f:
      m = r.search(line)
      try:
         ( country, code, rate ) = m.groups()
      except:
         sys.stderr.write('ERREUR: fichier tarif TelIAX::' + line)
         continue
      rate = float(rate)
      codes[code] = (rate, re.compile(code))
   # Renvoi un dictionnaire: indicatif => [coût,regex]
   return codes

# -----------------------------------------------------------------------------
# Lecture du fichier des tarifs internationaux de l'OPT
# voir http://www.opt.pf/map_fuseau/
# Pour enregistrer le fichier, utiliser la commande:
# lynx -source -preparsed http://www.opt.pf/map_fuseau/ | grep "<OPTION "
# Tarifs Optimum (scannés !) puis OCR (Tesseract), puis filtrés par:
# perl -pe 's/(.*) (MOBILE|FIXE|AUTRE) (\d*) ([+-\d]*) (\D) (\d\d?) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)/$1;$2;$3;$4;$5;$6;$7;$8;$9;$10;$11;$12;$13/' < inter.txt > inter.csv
def opt(fich):
   try:
      f = csv.reader(open(fich),delimiter=';')
   except:
      sys.stderr.write('Open CSV file error: ' + fich)
      sys.exit(1)
   codes = {}
   re_opt = re.compile('<OPTION.*VALUE="(.*)\|(.*)\|(.*)\|(.*)">(.*)')
   for line in f:
      try:
         # ttc0 = classic
         # ttc1 = optimum 
         # ttc2 = optimum 1-16
         # ttc3 = optimum 25-250
         # ttc4 = optimum 500-1000
         ( pays, type, code, dec, auto, manu, impuls, ttc0, ttc1, ttc2, ttc3, ttc4 ) = line
         #( dec, code, auto, manu, pays ) = r.groups()
      except:
         sys.stderr.write('ERREUR: fichier des tarifs OPT: ' + str(line) + '\n')
         continue
      if auto in 'ABCDE': # Groupe défini ?
         codes[code] = (auto, re.compile(code), pays, type, dec, manu, impuls, ttc0, ttc1, ttc2, ttc3, ttc4 )
   # Renvoi un dictionnaire: indicatif => groupe automatique
   return codes

# -----------------------------------------------------------------------------
# Sortie résultats:
# Service,Poste,Nom,Numéro demandé,Date,Heure,Durée,Canal,Taxes,Tarif,Coût,Etiquette
# Classements
par_provider = par_poste = {} 
def resultat( conn, acctid, ut, cout, verbose=False ):
   if verbose:
      sys.stderr.write( '%d, %d, %d\n' % (acctid, ut, cout) )

   curs2 = conn.cursor()
   curs2.execute('''
UPDATE cdr 
SET ut=%d, ht=%d, ttc=%d
WHERE acctid = %d
''' % (ut, cout, 1.1 * cout, acctid))
   conn.commit()


# MAIN ------------------------------------------------------------------------

# Command line options
( verbose, usd2cfp ) = options( sys.argv[1:] )
teliax_rates = teliax('teliax-rates.csv')
opt_rates = opt('inter.csv') # 'opt_rates.txt')

# Durée de l'impulsion pour chaque groupe
groupe2ut = { 'A': 30.0, 'B1': 20.0, 'B2': 20.0, 'C': 15.0, 'D': 4.5, 'E': 3.75 }
ut2cfp = 3106

# Définition des expressions régulières sur numéro demandé
re_ile = '(' + '|'.join(iles) + ')\d'
re_ile = re.compile( '(' + re_ile + '|88[^9])\d\d\d' )   # Iles
re_gsm = re.compile('[72]\d\d\d\d\d')                     # GSM Vini
re_tah = re.compile('[1345689]\d\d\d\d\d')                  # Tahiti
re_int = re.compile('00\d*')                              # International OPT
re_19  = re.compile('19$')                              # OPT 19
re_13  = re.compile('13$')                              # OPT 13
re_321 = re.compile('321$')                           # OPT
re_3612 = re.compile('3612$')                           # Renseignements
re_3640 = re.compile('3640$')                           # Mana
re_3660 = re.compile('3660$')                           # 
re_audiotel = re.compile('36(65|70)\d\d$')            # Audiotel
re_sviint = re.compile('99001$')                        # SVI international
re_provider = re.compile('00\d+')                     # Provider

# Canaux de sortie
re_zap = re.compile('(Zap|DAHDI)/')         # T2 OPT
re_sipgsm = re.compile('SIP/gsm')      # Passerelle GSM
re_iax = re.compile('IAX2/(\w+)-\d+')   # International IP

# Compteurs divers
ut_total = vini_total = iax_total = optimum_total = erreurs = lignes = sortants = 0
mois = -1
optimum_forfait = 1500000 # Forfait Optimum 25 16500 F TTC / mois
# Cout HT / seconde
optimum_tah_forfait = 100.0*11/60/1.1
optimum_gsm_forfait = 100.0*18/60/1.1
optimum_ile_forfait = 100.0*14/60/1.1
optimum_tah_depasse = 100.0*14/60/1.1
optimum_gsm_depasse = 100.0*23/60/1.1
optimum_ile_depasse = 100.0*18/60/1.1

h0 = datetime.time(0,0,0)
h6 = datetime.time(6,0,0)
h18 = datetime.time(18,0,0)
h22 = datetime.time(22,0,0)

if verbose:
   sys.stderr.write( 'Cours utilisé: %f F.CFP / US$\n' % usd2cfp)
   sys.stderr.write('Traitement en cours...\n')

# Open database connection
import psycopg2
conn = psycopg2.connect('dbname=druid user=druid password=OqEibl4gbM')
curs = conn.cursor()

# Look for outgoing calls, where ht not computed
curs.execute( '''
SELECT acctid, dst, billsec, dstchannel, disposition, calldate
FROM cdr 
WHERE lastdata ILIKE 'Dahdi/g0/%' AND billsec>0 AND ht isnull''' )

# Loop over CDR data
for acctid, dst, billsec, dstchannel, disposition, calldate in curs.fetchall():
   if verbose:
      sys.stderr.write('%d, %s, %d, %s, %s, %s' % 
            (acctid, dst, billsec, dstchannel, disposition, calldate) )
   dat = calldate.date()
   if dat.month != mois:
      # RAZ total Optimum
      optimum_total = 0
   heure = calldate.time()

   if re_provider.match(dst) and not re_zap.match(dstchannel): # Appel international via provider
      dst = dst[2:]
      ut = 0; cout = rate = 0.0
      match = re_iax.match(dstchannel)
      if match or disposition == 'ANSWERED':

         try:
            provider = match.group(1)

            if provider == 'teliax':
               if billsec == 0:
                  # Les communications à durée nulle n'apparaissent pas dans la
                  # facture Teliax, on les ignore
                  continue;

               # Première minute indivisible, puis incréments de six seconde
               # ut correspond au nombre de periodes de six secondes
               # rate est par minute, d'ou la division par 10
               if billsec <= 60:
                  ut = 10
               else:
                  ut = int(math.ceil(billsec/6))
               for k in reversed(sorted(teliax_rates.keys())):
                  if teliax_rates[k][1].match(dst):
                     # XXX ind = k
                     rate = teliax_rates[k][0]
                     cout = (rate * ut / 10) * usd2cfp
                     break
            # /TelIAX

            elif provider == 'nufone':
               # On ne dispose pas du tableau des tarifs
               # on interroge le site...
               ut = billsec
               url = 'http://www.nufone.net/solutions/international-rates/?number=' + dst + '&submit=Lookup+Rate'
               try:
                  page = urllib.urlopen(url)
                  # On cherche la ligne <td>$0.3390 USD</td>
                  r = re.compile('<td>\$([\d\.]+) USD</td>')
                  for l in page:
                     m = r.search(l)
                     if m:
                        rate, = m.groups(1)
                        rate = float(rate)
                        # 2 décimales, arrondi supérieur
                        cout = math.ceil((rate*billsec/60)*100)/100
                        cout *= usd2cfp
                        break
               except e:
                  sys.stderr.write('ERREUR: accès site NuFone impossible ' + e + '\n')
                  sys.exit(1)
            # /NuFone
 
            else:
               sys.stderr.write('ERREUR: provider inconnu ' + provider + '\n')
               sys.exit(1)

         except:
            sys.stderr.write('ERREUR: pas de provider !\n')
            provider = 'inconnu'
#            sys.exit(1)

         resultat( conn, acctid, ut, cout, verbose )
   # /provider

   elif re_sipgsm.match(dstchannel):
      # Appel sortant par canal SIP GSM (passerelle VoiceBlue)
      # Facturation Tikiphone forfait 4 heures
      # 20 F.HT / min, première minute indivisible puis décompte à la seconde
      if billsec <= 60: cout = 20
      else: cout = int(math.ceil(20.0 * billsec / 60))
      resultat( conn, acctid, ut, cout, verbose )

   elif re_zap.match(dstchannel):
      # Appel sortant par canal Zap (T2 OPT)

      if re_gsm.match(dst):
         if optimum_forfait:
            # Optimum: première minute indivisible, puis décompte à la seconde
            if billsec<60: billsec=60
            if optimum_total > optimum_forfait:
               cout = int(math.ceil(billsecr*optimum_gsm_depasse))
            else:
               cout = int(math.ceil(billsec*optimum_gsm_forfait))
            optimum_total += cout
            resultat( conn, acctid, -1, cout, verbose )

         else:
            # Appel vers GSM: impulsion 34 sec (réduit 60 sec, de 18h00 à 6h00 et week-end)
            if dat.weekday()<5 and datetime.time(6,0,0) <= heure < datetime.time(18,0,0):
               ut = int(math.ceil(billsec/34.0))
            else:
               ut = int(math.ceil(billsec/60.0))
            resultat( conn, acctid, ut, ut2cfp*ut, verbose )

      elif re_ile.match(dst):
         if optimum_forfait:
            # Optimum: première minute indivisible, puis décompte à la seconde
            if billsec<60: billsec=60
            if optimum_total > optimum_forfait:
               cout = int(math.ceil(billsec*optimum_ile_depasse))
            else:
               cout = int(math.ceil(billsec*optimum_ile_forfait))
            optimum_total += cout
            resultat( conn, acctid, -1, cout, verbose )

         else:
            # Appel vers île: implusion 2 min 30 sec (réduit 5 min, de 22h00 à 6h00)
            if h6 <= heure < h22:
               ut = int(math.ceil(billsec/150.0))
            else:
               ut = int(math.ceil(billsec/300.0))
            resultat( conn, acctid, ut, ut2cfp*ut, verbose )

      elif re_tah.match(dst):
         if optimum_forfait:
            # Optimum: première minute indivisible, puis décompte à la seconde
            if billsec<60: billsec=60
            if optimum_total > optimum_forfait:
               cout = int(math.ceil(billsec*optimum_tah_depasse))
            else:
               cout = int(math.ceil(billsec*optimum_tah_forfait))
            optimum_total += cout
            resultat( conn, acctid, -1, cout, verbose )

         else:
            # Appel vers Tahiti: implusion 4 min (réduit 8 min, de 22h00 à 6h00)
            if h6 <= heure < h22:
               ut = int(math.ceil(billsec/240.0))
            else:
               ut = int(math.ceil(billsec/480.0))
            resultat( conn, acctid, ut, ut2cfp*ut, verbose )

      elif dst[:2] == '00':
         # Appel vers international via OPT
         d = dst[2:]
         for k in reversed(sorted(opt_rates.keys())):
            if opt_rates[k][1].match(d):
               if optimum_forfait:
                  # Optimum: première minute indivisible, puis décompte à la seconde
                  ttc3 = int(opt_rates[k][10])
                  ttc4 = int(opt_rates[k][11])
                  if billsec<60: billsec=60
                  if optimum_total > optimum_forfait:
                     cout = int(math.ceil(billsec*ttc3/60.0/1.1))
                  else:
                     cout = int(math.ceil(billsec*ttc4/60.0/1.1))
                  optimum_total += cout
                  resultat( conn, acctid, -1, cout, verbose )
                  break

               else:
                  # XXX ind = k
                  g = opt_rates[k][0]
                  if g == 'B': 
                     if h0 <= heure < h6: g = 'B2'
                     else: g = 'B1'
                  ut = int(math.ceil(billsec / groupe2ut[g]))
                  resultat( conn, acctid, ut, ut2cfp*ut, verbose )
                  break
         else:
            if disposition == 'ANSWERED':
               # Pas reconnu, mais répondu !
               resultat( conn, acctid, 0, 0, verbose )

      elif re_321.match(dst) or re_3612.match(dst) or \
            re_13.match(dst) or re_19.match(dst) or \
            re_3640.match(dst) or re_3660.match(dst) or \
               re_audiotel.match(dst):
         # Numéros spéciaux XXX
         resultat( conn, acctid, 0, 0, verbose )

      elif re_sviint.match(dst):
         # SVI
         resultat( conn, acctid, 0, 0, verbose )

   # Les appels non reconnus sont traités ici
   elif disposition == 'ANSWERED':
      # Pas reconnu, mais répondu !
      resultat( conn, acctid, 0, 0, verbose )
   else:
      # En erreur
      resultat( conn, acctid, 0, 0, verbose )

