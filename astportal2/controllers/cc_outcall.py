# -*- coding: utf-8 -*-
'''
Call center outgoing calls

Some functionnality depends on Asterisk configuration:
[stdexten]
 . . .
exten => _X.,n,GotoIf(${OUTCALL}?:no_outcall)
exten => _X.,n,Set(out=${CURL(http://192.168.0.200:8080/cc_outcall/uniqueid,outcall=${OUTCALL}&uniqueid=${UNIQUEID}&cookie=${COOKIE})})
exten => _X.,n(no_outcall),Set(__DYNAMIC_FEATURES=stop_monitor)
 . . .
'''

from tg import expose, tmpl_context, validate, request, session, flash, redirect
from tgext.menu import sidebar
from repoze.what.predicates import in_any_group, not_anonymous
from tw.forms import TableForm, TextArea, TextField, Button, CheckBox,\
         SingleSelectField, CalendarDateTimePicker, HiddenField, FileField
from tw.forms.validators import NotEmpty, Int, DateTimeConverter, \
         FieldStorageUploadConverter, Schema, Invalid
from tw.api import js_callback
from genshi import Markup

from astportal2.model import DBSession, Campaign, Customer, User, Outcall, CDR, Phonebook
from astportal2.lib.base import BaseController
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

from tg import config
default_cid = config.get('default_cid')

from sqlalchemy import func, desc
from re import sub
from datetime import datetime, timedelta
from random import randint
from string import capwords
import logging
log = logging.getLogger(__name__)

from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.encoders import encode_7or8bit
import smtplib
import vobject
from uuid import uuid4


campaign_grid = MyJqGrid( 
   id='grid', url='campaign_fetch', caption=u'Campagnes',
   colNames = [u'Nom', u'Active', u'Type', u'Clients actifs / total'],
   colModel = [ 
      { 'name': 'name', 'width': 80 },
      { 'name': 'active', 'width': 160 },
      { 'name': 'type', 'width': 100,  },
      { 'name': 'count', 'width': 80, 'sortable': False},
   ],
   sortname = 'name',
   navbuttons_options = {'view': False, 'edit': False, 'add': False,
      'del': False, 'search': False, 'refresh': True, 
      }
)


result_options = (
   (-1, u' - - - '),
   (0, u'RDV Call Center'),
   (1, u'\u00C0 rappeler'),
#   (2, u'\u00C0 rappeler une deuxième fois'),
   (3, u'Dernier rappel'),
   (4, u'Contacte directement son cc/réfléchi'),
   (5, u'Pas intéressé / coupe court'),
   (6, u'Absent pendant la campagne'),
   (7, u'Décédé'),
   (8, u'Faux numéro / Aucun numéro'),
   (9, u'Injoignable'),
   (10, u'Hors cible'),
   (11, u'Réclamation')
)
result_text = [r[1] for r in result_options]


cmp_types = ((-1, ' - - - '), (0, u'Commerciale'), 
   (1, u'Récurrente'), (2, u'\u00C9vénementielle'))

def campaign_row(c):
   '''Displays a formatted row of the campaigns list
   Parameter: Campaign object
   '''
   row = []
   now = datetime.now()
   active = False
   if c.active:
      if c.begin and c.end:
         if c.begin<now<c.end: 
            active = True
      elif c.begin:
         if c.begin<now:
            active = True
      elif c.end:
         if now<c.end:
            active = True
      else: 
         active = True
   if active:
      row.append(
         u'<a href="#" onclick="postdata(\'list\',{cmp_id:%d, cmp_name:\'%s\'})" title="Utiliser">%s</a>' % (
         c.cmp_id, c.name, c.name))
   else:
      row.append(c.name)

   if c.active:
      if c.begin and c.end:
         row.append(u'Du %s au %s' %(
            c.begin.strftime('%d/%m/%y %H:%M'),
            c.end.strftime('%d/%m/%y %H:%M') ))
      elif c.begin:
         row.append(u'\u00C0 partir du %s' % c.begin.strftime('%d/%m/%y %H:%M'))
      elif c.end:
         row.append(u"Jusqu'au %s" % c.end.strftime('%d/%m/%y %H:%M'))
      else:
         row.append(u'Oui')
   else:
      row.append(u'Non')

   row.append(cmp_types[1+c.type][1])
   row.append(u'%d / %d' % (DBSession.query(Customer). \
         filter(Customer.cmp_id==c.cmp_id). \
         filter(Customer.active==True).count(),
      DBSession.query(Customer). \
         filter(Customer.cmp_id==c.cmp_id). \
         count()))

   return row


