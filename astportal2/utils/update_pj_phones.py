#! /opt/venv-astportal/bin/python
# -*- coding: utf-8 -*-

from os import popen
from sys import path, exit, argv
from getopt import getopt
import re
import logging
logging.basicConfig()

path.insert(0, '/home/SysNux/Projets/astportal3')

from paste.deploy import appconfig
from astportal2.config.environment import load_environment
conf = appconfig('config:/opt/astportal/astportal.ini')
load_environment(conf.global_conf, conf.local_conf) # Needed for DBSession

from tg import config
from astportal2.lib.grandstream import Grandstream
from astportal2.model import DBSession, Phone

server_sip = config.get('server.sip')
server_firmware = config.get('server.firmware')
server_config = config.get('server.config')
server_syslog = config.get('server.syslog')
server_ntp = config.get('server.ntp')
command_fping = config.get('command.fping')
command_arp = config.get('command.arp')
directory_tftp = config.get('directory.tftp')
directory_asterisk = config.get('directory.asterisk')

#tiare*CLI> pjsip show contacts
#
#  Contact:  <Aor/ContactUri..............................> <Hash....> <Status> <RTT(ms)..>
# ========================================================================================= 
#
#  Contact:  2ntI5KYU/sip:2ntI5KYU@192.168.10.100;line=2629 bcb60640f1 Avail         6.022
re_pjsip = re.compile('(\w+)/sip:(\w+)@(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')

def usage():
   print '''
Script de mise à jour des téléphones
Usage: %s [options]
Options:
\t-f             force la mise à jour sans confirmation
\t-p adresse_ip  met à jour uniquement ce téléphone (peut être répété)
\t-e numéro      met à jour uniquement ce téléphone (peut être répété)
\t-h             aide (cet écran!)
''' % argv[0]
   exit(1)


def options( argv ):
   try: ( opts, params ) = getopt( argv, 'hfp:e:' )
   except: usage()
   f = False # Force
   p = [] # Phones'ip address
   e = [] # Phones'ip address
   for o in opts:
      if o[0] == '-h': usage()
      if o[0] == '-f': f = True
      if o[0] == '-p': p.append(o[1])
      if o[0] == '-e': e.append(o[1])
   return f, p, e


# Main
force, phones, extens = options( argv[1:] )

for l in popen("asterisk -rx 'pjsip show contacts'"):

   m = re_pjsip.search(l)
   if m:
      name, sip_id, ip = m.groups()

      if phones != [] and ip not in phones:
         continue

      try:
         p = DBSession.query(Phone).filter(Phone.sip_id==sip_id).one()
      except:
         print u'\tERREUR téléphone "%s" inexistant !\n' % sip_id

      if extens != [] and p.exten not in extens:
         continue

      print u'Téléphone %d: %s / %s (%s @%s)' % \
            (p.phone_id, sip_id, p.password, p.exten, ip)
      gs = Grandstream(ip, p.mac)

      if not gs.login(p.password):
         print u'\tERREUR login\n'
         continue

      infos = gs.infos()
      if not infos['model'].startswith('GXP'):
         print u'\tTrouvé téléphone inconnu (%s), abandon' % (infos),
         continue

      print u'\tTrouvé téléphone %s (%s)' % (infos['model'], infos['version']),

      if not force:
         x = None
         while (x not in ('o', 'n')):
            x = raw_input(u'le configurer (O/N) ? ').lower()
         if x == 'n':
            print
            continue

      else:
         print

      sip_display_name = ''
      mwi_subscribe = 0
      if p.user:
         print u'Utilisateur:', p.user.ascii_name, p.user.email_address
         sip_display_name = p.user.ascii_name
         if p.user.email_address:
            mwi_subscribe = 1

      print u'\tconfiguration en cours... ',
#      gs.configure( p.password, directory_tftp, \
#         server_firmware + '/phones/firmware', \
#         server_config + '/phones/config', server_syslog, \
#         server_config + ':8080/phonebook/gs_phonebook_xml', '', '', '', \
#         server_sip, sip_id, '', 1, exten=p.exten)
      gs.configure( p.password, directory_tftp,
            server_firmware + '/phones/firmware', 
            server_config + '/phones/config', server_ntp,
            server_config, '', '', '',
            server_sip, sip_id, sip_display_name, mwi_subscribe,
            screen_url = server_config, exten=p.exten,
            sip_server2='')
      print u'ok\n'


#   else:
#      print u'ko :', l[:40], '...'

print u'Fin normale !'

