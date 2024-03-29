# -*- coding: utf-8 -*-
# Voicemail controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config, session
from tgext.menu import sidebar

try:
   from tg.predicates import not_anonymous, in_group, in_any_group
except ImportError:
   from repoze.what.predicates import not_anonymous, in_group, in_any_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, FileField, RadioButtonList
from tw.forms.validators import NotEmpty, Int, FieldStorageUploadConverter

from astportal2.lib.app_globals import Markup
from os import unlink, rename, chdir, listdir, stat
import logging
log = logging.getLogger(__name__)
import re
from datetime import datetime, timedelta
from time import time, sleep
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

from astportal2.model import DBSession, User, Voicemessages
from astportal2.lib.base import BaseController
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

dir_vm = config.get('directory.voicemail')
utc_delta = timedelta(hours=float(config.get('server.utc_diff')))
sip_type = 'PJSIP' if config.get('asterisk.sip').lower()=='pjsip' else 'SIP'

folders = dict(INBOX = u'Nouveaux',
      Old = u'Anciens',
      Work = u'Travail',
      Family =  u'Famille',
      Friends =  u'Amis')
# XXX what about ( "Cust1", "Cust2", "Cust3", "Cust4", "Cust5" )
month = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6,
      Jul=7, Aug=8, Sep=9, Oct=10, Nov=11, Dec=12)


def row(vm, folder):
   '''Displays a formatted row of the voicemail list
   Parameter: Voicemail dict
   '''

   action =  u'''<a href="#" onclick="move('%s',%d)" title="Déplacer">''' % (
      vm['mb'], vm['id'])
   action += u'<img src="/images/edit.png" border="0" alt="Déplacer" /></a>'
   action += u'&nbsp;&nbsp;&nbsp;'
   action += u'''<a href="#" onclick="del('%s','%d','Suppression du message %d')" title="Supprimer">''' % (
      vm['mb'], vm['id'], 1+vm['id'])
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

#   listen = u'''<a href="#" onclick="listen('%s',%d,'listen')" title="\u00C9coute">\u00C9coute</a>''' % (
#      vm['mb'], vm['id'])

   listen = u'''<a href="#" onclick="listen('%s',%d,'download')"><img src="/images/emblem-downloads.png" title="Télécharger"></a>''' % \
      (vm['mb'], vm['id'])
   listen += u'''&nbsp;&nbsp;&nbsp;<a href="#" onclick="listen('%s',%d,'listen')"><img src="/images/sound_section.png" title="&Eacute;couter"></a>''' % \
      (vm['mb'], vm['id'])
   return [Markup(action), vm['mb'], 1+vm['id'], vm['callerid'], 
      vm['origdate'].strftime("%A %d %B, %Hh%Mm%Ss").decode('utf-8'),
      Markup(listen) ]


