# -*- coding: utf-8 -*-
# Call center stats controller

from tg import expose, flash, redirect, tmpl_context, validate, config
from tgext.menu import sidebar

from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import Form, TableForm, Label, CalendarDatePicker, Spacer, \
   SingleSelectField, MultipleSelectField, CheckBoxList, HiddenField
from tw.forms.validators import NotEmpty, Int, DateTimeConverter
from tw.jquery import FlotWidget

from genshi import Markup

from astportal2.model import DBSession, Queue_log, Queue_event, Phone
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.base import BaseController

from sqlalchemy import desc, func, sql, types, outerjoin, extract, and_

import datetime
import re
import logging
log = logging.getLogger(__name__)

re_month = re.compile(r'^(1?\d)-(\d\d\d\d)$')

def mk_filters(period, begin, end, queues, members):
   
   date_filter = None
   if not begin and not end:
      if period=='today':
          date_filter = sql.cast(Queue_log.timestamp, types.DATE)==\
             datetime.date.today()
      elif period=='yesterday':
         date_filter = sql.cast(Queue_log.timestamp, types.DATE)==\
            datetime.date.today() - datetime.timedelta(1)
      elif period=='ten_days':
         date_filter = (sql.cast(Queue_log.timestamp, types.DATE)).between(\
            datetime.date.today() - datetime.timedelta(10),
            datetime.date.today())
      elif re_month.search(period):
         (m,y) = re_month.search(period).groups()
         date_filter = and_(extract('year', Queue_log.timestamp)==y,
            extract('month', Queue_log.timestamp)==m)

   else:
      if begin and not end:
          date_filter = sql.cast(Queue_log.timestamp, types.DATE)>=\
             datetime.datetime.strptime(begin, '%d/%m/%Y').date()
      elif not begin and end:
          date_filter = sql.cast(Queue_log.timestamp, types.DATE)<=\
             datetime.datetime.strptime(end, '%d/%m/%Y').date()
      elif begin and end:
          date_filter = (sql.cast(Queue_log.timestamp, types.DATE)).between(\
             datetime.datetime.strptime(begin, '%d/%m/%Y').date(),
             datetime.datetime.strptime(end, '%d/%m/%Y').date())

   queue_filter = Queue_log.queue.in_(queues)
   member_filter = Queue_log.queue.in_(members)
   return date_filter, queue_filter, member_filter


def stat_global(page, rows, offset, sidx, sord, date_filter, queues_filter):
   # Global stats
   q = DBSession.query(Queue_log.queue, 
      func.count(Queue_log.queue).label('count')).\
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='ENTRANT').\
      filter(queues_filter).group_by(Queue_log.queue)

   if date_filter is not None:
      q = q.filter(date_filter)

   if sidx=='count':
      q = q.order_by(func.count(Queue_log.queue)) if sord=='asc' \
            else q.order_by(desc(func.count(Queue_log.queue)))
   else:
      q = q.order_by(Queue_log.queue) if sord=='asc' \
            else q.order_by(desc(Queue_log.queue))
   log.debug(q)

   q = q.offset(offset).limit(rows)
   total = q.count()/rows + 1
   data = [{ 'id'  : i, 
      'cell': (r.queue, r.count)
      } for i, r in enumerate(q.all())]

   return dict(page=page, total=total, rows=data)


def stat_queues(page, rows, offset, sidx, sord, date_filter, queues_filter):
   # Queues
