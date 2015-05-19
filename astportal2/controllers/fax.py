# -*- coding: utf-8 -*-
# Fax CReate / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config, session
from tg.controllers import RestController
from tgext.menu import sidebar

try:
   from tg.predicates import in_group, not_anonymous, in_any_group
except ImportError:
   from repoze.what.predicates import in_group, not_anonymous, in_any_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, FileField, RadioButtonList
from tw.forms.validators import NotEmpty, Int, FieldStorageUploadConverter

from genshi import Markup
from os import system, unlink
import logging
log = logging.getLogger(__name__)
import re

from astportal2.model import DBSession, Fax, User
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

dir_fax = config.get('directory.fax')
sendfax = config.get('command.sendfax')

# User forms
new_fax_form = TableForm(
   fields = [
      TextField('dest', validator=NotEmpty,
         label_text=u'Numéro(s) destinataire(s)', 
#         help_text=u'Liste de destinataires séparés par ";"'
         ),
      FileField('file', validator=FieldStorageUploadConverter(not_empty=True),
         label_text=u'Fichier PDF',
#         help_text=u'Fichier à envoyer'
         ),
      TextField('comment',
         label_text=u'Commentaires', 
#         help_text=u'Description de la télécopie' 
         ),
   ],
   submit_text = u'Valider...',
   action = '/fax/create',
#   hover_help = True
   )

def process_file(upload, id, dest, email):
   ''' Check file type, then call Hylafax sendfax
   '''

   # Temporarily save uploaded audio file
   filename = upload.filename
   filetype = upload.type
   filedata = upload.file
   log.debug('process_file: <%s> <%s> <%s> -> %s' % (filename, filetype, filedata, dest))

# Firefox sends text/html ?!?! bug
#   if filetype!='application/pdf':
#      return u'Le fichier doit être au format PDF !'

   file = '%s/%d_%s' % (dir_fax, id, re.sub(r'[^\w\.]', '_', filename))
   pdf_data = filedata.read()
   out = open(file, 'w')
   out.write(pdf_data)
   out.close()

   # Send fax
   d = re.sub(r'[^0-9;]', '', dest)
   cmd = sendfax
   if email: cmd += ' -f ' + email
   cmd += ' -d ' + ' -d '.join(d.split(';'))
   cmd += ' ' + file
   log.debug('senfax command: <%s>' % cmd)
   ret = 0
   ret = system(cmd)

   if ret:
      log.error('executing <%s> returns <%d>' % (cmd,ret))
      return u"Erreur lors de l'envoi, le fichier PDF n'a pas été envoyé !", None

   return None, pdf_data


def row(f):
   '''Displays a formatted row of the moh list
   Parameter: Fax object
   '''

   action = u'<a href="#" onclick="del(\'%s\',\'%s\')" title="Supprimer">' % (str(f.fax_id), u"Suppression de la télécopie %s" % f.filename)
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   download = u'''<a href="download?id=%s"><img src="/images/emblem-downloads.png" title="Télécharger"></a>''' % f.fax_id

   type = u'Envoyé' if f.type==0 else u'Reçu'

   return [Markup(action), type, f.dest, f.src, f.filename, f.comment , 
      f.created.strftime('%A %d %B, %Hh%M').decode('utf-8'), Markup(download) ]


