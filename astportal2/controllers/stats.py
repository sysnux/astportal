# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context, validate, response
from tgext.menu import sidebar

try:
   from tg.predicates import not_anonymous, in_group, in_any_group
except ImportError:
   from repoze.what.predicates import not_anonymous, in_group, in_any_group

from tw.api import js_callback
from tw.jquery import FlexiGrid, FlotWidget
from tw.forms import Form, HiddenField
from tw.forms.validators import Int

from sqlalchemy import func, desc, text, cast, TIME

from astportal2.model import DBSession, CDR, User
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.base import BaseController

from genshi import Markup

import datetime
from calendar import monthrange
import logging
log = logging.getLogger(__name__)

db_engine = DBSession.connection().engine.name

# Pour affichage titres
month_name = [u'janvier', u'février', u'mars', u'avril', u'mai', u'juin',
   u'juillet', u'août', u'septembre', u'octobre', u'novembre', u'décembre']

def hms(sec):
   h, x = divmod(sec, 3600)
   m, s = divmod(x, 60)
   return '%d h %d m %d s' % (h, m, s)


# Formattage ligne grid, avec éventuellement lien sur la première colonne
def cell(type,i,c):
   if type:
      date = c[0].strftime('%d')
   else:
      date = Markup(u'<a href="#" onclick="daily(\'%s\');" title="Statistiques quotidiennes">%s</a>' % (c[0].strftime('%m/01/%Y'),  c[0].strftime('%m/%Y')))
   return date, c[1], hms(c[2])


