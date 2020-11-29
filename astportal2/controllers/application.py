# -*- coding: utf-8 -*-
# Application CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, \
   response, session, config
from tg.controllers import RestController
from tgext.menu import sidebar

try:
   from tg.predicates import in_group, not_anonymous
except ImportError:
   from repoze.what.predicates import in_group, not_anonymous

from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, \
   HiddenField, CheckBox, CalendarDateTimePicker, TextArea
from tw.forms.validators import NotEmpty, Int, DateConverter, DateTimeConverter

from astportal2.lib.app_globals import Markup

from astportal2.model import DBSession, Application, User, Group, Action, \
   Scenario, Sound, User, Queue, Queue_event
from astportal2.lib.asterisk import asterisk_string

from datetime import datetime
import re
from os import rename, system, fsync
from tempfile import mkdtemp

import logging
log = logging.getLogger(__name__)

dir_monitor = config.get('directory.monitor')

def play_or_tts(typ, val, brk=None):
   ''' Choose Playback / Background or RealSpeak 
   Return app, param
   '''
   if typ=='s':
# XXX      if val not in application.sounds:
# XXX         application.sounds.append(DBSession.query(Sound).get(val))
      s = DBSession.query(Sound).get(val)
      name = 'astportal/%s' % s.name if s is not None else 'beep'
      if brk is not None:
         app = u'Background'
         param = u'%s' % (name)
      else:
         app = u'Playback'
         param = u'%s' % (name)

   elif typ=='t':
# XXX      if val not in application.texts:
# XXX         application.texts.append(DBSession.query(Text).get(val))
      app = u'RealSpeak'
      txt = DBSession.query(Text).get(val)
      param = u'%s' % (txt.text.replace(',','\,'))
      if brk is not None:
         param += u',%s' % (brk)

   return (app, param)


# Dynamic select of users(user_id,display_name) of group 'SVI'
class SVI_user_select_field(SingleSelectField):
   def update_params(self,sf):
      svi = DBSession.query(Group).filter(Group.group_name=='SVI').one()
      sf['options'] = [(u.user_id, u.display_name) for u in svi.users]
      SingleSelectField.update_params(self, sf)
      return sf


# Common fields for application form
common_fields = [
   TextField('exten', not_empty=False, #validator=None,
      label_text=u'Numéro interne'),
# help_text=u'Choisissez l\'extension'),
   TextField('dnis', not_empty=False, #validator=None,
      label_text=u'Numéro extérieur'),
# help_text=u'Choisissez le numéro RNIS'),
   TextField('exten', not_empty=False, #validator=None,
      label_text=u'Numéro interne'),
# help_text=u'Choisissez le numéro interne'),
   CheckBox('active', 
      label_text=u'Active', default=True),
#      help_text=u'Application active'),
   CalendarDateTimePicker('app_begin',
      label_text=u'Début',
#      help_text=u'Date de début',
      date_format =  '%d/%m/%y %Hh%Mm',
      not_empty = False, picker_shows_time = True,
      validator = DateTimeConverter(format='%d/%m/%y %Hh%Mm',
         messages = {'badFormat': 'Format date / heure invalide'})),
   CalendarDateTimePicker('app_end',
      label_text=u'Fin',
# help_text=u'Date de fin',
      date_format =  '%d/%m/%y %Hh%Mm',
      not_empty = False, picker_shows_time = True,
      validator = DateTimeConverter(format='%d/%m/%y %Hh%Mm',
         messages = {'badFormat': 'Format date / heure invalide'})),
   TextArea('comment',
      label_text=u'Commentaires'),
# help_text=u"Description de l'application"),
#         HiddenField('_method', validator=None), # Needed by RestController
   HiddenField('app_id', validator=Int),
         ]

# New application form
new_fields = common_fields[:]
new_fields[0:1] = [
   TextField('name', validator=NotEmpty,
      label_text=u'Nom'),
# help_text=u"Entrez le nom de l'application"),
]
new_application_form = TableForm(
   fields = new_fields,
   submit_text = u'Valider...',
   action = '/applications/create',
#   hover_help = True
   )

# Edit application form
edit_fields = common_fields[:]
edit_fields[0:1] = [
   HiddenField('_method', validator=None), # Needed by RestController
]
edit_application_form = TableForm(
   fields = edit_fields,
   submit_text = u'Valider...',
   action = '/applications/',
#   hover_help = True
   )

def row(a):
   '''Displays a formatted row of the applications list
   Parameter: Application object
   '''
   row = []
   if a.owner_id:
      user = a.owner_id #.display_name
   else:
      user = ''

   action =  u'<a href="'+ str(a.app_id) + u'/edit" title="Modifier">'
   action += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   action += u'&nbsp;&nbsp;&nbsp;'
   action += u'<a href="#" onclick="del(\'%s\',\'%s\')" title="Supprimer">' % (str(a.app_id), u"Suppression de l\\'application: " + a.name.replace("'","\\'"))
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'
   row.append(Markup(action))
   row.append(a.name)
   row.append(a.exten)
   row.append(a.dnis)
   if a.active:
      if a.begin and a.end:
         row.append(u'Du %s au %s' %(
            a.begin.strftime('%d/%m/%y %H:%M'),
            a.end.strftime('%d/%m/%y %H:%M') ))
      elif a.begin:
         row.append(u'\u00C0 partir du %s' % a.begin.strftime('%d/%m/%y %H:%M'))
      elif a.end:
         row.append(u"Jusqu'au %s" % a.end.strftime('%d/%m/%y %H:%M'))
      else:
         row.append(u'Oui')
   else:
      row.append(u'Non')
   scenario = u'<a href="/applications/scenario?id=%d" title="Scénario">Scénario</a>' %a.app_id
   row.append(Markup(scenario))
# XXX   if in_group('admin'): row.append(user)

   return row


