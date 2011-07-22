# -*- coding: utf-8 -*-
# Call center stats controller

from tg import expose, flash, redirect, tmpl_context, validate, config, response
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

import StringIO
import csv
import datetime
import re
import logging
log = logging.getLogger(__name__)


def td_hms(td):
   ''' timedelta to hour:min:sec 
   '''
   if td is None:
      return ''
   h, x = divmod(td.seconds, 3600)
   m, s = divmod(x, 60)
   h += 24 * td.days
   if h>0:
      return '%dh%02dm%02d' % (h,m,s)
   else:
      return '%dm%02d' % (m,s)


def mk_filters(period, begin, end, queues, members):
   
   date_filter = None
   re_month = re.compile(r'^(1?\d)-(\d\d\d\d)$')
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

   queues_filter = Queue_log.queue.in_(queues)
   members_filter = Queue_log.channel.in_(members)
   return date_filter, queues_filter, members_filter


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

   log.debug(data)
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

   elif sidx=='incoming':
      q = q.order_by(func.count('*')) if sord=='asc' \
            else q.order_by(desc(func.count('*')))

   elif sidx=='connect':
      q = q.order_by(connect.c.count) if sord=='asc' \
            else q.order_by(desc(connect.c.count))

   elif sidx=='abandon':
      q = q.order_by(abandon.c.count) if sord=='asc' \
            else q.order_by(desc(abandon.c.count))

   elif sidx=='dissuasion':
      q = q.order_by(dissuasion.c.count) if sord=='asc' \
            else q.order_by(desc(dissuasion.c.count))

   elif sidx=='closed':
      q = q.order_by(closed.c.count) if sord=='asc' \
            else q.order_by(desc(closed.c.count))

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
      group_by(xd)

   if date_filter is not None:
      q = q.filter(date_filter)
   
   if sidx=='count':
      q = q.order_by(func.count('*')) if sord=='asc' \
            else q.order_by(desc(func.count('*')))
   else:
      q = q.order_by(xd) if sord=='asc' \
            else q.order_by(desc(xd))

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