class Voicemail_ctrl(BaseController):
   
   allow_only = not_anonymous( msg=u'Veuillez vous connecter pour continuer' )

   @sidebar(u"Messagerie vocale", sortorder=3,
      icon = '/images/message.png')
   @expose(template="astportal2.templates.grid_voicemail")
   def index(self, mb=None, id=None, folder='INBOX', to=None, 
         busy=None, unavail=None, greet=None):
      ''' List messages
      '''

      res = Globals.manager.send_action({'Action': 'Command',
         'command': 'voicemail reload'})
      log.debug('Reload voicemail returns "%s"' % res)

      log.debug('mb=%s, id=%s, folder=%s, to=%s, busy=%s, unavail=%s, greet=%s' % (
            mb, id, folder, to, busy, unavail, greet))

      grid = MyJqGrid( id='grid', url='fetch', 
            caption=u"%s" % folders[folder],
            sortname='id', sortorder='asc',
            colNames = [u'Action', u'Extension',
               u'Message', u'De', u'Date', u'Ecoute' ],
            colModel = [ { 'width': 60, 'align': 'center', 'sortable': False },
               { 'name': 'mb', 'width': 60 },
               { 'name': 'id', 'width': 60 },
               { 'name': 'callerid', 'width': 100 },
               { 'name': 'origdate', 'width': 100 },
               { 'width': 60, 'align': 'center', 'sortable': False },
               ],
            navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': False, 'refresh': True},
            postData = {'folder': folder},
         )

      tmpl_context.grid = grid

      tmpl_context.form2 = None if in_group('admin') else \
         TableForm(
            'messages_form', name = 'messages_form',
            fields = [
               Label(text = u'Nouveaux messages personnalisés :'),
               FileField('greet', 
                  validator=FieldStorageUploadConverter(not_empty=False),
                  label_text=u'Nom', help_text=u'Fichier au format WAV'),
               FileField('unavail', 
                  validator=FieldStorageUploadConverter(not_empty=False),
                  label_text=u'Indisponible', help_text=u'Fichier au format WAV'),
               FileField('busy', 
                  validator=FieldStorageUploadConverter(not_empty=False),
                  label_text=u'Occupé', help_text=u'Fichier au format WAV'),
            ],
            submit_text = u'Valider...',
            action = 'custom_messages',
#            hover_help = True
         )

      tmpl_context.form = TableForm(
         'folder_form', name = 'folder_form',
         fields = [
            SingleSelectField('folder',
               options = [(k,v) for k,v in folders.iteritems()],
               label_text = u'Dossier : ', help_text = u'Choisissez un dossier',
               attrs = {'onchange': js_callback('change_folder()')}),
            HiddenField('mb'),
            HiddenField('id'),
            HiddenField('to'),
         ],
         submit_text = None,
         action = '',
#         hover_help = True
      )
      return dict( title=u"Messages vocaux", debug='', 
            values={'folder': folder}, values2={'greet': 'Mon nom', 
               'unavail': 'Indisponible', 'busy': 'Occupé'})


   @expose('json')
   def fetch(self, page, rows, sidx='mb', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, 
          folder='INBOX', **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data
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

      voicemails = []
      u = DBSession.query(User). \
            filter(User.user_name==request.identity['repoze.who.userid']). \
            one()
      for phone in u.phone:
         mb = phone.exten # get mailbox from user exten
         wd = '%s/%s/%s' % (dir_vm, mb, folder)
         log.debug(u'Voicemail dir: %s' % wd)

         for msg in DBSession.query(Voicemessages). \
               filter(Voicemessages.dir == '%s/%s/%s' % (dir_vm, mb, folder)). \
               all():
            vm = {}
            vm['id'] = msg.uniqueid
            vm['mb'] = mb
            vm['origdate'] = datetime.fromtimestamp(float(msg.origtime))
            vm['callerid'] = msg.callerid
            voicemails.append(vm)

      sort_key = lambda x : x[sidx]
      data = []
      total = 0
      for v in sorted(voicemails, key=sort_key,
            reverse = True if sord=='desc' else False):
         data.append({ 'id'  : v['id'], 'cell': row(v,folder) })
         total += 1

      return dict(page=page, total=total, rows=data[offet:offset+rows])


   @expose('json')
   def fetch_folders(self, folder):
      log.debug('fetch_folders %s' % folder)
      ff = folders.copy()
      del(ff[folder])
      return dict(folders = ff)


   @expose()
   def delete(self, mb, id, folder, to):
      ''' Delete message
      '''
      id = int(id)
      log.info('delete %s/%d' % (folder, id))
      msg = DBSession.query(Voicemessages).get(id)
      log.debug('message = %s' % msg)
      DBSession.delete(msg)

      # To clear MWI
      Globals.manager.send_action({'Action': 'Command',
         'command': 'voicemail reload'})

      redirect('/voicemail/?folder=%s' % folder)


   @expose()
   def move(self, mb, id, folder, to):
      ''' Delete message
      '''
      id = int(id)
      log.info('move %d from %s to %s' % (id, folder, to))
      fro = '%s/%s/%s' % (dir_vm, mb, folder)
      to = '%s/%s/%s' % (dir_vm, mb, to)
      try:
         chdir(fro)
         msgs_to = sorted(listdir(to), reverse=True)
      except:
         log.error('chdir %s / listdir %s\n' % (fro, to))
         flash(u'Une erreur est survenue', 'error')
         redirect('/voicemail/?folder=%s' % folder)
      if len(msgs_to)==0:
         max = 0
      else:
         max = 1 + int(msgs_to[0][3:7])

      # Move message
      for e in ('gsm', 'WAV', 'wav', 'txt'):
         try:
            rename('msg%04d.%s' % (id, e), 
               '%s/msg%04d.%s' % (to, max, e))
         except:
            log.warning('unlink %s\n' % e)

      # Rename following messages
      for f in sorted(listdir('.')):
         m = int(f[3:7])
         if m<id:
            continue
         try:
            rename(f, 'msg%04d.%s' % (m-1, f[-3:]))
         except:
            log.warning('rename %s\n' % f)

      # To clear MWI
      Globals.manager.send_action({'Action': 'Command',
         'command': 'voicemail reload'})

      redirect('/voicemail/?folder=%s' % folder)


   @expose()
   def listen(self,  mb, folder, id, to):
      ''' Listen sound
      '''
      log.debug('listen %s %s %s %s' % (mb, folder, id, to))

      msg = DBSession.query(Voicemessages).get(id)
      log.debug('message = %s' % msg)
      fn = '/tmp/msg-%d.WAV' % (msg.uniqueid)

      import psycopg2
      conn = psycopg2.connect('dbname=astportal2 user=postgres')
      lo = conn.lobject(int(msg.recording), 'rb')
      f = open( fn, 'w')
      f.write(lo.read())
      f.close()
      conn.close()

      try:
         st = stat(fn)
         f = open(fn)
      except:
         flash(u'Message introuvable: %s' % fn, 'error')

      phones = DBSession.query(User).filter(User.user_name==request.identity['repoze.who.userid']).one().phone
      if len(phones)<1:
         log.debug('Playback from user %s : no extension' % (
            request.identity['user']))
         flash(u'Poste de l\'utilisateur %s introuvable' % \
               request.identity['user'], 'error')
         redirect('/voicemail/?folder=%s' % folder)

      sip = phones[0].sip_id
      res = Globals.manager.originate(
            sip_type + '/' + sip, # Channel
            sip, # Extension
            application = 'Playback',
            data = fn[:-4],
            )
      log.debug('Playback %s from user %s (%s) returns %s' % (
         fn[:-4], request.identity['user'], sip, res))

      # Move to "Old" folder and reload voicemail to clear MWI
      log.debug('Move message = "%s" to "Old" folder' % msg)
      msg.dir = '/var/spool/asterisk/voicemail/astportal/%s/Old' % msg.mailboxuser
      DBSession.flush()
      sleep(10)
      res = Globals.manager.send_action({'Action': 'Command',
         'command': 'voicemail reload'})
      log.debug('Reload voicemail returns "%s"' % res)

      redirect('/voicemail/?folder=%s' % folder)


   @expose()
   def download(self, mb, folder, id, to):
      ''' Download message
      '''
      log.debug('download %s %s %s %s' % (mb, folder, id, to))

      msg = DBSession.query(Voicemessages).get(id)
      log.debug('message = %s' % msg)

      import psycopg2
      conn = psycopg2.connect('dbname=astportal2 user=postgres')
      lo = conn.lobject(int(msg.recording), 'rb')
      f = open( '/tmp/msg-%d.gsm' % msg.uniqueid, 'w')
      f.write(lo.read())
      f.close()
      conn.close()

      name = 'msg%04d.gsm' % msg.msgnum
      fn = '/tmp/msg-%d.gsm' % msg.uniqueid
      try:
         st = stat(fn)
         f = open(fn)
      except:
         flash(u'Message introuvable: %s' % fn, 'error')
         redirect('/voicemail/?folder=%s' % folder)
      rh = response.headers
      rh['Pragma'] = 'public' # for IE
      rh['Expires'] = '0'
      rh['Cache-Control'] = 'max-age=0' #for IE
      rh['Content-Type'] = 'audio/x-gsm'
      rh['Content-Disposition'] = str( (u'attachment; filename="%s"; size=%d;' % (
         name, st.st_size)).encode('utf-8') )
      rh['Content-Transfer-Encoding'] = 'binary'

      # Move to "Old" folder and reload voicemail to clear MWI
      log.debug('Move message = "%s" to "Old" folder' % msg)
      msg.dir = '/var/spool/asterisk/voicemail/astportal/%s/Old' % msg.mailboxuser
      DBSession.flush()
      sleep(10)
      res = Globals.manager.send_action({'Action': 'Command',
         'command': 'voicemail reload'})
      log.debug('Reload voicemail returns "%s"' % res)

      return f.read()


   @expose()
   def custom_messages(self, greet, unavail, busy):
      log.debug('greet=%s, unavail=%s, busy=%s' % (greet, unavail, busy))
      redirect('/voicemail/')
#      return dict()