def customer_row(c, managers):
   ''' Returns a formatted row for the list of cutomers
   Parameter: customer object
   '''
   row = []
   row.append(Markup(
      u'''<a href="#" onclick="postdata('crm', {cust_id:%d})">%s</a>''' % (
      c.cust_id, 
      capwords(c.display_name))))
   row.append(('CLIPRI', 'CLICOM', 'CLIPRO VD', 'CLIPRO VP', 'CASDEN')[c.type])
   row.append(c.branch)
   
   try:
      row.append(managers[c.manager])
   except:
      log.error(u'customer_row: manager "%s" not found!' % c.manager)
      row.append(c.manager)

   phones = []
   if c.phone1:
      phones.append(c.phone1)
   if c.phone2:
      phones.append(c.phone2)
   if c.phone3:
      phones.append(c.phone3)
   if c.phone4:
      phones.append(c.phone4)
   if c.phone5:
      phones.append(c.phone5)
   row.append(Markup(', '.join(phones)))

   return row

dispo2text= {'BUSY': u'Occupé', 'FAILED': u'Erreur', 
   'ANSWERED': u'Répondu', 'NO ANSWER': u'Pas de réponse'}
def outcall_row(o):
   ''' Returns a formatted row for the calls list
   Parameter: outcall object
   '''
   created = o.Outcall.created.strftime("%a %d %b, %Hh%Mm")
   result = [r[1] for r in result_options][o.Outcall.result+1] \
      if o.Outcall.result is not None else u''
   comment = o.Outcall.comment
   if o.CDR is not None:
      result += u' (%s)' % dispo2text[o.CDR.disposition] \
         if o.CDR.disposition in dispo2text else o.CDR.disposition
      dst = o.CDR.dst
   else:
      dst = None
   return [created, dst, result, comment]


class CRM_validate(Schema):
   def validate_python(self, value, state):
      if value['result']==0 and (
            value['begin']=='' or value['duration']==-1):
         raise Invalid(
            u'Veuillez choisir une heure et durée de RDV',
            value, state)
      return value


crm_form = TableForm(
   'form0',
   validator = CRM_validate,
   name = 'form0',
   fields = [
      HiddenField('cust_id', validator=Int()),
      HiddenField('out_id', validator=Int()),
      HiddenField('phone'),
      SingleSelectField('result',
         label_text = u'Résultat d\'appel',
         validator=Int(min=0, messages= {
            'tooLow': u'Veuillez choisir un résultat'}),
         options = result_options,
         attrs = {'onchange': 'result_change()'}
         ),
      CalendarDateTimePicker('begin',
         label_text=u'Début', help_text=u'Date de début',
         date_format =  '%d/%m/%y %Hh%mm',
         not_empty = False, picker_shows_time = True,
         validator = DateTimeConverter(format='%d/%m/%y %Hh%Mm',
            messages = {'badFormat': 'Format date / heure invalide'}),
         ),
      SingleSelectField('duration',
         validator=Int(),
         label_text = u'Durée prévue',
         help_text = u'Durée prévue pour le RDV',
         options = ((-1, u' - - - '),
            (15, u'15 minutes'),
            (30, u'30 minutes'),
            (45, u'45 minutes'),
            (60, u'1 heure'),
            (75, u'1 heure 15 minutes'),
            (90, u'1 heure 30 minutes'),
            (105, u'1 heure 45 minutes'),
            (120, u'2 heure'),
            ),
         ),
      SingleSelectField('alarm_type',
         validator=Int(),
         label_text = u'Rappel',
         help_text = u'Type de rappel RDV ',
         options = ((-1, u' - - - '),
            (0, u'Pas de rappel'),
            (1, u'Rappel par email'),
            (2, u'Rappel par SMS'),
            ),
         attrs = {'onchange': 'alarm_change()'}
         ),
      TextField('alarm_dest',
         label_text = u'Destinaire rappel',
         help_text = u'Numéro GSM ou adresse email'),
      TextArea('message',
         attrs = {'rows': 4, 'cols': 40},
         help_text=u'Message à destination du gestionnaire et du responsable d\'agence',
         label_text=u'Message'),
      TextArea('comment',
         attrs = {'rows': 4, 'cols': 40},
         help_text=u'Pour statistiques call center multimédia',
         label_text=u'Observations'),
      Button('mysubmit',
         attrs={ 'value': u'Envoyer',
            'onclick': 'my_submit();'}),
      ],
   submit_text = None,
   action = 'result',
   hover_help = True,
)


