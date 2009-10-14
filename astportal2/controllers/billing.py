# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context
from astportal2.model import DBSession, CDR, Department, Phone, User
from tg.decorators import allow_only
from repoze.what import predicates
from pylons import tmpl_context
from pylons import request

import logging
log = logging.getLogger("astportal.controllers.cdr")

from tw.api import WidgetsList
from tw.forms import TableForm, HiddenField, Label, CalendarDatePicker, SingleSelectField, TextField, TextArea, MultipleSelectField
from tw.forms.datagrid import DataGrid, Column
from tw.jquery import FlexiGrid


from genshi import Markup
from os import path
from re import compile

re_sip = compile('^SIP/poste\d-.*')
re_hm = compile('^\s*(\d\d?)\D(\d\d?)\s*$')

class Billing_form(TableForm):
   '''
   '''

   import datetime
   dptms = [(d.dptm_id, d.comment) 
      for d in DBSession.query(Department).order_by(Department.name).all()]
   dptms.insert( 0, ('ALL',u'* - Tous les services') )
   phones = [(p.number, p.number) 
      for p in DBSession.query(Phone).order_by('number').all()]
   m = [ u'Janvier', u'Février', u'Mars', u'Avril', u'Mai', u'Juin', 
      u'Juillet', u'Août', u'Septembre', u'Octobre', u'Novembre', u'Décembre' ]
   month = [ ('', u' - - - - - - ') ]
   today = datetime.datetime.now()
   for i in range(0,12):
      j = today.month-i-2
      if j<0:
         y = today.year-1
         j += 12
      else:
         y = today.year
      month.append( ( '%04d%02d01' % (y,j+1), m[j] + ' ' + str(y)) )

   interval = '30 min'
   name = 'search_form'
   fields = [
      Label( text = u'Sélectionnez un ou plusieurs critères'),
#      TextField( attrs = {'size': 10, 'maxlength': 20},
#         name = 'number',
#         label_text = u'Numéro'),
      SingleSelectField(
         name = 'month',
         label_text = u'Mois',
         options = month),
      CalendarDatePicker(
         name = 'end',
         label_text = u'Date fin',
         date_format =  '%d/%m/%Y',
         picker_shows_time = False ),
      CalendarDatePicker(
         name = 'begin',
         label_text = u'Date début',
         date_format =  '%d/%m/%Y',
         picker_shows_time = False ),
      SingleSelectField(
         name = 'department',
         label_text = u'Service',
         options = dptms),
      MultipleSelectField(
         name = 'phones',
         label_text = u'Téléphones',
         options = phones),
   ]
   submit_text = u'Valider...'
   action = 'result'
   hover_help = True
new_billing_form = Billing_form('new_billing_form')


def rec_link(row):
   '''Create link to download recording if file exists'''
   if row.disposition != 'ANSWERED':
      return ''

   dir = '/var/spool/asterisk/monitor/' + row.calldate.strftime('%Y/%m/%d/')
   ts = row.calldate.strftime('-%Y%m%d-%H%M%S')

   if re_sip.search(row.channel):
      if len(dst)>4: dst = dst[1:]
      file1 = 'out-' + row.channel[4:10] + '-' + row.dst + '-' + row.uniqueid + '.wav'
      file2 = 'out-' + row.channel[4:10] + '-' + row.dst + ts +'.wav'
   elif re_sip.search(row.dstchannel):
      file1 = 'in-' + row.dstchannel[4:10] + '-' + row.src + '-' + row.uniqueid + '.wav'
      file2 = 'in-' + row.dstchannel[4:10] + '-' + row.src + ts + '.wav'
   else:
      file1 = file2 = None
#      return ''

   if file1 and path.exists(dir + file1): 
      file = file1
   elif file2 and path.exists(dir + file2):
      file = file2
   else:
      file = None
