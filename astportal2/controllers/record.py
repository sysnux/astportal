# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config, session
from astportal2.lib.base import BaseController
from tgext.menu import sidebar

from repoze.what.predicates import in_group, not_anonymous, in_any_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, RadioButtonList, CalendarDatePicker
from tw.forms.validators import NotEmpty, Int, DateConverter, TimeConverter

from tw.jquery.ui import ui_tabs_js

from genshi import Markup
from os import system, unlink
import logging
log = logging.getLogger(__name__)
import re
from os import stat

from astportal2.model import DBSession, Record, User, Queue, Queue_log
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals
from datetime import timedelta

import sqlalchemy
db_engine = DBSession.connection().engine.name
dir_monitor = config.get('directory.monitor')

def row(r, users):
   '''Displays a formatted row of the record list
   Parameter: Record object, users dict
   '''

#   action = u'<a href="#" onclick="del(\'%s\',\'%s\')" title="Supprimer">' % (
#      str(r.Record.record_id), u"Suppression de l\\'enregistrement ?")
#   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   listen = u'''<a href="/records/download?id=%s"><img src="/images/emblem-downloads.png" title="Télécharger l'enregitrement"></a>''' % \
         r.Record.record_id
   listen += u'''&nbsp;&nbsp;&nbsp;<a href="/records/listen?id=%s"><img src="/images/sound_section.png" title="&Eacute;couter l'enregitrement"></a>''' % \
         r.Record.record_id

   user = users[r.Record.user_id] if r.Record.user_id is not None else ''

   return [#Markup(action), 
         r.Queue.name, users[r.Record.member_id], user, 
         r.Record.created.strftime("%d %B, %Hh%Mm%Ss").decode('utf-8'),
         Markup(listen)]


def check_access(queues):
   '''Check access rigths to queues
   '''
   if in_group('admin'):
      user_queues = queues
   else:
      user_queues = []
      if type(queues)!=type([]):
         queues = [queues]
      for q in queues:
         if in_group('SV ' + q):
            user_queues.append(q)
   log.debug('User queues: %s' % user_queues)
   return user_queues


def queues_options():
   ''' Returns distinct queues from queue log
   '''
   # queue_event_id==24 => AddMember
   queues = [q[0] for q in DBSession.query(Queue_log.queue).distinct().\
         filter(Queue_log.queue_event_id==24).order_by(Queue_log.queue)]
   return check_access(queues)


def members_options():
   ''' Returns distinct members from queue log
   '''
   # queue_event_id==24 => AddMember
   uids = [a.user for a in DBSession.query(Queue_log.user).distinct(). \
         filter(Queue_log.queue_event_id==24)]
   log.debug(u'Queue members uids=%s' % uids)

   return [(a.user_id, u'%s (%s)' % (a.display_name, a.user_name)) \
      for a in DBSession.query(User). \
         filter(User.user_id.in_(uids)).order_by(User.display_name)]

interval = '30 min'
class Search_Record(TableForm):
   name = 'search_form'
   submit_text = u'Valider...'
   fields = [
      Label(text = u'Sélectionnez un ou plusieurs critères'),
      TextField( 'custom1',
         attrs = {'size': 20, 'maxlength': 20},
         label_text = u"Numéro d'abonné"),
      SingleSelectField('member',
         label_text = u'Agent',
         validator = Int(not_empty=False),
         options = [ (-1, ' - - -') ] + members_options()),
      SingleSelectField('queue',
         label_text = u'Groupe ACD',
         validator = Int(not_empty=False),
         options = [ (-1, ' - - -') ] + queues_options()),
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
         validator = TimeConverter(not_empty=False),
         label_text = u'Heure +/- ' + interval),
      ]
search_form = Search_Record('search_record_form', action='index2')