def email_appointment(sender, to, message, cust_id, cust_name, cust_phone, 
      cmp_name, begin, duration, member_name):
   ''' Create and send email with iCalendar event attached
   '''

   # Create email 
   msg = Message()
   msg['Subject'] = u'RDV Call center Multimédia %s' % cust_name
   msg['To'] = to
   msg['From'] = sender
   msg['Content-class'] = 'urn:content-classes:calendarmessage'
   msg['Content-type'] = 'text/calendar; method=REQUEST; charset=UTF-8'
   msg['Content-transfer-encoding'] = '8BIT'

   # vCal (vobject automatically adds missing fields, eg. UUID)
   vcal = vobject.newFromBehavior('vcalendar')
   vcal.add('method').value = u'REQUEST'
   vcal.add('vevent')
   vcal.add('prodid').value = '-//SysNux.pf/NONSGML AstPortal V1.0//EN'
   vcal.add('version').value = '2.0'
   vcal.vevent.add('description').value = u'''Rendez-vous fixé par le Call Center Multimédia pour la campagne "%s"

Client n°%s / %s
N° de téléphone : %s
Message :
-----
%s
-----

Observations particulières :
NB : Cet événement est envoyé à titre d'information et ne nécessite pas de retour.

Merci et bonne réception
%s
''' % (cmp_name, cust_id, cust_name, cust_phone, message, member_name)
   vcal.vevent.add('dtstart').value = begin
   vcal.vevent.add('dtend').value = begin + timedelta(0, duration*60)
   vcal.vevent.add('class').value = u'PUBLIC'
   vcal.vevent.add('dtstamp').value = datetime.now()
   vcal.vevent.add('created').value = datetime.now()
   vcal.vevent.add('last-modified').value = datetime.now()
   vcal.vevent.add('organizer').value = u'mailto:%s' % sender
   vcal.vevent.add('attendee').value = u'mailto:%s' % to
   vcal.vevent.add('transp').value = 'OPAQUE'
   vcal.vevent.add('summary').value = u'RDV %s' % cust_name
   vcal.add('vtimezone')
   vcal.vtimezone.add('tzid').value = 'Pacific/Tahiti'
   vcal.vtimezone.add('x-lic-location').value = 'Pacific/Tahiti'
   vcal.vtimezone.add('standard')
   vcal.vtimezone.standard.add('TZOFFSETFROM').value = '-1000'
   vcal.vtimezone.standard.add('TZOFFSETTO').value = '-1000'
   vcal.vtimezone.standard.add('TZNAME').value = 'TAHT'
   vcal.vtimezone.standard.add('DTSTART').value = datetime(1970,1,1)