#      enter = DBSession.query(Queue_log.queue.label('queue'), 
#            func.count('*').label('count')).\
#            filter(Queue_log.queue_event_id==Queue_event.qe_id).\
#            filter(Queue_event.event=='ENTERQUEUE').\
#            group_by(Queue_log.queue).subquery()

   abandon = DBSession.query(Queue_log.queue.label('queue'), 
         func.count('*').label('count')).\
         filter(Queue_log.queue_event_id==Queue_event.qe_id).\
         filter(Queue_event.event=='ABANDON')
   if date_filter is not None:
      abandon = abandon.filter(date_filter)
   abandon = abandon.filter(queues_filter).group_by(Queue_log.queue).subquery()

   connect = DBSession.query(Queue_log.queue.label('queue'), 
         func.count('*').label('count')).\
         filter(Queue_log.queue_event_id==Queue_event.qe_id).\
         filter(Queue_event.event=='CONNECT')
   if date_filter is not None:
      connect = connect.filter(date_filter)
   connect = connect.filter(queues_filter).group_by(Queue_log.queue).subquery()

   dissuasion = DBSession.query(Queue_log.queue.label('queue'), 
         func.count('*').label('count')).\
         filter(Queue_log.queue_event_id==Queue_event.qe_id).\
         filter(Queue_event.event=='DISSUASION')
   if date_filter is not None:
      dissuasion = dissuasion.filter(date_filter)
   dissuasion = dissuasion.filter(queues_filter).group_by(Queue_log.queue).subquery()

   closed = DBSession.query(Queue_log.queue.label('queue'), 
         func.count('*').label('count')).\
         filter(Queue_log.queue_event_id==Queue_event.qe_id).\
         filter(Queue_event.event=='FERME')
   if date_filter is not None:
      closed = closed.filter(date_filter)
   closed = closed.filter(queues_filter).group_by(Queue_log.queue).subquery()

   q = DBSession.query(Queue_log.queue.label('queue'), 
            func.count('*').label('enter'), 
            abandon.c.count.label('abandon'),
            connect.c.count.label('connect'), 
            dissuasion.c.count.label('dissuasion'), 
            closed.c.count.label('closed')).\
         filter(Queue_log.queue_event_id==Queue_event.qe_id).\
         filter(Queue_event.event=='ENTERQUEUE').\
         filter(queues_filter).\
         outerjoin((abandon, Queue_log.queue==abandon.c.queue)).\
         outerjoin((connect, Queue_log.queue==connect.c.queue)).\
         outerjoin((dissuasion, Queue_log.queue==dissuasion.c.queue)).\
         outerjoin((closed, Queue_log.queue==closed.c.queue)).\
         group_by(Queue_log.queue, abandon.c.count, connect.c.count, 
         dissuasion.c.count, closed.c.count)

   if date_filter is not None:
      q = q.filter(date_filter)

   if sidx=='name':
      q = q.order_by(Queue_log.queue) if sord=='asc' \
            else q.order_by(desc(Queue_log.queue))

   q = q.offset(offset).limit(rows)
   total = q.count()/rows + 1
   total_enter = total_connect = total_abandon = total_dissuasion = total_closed = 0
   data = []
   for i, r in enumerate(q.all()):
      data.append({ 'id'  : i, 'cell': (r.queue, r.enter, 
         r.connect, (100 * r.connect / r.enter) if r.connect else '',
         r.abandon, (100 * r.abandon / r.enter) if r.abandon else '', 
         r.dissuasion, (100 * r.dissuasion / r.enter) if r.dissuasion else '', 
         r.closed, (100 * r.closed / r.enter) if r.closed else '')})
      if r.enter: total_enter += r.enter 
      if r.connect: total_connect += r.connect
      if r.abandon: total_abandon += r.abandon
      if r.dissuasion: total_dissuasion += r.dissuasion
      if r.closed: total_closed += r.closed

   data.append({ 'id'  : i, 'cell': (u'Total', total_enter, 
      total_connect, 100 * total_connect / total_enter, 
      total_abandon, 100 * total_abandon / total_enter,
      total_dissuasion, 100 * total_dissuasion / total_enter, 
      total_closed, 100 * total_closed / total_enter)})

   return dict(page=page, total=total, rows=data)
   
