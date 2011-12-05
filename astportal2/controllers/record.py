# -*- coding: utf-8 -*-
# Record CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config, session
from tg.controllers import RestController, CUSTOM_CONTENT_TYPE
from tgext.menu import sidebar

from repoze.what.predicates import in_group, not_anonymous, in_any_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, FileField, RadioButtonList
from tw.forms.validators import NotEmpty, Int, FieldStorageUploadConverter

from genshi import Markup
from os import system, unlink
import logging
log = logging.getLogger(__name__)
import re
from os import stat

from astportal2.model import DBSession, Record, User, Queue
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

dir_monitor = config.get('directory.monitor')

def row(r, users):
   '''Displays a formatted row of the record list
   Parameter: Record object, users dict
   '''

   action = u'<a href="#" onclick="del(\'%s\',\'%s\')" title="Supprimer">' % (
      str(r.Record.record_id), u"Suppression de l\\'enregistrement ?")
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   listen = u'''<a href="/records/download?id=%s"><img src="/images/emblem-downloads.png" title="Télécharger l'enregitrement"></a>''' % \
         r.Record.record_id
   listen += u'''&nbsp;&nbsp;&nbsp;<a href="/records/listen?id=%s"><img src="/images/sound_section.png" title="&Eacute;couter l'enregitrement"></a>''' % \
         r.Record.record_id

   return [Markup(action), r.Queue.name, 
         users[r.Record.user_id], users[r.Record.member_id], 
         r.Record.created.strftime("%d %B, %Hh%Mm%Ss"), Markup(listen)]


class Record_ctrl(RestController):
   
   @sidebar(u"-- Groupes d'appels || Enregistre- -ments", sortorder=10,
      icon = '/images/media-record.png')
   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all records
      '''

      if Globals.manager is None:
         flash(u'Vérifier la connexion Asterisk', 'error')
      else:
         Globals.manager.send_action({'Action': 'QueueStatus'})
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
      if not in_any_group(*sv):
         tmpl_context.grid = None
         flash(u'Accès interdit !', 'error')
      else:
         grid = MyJqGrid( id='grid', url='fetch', caption=u"Enregistrements ACD",
            sortname='created', sortorder='asc',
            colNames = [u'Action', u'Groupe ACD', u'Agent', u'Enregistré par', 
               u'Date', u'\u00C9coute' ],
            colModel = [ { 'width': 60, 'align': 'center', 'sortable': False},
               { 'name': 'queue_id', 'width': 80, 'sortable': False },
               { 'name': 'member_id', 'width': 80, 'sortable': False },
               { 'name': 'user_id', 'width': 80, 'sortable': False },
               { 'name': 'created', 'width': 80 },
               { 'name': 'listen', 'width': 60, 'sortable': False, 'align': 'center'},
               ],
            navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': False, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
         tmpl_context.grid = grid

      tmpl_context.form = None
      return dict( title=u"Liste des enregistrements", debug='')


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

      if len(request.identity['user'].phone)<1:
         log.debug('Playback from user %s : no extension' % (
            request.identity['user']))
         flash(u'Poste de l\'utilisateur %s introuvable' % \
               request.identity['user'], 'error')
         redirect('/records/')

      sip = request.identity['user'].phone[0].sip_id
      res = Globals.manager.originate(
            'SIP/' + sip, # Channel
            sip, # Extension
            application = 'Playback',
            data = fn[:-4],
            )
      log.debug('Playback %s from user %s (%s) returns %s' % (
         fn[:-4], request.identity['user'], sip, res))

      redirect('/records/')


   @expose(content_type=CUSTOM_CONTENT_TYPE)
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