#   valarm = vobject.newFromBehavior('VALARM')
#   valarm.add('trigger').value = timedelta(-1)
#   valarm.add('action').value = 'email'
#   valarm.add('attendee').value = to
#   valarm.add('summary').value = 'Rappel RDV %s' % cust_name
#   valarm.add('description').value = 'RDV dans 24 heures avec client %s' % cust_id
#   vcal.vevent.add(valarm)
   log.debug(vcal.prettyPrint())
   msg.set_payload(vcal.serialize())

   # Send email
   log.debug(msg.as_string())
   s = smtplib.SMTP()
   try:
      s.connect('localhost')
      s.sendmail(sender, to, msg.as_string())
      s.close()
   except:
      flash(u'Une erreur est survenue, l\'email n\'a pu être envoyé', 'error')


def email_other(sender, to, message, cust_id, cust_name, cust_phone, 
      member_name, intro):
   ''' Create and send reclaim or other email
   '''

   # Create email 
   msg = MIMEMultipart('alternative')
   msg['Subject'] = u'Appel au Call Center Multimédia'
   msg['To'] = ', '.join(to)
   msg['From'] = sender
   msg.preamble = 'Please use a MIME-aware mail reader to read this email.\n'

   # Text part
   text = u'''\
Bonjour,

Suite appel auprès du client, %s.

Client n°%s / %s
N° de téléphone : %s
Message :
%s

Observations particulières :
NB : Ce mail est envoyé à titre d'information et ne nécessite pas de retour.

Merci et bonne réception
%s
''' % (intro, cust_id, cust_name, cust_phone, message, member_name)
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

<p>Suite appel auprès du client, %s.</p>

Client n°%s / %s.<br/>
<u>N° de téléphone :</u> %s.<br/>
<h4>Message :</h4>
<pre class="shadow">
%s
</pre>
<h4>Observations particulières :</h4>
<u>NB :</u> Ce mail est envoyé à titre d'information et ne nécessite pas de retour.<br/>
<p>Merci et bonne réception,<br/>
%s</p>