def stat_sla(page, rows, offset, sidx, sord, date_filter, queues_filter, type):
   # Service Level, connect or abandon (count connect time / 30 s)
   o = sql.cast(Queue_log.data1 if type=='CONNECT' else Queue_log.data3,
         types.INT)/30
   q = DBSession.query(func.count('*').label('count'), 
         (o).label('qwait')).\
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event==type).\
      filter(queues_filter).\
      group_by(o).order_by(o)

   if date_filter is not None:
      q = q.filter(date_filter)
   
   q = q.offset(offset).limit(rows)
   total = q.count()/rows + 1

   data = []
   total_connect = 0
   for i, r in enumerate(q.all()):
      total_connect += r.count
      label = u'< %dm' % ((1+r.qwait)/2) if i%2 \
            else u'< %dm30s' % ((1+r.qwait)/2)
      data.append({ 'id'  : i, 'cell': [label, r.count, 0, 0]
      })

   sum_connect = 0.0
   for x in data:
      pc = 100.0 * x['cell'][1] / total_connect
      sum_connect += pc
      x['cell'][2] = '%.1f %%' % pc
      x['cell'][3] = '%.1f %%' % sum_connect

   return dict(page=page, total=total, rows=data)


def stat_daily(page, rows, offset, sidx, sord, date_filter, queues_filter):
   # Day of week distribution
   xd = (extract('dow', Queue_log.timestamp)).label('dow')
   q = DBSession.query(xd, (func.count('*')).label('count')).\
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='CONNECT').\
      filter(queues_filter).\
      group_by(xd).order_by(xd)

   if date_filter is not None:
      q = q.filter(date_filter)
   
   q = q.offset(offset).limit(rows)
   total = q.count()/rows + 1

   dow = [ u'dimanche', u'lundi', u'mardi', u'mercredi', 
         u'jeudi', u'vendredi', u'samedi']
   data = []
   total_connect = 0
   for i, r in enumerate(q.all()):
      total_connect += r.count
      data.append({ 'id'  : i, 'cell': [dow[int(r.dow)], r.count, 0]
      })

   for x in data:
      pc = 100.0 * x['cell'][1] / total_connect
      x['cell'][2] = '%.1f %%' % pc

   return dict(page=page, total=total, rows=data)


def stat_hourly(page, rows, offset, sidx, sord, date_filter, queues_filter):
   # Hourly distribution (30 min sections)
   xh = (func.floor((extract('hour', Queue_log.timestamp) * 60 + \
         extract('min', Queue_log.timestamp) ) / 30)).label('xhour')

   h_entrant = DBSession.query(xh, func.count('*').label('entrant')).\
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='ENTRANT').filter(queues_filter)
   if date_filter is not None:
      h_entrant = h_entrant.filter(date_filter)
   h_entrant = h_entrant.group_by(xh).order_by(xh).subquery()

   h_connect = DBSession.query(xh, func.count('*').label('connect')).\
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='CONNECT').filter(queues_filter)
   if date_filter is not None:
      h_connect = h_connect.filter(date_filter)
   h_connect = h_connect.group_by(xh).order_by(xh).subquery()

   h_abandon = DBSession.query(xh, func.count('*').label('abandon')).\
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='ABANDON').filter(queues_filter)
   if date_filter is not None:
      h_abandon = h_abandon.filter(date_filter)
   h_abandon = h_abandon.group_by(xh).order_by(xh).subquery()

   h_closed = DBSession.query(xh, func.count('*').label('closed')).\
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='FERME').filter(queues_filter)
   if date_filter is not None:
      h_closed = h_closed.filter(date_filter)
   h_closed = h_closed.group_by(xh).order_by(xh).subquery()

   h_dissuasion = DBSession.query(xh, func.count('*').label('dissuasion')).\
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='DISSUASION').filter(queues_filter)
   if date_filter is not None:
      h_dissuasion = h_dissuasion.filter(date_filter)
   h_dissuasion = h_dissuasion.group_by(xh).order_by(xh).subquery()

   q = q.offset(offset).limit(rows)
   total = q.count()/rows + 1
   data = []

   return dict(page=page, total=total, rows=data)


