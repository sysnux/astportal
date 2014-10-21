#! /opt/tg22env/bin/python
# -*- coding: utf-8 -*-

# Script de changement des mots de passe

# Import nécessaires pour utiliser le modèle
import transaction
import os, sys
import ConfigParser
from sqlalchemy import create_engine

sys.path.append('/opt/astportal21')
os.environ['PYTHON_EGG_CACHE'] = '/opt/astportal21'
from astportal2.model import init_model, DBSession, Phone

config = ConfigParser.ConfigParser({'here': os.getcwd()})
config.read(os.path.join(os.getcwd(), '/opt/astportal21/socredo.ini'))
sqlalchemy_url = config.get('app:main', 'sqlalchemy.url')
engine = create_engine(sqlalchemy_url)
init_model(engine)


try:
   context = sys.argv[1]
   mailbox = sys.argv[2]
   passwd = sys.argv[3]
except:
   sys.stderr.write('Error: missing arguments\n')
   sys.exit(1)

try:
   p = DBSession.query(Phone).filter(Phone.exten==mailbox).one()
except:
   sys.stderr.write('Error: extension <%s> not found\n' % mailbox)
   sys.exit(1)

p.user.password = passwd
DBSession.flush()
transaction.commit() 
