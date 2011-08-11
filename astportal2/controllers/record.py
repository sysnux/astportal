# -*- coding: utf-8 -*-
# Record CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config
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

from astportal2.model import DBSession, Record, User, Queue
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

dir_tmp = '/tmp'
dir_monitor = '/var/spool/asterisk/monitor'


def row(r):
   '''Displays a formatted row of the record list
   Parameter: Record object
   '''

   action = u'<a href="#" onclick="del(\'%s\',\'%s\')" title="Supprimer">' % (
      str(r.record_id), u"Suppression de l'enregistrement ") # XXX
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   listen = u'<a href="/record/listen?id=%s" title="Ecoute">Ecoute</a>' % r.record_id

   return [Markup(action), r.queue_id, r.member_id, r.user_id, r.created, Markup(listen)]


class Record_ctrl(RestController):
   
   @sidebar(u"-- Groupes d'appels || Enregistre- -ments", sortorder=10,
      icon = '/images/record_section-large.png')
   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all records
      '''

      grid = MyJqGrid( id='grid', url='fetch', caption=u"Sons et musiques d\'attente",
            sortname='created', sortorder='asc',
            colNames = [u'Action', u'Groupe ACD', u'Agent', u'Enregistré par', 
               u'Date', u'\u00C9coute' ],
            colModel = [ { 'width': 60, 'align': 'center', 'sortable': False},
               { 'name': 'queue_id', 'width': 80 },
               { 'name': 'member_id', 'width': 80 },
               { 'name': 'user_id', 'width': 80 },
               { 'name': 'created', 'width': 80 },
               { 'name': 'listen', 'width': 60, 'sortable': False },
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
   def fetch(self, page=1, rows=10, sidx='user_name', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * rows
      except:
         offset = 0
         page = 1
         rows = 25

      records = DBSession.query(Record)

      total = records.count()/rows + 1
      column = getattr(Record, sidx)
      records = records.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      rows = [ { 'id'  : s.record_id, 'cell': row(s) } for s in records ]

      return dict(page=page, total=total, rows=rows)


   @expose(content_type=CUSTOM_CONTENT_TYPE)
   def listen(self, id, **kw):
      ''' Listen record
      '''
      s = DBSession.query(Record).get(id)
      dir = dir_moh if s.type==0 else dir_records
      fn = '%s/%s.wav' % (dir, s.name)
      import os
      try:
         st = os.stat(fn)
         f = open(fn)
      except:
         flash(u'Enregistrement introuvable: %s' % fn, 'error')
         redirect('/record/')
      rh = response.headers
      rh['Pragma'] = 'public' # for IE
      rh['Expires'] = '0'
      rh['Cache-control'] = 'must-revalidate, post-check=0, pre-check=0' #for IE
      rh['Cache-control'] = 'max-age=0' #for IE
      rh['Content-Type'] = 'audio/wav'
      rh['Content-disposition'] = u'attachment; filename="%s"; size=%d;' % (
         s.name, st.st_size)
      rh['Content-Transfer-Encoding'] = 'binary'
      return f.read()

