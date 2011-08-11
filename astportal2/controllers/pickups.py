# -*- coding: utf-8 -*-
# Pickup CReate / Update RESTful controller
# Pickups cannot be deleted
# Asterisk supports 64 pickup groups (0-63)

from tg import expose, flash, redirect, tmpl_context, validate, config
from tg.controllers import RestController
from tgext.menu import sidebar

from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, Label, TextField, HiddenField
from tw.forms.validators import NotEmpty, Int

from genshi import Markup

from astportal2.model import DBSession, Pickup, Phone
from astportal2.lib.myjqgrid import MyJqGrid

import logging
log = logging.getLogger(__name__)


class Pickup_form(TableForm):
   ''' Pickup form
   '''
   fields = [
      TextField('name', validator=NotEmpty,
         label_text=u'Nom', help_text=u'Entrez le nom du groupe d\'interception'),
      TextField('comment', validator=NotEmpty,
         label_text=u'Descriptif', help_text=u'Entrez le descriptif du groupe d\'appel'),
      HiddenField('_method',validator=None), # Needed by RestController
      HiddenField('pickup_id',validator=Int),
   ]
   submit_text = u'Valider...'
   hover_help = True


class New_pickup_form(Pickup_form):
   ''' Pickup form
   '''
   action = 'create'
new_pickup_form = New_pickup_form('new_pickup_form')


class Edit_pickup_form(Pickup_form):
   ''' Pickup form
   '''
   action = '/pickups'
edit_pickup_form = Edit_pickup_form('edit_pickup_form')


def row(p, callgroups, pickupgroups):
   '''Displays a formatted row of the pickups list
   Parameter: Pickup object
   '''

   html =  u'<a href="'+ str(p.pickup_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'

   return [Markup(html), p.name, p.comment, ', '.join(callgroups), 
         ', '.join(pickupgroups) ]


class Pickup_ctrl(RestController):
   
   allow_only = in_group('admin', 
         msg=u'Vous devez appartenir au groupe "admin" pour gérer les services')

   @sidebar(u'-- Administration || Groupes d\'interception',
      icon = '/images/kdf.png', sortorder = 16)
   @expose("genshi:astportal2.templates.grid")
   def get_all(self):
      ''' List all pickups
      '''
      grid = MyJqGrid( 
            id='grid', url='fetch', caption=u'Groupes d\'interception',
            colNames = [u'Action', u'Nom', u'Description', u'Appels', u'Interception'],
            colModel = [ 
               { 'width': 80, 'align': 'center', 'sortable': False, 'search': False },
               { 'name': 'name', 'width': 80 },
               { 'name': 'comment', 'width': 160 },
               { 'width': 160, 'sortable': False, 'search': False },
               { 'width': 160, 'sortable': False, 'search': False },
            ],
            sortname = 'name',
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': False, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des groupes d\'interception', debug='')


   @expose('json')
   def fetch(self, page=1, rows=10, sidx='user_name', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by Grid JS component
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

      pickup = DBSession.query(Pickup)
      total = pickup.count()/rows + 1
      column = getattr(Pickup, sidx)
      pickup = pickup.order_by(getattr(column,sord)()).offset(offset).limit(rows)

      # Find phones belonging to call / pickup groups
      callgroups  = [[] for x in xrange(64)]
      pickupgroups  = [[] for x in xrange(64)]
      for f in DBSession.query(Phone):
         if f.callgroups:
            try:
               for g in f.callgroups.split(','):
                  callgroups[int(g)].append(f.exten)
            except:
               callgroups[int(g)].append(f.exten)
            try:
              for g in f.pickupgroups.split(','):
                  pickupgroups[int(g)].append(f.exten)
            except:
               pickupgroups[int(g)].append(f.exten)

      data = [ { 'id'  : p.pickup_id, \
            'cell': row(p, callgroups[p.pickup_id], pickupgroups[p.pickup_id]) 
            } for p in pickup ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new pickup form
      '''
      tmpl_context.form = new_pickup_form
      return dict(title = u'Nouveau groupe d\'interception', debug='', values='')
      
   @validate(new_pickup_form, error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new pickup to DB
      '''
      p = Pickup()
      p.name = kw['name']
      p.comment = kw['comment']
      DBSession.add(p)

      flash(u'Nouveau groupe d\'interception "%s" créé' % (kw['name']))
      redirect('/pickups/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit pickup form
      '''
      if not id: id = kw['pickup_id']
      p = DBSession.query(Pickup).get(id)
      v = {'pickup_id': p.pickup_id, 'name': p.name, 
            'comment': p.comment, '_method': 'PUT'}
      tmpl_context.form = edit_pickup_form
      return dict(title = u'Modification groupe d\'interception ' + p.name, debug='', values=v)


   @validate(edit_pickup_form, error_handler=edit)
   @expose()
   def put(self, pickup_id, **kw):
      ''' Update pickup in DB
      '''
      log.info('update %d' % pickup_id)
      p = DBSession.query(Pickup).get(pickup_id)
      p.name = kw['name']
      p.comment = kw['comment']
      flash(u'Groupe d\'interception modifié')

      redirect('/pickups/')

