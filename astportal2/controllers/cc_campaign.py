# -*- coding: utf-8 -*-
'''
Call center outgoing campaign
'''

from tg import expose, tmpl_context, validate, request, session, flash, redirect
from tg.controllers import RestController
from tgext.menu import sidebar
from repoze.what.predicates import in_any_group, not_anonymous
from tw.forms import TableForm, TextField, TextArea, CheckBox, \
         SingleSelectField, CalendarDateTimePicker, FileField, HiddenField
from tw.forms.validators import NotEmpty, Int, DateTimeConverter, \
         FieldStorageUploadConverter, Schema, Invalid
from tw.api import js_callback
from genshi import Markup

from astportal2.model import DBSession, Campaign, Customer
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

from datetime import datetime
import logging
log = logging.getLogger(__name__)

grid = MyJqGrid( 
   id='grid', url='fetch', caption=u'Campagnes',
   colNames = [u'Action', u'Nom', u'Active',
      u'Type', u'Utiliser'],
   colModel = [ 
      { 'width': 80, 'align': 'center', 'sortable': False, 'search': False },
      { 'name': 'name', 'width': 80 },
      { 'name': 'active', 'width': 160 },
      { 'name': 'type', 'width': 100,  },
      { 'name': 'Utiliser', 'width': 80,  },
   ],
   sortname = 'name',
   navbuttons_options = {'view': False, 'edit': False, 'add': True,
      'del': False, 'search': False, 'refresh': True, 
      'addfunc': js_callback('add'),
      }
)


cmp_types = ((-1, ' - - - '), (0, u'Commerciale'), 
   (1, u'Récurrente'), (2, u'\u00C9vénementielle'))

def row(c):
   '''Displays a formatted row of the campaigns list
   Parameter: Campaign object
   '''
   row = []
   action =  u'<a href="'+ str(c.cmp_id) + u'/edit" title="Modifier">'
   action += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   action += u'&nbsp;&nbsp;&nbsp;'
   action += u'<a href="#" onclick="del(\'%s\',\'%s\')" title="Supprimer">' % (str(c.cmp_id), u"Suppression de la campagne : " + c.name.replace("'","\\'"))
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'
   row.append(Markup(action))
   row.append(c.name)
   if c.active:
      if c.begin and c.end:
         row.append(u'Du %s au %s' %(
            c.begin.strftime('%d/%m/%y %H:%M'),
            c.end.strftime('%d/%m/%y %H:%M') ))
      elif c.begin:
         row.append(u'\u00C0 partir du %s' % c.begin.strftime('%d/%m/%y %H:%M'))
      elif c.end:
         row.append(u"Jusqu'au %s" % c.end.strftime('%d/%m/%y %H:%M'))
      else:
         row.append(u'Oui')
   else:
      row.append(u'Non')
   row.append(cmp_types[1+c.type][1])
   use = u'<a href="/cc_campaign/use?id=%d" title="Utiliser">Utiliser</a>' % c.cmp_id
   row.append(Markup(use))

   return row



def process_file(csv, cmp_id):

   # Check file
   filename = csv.filename
   filetype = csv.type
   filedata = csv.file
   log.debug('process_file: <%s> <%s> <%s>' % (filename, filetype, filedata))

   if filetype!='text/csv':
      return u'Le fichier doit être de type CSV !'

   # Temporarily save uploaded file
   tmp = open('/tmp/customer-%d.csv' % cmp_id, 'w')
   tmp.write(filedata.read())
   tmp.close()

   import re
   re_pri = re.compile(r'CLIPRI')
   re_com = re.compile(r'CLICOM')
   re_pro = re.compile(r'CLIPRO')

   # Then read it
   tmp = open('/tmp/customer-%d.csv' % cmp_id, 'U')
   lines = 0
   for l in tmp:
      lines += 1
      data = l.split(';')
      if lines==1: continue
      log.debug(data)
      c = Customer()
      c.cmp_id = cmp_id
      c.code = data[2].strip()
      c.gender = data[3].strip()
      c.lastname = data[4].strip()
      c.firstname = data[5].strip()
      if re_pri.search(data[6]):
         c.type = 0
      elif re_com.search(data[6]):
         c.type = 1
      elif re_pro.search(data[6]):
         c.type = 2
      c.phone1 = data[7].strip()
      c.phone2 = data[8].strip()
      c.phone3 = data[9].strip()
      c.phone4 = data[10].strip()
      c.phone5 = data[11].strip()
      c.email = data[12].strip()
      c.manager = data[13].strip()
      c.branch = data[14].strip()
      c.filename = filename
      DBSession.add(c)
   tmp.close()

   # remove uploaded file
#   unlink(tmp)


class Campaign_validate(Schema):
   def validate_python(self, value, state):
      # Check name is unique
      try:
         c = DBSession.query(Campaign).filter(Campaign.name==value['name']).one()
      except:
         return value
      if 'cmp_id' not in value.keys(): # New campaign
         log.debug('Campaign_validate new %d' % c.cmp_id)
         raise Invalid(
            u'Une campagne avec ce nom existe déjà, veuillez choisir un nom unique',
            value, state)
      elif c.cmp_id!=int(value['cmp_id']): # Edit existing campaign
         log.debug('Campaign_validate edit %d' % c.cmp_id)
         raise Invalid(
            u'Une campagne avec ce nom existe déjà, veuillez choisir un nom unique',
            value, state)
      return value


