# -*- coding: utf-8 -*-
# Holidays CReate / Update RESTful controller

from tg import expose, flash, redirect, tmpl_context, validate, config, session
from tg.controllers import RestController
from tgext.menu import sidebar

from repoze.what.predicates import in_any_group

from tw.api import js_callback
from tw.forms import TableForm, Label, TextField, HiddenField, CalendarDatePicker
from tw.forms.validators import NotEmpty, Int, DateTimeConverter

from genshi import Markup

from astportal2.model import DBSession, Holiday
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

from sqlalchemy import desc

import datetime
import logging
log = logging.getLogger(__name__)

directory_asterisk = config.get('directory.asterisk')


def update_extensions():
   '''Generate Asterisk holiday context:

[holidays]
exten => s,1,Set(holiday=false)
exten => s,n,GotoIfTime(*,*,d,m?true)
exten => s,n,GotoIfTime(*,*,d,m?true)
exten => s,n,return
exten => s,n(true),Set(holiday=true)
exten => s,n,return
   '''

   # Create list of actions
   actions = [
      ('NewCat', 'holidays'),
      ('Append', 'holidays', 'exten', '>s,1,Set(holiday=false)')
   ]
   for h in DBSession.query(Holiday).order_by(Holiday.month, Holiday.day):
      actions.append(('Append', 'holidays', 'exten',
         '>s,n,GotoIfTime(*,*,%d,%d?true)' % (h.day, h.month)))

   actions.append(('Append', 'holidays', 'exten', '>s,n,return'))
   actions.append(('Append', 'holidays', 'exten',
      '>s,n(true),Set(holiday=true)'))
   actions.append(('Append', 'holidays', 'exten', '>s,n,return'))
   

   # ... Now really update (delete + add)
   Globals.manager.update_config(directory_asterisk  + 'extensions.conf', 
         None, [('DelCat', 'holidays')])
   res = Globals.manager.update_config(directory_asterisk + 'extensions.conf', 
         None, actions)
   log.debug('Update extensions.conf returns %s' % res)

   # Allways reload dialplan
   Globals.manager.send_action({'Action': 'Command',
      'Command': 'dialplan reload'})


class Holiday_form(TableForm):
   ''' Holiday form
   '''
   fields = [
      TextField('name', validator=NotEmpty,
         label_text=u'Nom', help_text=u'Entrez le jour férié'),
      CalendarDatePicker('date',
         attrs = {'readonly': True, 'size': 8},
         date_format = '%d/%m',
         validator = DateTimeConverter(format="%d/%m", not_empty=True),
         default = '',
         label_text=u'Date',
         calendar_lang = 'fr',
         button_text=u'Choisir...'),
      HiddenField('holiday_id',validator=Int),
   ]
   submit_text = u'Valider...'
   hover_help = True


class New_holiday_form(Holiday_form):
   ''' Holiday form
   '''
   action = '/holidays/create'
new_holiday_form = New_holiday_form('new_holiday_form')


class Edit_holiday_form(Holiday_form):
   ''' Holiday form
   '''
   fields = Holiday_form.fields + [
      HiddenField('_method',validator=None)] # Needed by RestController
   action = '/holidays'
edit_holiday_form = Edit_holiday_form('edit_holiday_form')


def row(h):
   '''Displays a formatted row of the holhtml list
   Parameter: Holiday object
   '''

   html =  u'<a href="'+ str(h.holiday_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   html += u'&nbsp;&nbsp;&nbsp;'
   html += u'<a href="#" onclick="del(\''+ str(h.holiday_id) + \
         u'\',\'Suppression de ' + h.name + '\')" title="Supprimer">'
   html += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   m = [ u'Janvier', u'Février', u'Mars', u'Avril', u'Mai', u'Juin', 
      u'Juillet', u'Août', u'Septembre', u'Octobre', u'Novembre', 
      u'Décembre' ][h.month-1]

   return [Markup(html), h.name, '%d %s' % (h.day , m)]


class Holiday_ctrl(RestController):
   
   allow_only = in_any_group('admin', u'Fériés',
         msg=u'Vous devez appartenir au groupe "Fériés" pour gérer les jours fériés')

   @sidebar(u'-- Administration || Jours fériés',
      icon = '/images/view-calendar-journal.png', sortorder = 16)
   @expose("genshi:astportal2.templates.grid")
   def get_all(self):
      ''' List all holidays
      '''
      grid = MyJqGrid( 
            id='grid', url='fetch', caption=u'Jours fériés',
            colNames = [u'Action', u'Nom', u'Date'],
            colModel = [ 
               { 'width': 80, 'align': 'center', 'sortable': False, 
               'search': False },
               { 'name': 'name', 'width': 80 },
               { 'name': 'date', 'width': 60 },
            ],
            sortname = 'date',
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': False, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des jours fériés', debug='')


   @expose('json')
   def fetch(self, page, rows, sidx='date', sord='asc', _search='false',
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

      holiday = DBSession.query(Holiday)
      total = holiday.count()/rows + 1
      if sidx=='date':
         holiday = holiday.order_by(Holiday.month, Holiday.day) if sord!='desc' \
               else holiday.order_by(desc(Holiday.month), desc(Holiday.day))
      else:
         holiday = holiday.order_by(Holiday.name) if sord!='desc' \
               else holiday.order_by(desc(Holiday.name))
      holiday = holiday.offset(offset).limit(rows)

      data = [ { 'id'  : h.holiday_id, 'cell': row(h) 
            } for h in holiday ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display create holiday form
      '''
      tmpl_context.form = new_holiday_form
      return dict(title = u'Nouveau jour férié', debug='', values='')
      
   @validate(new_holiday_form, error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new holiday to DB
      '''
      h = Holiday()
      h.name = kw['name']
      h.day = kw['date'].day
      h.month = kw['date'].month
      DBSession.add(h)
      update_extensions()
      flash(u'Nouveau jour férié "%s" créé' % (kw['name']))
      redirect('/holidays/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit holiday form
      '''
      if not id: id = kw['holiday_id']
      h = DBSession.query(Holiday).get(id)
      v = {'holiday_id': h.holiday_id, 'name': h.name, 
            'date': datetime.date(datetime.date.today().year, h.month, h.day),
            '_method': 'PUT'}
      tmpl_context.form = edit_holiday_form
      return dict(title = u'Modification groupe jour férié ' + h.name, debug='', values=v)


   @validate(edit_holiday_form, error_handler=edit)
   @expose()
   def put(self, holiday_id, **kw):
      ''' Update holiday in DB
      '''
      log.info('update %d' % holiday_id)
      h = DBSession.query(Holiday).get(holiday_id)
      h.name = kw['name']
      h.day = kw['date'].day
      h.month = kw['date'].month
      update_extensions()
      flash(u'Jour férié modifié')
      redirect('/holidays/%d/edit' % holiday_id)

   @expose()
   def delete(self, id, **kw):
      ''' Delete holiday from DB
      '''
      log.info('delete ' + kw['_id'])
      DBSession.delete(DBSession.query(Holiday).get(kw['_id']))
      update_extensions()
      flash(u'Jour férié supprimé', 'notice')
      redirect('/holidays/')

