# -*- coding: utf-8 -*-
# Forward controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config
from tg.controllers import CUSTOM_CONTENT_TYPE
from tg.controllers import RestController
from tgext.menu import sidebar

from repoze.what.predicates import in_group, not_anonymous, in_any_group

from tw.api import js_callback
from tw.forms import TableForm, SingleSelectField, HiddenField, RadioButtonList
from tw.forms.validators import NotEmpty, Int

from genshi import Markup
from os import unlink, rename, chdir, listdir, stat
import logging
log = logging.getLogger(__name__)
import re
from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

from astportal2.model import DBSession, User, Phone
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

re_db = re.compile(r'(\w*)\s*: (\S*)')
cf_types = dict(CFIM = u'immédiat',
      CFUN = u'sur non réponse',
      CFBS = u'sur occupation')

new_forward_form = TableForm(
   'folder_form',
   name = 'folder_form',
   fields = [
      RadioButtonList('cf_types',
         options = [(k,v) for k,v in cf_types.iteritems()],
         label_text = u'Type de renvoi : ',
         help_text = u'Cochez le type de renvoi'),
      SingleSelectField('to_intern',
         label_text = u'Poste : ',
         options=DBSession.query(Phone.exten, Phone.exten).order_by(Phone.exten),
         help_text = u'Numéro interne'),
#            TextField('to_extern', label_text = u'Destination : ',
#               help_text = u'Numéro extérieur'),
      HiddenField('_method',validator=None), # Needed by RestController
   ],
   submit_text = u'Valider...',
   action = 'create',
   hover_help = True
)

def row(cf):
   '''Displays a formatted row of the voicemail list
   Parameter: call forward = (exten, type, dest)
   '''

   action = u'''<a href="#" onclick="del('%s', 'Suppression du renvoi %s')" title="Supprimer">''' % (
      '%s:%s:%s' % (cf[0], cf[1], cf[2]), 
      u'%s vers %s' % (cf_types[cf[1]], cf[2]))
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return (Markup(action), cf[0], cf_types[cf[1]], cf[2]) 


class Forward_ctrl(RestController):

   @sidebar(u"Renvois", sortorder=2,
      icon = '/images/edit-redo.png')
   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List call forwards
      '''

      grid = MyJqGrid( id='grid', url='fetch', 
            caption = u'Renvois',
            sortname='id', sortorder='asc',
            colNames = [u'Action', u'Extension',
               u'Renvoi', u'Vers' ],
            colModel = [ { 'width': 60, 'align': 'center', 'sortable': False },
               { 'name': 'exten', 'width': 60 },
               { 'name': 'type', 'width': 60 },
               { 'name': 'to', 'width': 100 },
               ],
            navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': False, 'refresh': True,
               'addfunc': js_callback('add')},
         )
      if not in_group('admin'): 
         grid.navbuttons_options['add'] = True
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u"Renvois", debug='', values='')


   @expose('json')
   def fetch(self, page=1, rows=10, sidx='mb', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data
      '''

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * rows
      except:
         offset = 0
         page = 1
         rows = 25

      u = DBSession.query(User). \
            filter(User.user_name==request.identity['repoze.who.userid']). \
            one()
      for phone in u.phone:
         exten = phone.exten

      cfs = []
      man = Globals.manager.command('database show CFIM')
      for i,r in enumerate(man.response[3:-2]):
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            if in_group('admin') or k==exten:
               cfs.append((k, 'CFIM', v))
      man = Globals.manager.command('database show CFBS')
      for i,r in enumerate(man.response[3:-2]):
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            if in_group('admin') or k==exten:
               cfs.append((k, 'CFBS', v))
      man = Globals.manager.command('database show CFUN')
      for i,r in enumerate(man.response[3:-2]):
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            if in_group('admin') or k==exten:
               cfs.append((k, 'CFUN', v))
      log.debug('Call forwards-> %s' % (cfs))

#      sort_key = lambda x : x[sidx]
      data = []
      total = 0
      for i, c in enumerate(cfs):
         data.append({'id'  : i, 'cell': row(c)})
         total += 1
 
      return dict(page=page, total=total, rows=data)

   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new user form
      '''
      tmpl_context.form = new_forward_form
      return dict(title = u'Nouveau renvoi', debug=None, values=None)


   @validate(new_forward_form, error_handler=new)
   @expose()
   def create(self, cf_types, to_intern):
      ''' Add call forward to Asterisk database
      '''
      u = DBSession.query(User). \
            filter(User.user_name==request.identity['repoze.who.userid']). \
            one()
      for phone in u.phone:
         exten = phone.exten
         man = Globals.manager.command('database put %s %s %s' % (
            cf_types, phone.exten, to_intern))
         log.debug('database put %s %s %s returns %s' % (
            cf_types, phone.exten, to_intern, man))
#      flash(u'Une erreur est survenue', 'error')
      redirect('/forward/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete call forward
      '''
      exten, cf, to = kw['_id'].split(':')
      log.info('delete %s %s %s' % (exten, cf, to))
      if in_group('admin'):
         man = Globals.manager.command('database del %s %s' % (
            cf, exten))
         log.debug('admin: database delete %s %s returns %s' % (
            cf_types, exten, man))

      else:
         u = DBSession.query(User). \
            filter(User.user_name==request.identity['repoze.who.userid']). \
            one()
         for phone in u.phone:
            man = Globals.manager.command('database del %s %s' % (
               cf, exten))
            log.debug('database delete %s %s returns %s' % (
               cf_types, exten, man))
#      flash(u'Une erreur est survenue', 'error')

      redirect('/forward/')