class Stats_ctrl(BaseController):

   allow_only = not_anonymous(msg=u'Veuiller vous connecter pour continuer')

   stats_type = None
   stats_req = None

   @sidebar(u"-- Administration || Statistiques globales", sortorder=19,
      icon = '/images/office-chart-area-stacked.png',
      permission = in_any_group('admin', 'STATS'))
   @expose(template="astportal2.templates.stats")
   def index(self, selected=None, daily=None):

      if not in_any_group('admin','STATS'):
         flash(u'Accès interdit !', 'error')
         redirect('/')
      
      if daily:
         log.info('stats_type <- %s' % daily)
         self.stats_type = daily
         (m,d,y) = daily.split('/')
         title = u'Statistiques quotidiennes de %s %s' % (month_name[int(m)-1], y)
         flot_label = u'Appels quotidiens (%s %s)' % (month_name[int(m)-1], y)
         last_day = monthrange(int(y),int(m))[1]
         row_list = [last_day, 15, 10, 5]

      else:
         self.stats_type = None
         title = u'Statistiques mensuelles'
         flot_label = u'Appels mensuels'
         row_list = [12, 18, 24, 30, 36, 48, 60, 120]

      # Data grid
      tmpl_context.data_grid = MyJqGrid( id='data_grid', 
         url='/stats/fetch', caption=u"Valeurs",
         sortname='name', sortorder='desc',
         colNames = [u'Jour' if daily else u'Mois', u'Appels', u'Durée'],
         colModel = [
            { 'name': 'date', 'width': 60, 'sortable': True},
            { 'name': 'calls', 'width': 40, 'align': 'right', 'sortable': True},
            { 'name': 'billsec', 'width': 40, 'align': 'right', 'sortable': True}
               ],
         navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': False, 'refresh': True, 
               },
         loadComplete = js_callback('load_complete'),
         rowNum = row_list[0],
         rowList = row_list,
      )

      # Hidden form for daily stats
      tmpl_context.form = Form(
         name = 'stats_form',
         submit_text = None,
         hover_help = True,
         fields = [
            HiddenField(name='daily',default=self.stats_type),
         ]
      )

      log.info('stats_type -> %s' % self.stats_type)

      # Plot: data are gathered from the grid, through javscript, cf. stats.html
      tmpl_context.data_flot = FlotWidget(
            data = [
               { 'data': [],
               'label': u'Appels mensuels' },
            ],
            options = {
               'grid': { 'backgroundColor': '#fffaff',
               'clickable': True,
               'hoverable': True},
               'xaxis': { 'ticks': []}
               },
            height = '300px',
            width = '600px',
            label = flot_label,
            id='data_flot'
            )

      # Hourly grid
      tmpl_context.hourly_grid = MyJqGrid( id='hourly_grid', 
         url='/stats/fetch_hourly', caption=u'Valeurs horaires',
         sortname='name', sortorder='desc',
         colNames = [u'Tranche horaire', u'Appels', u'Durée'],
         colModel = [
            { 'name': 'date', 'width': 60, 'sortable': False},
            { 'name': 'calls', 'width': 40, 'align': 'right', 'sortable': False},
            { 'name': 'billsec', 'width': 40, 'align': 'right', 'sortable': False}
               ],
         navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': False, 'refresh': True, 
               },
         loadComplete = js_callback('load_hourly_complete'),
         rowNum = 24,
         rowList = [12,24],
      )

      # Plot: data are gathered from the grid, through javscript, cf. stats.html
      tmpl_context.hourly_flot = FlotWidget(
            data = [
               { 'data': [],
               'label': u'Distribution horaire' },
            ],
            options = {
               'grid': { 'backgroundColor': '#fffaff',
               'clickable': True,
               'hoverable': True},
               'xaxis': { 'ticks': []}
               },
            height = '300px',
            width = '600px',
            label = flot_label,
            id='hourly_flot'
            )

      # Inject javascript for tabs
      from tw.jquery.ui import ui_tabs_js
      ui_tabs_js.inject()

      return dict( title=title, debug=False, values={})


   @expose('json')
   def fetch(self, page, rows, sidx, sord='desc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''
      if not in_any_group('admin','STATS'):
         flash(u'Accès interdit !', 'error')
         redirect('/')
 
      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * rows
      except:
         page = 1
         rows = 12
         offset = 0

      log.info('fetch : page=%d, rows=%d, offset=%d' % (page, rows, offset))

      if self.stats_type:
         # Daily stats
         d = datetime.datetime.strptime(self.stats_type, '%m/%d/%Y')
         if db_engine=='oracle':
            req = func.trunc(CDR.calldate, 'J')
         else: # PostgreSql
            req = func.date_trunc('day', CDR.calldate)
         cdrs = DBSession.query(req, func.count(req), func.sum(CDR.billsec))
         if db_engine=='oracle':
            cdrs = cdrs.filter(func.trunc(CDR.calldate, 'month') == \
               func.trunc(d, 'month'))
         else: # PostgreSql
            cdrs = cdrs.filter(func.date_trunc('month', CDR.calldate) == \
               func.date_trunc('month', d))
         cdrs = cdrs.group_by(req)

      else:
         # Monthly stats
         if db_engine=='oracle':
            req = func.trunc(CDR.calldate, 'month')
         else: # PostgreSql
            req = func.date_trunc('month', CDR.calldate)
         cdrs = DBSession.query(req, func.count(req), func.sum(CDR.billsec))
         cdrs = cdrs.group_by(req)

      self.stats_req = cdrs

      if sidx=='calls':
         cdrs = cdrs.order_by(getattr(func.count(req),sord)())
      elif sidx=='billsec':
         cdrs = cdrs.order_by(getattr(func.sum(CDR.billsec),sord)())
      else:
         cdrs = cdrs.order_by(getattr(req,sord)())

      cdrs = cdrs.offset(offset).limit(rows)
      total = cdrs.count()/rows + 1
      data = [{ 'id'  : i, 
         'cell': cell(self.stats_type, i, c)
         } for i, c in enumerate(cdrs.all()) ]

      return dict(page=page, total=total, rows=data)


   @expose('json')
   def fetch_hourly(self, page, rows, sidx, sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''
      if not in_any_group('admin','STATS'):
         return dict(page=0, total=0, rows=[])
 
      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * rows
      except:
         page = 1
         rows = 24
         offset = 0

      log.info('fetch_hourly : page=%d, rows=%d, offset=%d, sidx=%s, sord=%s' % (
         page, rows, offset, sidx, sord))

      # Initialize data, in case no data is available for that time slice
      data = [{'id': x, 'cell': ['%d h 00 < %d h 00' % (x, x+1), 0, None]}
         for x in range(24)]

      # Count calls by hour
      if db_engine=='oracle':
         req = func.to_char(CDR.calldate, 'HH24')
      else: # PostgreSql
         req = func.date_trunc('hour', cast(CDR.calldate, TIME))
      cdrs = DBSession.query(req, func.count(req), func.sum(CDR.billsec))
      if self.stats_type:
         # Monthly stats
         d = datetime.datetime.strptime(self.stats_type, '%m/%d/%Y')
         if db_engine=='oracle':
            cdrs = cdrs.filter(func.trunc(CDR.calldate, 'month') == \
               func.trunc(d, 'month'))
         else: # PostgreSql
            cdrs = cdrs.filter(func.date_trunc('month', CDR.calldate) == \
               func.date_trunc('month', d))
      cdrs = cdrs.group_by(req)
#      cdrs = cdrs.order_by(func.sum(CDR.billsec))

      for i, c in enumerate(cdrs):
         if db_engine=='oracle':
            j = int(c[0])
         else: # PostgreSql
            j = c[0].seconds / 3600
         data[j] =  {'id': j, 'cell': ['%d h 00 < %d h 00' % (j,j+1), c[1], hms(c[2])]}

      return dict(page=page, total=24, rows=data[offset:offset+page*rows])

   @expose()
   def csv(self, **kw):

      if not in_any_group('admin', 'STATS'):
         flash(u'Accès interdit')
         redirect('/')

      today = datetime.datetime.today()
      filename = 'statistiques-' + today.strftime('%Y%m%d') + '.csv'
      import StringIO
      import csv
      csvdata = StringIO.StringIO()
      writer = csv.writer(csvdata)

      # Global headers
      if self.stats_type:
         rt = 'quotidien ' + self.stats_type[0:2] + self.stats_type[5:]
         col1 = 'Jour' 
      else: 
         rt = 'mensuel'
         col1 = 'Mois'
      writer.writerow(['Statistiques SVI'])
      writer.writerow(['Date', today.strftime('%d/%m/%Y')])
      writer.writerow(['Type de rapport', rt])
      writer.writerow([])
      cols = [col1]

      if self.stats_type:
         # Daily stats
         d = datetime.datetime.strptime(self.stats_type, '%m/%d/%Y')
         if db_engine=='oracle':
            req = func.trunc(CDR.calldate, 'J')
         else: # PostgreSql
            req = func.date_trunc('day', CDR.calldate)

      else:
         # Monthly stats
         if db_engine=='oracle':
            req = func.trunc(CDR.calldate, 'month')
         else: # PostgreSql
            req = func.date_trunc('month', CDR.calldate)

      # Order by date
      cdrs = self.stats_req
      cdrs = cdrs.order_by(req)

      cols.append( (u'Appels\n(nombre)').encode('utf-8') )
      cols.append( (u'Appels\n(durée)').encode('utf-8') )
      writer.writerow(cols)

      for c in cdrs.all():
         row = []
         if self.stats_type:
            row.append(c[0].strftime('%d'))
         else:
            row.append(c[0].strftime('%m/%Y'))
         row.append(c[1])
         row.append(hms(c[2]))
         writer.writerow(row)

      rh = response.headers
      rh['Content-Type'] = 'text/csv; charset=utf-8'
      rh['Content-disposition'] = 'attachment; filename="%s"' % filename
      rh['Pragma'] = 'public' # for IE
      rh['Cache-control'] = 'max-age=0' #for IE

      return csvdata.getvalue()

