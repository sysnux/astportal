#! /opt/Python-2.5.5/bin/python
# -*- coding: utf-8 -*-

# Script d'importation de l'annuaire au format CSV:
# "Nom";"Prenom";"Fonction";"Téléphone","Fax","Service"

import os, csv, sys, re
from argparse import ArgumentParser
from paste.deploy import appconfig
from astportal2.config.environment import load_environment
from astportal2.model import DBSession, User, Department, Phone
from sqlalchemy.orm.exc import NoResultFound
import transaction

def load_config(filename):
   conf = appconfig('config:' + os.path.abspath(filename))
   load_environment(conf.global_conf, conf.local_conf)

def parse_args():
   parser = ArgumentParser(description=__doc__)
   parser.add_argument("conf_file", help="configuration to use")
   parser.add_argument("csv_file", help="csv file to use")
   return parser.parse_args()

def utf_8_encoder(x):
   for line in x:
      yield line.encode('utf-8')

def create_phones(base):
   for i in range(0,100):
      p = Phone()
      p.number = '%s%02d' % (base, i)
      p.department_id = -1
      DBSession.add(p)
   DBSession.flush()
   transaction.commit()


def main():
   args = parse_args()
   load_config(args.conf_file)

   if len(DBSession.query(Phone).all())==0:
      create_phones('4643')
      create_phones('4752')

   data = csv.reader(open(args.csv_file,'rb'), delimiter=',')

   try:
      dptm = ''
      for row in data:
   

         uname = unicode(re.sub('\W', '', (row[1][0:2] + row[0]).lower()), 'utf-8')
         dname = unicode(row[0] + ' ' + row[1], 'utf-8')
         num = unicode(row[3].replace(' ',''), 'utf-8')
         fax = unicode(row[4].replace(' ',''), 'utf-8')
         dptm = unicode(row[5], 'utf-8')
         #print ' * * * ', uname, dname, num, dptm

         try:
            p = DBSession.query(Phone).filter(Phone.number==num).one()
         except NoResultFound, e:
            # Nouveau tél ???
            p = Phone()
            p.number = num
            p.department_id = -1
            DBSession.add(p)

         try:
            d = DBSession.query(Department).filter(Department.name==dptm).one()
         except NoResultFound, e:
            # Nouveau département
            d = Department()
            d.name = dptm
            DBSession.add(d)

         u = User()
         u.user_name = uname
         u.display_name = dname
         u.phone = [p]
         u.password = u'n5oBwdpytxdvj~Rz1uum'
         p.department = d
         DBSession.add(u)
         DBSession.add(p)

   except csv.Error, e:
      sys.exit('! ! ! ERREUR ligne %d: %s\n' % (data.line_num, e))

   DBSession.flush()
   transaction.commit()
   sys.stderr.write('- - - Fin normale\n')

if __name__ == '__main__':
   sys.exit(main())
