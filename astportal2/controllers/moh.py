# -*- coding: utf-8 -*-
# Sound CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config
from tg.controllers import RestController, CUSTOM_CONTENT_TYPE
from tgext.menu import sidebar

from repoze.what.predicates import in_group, not_anonymous, in_any_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, FileField
from tw.forms.validators import NotEmpty, Int, FieldStorageUploadConverter

from genshi import Markup
from os import system, unlink
import logging
log = logging.getLogger(__name__)
import re

from astportal2.model import DBSession, Sound, User, Group
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

dir_tmp = '/tmp'
dir_moh = '/var/lib/asterisk/moh/astportal'

# Common fields
edit_sound_fields = [
         FileField('file', validator=FieldStorageUploadConverter(not_empty=True),
            label_text=u'Fichier sonore', help_text=u'Fichier au format WAV'),
         TextField('comment',
            label_text=u'Commentaires', help_text=u'Description du son' ),
         HiddenField('_method'), # Needed by RestController
         HiddenField('id', validator=Int),
         ]

new_sound_fields = [
         TextField('name', validator=NotEmpty,
            label_text=u'Nom', help_text=u'Nom du son'),
         FileField('file', validator=FieldStorageUploadConverter(not_empty=True),
            label_text=u'Fichier sonore', help_text=u'Fichier au format WAV'),
         TextField('comment',
            label_text=u'Commentaires', help_text=u'Description du son' ),
]


# User forms (new and edit)
new_sound_form = TableForm(
   fields = new_sound_fields,
   submit_text = u'Valider...',
   action = 'create',
   hover_help = True
   )

edit_sound_form = TableForm(
   fields = edit_sound_fields,
   submit_text = u'Valider...',
   action = '/moh/',
   hover_help = True
   )

def process_file(wav, id, name):
      ''' Convert and move to asterisk dir, with name "name.wav'
      '''

      # Temporarily save uploaded audio file
      filename = wav.filename
      filetype = wav.type
      filedata = wav.file

      if filetype.split('/')[0]!='audio':
         return u'Le fichier doit être de type son !'

      orig = '%s/%d_%s' % (dir_tmp, id, filename)
      final = '%s/%s.wav' % (dir_moh, re.sub(r'\W', '_', name))
      out = open(orig, 'w')
      out.write(filedata.read())
      out.close()

      # Convert to wav 16 bits, 8000 Hz, mono
      cmd = config.get('command.sox') % (orig, final)
      log.debug('sox command: <%s>' % cmd)
      ret = system(cmd)

      if ret:
         log.error('executing <%s> returns <%d>' % (cmd,ret))
         return u"Erreur lors de la conversion WAV, le son n'a pas été ajouté !"

      else:
         # remove uploaded file
         unlink(orig)
         Globals.manager.send_action({'Action': 'Command',
            'Command': 'moh reload'})

      return None


class SVI_users(SingleSelectField):
   def update_params(self,d):
      options = [(u.user_id, u.user_name) for u in 
         (DBSession.query(Group).filter(Group.group_name=='SVI').one()).users]
      d['options'] = options
      SingleSelectField.update_params(self, d)
      return d

# Fields for admin
admin_edit_sound_fields = []
admin_edit_sound_fields.extend(edit_sound_fields)
admin_edit_sound_fields.insert(0,
   SVI_users('owner_id',
      label_text=u'Client', help_text=u'Propriétaire du message')
   )
admin_new_sound_fields = []
admin_new_sound_fields.extend(new_sound_fields)
admin_new_sound_fields.insert(0,
   SVI_users('owner_id',
      label_text=u'Client', help_text=u'Propriétaire du message') 
   )

# Admin forms (new and edit)
admin_edit_sound_form = TableForm(
   fields = admin_edit_sound_fields,
   submit_text = u'Valider...',
   action = '/moh/',
   hover_help = True,
   )
admin_new_sound_form = TableForm(
   fields = admin_new_sound_fields,
   submit_text = u'Valider...',
   action = 'create',
   hover_help = True,
   )


def row(s):
   '''Displays a formatted row of the moh list
   Parameter: Sound object
   '''
   if s.owner_id:
      user = DBSession.query(User.display_name).get(s.owner_id).display_name
   else:
      user = ''

   action =  u'<a href="'+ str(s.sound_id) + u'/edit" title="Modifier">'
   action += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   action += u'&nbsp;&nbsp;&nbsp;'
   action += u'<a href="#" onclick="del(\'%s\',\'%s\')" title="Supprimer">' % (str(s.sound_id), u"Suppression de la musique: " + s.name.replace("'","\\'"))
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   listen = u'<a href="/moh/listen?id=%s" title="Ecoute">Ecoute</a>' % s.sound_id

   return [Markup(action), s.name, s.comment , Markup(listen) ]


