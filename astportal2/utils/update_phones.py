#! /opt/tg22env/bin/python
# -*- coding: utf-8 -*-

from os import popen
from sys import path, exit, argv
from getopt import getopt
import re

path.insert(0, '/opt/astportal21')

from paste.deploy import appconfig
from astportal2.config.environment import load_environment
conf = appconfig('config:/opt/astportal21/socredo.ini')
load_environment(conf.global_conf, conf.local_conf) # Needed for DBSession

from tg import config
from astportal2.lib.grandstream import Grandstream
from astportal2.model import DBSession, Phone

server_sip = config.get('server.sip')
server_sip2 = config.get('server.sip2')
server_firmware = config.get('server.firmware')
server_config = config.get('server.config')
server_syslog = config.get('server.syslog')
server_ntp = config.get('server.ntp')
command_fping = config.get('command.fping')
command_arp = config.get('command.arp')
directory_tftp = config.get('directory.tftp')
directory_asterisk = config.get('directory.asterisk')

re_sip = re.compile('(\w+)/(\w+)\s+((\d{1,3}\.){3}\d{1,3})')

def usage():
   print '''
Script de mise à jour des téléphones
Usage: %s [options]
Options:
\t-f             force la mise à jour sans confirmation
\t-p adresse_ip  met à jour uniquement ce téléphone (peut être répété)
\t-h             aide (cet écran!)
''' % argv[0]
   exit(1)


def options( argv ):
   try: ( opts, params ) = getopt( argv, 'hfp:' )
   except: usage()
   f = False # Force
   p = [] # Phones'ip address
   for o in opts:
      if o[0] == '-h': usage()
      if o[0] == '-f': f = True
      if o[0] == '-p': p.append(o[1])
   return f, p


# Main
force, phones = options( argv[1:] )
print phones

for l in popen("asterisk -rx 'sip show peers'"):
   m = re_sip.match(l)
   if m:
      name, sip_id, ip, x = m.groups()
      if phones != [] and ip not in phones:
         continue

      p = DBSession.query(Phone).filter(Phone.sip_id==sip_id).one()
      print u'Téléphone %d: %s / %s (%s)' % (p.phone_id, sip_id, p.password, ip)
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

      print u'\tconfiguration en cours... ',
#      gs.configure( p.password, directory_tftp, \
#         server_firmware + '/phones/firmware', \
#         server_config + '/phones/config', server_syslog, \
#         server_config + ':8080/phonebook/gs_phonebook_xml', '', '', '', \
#         server_sip, sip_id, '', 1)
#      gs.configure(p.password, directory_tftp, \
#         phonebook_url=None, syslog_server=None, dns1=None, dns2=None,
#         sip_server=None, sip_user=None, sip_display_name=None,
#         mwi_subscribe=False, reboot=True, screen_url=None, exten=None,
#         sip_server2=None):
      gs.configure( p.passwd, directory_tftp,
            server_firmware + '/phones/firmware', 
            server_config + '/phones/config', server_ntp,
            server_config, '', '', '',
            sip_server, sip_id, sip_display_name, mwi_subscribe,
            screen_url = server_config, exten=p.exten,
            sip_server2=server_sip2)
      print u'ok\n'

#   else:
#      print u'ko :', l[:40], '...'

print u'Fin normale !'

