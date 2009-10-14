# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context
from astportal2.model import CDR, DBSession
from tg.decorators import allow_only
from repoze.what import predicates
from pylons import tmpl_context
from pylons import request

import logging
log = logging.getLogger("astportal.controllers.cdr")

from tw.api import WidgetsList
from tw.forms import TableForm, HiddenField, Label, CalendarDatePicker, SingleSelectField, TextField, TextArea
from tw.forms.datagrid import DataGrid, Column
from tw.jquery import FlexiGrid


from genshi import Markup
from os import path
from re import compile

re_sip = compile('^SIP/poste\d-.*')
re_hm = compile('^\s*(\d\d?)\D(\d\d?)\s*$')

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


class Display_CDR:

   #allow_only = predicates.not_anonymous('NOT ANONYMOUS')
   paginate_limit = 25
   filtered_cdrs = None

   @expose(template="astportal2.templates.cdr")
   def index(self, limit_val=paginate_limit, number=None, in_out=None, date=None, hour=None, limit_sel=paginate_limit):

#      if not predicates.in_group('admin'):
#         flash(u'Accès interdit')
#         redirect('/')

      interval = '30 min'
      search_form = TableForm(
         name = 'search_form',
         fields = [
               HiddenField(name='limit_val', 
                  default = limit_val
                  ),
               Label( text = u'Sélectionnez un ou plusieurs critères'),
               TextField(
               attrs = {'size': 10, 'maxlength': 20},
                  default = number,
                  name = 'number',
                  label_text = u'Numéro'),
               SingleSelectField(
                  name = 'in_out',
                  label_text = u'Type',
                  default = in_out,
                  options = [ u'Indifférent', u'Entrant', u'Sortant' ]),
               CalendarDatePicker(
                  id = 'date', date_format =  '%d/%m/%Y', picker_shows_time = False ),
#                  attrs = {'readonly': True, 'size': 8},
#                  default = date or '',
#                  format = '%d/%m/%Y',
#                  validator = validators.DateTimeConverter(format="%d/%m/%Y"),
#                  name = 'date',
#                  button_text=u'Choisir...'),
               TextField(
                  attrs = {'size': 5, 'maxlength': 5},
                  default = hour,
#                  validator = validators.TimeConverter(format="%H:%M"),
                  name = 'hour',
                  label_text = u'Heure +/- ' + interval),
               SingleSelectField(
                  name = 'limit_sel',
                  label_text = u'Lignes par page',
                  default = limit_sel or limit_val,
                  options = [ 10, 25, 50, 100, 500 ])
  		],
      	)

      filter = []
      cdrs = DBSession.query(CDR)
      if number:
         filter.append(u'numéro contient ' + number)
         cdrs = cdrs.filter((CDR.src.like('%' + number + '%')) | (CDR.dst.like('%' + number + '%')))

      if in_out=='Entrant':
         filter.append(u'type entrant')
         cdrs = cdrs.filter(CDR.dstchannel.like('SIP/poste%'))
      elif in_out=='Sortant':
         filter.append(u'type sortant')
         cdrs = cdrs.filter(CDR.channel.like('SIP/poste%'))

      if date:
         filter.append(u'date ' + date)
         cdrs = cdrs.filter("calldate::date='" + date[6:10] + date[3:5] + date[0:2] + "'")

      if hour:
         try:
            (h,m) = re_hm.search(hour).groups()
            h = int(h)
            m = int(m)
            if h<0 or h>23 or m<0 or m>59:
               flash(u'Vérifiez le formulaire')
            else:
               filter.append(u'heure approximative ' + hour)
               hour = '%d:%02d' % (h,m)
               cdrs = cdrs.filter("'" + hour + "' - '" + interval + "'::interval <= calldate::time AND calldate::time <= '" + hour + "' + '" + interval + "'::interval")
         except:
            flash(u'Vérifiez le formulaire')

      grid = FlexiGrid( id='flexi', fetchURL='fetch', title=None,
            sortname='calldate', sortorder='desc',
            colModel = [ { 'display': u'Date / heure', 'name': 'calldate', 'width': 140 },
               { 'display': u'Source', 'name': 'src', 'width': 80 },
               { 'display': u'Destination', 'name': 'dst', 'width': 80 },
               { 'display': u'\u00C9tat', 'name': 'disposition', 'width': 100 },
               { 'display': u'Durée', 'name': 'billsec', 'width': 60 },
#               { 'display': u'\u00C9coute', 'width': 60, 'align':'center' },
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
      return dict( title=u'Appels traités', debug='', form=search_form, grid=grid)


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

