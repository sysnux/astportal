# -*- coding: utf-8 -*-
'''
Call center outgoing campaign
'''

from tg import expose, tmpl_context, validate, request, session, flash, \
   redirect, response
from tg.controllers import RestController
from tgext.menu import sidebar
try:
   from tg.predicates import in_group, not_anonymous, in_any_group
except ImportError:
   from repoze.what.predicates import in_group, not_anonymous, in_any_group
from tw.forms import TableForm, TextField, TextArea, CheckBox, \
         SingleSelectField, CalendarDateTimePicker, FileField, HiddenField
from tw.forms.validators import NotEmpty, Int, DateTimeConverter, \
         FieldStorageUploadConverter, Schema, Invalid
from tw.api import js_callback
from astportal2.lib.app_globals import Markup

from astportal2.model import DBSession, Campaign, Customer, Outcall
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

from sqlalchemy import desc, func, sql, types, outerjoin, extract, and_

from datetime import datetime
from time import time
import logging
log = logging.getLogger(__name__)

import StringIO
import csv
import re
re_pri = re.compile(r'CLIPRI')
re_com = re.compile(r'CLICOM')
re_pro = re.compile(r'CLIPRO')

grid = MyJqGrid( 
   id='grid', url='fetch', caption=u'Campagnes',
   colNames = [u'Action', u'Nom', u'Active', u'Type', u'Statistiques'],
   colModel = [ 
      { 'width': 80, 'align': 'center', 'sortable': False, 'search': False },
      { 'name': 'name', 'width': 80 },
      { 'name': 'active', 'width': 160 },
      { 'name': 'type', 'width': 100,  },
      { 'name': 'stats', 'width': 100,  'sortable': False, 'search': False },
   ],
   sortname = 'name',
   navbuttons_options = {'view': False, 'edit': False, 'add': True,
      'del': False, 'search': False, 'refresh': True, 
      'addfunc': js_callback('add'),
      }
)


cmp_types = ((-1, ' - - - '), (0, u'Commerciale'), 
   (1, u'Récurrente'), (2, u'\u00C9vénementielle'))

def percent(n, t):
   if t==0: return '-'
   r = 100*n/t
   return  u'%d %%' % r

def stats_compute(cmp_id):
      p = DBSession.query(Campaign).get(cmp_id)

      members = dict()
      total = dict(tot=0, answ=0, no_answ=0, 
         r0=0, r1=0, r2=0, r3=0, r4=0, r5=0, r6=0, r7=0, 
         r8=0, r9=0, r10=0, r11=0, r12=0)

      # Compute totals, global and by member
      for c in p.customers: # For all customers in this campaign
         for o in c.outcalls: # For all calls to these customers
            total['tot'] += 1
            if o.user.display_name not in members.keys():
               members[o.user.display_name] = dict(tot=0, answ=0, no_answ=0, 
                  r0=0, r1=0, r2=0, r3=0, r4=0, r5=0, r6=0, r7=0, 
                  r8=0, r9=0, r10=0, r11=0, r12=0)
            if o.result is None:
               log.warning('stats_fetch: "None" result for outcall "%d"' % o.out_id)
               continue
            total['r%d' % o.result] += 1
            members[o.user.display_name]['r%d' % o.result] += 1
            members[o.user.display_name]['tot'] += 1
            if o.result in (0, 1, 2, 3, 4, 5): 
               total['answ'] += 1
               members[o.user.display_name]['answ'] += 1
            elif o.result in (6, 7, 8, 9): 
               total['no_answ'] += 1
               members[o.user.display_name]['no_answ'] += 1
#      log.debug(members)

      return members, total


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
   row.append(Markup(
      u'''<a href="/cc_campaign/stats?cmp_id=%d" 
      title="Afficher les statistiques de cette campagne">Afficher</a>''' % c.cmp_id))

   return row


def line2data(l):

   # Guess encoding
   for enc in ('windows-1252', 'iso-8859-15', 'utf-8'):
      try:
         l = l.decode(enc)
         break
      except:
         pass

   data = []
   # Split and cleanup line -> data
   for d in l.split(';'):
      d = d.strip()
      data.append(d if d!='' else None)

   return data