campaign_fields = [
      TextField('name', validator=NotEmpty,
         label_text = u'Nom', 
         help_text = u'Entrez le nom de la campagne'),
      TextArea('comment',
         label_text = u'Description', 
         help_text = u'Description de la campagne'),
      SingleSelectField('type',
         options = cmp_types,
         validator=Int(min=0, messages= {
            'tooLow': u'Veuillez choisir un type de campagne'}),
         label_text = u'Type de campagne', 
         help_text = u'Choisissez le type de campagne'),
      CheckBox('active', 
         label_text=u'Active', default=True,
         help_text=u'Cliquez pur activer la campagne'),
      CalendarDateTimePicker('begin',
         label_text=u'Début', help_text=u'Date de début',
         date_format =  '%d/%m/%y %Hh%mm',
         not_empty = False, picker_shows_time = True,
         validator = DateTimeConverter(format='%d/%m/%y %Hh%Mm',
            messages = {'badFormat': 'Format date / heure invalide'})),
      CalendarDateTimePicker('end',
         label_text=u'Fin', help_text=u'Date de fin',
         date_format =  '%d/%m/%y %Hh%mm',
         not_empty = False, picker_shows_time = True,
         validator = DateTimeConverter(format='%d/%m/%y %Hh%Mm',
            messages = {'badFormat': 'Format date / heure invalide'})),
      FileField('file', 
         validator=FieldStorageUploadConverter(),
         label_text=u'Fichier clients', 
         help_text=u'Fichier des clients au format CSV'),
      ]

cc_campaign_form = TableForm(
   validator = Campaign_validate,
   fields = campaign_fields,
   submit_text = u'Valider',
   action = '/cc_campaign/save',
   hover_help = True)

cc_campaign_edit_form = TableForm(
   validator = Campaign_validate,
   fields = campaign_fields + [HiddenField('_method', validator=None), 
      HiddenField('cmp_id')],
   submit_text = u'Modifier',
   action = '/cc_campaign/',
   hover_help = True)

class CC_Campaign_ctrl(RestController):

   allow_only = not_anonymous(
      msg=u'Veuiller vous connecter pour accéder à cette page')

   @sidebar(u"-- Groupes d'appels || Gestion campagnes", sortorder=14,
         icon = '/images/phonebook-small.jpg')
   @expose(template='astportal2.templates.grid')
   def get_all(self):
      ''' Display the list of existing campaigns
      '''

      # User must be admin or queue supervisor
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
      if not in_any_group(*sv):
         tmpl_context.grid = None
         flash(u'Accès interdit !', 'error')
      else:
         tmpl_context.grid = grid
      tmpl_context.form = None

      return dict(title=u"Liste des campagnes", debug='')


   @expose('json')
   def fetch(self, page, rows, sidx, sord, **kw):
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
         offset = (page-1) * int(rp)
      except:
         offset = 0
         page = 1
         rows = 25

      apps = DBSession.query(Campaign).filter(Campaign.deleted==None)
      total = apps.count()
      column = getattr(Campaign, sidx)
      apps = apps.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      rows = [ { 'id'  : a.cmp_id, 'cell': row(a) } for a in apps ]

      return dict(page=page, total=total, rows=rows)


   @expose(template='astportal2.templates.form_new')
   def new(self, name=None, comment=None, type=None,
         active=None, begin=None, end=None, file=None):
      ''' Display the list of existing campaigns
      '''

      tmpl_context.form = cc_campaign_form

      return dict(title=u"Liste des campagnes", debug='', values={})


   @expose()
   @validate(cc_campaign_form, error_handler=new)
   def save(self, name, comment, type, begin, end, file, active=None):

      log.debug('Save "%s"!' % file)

      c = Campaign()
      c.name = name
      c.comment = comment
      c.type = type
      c.active = active
      c.begin = begin
      c.end = end
      DBSession.add(c)
      DBSession.flush()
      log.debug(u'nouvelle campagne %s créée' % c.cmp_id)

      if file is not None:
         process_file(file, c.cmp_id)

      flash(u'Campagne "%s" créée' % name)
      redirect('/cc_campaign/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, cmp_id=None, **kw):
      ''' Display edit form
      '''
      if id is None: id = cmp_id
      c = DBSession.query(Campaign).get(id)
      v = dict(cmp_id=c.cmp_id, name=c.name, comment = c.comment, type = c.type,
         active = c.active, begin = c.begin, end = c.end, _method='PUT')
      tmpl_context.form = cc_campaign_edit_form
      return dict(title = u'Modification campagne', debug='', values=v)



   @expose()
   @validate(cc_campaign_edit_form, error_handler=edit)
   def put(self, name, comment, type, begin, end, file, cmp_id, active=None):

      log.debug('Save "%s"!' % file)

      c = DBSession.query(Campaign).get(cmp_id)
      c.name = name
      c.comment = comment
      c.type = type
      c.active = active
      c.begin = begin
      c.end = end
      DBSession.add(c)
      DBSession.flush()
      log.debug(u'nouvelle campagne %s créée' % c.cmp_id)

      if file is not None:
         process_file(file, c.cmp_id)

      flash(u'Campagne "%s" modifiée' % name)
      redirect('/cc_campaign/')


   @expose()
   def delete(self, id, _id):
      ''' Mark campaign as deleted
      '''
      a = DBSession.query(Campaign).get(int(_id))
      log.info(u'Mark campaign %s as deleted' % _id)
      a.deleted = datetime.now()

      flash(u'Campagne supprimée')
      redirect('/cc_campaign/')