#      return ''

   file = dir + 'XXX'
   link = Markup('<a href="#" title="&Eacute;coute" onclick="ecoute(\'' + file + '\')"><img src="/images/sound_section.png" border="0" alt="&Eacute;coute" /></a>')
   return link


def f_bill(billsec):
   '''Formatted billing'''
   h = billsec/3600
   s = billsec-3600*h
   m = s/60
   s = s%60
   return '%d:%02d:%02d' % (h, m, s)


def f_disp(disposition):
   '''Formatted disposition'''
   disp=disposition
   if disposition=='ANSWERED': disp = u'Communication'
   elif disposition=='BUSY': disp = u'Occupé'
   elif disposition=='FAILED': disp = u'Echec'
   elif disposition=='NO ANSWER': disp = u'Pas de réponse'
   return disp


class Billing_ctrl:

   #allow_only = predicates.not_anonymous('NOT ANONYMOUS')
   paginate_limit = 25
   filtered_cdrs = None

   @expose(template="astportal2.templates.form_new")
   def index(self):
      '''Formulaire facturation
      '''
      tmpl_context.form = new_billing_form
      return dict( title=u'Facturation', debug='',values='')

   @expose(template="astportal2.templates.flexigrid")
   def result(self, month=None, end=None, begin=None, department='ALL', phones=None):

#      if not predicates.in_group('admin'):
#         flash(u'Accès interdit')
#         redirect('/')

      filter = []
# XXX
      cdrs = DBSession.query(CDR)

      grid = FlexiGrid( id='flexi', fetchURL='fetch', title=None,
            sortname='calldate', sortorder='desc',
            colModel = [ { 'display': u'Date / heure', 'name': 'calldate', 'width': 140 },
               { 'display': u'Source', 'name': 'src', 'width': 80 },
               { 'display': u'Destination', 'name': 'dst', 'width': 80 },
               { 'display': u'\u00C9tat', 'name': 'disposition', 'width': 100 },
               { 'display': u'Durée', 'name': 'billsec', 'width': 60 },
               ],
            usepager=True,
            useRp=True,
            rp=10,
            resizable=False,
            )

      if len(filter):
         if len(filter)>1: m = u'Critères: '
         else: m = u'Critere: '
         flash( m + ', et '.join(filter) + '.')

      global filtered_cdrs
      filtered_cdrs = cdrs
      tmpl_context.grid = grid
      return dict( title=u'Facturation', debug='', form='')


   @expose('json')
   def fetch(self, page=1, rp=25, sortname='calldate', sortorder='desc', qtype=None, query=None):

      try:
         offset = (int(page)-1) * int(rp)
      except:
         offset = 0
         page = 1
         rp = 25

      global filtered_cdrs
      cdrs = filtered_cdrs
      total = cdrs.count()
      column = getattr(CDR, sortname)
      cdrs = cdrs.order_by(getattr(column,sortorder)()).offset(offset).limit(rp)
      rows = [
            {
               'id'  : cdr.acctid,
               'cell': [
                  cdr.calldate, cdr.src, cdr.dst,
                  f_disp(cdr.disposition),
                  f_bill(cdr.billsec)# , rec_link(cdr)
                  ]
               } for cdr in cdrs
            ]

      return dict(page=page, total=total, rows=rows)


   @expose(content_type='audio/wav')
   @allow_only(predicates.not_anonymous())
   def ecoute(self, date=None, file=None):

      import paste.fileapp
      f = paste.fileapp.FileApp('/usr/share/games/extremetuxracer/music/start1-jt.ogg')
      f.content_type = 'audio/ogg'
      f.content_disposition = 'attachment'
      f.filename = file
      from tg import use_wsgi_app
      return use_wsgi_app(f)

      if not predicates.in_group('TDM'):
         flash(u'Accès interdit')
         redirect('/')

      if not path.exists(file): 
         flash(u'Enregistrement introuvable: ' + file)
         redirect('/cdr/')

      return serve_file(path=dir + file, contentType='audio/wav', disposition='attachment', name=file)