def process_file(csv, cmp_id):

   # Check file
   filename = csv.filename
   filetype = csv.type
   filedata = csv.file
   log.debug('process_file: <%s> <%s> <%s>' % (filename, filetype, filedata))

   if filetype not in ('text/csv', 'application/csv', 'application/vnd.ms-excel'):
      log.warning('process_file: not CSV : <%s> <%s> <%s>' % (
         filename, filetype, filedata))
      return 0, 0, u'Le fichier doit être de type CSV !'

   # Temporarily save uploaded file
   tmpfn = '/tmp/customer-%d-%d.csv' % (cmp_id, int(time()))
   tmp = open(tmpfn, 'w')
   tmp.write(filedata.read())
   tmp.close()

   # Then read it
   tmp = open(tmpfn, 'U')
   lines = errors = 0
   for l in tmp:
      lines += 1
      if lines==1: continue
      data = line2data(l)
      if len(data)!=10:
         log.warning('process_file: invalid data %s' % data)
         errors += 1
         continue
      c = Customer()
      c.cmp_id = cmp_id
      c.active = True
      c.code = data[0]
      c.gender = data[1]
      c.lastname = data[2]
      c.firstname = data[3]
      c.phone1 = data[4]
      c.phone2 = data[5]
      c.phone3 = data[6]
      c.phone4 = data[7]
      c.phone5 = data[8]
      c.email = data[9]
      c.filename = filename
      DBSession.add(c)
   tmp.close()

   # remove uploaded file
#   unlink(tmp)
   return lines, errors, ''


class Campaign_validate(Schema):
   def _validate_python(self, value, state):
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
   action = '/cc_campaign/save')
#   hover_help = True)

cc_campaign_edit_form = TableForm(
   validator = Campaign_validate,
   fields = campaign_fields + [HiddenField('_method', validator=None), 
      HiddenField('cmp_id')],
   submit_text = u'Modifier',
   action = '/cc_campaign/')
#   hover_help = True)