def stat_agents(page, rows, offset, sidx, sord, date_filter, queues_filter):
   # Agents stats

   # Service
   service = DBSession.query(Queue_log.timestamp, Queue_log.channel, Queue_event.event).\
         filter(Queue_log.queue_event_id==Queue_event.qe_id).\
         filter(Queue_event.event.in_(('ADDMEMBER', 'REMOVEMEMBER'))).\
         order_by(Queue_log.channel, desc(Queue_log.timestamp))

   # Pause
   pause = DBSession.query(Queue_log.timestamp, Queue_log.channel, Queue_event.event).\
         filter(Queue_log.queue_event_id==Queue_event.qe_id).\
         filter(Queue_event.event.in_(('PAUSE','UNPAUSE'))).\
         order_by(Queue_log.channel, desc(Queue_log.timestamp))

   # Calls received per agents
   calls = DBSession.query(Queue_log.channel, 
         func.count(Queue_log.channel), 
         func.avg(sql.cast(Queue_log.data2, types.INT)),
         func.sum(sql.cast(Queue_log.data2, types.INT))).\
            filter(Queue_log.queue_event_id==Queue_event.qe_id).\
            filter(Queue_event.event.in_(('COMPLETECALLER', 'COMPLETEAGENT'))).\
            group_by(Queue_log.channel)

   q = q.offset(offset).limit(rows)
   total = q.count()/rows + 1
   data = []

   return dict(page=page, total=total, rows=data)


def period_options():
   ''' Returns date options
   '''
   m = [ u'Janvier', u'Février', u'Mars', u'Avril', u'Mai', u'Juin', 
      u'Juillet', u'Août', u'Septembre', u'Octobre', u'Novembre', u'Décembre' ]
   p = [ ('NONE', u' - - - - - - '),
         ('today', u"Aujourd'hui"),
         ('yesterday', u'Hier'),
         ('ten_days', u'10 derniers jours'),
         ]
   today = datetime.date.today()
   for i in range(0,13):
      j = today.month-i-1
      if j<0:
         y = today.year-1
         j += 12
      else:
         y = today.year
      p.append( ( '%d-%d' % (j+1,y), m[j] + ' ' + str(y)) )

   return p

def queues_options():
   ''' Returns distinct queues from queue log
   '''
   # queue_event_id==24 => AddMember
   return [q[0] for q in DBSession.query(Queue_log.queue).distinct().\
         filter(Queue_log.queue_event_id==24).order_by(Queue_log.queue)]

def agents_options():
   ''' Returns distinct agents from queue log
   '''
   # queue_event_id==24 => AddMember
   return [a[0] for a in DBSession.query(Queue_log.channel).distinct().\
         filter(Queue_log.queue_event_id==24).order_by(Queue_log.channel)]

class Stats_form(TableForm):
   ''' Stats form
   '''
   fields = [
      Label(text= u'1. Sélectionnez une période ou les dates de début et de fin'),
      SingleSelectField('period',
         label_text = u'Période',
         default = 'ten_days', # period or 'ten_days',
         options = period_options),
      CalendarDatePicker('begin',
         attrs = {'readonly': True, 'size': 8},
         date_format = '%d/%m/%Y',
         validator = DateTimeConverter(format="%d/%m/%Y"),
         default = '', # begin or '',
         label_text=u'Date début',
         button_text=u'Choisir...'),
      CalendarDatePicker('end',
         attrs = {'readonly': True, 'size': 8},
         default = '', # end or '',
         date_format = '%d/%m/%Y',
         calendar_lang = 'fr',
         validator = DateTimeConverter(format="%d/%m/%Y"),
         label_text=u'Date fin',
         button_text=u'Choisir...'),
      Spacer(),
      Label( text = u'2. Sélectionnez un ou plusieurs groupes d\'appels'),
      CheckBoxList(
         name = 'queues',
         label_text = u'Groupes d\'appels',
         options = queues_options,
         default = queues_options, #q_checked, #queue_select or q_checked,
         validator = NotEmpty()
         ),
      Spacer(),
      Label( text = u'3. Sélectionnez un ou plusieurs agents'),
      MultipleSelectField(
         name = 'members',
         label_text = u'Agents',
         options = agents_options,
         default = agents_options,
         validator = NotEmpty(),
         ),
      Spacer(),
      Label( text = u'4. Sélectionnez la statistique à afficher'),
      SingleSelectField('stat',
         label_text = u'Statistique',
         options = [('global', u'Globale'), 
            ('queues', u'Appels par groupe'), ('sla', u'Niveau de service'),
            ('abandon', u'Abandons'), ('daily', u'Distribution quotidienne'),
            ('hourly', u'Distribution horaire'), ('agents', u'Service par agent'),
            ]),
   ]
   submit_text = u'Valider...'
   hover_help = True
   action = 'do_stat'
