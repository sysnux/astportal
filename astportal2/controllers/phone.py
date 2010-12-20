# -*- coding: utf-8 -*-
# Phone CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, require
from tg.controllers import RestController

from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField
from tw.forms.validators import NotEmpty, Int

from genshi import Markup

from astportal2.model import DBSession, Phone, Department, User
from astportal2.lib.myjqgrid import MyJqGrid

import logging
log = logging.getLogger(__name__)


class New_phone_form(TableForm):
   ''' New phone form
   '''
   fields = [
         TextField('number', validator=NotEmpty,
            label_text=u'Numéro', help_text=u'Entrez le numéro du téléphone'),
         SingleSelectField('dptm_id',
            options=DBSession.query(Department.dptm_id, 
               Department.comment).order_by(Department.comment),
            label_text=u'Service', help_text=u'Service facturé'),
         SingleSelectField('user_id',
            options=DBSession.query(User.user_id, 
               User.display_name).order_by(User.display_name),
            label_text=u'Utilisateur', help_text=u'Utilisateur du téléphone'),
         ]
   submit_text = u'Valider...'
   action = 'create'
   hover_help = True
new_phone_form = New_phone_form('new_form_phone')


class Edit_phone_form(TableForm):
   ''' Edit phone form
   '''
   fields = [
         SingleSelectField('dptm_id', 
            options= DBSession.query(Department.dptm_id, 
               Department.comment).order_by(Department.comment),
            label_text=u'Service', help_text=u'Service facturé',
            valdator=Int
            ),
         SingleSelectField('user_id',
            options=DBSession.query(User.user_id, User.display_name).
            order_by(User.display_name),
            label_text=u'Utilisateur', help_text=u'Utilisateur du téléphone',
            validator=Int
            ),
         HiddenField('_method', validator=None), # Needed by RestController
         HiddenField('phone_id', validator=Int),
         ]
   submit_text = u'Valider...'
   action = '/phones/'
   hover_help = True
edit_phone_form = Edit_phone_form('edit_form_phone')


def row(p):
   '''Displays a formatted row of the phones list
   Parameter: Phone object
   '''
   if p.user:
      user = p.user.display_name
   else:
      user = ''

   html =  u'<a href="'+ str(p.phone_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   html += u'&nbsp;&nbsp;&nbsp;'
   html += u'<a href="#" onclick="del(\''+ str(p.phone_id) + \
         u'\',\'Suppression du téléphone ' + str(p.number) + u'\')" title="Supprimer">'
   html += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(html), p.number, user , p.department.name]


class Phone_ctrl(RestController):
   
   allow_only = in_group('admin', 
         msg=u'Vous devez appartenir au groupe "admin" pour gérer les téléphones')

   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all phones
      '''
      grid = MyJqGrid( id='grid', url='fetch', caption=u'Téléphones',
            sortname='number',
            colNames = [u'Action', u'Numéro', u'Utilisateur', u'Service'],
            colModel = [ 
               { 'display': u'Action', 'width': 80, 'align': 'center', 'search': False },
               { 'name': 'number', 'width': 80 },
               { 'name': 'user_id', 'width': 160, 'search': False },
               { 'name': 'department_id', 'width': 160, 'search': False } ],
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': True, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des téléphones', debug='')


   @expose('json')
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut afficher la liste des utilisateurs'))
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

      phones = DBSession.query(Phone)
      if  searchOper and searchField and searchString:
         log.debug('fetch query <%s> <%s> <%s>' % \
            (searchField, searchOper, searchString))
         try:
            field = eval('Phone.' + searchField)
         except:
            field = None
            log.error('eval: Phone.' + searchField)
         if field and searchOper=='eq': 
            phones = phones.filter(field==searchString)
         elif field and searchOper=='ne':
            phones = phones.filter(field!=searchString)
         elif field and searchOper=='le':
            phones = phones.filter(field<=searchString)
         elif field and searchOper=='lt':
            phones = phones.filter(field<searchString)
         elif field and searchOper=='ge':
            phones = phones.filter(field>=searchString)
         elif field and searchOper=='gt':
            phones = phones.filter(field>searchString)
         elif field and searchOper=='bw':
            phones = phones.filter(field.ilike(searchString + '%'))
         elif field and searchOper=='bn':
            phones = phones.filter(~field.ilike(searchString + '%'))
         elif field and searchOper=='ew':
            phones = phones.filter(field.ilike('%' + searchString))
         elif field and searchOper=='en':
            phones = phones.filter(~field.ilike('%' + searchString))
         elif field and searchOper=='cn':
            phones = phones.filter(field.ilike('%' + searchString + '%'))
         elif field and searchOper=='nc':
            phones = phones.filter(~field.ilike('%' + searchString + '%'))
         elif field and searchOper=='in':
            phones = phones.filter(field.in_(str(searchString.split(' '))))
         elif field and searchOper=='ni':
            phones = phones.filter(~field.in_(str(searchString.split(' '))))

      total = phones.count()/rows + 1
      column = getattr(Phone, sidx)
      phones = phones.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      data = [ { 'id'  : p.phone_id, 'cell': row(p) } for p in phones ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new phone form
      '''
      tmpl_context.form = new_phone_form
      return dict(title = u'Nouveau téléphone', debug='', values='')
      
   @validate(new_phone_form, error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new phone to DB
      '''
      p = Phone()
      p.number = kw['number']
      p.department_id = kw['dptm_id']
      p.user_id = kw['user_id']
      DBSession.add(p)
      flash(u'Nouveau téléphone "%s" créé' % (kw['number']))
      redirect('/phones/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit phone form
      '''
      if not id: id=kw['phone_id']
      p = DBSession.query(Phone).get(id)
      v = {'phone_id': p.phone_id, 'dptm_id': p.department_id, 'user_id': p.user_id, '_method': 'PUT'}
      tmpl_context.form = edit_phone_form
      return dict(title = u'Modification téléphone ' + p.number, debug='', values=v)


   @validate(edit_phone_form, error_handler=new)
   @expose()
   def put(self, phone_id, dptm_id, user_id):
      ''' Update phone in DB
      '''
      log.info('update %d' % phone_id)
      p = DBSession.query(Phone).get(phone_id)
      p.department_id = dptm_id
      p.user_id = user_id
      flash(u'Téléphone modifié')
      redirect('/phones/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete phone from DB
      '''
      log.info('delete ' + kw['_id'])
      DBSession.delete(DBSession.query(Phone).get(kw['_id']))
      flash(u'Téléphone supprimé', 'notice')
      redirect('/phones/')


