# -*- coding: utf-8 -*-
# Department CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, session
from tg.controllers import RestController
from tgext.menu import sidebar

try:
   from tg.predicates import in_group
except ImportError:
   from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField
from tw.forms.validators import NotEmpty, Int

from genshi import Markup

from astportal2.model import DBSession, Department, Phone
from astportal2.lib.myjqgrid import MyJqGrid

import logging
log = logging.getLogger(__name__)


class New_dtpm_form(TableForm):
   ''' New department form
   '''
   fields = [
         TextField('name', validator=NotEmpty,
            label_text=u'Abrégé', help_text=u'Entrez le nom court du service'),
         TextField('comment', validator=NotEmpty,
            label_text=u'Nom complet', help_text=u'Entrez le nom complet du service'),
         ]
   submit_text = u'Valider...'
   action = '/departments/create'
   hover_help = True
new_dptm_form = New_dtpm_form('new_dptm_form')


class Edit_dptm_form(TableForm):
   ''' Edit department form
   '''
   fields = [
         TextField('comment', validator=NotEmpty,
            label_text=u'Nom complet', help_text=u'Entrez le nom complet du service'),
         HiddenField('_method', validator=None), # Needed by RestController
         HiddenField('dptm_id', validator=Int),
         ]
   submit_text = u'Valider...'
   action = '/departments/'
   hover_help = True
edit_dptm_form = Edit_dptm_form('edit_dptm_form')


def row(d):
   '''Displays a formatted row of the departments list
   Parameter: Department object
   '''
   if d.phones:
      phones = ', '.join([p.exten for p in d.phones]) #()[:80] + '...'
   else:
      phones = ''

   html =  u'<a href="'+ str(d.dptm_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   html += u'&nbsp;&nbsp;&nbsp;'
   html += u'<a href="#" onclick="del(\''+ str(d.dptm_id) + \
         u'\',\'Suppression du service ' + d.name + u'\')" title="Supprimer">'
   html += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(html), d.name, d.comment , phones]


class Dptm_ctrl(RestController):
   
   allow_only = in_group('admin', 
         msg=u'Vous devez appartenir au groupe "admin" pour gérer les services')

   @sidebar(u'-- Administration || Services',
      icon = '/images/view-catalog.png', sortorder = 13)
   @expose("genshi:astportal2.templates.grid")
   def get_all(self):
      ''' List all departments
      '''
      grid = MyJqGrid( 
            id='grid', url='fetch', caption=u'Services',
            colNames = [u'Action', u'Nom court', u'Nom complet', u'Téléphones',],
            colModel = [ 
               { 'width': 80, 'align': 'center', 'sortable': False, 'search': False },
               { 'display': u'Nom court', 'name': 'name', 'width': 80 },
               { 'display': u'Nom complet', 'name': 'comment', 'width': 160 },
               { 'display': u'Téléphones', 'width': 500, 'sortable': False, 'search': False }
            ],
            sortname = 'name',
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': True, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des services', debug='')


   @expose('json')
   def fetch(self, page, rows, sidx='user_name', sord='asc', _search='false',
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

      dptms = DBSession.query(Department)
      if  searchOper and searchField and searchString:
         log.debug('fetch query <%s> <%s> <%s>' % \
            (searchField, searchOper, searchString))
         try:
            field = eval('Department.' + searchField)
         except:
            field = None
            log.error('eval: Department.' + searchField)
         if field and searchOper=='eq': 
            dptms = dptms.filter(field==searchString)
         elif field and searchOper=='ne':
            dptms = dptms.filter(field!=searchString)
         elif field and searchOper=='le':
            dptms = dptms.filter(field<=searchString)
         elif field and searchOper=='lt':
            dptms = dptms.filter(field<searchString)
         elif field and searchOper=='ge':
            dptms = dptms.filter(field>=searchString)
         elif field and searchOper=='gt':
            dptms = dptms.filter(field>searchString)
         elif field and searchOper=='bw':
            dptms = dptms.filter(field.ilike(searchString + '%'))
         elif field and searchOper=='bn':
            dptms = dptms.filter(~field.ilike(searchString + '%'))
         elif field and searchOper=='ew':
            dptms = dptms.filter(field.ilike('%' + searchString))
         elif field and searchOper=='en':
            dptms = dptms.filter(~field.ilike('%' + searchString))
         elif field and searchOper=='cn':
            dptms = dptms.filter(field.ilike('%' + searchString + '%'))
         elif field and searchOper=='nc':
            dptms = dptms.filter(~field.ilike('%' + searchString + '%'))
         elif field and searchOper=='in':
            dptms = dptms.filter(field.in_(str(searchString.split(' '))))
         elif field and searchOper=='ni':
            dptms = dptms.filter(~field.in_(str(searchString.split(' '))))

      total = dptms.count()/rows + 1
      column = getattr(Department, sidx)
      dptms = dptms.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      data = [ { 'id'  : d.dptm_id, 'cell': row(d) } for d in dptms ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new department form
      '''
      tmpl_context.form = new_dptm_form
      return dict(title = u'Nouveau service', debug='', values='')
      
   @validate(new_dptm_form, error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new department to DB
      '''
      d = Department()
      d.name = kw['name']
      d.comment = kw['comment']
      DBSession.add(d)
      flash(u'Nouveau service "%s" créé' % (kw['name']))
      redirect('/departments/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit department form
      '''
      if not id: id = kw['dptm_id']
      d = DBSession.query(Department).get(id)
      v = {'dptm_id': d.dptm_id, 'comment': d.comment, '_method': 'PUT'}
      tmpl_context.form = edit_dptm_form
      return dict(title = u'Modification service ' + d.name, debug='', values=v)


   @validate(edit_dptm_form, error_handler=edit)
   @expose()
   def put(self, dptm_id, comment):
      ''' Update department in DB
      '''
      log.info('update %d' % dptm_id)
      d = DBSession.query(Department).get(dptm_id)
      d.comment = comment
      flash(u'Service modifié')
      redirect('/departments/%d/edit' % dptm_id)


   @expose()
   def delete(self, id, **kw):
      ''' Delete department from DB
      '''
      log.info('delete ' + kw['_id'])
      DBSession.delete(DBSession.query(Department).get(kw['_id']))
      flash(u'Service supprimé', 'notice')
      redirect('/departments/')


