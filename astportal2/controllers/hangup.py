# -*- coding: utf-8 -*-
'''
Hangup form

Called when call is hung up from templates/cc_monitor.py if HangupURL
has been configured accordingly.
'''

from tg import expose, flash, redirect, tmpl_context, validate, request, response, session

from astportal2.model import DBSession, Phonebook, Report, View_phonebook
from astportal2.lib.base import BaseController

from tw.api import js_callback
from tw.forms import TableForm, TextField, SingleSelectField, TextArea, HiddenField, Button
#from tw.forms.validators import NotEmpty, Int, Bool

import logging
log = logging.getLogger(__name__)

subjects = [ 
   (None,[
      (-1, u' - - - ') ]),
   ('Banque au quotidien',[
      (0, u'Information produits/services'),
      (1, u'Information sur compte') ]),
   ('Moyens de paiement',[
      (2, u'Virement compte à compte BDP'),
      (3, u'Création / modification d\'un virement permanent'),
      (4, u'Opposition sur Carte'),
      (5, u'Refabrication de la carte'),
      (6, u'Commande de chéquier, chèque de banue, de service aux particulier et de devises') ]),
   ('Epargne et placement',[
      (7, u'Versement sur PEL'),
      (8, u'Modification de contrat PEL'),
      (9, u'Versement libre sur Assurance vie') ]),
   ('Divers',[
      (10, u'Banque à distance'),
      (11, u'MAJ coordonnées client'),
      (12, u'Prise de RDV'),
      (13, u'Réclamation'),
      (14, u'Autres') ]),
]

def managers():
   m = [(-1, u' - - - ')]
   for pb in DBSession.query(Phonebook). \
      filter(Phonebook.code!=None). \
      filter(Phonebook.email!=None). \
      order_by(Phonebook.lastname). \
      order_by(Phonebook.firstname):
      name = pb.firstname + ' ' if pb.firstname is not None else u''
      name += pb.lastname if pb.lastname is not None else u''
      m.append((pb.code, name))
   return m

#------------------------------------
def email(sender, to, customer, manager, message, subject):

   # Création email avec pièce jointe CSV
   from email.message import Message
   from email.mime.multipart import MIMEMultipart
   from email.mime.text import MIMEText
   from time import strftime

   now = strftime('%d/%m/%Y %H:%M:%S')
   recipients = ('jd.girard@sysnux.pf',)

   msg = MIMEMultipart()
   msg['Subject'] = u'Appel au Call Center Multimédia %s' %  (now)
   msg['To'] = ', '.join(recipients)
   msg['From'] = sender

   msg.preamble = 'Please use a MIME-aware mail reader to read this email.\n'

   part = MIMEText(u'''\
Nom/Prénom Client : %s
Nom du gestionnaire : %s

Bonjour,
Votre client vient de contacter le Call Center Multimédia, 
il souhaite :
%s
(%s).
Merci et bonne réception
   
Merci'''.encode('utf_8') % (customer, manager, message, subject), \
   _subtype='plain', _charset='utf-8')

   msg.attach(part)

   # Envoi email
   import smtplib
   s = smtplib.SMTP()
   s.connect('localhost')
   s.sendmail(sender, recipients, msg.as_string())
   s.close()

#------------------------------------


class Hangup_form(TableForm):
   fields = [
      SingleSelectField('subject',
         options = subjects,
         label_text=u'Objet', help_text=u'Choisisséz un objet'),
      TextField('customer',
         label_text = u'Nom / Prénom du client', 
         help_text = u'Entrez les nom et prénom du client'),
      SingleSelectField('manager',
         options = managers,
         label_text = u'Nom du gestionnaire', 
         help_text = u'Entrez le nom du gestionnaire'),
      TextArea('message',
         label_text = u'Message', 
         help_text = u'Entrez le message à transmettre'),
      HiddenField('uniqueid'),
      HiddenField('member'),
      HiddenField('queue'),
      HiddenField('custom1'),
      HiddenField('custom2'),
      HiddenField('send_or_save'),
      Button('send', attrs={'onclick': 'document.forms[0].send_or_save.value="send"; submit()',
         'name': 'send', 'value': u'Envoyer'}),
      Button('save',  attrs={'onclick': 'document.forms[0].send_or_save.value="save"; submit()',
         'name': 'save', 'value': u'Sauver'})
      ]
   submit_text = None
   action = '/hangup/save'
   hover_help = True
hangup_form = Hangup_form('hangup')


class Hangup_ctrl(BaseController):

   @expose(template="astportal2.templates.form_hangup")
   def index(self, **kw):
      ''' Display the hangup form
      '''
      v = {
         'uniqueid': kw['uid'],
         'member': kw['member'],
         'queue': kw['queue'],
         'custom1': kw['custom1'],
         'custom2': kw['custom2'],
         'send_or_save': '?'
      }
      tmpl_context.form = hangup_form
      return dict(title = u'Compte rendu d\'appel', debug=None, values=v)

   @expose()
   def save(self, uniqueid, member, queue, custom1, custom2, send_or_save,
         subject, customer, manager, message):

      log.debug(u'Action: %s' % send_or_save)
      data = u'Envoyé' if send_or_save=='send' else u'Sauvé'
      r = Report()
      r.uniqueid = uniqueid
      r.member_id = member
      r.queue_id = queue
      r.custom1 = custom1
      r.custom2 = custom2
      r.subject = subject
      r.customer = customer
      r.manager = manager
      r.message = message
      r.email = 'xxx@yyy.zz' if send_or_save=='send' else None
      DBSession.add(r)

      return u'<h2>Compte rendu</h2><ul>%s</ul>' % data


