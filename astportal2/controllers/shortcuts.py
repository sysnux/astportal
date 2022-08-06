# -*- coding: utf-8 -*-
# Shortcut CReate / Update RESTful controller

from tg import expose, flash, redirect, tmpl_context, validate, config, session
from tg.controllers import RestController
from tgext.menu import sidebar

try:
   from tg.predicates import in_group
except ImportError:
   from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, Label, TextField, HiddenField, SingleSelectField
from tw.forms.validators import NotEmpty, Int

from astportal2.lib.app_globals import Globals, Markup

from astportal2.model import DBSession, Shortcut, Phone
from astportal2.lib.myjqgrid import MyJqGrid

import logging
log = logging.getLogger(__name__)
directory_asterisk = config.get('directory.asterisk')

def phones():
   phones_list = [(None, u'Raccourci global')]
   for p in DBSession.query(Phone).order_by(Phone.exten):
      label = p.exten
      if p.user is not None:
         label += ' (%s)' % p.user.display_name
      phones_list.append((p.sip_id, label))
   return phones_list

class Shortcut_form(TableForm):
   ''' Shortcut form
   '''
   fields = [
      TextField('exten', validator=NotEmpty,
         label_text=u'Numéro abrégé'), #help_text=u'Entrez le numéro abrégé'),
      TextField('number', validator=NotEmpty,
         label_text=u'Numéro réel'), # help_text=u'Entrez le numéro réel'),
      TextField('comment', validator=NotEmpty,
         label_text=u'Descriptif'), # help_text=u'Entrez un descriptif'),
      HiddenField('shortcut_id',validator=Int),
#      SingleSelectField('phone', options = phones,
#         label_text=u'téléphone')
   ]
   submit_text = u'Valider...'
#   hover_help = True


class New_shortcut_form(Shortcut_form):
   ''' Shortcut form
   '''
   action = '/shortcuts/create'
new_shortcut_form = New_shortcut_form('new_shortcut_form')


class Edit_shortcut_form(Shortcut_form):
   ''' Shortcut form
   '''
   fields = Shortcut_form.fields + [
      HiddenField('_method',validator=None)] # Needed by RestController
   action = '/shortcuts'
edit_shortcut_form = Edit_shortcut_form('edit_shortcut_form')


def row(s):
   '''Displays a formatted row of the shortcuts list
   Parameter: Shortcut object
   '''

   html =  u'<a href="'+ str(s.shortcut_id) + u'/edit" title="Modifier">' \
      + u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>' \
      + u'&nbsp;&nbsp;&nbsp;' \
      + u'<a href="#" onclick="del(\''+ str(s.shortcut_id) \
      + u'\',\'Suppression du raccourci ' + s.exten + u'\')" title="Supprimer">' \
      + u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(html), s.comment, s.exten, s.number ]


