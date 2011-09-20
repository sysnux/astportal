# -*- coding: utf-8 -*-
# Forward controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config, require
from tg.controllers import RestController
from tgext.menu import sidebar

from repoze.what.predicates import in_group, not_anonymous, in_any_group

from tw.api import js_callback
from tw.forms import TableForm, SingleSelectField, HiddenField, RadioButtonList, TextField, Label
from tw.forms.validators import NotEmpty, Int

from genshi import Markup
import logging
log = logging.getLogger(__name__)
import re
from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

from astportal2.model import DBSession, User, Phone, Department, Application
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

re_db = re.compile(r'(\w*)\s*: (\S*)')
cf_types = dict(CFIM = u'immédiat',
      CFUN = u'sur non réponse',
      CFBS = u'sur occupation',
      CFVM = u'messagerie vocale',
      )

class SRC_select(SingleSelectField):
   label_text = u'Poste à renvoyer'
   help_text = u'Sélectionnez le poste interne à renvoyer'

   def update_params(self,d):
      q = DBSession.query(Phone)
      if not in_group('admin'):
         dptm = [p.department.dptm_id for p in request.identity['user'].phone]
         q = q.filter(Phone.department_id.in_(dptm))
      q = q.order_by(Phone.exten)
      d['options'] = [(p.exten,p.exten) for p in q]
      SingleSelectField.update_params(self, d)
      return d
 
class DST_select(SingleSelectField):
   label_text = u'Destination'
   help_text = u'Sélectionnez le poste interne destination du renvoi'

   def update_params(self,d):
      opt_ext = [(p.exten,p.exten) for p in DBSession.query(Phone).order_by(Phone.exten)]
      if in_group('admin'):
         help_text = u'Sélectionnez le poste interne ou le SVI destination du renvoi'
         opt_ivr = [(a.exten,a.name) for a in DBSession.query(Application).order_by(Application.name)]
         d['options'] = [(u'Postes', opt_ext), (u'SVI', opt_ivr)]
      else:
         d['options'] = opt_ext
      SingleSelectField.update_params(self, d)
      return d

common_fields = [
      RadioButtonList('cf_types',
         options = [(k,v) for k,v in cf_types.iteritems()],
         label_text = u'Type de renvoi : ',
         help_text = u'Cochez le type de renvoi'),
      DST_select('to_intern'),
      HiddenField('_method',validator=None), # Needed by RestController
   ]

external_fields = []
external_fields.extend(common_fields)
external_fields.insert(1,
   Label( text = u'Choisissez la destination du renvoi poste interne ou numéro extérieur (prioritaire)'))
external_fields.append(
   TextField('to_extern', label_text = u'Numéro extérieur : ',
      help_text = u'Numéro extérieur'),
   )

cds_fields = []
cds_fields.extend(external_fields)
cds_fields.insert(0, SRC_select('exten'))

class Forward_form(TableForm):
   name = 'forward_form'
   fields = common_fields
   submit_text = u'Valider...'
   action = 'create_forward'
   hover_help = True
new_forward_form = Forward_form('new_forward_form')

class Forward_external_form(Forward_form):
   fields = external_fields
new_forward_external_form = Forward_external_form('new_forward_external_form')

class Forward_CDS_form(Forward_form):
   fields = cds_fields
   action = 'create_admin'
new_forward_cds_form = Forward_CDS_form('new_forward_cds_form')


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
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': False, 'refresh': True,
               'addfunc': js_callback('add')},
         )
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

      q = DBSession.query(Phone)
      if in_group('CDS'):
         dptm = [p.department.dptm_id for p in request.identity['user'].phone]
         q = q.filter(Phone.department_id.in_(dptm))

      elif not in_group('admin'):
         u = DBSession.query(User).get(request.identity['user'].user_id)
         q = q.filter(Phone.user_id==u.user_id)

      exten = [p.exten for p in q]

      cfs = []
      man = Globals.manager.command('database show CFIM')
      for i,r in enumerate(man.response[3:-2]):
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            if k in exten:
               cfs.append((k, 'CFIM', v))
      man = Globals.manager.command('database show CFBS')
      for i,r in enumerate(man.response[3:-2]):
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            if k in exten:
               cfs.append((k, 'CFBS', v))
      man = Globals.manager.command('database show CFUN')
      for i,r in enumerate(man.response[3:-2]):
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            if k in exten:
               cfs.append((k, 'CFUN', v))
      man = Globals.manager.command('database show CFVM')
      for i,r in enumerate(man.response[3:-2]):
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            if k in exten:
               cfs.append((k, 'CFVM', v))
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
      ''' Display new forward form
      '''

      if in_any_group('admin', 'CDS'):
         tmpl_context.form = new_forward_cds_form
         log.debug('admin / CDS -> tmpl_context.form = new_forward_CDS_form')

      elif in_group('Renvoi externe'):
         tmpl_context.form = new_forward_external_form
         log.debug('tmpl_context.form = new_forward_external_form')

      else:
         tmpl_context.form = new_forward_form
         log.debug('tmpl_context.form = new_forward_form')

      return dict(title = u'Nouveau renvoi', debug='', values=None)


   class forward_form_valid(object):
      def validate(self, params, state):
         log.debug(params)
         f = new_forward_external_form if in_group('Renvoi externe') \
            else new_forward_form
         return f.validate(params, state)

   @validate(forward_form_valid(), error_handler=new)
   @expose()
   def create_forward(self, cf_types, to_intern, to_extern=None, **kw):
      ''' Add call forward to Asterisk database
      '''
      log.debug('create_forward: %s %s %s' % (cf_types, to_intern, to_extern))
      dest = to_extern if to_extern else to_intern
      u = DBSession.query(User). \
            filter(User.user_name==request.identity['repoze.who.userid']). \
            one()
      for phone in u.phone:
         exten = phone.exten
         man = Globals.manager.command('database put %s %s %s' % (
            cf_types, phone.exten, dest))
         log.debug('database put %s %s %s returns %s' % (
            cf_types, phone.exten, dest, man))
#      flash(u'Une erreur est survenue', 'error')
      redirect('/forwards/')


   @require(in_any_group('admin', 'CDS',
      msg=u'Seul un membre du groupe administrateur peut créer ce renvoi'))
   @validate(new_forward_cds_form, error_handler=new)
   @expose()
   def create_admin(self, cf_types, exten, to_intern, to_extern):
      ''' Add call forward to Asterisk database
      '''
      dest = to_extern if to_extern else to_intern
      man = Globals.manager.command('database put %s %s %s' % (
         cf_types, exten, dest))
      log.debug('database put %s %s %s returns %s' % (
         cf_types, exten, dest, man))
#      flash(u'Une erreur est survenue', 'error')
      redirect('/forwards/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete call forward
      '''
      exten, cf, to = kw['_id'].split(':')
      log.info('delete %s %s %s' % (exten, cf, to))
      if in_any_group('admin', 'CDS'):
         man = Globals.manager.command('database del %s %s' % (
            cf, exten))
         log.debug('admin: database delete %s %s returns %s' % (
            cf_types, exten, man))

      else:
         u = DBSession.query(User).get(request.identity['user'].user_id)
         for p in u.phone:
            man = Globals.manager.command('database del %s %s' % (
               cf, p.exten))
            log.debug('database delete %s %s returns %s' % (
               cf, p.exten, man))
#      flash(u'Une erreur est survenue', 'error')

      redirect('/forwards/')


