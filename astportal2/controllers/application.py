# -*- coding: utf-8 -*-
# Application CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request
from tg.controllers import RestController
from tgext.menu import sidebar

from repoze.what.predicates import in_group, not_anonymous

from astportal2.lib.myjqgrid import MyJqGrid
#from tw.jquery import ui, ui_dialog
from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, CheckBox, CalendarDateTimePicker, TextArea
from tw.forms.validators import NotEmpty, Int, DateConverter, DateTimeConverter

from genshi import Markup

from astportal2.model import DBSession, Application, User, Group, Action, Scenario, Sound, User
#from astportal2.asterisk import extensions

from datetime import datetime
import re
from os import rename, system
import logging
log = logging.getLogger(__name__)


def play_or_tts(typ, val, brk=None):
   ''' Choose Playback / Background or RealSpeak 
   Return app, param
   '''
   if typ=='s':
# XXX      if val not in application.sounds:
# XXX         application.sounds.append(DBSession.query(Sound).get(val))
      if brk:
         app = u'Background'
         param = u'SVI/%d,%s' % (val,brk)
      else:
         app = u'Playback'
         param = u'SVI/%d' % (val)

   elif typ=='t':
# XXX      if val not in application.texts:
# XXX         application.texts.append(DBSession.query(Text).get(val))
      app = u'RealSpeak'
      txt = DBSession.query(Text).get(val)
      param = u'%s' % (txt.text.replace(',','\,'))
      if brk:
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
         CheckBox('active', 
            label_text=u'Active', default=True,
            help_text=u'Application active'),
         CalendarDateTimePicker('app_begin',
            label_text=u'Début', help_text=u'Date de début',
            date_format =  '%d/%m/%y %Hh%mm',
            not_empty = False, picker_shows_time = True,
            validator = DateTimeConverter(format='%d/%m/%y %Hh%Mm',
               messages = {'badFormat': 'Format date / heure invalide'})),
         CalendarDateTimePicker('app_end',
            label_text=u'Fin', help_text=u'Date de fin',
            date_format =  '%d/%m/%y %Hh%mm',
            not_empty = False, picker_shows_time = True,
            validator = DateTimeConverter(format='%d/%m/%y %Hh%Mm',
               messages = {'badFormat': 'Format date / heure invalide'})),
         TextArea('comment',
            label_text=u'Commentaires', help_text=u"Description de l'application"),
         HiddenField('_method', validator=None), # Needed by RestController
         HiddenField('app_id', validator=Int),
         ]

# Add application form for 'admin'
admin_fields = []
admin_fields.extend(common_fields)
#admin_fields.insert(0, SVI_user_select_field('owner_id', not_empty=False, #options = [],
#   label_text=u'Client', help_text=u"Propriétaire de l'application"))
admin_fields.insert(0, TextField('name', validator=NotEmpty,
      label_text=u'Nom', help_text=u"Entrez le nom de l'application"))
admin_fields.insert(1, TextField('exten', not_empty=False, #validator=None,
      label_text=u'Numéro interne', help_text=u'Choisissez l\'extension'))
admin_fields.insert(2, TextField('dnis', not_empty=False, #validator=None,
      label_text=u'Numéro extérieur', help_text=u'Choisissez le numéro RNIS'))
admin_new_application_form = TableForm(
   fields = admin_fields,
   submit_text = u'Valider...',
   action = 'create',
   hover_help = True
   )

# Add application form for 'normal' user
user_fields = []
user_fields.extend(common_fields)
user_fields.insert(0, TextField('name', validator=NotEmpty,
      label_text=u'Nom', help_text=u"Entrez le nom de l'application"))
new_application_form = TableForm(
   fields = user_fields,
   submit_text = u'Valider...',
   action = 'create',
   hover_help = True
   )

