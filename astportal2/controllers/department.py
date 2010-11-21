# -*- coding: utf-8 -*-
# Department CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate
from tg.controllers import RestController

from repoze.what.predicates import in_group

from tw.jquery import FlexiGrid
from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField
from tw.forms.validators import NotEmpty, Int

from genshi import Markup

from astportal2.model import DBSession, Department, Phone

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
   action = 'create'
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
      phones = ', '.join([p.number for p in d.phones]) #()[:80] + '...'
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

   @expose(template="astportal2.templates.flexigrid")
   def get_all(self):
      ''' List all departments
      '''
      grid = FlexiGrid( id='flexi', fetchURL='fetch', title=None,
            sortname='name', sortorder='asc',
            colModel = [ { 'display': u'Action', 'width': 80, 'align': 'center' },
               { 'display': u'Nom court', 'name': 'name', 'width': 80 },
               { 'display': u'Nom complet', 'name': 'comment', 'width': 160 },
               { 'display': u'Téléphones', 'width': 160 } ],
            searchitems = [{'display': u'Nom', 'name': 'name'} ],
            buttons = [  {'name': u'Ajouter', 'bclass': 'add', 'onpress': js_callback('add')},
               {'separator': True} ],
            usepager=True,
            useRp=True,
            rp=10,
            resizable=False,
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des services', debug='')


   @expose('json')
   def fetch(self, page=1, rp=25, sortname='number', sortorder='asc',
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
         dptms = DBSession.query(Department).filter_by(**q)
      else:
         dptms = DBSession.query(Department)

      total = dptms.count()
      column = getattr(Department, sortname)
      dptms = dptms.order_by(getattr(column,sortorder)()).offset(offset).limit(rp)
      rows = [ { 'id'  : d.dptm_id, 'cell': row(d) } for d in dptms ]

      return dict(page=page, total=total, rows=rows)


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
      redirect('/departments/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete department from DB
      '''
      log.info('delete ' + kw['_id'])
      DBSession.delete(DBSession.query(Department).get(kw['_id']))
      flash(u'Service supprimé', 'notice')
      redirect('/departments/')