#   h_incoming = DBSession.query(xh, func.count('*').label('incoming')).\
#      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
#      filter(Queue_event.event=='ENTRANT').filter(queues_filter)
#   if date_filter is not None:
#      h_incoming = h_incoming.filter(date_filter)
#   h_incoming = h_incoming.group_by(xh).order_by(xh).subquery()

   h_connect = DBSession.query(
         xh, func.count('*').label('count')).\
      filter(queues_filter). \
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='CONNECT').filter(queues_filter)
   if date_filter is not None:
      h_connect = h_connect.filter(date_filter)
   h_connect = h_connect.group_by(xh).subquery()

   h_abandon = DBSession.query(
         xh, func.count('*').label('count')).\
      filter(queues_filter). \
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='ABANDON').filter(queues_filter)
   if date_filter is not None:
      h_abandon = h_abandon.filter(date_filter)
   h_abandon = h_abandon.group_by(xh).subquery()

   h_closed = DBSession.query(
         xh, func.count('*').label('count')).\
      filter(queues_filter). \
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='FERME').filter(queues_filter)
   if date_filter is not None:
      h_closed = h_closed.filter(date_filter)
   h_closed = h_closed.group_by(xh).subquery()

   h_dissuasion = DBSession.query(
         xh, func.count('*').label('count')).\
      filter(queues_filter). \
      filter(Queue_log.queue_event_id==Queue_event.qe_id).\
      filter(Queue_event.event=='DISSUASION').filter(queues_filter)
   if date_filter is not None:
      h_dissuasion = h_dissuasion.filter(date_filter)
   h_dissuasion = h_dissuasion.group_by(xh).subquery()

   q = DBSession.query(xh, func.count('*').label('incoming'),
            h_abandon.c.count.label('abandon'),
            h_connect.c.count.label('connect'), 
            h_dissuasion.c.count.label('dissuasion'), 
            h_closed.c.count.label('closed')).\
      filter(Queue_log.queue_event_id==Queue_event.qe_id). \
      filter(Queue_event.event=='ENTRANT').filter(queues_filter). \
      filter(queues_filter). \
      outerjoin((h_connect, xh==h_connect.c.xhour)). \
      outerjoin((h_abandon, xh==h_abandon.c.xhour)). \
      outerjoin((h_closed, xh==h_closed.c.xhour)). \
      outerjoin((h_dissuasion, xh==h_dissuasion.c.xhour)). \
      group_by(xh,h_abandon.c.count, h_connect.c.count, 
            h_dissuasion.c.count, h_closed.c.count)
   
   if date_filter is not None:
      q = q.filter(date_filter)

   if sidx=='incoming':
      q = q.order_by(desc(func.count('*'))) if sord=='desc' \
            else q.order_by(func.count('*'))

   elif sidx=='connect':
      q = q.order_by(desc(h_connect.c.count)) if sord=='desc' \
            else q.order_by(h_connect.c.count)

   elif sidx=='abandon':
      q = q.order_by(desc(h_abandon.c.count)) if sord=='desc' \
            else q.order_by(h_abandon.c.count)

   elif sidx=='dissuasion':
      q = q.order_by(desc(h_dissuasion.c.count)) if sord=='desc' \
            else q.order_by(h_dissuasion.c.count)

   elif sidx=='closed':
      q = q.order_by(desc(h_closed.c.count)) if sord=='desc' \
            else q.order_by(h_closed.c.count)

   else:
      q = q.order_by(desc(xh)) if sord=='desc' \
            else q.order_by(xh)

   q = q.offset(offset).limit(rows)
   total = q.count()/rows + 1
   data = []
   total_in = 0
   for i, r in enumerate(q.all()):
      total_in += r.incoming
      data.append({ 'id'  : i, 'cell': [
         u'%dh30' % ((r.xhour)/2) if i%2 \
            else u'%dh' % ((r.xhour)/2),
         r.incoming, 0, r.closed, 0, r.dissuasion, 0,
         r.abandon, 0, r.connect, 0]
      })

   for x in data:
      x['cell'][2] = '%.1f %%' % (100.0 * x['cell'][1] / total_in) \
            if x['cell'][1] else ''
      x['cell'][4] = '%.1f %%' % (100.0 * x['cell'][3] / total_in) \
            if x['cell'][3] else ''
      x['cell'][6] = '%.1f %%' % (100.0 * x['cell'][5] / total_in) \
            if x['cell'][5] else ''
      x['cell'][8] = '%.1f %%' % (100.0 * x['cell'][7] / total_in) \
            if x['cell'][7] else ''
      x['cell'][10] = '%.1f %%' % (100.0 * x['cell'][9] / total_in) \
            if x['cell'][9] else ''
   log.debug(data)
   return dict(page=page, total=total, rows=data)