class MOH_ctrl(RestController):
   
   allow_only = in_group('admin', 
      msg=u'Vous devez appartenir au groupe "admin" pour gérer les musique d\'attente')

   @sidebar(u"-- Administration || Musiques d'attente", sortorder=10,
      icon = '/images/sound_section-large.png')
   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all moh
      '''

      grid = MyJqGrid( id='grid', url='fetch', caption=u"Musiques d'attente",
            sortname='name', sortorder='asc',
            colNames = [u'Action', u'Nom', u'Commentaires', u'Ecoute' ],
            colModel = [ { 'width': 60, 'align': 'center' },
               { 'name': 'name', 'width': 60 },
               { 'name': 'comment', 'width': 280 },
               { 'name': 'owner_id', 'width': 60 },
               ],
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': True, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u"Liste des musiques d'attente", debug='')


   @expose('json')
   def fetch(self, page=1, rows=10, sidx='user_name', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * rows
      except:
         offset = 0
         page = 1
         rows = 25

      sounds = DBSession.query(Sound)

      total = sounds.count()/rows + 1
      column = getattr(Sound, sidx)
      sounds = sounds.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      rows = [ { 'id'  : a.sound_id, 'cell': row(a) } for a in sounds ]

      return dict(page=page, total=total, rows=rows)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new sound form
      '''
      if in_group('ADM'):
         tmpl_context.form = admin_new_sound_form
      else:
         tmpl_context.form = new_sound_form
      return dict(title = u"Nouvelle musique d'attente", debug='', values='')

   class new_form_valid(object):
      def validate(self, params, state):
         f = admin_new_sound_form if in_group('ADM') else new_sound_form
         return f.validate(params, state)

   @validate(new_form_valid(), error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new sound to DB
      '''
      s = Sound()
      s.name = kw['name']
      s.comment = kw['comment']
      if 'owner_id' in kw.keys():
         s.owner_id = kw['owner_id']
      else:
         s.owner_id = request.identity['user'].user_id

      # Try to insert file in DB: might fail if name already exists
      try:
         DBSession.add(s)
         DBSession.flush()
      except:
         flash(u'Impossible de créer le son (vérifier son nom)', 'error')
         redirect('/moh/')

      ret = process_file(kw['file'], s.sound_id, s.name)

      if ret:
         flash(ret,'error')
         DBSession.delete(s)
         redirect('/moh/')

      flash(u'Nouvelle musique d\'attente "%s" ajoutée à votre bibliothèque sonore' % (s.name))
      redirect('/moh/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id, **kw):
      ''' Display edit sound form
      '''
      id = int(id)
      s = DBSession.query(Sound).get(id)
      log.info('%s: %s' % (str(id), type(id)))
      v = {'id': s.sound_id, 'comment': s.comment, '_method': 'PUT'}
      tmpl_context.form = edit_sound_form
      return dict(title = u'Modification son ' + s.name, debug='', values=v)


   class edit_form_valid(object):
      def validate(self, params, state):
         f = admin_edit_sound_form if in_group('ADM') else edit_sound_form
         return f.validate(params, state)

#   @validate(edit_form_valid(), error_handler=edit)
   @expose()
   def put(self, **kw):
      ''' Update sound in DB
      '''
      id = int(kw['id'])
      s = DBSession.query(Sound).get(id)
      if kw.has_key('owner_id'):
         s.owner_id = kw['owner_id']
      s.comment = kw['comment']
      ret = process_file(kw['file'], id, s.name)

      if ret:
         flash(ret,'error')
         DBSession.delete(s)
         redirect('/moh/')

      flash(u'Son modifié')
      redirect('/moh/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete sound from DB
      '''
      id = kw['_id']
      log.info('delete ' + id)
      DBSession.delete(DBSession.query(Sound).get(id))
      # remove uploaded file
      try:
         unlink('%s/%s.wav' % (dir_moh, id))
      except:
         pass
      Globals.manager.send_action({'Action': 'Command',
         'Command': 'moh reload'})
      flash(u'Son supprimé', 'notice')
      redirect('/moh/')


   @expose(content_type=CUSTOM_CONTENT_TYPE)
   def listen(self, id, **kw):
      ''' Listen record
      '''
      fn = '%s/%s.wav' % (dir_moh, id)
      import os
      try:
         st = os.stat(fn)
         f = open(fn)
      except:
         flash(u'Fichier sonore introuvable: %s' % fn, 'error')
         redirect('/moh/')
      rh = response.headers
      rh['Pragma'] = 'public' # for IE
      rh['Expires'] = '0'
      rh['Cache-control'] = 'must-revalidate, post-check=0, pre-check=0' #for IE
      rh['Cache-control'] = 'max-age=0' #for IE
      rh['Content-Type'] = 'audio/wav'
      rh['Content-disposition'] = u'attachment; filename="%s"; size=%d;' % (fn, st.st_size)
      rh['Content-Transfer-Encoding'] = 'binary'
      return f.read()

