#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Script de réception des télécopies

# Appelé par /var/spool/hylafax/etc/FaxDispatch :
'''
log=log/faxdispatch.log
echo "NEW FaxDispatch $(date)" >> $log
echo "Running as $(id), from $(pwd)" >> $log

FROMADDR=fax@asterisk.lolita.pf
NOTIFY_FAXMASTER=never # errors
FILETYPE=pdf
LANG=fr

echo "CID1=$CALLID1, CID2=$CALLID2, CID3=$CALLID3, CID4=$CALLID4, CID5=$CALLID5, CID6=$CALLID6," >> $log
echo "TIFF2PDF=$TIFF2PDF, FILE=$FILE" >> $log

pdf=$(basename $FILE .tif).pdf
$TIFF2PDF -o astportal/$pdf $FILE >> $log 2>&1
chmod 666 astportal/$pdf
ls -l astportal/$pdf >> $log 2>&1

echo "Appel script Python" >> $log 2>&1
eval $(python astportal/faxdispatch.py $CALLID4 $CALLID1 $pdf)
if [ "x$SENDTO" = 'x' ]; then 
echo SENDTO=FaxMaster@lolita.pf;
fi
echo "SENDTO=$SENDTO" >> $log

echo "END FaxDispatch $(date)" >> $log
echo "" >> $log
'''
# Fin FaxDispatch

# Import nécessaires pour utiliser le modèle
import transaction
import os, sys
import ConfigParser
from sqlalchemy import create_engine

sys.path.append('/home/SysNux/Projets/astportal21')
os.environ['PYTHON_EGG_CACHE'] = '/home/SysNux/Projets/astportal21'
from astportal2.model import init_model, DBSession, Phone

config = ConfigParser.ConfigParser({'here': os.getcwd()})
config.read(os.path.join(os.getcwd(), '/home/SysNux/Projets/astportal21/x220.ini'))
sqlalchemy_url = config.get('app:main', 'sqlalchemy.url')
engine = create_engine(sqlalchemy_url)
init_model(engine)

log = open('/tmp/faxdispatch.log', 'a')
log.write('\n' + '-' * 40 + '\n')
for k in os.environ.keys(): 
   log.write('%s => %s\n' % (k, os.environ[k]))
log.write('\n')

#try:
#   p = DBSession.query(Phone).filter(Phone.exten==mailbox).one()
#except:
#   sys.stderr.write('Error: extension <%s> not found\n' % mailbox)
#   sys.exit(1)
#
#p.user.password = passwd
#DBSession.flush()
#transaction.commit() 