class Fax_ctrl(RestController):
   
   allow_only = in_any_group('admin', 'Fax', 
      msg=u'Vous devez appartenir au groupe "Fax" pour envoyer des télécopies')

   @sidebar(u"Fax", sortorder=3,
      icon = '/images/kfax.png')
   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all fax
      '''

      grid = MyJqGrid( id='grid', url='fetch', caption=u"Télécopies",
            sortname='created', sortorder='desc',
            colNames = [u'Action', u'Type', u'Destinataire(s)', u'Origine', 
               u'Fichier', u'Commentaires', u'Date', u'Télécharg.' ],
            colModel = [ { 'width': 60, 'align': 'center', 'sortable': False },
               { 'name': 'type', 'width': 60 },
               { 'name': 'dest', 'width': 100 },
               { 'name': 'src', 'width': 100 },
               { 'name': 'filename', 'width': 100 },
               { 'name': 'comment', 'width': 280 },
               { 'name': 'created', 'width': 120 },
               { 'width': 60, 'align': 'center', 'sortable': False },
               ],
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': True, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u"Liste des télécopies", debug='')


   @expose('json')
   def fetch(self, page, rows, sidx='date', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

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

      u = DBSession.query(User).filter(User.user_name==request.identity['repoze.who.userid']).one()
      fax = DBSession.query(Fax)
      if not in_group('admin'):
         fax = fax.filter(Fax.user_id==u.user_id)

      total = fax.count()/rows + 1
      column = getattr(Fax, sidx)
      fax = fax.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      rows = [ { 'id'  : f.fax_id, 'cell': row(f) } for f in fax ]

      return dict(page=page, total=total, rows=rows)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new fax form
      '''
      tmpl_context.form = new_fax_form
      return dict(title = u"Envoi télécopie", debug='', values='')

   @validate(new_fax_form, error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new fax to DB
      '''
      f = Fax()
      f.type = 0 # 0=Sent, 1=Received
      f.comment = kw['comment']
      f.dest = kw['dest']
      f.filename = kw['file'].filename
      u = DBSession.query(User).filter(User.user_name==request.identity['repoze.who.userid']).one()
      f.user_id = u.user_id
      try:
         f.src = u.phone[0].exten
      except:
         f.src = None

      # Try to insert file in DB: might fail if name already exists
      try:
         DBSession.add(f)
         DBSession.flush()
      except:
         flash(u'Impossible de créer le fax', 'error')
         redirect('/fax/')

      ret, pdf_data = process_file(kw['file'], f.fax_id, kw['dest'], u.email_address)
      
      if ret is not None:
         flash(ret,'error')
         DBSession.delete(f)
         redirect('/fax/')

      f.pdf = pdf_data

      flash(u'"%s" en cours d\'envoi à %s' % (kw['file'].filename, kw['dest']))
      redirect('/fax/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete fax from DB
      '''
      id = kw['_id']
      log.info('delete ' + id)
      f = DBSession.query(Fax).get(id)
      # remove uploaded file
      try:
         if f.type==0:
            pdf = '%s/%d_%s' % (dir_fax, f.fax_id, re.sub(r'[^\w\.]', '_', f.filename))
         else:
            pdf = '%s/%s' % (dir_fax, f.filename)
         unlink(pdf)
      except:
         # No file since move into fax in database
         log.warning('unlink failed %s' % id)
      DBSession.delete(f)
      flash(u'Fax supprimé', 'notice')
      redirect('/fax/')


   @expose()
   def download(self, id, **kw):
      ''' Download fax
      '''
      f = DBSession.query(Fax).get(id)

      if f.pdf is None:
         flash(u'Fichier PDF non disponible', 'error')
         redirect('/fax/')

      name = 'fax-%s.pdf' % id
      fn = '/tmp/' + name
      try:
         fd = open( fn, 'w')
         fd.write(f.pdf)
         fd.close()
      except:
         flash(u'Fichier PDF non disponible', 'error')
         redirect('/fax/')
 
      import os
      try:
         st = os.stat(fn)
         fd = open(fn)
      except:
         flash(u'Fichier PDF introuvable: %s' % fn, 'error')
         redirect('/fax/')

      rh = response.headers
      rh['Pragma'] = 'public' # for IE
      rh['Expires'] = '0'
      rh['Cache-control'] = 'must-revalidate, post-check=0, pre-check=0' #for IE
      rh['Cache-control'] = 'max-age=0' #for IE
      rh['Content-Type'] = 'application/pdf'
      rh['Content-disposition'] = u'attachment; filename="%s"; size=%d;' % (
         name, st.st_size)
      rh['Content-Transfer-Encoding'] = 'binary'
      return fd.read()

