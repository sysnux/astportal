#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# Script d'importation de l'annuaire fourni par la Présidence

import csv, sys

from astportal2.model import DBSession, User, Department, Phone

data = csv.reader(open('utils/annuaire.csv','rb'), delimiter=';', quoting=csv.QUOTE_NONE)
dptm_data = csv.writer(open('utils/dptm.csv','wb'), delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
dptm_id = 0
users_data = csv.writer(open('utils/users.csv','wb'), delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
users_id = 0
phones_data = csv.writer(open('utils/phones.csv','wb'), delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
phones_id = 0


try:
   dptm = ''
   for row in data:
      if len(row)>=4:
         if row[0].startswith('::'):
            dptm = row[0][2:]
            dptm_data.writerow((dptm_id, dptm,dptm.title()))
            dptm_id += 1
         if row[3] and len(row[3])==4:
            print '%s, %s, %s, %s, %s.%s@presidence.pf' % (dptm, row[1], row[2], row[3], row[2].replace(' ','').lower(), row[1].replace(' ','').lower())
            users_data.writerow((
            users_id,
            row[2].replace(' ','').lower() + '.' + row[1].replace(' ','').lower(), 
            row[2].replace(' ','').lower() + '.' + row[1].replace(' ','').lower() + '@presidence.pf' ,
            row[1] + ' ' + row[2],
            None,
            None
            ))
            phones_data.writerow((phones_id, row[3], dptm_id, users_id, None))
            users_id += 1
            phones_id += 1
         else:
            sys.stderr.write( '* * * ' + dptm + str(row) + '\n')
      else:
         sys.stderr.write( '+ + + ' + dptm + str(row) + '\n')

except csv.Error, e:
   sys.exit('! ! ! ERREUR ligne %d: %s\n' % (data.line_num, e))

sys.stderr.write('- - - Fin normale\n')

