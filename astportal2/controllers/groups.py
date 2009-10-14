# -*- coding: utf-8 -*-
# Group CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate
from tg.controllers import RestController

from repoze.what.predicates import in_group

from tw.jquery import FlexiGrid
from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField
from tw.forms.validators import NotEmpty

from genshi import Markup

from astportal2.model import DBSession, Group, User


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
   action = 'create'
   hover_help = True
new_group_form = New_group_form('new_group_form')


class Edit_group_form(TableForm):
   ''' Edit group form
   '''
   fields = [
         TextField('display_name', validator=NotEmpty,
            label_text='Descriptif', help_text=u'Entrez un descriptif du groupe'),
         HiddenField('_method'), # Needed by RestController
         HiddenField('group_id'),
         ]
   submit_text = u'Valider...'
   action = '/groups/'
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
   html += u'&nbsp;&nbsp;&nbsp;'
   html += u'<a href="#" onclick="del(\''+ str(g.group_id) + \
         u'\',\'Suppression du groupe ' + str(g.group_name) + u'\')" title="Supprimer">'
   html += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(html), g.group_name, g.display_name , users]


class Group_ctrl(RestController):
   
#   allow_only = in_group('admin', 
#         msg=u'Vous devez appartenir au groupe "admin" pour gérer les groupes')

   @expose(template="astportal2.templates.flexigrid")
   def get_all(self):
      ''' List all groups
      '''
      grid = FlexiGrid( id='flexi', fetchURL='fetch', title=None,
            sortname='group_name', sortorder='asc',
            colModel = [ { 'display': u'Action', 'width': 80, 'align': 'center' },
               { 'display': u'Nom', 'name': 'group_name', 'width': 80 },
               { 'display': u'Description', 'name': 'display_name', 'width': 160 },
               { 'display': u'Utilisateurs', 'width': 160 } ],
            searchitems = [{'display': u'Nom', 'name': 'group_name'} ],
            buttons = [ {'name': u'Ajouter', 'bclass': 'add', 'onpress': js_callback('add')},
               {'separator': True} ],
            usepager=True,
            useRp=True,
            rp=10,
            resizable=False,
            )
      tmpl_context.grid = grid
      return dict( title=u'Liste des groupes', debug='', form='')


   @expose('json')
   def fetch(self, page=1, rp=25, sortname='group_name', sortorder='asc',
         qtype=None, query=None):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      try:
         page = int(page)
         offset = (page-1) * int(rp)
      except:
         offset = 0
         page = 1
         rp = 25

      if (query):
         q = {str(qtype): query}
         groups = DBSession.query(Group).filter_by(**q)
      else:
         groups = DBSession.query(Group)

      total = groups.count()
      column = getattr(Group, sortname)
      groups = groups.order_by(getattr(column,sortorder)()).offset(offset).limit(rp)
      rows = [ { 'id'  : g.group_id, 'cell': row(g) } for g in groups ]

      return dict(page=page, total=total, rows=rows)


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
   def edit(self, id, **kw):
      ''' Display edit group form
      '''
      g = DBSession.query(Group).get(id)
      v = {'group_id': g.group_id, 'display_name': g.display_name, '_method': 'PUT'}
      tmpl_context.form = edit_group_form
      return dict(title = u'Modification groupe ' + g.group_name, debug='', values=v)


   @validate(edit_group_form, error_handler=new)
   @expose()
   def put(self, **kw):
      ''' Update group in DB
      '''
      g = DBSession.query(Group).get(kw['group_id'])
      g.display_name = kw['display_name']
      flash(u'Groupe modifié')
      redirect('/groups/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete group from DB
      '''
      DBSession.delete(DBSession.query(Group).get(id))
      flash(u'Groupe supprimé', 'notice')
      redirect('/groups/')


