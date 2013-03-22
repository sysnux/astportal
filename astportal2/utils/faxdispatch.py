#! /opt/tg22env/bin/python
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
eval $(astportal/faxdispatch.py)
if [ "x$SENDTO" = 'x' ]; then 
   SENDTO=FaxMaster@sysnux.pf
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

# Connexion base de données AstPortal via SqlAlchemy
sys.path.append('/opt/astportal21')
from paste.deploy import appconfig
conf = appconfig('config:/opt/astportal21/upf.ini')

from astportal2.config.environment import load_environment
load_environment(conf.global_conf, conf.local_conf)
from astportal2.model import DBSession, Phone, Fax

log = open('/var/spool/hylafax/log/faxdispatch.log', 'a')
log.write('\n' + '>' * 40 + '\n')
for k in os.environ.keys(): 
   log.write('%s => %s\n' % (k, os.environ[k]))
log.write('\n')

dst = os.environ.get('CALLID4')
src = os.environ.get('CALLID1')
hyla_id = os.environ.get('COMMID')
try:
   pdf = sys.argv[1]
except:
   pdf = ''

log.write('src=%s -> dst=%s, hyla_id=%s, pdf=%s\n' % (src, dst, hyla_id, pdf))

try:
   p = DBSession.query(Phone).filter(Phone.exten==dst).one()
except:
   log.write('Error: extension <%s> not found\n' % dst)
   p = None
log.write('%s\n' % (p))

if p is not None and p.user is not None:
   email = p.user.email_address
   uid = p.user.user_id
else:
   email = uid = None
log.write('uid=%s, email=%s\n' % (uid, email))

f = Fax()
f.type = 1 #  => received fax
f.hyla_id = hyla_id
f.user_id = uid
f.src = src
f.dest = dst
f.filename = pdf
DBSession.add(f)

DBSession.flush()
transaction.commit() 
log.write('New fax added to database\n')

if email is not None:
   log.write('SENDTO=%s\n' % email)
   print 'SENDTO=%s' % email

log.write('\n' + '<' * 40 + '\n')

