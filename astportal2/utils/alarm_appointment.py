#! /opt/Python-2.7.3/bin/python
# -*- coding: utf-8 -*-
#
# Send alarm for call center appointments
#
# Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/

import sys
import locale
import re
from datetime import datetime, timedelta

import urllib, urllib2 # SMS

from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

re_smsid = re.compile(r'MsgId=(\d+)')
re_nbsms = re.compile(r'NbSMS=(\d+)')
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

# Open database connection
sys.path.append('/opt/astportal21')
from paste.deploy import appconfig
conf = appconfig('config:/opt/astportal21/sgbdp.ini')

from astportal2.config.environment import load_environment
load_environment(conf.global_conf, conf.local_conf)
from astportal2.model import DBSession, Outcall



def check_none(x):
   return x if x!='NONE' else None


def email(dest, begin):
   ''' Create and send email
   '''

   sender = 'infos@sg-bdp.pf' # XXX

   # Create email 
   msg = MIMEMultipart('alternative')
   msg['Subject'] = u'Rappel rendez-vous Banque de Polynésie'
   msg['From'] = sender
   msg['To'] = dest
#   msg['Cc'] = cc
   msg.preamble = 'Please use a MIME-aware mail reader to read this email.\n'

   # Text part
   text = u'''\
Bonjour,

Nous vous rapelons votre rendez-vous à la Banque de Polynésie :
%s

Merci et bonne réception
''' % (begin.strftime("%A %d %B, %Hh%Mm%Ss").encode('utf-8'))

   part = MIMEText(text, _subtype='plain', _charset='utf-8')
   msg.attach(part)

   # HTML part
   text = u'''\
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset="UTF-8">
<style>
.shadow {
   margin: 10px 40px;
   padding: 5px;
   border: 1px solid #aaa;
	-moz-box-shadow: 3px 3px 4px #000;
	-webkit-box-shadow: 3px 3px 4px #000;
	box-shadow: 3px 3px 4px #000;
   -moz-border-radius: 10px;
   -webkit-border-radius: 10px;
   border-radius: 10px; /* future proofing */
   -khtml-border-radius: 10px;
	/* For IE 8 */
	-ms-filter: "progid:DXImageTransform.Microsoft.Shadow(Strength=4, Direction=135, Color='#000000')";
	/* For IE 5.5 - 7 */
	filter: progid:DXImageTransform.Microsoft.Shadow(Strength=4, Direction=135, Color='#000000');
}
</style>
</head><body>
<p>Bonjour,</p>

Nous vous rappelons votre rendez-vous à la Banque de Polynésie&nbsp;:
<em>%s</pre>

<p>Merci et bonne réception</p>
</body></html>
''' % (begin.strftime("%A %d %B, %Hh%Mm%Ss").encode('utf-8'))
   part = MIMEText(text, _subtype='html', _charset='utf-8')
   msg.attach(part)

   # Send email
   s = smtplib.SMTP()
   try:
      s.connect('localhost')
      s.sendmail(sender, dest, msg.as_string())
      s.close()
      return 100, u'Email envoyé'
   except:
      return 101, u'%s' % sys.exc_info()[0]


def sms(dest, begin):
   '''Envoi SMS via plateforme de Tikiphone

Page retournée par Tikiphone :
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
    <title>
        
        HTTP Connect 2.0
    </title>
    <link rel="stylesheet" href="/skins/default/default-skin-css.jsp;jsessionid=a11RTg_AeRie" type="text/css">
    <link rel="stylesheet" href="/skins/default/default-body-css.jsp;jsessionid=a11RTg_AeRie" type="text/css">
    <link rel="SHORTCUT ICON" href="/skins/default/images/shortcut.ico;jsessionid=a11RTg_AeRie">
    
</head>



<body >
<div class="skinBody">
    Status=0<br>
MsgId=45702301<br>
NbSMS=1<br>
Message successfully sent.<br>
</div>
</body>
</html>
'''

   msg = u'''Rappel rendez-vous 
Banque de Polynésie 
%s
''' % (begin.strftime("%A %d %B, %Hh%Mm%Ss").encode('utf-8'))

   url = 'https://partenaires.vini.pf:9510/sender/httpconnect.jsp'
   proxy = {'https': 'http://10.10.3.10:8080'}

   opener = urllib2.build_opener(urllib2.ProxyHandler(proxy))
   urllib2.install_opener(opener)
   params = {
      'UserName': 'bankdepo',
      'Password': 'FI5kY)',
      'DA': '689' + dest,
      'SOA': '466666',
      'Content': msg.encode('utf-8'),
      'Flags': 1
      }
   try:
      rsp = urllib2.urlopen( url, urllib.urlencode(params))
   except urllib2.HTTPError, e:
      return 201, u'Erreur HTTP : %s' % e.code
   except urllib2.URLError, e:
      return 202, u'Erreur connexion : %s' % e.args

   if rsp.code!=200:
      return 203, u'Erreur requête, code %d' % rsp.code

   smsid = nb = status = None
   for l in rsp.readlines():

      if smsid is None: # Recherche ligne MsgId
         m = re_smsid.match(l)
         if m:
            smsid = m.group(1)
         else:
            continue

      elif nb is None: # Recherche ligne NbSMS
         m = re_nbsms.match(l)
         if m:
            nb = m.group(1)

      else: # MsgId et NbSMS trouvés, la ligne suivante contient l'état
         status = l[:-5]
         break

   return 200, u'Requête OK (%s), réponse : id=%s, nb=%s, status=%s' % (
      rsp.code, smsid, nb, status)


class __main__:

   now = datetime.now()
   now = datetime(now.year, now.month, now.day) # Today 0:00:00

   # Search alarm for today
   for o in DBSession.query(Outcall). \
      filter(Outcall.alarm_sent==None). \
      filter(Outcall.alarm_type>0). \
      filter(Outcall.begin>=now). \
      filter(Outcall.begin<now+timedelta(1)):
      
#      print u'Rappel type %d, pour %s (%s)' % (o.alarm_type, o.alarm_dest, o.begin)

      if o.alarm_type==1: # email
         ret, msg = email(o.alarm_dest, o.begin)

      elif o.alarm_type==2: # SMS
         ret, msg = sms(o.alarm_dest, o.begin)

      else:
         ret , msg = -1, u'Unknown alarm type (%d)' % o.alarm_type

      o.alarm_sent = datetime.now()
      o.alarm_result_code = ret
      o.alarm_result_msg = msg

# Normal end
import transaction
transaction.commit()