# Edit application form for 'normal' user
edit_fields = []
edit_fields.extend(common_fields)
edit_application_form = TableForm(
   fields = edit_fields,
   submit_text = u'Valider...',
   action = '/applications/',
   hover_help = True
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
   if in_group('admin'): row.append(user)

   return row


class Application_ctrl(RestController):
   
   allow_only = not_anonymous(msg=u'Veuiller vous connecter pour continuer')

   @sidebar(u'-- Administration || Applications (SVI)', sortorder = 12,
      icon = '/images/preferences-desktop-user.png',
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

      if in_group('admin'):
         grid.colNames.append(u'Utilisateur')
         grid.colModel.append({ 'name': 'owner_id', 'width': 100 })

      tmpl_context.grid = grid
      tmpl_context.form = None

      return dict( title=u'Liste des applications', debug='')


   @expose('json')
   def fetch(self, page, rows, sidx, sord, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      log.debug('fetch')
      apps = DBSession.query(Application)
      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * int(rp)
      except:
         offset = 0
         page = 1
         rows = 25

      total = apps.count()
      column = getattr(Application, sidx)
      apps = apps.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      rows = [ { 'id'  : a.app_id, 'cell': row(a) } for a in apps ]

      return dict(page=page, total=total, rows=rows)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new application form
      '''
      if in_group('admin'):
         tmpl_context.form = admin_new_application_form
      else:
         tmpl_context.form = new_application_form
      return dict(title = u'Nouvelle application', debug='', values='')
      
   class new_form_valid(object):
      def validate(self, params, state):
         f = admin_new_application_form if in_group('admin') \
            else new_application_form
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
         flash(u"Impossible de créer l'application (vérifier son nom)",'error')
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


   @validate(edit_application_form, error_handler=new)
   @expose()
   def put(self, **kw):
      ''' Update application in DB
      '''
      a = DBSession.query(Application).get(kw['app_id'])
      if not in_group('admin') and a.owner_id != request.identity['user'].user_id:
         flash(u'Accès interdit !', 'error')
         redirect('/')

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
         flash(u'Application modifiée',error)
      redirect('/applications/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete application from DB
      '''
      a = DBSession.query(Application).get(id)

      # 1. Delete scenario
      DBSession.query(Scenario).filter(Scenario.app_id==a.app_id).delete()

      # 2. Delete application
      DBSession.delete(a)

      # 3. Recreate extensions
      result = generate_dialplan()
      if result==0:
         flash(u'Application modifiée')
      else:
         flash(u'Application modifiée',error)
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

      actions = [{'action_id': x.action_id, 'action_name': x.name, 'action_comment': x.comment}
         for x in DBSession.query(Action).order_by(Action.name)]

      owner = DBSession.query(Application.owner_id).get(id)[0]

      sounds = [{'sound_id': x.sound_id, 'sound_name': x.name, 'sound_comment': x.comment}
         for x in DBSession.query(Sound).filter(Sound.owner_id==owner).order_by(Sound.name)]

      texts = []

      scenario = [{'sce_id': x.sce_id, 'context': x.context, 'extension': x.extension, 
         'priority': x.step, 'application': x.action, 'parameters': x.parameters, 
         'comments': x.comments, 'target': 0}
         for x in DBSession.query(Scenario).filter(Scenario.app_id==id).order_by(Scenario.context).order_by(Scenario.step)]

      return dict(scenario=scenario, sounds=sounds, texts=texts, actions=actions)



   @expose('json')
   def save_scenario(self, id, **kw):

      if kw.has_key('scenario[]'):
         scenario = kw['scenario[]']
      else:
         scenario = None
         # return dict(result=0) # XXX ?
      log.info('id %s, scenario %s (type %s)' % (id, scenario, type(scenario)) )
      application = DBSession.query(Application).get(int(id))

      # 1. Delete old entries
      DBSession.query(Scenario).filter(Scenario.app_id==int(id)).delete()

      # 2. Create new ones
      if scenario:
         if type(scenario)==type([]):
            for s in scenario:
               sc = Scenario()
               (c,i,e,p,a,m) = s.split('::',5)
               (sc.comments, sc.app_id, sc.context, sc.extension, sc.step, sc.action, 
                  sc.parameters) = (c, id, i, e, (1+int(p)) or 0, a, m)
               DBSession.add(sc)
         else:
            sc = Scenario()
            (c,i,e,p,a,m) = scenario.split('::',5)
            (sc.comments, sc.app_id, sc.context, sc.extension, sc.step, sc.action, 
               sc.parameters) = (c, id, i, e, (1+int(p)) or 0, a, m)
            DBSession.add(sc)

      result = generate_dialplan()
      return dict(result=result)

def generate_dialplan():
   ''' Generate dialplan from database
   '''
   # Check / acquire exclusive lock on file
   # XXX fcntl.lockf

   # 3. Generate dialplan
   import codecs
   svi_out = codecs.open('/etc/asterisk/SVI/svi.conf.new',
         mode='w', encoding='iso-8859-1')
   now = datetime.today().strftime('%Y/%m/%d %H:%M:%S')
   svi_out.write(u';\n; Dialplan generated automatically, manual changes will be lost !\n; %s\n;\n\n' % now)
 
   # Main context: check active + date, setup accountcode + userfield, then
   # route called number (RNIS) to application
   svi_out.write(u'[SVI] ; Main context RNIS -> App\n')
   apps = DBSession.query(Application)
   apps = apps.filter(Application.active==True)
   apps = apps.order_by(Application.exten)
   for a in apps:
      dnis = u'exten => %s' % a.dnis
      app_id = a.app_id
      name = a.name
      begin = a.begin
      end = a.end
      exten = a.exten

      svi_out.write(u'; %s (%d): %s <-> %s\n' % (name, app_id, exten, dnis))
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
      svi_out.write(u'%s,n,Answer()\n' % dnis)
#      svi_out.write(u'%s,n,Set(TIMEOUT(digit)=15)\n' % dnis)
      svi_out.write(u'%s,n,Set(CDR(accountcode)=%s)\n' % (dnis, app_id))
      svi_out.write(u'%s,n,Set(CDR(userfield)=SVI)\n' % dnis)
      svi_out.write(u'%s,n,Goto(App_%s_Entrant,s,1)\n' % (dnis, app_id))
   svi_out.write(u'\n')


   # Create contexts, priorities, ... from database
   prev_ctxt = ''
   scenario = DBSession.query(Scenario, Application)
   scenario = scenario.filter(Scenario.app_id==Application.app_id)
   scenario = scenario.filter(Application.active==True)
   scenario = scenario.order_by(Scenario.app_id)
   scenario = scenario.order_by(Scenario.context)
   scenario = scenario.order_by(Scenario.step)
   for dp in scenario.all():
      sce_id = int(dp.Scenario.sce_id)
      action = int(dp.Scenario.action)
      app_id = int(dp.Scenario.app_id)
      context = dp.Scenario.context
      parameters = dp.Scenario.parameters
      log.info('App %d, scenario %d: %s, %d(%s)' % (app_id, sce_id, context, action, parameters))

      ctxt = u'[App_%s_%s]\n' % (app_id, context)
      if prev_ctxt!=ctxt:
         if prev_ctxt!='': svi_out.write(u'exten => s,%d,Return\n\n' % prio)
         svi_out.write(ctxt)
         prio=1
         prev_ctxt = ctxt

      if action==0: # 'NoOp'
         app = u'NoOp'
         param = u''

      elif action==1: # Playback
         (app, param) = play_or_tts(parameters[0], int(parameters[2:]))

      elif action==2: # Menu
         if context=='Entrant': next = 'App_%s_Suite' % app_id
         else: next = 'App_%s_%s' % (app_id, context)
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
         (a, p) = play_or_tts(param[0][0], int(param[0][2:]))
         svi_out.write(u'exten => s,%d,%s(%s,%s)\n' % (prio, a, p, param[3]))
         prio +=1
         #svi_out.write(u'exten => s,%d,AGI(SVI/readvar.agi,m_%d,1,%s)\n' % (
         #   prio, sce_id, param[3]))
         svi_out.write(u'exten => s,%d,WaitExten\n' % prio)
         prio +=1
         (a, p) = play_or_tts(param[1][0], int(param[1][2:]))
         svi_out.write(u'exten => i,1,%s(%s)\n' % (a, p))
         svi_out.write(u'exten => i,2,Goto(s,a_%d)\n' % (tag))
         svi_out.write(u'exten => t,1,Goto(s,a_%d)\n' % (tag))
         (a, p) = play_or_tts(param[2][0], int(param[2][2:]))
         svi_out.write(u'exten => e_%d,1,%s(%s)\n' % (tag,a, p))
         svi_out.write(u'exten => e_%d,2,Hangup\n' % tag)
         for c in param[3]:
            svi_out.write(u'exten => %c,1,Goto(%s_${EXTEN},s,1)\n' % (c, next))
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
         svi_out.write(u'exten => s,%d,AGI(SVI/readvar.agi,%s,1,%s)\n' % (prio, param[4], param[3]))
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
         if context=='Entrant': next = 'App_%s_' % app_id
         else: next = 'App_%s_%s_' % (app_id, context)
         param = parameters.split('::')
         cpt = 'svi_cpt_%s_%d' % (context, prio)
         svi_out.write(u'exten => s,%d,Set(%s=0)\n' % (prio, cpt))
         prio +=1
         tag = prio
         svi_out.write(u'exten => s,%d(a_%d),Set(%s=$[1 + ${%s}])\n' % (tag, prio, cpt, cpt))
         prio +=1
         svi_out.write(u'exten => s,%d,GotoIf($[ 0${%s} > 3 ]?e_%d,1)\n' % (prio, cpt, tag))
         prio +=1
         (a, p) = play_or_tts(param[0][0], int(param[0][2:]))
         # svi_out.write(u'exten => s,%d,%s(%s,%s)\n' % (prio, a, p, param[3]))
         svi_out.write(u'exten => s,%d,%s(%s)\n' % (prio, a, p))
         prio +=1
         if param[4]=='fixed':
            svi_out.write(u'exten => s,%d,AGI(SVI/readvar.agi,%s,%s)\n' % (prio,param[3],param[5]))
         elif param[4]=='star':
            svi_out.write(u'exten => s,%d,AGI(SVI/readvar.agi,%s,*)\n' % (prio,param[3]))
         elif param[4]=='pound':
            svi_out.write(u'exten => s,%d,AGI(SVI/readvar.agi,%s,#)\n' % (prio,param[3]))
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
         file = '/var/spool/asterisk/monitor/rec-${UNIQUEID}.wav'
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
         (tel, timeout, noanswer, busy, error) = parameters.split('::')
         svi_out.write(u'exten => s,%d,Dial(${opt}/%s,%s,g)\n' % (prio, tel, timeout))
         prio += 1
         tag = prio
         svi_out.write(u'exten => s,%d,Goto(s-%d-${DIALSTATUS},1)\n' % (tag,prio))
         prio += 1
         if noanswer!='-2':
            svi_out.write(u'exten => s-%d-NOANSWER,1,Goto(%s,s,1)\n' % (tag,noanswer))
         else:
            svi_out.write(u'exten => s-%d-NOANSWER,1,Goto(s,%d)\n' % (tag,prio))
         if busy!='-2':
            svi_out.write(u'exten => s-%d-BUSY,1,Goto(%s,s,1)\n' % (tag,busy))
         else:
            svi_out.write(u'exten => s-%d-BUSY,1,Goto(s,%d)\n' % (tag,prio))
         if error!='-2':
            svi_out.write(u'exten => s-%d-ERROR,1,Goto(%s,s,1)\n' % (tag,error))
         else:
            svi_out.write(u'exten => s-%d-ERROR,1,Goto(s,%d)\n' % (tag,prio))
         svi_out.write(u'exten => _s-%d-.,1,Goto(s,%d)\n' % (tag,prio))
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
         svi_out.write(u'exten => s,%d,GoSubIf($[ 0${%s} > %s ]?%d:App_%d_%s,s,1)\n' % (prio, cpt, num, prio+2, app_id,bloc[2:]))
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

         svi_out.write(u'exten => s,%d,GotoIf($[ ${%s} %s %s ]?%s:%s)\n' % 
               (prio, var, ops[ope], val, if_true, if_false))
         prio +=1
         continue

      elif action==11: # Timed test
         (begin, end, dow, days, months, if_true, if_false) = parameters.split('::')
         time = begin + '-' + end if begin!='' and end!='' else '*'
         dow = dow.replace(',', '&') if dow!='' else '*'
         days = days.replace(',', '&') if days!='' else '*'
         months = months.replace(',', '&') if months!='' else '*'
         svi_out.write(u'exten => s,%d,GotoIfTime(%s,%s,%s,%s?App_%s_%s,s,1)\n' % 
               (prio, time, dow, days, months, app_id, if_true[2:]))
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
         (typ,dest) = parameters.split(':')
         if typ=='c': # Jump to context
            param = u'App_%s_%s,s,1' % (app_id, dest)
         elif typ=='l': # Jump to label in context
            (c,l) = dest.split(',')
            param = u'App_%s_%s,s,%s' % (app_id, c, l)
         app = 'Goto'

      elif action==16: # Label
         svi_out.write(u'exten => s,%d(%s),NoOp(Label)\n' % (prio, parameters))
         prio +=1
         continue

      elif action==17: # Store variable to database
         svi_out.write(u"exten => s,%d,Set(SVI_DATA()=%s\\,'%s'\\,'${%s}')\n" % 
               (prio, app_id, parameters, parameters) )
         prio += 1
         continue

      else:
         m = u'Unknown action sce_id=%d, action=%d\n' % (sce_id, action)
         log.error(m)
         svi_out.write(u'; ERROR: %s' % m)
         continue

      svi_out.write(u'exten => s,%d,%s(%s)\n' % (prio, app, param))
      prio += 1

   if prev_ctxt!='': svi_out.write(u'exten => s,%d,Return\n\n' % prio)
   svi_out.write(u'\n')
   svi_out.close()

   result = -1
   try:
      # Create new extension file, and use it (reload dialplan)
      try:
         rename('/etc/asterisk/SVI/svi.conf', '/etc/asterisk/SVI/svi.conf.old')
      except:
         pass
      rename('/etc/asterisk/SVI/svi.conf.new', '/etc/asterisk/SVI/svi.conf')
      system('/etc/asterisk/SVI/sync.sh')
      result = 0
   except:
      result = 1
      log.error('ERROR system')
   
   # /function generate_dialplan
   return result

