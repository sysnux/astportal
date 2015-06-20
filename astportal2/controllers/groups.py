# -*- coding: utf-8 -*-
# Group CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, session
from tg.controllers import RestController
from tgext.menu import sidebar

try:
   from tg.predicates import in_group
except ImportError:
   from repoze.what.predicates import in_group

from tw.jqgrid import JqGrid
from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField
from tw.forms.validators import NotEmpty, Int

from astportal2.lib.app_globals import Markup

from astportal2.model import DBSession, Group, User
from astportal2.lib.myjqgrid import MyJqGrid

import logging
log = logging.getLogger(__name__)


class New_group_form(TableForm):
   ''' New group form
   '''
   fields = [
         TextField('group_name', validator=NotEmpty,
            label_text=u'Nom', help_text=u'Entrez le nom du groupe'),
         TextField('display_name', validator=NotEmpty,
            label_text=u'Descriptif', help_text=u'Entrez un descriptif du groupe'),
         ]
   submit_text = u'Valider...'
   action = '/groups/create'
   hover_help = True
new_group_form = New_group_form('new_group_form')


class Edit_group_form(TableForm):
   ''' Edit group form
   '''
   fields = [
         TextField('display_name', validator=NotEmpty,
            label_text='Descriptif', help_text=u'Entrez un descriptif du groupe'),
         HiddenField('_method', validator=None), # Needed by RestController
         HiddenField('group_id', validator=Int),
         ]
   submit_text = u'Valider...'
   action = '/groups'
   method = 'POST'
   hover_help = True
edit_group_form = Edit_group_form('edit_group_form')


def row(g):
   '''Displays a formatted row of the groups list
   Parameter: Group object
   '''
   if g.users:
      users = ', '.join([u.user_name for u in g.users]) #()[:80] + '...'
   else:
      users = ''

   html =  u'<a href="'+ str(g.group_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   if not g.group_name.startswith(u'SV ') and \
         not g.group_name.startswith(u'AG ') and not g.group_name=='admin':
      html += u'&nbsp;&nbsp;&nbsp;'
      html += u'<a href="#" onclick="del(\''+ str(g.group_id) + \
         u'\',\'Suppression du groupe ' + g.group_name + u'\')" title="Supprimer">'
      html += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(html), g.group_name, g.display_name , users]


class Group_ctrl(RestController):
   
   allow_only = in_group('admin', 
         msg=u'Vous devez appartenir au groupe "admin" pour gérer les groupes')


   @sidebar(u'-- Administration || Profils', sortorder = 14,
      icon = '/images/system-users.png')
   @expose(template='astportal2.templates.grid')
   def get_all(self):
      ''' List all groups
      '''
      grid = MyJqGrid(
            id='grid', url='fetch', caption=u'Profils',
            colNames = [u'Action', u'Nom', u'Description', u'Utilisateurs'],
            colModel = [ 
               { 'sortable': False, 'search': False, 'width': 80, 'align': 'center' },
               { 'name': 'group_name', 'width': 80 },
               { 'name': 'display_name', 'width': 160 },
               { 'name': 'users', 'sortable': False, 'search': False, 'width': 160 } ],
            sortname = 'group_name',
            navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': True, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des groupes', debug='', values=None)


   @expose('json')
   def fetch(self, page, rows, sidx='group_name', sord='asc', _search='false',
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

      groups = DBSession.query(Group)
      users = DBSession.query(User)
      if  searchOper and searchField and searchString:
         log.debug('fetch query <%s> <%s> <%s>' % \
            (searchField, searchOper, searchString))
         try:
            field = eval('Group.' + searchField)
         except:
            field = None
            log.error('eval: Group.' + searchField)
         if field and searchOper=='eq': 
            groups = groups.filter(field==searchString)
         elif field and searchOper=='ne':
            groups = groups.filter(field!=searchString)
         elif field and searchOper=='le':
            groups = groups.filter(field<=searchString)
         elif field and searchOper=='lt':
            groups = groups.filter(field<searchString)
         elif field and searchOper=='ge':
            groups = groups.filter(field>=searchString)
         elif field and searchOper=='gt':
            groups = groups.filter(field>searchString)
         elif field and searchOper=='bw':
            groups = groups.filter(field.ilike(searchString + '%'))
         elif field and searchOper=='bn':
            groups = groups.filter(~field.ilike(searchString + '%'))
         elif field and searchOper=='ew':
            groups = groups.filter(field.ilike('%' + searchString))
         elif field and searchOper=='en':
            groups = groups.filter(~field.ilike('%' + searchString))
         elif field and searchOper=='cn':
            groups = groups.filter(field.ilike('%' + searchString + '%'))
         elif field and searchOper=='nc':
            groups = groups.filter(~field.ilike('%' + searchString + '%'))
         elif field and searchOper=='in':
            groups = groups.filter(field.in_(str(searchString.split(' '))))
         elif field and searchOper=='ni':
            groups = groups.filter(~field.in_(str(searchString.split(' '))))

      total = groups.count()/rows + 1
      column = getattr(Group, sidx)
      groups = groups.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      data = [ { 'id'  : g.group_id, 'cell': row(g) } for g in groups ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new group form
      '''
      tmpl_context.form = new_group_form
      return dict(title = u'Nouveau groupe', debug='', values='')
      
   @validate(new_group_form, error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new group to DB
      '''
      g = Group()
      g.group_name = kw['group_name']
      g.display_name = kw['display_name']
      DBSession.add(g)
      flash(u'Nouveau groupe "%s" créé' % (kw['group_name']))
      redirect('/groups/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit group form
      '''
      if not id: id = kw['group_id']
      g = DBSession.query(Group).get(id)
      v = {'group_id': g.group_id, 'display_name': g.display_name, '_method': 'PUT'}
      tmpl_context.form = edit_group_form
      return dict(title = u'Modification groupe ' + g.group_name, debug='', values=v)


   @validate(edit_group_form, error_handler=edit)
   @expose()
   def put(self, display_name, group_id):
      ''' Update group in DB
      '''
      log.info('update %d' % group_id)
      g = DBSession.query(Group).get(group_id)
      g.display_name = display_name
      flash(u'Groupe modifié')
      redirect('/groups/%d/edit' % group_id)


   @expose()
   def delete(self, id, **kw):
      ''' Delete group from DB
      '''
      log.info('delete ' + kw['_id'])
      DBSession.delete(DBSession.query(Group).get(kw['_id']))
      flash(u'Groupe supprimé', 'notice')
      redirect('/groups/')