def stat_members(page, rows, offset, sidx, sord, date_filter, queues_filter, members_filter):
   # members stats

   # Service: list of connects / disconnects, ordered by member, timestamp
   q_service = DBSession.query(Queue_log.timestamp,
         Queue_log.channel, Queue_event.event). \
         filter(Queue_log.queue_event_id==Queue_event.qe_id). \
         filter(queues_filter).filter(members_filter). \
         filter(Queue_event.event.in_(('ADDMEMBER', 'REMOVEMEMBER'))). \
         order_by(Queue_log.channel, desc(Queue_log.timestamp))

   # Pause
   q_pause = DBSession.query(Queue_log.timestamp, 
         Queue_log.channel, Queue_event.event). \
         filter(Queue_log.queue_event_id==Queue_event.qe_id). \
         filter(Queue_event.event.in_(('PAUSE','UNPAUSE'))). \
         filter(queues_filter).filter(members_filter). \
         order_by(Queue_log.channel, desc(Queue_log.timestamp))

   # Calls received per members
   q_call = DBSession.query(Queue_log.channel, 
         func.count('*').label('calls'), 
         func.avg(sql.cast(Queue_log.data2, types.INT)).label('avgtime'),
         func.sum(sql.cast(Queue_log.data2, types.INT)).label('calltime')). \
            filter(Queue_log.queue_event_id==Queue_event.qe_id). \
            filter(Queue_event.event.in_(('COMPLETECALLER', 'COMPLETEmember'))). \
            filter(queues_filter).filter(members_filter). \
            group_by(Queue_log.channel)

   if date_filter is not None:
      q_service = q_service.filter(date_filter)
      q_pause = q_pause.filter(date_filter)
      q_call = q_call.filter(date_filter)

   # members service
   members_service = {}
   services = q_service.all()
   for i,s in enumerate(services):
      if s.event=='REMOVEMEMBER': # End service
         member = s.channel[5:]
         if member in members_service.keys(): 
            members_service[member]['service_num'] += 1
            if members_service[member]['service']==None:
               if len(services)>i+1:
                  # Connect time = time(REMOVEMENBER) - time(ADDMEMBER)
                  members_service[member]['service'] = s.timestamp - \
                        service[i+1].timestamp
            else:
               if len(services)>i+1:
                  members_service[member]['service'] += s.timestamp-services[i+1].timestamp
         else: # member not seen before
            if len(services)>i+1:
               members_service[member] = {'service_num': 1,
                  'service': s.timestamp-services[i+1].timestamp,
                  'pause': datetime.timedelta(0),
                  'pause_num': 0,
                  'calls_in': 0,
                  'ci_dur': datetime.timedelta(0),
                  'ci_avg': datetime.timedelta(0)}

   # members pause
   pauses = q_pause.all()
   for i in range(0, len(pauses)-2):
      p1 = pauses[i]
      p2 = pauses[i+1]
      member = p1.channel[5:]
      if p1.event=='UNPAUSE' and p2.event=='PAUSE' and p2.channel[5:]==member:
         if member in members_service.keys():
            members_service[member]['pause_num'] += 1
            if members_service[member]['pause']==datetime.timedelta(0):
               members_service[member]['pause'] = p1.timestamp - p2.timestamp
            else:
               members_service[member]['pause'] += p1.timestamp - p2.timestamp
         else:
            members_service[member] = {'pause_num': 1,
                  'pause': p1.timestamp - p2.timestamp,
                  'service_num': 0,
                  'service': datetime.timedelta(0),
                  'calls_in': 0,
                  'ci_dur': datetime.timedelta(0),
                  'ci_avg': datetime.timedelta(0)}
         i += 2
      else:
         i += 1

   # Calls per members
   for c in q_call:
      member = c.channel[5:]
      if member in members_service.keys():
         members_service[member]['calls_in'] = c.calls
         members_service[member]['ci_dur'] = datetime.timedelta(0, c.calltime)
         members_service[member]['ci_avg'] = datetime.timedelta(0, int(c.avgtime))

   i = 0
   data = []
   sort_key = lambda x: x[0] # Sort by keys
   if sidx in ('service_num', 'service', 'pause_num', 'pause',
         'calls_in', 'ci_dur', 'ci_avg', 'calls_out', 'co_dur', 'co_avg'):
      # Sort by value
      sort_key = lambda x: x[1][sidx]

   for k,v in sorted(members_service.iteritems(), 
         key = sort_key, 
         reverse = True if sord=='desc' else False):
      data.append({'id': i, 'cell': [
         k, v['service_num'], td_hms(v['service']),
         v['pause_num'], td_hms(v['pause']),
         v['calls_in'], td_hms(v['ci_dur']), td_hms(v['ci_avg']),
         0, 0, 0
      ]})
      i += 1

   log.debug('total: %d members' % len(data))
   return dict(page=page, total=1, rows=data)


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

