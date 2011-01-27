#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Script de création des postes dans les plages SDA

# Import nécessaires pour utiliser le modèle
import transaction
import os
import ConfigParser
from sqlalchemy import create_engine

#from astportal2.model import *
from astportal2.model import init_model, DBSession, Phone

config = ConfigParser.ConfigParser({'here': os.getcwd()})
config.read(os.path.join(os.getcwd(), 'development.ini'))
sqlalchemy_url = config.get('app:main', 'sqlalchemy.url')
engine = create_engine(sqlalchemy_url)
init_model(engine)

import csv, sys


numbers = [p.number for p in DBSession.query(Phone.number).all()]

#for i in range(0,400):
#for i in range(500,700):
for i in range(800,900):
    n = '2%03d' % i
    if n not in numbers:
       p = Phone()
       p.number = n
       p.department_id = 28
       try:
          DBSession.add(p)
          DBSession.flush()
       except:
          sys.exit('ERREUR sur poste ' + n)
       print n, 'OK !'
transaction.commit() 
