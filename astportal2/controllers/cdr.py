# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config, session
from tg.controllers import WSGIAppController
from tgext.menu import sidebar
import paste.fileapp
#from tg.decorators import allow_only
from repoze.what.predicates import not_anonymous, in_group, in_any_group

from astportal2.model import DBSession, CDR, Phone
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.base import BaseController

import logging
log = logging.getLogger(__name__)

from tw.api import WidgetsList
from tw.api import js_callback
from tw.forms import TableForm, HiddenField, Label, CalendarDatePicker, SingleSelectField, TextField, TextArea
from tw.forms.validators import Int, DateConverter, TimeConverter
from tw.jquery.ui import ui_tabs_js

import sqlalchemy
db_engine = DBSession.connection().engine.name

from genshi import Markup
from os import path

dir_monitor = config.get('directory.monitor')
try:
   hide_numbers = False if config.get('hide_numbers').lower()=='false' else True
except:
   hide_numbers = True

import re
re_sip = re.compile('^SIP/poste\d-.*')
prefix_src = config.get('prefix.src')

def rec_link(row):
   '''Create link to download recording if file exists'''
   if row.disposition != 'ANSWERED':
      return ''

   dir = dir_monitor + row.calldate.strftime('%Y/%m/%d/')
   ts = row.calldate.strftime('-%Y%m%d-%H%M%S')

   if re_sip.search(row.channel):
      if len(dst)>4: dst = dst[1:]
      file1 = 'out-' + row.channel[4:10] + '-' + row.dst + '-' + row.uniqueid + '.wav'
      file2 = 'out-' + row.channel[4:10] + '-' + row.dst + ts +'.wav'
   elif row.dstchannel and re_sip.search(row.dstchannel):
      file1 = 'in-' + row.dstchannel[4:10] + '-' + row.src + '-' + row.uniqueid + '.wav'
      file2 = 'in-' + row.dstchannel[4:10] + '-' + row.src + ts + '.wav'
   else:
      file1 = file2 = None
#XXX      return '' 

   if file1 and path.exists(dir + file1): 
      file = file1
   elif file2 and path.exists(dir + file2):
      file = file2
   else:
      file = None
#XXX      return ''

   file = dir + 'XXX'
   link = Markup('<a href="#" title="&Eacute;coute" onclick="ecoute(\'' + file + '\')"><img src="/images/sound_section.png" border="0" alt="&Eacute;coute" /></a>')
   return link


def check_access():
   '''Check access rights / group: admin=full access, boss=users from same department, user.
   Returns SA Query object for selected CDRs
   '''

   if in_any_group('admin', 'APPELS'):
      cdrs = DBSession.query(CDR)

   elif in_group('CDS'):
      # Find list of phones from the user's list of phones
      # user_phones -> departments -> phones
      phones = []
      for p in request.identity['user'].phone:
         log.info('CDS phone %s -> department %s' % (p, p.department))
      for d in [d.department for d in request.identity['user'].phone]:
         log.info('CDS department <%s>' % (d))
         for p in d.phones:
            phones.append(p)
      src = [prefix_src + p.exten for p in phones]
      dst = [p.exten for p in phones]
      cdrs = DBSession.query(CDR).filter( (CDR.src.in_(src)) | (CDR.dst.in_(dst)) )
      log.info('CDS phone <%s> -> source <%s>, destination <%s>' % (
         request.identity['user'].phone, src, dst))


   elif in_group('utilisateurs'):
      src = [prefix_src + p.exten for p in request.identity['user'].phone]
      dst = [p.exten for p in request.identity['user'].phone]
      cdrs = DBSession.query(CDR).filter( (CDR.src.in_(src)) | (CDR.dst.in_(dst)) )

   else:
      flash(u'Accès interdit')
      redirect('/')

   return cdrs


def f_bill(billsec):
   '''Formatted billing'''
   if billsec is not None:
      h = billsec/3600
      s = billsec-3600*h
      m = s/60
      s = s%60
   else:
      h = m = s = 0
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
         attrs = {'readonly': True, 'size': 8},
         default = '', # end or '',
         date_format = '%d/%m/%Y',
         calendar_lang = 'fr',
         label_text=u'Date',
         button_text=u'Choisir...',
         not_empty = False,
         validator = DateConverter(month_style='dd/mm/yyyy'),
         picker_shows_time = False ),
      TextField('hour',
         attrs = {'size': 5, 'maxlength': 5},
         validator = TimeConverter(),
         label_text = u'Heure +/- ' + interval),
      ]
search_form = Search_CDR('search_cdr_form', action='index2')


cdr_grid = MyJqGrid(
   caption = u'Appels',
   id = 'grid',
   url = 'fetch',
   colNames = [u'Date / heure', u'Source', u'Destination', u'\u00C9tat', u'Durée'], #, u'\u00C9coute'],
   colModel = [
      { 'name': 'calldate', 'width': 100 },
      { 'name': 'src', 'width': 70 },
      { 'name': 'dst', 'width': 70 },
      { 'name': 'disposition', 'width': 80 },
      { 'name': 'billsec', 'width': 40 },
#      { 'sortable': False, 'search': False, 'width': 40, 'align':'center' },
      ],
   sortname = 'calldate',
   sortorder = 'desc',
   )