def members_options():
   ''' Returns distinct members from queue log
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
         options = members_options,
         default = members_options,
         validator = NotEmpty(),
         ),
      Spacer(),
      Label( text = u'4. Sélectionnez la statistique à afficher'),
      SingleSelectField('stat',
         label_text = u'Statistique',
         options = [('global', u'Globale'), 
            ('queues', u'Appels par groupe'), ('sla', u'Niveau de service'),
            ('abandon', u'Abandons'), ('daily', u'Distribution quotidienne'),
            ('hourly', u'Distribution horaire'), ('members', u'Service par agent'),
            ]),
   ]
   submit_text = u'Valider...'
   hover_help = True
   action = 'do_stat'
stats_form = Stats_form('stats_form')


class CC_Stats_ctrl(BaseController):
   
#   allow_only = in_group('admin', 
#         msg=u'Vous devez appartenir au groupe "admin" pour gérer les services')

   sort_order = sort_index = None # Keep track of sorting for CSV export

   @sidebar(u'-- Groupes d\'appels || Statistiques',
      icon = '/images/kdf.png', sortorder = 20)
   @expose(template='astportal2.templates.form_new')
   def index(self):
      ''' Display Stats form
      '''
      tmpl_context.form = stats_form
      return dict( title=u'Statistiques des groupes d\'appels', debug='', values='')


   @expose(template='astportal2.templates.cc_stats')
   def do_stat(self, period, begin, end, queues, members, stat):

      if type(queues) != type([]):
         queues = (queues)
      queue_filter = Queue_log.queue.in_(queues)

      if type(members) != type([]):
         members = (members)
      member_filter = Queue_log.channel.in_(members)
      log.debug('member_filter')

# Dynamic template
#tg.decorators.override_template(controller, "genshi:myproject.templates.index2")

      tmpl_context.flot_labels_rotated = 'false' # Rotate plot labels ?

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
            { 'name': 'connect', 'width': 40, 'align': 'right', 'sortable': True},
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
            { 'name': 'wait', 'width': 60, 'sortable': False},
            { 'name': 'count', 'width': 40, 'align': 'right', 'sortable': False},
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
         caption = flot_label = u'Distribution horaire'
         sortname = 'hour'
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
         tmpl_context.flot_series = '"0,2,4,6"' # List of series to plot
         title = u'Distribution horaire'
         tmpl_context.flot_labels_rotated = 'true' # Rotate plot labels ?

      elif stat=='members':
         row_list = (50, 100, 150)
         caption = flot_label = u'Agents'
         sortname = 'member'
         sortorder = 'asc'
         colnames = [u'Agent', u'Services', u'Durée', u'Pauses', u'Durée',
               u'Appels reçus', u'Durée', u'Moyenne', 
               u'Appels émis', u'Durée', u'Moyenne' ]
         colmodel = [
            {'name': 'member', 'width': 60, 'sortable': True},
            {'name': 'service_num', 'width': 40, 'align': 'right', 'sortable': True},
            {'name': 'service', 'width': 40, 'align': 'right', 'sortable': True},
            {'name': 'pause_num', 'width': 40, 'align': 'right', 'sortable': True},
            {'name': 'pause', 'width': 20, 'align': 'right', 'sortable': True},
            {'name': 'calls_in', 'width': 40, 'align': 'right', 'sortable': True},
            {'name': 'ci_dur', 'width': 20, 'align': 'right', 'sortable': True},
            {'name': 'ci_avg', 'width': 20, 'align': 'right', 'sortable': True},
            {'name': 'calls_out', 'width': 40, 'align': 'right', 'sortable': True},
            {'name': 'co_dur', 'width': 20, 'align': 'right', 'sortable': True},
            {'name': 'co_avg', 'width': 20, 'align': 'right', 'sortable': True},
         ]
         tmpl_context.flot_series = '"0,2,4,7"' # List of series to plot
         title = u'Distribution par agent'
         tmpl_context.flot_labels_rotated = 'true' # Rotate plot labels ?

      # Hidden form for CSV export
      tmpl_context.form = Form(
         name = 'stats_form',
         submit_text = None,
         hover_help = True,
         fields = [
            HiddenField(name='period',default=period),
            HiddenField(name='begin',default=begin),
            HiddenField(name='end',default=end),
            HiddenField(name='queues',default=';'.join(queues)),
            HiddenField(name='members',default=';'.join(members)),
            HiddenField(name='stat',default=stat),
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

      self.sort_order = sord
      self.sort_index = sidx

      date_filter, queues_filter, members_filter = mk_filters(period, begin, end,
         kw['queues[]'] if 'queues[]' in kw.keys() else (kw['queues']),
         kw['members[]'] if 'members[]' in kw.keys() else (kw['members']) )

      log.debug(kw['members[]'] if 'members[]' in kw.keys() else (kw['members']))
      log.debug(members_filter)

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

      elif stat=='members':
         return stat_members(page, rows, offset, sidx, sord, 
               date_filter, queues_filter, members_filter)


   @expose()
   def csv(self, period, begin, end, stat, queues, members):
      log.debug(
         'csv: period=%s, begin=%s, end=%s, stat=%s, queues=%s, members=%s, sidx=%s, sord=%s' % (
         period, begin, end, stat, queues, members, self.sort_index, self.sort_order))

      date_filter, queues_filter, members_filter = mk_filters(period, begin, end,
         queues.split(';'), members.split(';') )

      log.debug(u'date_filter=%s, queues_filter=%s, members_filter=%s' %(
         date_filter, queues_filter, members_filter))

      if stat=='global':
         colnames = [u'Groupe d\'appels', u'Nombre d\'appels reçus']
         title = u'Statistiques globales'
         rows = stat_global(0, 1000, 0, self.sort_index, self.sort_order, 
               date_filter, queues_filter)['rows']

      elif stat=='queues':
         colnames = [u'Groupe d\'appels', u'Appels reçus', u'Traités', u'%',
               u'Abandons', u'%', u'Dissuasions', u'%', u'Fermé', u'%']
         title = u'Statistiques par groupes d\'appels'
         rows = stat_queues(0, 1000, 0, self.sort_index, self.sort_order, 
               date_filter, queues_filter)['rows']

      elif stat in ('sla','abandon'):
         colnames = [u'Attente', u'Appels', u'%', u'Cumul (%)']
         tmpl_context.flot_series = '"0,"' # List of series to plot
         if stat=='sla':
            title = u'Niveau de service'
            rows = stat_sla(0, 1000, 0, self.sort_index, self.sort_order, 
               date_filter, queues_filter, 'CONNECT')['rows']
         else:
            title = u'Abandons'
            rows = stat_sla(0, 1000, 0, self.sort_index, self.sort_order, 
               date_filter, queues_filter, 'ABANDON')['rows']

      elif stat=='daily':
         colnames = [u'Jour de la semaine', u'Appels', u'%']
         title = u'Distribution quotidienne'
         rows = stat_daily(0, 1000, 0, self.sort_index, self.sort_order, 
            date_filter, queues_filter,)['rows']

      elif stat=='hourly':
         colnames = [u'Heure', u'Entrant', u'%', u'Fermé', u'%',
               u'Dissuasion', u'%', u'Abandons', u'%', u'Traités', u'%']
         title = u'Distribution horaire'
         rows = stat_hourly(0, 1000, 0, self.sort_index, self.sort_order, 
            date_filter, queues_filter,)['rows']

      elif stat=='members':
         colnames = [u'Agent', u'Services', u'Durée', u'Pauses', u'Durée',
               u'Appels reçus', u'Durée', u'Moyenne', 
               u'Appels émis', u'Durée', u'Moyenne' ]
         title = u'Distribution par agent'
         rows = stat_members(0, 1000, 0, self.sort_index, self.sort_order, 
            date_filter, queues_filter, members_filter)['rows']
         log.debug(rows)

      else:
         log.error(u'Unknown stat %s' % stat)

      csvdata = StringIO.StringIO()
      writer = csv.writer(csvdata)

      # File name + write header
      today = datetime.datetime.today()
      filename = 'statistiques-groupes-' + today.strftime('%Y%m%d') + '.csv'
      writer.writerow([title])
      writer.writerow(['Date', today.strftime('%d/%m/%Y')])
      writer.writerow([c.encode('utf-8') for c in colnames])

      # Write CSV data
      for r in rows:
         writer.writerow(r['cell'])

      rh = response.headers
      rh['Content-Type'] = 'text/csv; charset=utf-8'
      rh['Content-disposition'] = 'attachment; filename="%s"' % filename
      rh['Pragma'] = 'public' # for IE
      rh['Cache-control'] = 'max-age=0' #for IE

      return csvdata.getvalue()
