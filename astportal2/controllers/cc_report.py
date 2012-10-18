# -*- coding: utf-8 -*-
'''
Report form

Called when call is hung up from templates/cc_monitor.py if HangupURL
has been configured accordingly.
'''

from tg import expose, tmpl_context, validate, request
from repoze.what.predicates import in_group, not_anonymous
from tw.forms import TableForm, TextField, SingleSelectField, \
   TextArea, HiddenField, Button
from tw.forms.validators import NotEmpty, Int, Schema, Invalid

from astportal2.model import DBSession, Phonebook, Report
from astportal2.lib.base import BaseController

import logging
log = logging.getLogger(__name__)

from email.message import Message
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


# List of subjects grouped by categories
subjects = [ 
   (None,[
      (-1, u' - - - ') ]),
   ('Banque au quotidien',[
      (10, u'Information produits/services'),
      (11, u'Information sur compte') ]),
   ('Moyens de paiement',[
      (20, u'Virement compte à compte BDP'),
      (21, u'Création / modification d\'un virement permanent'),
      (22, u'Opposition sur Carte'),
      (23, u'Refabrication de la carte'),
      (24, u'Commande de chéquier, chèque de banue, de service aux particuliers et de devises') ]),
   ('Epargne et placement',[
      (30, u'Versement sur PEL'),
      (31, u'Modification de contrat PEL'),
      (32, u'Versement libre sur Assurance vie') ]),
   ('Divers',[
      (40, u'Banque à distance'),
      (41, u'MAJ coordonnées client'),
      (42, u'Prise de RDV'),
      (43, u'Réclamation'),
      (44, u'Autres') ]),
]

# Subject code -> text
subjects_dict = {}
for s in subjects:
    for ss in s[1]:
        subjects_dict[ss[0]] = ss[1]


def managers():
   ''' Returns list of managers for select field
   '''
   m = [('null', u' - - - ')]
   for pb in DBSession.query(Phonebook). \
      filter(Phonebook.code!=None). \
      filter(Phonebook.email!=None). \
      order_by(Phonebook.lastname). \
      order_by(Phonebook.firstname):
      name = pb.firstname + ' ' if pb.firstname is not None else u''
      name += pb.lastname if pb.lastname is not None else u''
      m.append((pb.code, name))
   return m


def email(sender, to, customer, manager, message, subject):
   ''' Create and send email
   '''

   # Create email 
   msg = MIMEMultipart('alternative')
   msg['Subject'] = u'Appel au Call Center Multimédia'
   msg['To'] = to
   msg['From'] = sender
   msg.preamble = 'Please use a MIME-aware mail reader to read this email.\n'

   # Text part
   text = u'''\
Nom / Prénom Client : %s
Nom du gestionnaire : %s

Bonjour,
Votre client vient de contacter le Call Center Multimédia, 
il souhaite :
-------------------
%s
-------------------
(%s)


Merci et bonne réception
'''
   part = MIMEText(text % (customer, manager, message, subject), \
      _subtype='plain', _charset='utf-8')
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
Nom / Prénom Client : <em>%s</em><br/>
Nom du gestionnaire : <em>%s</em><br/>

<p>Bonjour,</p>
Votre client vient de contacter le Call Center Multimédia,<br/>
il souhaite :
<pre class="shadow">
%s
</pre>
(%s)<br/>

<p>Merci et bonne réception</p>
</body></html>
'''
   part = MIMEText(text % (customer, manager, message, subject), \
      _subtype='html', _charset='utf-8')
   msg.attach(part)

   # Send email
   s = smtplib.SMTP()
   s.connect('localhost')
   s.sendmail(sender, to, msg.as_string())
   s.close()


class Send_validate(Schema):
   def validate_python(self, value, state):
      if value['send_or_save']==u'send' and value['manager']==u'null':
         raise Invalid(
            u'Veuillez sélectionner un gestionnaire pour envoyer le message',
            value, state)
      return value


class CC_Report_form(TableForm):
   validator = Send_validate
   fields = [
      SingleSelectField('subject', 
         validator=Int(min=0, messages= {
            'tooLow': u'Veuillez choisir un objet'}),
         options = subjects,
         label_text=u'Objet', help_text=u'Choisisséz un objet'),
      TextField('customer', validator=NotEmpty,
         label_text = u'Nom / Prénom du client', 
         help_text = u'Entrez les nom et prénom du client'),
      SingleSelectField('manager',
         options = managers,
         label_text = u'Nom du gestionnaire', 
         help_text = u'Entrez le nom du gestionnaire'),
      TextArea('message', validator=NotEmpty,
         label_text = u'Message', 
         help_text = u'Entrez le message à transmettre'),
      HiddenField('uid'),
      HiddenField('member'),
      HiddenField('queue'),
      HiddenField('custom1'),
      HiddenField('custom2'),
      HiddenField('send_or_save'),
      Button('send',
         label_text = u'Email au gestionnaire', 
         attrs={
         'onclick': 'document.forms[0].send_or_save.value="send"; submit()',
         'name': 'send', 'value': u'Envoyer'}),
      Button('save', 
         label_text = u'Enregistrement pour statistiques',
         attrs={
         'onclick': 'document.forms[0].send_or_save.value="save"; submit()',
         'name': 'save', 'value': u'Sauver'})
      ]
   submit_text = None
   action = '/cc_report/save'
   hover_help = True
cc_report_form = CC_Report_form('cc_report')


class CC_Report_ctrl(BaseController):

   allow_only = not_anonymous(
      msg=u'Veuiller vous connecter pour accéder à cette page')

   @expose(template='astportal2.templates.form_cc_report')
   def index(self, **kw):
      ''' Display the report form
      '''
      v = {
         'uid': kw['uid'],
         'member': kw['member'],
         'queue': kw['queue'],
         'custom1': kw['custom1'],
         'custom2': kw['custom2'],
         'send_or_save': '?'
      }
      tmpl_context.form = cc_report_form
      return dict(title = u'Compte rendu d\'appel', close=None, values=v)


   @expose(template='astportal2.templates.form_cc_report_close')
   @validate(cc_report_form, error_handler=index)
   def save(self, uid, member, queue, custom1, custom2, send_or_save,
         subject, customer, manager, message):

      log.debug(u'Action: %s' % send_or_save)
      log.debug(request.identity['user'])

      if manager!='null':
         m = DBSession.query(Phonebook).filter(Phonebook.code==manager).one()
         to = m.email
         name = m.firstname + ' ' if m.firstname is not None else u''
         name += m.lastname if m.lastname is not None else u''
         manager = '%s (%s)' % (manager, name)

      else:
         to = name = manager = None

      if send_or_save=='send' and to is not None:
         sender = request.identity['user'].email_address
         email(sender, to, customer, name, message, subjects_dict[subject])
         html = u'Message envoyé'

      else:
         html = u'Compte-rendu sauvé'

      r = Report()
      r.user_id = request.identity['user'].user_id
      r.uniqueid = uid
      r.member_id = member
      r.queue_id = queue
      r.custom1 = custom1
      r.custom2 = custom2
      r.subject = subject
      r.customer = customer
      r.manager = manager
      r.message = message
      r.email = to
      DBSession.add(r)

      return dict(title=html)

