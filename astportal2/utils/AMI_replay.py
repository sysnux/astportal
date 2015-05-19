#! /bin/env python
# -*- coding: utf-8 -*-
#
# AMI server replays capture events from file (format JSON)
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/

from time import sleep
import socket
from sys import argv, exit, stderr
printerr = stderr.write
import json


if len(argv)<2:
   printerr('Usage: AMI_replay nom_fihier [coeff]\n')
   exit(1)

nom_fich = argv[1]
try:
   if nom_fich.endswith('xz'):
      import lzma
      fich = lzma.LZMAFile(nom_fich)
   else:
      fich = open(nom_fich)
except:
   printerr('ERREUR fichier\n')
   exit(2)

coeff = 1.0
if len(argv)==3:
   try:
      coeff = float(argv[2])
      printerr('Coefficient temporel = %f.\n' % coeff)
   except:
      printerr('Erreur coefficient : "%s" pas un nombre flottant ?\n' % argv[2])

compte = 0
s = ''
for l in fich:
   s += l[:-1]
fich.close()

data = json.loads(s[:-2] + ']')
del(s)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('localhost', 5039))
sock.listen(1)
printerr('Attente connexion\n')

conn, client = sock.accept()
printerr('Connexion depuis %s\n' % (client,))

conn.sendall('Asterisk Call Manager/1.3\r\n')
sleep(1)
login = conn.recv(1024)
for l in login.split('\n'):
   if l.startswith('ActionID:'):
      break
conn.sendall('Response: Success\r\nMessage: Authentication accepted\r\n' + l + '\r\n\r\n')
last = 0.0
try:
   for e in data:
      sleep((e[0]-last) * coeff)
      printerr('Envoi evenement %s: %s\n' % (e[0], e[1]['Event']))
      last = e[0]
      for k, v in e[1].iteritems():
         conn.sendall('%s: %s\r\n' % (k, v))
      conn.sendall('\r\n')

except:
   pass

printerr('\nFin normale\n')
conn.close()