grid = MyJqGrid( id='grid', url='fetch', caption=u"Enregistrements ACD",
            sortname='created', sortorder='asc',
#            colNames = [u'Action', 
            colNames = [u'Groupe ACD', u'Agent', u'Enregistré par', 
               u'Date', u'\u00C9coute' ],
#            colModel = [ { 'width': 50, 'align': 'center', 'sortable': False},
            colModel = [ { 'name': 'queue_id', 'width': 80, 'sortable': False },
               { 'name': 'member_id', 'width': 60, 'sortable': False },
               { 'name': 'user_id', 'width': 70, 'sortable': False },
               { 'name': 'created', 'width': 120 },
               { 'name': 'listen', 'width': 50, 'sortable': False, 'align': 'center'},
               ],
            navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': False, 'refresh': True, 
               }
            )

class Record_ctrl(BaseController):
   
   @sidebar(u"-- Groupes d'appels || Enregistre- -ments", sortorder=10,
      icon = '/images/media-record.png')
   @expose(template="astportal2.templates.cdr")
   def index(self, **kw):

      log.debug('index')

      if Globals.manager is None:
         flash(u'Vérifier la connexion Asterisk', 'error')
      else:
         Globals.manager.send_action({'Action': 'QueueStatus'})

      for k in ('custom1', 'member', 'queue', 'date', 'hour'):
         if k in session.keys():
            del(session[k])
      session.save()

      # User must be admin or queue supervisor
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
      if not in_any_group(*sv):
         tmpl_context.grid = None
         flash(u'Accès interdit !', 'error')
      else:
         tmpl_context.grid = grid

      tmpl_context.form = search_form

      # Use tabs
      ui_tabs_js.inject()

      return dict(title=u"Liste des enregistrements", debug='', values={})


   @expose(template="astportal2.templates.cdr")
   @validate(search_form, index)
   def index2(self, custom1=None, member=None, queue=None, date=None, hour=None):
      ''' List records
      '''

      log.debug('index2: custom1=%s (%s), member=%s (%s), queue=%s (%s), date=%s (%s), hour=%s (%s).' % (
         custom1, type(custom1), member, type(member), queue, type(queue), date, type(date), hour, type(hour)))
      session['custom1'] = custom1 if custom1 is not None and custom1!='' else None
      session['member'] = member if member is not None and member!=-1 else None
      session['queue'] = queue if queue is not None and queue!=-1 else None
      session['date'] = date if date is not None else None
      session['hour'] = hour if hour is not None and hour!='' else None
      session.save()

      # User must be admin or queue supervisor
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
      if not in_any_group(*sv):
         tmpl_context.grid = None
         flash(u'Accès interdit !', 'error')
      else:
         tmpl_context.grid = grid

      tmpl_context.form = search_form

      # Use tabs
      ui_tabs_js.inject()

      return dict( title=u"Liste des enregistrements", debug='', 
         values={'custom1': custom1, 'member': member, 'queue': queue, 
            'date': date, 'hour': hour})


   @expose('json')
   def fetch(self, page, rows, sidx='user_name', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):

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
         offset = (page-1) * rows
      except:
         offset = 0
         page = 1
         rows = 25

      users = {}
      for u in DBSession.query(User):
         users[u.user_id] = u.user_name

      records = DBSession.query(Record, Queue). \
            filter(Record.queue_id==Queue.queue_id)

      filter = []
      custom1 = session.get('custom1', None)
      member = session.get('member', None)
      queue = session.get('queue', None)
      date = session.get('date', None)
      hour = session.get('hour', None)

      if custom1 is not None:
         filter.append(u'Client %s' % custom1)
         records = records.filter(Record.custom1==custom1)

      if member is not None and member!=-1:
         filter.append(u'Groupe %s' % member)
         records = records.filter(Record.member_id==member)

      if queue is not None and queue!=-1:
         filter.append(u'Groupe %s' % queue)
         records = records.filter(Record.queue_id==queue)

      if date is not None:
         filter.append(u'date %s' % date.strftime('%d/%m/%Y'))
         if db_engine=='oracle':
            records = records.filter(sqlalchemy.func.trunc(CDR.calldate, 'J')==date)
         else: # PostgreSql
            records = records.filter(sqlalchemy.sql.cast(Record.created, 
               sqlalchemy.types.DATE) == date)

      if hour is not None:
         filter.append(u'heure approximative %dh%02d' % (hour[0], hour[1]))
         if db_engine=='oracle':
            if hour[1]>=30: 
               hour1 = '%02d:%02d' % (hour[0], hour[1]-30)
               hour2 = '%02d:%02d' % (hour[0]+1, hour[1]-30)
            else:
               hour1 = '%02d:%02d' % (hour[0]-1, hour[1]+30)
               hour2 = '%02d:%02d' % (hour[0], hour[1]+30)
            records = records.filter(hour1<=sqlalchemy.func.to_char(Record.created, 'HH24:MI'))
            records = records.filter(sqlalchemy.func.to_char(Record.created, 'HH24:MI')<=hour2)
         else: # PostgreSql
            hour = '%d:%02d' % (hour[0], hour[1])
            records = records.filter("'%s' - '%s'::interval <= record.created::time AND record.created::time <= '%s' + '%s'::interval" % (hour, interval, hour, interval))

