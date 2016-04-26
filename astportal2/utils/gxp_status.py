#! /usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from sys import argv, exit
from time import time, sleep
from datetime import datetime

def login(cgi, secret):
    r = session.post(cgi + 'dologin',
                     data = {'username': 'admin',
                             'password': secret},
                     verify = False)
    ret = r.json()

    if ret['response'] != 'success':
        print 'Erreur login : ', ret
        exit(2)
    return ret['body']['sid']


if len(argv) != 3:
    print 'Usage: %s adresse_poste mot_de_passe' % argv[0]
    exit(1)

# L'objet session permet d'utiliser les connexions persistantes
session = requests.session()
cgi = 'https://%s/cgi-bin/' % argv[1]
sid = login(cgi, argv[2])

duree_max = duree_moy = compteur = 0.0
while True:
    debut = time()
    r = session.post(cgi + 'api-get_phone_status',
                     data = {'sid': sid},
                     verify = False)
    ret = r.json()
    duree = time() - debut
    if duree > duree_max:
        duree_max = duree
    duree_moy += duree
    compteur += 1
    print u'%s "%s", duree %.3f s, max = %.3f s, moy = %.3f s (%d).' % \
        (datetime.now().strftime('%H:%M:%S.%f'), ret['body'], 
        duree, duree_max, duree_moy / compteur, compteur)

    if ret['body'] == 'unauthorized':
        sid = login(cgi, argv[2])

    if duree < 1:
        sleep(1-duree)