class Shortcut_ctrl(RestController):
   
   allow_only = in_group('admin', 
         msg=u'Vous devez appartenir au groupe "admin" pour gérer les raccourcis')

   @sidebar(u'-- Administration || Numéros abrégés',
      icon = '/images/kdf.png', sortorder = 16)
   @expose("astportal2.templates.grid")
   def get_all(self):
      ''' List all shortcuts
      '''
      grid = MyJqGrid( 
            id='grid', url='fetch', caption=u'Numéros raccourcis',
            colNames = [u'Action', u'Description', u'Raccourci', u'Numéro réel'],
            colModel = [ 
               { 'width': 80, 'align': 'center', 'sortable': False, 'search': False },
               { 'name': 'comment', 'width': 160 },
               { 'name': 'exten', 'width': 80 },
               { 'name': 'number', 'width': 80 },
            ],
            sortname = 'exten',
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': False, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des raccourcis', debug='')


   @expose('json')
   def fetch(self, page, rows, sidx='exten', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by Grid JS component
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

      shortcut = DBSession.query(Shortcut)
      total = shortcut.count()/rows + 1
      column = getattr(Shortcut, sidx)
      shortcut = shortcut.order_by(getattr(column,sord)()).offset(offset).limit(rows)

      data = [ { 'id'  : s.shortcut_id, \
            'cell': row(s)
            } for s in shortcut ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new hostrcut form
      '''
      tmpl_context.form = new_shortcut_form
      return dict(title = u'Nouveau raccourci', debug='', values='')
      
   @validate(new_shortcut_form, error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new shortcut to DB
      '''

      if DBSession.query(Shortcut).filter((Shortcut.exten==kw['exten']) |
                                          (Shortcut.number==kw['number'])).all():
         flash(u'Erreur : raccourci %s ou numéro %s existe déjà' % (
            kw['exten'], kw['number']), 'error')
         redirect('/shortcuts/')

      s = Shortcut()
      s.exten = kw['exten']
      s.number = kw['number']
      s.comment = kw['comment']
#      s.phone = kw['phone']
      DBSession.add(s)
      flash(u'Nouveau raccourci "%s -> %s" créé' % (s.exten, s.number))

      # Create new shortcut
      res = Globals.manager.update_config(
         directory_asterisk  + 'shortcuts.conf', 
         None,
         [('Append',
           'shortcuts', 'exten', 
           '>%s,1,Goto(${CHANNEL:-17:8},%s,1)' % (s.exten, s.number))])
      log.debug('Create shortcuts returns %s', res)

      # Reload dialplan
      Globals.manager.send_action({'Action': 'Command',
                                   'Command': 'dialplan reload'})

      redirect('/shortcuts/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit shortcut form
      '''
      if not id: id = kw['shortcut_id']
      s = DBSession.query(Shortcut).get(id)
      v = {'shortcut_id': s.shortcut_id, 'exten': s.exten, 
            'number': s.number, 'comment': s.comment, 
            'phone': s.phone, '_method': 'PUT'}
      tmpl_context.form = edit_shortcut_form
      return dict(title = u'Modification raccourci ' + s.exten, 
         debug='', values=v)


   @validate(edit_shortcut_form, error_handler=edit)
   @expose()
   def put(self, shortcut_id, **kw):
      ''' Update shortcut in DB
      '''
      log.info('update %d' % shortcut_id)
      s = DBSession.query(Shortcut).get(shortcut_id)
      # First, delete old shortcut
      actions = [('Delete',
                  'shortcuts',
                  'exten',
                  None,
                  '%s,1,Goto(${CHANNEL:-17:8},%s,1)' % (s.exten, s.number))]

      s.exten = kw['exten']
      s.number = kw['number']
      s.comment = kw['comment']
#      s.phone = kw['phone']

      # Next, create new shortcut
      actions.append(('Append',
                      'shortcuts', 'exten', 
                      '>%s,1,Goto(${CHANNEL:-17:8},%s,1)' % (s.exten, s.number)))

      res = Globals.manager.update_config(
         directory_asterisk  + 'shortcuts.conf', 
         None,
         actions)
      log.debug('Update shortcuts returns %s', res)

      # Reload dialplan
      Globals.manager.send_action({'Action': 'Command',
                                   'Command': 'dialplan reload'})

      flash(u'Raccourci modifié')
      redirect('/shortcuts/%d/edit' % shortcut_id)


   @expose()
   def delete(self, id, **kw):
      ''' Delete shortcut from DB
      '''
      log.info('delete ' + kw['_id'])
      s = DBSession.query(Shortcut).get(kw['_id'])
      # Delete shortcut
      res = Globals.manager.update_config(
         directory_asterisk  + 'shortcuts.conf', 
         None,
         [('Delete',
           'shortcuts',
           'exten',
           None,
           '%s,1,Goto(${CHANNEL:-17:8},%s,1)' % (s.exten, s.number))])

      # Reload dialplan
      Globals.manager.send_action({'Action': 'Command',
                                   'Command': 'dialplan reload'})

      DBSession.delete(s)
      log.debug('Update shortcuts returns %s', res)
      flash(u'Raccourci supprimé', 'notice')
      redirect('/shortcuts/')