#      if len(filter):
#         m = u'Critères: ' if len(filter)>1 else u'Critere: '
#         flash( m + ', et '.join(filter) + '.')

      # Access rights
      if not in_group('admin'):
         user_queues = []
         for q in DBSession.query(Queue):
            if in_group('SV ' + q.name):
               user_queues.append(q.queueid)
         log.debug('User queues: %s' % user_queues)
         records = records.filter(Record.queue_id.in_(user_queues))

      total = records.count()/rows + 1
      column = getattr(Record, sidx)
      records = records.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      rows = [ { 'id'  : r.Record.record_id, 
         'cell': row(r, users) } for r in records ]

      return dict(page=page, total=total, rows=rows)


   @expose()
   def delete(self, id, **kw):
      ''' Delete record
      '''
      r = DBSession.query(Record).get(kw['_id'])
      fn = '%s/rec-%s.wav' % (dir_monitor, r.uniqueid)

      # remove file
      try:
         unlink(fn)
      except:
         log.error('unlink failed %s' % r.uniqueid)
      DBSession.delete(r)
      flash(u'Enregistrement supprimé', 'notice')
      redirect('/records/')



   @expose()
   def listen(self, id, **kw):
      ''' Listen record
      '''
      r = DBSession.query(Record).get(id)
      fn = '%s/rec-%s.wav' % (dir_monitor, r.uniqueid)
      try:
         st = stat(fn)
      except:
         flash(u'Enregistrement introuvable: %s' % fn, 'error')
         redirect('/records/')

      phones = DBSession.query(User).filter(User.user_name==request.identity['repoze.who.userid']).one().phone
      if len(phones)<1:
         log.debug('Playback from user %s : no extension' % (
            request.identity['user']))
         flash(u'Poste de l\'utilisateur %s introuvable' % \
               request.identity['user'], 'error')
         redirect('/records/')

      sip = phones[0].sip_id
      res = Globals.manager.originate(
            'SIP/' + sip, # Channel
            sip, # Extension
            application = 'Playback',
            data = fn[:-4],
            )
      log.debug('Playback %s from user %s (%s) returns %s' % (
         fn[:-4], request.identity['user'], sip, res))

      redirect('/records/')


   @expose()
   def download(self, id, **kw):
      ''' Download record
      '''
      r = DBSession.query(Record).get(id)
      fn = '%s/rec-%s.wav' % (dir_monitor, r.uniqueid)
      try:
         st = stat(fn)
         f = open(fn)
      except:
         flash(u'Enregistrement introuvable: %s' % fn, 'error')
         redirect('/records/')

      rh = response.headers
      rh['Pragma'] = 'public' # for IE
      rh['Expires'] = '0'
      rh['Cache-control'] = 'must-revalidate, post-check=0, pre-check=0' #for IE
      rh['Cache-control'] = 'max-age=0' #for IE
      rh['Content-Type'] = 'audio/wav'
      rh['Content-disposition'] = u'attachment; filename="%s"; size=%d;' % (
         'rec-%s.wav' % r.uniqueid, st.st_size)
      rh['Content-Transfer-Encoding'] = 'binary'

      return f.read()