class Display_CDR(BaseController):

   allow_only = not_anonymous(msg=u'Veuiller vous connecter pour continuer')
   paginate_limit = 25
   filtered_cdrs = None


   @sidebar(u'Journal des appels',  sortorder = 3,
         icon = '/images/databases_section.png')
   @expose(template="astportal2.templates.cdr")
   def index(self, **kw):

      global filtered_cdrs
      filtered_cdrs =  check_access()
      tmpl_context.form = search_form
      tmpl_context.grid = cdr_grid
      return dict( title=u'Journal des appels', debug='', values={})


   @validate(search_form, error_handler=index)
   @expose(template="astportal2.templates.cdr")
   def index2(self, number=None, in_out=None, date=None, hour=None):

      cdrs = check_access()
      filter = []
      if number:
         number = str(number)
         filter.append(u'numéro contient ' + number)
         cdrs = cdrs.filter((CDR.src.like('%' + number + '%')) | (CDR.dst.like('%' + number + '%')))

      if in_out=='in':
         filter.append(u'type entrant')
#cdrs = cdrs.filter('''NOT (dstchannel ~ E'Dahdi/1?\\\\d-1' OR dstchannel LIKE 'IAX2/teliax%')''')
#cdrs = cdrs.filter(sqlalchemy.not_(CDR.lastdata.ilike('Dahdi/g0/%')))
         cdrs = cdrs.filter(CDR.channel.ilike('SIP/TOICSB%'))

      elif in_out=='out':
         filter.append(u'type sortant')
#cdrs = cdrs.filter(''' (dstchannel ~ E'Dahdi/1?\\\\d-1' OR dstchannel LIKE 'IAX2/teliax%')''')
#cdrs = cdrs.filter(CDR.lastdata.ilike('Dahdi/g0/%'))
         cdrs = cdrs.filter(CDR.dstchannel.ilike('SIP/TOICSB%'))

      if date:
         filter.append(date.strftime('date %d/%m/%Y'))
         if db_engine=='oracle':
            cdrs = cdrs.filter(sqlalchemy.func.trunc(CDR.calldate, 'J')==date)
         else: # PostgreSql
            cdrs = cdrs.filter(sqlalchemy.sql.cast(CDR.calldate, sqlalchemy.types.DATE)==date)


      if hour:
         filter.append(u'heure approximative %dh%02d' % (hour[0], hour[1]))
         if db_engine=='oracle':
            if hour[1]>=30: 
               hour1 = '%02d:%02d' % (hour[0], hour[1]-30)
               hour2 = '%02d:%02d' % (hour[0]+1, hour[1]-30)
            else:
               hour1 = '%02d:%02d' % (hour[0]-1, hour[1]+30)
               hour2 = '%02d:%02d' % (hour[0], hour[1]+30)
            cdrs = cdrs.filter(hour1<=sqlalchemy.func.to_char(CDR.calldate, 'HH24:MI'))
            cdrs = cdrs.filter(sqlalchemy.func.to_char(CDR.calldate, 'HH24:MI')<=hour2)
         else: # PostgreSql
            hour = '%d:%02d' % (hour[0], hour[1])
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

      # Use tabs
      ui_tabs_js.inject()

      return dict( title=u'Journal des appels', debug='', values=values)


   @expose('json')
   def fetch(self, rows, page=1, sidx='calldate', sord='desc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Called by Grid JavaScript component
      '''

      if not in_any_group('admin', 'APPELS', 'CDS', 'utilisateurs'):
         flash(u'Accès interdit')
         redirect('/')

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
         offset = (page-1) * rows
      except:
         offset = 0
         page = 1

      global filtered_cdrs
      cdrs = filtered_cdrs
      total = cdrs.count()/rows + 1
      column = getattr(CDR, sidx)
      cdrs = cdrs.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      data = []
      for cdr in cdrs.all():
         src = cdr.src
         if src and in_any_group('admin', 'APPELS', 'CDS') and hide_numbers:
            src = src[:-3] + '***'
         dst = cdr.dst
         if dst and in_any_group('admin', 'APPELS', 'CDS') and hide_numbers: 
            dst = cdr.dst[:-3] + '***'
         data.append({
            'id'  : cdr.acctid,
            'cell': [
               cdr.calldate, src, dst,
               f_disp(cdr.disposition),
               f_bill(cdr.billsec), rec_link(cdr)
            ]
         })

      return dict(page=page, total=total, rows=data)


   @expose()
   def ecoute(self, date=None, file=None):
      ''' Send recorded file
      '''

      filename = 'test.ogg'
      rec = '/usr/share/games/xmoto/Textures/Musics/speeditup.ogg' # XXX
      f = paste.fileapp.FileApp(rec,
            **{'Content-Type': 'audio/ogg',
            'Content-Disposition': 'attachment; filename=' + filename})

      return WSGIAppController(f)._default()