class CC_Campaign_ctrl(RestController):

   allow_only = not_anonymous(
      msg=u'Veuiller vous connecter pour accéder à cette page')

   @sidebar(u"-- Groupes d'appels || Gestion campagnes", sortorder=14,
         icon = '/images/megaphone-prefs.png')
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
         offset = (page-1) * int(rows)
      except:
         offset = 0
         page = 1
         rows = 25

      apps = DBSession.query(Campaign).filter(Campaign.deleted==None)
      total = 1 + apps.count() / rows
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

      msg = u'Campagne "%s" créée' % name
      if file is not None:
         l, e, m = process_file(file, c.cmp_id)
         if l==0:
            msg += m
         else:
            msg += u', %d lignes intégrées' % l
            if e!=0:
               msg += u', %d erreurs' % e

      flash(msg)
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
      log.debug(u'nouvelle campagne %s modifiée' % c.cmp_id)

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


   @expose(template='astportal2.templates.grid_cc_campaign_stats')
   def stats(self, cmp_id):

      p = DBSession.query(Campaign).get(cmp_id)

      # User must be admin or queue supervisor
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
      if not in_any_group(*sv):
         tmpl_context.grid = None
         flash(u'Accès interdit !', 'error')
      else:
         tmpl_context.grid = MyJqGrid(
            id='grid', url='stats_fetch', caption=u'Statitiques',
            colNames = [
               u'Agent', 
               u'RDV', 
               u'\u00C0 rappeler', 
               u'Contact direct. son CC / réflechit',
               u'Pas intéressé coupe court',
               u'Appels aboutis', 
               u'Absent',
               u'Décédé',
               u'Faux numéro/ Aucun numéro',
               u'Injoi- gnable',
               u'Appels non aboutis', 
               u'Hors cible',
               u'Réclam.',
               u'Total fiches clients traitées'],
            colModel = [
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
               { 'width': 40, 'sortable': False, 'search': False },
            ],
            #   sortname = 'name',
            postData = {'cmp_id': cmp_id},
            navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': False, 'refresh': True, 
            }
         )

      first = datetime(2222, 12, 31)
      last = datetime(2000, 1, 1)
      for c in p.customers: # For all customers in this campaign
         for o in c.outcalls: # For all calls to these customers
            if first > o.created: first = o.created
            if last < o.created: last = o.created
      tmpl_context.form = None

      return dict(title=u"Statistiques campagne %s" % p.name, 
         debug='', 
         csv_href = {'href': 'csv?cmp_id=%s' % cmp_id},
         first_last=u'Premier appel %s, dernier appel %s.' % (
            first.strftime('%A %d %B %Y à %Hh%Mm%Ss').decode('utf-8'), 
            last.strftime('%A %d %B %Y à %Hh%Mm%Ss').decode('utf-8')))


   @expose('json')
   def stats_fetch(self, cmp_id, page, rows, sidx, sord, **kw):

      # User must be admin or queue supervisor
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
      if not in_any_group(*sv):
         tmpl_context.grid = None
         flash(u'Accès interdit !', 'error')
         return ''

      members, total = stats_compute(cmp_id)
      rows = []

      # Create a row for each member
      for k,v in members.iteritems():
         rows.append({ 'id'  : k, 'cell': [
            k, 
            u'%d (%s)' % (v['r0'], 
               percent(v['r0'], total['r0'])), # RDV
            u'%d (%s)' % ( v['r1'] + v['r2'] + v['r3'],
               percent(v['r1'] + v['r2'] + v['r3'],
               total['r1']+total['r2']+total['r3'])), # A rappeler
            u'%d (%s)' % (v['r4'], 
               percent(v['r4'], total['r4'])),  # Contact direct CC
            u'%d (%s)' % (v['r5'], 
               percent(v['r5'], total['r5'])), # Pas intéressé
            u'%d (%s)' % (v['answ'], 
               percent(v['answ'], total['answ'])), # Total appels aboutis
            u'%d (%s)' % (v['r6'], 
               percent(v['r6'], total['r6'])), # Absent
            u'%d (%s)' % (v['r7'], 
               percent(v['r7'], total['r7'])), # Décédé
            u'%d (%s)' % (v['r8'], 
               percent(v['r8'], total['r8'])), # Faux numéro / Aucun numéro
            u'%d (%s)' % (v['r9'], 
               percent(v['r9'], total['r9'])), # Injoignable
            u'%d (%s)' % (v['no_answ'], 
               percent(v['no_answ'], total['no_answ'])), # Total appels non aboutis
            u'%d (%s)' % (v['r10'], 
               percent(v['r10'], total['r10'])), # Hors cible
            u'%d (%s)' % (v['r11'], 
               percent(v['r11'], total['r11'])), # Réclamation
            u'%d (%s)' % (v['tot'], 
               percent(v['tot'], total['tot'])), # Total Fiches clients traitées
         ]})

      # Add global
      rows.append({ 'id'  : 'total', 'cell': [
         Markup(u'<em>Total</em>'), 
         Markup(u'<em>%d</em>' % total['r0']), # RDV
         Markup(u'<em>%d</em>' % (
            total['r1'] + total['r2'] + total['r3'])), # A rappeler
         Markup(u'<em>%d</em>' % total['r4']),  # Contact direct CC
         Markup(u'<em>%d</em>' % total['r5']), # Pas intéressé
         Markup(u'<em>%d</em>' % total['answ']), # Total appels aboutis
         Markup(u'<em>%d</em>' % total['r6']), # Absent
         Markup(u'<em>%d</em>' % total['r7']), # Décédé
         Markup(u'<em>%d</em>' % total['r8']), # Faux numéro / Aucun numéro
         Markup(u'<em>%d</em>' % total['r9']), # Injoignable
         Markup(u'<em>%d</em>' % total['no_answ']), # Total appels non aboutis
         Markup(u'<em>%d</em>' % total['r10']), # Hors cible
         Markup(u'<em>%d</em>' % total['r11']), # Réclamation
         Markup(u'<em>%d</em>' % total['tot']), # Total Fiches clients traitées
      ]})
      return dict(page=page, total=1, rows=rows)


   @expose()
   def csv(self, cmp_id):

      # User must be admin or queue supervisor
      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
      if not in_any_group(*sv):
         tmpl_context.grid = None
         flash(u'Accès interdit !', 'error')
         return ''

      csvdata = StringIO.StringIO()
      writer = csv.writer(csvdata)

      p = DBSession.query(Campaign).get(cmp_id)

      # File name + write header
      today = datetime.today()
      name = p.name
      filename = 'statistiques-campagne-%s-%s.csv' % (name.replace(' ', '_'),
         today.strftime('%Y%m%d-%H%M%S'))
      writer.writerow(('Campagne', name.encode('utf-8')))
      writer.writerow(('Statistiques au', today.strftime('%d/%m/%Y-%Hh%Mh%Ss')))
      writer.writerow(())
      colnames = ((-1, u'Agent'),
         (0, u'RDV Call Center'),
         (1, u'\u00C0 rappeler'),
         (2, u'\u00C0 rappeler une deuxième fois'),
         (3, u'Dernier rappel'),
         (4, u'Contacte directement son cc/réfléchi'),
         (5, u'Pas intéressé / coupe court'),
         (6, u'Absent pendant la campagne'),
         (7, u'Décédé'),
         (8, u'Faux numéro / Aucun numéro'),
         (9, u'Injoignable'),
         (10, u'Hors cible'),
         (11, u'Réclamation'))
      writer.writerow([c[1].encode('utf-8') for c in colnames])

      members, total = stats_compute(cmp_id)
      # Write CSV data
      for k,v in members.iteritems():
         writer.writerow([k, v['r0'], v['r1'], v['r2'], v['r3'], v['r4'], 
            v['r5'], v['r6'], v['r7'], v['r8'], v['r9'], v['r10'], v['r11']])

      rh = response.headers
      rh['Content-Type'] = 'text/csv; charset=utf-8'
      rh['Content-Disposition'] = str( (u'attachment; filename="%s"' % (
         filename)).encode('utf-8') )
      rh['Pragma'] = 'public' # for IE
      rh['Cache-Control'] = 'max-age=0' #for IE

      return csvdata.getvalue()