</body></html>
''' % (intro, cust_id, cust_name, cust_phone, message, member_name)
   part = MIMEText(text, _subtype='html', _charset='utf-8')
   msg.attach(part)

   # Send email
   s = smtplib.SMTP()
   try:
      s.connect('localhost')
      s.sendmail(sender, to, msg.as_string())
      s.close()
   except:
      flash(u'Une erreur est survenue, l\'email n\'a pu être envoyé', 'error')


class CC_Outcall_ctrl(BaseController):

#   allow_only = not_anonymous(
#      msg=u'Veuiller vous connecter pour accéder à cette page')

   @sidebar(u"-- Groupes d'appels || Campagnes", sortorder=14,
         icon = '/images/megaphone.png')
   @expose(template='astportal2.templates.grid_cc_outcall')
   def index(self):
      ''' Display the list of existing campaigns
      '''

      # User must be admin or queue supervisor or queue member
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
         sv.append('AG ' + q)
      if not in_any_group(*sv):
         tmpl_context.grid = None
         flash(u'Accès interdit !', 'error')
      else:
         tmpl_context.grid = campaign_grid
      tmpl_context.form = None

      return dict(title=u"Liste des campagnes", debug='')


   @expose('json')
   def campaign_fetch(self, page, rows, sidx, sord, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      # Try and use grid preference
      grid_rows = session.get('grid_rows', None)
      if rows=='-1': # Default value
         rows = grid_rows if grid_rows is not None else 25

      # Save grid preference
      session['grid_rows'] = rows
      session.save()
      rows = int(rows)

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * int(rows)
      except:
         offset = 0
         page = 1
         rows = 25

      data = DBSession.query(Campaign).filter(Campaign.deleted==None)
      total = 1 + data.count() / rows
      column = getattr(Campaign, sidx)
      data = data.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      rows = [ { 'id'  : a.cmp_id, 'cell': campaign_row(a) } for a in data ]

      return dict(page=page, total=total, rows=rows)


   @expose(template='astportal2.templates.grid_cc_outcall')
   def list(self, cmp_id, cmp_name):
      ''' Display the list of customers
      '''

      # User must be admin or queue supervisor or queue member
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
         sv.append('AG ' + q)
      if not in_any_group(*sv):
         tmpl_context.grid = None
         flash(u'Accès interdit !', 'error')
      else:
         tmpl_context.grid = MyJqGrid( 
            id='grid', url='customer_fetch', caption=u'Clients',
            colNames = [u'Nom', u'Type', u'agence', u'Gestionnaire', u'Téléphone(s)'],
            colModel = [ 
               { 'name': 'name', 'width': 160 },
               { 'name': 'type', 'width': 40 },
               { 'name': 'branch', 'width': 40,  },
               { 'name': 'code', 'width': 60,  },
               { 'name': 'phone', 'width': 160, 'sortable': False, 'search': False },
            ],
            postData = {'cmp_id': cmp_id},
            sortname = 'lastname',
            navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': False, 'refresh': True, 
            },
         )

      tmpl_context.form = None

      return dict(title=u'Clients pour la campagne "%s"' % cmp_name, debug='')


   @expose('json')
   def customer_fetch(self, page, rows, sidx, sord, cmp_id, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      # Try and use grid preference
      grid_rows = session.get('grid_rows', None)
      if rows=='-1': # Default value
         rows = grid_rows if grid_rows is not None else 25

      # Save grid preference
      session['grid_rows'] = rows
      session.save()
      rows = int(rows)

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * int(rows)
      except:
         offset = 0
         page = 1
         rows = 25

      data = DBSession.query(Customer). \
         filter(Customer.cmp_id==cmp_id). \
         filter(Customer.active==True)
      total = 1 + data.count() / rows
      column = getattr(Customer, sidx if sidx!='name' else 'lastname')
      data = data.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      managers = dict([ (pb.code, u'%s %s' % (pb.firstname, pb.lastname)) \
         for pb in DBSession.query(Phonebook).\
            filter(Phonebook.account_manager==True).\
            filter(Phonebook.code!=None) ])
      rows = [ { 'id'  : a.cust_id, 'cell': customer_row(a, managers) } for a in data ]

      return dict(page=page, total=total, rows=rows)


   @expose('json')
   def originate(self, exten, cust):
      ''' Originate call
      '''
      uphones = DBSession.query(User).get(request.identity['user'].user_id).phone
      if len(uphones)<1:
         return dict(status=2)

      o = Outcall()
      o.user_id = request.identity['user'].user_id
      o.cust_id = cust
      o.cookie = randint(-2147483648, 2147483647)
      DBSession.add(o)
      DBSession.flush() # needed to get the out_id

      chan = uphones[0].sip_id
      exten = sub(r'\D', '', exten)
      log.debug('originate: outcall %d from extension %s to %s' % (
         o.out_id, chan, exten))
      res = Globals.manager.originate(
            'SIP/' + chan.encode('iso-8859-1'), # Channel
            exten.encode('iso-8859-1'), # Extension
            context=chan.encode('iso-8859-1'),
            priority='1',
            caller_id=default_cid,
            variables= {'OUTCALL': o.out_id,
               'COOKIE': o.cookie},
            async = True   # Seems to be needed else DB is not commited and
                           # call to uniqueid below fails with "inexistant call"
            )
      status = o.out_id if res.headers['Response']==u'Success' else -1
      log.debug('originate: res=%s, outcall=%d, status=%s, cookie=%d' % (
         res, o.out_id, status, o.cookie))
      return dict(status=status)


   @expose()
   def uniqueid(self, outcall, cookie, uniqueid):
      ''' Called by Asterisk (function CURL) to update the uniqueid 
      related to an outcall
      '''
      outcall = int(outcall)
      o = DBSession.query(Outcall).get(outcall)

      if not o:
         log.warning('Inexistant outcall (%d)' % outcall)
         return u'ko'

      if o.cookie!=int(cookie):
         log.warning('Wrong cookie (%s) for outcall (%d)' % (
            cookie, outcall))
         return u'ko'

      log.debug('Setting uniqueid for outcall <%d>' % outcall)
      o.uniqueid = uniqueid
      return u'ok'



   @expose(template='astportal2.templates.cc_outcall_crm')
   def crm(self, cust_id, out_id=None, result=None, message=None,
         begin=None, duration=None, alarm_type=None, alarm_dest=None,
         comment=None, next=None, prev=None):
      ''' CRM page
      '''

      cust_id = int(cust_id)
      c = DBSession.query(Customer).get(cust_id)

      if next:
         cc = DBSession.query(Customer). \
            filter(Customer.cmp_id==c.cmp_id). \
            filter(Customer.active==True). \
            filter(func.lower(Customer.lastname)>c.lastname.lower()). \
            order_by(func.lower(Customer.lastname)). \
            first()
         if cc:
            c = cc
            cust_id = cc.cust_id

      elif prev:
         cc = DBSession.query(Customer). \
            filter(Customer.cmp_id==c.cmp_id). \
            filter(Customer.active==True). \
            filter(func.lower(Customer.lastname)<c.lastname.lower()). \
            order_by(desc(func.lower(Customer.lastname))). \
            first()
         if cc:
            c = cc
            cust_id = cc.cust_id

      if not c.active:
         # Return to list of customers
         redirect('/cc_outcall/list', params={
            'cmp_id': c.campaign.cmp_id,
            'cmp_name': c.campaign.name})

      type = ('CLIPRI', 'CLICOM', 'CLIPRO VD', 'CLIPRO VP', 'CASDEN')[c.type]
      phone1 = c.phone1
      phone2 = c.phone2
      phone3 = c.phone3
      phone4 = c.phone4
      phone5 = c.phone5
      ph1_click = {'onclick': 'originate("%s",%d)' % (c.phone1, cust_id)}
      ph2_click = {'onclick': 'originate("%s",%d)' % (c.phone2, cust_id)}
      ph3_click = {'onclick': 'originate("%s",%d)' % (c.phone3, cust_id)}
      ph4_click = {'onclick': 'originate("%s",%d)' % (c.phone4, cust_id)}
      ph5_click = {'onclick': 'originate("%s",%d)' % (c.phone5, cust_id)}
      email_href = {'href': 'mailto:%s' % c.email}
      grc = {'onclick': 'grc("%s")' % c.code}
      try:
         cal = {'onclick': 'cal("%s")' % DBSession.query(Phonebook.email).filter(Phonebook.code==c.manager).one()}
      except:
         cal = {'onclick': u'alert("email gestionnaire %s pas trouvé")' % c.manager}
      back_list = {
         'onclick': 'postdata("list",{cmp_id:%d,cmp_name:"%s"})' % (
         c.campaign.cmp_id, c.campaign.name)}
      next_cust = {
         'onclick': 'postdata("crm",{cust_id:%d,next:true})' % cust_id}
      prev_cust = {
         'onclick': 'postdata("crm",{cust_id:%d,prev:true})' % cust_id}
      title = u'%s : %s' % (c.campaign.name, capwords(c.display_name))

      tmpl_context.grid = MyJqGrid( 
         id='grid', url='outcall_fetch', caption=u'Appels',
         colNames = [u'Date', u'Numéro', u'Résultat', u'Commentaire'],
         colModel = [ 
            { 'name': 'created', 'width': 80 },
            { 'name': 'dst', 'width': 40, 'sortable': False },
            { 'name': 'result', 'width': 160, 'sortable': False },
            { 'name': 'comment', 'width': 160, 'sortable': False },
         ],
         postData = {'cust_id': cust_id},
         sortname = 'created',
         navbuttons_options = {'view': False, 'edit': False, 'add': False,
            'del': False, 'search': False, 'refresh': True, 
         },
         loadComplete = js_callback('load_complete'),
      )

      tmpl_context.form = crm_form
      values = {'cust_id': cust_id, 'out_id': out_id, 'result': result,
         'begin': begin, 'duration': duration, 'message': message,
         'comment': comment}

      try:
         pb = DBSession.query(Phonebook).\
               filter(Phonebook.code==c.manager).one()
         manager = u'%s %s' % (pb.firstname, pb.lastname)
      except:
         manager = c.manager

      return dict(title=title, campaign=c.campaign.name, code=c.code, 
         branch=c.branch, name=capwords(c.display_name),
         phone1=phone1, phone2=phone2, phone3=phone3, phone4=phone4, phone5=phone5,
         type=type, email=c.email, manager=manager,
         ph1_click=ph1_click, ph2_click=ph2_click, ph3_click=ph3_click,
         ph4_click=ph4_click, ph5_click=ph5_click, email_href=email_href,
         grc_click=grc, cal_click=cal, back_list=back_list,
         next_cust=next_cust, prev_cust=prev_cust, values=values)


   @expose('json')
   def outcall_fetch(self, page, rows, sidx, sord, cust_id, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      # Try and use grid preference
      grid_rows = session.get('grid_rows', None)
      if rows=='-1': # Default value
         rows = grid_rows if grid_rows is not None else 25

      # Save grid preference
      session['grid_rows'] = rows
      session.save()
      rows = int(rows)

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * int(rp)
      except:
         offset = 0
         page = 1
         rows = 25

      data = DBSession.query(Outcall, CDR) \
         .outerjoin(CDR, Outcall.uniqueid==CDR.uniqueid) \
         .filter(Outcall.cust_id==cust_id)

      total = 1 + data.count() / rows
      column = getattr(Outcall, sidx)
      data = data.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      rows = [ 
         { 'id'  : a.Outcall.out_id, 'cell': outcall_row(a) } for a in data ]

      return dict(page=page, total=total, rows=rows)


   @expose()
   @validate(crm_form, error_handler=crm)
   def result(self, cust_id, out_id, result, message, comment, begin, duration, 
         alarm_type, alarm_dest, phone):
      ''' Called on form validation by agent
      '''
      log.info(u'result: cust_id=%d, out_id=%d, result=%d, comment=%s, begin=%s, duration=%d, alarm_type=%s, alarm_dest=%s, phone=%s.' % (
         cust_id, out_id, result, comment, begin, duration, 
         alarm_type, alarm_dest, phone))
   
      # Update outcall data   
      o = DBSession.query(Outcall).get(out_id)
      o.result = result
      o.comment = comment if comment else None
      o.phone = phone if phone else None
      o.message = message if message else None

      if result==0: # Appointment
         o.begin = begin
         o.duration = duration
         o.customer.active = False
         email_appointment(request.identity['user'].email_address, 
            o.manager.email,
            message if message is not None else '',
            o.customer.cust_id,
            capwords(o.customer.display_name),
            phone, o.customer.campaign.name, begin, duration, 
            request.identity['user'].display_name)

         o.alarm_type = alarm_type
         if alarm_type>0: # Destination needed
            o.alarm_dest = alarm_dest

#      elif result in (1, 2, 3): # Call again
#         pass

      elif result in (4, 5, 6, 7, 8, 9, 10, 11): # Reclaim or other
         # No more call
         o.customer.active = False
         intro = u'je t\'informe d\'une réclamation' if result==11 \
               else u'je te transmets le message ci dessous'
         email_other(request.identity['user'].email_address,
            (o.manager.email, 'g_recherches@sg-bdp.pf'), # responsable AG, Julien Buluc
            message if message is not None else '', o.customer.cust_id, 
            capwords(o.customer.display_name),
            phone, request.identity['user'].display_name, intro)

      # Move to next customer
      redirect('crm', params={
         'cust_id': cust_id, 'next': 'true'})

      # Return to list of customers
#      redirect('/cc_outcall/list', params={
#         'cmp_id': o.customer.campaign.cmp_id, 
#         'cmp_name': o.customer.campaign.name})