stats_form = Stats_form('stats_form')


def row(p, callgroups, pickupgroups):
   '''Displays a formatted row of the pickups list
   Parameter: Pickup object
   '''

   html =  u'<a href="'+ str(p.pickup_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'

   return [Markup(html), p.name, p.comment, ', '.join(callgroups), 
         ', '.join(pickupgroups) ]


class CC_Stats_ctrl(BaseController):
   
#   allow_only = in_group('admin', 
#         msg=u'Vous devez appartenir au groupe "admin" pour gérer les services')

   @sidebar(u'-- Groupes d\'appels || Statistiques',
      icon = '/images/kdf.png', sortorder = 20)
   @expose(template='astportal2.templates.form_new')
   def index(self):
      ''' Display Stats form
      '''
      tmpl_context.form = stats_form
      return dict( title=u'Statistiques des groupes d\'appels', debug='', values='')


   @expose(template='astportal2.templates.cc_stats')
   def do_stat(self, period, begin, end, queues=None, members=None, stat=None):


      if type(queues) != type([]):
         queues = (queues)
      queue_filter = Queue_log.queue.in_(queues)

      if type(members) != type([]):
         members = (members)
      member_filter = Queue_log.channel.in_(members)

# Dynamic template
#tg.decorators.override_template(controller, "genshi:myproject.templates.index2")

      if stat=='global':
         row_list = (10, 25)
         caption = flot_label = u'Appels reçus par groupe'
         sortname = 'name'
         sortorder = 'asc'
         colnames = [u'Groupe d\'appels', u'Nombre d\'appels reçus']
         colmodel = [
            { 'name': 'name', 'width': 60, 'sortable': True},
            { 'name': 'count', 'width': 60, 'align': 'right', 'sortable': True},
         ]
         tmpl_context.flot_series = '"0,1"' # List of series to plot
         title = u'Statistiques globales'

      elif stat=='queues':
         row_list = (10, 25)
         caption = flot_label = u'Appels par groupe'
         sortname = 'name'
         sortorder = 'asc'
         colnames = [u'Groupe d\'appels', u'Appels reçus', u'Traités', u'%',
               u'Abandons', u'%', u'Dissuasions', u'%', u'Fermé', u'%']
         colmodel = [
            { 'name': 'name', 'width': 60, 'sortable': True},
            { 'name': 'incoming', 'width': 40, 'align': 'right', 'sortable': True},
            { 'name': 'received', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
            { 'name': 'abandon', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
            { 'name': 'dissuasion', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
            { 'name': 'closed', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
         ]
         tmpl_context.flot_series = '"0,1,3,5,7"' # List of series to plot
         title = u'Statistiques par groupes d\'appels'

      elif stat in ('sla','abandon'):
         row_list = (30,120)
         caption = flot_label = u'Niveau de service'
         sortname = 'wait'
         sortorder = 'asc'
         colnames = [u'Attente', u'Appels', u'%', u'Cumul (%)']
         colmodel = [
            { 'name': 'wait', 'width': 60, 'sortable': True},
            { 'name': 'count', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
            { 'width': 20, 'align': 'right', 'sortable': False},
         ]
         tmpl_context.flot_series = '"0,"' # List of series to plot
         if stat=='sla':
            title = u'Niveau de service'
         else:
            title = u'Abandons'

      elif stat=='daily':
         row_list = (30,120)
         caption = flot_label = u'Niveau de service'
         sortname = 'wait'
         sortorder = 'asc'
         colnames = [u'Jour de la semaine', u'Appels', u'%']
         colmodel = [
            { 'name': 'dow', 'width': 60, 'sortable': True},
            { 'name': 'count', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
         ]
         tmpl_context.flot_series = '"0,"' # List of series to plot
         title = u'Distribution quotidienne'

      elif stat=='hourly':
         row_list = (48,)
         caption = flot_label = u'Niveau de service'
         sortname = 'wait'
         sortorder = 'asc'
         colnames = [u'Heure', u'Entrant', u'%', u'Fermé', u'%',
               u'Dissuasion', u'%', u'Abandons', u'%', u'Traités', u'%']
         colmodel = [
            { 'name': 'hour', 'width': 60, 'sortable': True},
            { 'name': 'incoming', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
            { 'name': 'closed', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
            { 'name': 'dissuasion', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
            { 'name': 'abandon', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
            { 'name': 'connect', 'width': 40, 'align': 'right', 'sortable': True},
            { 'width': 20, 'align': 'right', 'sortable': False},
         ]
         tmpl_context.flot_series = '"0,"' # List of series to plot
         title = u'Distribution quotidienne'

      elif stat=='agents':
         q = queues

      # Hidden form for CSV export
      tmpl_context.form = Form(
         name = 'stats_form',
         submit_text = None,
         hover_help = True,
         fields = [
            HiddenField(name='param',default='XXX'),
         ]
      )

      # Data grid
      tmpl_context.data_grid = MyJqGrid( id='data_grid', 
         url='fetch', caption=caption,
         sortname=sortname, sortorder=sortorder,
         colNames = colnames, colModel = colmodel,
         navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': False, 'refresh': True, 
               },
         loadComplete = js_callback('load_complete'),
         rowNum = row_list[0],
         rowList = row_list,
         postData = {'period': period, 'begin': begin, 'end': end,
            'queues': queues, 'members': members, 'stat': stat},
      )

      # Plot: data are gathered from the grid, through javscript, cf. cc_stats.html
      tmpl_context.data_flot = FlotWidget(
            data = [
               { 'data': [],
               'label': u'' },
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

      log.debug('''
period=%s, begin=%s, end=%s
queues=%s
members=%s
stat=%s
''' % (period, begin, end, queues, members, stat))

      return dict( title=title , debug='', values='')


   @expose('json')
   def fetch(self, page, rows, sidx, sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None,
          period=None, begin=None, end=None, stat='global', **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''
#      if not in_any_group('admin','SVI'):
#         flash(u'Accès interdit !', 'error')
#         redirect('/')

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * rows
      except:
         page = 1
         rows = 24
         offset = 0

      date_filter, queues_filter, members_filter = mk_filters(period, begin, end,
         kw['queues[]'] if 'queues[]' in kw.keys() else (kw['queues']),
         kw['members[]'] if 'members[]' in kw.keys() else (kw['members']) )

      log.info('fetch_global : page=%d, rows=%d, offset=%d, sidx=%s, sord=%s' % (
         page, rows, offset, sidx, sord))

      if stat=='global':
         return stat_global(page, rows, offset, sidx, sord, 
               date_filter, queues_filter)

      elif stat=='queues':
         return stat_queues(page, rows, offset, sidx, sord, 
               date_filter, queues_filter)

      elif stat=='sla':
         return stat_sla(page, rows, offset, sidx, sord, 
               date_filter, queues_filter, 'CONNECT')

      elif stat=='abandon':
         return stat_sla(page, rows, offset, sidx, sord, 
               date_filter, queues_filter, 'ABANDON')

      elif stat=='daily':
         return stat_daily(page, rows, offset, sidx, sord, 
               date_filter, queues_filter)

      elif stat=='hourly':
         return stat_hourly(page, rows, offset, sidx, sord, 
               date_filter, queues_filter)

