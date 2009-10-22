# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context, validate
from astportal2.model import CDR, DBSession
from tg.decorators import allow_only
from repoze.what import predicates

import logging
log = logging.getLogger("astportal.controllers.cdr")

from tw.api import WidgetsList
from tw.forms import TableForm, HiddenField, Label, CalendarDatePicker, SingleSelectField, TextField, TextArea
from tw.forms.validators import Int, DateConverter, TimeConverter
from tw.jquery import FlexiGrid

import sqlalchemy

from genshi import Markup
from os import path

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


interval = '30 min'
class Search_CDR(TableForm):
   name = 'search_form'
   submit_text = u'Valider...'
   fields = [
      Label(text = u'Sélectionnez un ou plusieurs critères'),
      TextField( 'number',
         attrs = {'size': 20, 'maxlength': 20},
         validator = Int(not_empty=False),
         label_text = u'Numéro'),
      SingleSelectField('in_out',
         label_text = u'Type',
         options = [ ('',u'Indifférent'), ('in',u'Entrant'), ('out',u'Sortant') ]),
      CalendarDatePicker('date',
                  date_format =  '%d/%m/%Y',
                  not_empty = False,
                  validator = DateConverter(month_style='dd/mm/yyyy'),
                  picker_shows_time = False ),
      TextField('hour',
         attrs = {'size': 5, 'maxlength': 5},
         validator = TimeConverter(),
         label_text = u'Heure +/- ' + interval),
      ]
search_form = Search_CDR('search_cdr_form', action='index2')

cdr_grid = FlexiGrid( id='flexi', fetchURL='fetch', title=None,
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

class Display_CDR:

   #allow_only = predicates.not_anonymous('NOT ANONYMOUS')
   paginate_limit = 25
   filtered_cdrs = None


   @expose(template="astportal2.templates.cdr")
   def index(self, **kw):

      cdrs = DBSession.query(CDR)

      #if not predicates.in_group('admin'):
      #   cdrs = cdrs.filter((CDR.src.like('%' + number + '%')) | (CDR.dst.like('%' + number + '%')))

      global filtered_cdrs
      filtered_cdrs = cdrs
      tmpl_context.form = search_form
      tmpl_context.grid = cdr_grid
      return dict( title=u'Journal des appels', debug='', values={})

   @validate(search_form, error_handler=index)
   @expose(template="astportal2.templates.cdr")
   def index2(self, number=None, in_out=None, date=None, hour=None):

      #if not predicates.in_group('admin'):
      #   cdrs = cdrs.filter((CDR.src.like('%' + number + '%')) | (CDR.dst.like('%' + number + '%')))

      filter = []
      cdrs = DBSession.query(CDR)
      if number:
         number = str(number)
         filter.append(u'numéro contient ' + number)
         cdrs = cdrs.filter((CDR.src.like('%' + number + '%')) | (CDR.dst.like('%' + number + '%')))

      if in_out=='in':
         filter.append(u'type entrant')
         cdrs = cdrs.filter(sqlalchemy.not_(CDR.lastdata.ilike('Dahdi/g0/%')))
      elif in_out=='out':
         filter.append(u'type sortant')
         cdrs = cdrs.filter(CDR.lastdata.ilike('Dahdi/g0/%'))

      if date:
         filter.append(date.strftime('date %d/%m/%Y'))
         cdrs = cdrs.filter(sqlalchemy.sql.cast(CDR.calldate, sqlalchemy.types.DATE)==date)

      if hour:
         hour = '%d:%02d' % (hour[0], hour[1])
         filter.append(u'heure approximative ' + hour)
         # XXX import datetime
         #time = datetime.time(h,m)
         #cdrs = cdrs.filter(sqlalchemy.sql.cast(CDR.calldate, sqlalchemy.types.TIME)==time)
         cdrs = cdrs.filter("'" + hour + "' - '" + interval + "'::interval <= calldate::time AND calldate::time <= '" + hour + "' + '" + interval + "'::interval")

      if len(filter):
         if len(filter)>1: m = u'Critères: '
         else: m = u'Critere: '
         flash( m + ', et '.join(filter) + '.')

      global filtered_cdrs
      filtered_cdrs = cdrs
      tmpl_context.form = search_form
      tmpl_context.grid = cdr_grid
      values = {'in_out': in_out, 'date': date, 'number': number, 'hour': hour}
      return dict( title=u'Journal des appels', debug='', values=values)


   @expose('json')
   def fetch(self, page=1, rp=25, sortname='calldate', sortorder='desc', qtype=None, query=None):

      #if not predicates.in_group('admin'):
      #   cdrs = cdrs.filter((CDR.src.like('%' + number + '%')) | (CDR.dst.like('%' + number + '%')))

      try:
         page = int(page)
         offset = (page-1) * int(rp)
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


   @expose()
   @allow_only(predicates.not_anonymous())
   def ecoute(self, date=None, file=None):

# XXX
#      if not predicates.in_group('TDM'):
#         flash(u'Accès interdit')
#         redirect('/')
#
#      if not path.exists(file): 
#         flash(u'Enregistrement introuvable: ' + file)
#         redirect('/cdr/')

      # Now really serve file
      import paste.fileapp
      f = paste.fileapp.FileApp('/usr/share/games/xmoto/Textures/Musics/speeditup.ogg',
            **{'Content-Disposition': 'attachment; filename=' + 'test.ogg'})
      from tg import use_wsgi_app
      return use_wsgi_app(f)