class Application_ctrl(RestController):
   
   allow_only = in_group('admin', 
      msg=u'Vous devez appartenir au groupe "admin" pour gérer les applications')

   @sidebar(u'-- Administration || Applications (SVI)', sortorder = 12,
      icon = '/images/code-class.png',
      permission = in_group('admin'))
   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all applications
      '''

      grid = MyJqGrid( id='grid', url='fetch', caption='Applications (SVI)',
         sortname='name', sortorder='asc',
         colNames = [u'Action', u'Application', u'Extension', 
            u'Numéro', u'Active', u'Scenario'],
         colModel = [ 
            { 'width': 60, 'align': 'center', 'sortable': False },
            { 'name': 'name', 'width': 120 },
            { 'name': 'exten', 'width': 40 },
            { 'name': 'dnis', 'width': 40 },
            { 'name': 'active', 'width': 280 },
            { 'display': u'Scénario', 'width': 60, 'sortable': False } ],
         navbuttons_options = {'view': False, 'edit': False, 'add': True,
            'del': False, 'search': False, 'refresh': True, 
            'addfunc': js_callback('add'), }
      )

      tmpl_context.grid = grid
      tmpl_context.form = None

      return dict( title=u'Liste des applications', debug='')


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

      apps = DBSession.query(Application)
      total = apps.count()
      column = getattr(Application, sidx)
      apps = apps.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      rows = [ { 'id'  : a.app_id, 'cell': row(a) } for a in apps ]

      return dict(page=page, total=total, rows=rows)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new application form
      '''
      tmpl_context.form = new_application_form
      return dict(title = u'Nouvelle application', debug='', values='')
      
   class new_form_valid(object):
      def validate(self, params, state):
         f = new_application_form
         return f.validate(params, state)

   @validate(new_form_valid(), error_handler=new)
   @expose()
   def create(self, name, exten, dnis, comment, app_begin=None, app_end=None,
         active=True, owner_id=None, **kw):
      ''' Add new application  and initial dialplan to DB
      '''
      a = Application()
      a.name = name
      a.exten = exten
      a.dnis = dnis
      a.active = active
      a.begin = app_begin
      a.end = app_end
      a.comment = comment
      a.created_by = request.identity['user'].user_id
      if owner_id:
         a.owner_id = owner_id
      else:
         a.owner_id = request.identity['user'].user_id

      # Try to insert file in DB: might fail if name already exists
      try:
         DBSession.add(a)
         DBSession.flush()
      except:
         log.error(u'Insert failed %s' % a)
         flash(u"Impossible de créer l'application (vérifier son nom)", 'error')
         redirect('/applications/')

      s = Scenario()
      s.app_id = a.app_id
      s.context = 'Entrant'
      s.extension = 's'
      s.step = 1
      s.action = 0
      s.parameters = None
      DBSession.add(s)

      flash(u'Nouvelle application "%s" créée' % (name))
      redirect('/applications/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id, **kw):
      ''' Display edit application form
      '''
      a = DBSession.query(Application).get(id)
      v = {'app_id': a.app_id, 'exten': a.exten, 'dnis': a.dnis, 
            'owner_id': a.owner_id, 'active': a.active, 
            'app_begin': a.begin, 'app_end': a.end,
            'comment': a.comment, '_method': 'PUT', 'old_number': a.exten}

      tmpl_context.form = edit_application_form
      return dict(title = u'Modification application ' + a.name, debug='', values=v)


   class application_form_valid(object):
      def validate(self, params, state):
         log.debug(params)
         f = edit_application_form
         return f.validate(params, state)

   @validate(application_form_valid(), error_handler=edit)
   @expose()
   def put(self, **kw):
      ''' Update application in DB
      '''
      a = DBSession.query(Application).get(kw['app_id'])

      if 'exten' in kw.keys():
         a.exten = kw['exten']
      if 'dnis' in kw.keys():
         a.dnis = kw['dnis']
      a.active = kw['active']
      a.begin = kw['app_begin']
      a.end = kw['app_end']
      a.comment = kw['comment']
      result = generate_dialplan()
      if result==0:
         flash(u'Application modifiée')
      else:
         flash(u'Modification application', error)
      redirect('/applications/%s/edit' % kw['app_id'])


   @expose()
   def delete(self, id, **kw):
      ''' Delete application from DB
      '''
      id = int(kw['_id'])
      a = DBSession.query(Application).get(id)
      log.info(u'Delete application %d' % id)

      # 1. Delete scenario
      DBSession.query(Scenario).filter(Scenario.app_id==a.app_id).delete()

      # 2. Delete application
      DBSession.delete(a)

      # 3. Recreate extensions
      result = generate_dialplan()
      if result==0:
         flash(u'Application supprimée')
      else:
         flash(u'Application supprimée',error)
      redirect('/applications/')

   @expose(template="astportal2.templates.scenario")
   def scenario(self, id):
      ''' List scenario for given application
      '''
      a = DBSession.query(Application).get(id)
      tmpl_context.app_id = id
      return dict( title=u'Scénario de l\'application "%s"' % a.name, debug='')


   @expose('json')
   def fetch_scenario(self, id, page=1, rp=25, sortname='name', sortorder='asc',
         qtype=None, query=None):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      actions = [{'action_id': x.action_id, 'action_name': x.name, 
         'action_comment': x.comment}
         for x in DBSession.query(Action).order_by(Action.name)]

      owner = '' # DBSession.query(Application.owner_id).get(id)[0]

      sounds = [{'sound_id': x.sound_id, 'sound_name': x.name, 
         'sound_comment': x.comment}
         for x in DBSession.query(Sound). \
            filter(Sound.type==1).order_by(Sound.name)]

      texts = []

      queues = [{'queue_id': x.queue_id, 'queue_name': x.name, 
                 'queue_comment': x.comment}
                 for x in DBSession.query(Queue).order_by(Queue.name)]

      qevents = [{'qe_id': x.qe_id, 'event': x.event}
         for x in DBSession.query(Queue_event).order_by(Queue_event.event)]

      applications = dict((x.app_id, {'name': x.name, 'comment': x.comment})
                           for x in DBSession.query(Application).order_by(Application.name))
      log.debug('fetch_scenario applications=%s', applications)

      scenario = []
      positions = {}
      for x in DBSession.query(Scenario).filter(Scenario.app_id==id).order_by(Scenario.context).order_by(Scenario.step):
         scenario.append({'sce_id': x.sce_id, 'context': x.context, 
         'extension': x.extension, 'priority': x.step, 
         'application': x.action, 'parameters': x.parameters, 
         'comments': x.comments, 'target': 0})
         if x.top and x.left:
            context = 'context_' + x.context
            positions[context] = {'top': x.top, 'left': x.left}

      return dict(scenario=scenario, sounds=sounds, texts=texts, 
            actions=actions, queues=queues, qevents=qevents,
            positions=positions, applications=applications)


   @expose('json')
   def save_scenario(self, id, **kw):

      if kw.has_key('scenario[]'):
         scenario = kw['scenario[]']
      else:
         log.error(u'No scenario to save ???')
         scenario = None
         return dict(result=0) # XXX ?

      positions = {}
      if type(kw['positions[]'])!=type([]):
         kw['positions[]'] = (kw['positions[]'],)
      for p in kw['positions[]']:
         log.debug(p)
         (context, top, left) = p.split('::')
         positions[context] = (int(float(top)), int(float(left)))


      log.info('save_scenario %s, type %s' % (id, type(scenario)) )
      application = DBSession.query(Application).get(int(id))

      # 1. Delete old entries
      DBSession.query(Scenario).filter(Scenario.app_id==int(id)).delete()

      # 2. Create new ones
      if scenario:
         if type(scenario)!=type([]):
            scenario = (scenario,)
         for s in scenario:
            sc = Scenario()
            (c, i, e, p, a, m) = s.split('::',5)
            p = (1+int(p))
            (sc.comments, sc.app_id, sc.context, sc.extension, sc.step, sc.action, 
               sc.parameters) = (c, id, i, e, p, a, m)
            if p==1 :
               i = 'context_%s' % i 
               log.debug(u'position %s', i)
               if i in positions.keys():
                  sc.top = positions[i][0]
                  sc.left = positions[i][1]
            DBSession.add(sc)

      return dict(result=generate_dialplan())


   @expose()
   def pdf_export(self, id, **kw):

      app = DBSession.query(Application).get(id)
      log.info('pdf_export: id=%s' % (id))

      action_by_id = {}
      for a in DBSession.query(Action):
         action_by_id[a.action_id] = asterisk_string(a.name)

      prev_context = None
      nodes = []
      edges = []
      label = []
      for s in DBSession.query(Scenario).filter(Scenario.app_id==id). \
            order_by(Scenario.context).order_by(Scenario.step):

         if prev_context is None: # First loop
            log.debug(' * * * First context')
            prev_context = s.context

         elif prev_context!=s.context: # Next context
            log.debug(' * * * Write context %s' % prev_context)
            nodes.append(mk_label(label, action_by_id))
            label = []
            prev_context = s.context

         edges += mk_edges(s)
         label.append(s)

      log.debug(' * * * Write last %s' % prev_context)
      nodes.append(mk_label(label, action_by_id))

      dir_tmp = mkdtemp()
      dot = open(dir_tmp + '/graphviz.dot', 'w')
      dot.write('digraph g {\n')
      for n in nodes:
         dot.write(asterisk_string(n))
      log.debug('edges: %s' % edges)
      for e in edges:
         dot.write(asterisk_string(e))
      dot.write('}\n')
      dot.close()

      fn = '%s/%s.pdf' % (dir_tmp, app.name)
      from pygraphviz import AGraph
      g = AGraph(dir_tmp + '/graphviz.dot')
      log.debug(' * * * AGraph encoding %s' % g.encoding)
      g.layout(prog='dot')
      g.draw(fn)

      import os
      try:
         st = os.stat(fn)
         f = open(fn)
      except:
         flash(u'Erreur à la génération du fichier PDF', 'error')
         redirect('')
      rh = response.headers
      rh['Pragma'] = 'public' # for IE
      rh['Expires'] = '0'
      rh['Cache-control'] = 'must-revalidate, post-check=0, pre-check=0' #for IE
      rh['Cache-control'] = 'max-age=0' # for IE
      rh['Content-Type'] = 'application/pdf'
      rh['Content-Disposition'] = str( (u'attachment; filename="%s.pdf"; size=%d;' % (
         app.name, st.st_size)).encode('utf-8') )
      rh['Content-Transfer-Encoding'] = 'binary'
      return f.read()


def generate_dialplan():
   ''' Generate dialplan from database
   '''

   # Flush SqlAlchemy session, else we might generate dialplan with stale data
   DBSession.flush()

   # Check / acquire exclusive lock on file
   # XXX fcntl.lockf

   # 3. Generate dialplan
   import codecs
   svi_out = codecs.open('/etc/asterisk/astportal/svi.conf.new',
         mode='w', encoding='iso-8859-1')
   now = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
   svi_out.write(u';!\n;! Dialplan generated automatically, manual changes will be lost !\n;! %s\n;!\n\n' % now)
 
   # Main context: check active + date, setup accountcode + userfield, then
   # route called number (RNIS) to application
   svi_out.write(u'[SVI_dnis] ; Main context RNIS -> App\n')
   apps = DBSession.query(Application)
   apps = apps.filter(Application.active==True)
   apps = apps.order_by(Application.exten)
   for a in apps:
      if a.dnis is None:
         continue
      dnis = u'exten => %s' % a.dnis[-4:]
      app_id = a.app_id
      name = a.name
      begin = a.begin
      end = a.end
      exten = a.exten

      svi_out.write(u'; %s (App %d)\n' % (name, app_id))
      svi_out.write(u'%s,1,Noop(%s: %s)\n' % (dnis, name, exten))
      if begin:
         svi_out.write(u'%s,n,GotoIf($[ 0%s < ${STRFTIME(,,%%s)} ]?test_end)\n' % (
            dnis, begin.strftime('%s') ))
         svi_out.write(u'%s,n,Hangup()\n' % dnis)
      if end:
         svi_out.write(u'%s,n(test_end),GotoIf($[ 0${STRFTIME(,,%%s)} < %s ]?ok)\n' % (
            dnis, end.strftime('%s') ))
         svi_out.write(u'%s,n,Hangup()\n' % dnis)
      else:
         svi_out.write(u'%s,n(test_end),Noop(No end)\n' % dnis)
      svi_out.write(u'%s,n(ok),Wait(1)\n' % dnis)
      svi_out.write(u'%s,n,Set(CHANNEL(language)=${MASTER_CHANNEL(CHANNEL(language))})\n' % dnis)
      svi_out.write(u'%s,n,Set(CHANNEL(accountcode)=%s)\n' % (dnis, app_id))
      svi_out.write(u'%s,n,Set(CDR(userfield)=SVI)\n' % dnis)
      svi_out.write(u'%s,n,Goto(App_%s_Entrant,s,1)\n' % (dnis, app_id))
   svi_out.write(u'\n')

   # Internal context: same as above
   svi_out.write(u'[SVI_internal] ; Internal context -> App\n')
   apps = DBSession.query(Application)
   apps = apps.filter(Application.active==True)
   apps = apps.order_by(Application.exten)
   for a in apps:
      if a.exten is None:
         continue
      dnis = u'exten => %s' % a.exten
      app_id = a.app_id
      name = a.name
      begin = a.begin
      end = a.end
      exten = a.exten

      svi_out.write(u'; %s (App %d)\n' % (name, app_id))
      svi_out.write(u'%s,1,Noop(%s: %s)\n' % (dnis, name, exten))
      if begin:
         svi_out.write(u'%s,n,GotoIf($[ 0%s < ${STRFTIME(,,%%s)} ]?test_end)\n' % (
            dnis, begin.strftime('%s') ))
         svi_out.write(u'%s,n,Hangup()\n' % dnis)
      if end:
         svi_out.write(u'%s,n(test_end),GotoIf($[ 0${STRFTIME(,,%%s)} < %s ]?ok)\n' % (
            dnis, end.strftime('%s') ))
         svi_out.write(u'%s,n,Hangup()\n' % dnis)
      else:
         svi_out.write(u'%s,n(test_end),Noop(No end)\n' % dnis)
      svi_out.write(u'%s,n(ok),Wait(1)\n' % dnis)
      svi_out.write(u'%s,n,Set(CHANNEL(language)=${MASTER_CHANNEL(CHANNEL(language))})\n' % dnis)
      svi_out.write(u'%s,n,Set(CHANNEL(accountcode)=%s)\n' % (dnis, app_id))
      svi_out.write(u'%s,n,Set(CDR(userfield)=SVI)\n' % dnis)
      svi_out.write(u'%s,n,Goto(App_%s_Entrant,s,1)\n' % (dnis, app_id))
   svi_out.write(u'\n')

   # Create contexts, priorities, ... from database
   prev_ctxt = ''
   return_ok = True # Is it ok to return when context ends
   for dp in DBSession.query(Scenario, Application) \
                      .filter(Scenario.app_id == Application.app_id) \
                      .filter(Application.active) \
                      .order_by(Scenario.app_id) \
                      .order_by(Scenario.context) \
                      .order_by(Scenario.step):
      sce_id = int(dp.Scenario.sce_id)
      action = int(dp.Scenario.action)
      app_id = int(dp.Scenario.app_id)
      context = dp.Scenario.context
      parameters = dp.Scenario.parameters
      log.info('App %s, scenario %s: %s, %s(%s)', app_id, sce_id, context, action, parameters)

      ctxt = u'[App_%s_%s]\n' % (app_id, context)
      if prev_ctxt!=ctxt:
         if prev_ctxt!='' and return_ok: svi_out.write(u'exten => s,%d,Return\n\n' % prio)
         svi_out.write(ctxt)
         prio=1
         prev_ctxt = ctxt
         return_ok = True

      if action==0: # 'NoOp'
         app = u'NoOp'
         param = u''

      elif action==1: # Playback
         (app, param) = play_or_tts(parameters[0], int(parameters[2:]))

      elif action==2: # Menu
         next = 'App_%s_%s' % (app_id, context)
         param = parameters.split('::')
         cpt = 'svi_cpt_%s_%d' % (context, prio)
         svi_out.write(u'exten => s,%d,Set(%s=0)\n' % (prio, cpt))
         prio +=1
         tag = prio
         svi_out.write(u'exten => s,%d(a_%d),Set(%s=$[1 + ${%s}])\n' % (
            prio, tag, cpt, cpt))
         prio +=1
         svi_out.write(u'exten => s,%d,GotoIf($[ 0${%s} > 3 ]?e_%d,1)\n' % (
            prio, cpt, tag))
         prio +=1
         log.debug('Background ? (%s, %s, %s)' % (param[0][0], int(param[0][2:]), param[3]))
         (a, p) = play_or_tts(param[0][0], int(param[0][2:]), param[3])
         svi_out.write(u'exten => s,%d,%s(%s)\n' % (prio, a, p))
         prio +=1
         svi_out.write(u'exten => s,%d,WaitExten\n' % prio)
         prio +=1
         (a, p) = play_or_tts(param[1][0], int(param[1][2:]))
         svi_out.write(u'exten => i,1,%s(%s)\n' % (a, p))
         svi_out.write(u'exten => i,2,Goto(s,a_%d)\n' % (tag))
         svi_out.write(u'exten => t,1,Goto(s,a_%d)\n' % (tag))
         if param[2]=='-2': # Continue
            svi_out.write(u'exten => e_%d,1,Goto(s,%d)\n' % (tag, prio))
         else:
            (a, p) = play_or_tts(param[2][0], int(param[2][2:]))
            svi_out.write(u'exten => e_%d,1,%s(%s)\n' % (tag,a, p))
            svi_out.write(u'exten => e_%d,2,Hangup\n' % tag)
         for c in param[3]:
            svi_out.write(u'exten => %c,1,Goto(%s_Menu_${EXTEN},s,1)\n' % (c, next))
         return_ok = False # Don't return after "Menu" else timeout is never executed.
         continue

      elif action==15: # Choice
         param = parameters.split('::')
         cpt = 'svi_cpt_%s_%d' % (context, prio)
         svi_out.write(u'exten => s,%d,Set(%s=0)\n' % (prio, cpt))
         prio +=1
         tag = prio
         svi_out.write(u'exten => s,%d(a_%d),Set(%s=$[1 + ${%s}])\n' % (prio, tag, cpt, cpt))
         prio +=1
         svi_out.write(u'exten => s,%d,GotoIf($[ 0${%s} > 3 ]?e_%d,1)\n' % (prio, cpt, tag))
         prio +=1
         (a, p) = play_or_tts(param[0][0], int(param[0][2:]))
         #svi_out.write(u'exten => s,%d,%s(%s,%s)\n' % (prio, a, p, param[3]))
         svi_out.write(u'exten => s,%d,%s(%s)\n' % (prio, a, p))
         prio +=1
         svi_out.write(u'exten => s,%d,AGI(astportal/readvar.agi,,%s,1,%s)\n' % (prio, param[4], param[3]))
         (a, p) = play_or_tts(param[1][0], int(param[1][2:]))
         svi_out.write(u'exten => i_%d,1,%s(%s)\n' % (prio, a, p))
         svi_out.write(u'exten => i_%d,2,Goto(s,a_%d)\n' % (prio, tag))
         svi_out.write(u'exten => t_%d,1,Goto(s,a_%d)\n' % (prio, tag))
         (a, p) = play_or_tts(param[2][0], int(param[2][2:]))
         svi_out.write(u'exten => e_%d,1,%s(%s)\n' % (tag, a, p))
         svi_out.write(u'exten => e_%d,2,Hangup\n' % tag)
         prio +=1
         svi_out.write(u'exten => s,%d,Noop(Choice=${%s})\n' % (prio, param[4]))
         prio +=1
         continue

      elif action==3: # Input
         # Params: msg_sound, error_sound, abandon_sound, variable, type, len
         if context=='Entrant': next = 'App_%s_' % app_id
         else: next = 'App_%s_%s_' % (app_id, context)
         param = parameters.split('::')
         log.debug('Input: param=%s', param)
         cpt = 'svi_cpt_%s_%d' % (context, prio)
         svi_out.write(u'exten => s,%d,Set(%s=0)\n' % (prio, cpt))
         prio +=1
         tag = prio
         svi_out.write(u'exten => s,%d(a_%d),Set(%s=$[1 + ${%s}])\n' % (tag, prio, cpt, cpt))
         prio +=1
         svi_out.write(u'exten => s,%d,GotoIf($[ 0${%s} > 3 ]?e_%d,1)\n' % (prio, cpt, tag))
         prio +=1
         (a, p) = play_or_tts(param[0][0], int(param[0][2:]))
         if a == 'RealSpeak':
            svi_out.write(u'exten => s,%d,%s(%s)\n' % (prio, a, p))
            sound_file = ''
         else:
            svi_out.write(u'exten => s,%d,Answer()\n' % (prio))
            sound_file = p
         prio +=1
         if param[4]=='fixed':
            svi_out.write(u'exten => s,%d,AGI(astportal/readvar.agi,%s,%s,%s)\n' % (
                                       prio, sound_file, param[3], param[5]))
         elif param[4]=='star':
            svi_out.write(u'exten => s,%d,AGI(astportal/readvar.agi,%s,%s,*)\n' % (
                                       prio, sound_file, param[3]))
         elif param[4]=='pound':
            svi_out.write(u'exten => s,%d,AGI(astportal/readvar.agi,%s,%s,#)\n' % (
                                       prio, sound_file, param[3]))
         (a, p) = play_or_tts(param[1][0], int(param[1][2:]))
         svi_out.write(u'exten => i_%d,1,%s(%s)\n' % (prio,a, p))
         svi_out.write(u'exten => i_%d,2,Goto(s,a_%d)\n' % (prio,tag))
         svi_out.write(u'exten => t_%d,1,Goto(s,a_%d)\n' % (prio,tag))
         (a, p) = play_or_tts(param[2][0], int(param[2][2:]))
         svi_out.write(u'exten => e_%d,1,%s(%s)\n' % (tag,a, p))
         svi_out.write(u'exten => e_%d,2,Hangup\n' % tag)
         prio +=1
         svi_out.write(u'exten => s,%d,Noop(Input=${%s})\n' % (prio,param[3]))
         prio +=1
         continue

      elif action==4: # Hangup
         app = 'Hangup'
         param = ''

      elif action==5: # RealSpeak
         app = 'RealSpeak'
         param = parameters.replace(',','\,')

      elif action==6: # Play message, then record
         (msg, dur, bip) = parameters.split('::')
         file = dir_monitor + '/rec-${UNIQUEID}.wav'
         (a, p) = play_or_tts(msg[0], int(msg[2:]))
         svi_out.write(u'exten => s,%d,%s(%s)\n' % (prio, a, p))
         prio += 1
         svi_out.write(u'exten => s,%d,Set(SVI_RECORD()=%s)\n' % (prio, app_id) )
         prio += 1
         opts = 'q' if bip=='true' else ''
         opts += 'k'
         app = 'Record'
         param = u'%s,5,%s,%s' % (file, dur, opts)

      elif action==7: # Transfer
# From Asterisk doc:
#DIALSTATUS - This is the status of the call
#    CHANUNAVAIL
#    CONGESTION
#    NOANSWER
#    BUSY
#    ANSWER
#    CANCEL
#    DONTCALL - For the Privacy and Screening Modes. Will be set if the called party chooses to send the calling party to the 'Go Away' script.
#    TORTURE - For the Privacy and Screening Modes. Will be set if the called party chooses to send the calling party to the 'torture' script.
#    INVALIDARGS

         (tel, timeout, noanswer, busy, error) = parameters.split('::')
         tel = tel.lower()
         if not tel.startswith('local/'):
            tel = 'local/' + tel
         if '@' not in tel:
            tel += '@sviout'
         svi_out.write(u'exten => s,%d,Dial(%s/nj,%s,g)\n' % (prio, tel, timeout))
         prio += 1
         tag = prio
         svi_out.write(u'exten => s,%d,Goto(s_%d_${DIALSTATUS},1)\n' % (tag,prio))
         prio += 1
         if noanswer!='-2':
            svi_out.write(u'exten => s_%d_NOANSWER,1,Goto(App_%d_%s,s,1)\n' % \
               (tag, app_id, noanswer[2:]))
         else:
            svi_out.write(u'exten => s_%d_NOANSWER,1,Goto(s,%d)\n' % (tag,prio))
         if busy!='-2':
            svi_out.write(u'exten => s_%d_BUSY,1,Goto(App_%d_%s,s,1)\n' % \
               (tag, app_id, busy[2:]))
            svi_out.write(u'exten => s_%d_CONGESTION,1,Goto(App_%d_%s,s,1)\n' % \
               (tag, app_id, busy[2:]))
         else:
            svi_out.write(u'exten => s_%d_BUSY,1,Goto(s,%d)\n' % (tag,prio))
         if error!='-2':
            svi_out.write(u'exten => s_%d_CHANUNAVAIL,1,Goto(App_%d_%s,s,1)\n' % \
               (tag, app_id, error[2:]))
            svi_out.write(u'exten => s_%d_INVALIDARGS,1,Goto(App_%d_%s,s,1)\n' % \
               (tag, app_id, error[2:]))
         else:
            svi_out.write(u'exten => s_%d_ERROR,1,Goto(s,%d)\n' % (tag,prio))
#         svi_out.write(u'exten => _s_%d_.,1,Goto(s,%d)\n' % (tag,prio))
         continue

      elif action==8: # Web service
         (url, var) = parameters.split('::')
         svi_out.write(u'exten => s,%d,Set(%s=${CURL(%s)})\n' % (prio, var, url))
         prio += 1
         continue

      elif action==9: # Loop
         (bloc, num) = parameters.split('::')
         cpt = 'svi_cpt_%s_%d' % (context, prio)
         svi_out.write(u'exten => s,%d,Set(%s=0)\n' % (prio, cpt))
         prio +=1
         svi_out.write(u'exten => s,%d,Set(%s=$[1 + ${%s}])\n' % (prio, cpt, cpt))
         prio +=1
         svi_out.write(u'exten => s,%d,GoSubIf($[ 0${%s} > %s ]?%d:App_%d_%s,s,1)\n' % (
            prio, cpt, num, prio+2, app_id,bloc[2:]))
         prio +=1
         svi_out.write(u'exten => s,%d,GoTo(%d)\n' % (prio,prio-2))
         prio +=1
         svi_out.write(u'exten => s,%d,StackPop\n' % prio) # Forget last GoSub
         prio +=1
         continue

      elif action==10: # Test
         (var, ope, val, if_true, if_false) = parameters.split('::')
         ops = {'eq': '=', 'ne': '#', 'lt': '<', 'le': '<=', 'gt': '>', 'ge': '>='}
         if if_true=='-2': # Continue
            if_true='' 
         elif if_true[0]=='c': # Jump to context
            if_true = u'App_%s_%s,s,1' % (app_id, if_true[2:])
         elif if_true[0]=='l': # Jump to label in context
            (c,l) = if_true[2:].split(',')
            if_true = u'App_%s_%s,s,%s' % (app_id, c, l)

         if if_false=='-2': # Continue
            if_false='' 
         elif if_false[0]=='c': # Jump to context
            if_false = u'App_%s_%s,s,1' % (app_id, if_false[2:])
         elif if_false[0]=='l': # Jump to label in context
            (c,l) = if_false[2:].split(',')
            if_false = u'App_%s_%s,s,%s' % (app_id, c, l)

         svi_out.write(u'exten => s,%d,GotoIf($[ "${%s}" %s "%s" ]?%s:%s)\n' % 
               (prio, var, ops[ope], val, if_true, if_false))
         prio +=1
         continue

      elif action==11: # Date / time test
         (begin, end, dow, days, months, if_true, if_false) = parameters.split('::')
         log.debug(u'Date / time test: if_true=%s, if_false=%s' % (if_true, 
            if_false))
         if if_true=='-2': # Continue
            if_true='' 
         elif if_true[0]=='c': # Jump to context
            if_true = u'App_%s_%s,s,1' % (app_id, if_true[2:])
         elif if_true[0]=='l': # Jump to label in context
            (c,l) = if_true[2:].split(',')
            if_true = u'App_%s_%s,s,%s' % (app_id, c, l)

         if if_false=='-2': # Continue
            if_false='' 
         elif if_false[0]=='c': # Jump to context
            if_false = u'App_%s_%s,s,1' % (app_id, if_false[2:])
         elif if_false[0]=='l': # Jump to label in context
            (c,l) = if_false[2:].split(',')
            if_false = u'App_%s_%s,s,%s' % (app_id, c, l)

         time = begin + '-' + end if begin!='' and end!='' else '*'
         dow = dow.replace(',', '&') if dow!='' else '*'
         days = days.replace(',', '&') if days!='' else '*'
         months = months.replace(',', '&') if months!='' else '*'
         svi_out.write(u'exten => s,%d,GotoIfTime(%s,%s,%s,%s?%s:%s)\n' % 
               (prio, time, dow, days, months, if_true, if_false))
         prio +=1
         continue

      elif action==12: # Context
         continue

      elif action==13: # Variable
         app = 'Set'
         (name, value) = parameters.split('::')
         param = u'%s=' % name
         if (value=='__1__'): param += '${CALLERID(num)}'
         elif (value=='__2__'): param += '${UNIQUEID}'
         else: param += value

      elif action==14: # Goto
         typ, dest = parameters.split(':')
         if typ=='c': # Jump to context
            param = u'App_%s_%s,s,1' % (app_id, dest)
         elif typ=='l': # Jump to label in context
            (c,l) = dest.split(',')
            param = u'App_%s_%s,s,%s' % (app_id, c, l)
         elif typ=='a': # Jump to application
            for app in apps:
                if app.app_id != int(dest):
                    continue
                param = u'SVI_internal,%s,1' % (app.exten)
                break
         app = 'Goto'

      elif action==16: # Label
         svi_out.write(u'exten => s,%d(%s),NoOp(Label)\n' % (prio, parameters))
         prio +=1
         continue

      elif action==17: # Store variable to database
         svi_out.write(u"exten => s,%d,Set(SVI_DATA()=%s,%s,${%s})\n" % 
               (prio, app_id, parameters, parameters) )
         prio += 1
         continue

      elif action==18: # Holidays
         (if_true, if_false) = parameters.split('::')
         if if_true=='-2': # Continue
            if_true='' 
         elif if_true[0]=='c': # Jump to context
            if_true = u'App_%s_%s,s,1' % (app_id, if_true[2:])
         elif if_true[0]=='l': # Jump to label in context
            (c,l) = if_true[2:].split(',')
            if_true = u'App_%s_%s,s,%s' % (app_id, c, l)

         if if_false=='-2': # Continue
            if_false='' 
         elif if_false[0]=='c': # Jump to context
            if_false = u'App_%s_%s,s,1' % (app_id, if_false[2:])
         elif if_false[0]=='l': # Jump to label in context
            (c,l) = if_false[2:].split(',')
            if_false = u'App_%s_%s,s,%s' % (app_id, c, l)

         svi_out.write(u"exten => s,%d,Gosub(holidays,s,1)\n" % (prio) )
         prio += 1
         svi_out.write(u'exten => s,%d,GotoIf($[ "${holiday}" = "true" ]?%s:%s)\n' % 
               (prio, if_true, if_false))
         prio +=1
         
         continue

      elif action==19: # Voicemail
         try:
            mb, msgidx = parameters.split('::')
            msgidx = int(msgidx)
         except:
            mb = parameters
            msgidx = 0
         svi_out.write(u"exten => s,%d,Voicemail(%s@astportal,%s)\n" % 
               (prio, mb, 'sub'[msgidx]) )
         prio += 1
         continue

      elif action==20: # Queue
         q = DBSession.query(Queue).get(int(parameters))
         options = ''
         if q:
            if q.connecturl:
               svi_out.write(u"exten => s,%d,Set(CONNECTURL=%s)\n" %
                  (prio, q.connecturl) ) 
               prio += 1

            if q.hangupurl:
               svi_out.write(u"exten => s,%d,Set(HANGUPURL=%s)\n" %
                  (prio, q.hangupurl) ) 
               prio += 1

            if q.connectdelay:
               svi_out.write(u"exten => s,%d,Set(CONNECTDELAY=%d)\n" %
                  (prio, q.connectdelay) ) 
               prio += 1
            else:
               svi_out.write(u"exten => s,%d,Set(CONNECTDELAY=0)\n" % prio) 
               prio += 1

            if q.monitor:
               svi_out.write(u"exten => s,%d,Set(MONITOR=1)\n" % prio) 
               prio += 1
               svi_out.write(u"exten => s,%d,Set(__DYNAMIC_FEATURES=stop_monitor)\n" % prio) 
               prio += 1
            else:
               svi_out.write(u"exten => s,%d,Set(MONITOR=0)\n" % prio) 
               prio += 1

            if q.music_id is None:
               options += 'r' # Indicate ringing to calling party
            else:
               # Answer needed for music on hold to work
               svi_out.write(u"exten => s,%d,Answer()\n" % (prio) )
               prio += 1

            timeout = q.timeout if q.timeout else ''

            svi_out.write(u"exten => s,%d,Queue(%s,%s,,,%s,,,agent_connect)\n" % 
               (prio, q.name, options, timeout) )
         else:
            svi_out.write(u"exten => s,%d,Queue(UNDEFINED)\n" % prio)
         prio += 1
         continue

      elif action==21: # Queue_log
         try:
            q, e, i, a = parameters.split('::')
         except:
            q, e, i = parameters.split('::')
            a = ''
         if i!='':
            i = ',' + i
         if a=='':
            a = '-'
         q = int(q)
         if q >=0:
            q = DBSession.query(Queue).get(int(q))
            name = q.name
         elif q==-2:
            name = 'Trace 1'
         elif q==-3:
            name = 'Trace 2'
         elif q==-4:
            name = 'Trace 3'
         qe = DBSession.query(Queue_event).get(int(e))
         svi_out.write(u"exten => s,%d,QueueLog(%s,${UNIQUEID},%s,%s%s)\n" % \
            (prio, name, a, qe.event, i))
         prio += 1
         continue

      elif action==22: # Playback
         app = u'Playback'
         param = u'astportal/%s' % (parameters)

      elif action==23: # Conference
         app = u'ConfBridge'
         param = u'%s' % (parameters)

      elif action==24: # AGI
         app = u'AGI'
         param = u'astportal/%s' % (parameters)

      elif action==25: # Say digits
         app = u'SayDigits'
         param = parameters

      else:
         m = u'Unknown action sce_id=%d, action=%d\n' % (sce_id, action)
         log.error(m)
         svi_out.write(u'; ERROR: %s' % m)
         continue

      svi_out.write(u'exten => s,%d,%s(%s)\n' % (prio, app, param))
      log.debug(u'exten => s,%d,%s(%s)', prio, app, param)
      prio += 1

   if prev_ctxt!='': svi_out.write(u'exten => s,%d,Return\n\n' % prio)
   svi_out.write(u'\n')
   svi_out.flush()
   fsync(svi_out.fileno())
   svi_out.close()

   result = -1
   try:
      # Create new extension file, and use it (reload dialplan)
      try:
         rename('/etc/asterisk/astportal/svi.conf', '/etc/asterisk/astportal/svi.conf.old')
      except:
         log.warning('renaming svi.conf -> svi.conf.old')
      rename('/etc/asterisk/astportal/svi.conf.new', '/etc/asterisk/astportal/svi.conf')
      Globals.manager.send_action({'Action': 'Command',
         'Command': 'dialplan reload'})
      result = 0
   except:
      result = 1
      log.error('ERROR system')
   
   # /function generate_dialplan
   return result

def mk_edges(s):
   '''Make DOT edges

   Parameter: scenario object
   Return: edges list
   Dot edge format: "node11":f2 -> "node1":f0 [id = 16];
   '''
   edges = []
   id = 0
   import random
   colors = 'black chocolate blue forestgreen magenta red turquoise3'.split()
   color = random.randint(0,len(colors)-1)
   action = int(s.action)
   if action==2: # Menu
      choices = s.parameters.split('::')[3]
      dst = s.context + '_Menu_';
      for c in choices:
         edges.append(u'''"%s":%d -> "%s%s" [color=%s];\n''' % (
            s.context, s.step, dst, c, colors[color]))
         color = (1+color)%len(colors)

   elif action==10: # Test
      if_true, if_false = s.parameters.split('::')[3:5]
      if if_true.startswith('c'):
         # Context jump
         edges.append(u'''"%s":%d -> "%s" [color=%s];\n''' % (
            s.context, s.step, if_true[2:], colors[color]))
         color += 1
         color = (1+color)%len(colors)
      elif if_true.startswith('l'):
         # Label jump
         (c,l) = if_true[2:].split(',')
         edges.append(u'''"%s":%d -> "%s":"%s" [color=%s];\n''' % (
            s.context, s.step, c, l, colors[color]))
         color = (1+color)%len(colors)

      if if_false.startswith('c'):
         # Context jump
         edges.append(u'''"%s":%d -> "%s" [color=%s];\n''' % (
            s.context, s.step, if_false[2:], colors[color]))
         color += 1
         color = (1+color)%len(colors)
      elif if_false.startswith('l'):
         # Label jump
         (c,l) = if_false[2:].split(',')
         edges.append(u'''"%s":%d -> "%s":"%s" [color=%s];\n''' % (
            s.context, s.step, c, l, colors[color]))
         color = (1+color)%len(colors)

   elif action==11: # Time based test
      if_true, if_false = s.parameters.split('::')[5:7]
      if if_true!='-2':
         edges.append(u'''"%s":%d -> "%s" [color=%s];\n''' % (
            s.context, s.step, if_true[2:], colors[color]))
         color = (1+color)%len(colors)
      if if_false!='-2':
         edges.append(u'''"%s":%d -> "%s" [color=%s];\n''' % (
            s.context, s.step, if_false[2:], colors[color]))
         color = (1+color)%len(colors)

   elif action==9: # Loop
      dst = s.parameters.split('::')[0]
      edges.append(u'''"%s":%d -> "%s" [color=%s];\n''' % (
         s.context, s.step, dst, colors[color]))
      color = (1+color)%len(colors)

   elif action==14: # Goto
      if s.parameters.startswith('c'):
         edges.append(u'''"%s":%d -> "%s" [color=%s];\n''' % (
            s.context, s.step, s.parameters[2:], colors[color]))
         color = (1+color)%len(colors)
      elif s.parameters.startswith('l'):
         c, l = s.parameters[2:].split(',')
         edges.append(u'''"%s":%d -> "%s":%s [color=%s];\n''' % (
            s.context, s.step, c, l, colors[color]))
         color = (1+color)%len(colors)

   elif action==18: # Holidays
      if_true, if_false = s.parameters.split('::')
      if if_true!='-2':
         edges.append(u'''"%s":%d -> "%s" [color=%s];\n''' % (
            s.context, s.step, if_true[2:], colors[color]))
         color = (1+color)%len(colors)
      if if_false!='-2':
         edges.append(u'''"%s":%d -> "%s" [color=%s];\n''' % (
            s.context, s.step, if_false[2:], colors[color]))
         color = (1+color)%len(colors)

   return edges


def mk_label(scenario, action_by_id):
   '''Make label for graphviz

   Label format: "context" [
         label= "{<0>context|<1> action params comments|...}",
         shape="Mrecord"
         ];
   Parameters: list of scenario
   Returns: string
   '''

   labels = []
   for s in scenario:
      # Cleanup parameters and comments
      trans = { ord(u'{'): u'\{', ord(u'}'): u'\}', ord(u'<'): u'&lt;', ord(u'>'): u'&gt;'}
      if s.parameters is not None:
         params = s.parameters.translate(trans)
      else:
         params = ''
      if s.comments is not None:
         comments = s.comments.translate(trans)
      else:
         comments = ''

      act = int(s.action)
      if act==1: # Playback
         (a, p) = play_or_tts(params[0], int(params[2:]))
         labels.append(u'<%d>%s %s (%s)' % ( s.step, action_by_id[act], p, comments))

      elif act==2: # Menu
         (msg, err, abandon, choices) = params.split('::')
         (a, msg) = play_or_tts(msg[0], int(msg[2:]))
         (a, err) = play_or_tts(err[0], int(err[2:]))
         if abandon=='-2': # Continue
            abandon = u'Continuer'
         else:
            (a, abandon) = play_or_tts(abandon[0], int(abandon[2:]))
         labels.append(u'<%d>%s %s, %s, %s (%s)' % (
            s.step, action_by_id[act], msg, err, abandon, comments))

      elif act==16: # Label
         labels.append(u'<%s>%s %s (%s)' % (
               params, action_by_id[act], params, comments))

      elif act==10: # Test
         (var, ope, val, if_true, if_false) = params.split('::')
         ops = {'eq': u'=', 'ne': u'#', 'lt': u'&lt;', 
            'le': u'&le;', 'gt': u'&gt;', 'ge': u'&ge;'}
         x = u'%s %s %s ?\\n' % (var, ops[ope], val)
         x += u'Continuer' if if_true=='-2' else if_true[2:]
         x += ', sinon '
         x += u'continuer' if if_false=='-2' else if_false[2:]
         labels.append(u'<%d>%s (%s)' % ( s.step, x, comments))

      elif act==11: # Time based test
         begin, end, dow, days, months, if_true, if_false = params.split('::')
         x = u'%s à %s, %s, %s, %s ?\\n' % (begin if begin else u'', end if end else u'', 
            dow if dow else u'', days if days else u'', months if months else u'')
         x += u'Continuer' if if_true=='-2' else if_true[2:]
         x += ', sinon '
         x += u'continuer' if if_false=='-2' else if_false[2:]
         labels.append(u'<%d>%s (%s)' % (s.step, x, comments))

      elif act==13: # Variable
         (name, value) = params.split('::')
         param = u'%s=' % name
         if (value=='__1__'): param += u'$\{CALLERID(num)\}'
         elif (value=='__2__'): param += u'$\{UNIQUEID\}'
         else: param += value
         labels.append(u'<%d>%s (%s)' % ( s.step, param, comments))

      elif act==18: # Holidays
         if_true, if_false = params.split('::')
         x = u'continuer' if if_true=='-2' else if_true[2:]
         x += ', sinon '
         x += u'continuer' if if_false=='-2' else if_false[2:]
         labels.append(u'<%d>%s ? %s %s' % (
               s.step, action_by_id[act], x, comments))

      elif act==20: # Queue
         q = DBSession.query(Queue).get(int(params))
         qname = q.name if q is not None else u'INCONNU'
         labels.append(u'<%d>%s %s, (%s)' % (
                  s.step, action_by_id[act], qname, comments))

      elif act==21: # Queue_log
         try:
            q, e, i, a = params.split('::')
         except:
            q, e, i = params.split('::')
            a = ''
         q = DBSession.query(Queue).get(int(q))
         qname = q.name if q is not None else u'INCONNU'         
         e = DBSession.query(Queue_event).get(int(e))
         labels.append(u'<%d>%s, %s, %s, %s, %s (%s)' % (
               s.step, action_by_id[act], qname, e.event, i, a, comments))

      else:
         labels.append(u'<%d>%s %s (%s)' % (
               s.step, action_by_id[act], params, comments))

   return u'"%s" [ label= "{<0>%s|%s}", shape="Mrecord"];\n' % (
         scenario[0].context, scenario[0].context, '|'.join(labels))

