#! /opt/Python-2.7.3/bin/python
#  -*- coding: utf-8 -*-
#
# Envoi SMS via plateforme de Tikiphone
#
# Auteur : Jean-Denis Girard <jd.girard@sysnux.pf>
# SysNux (c) http://www.sysnux.pf/
#
# Page retournée par Tikiphone :
'''
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

import urllib, urllib2
import re
import sys

url = 'https://partenaires.vini.pf:9510/sender/httpconnect.jsp'
proxy = {'http': 'http://10.10.3.10:8080',
   'https': 'http://10.10.3.10:8080'}
msg = u'''Test rappel rendez-vous
é ê è ï î ô ö ù à ç € $ £ ù'''
to = '797527'

opener = urllib2.build_opener(urllib2.ProxyHandler(proxy))
urllib2.install_opener(opener)
params = {
   'UserName': 'bankdepo',
   'Password': 'FI5kY)',
   'DA': '689' + to,
   'SOA': '466666',
   'Content': msg.encode('utf-8'),
   'Flags': 1
   }
try:
   rsp = urllib2.urlopen( url, urllib.urlencode(params))
except urllib2.HTTPError, e:
   print( u'Erreur HTTP : %s' % e.code)
   sys.exit(1)
except urllib2.URLError, e:
   print( u'Erreur connexion : %s' % e.args)
   sys.exit(2)

if rsp.code!=200:
   print( u'Erreur requête, code %d' % rsp.code)
   sys.exit(3)

smsid = nb = status = None
for l in rsp.readlines():

   if smsid is None: # Recherche ligne MsgId
      m = re.match(r'MsgId=(\d+)', l)
      if m:
         smsid = m.group(1)
      else:
         continue

   elif nb is None: # Recherche ligne NbSMS
      m = re.match(r'NbSMS=(\d+)', l)
      if m:
         nb = m.group(1)

   else: # MsgId et NbSMS trouvés, la ligne suivante contient l'état
      status = l[:-5]
      break

print (u'Requête OK (%s), réponse : id=%s, nb=%s, status=%s' % (
   rsp.code, smsid, nb, status))

