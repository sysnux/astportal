# -*- coding: utf-8 -*-
# Voicemail controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, response, config
from tg.controllers import CUSTOM_CONTENT_TYPE
from tgext.menu import sidebar

from repoze.what.predicates import in_group, not_anonymous, in_any_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, FileField, RadioButtonList
from tw.forms.validators import NotEmpty, Int, FieldStorageUploadConverter

from genshi import Markup
from os import unlink, rename, chdir, listdir, stat
import logging
log = logging.getLogger(__name__)
import re
from datetime import datetime
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

from astportal2.model import DBSession, User
from astportal2.lib.base import BaseController
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

dir_vm = '/var/spool/asterisk/voicemail/default'
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

   listen = u'''<a href="#" onclick="listen('%s',%d)" title="\u00C9coute">\u00C9coute</a>''' % (
      vm['mb'], vm['id'])

   return [Markup(action), vm['mb'], 1+vm['id'], vm['callerid'], 
      vm['origdate'].strftime("%A %d %B, %Hh%Mm%Ss"), Markup(listen) ]


class Voicemail_ctrl(BaseController):
   

   @sidebar(u"Messagerie vocale", sortorder=11,
      icon = '/images/sound_section-large.png')
   @expose(template="astportal2.templates.grid_voicemail")
   def index(self, mb=None, id=None, folder='INBOX', to=None):
      ''' List messages
      '''

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
               { 'width': 60, 'sortable': False },
               ],
            navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': True, 'refresh': True},
            postData = {'folder': folder},
         )
      tmpl_context.grid = grid
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
         hover_help = True
      )
      return dict( title=u"Messages vocaux", debug='', values={'folder': folder})


   @expose('json')
   def fetch(self, page=1, rows=10, sidx='mb', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, 
          folder='INBOX', **kw):
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

      voicemails = []
      u = DBSession.query(User). \
            filter(User.user_name==request.identity['repoze.who.userid']). \
            one()
      for phone in u.phone:
         mb = phone.exten # get mailbox from user exten
         wd = '%s/%s/%s' % (dir_vm, mb, folder)
         log.debug(u'Voicemail dir: %s' % wd)
         # File: /var/spool/asterisk/voicemail/default/1/Old/msg0000.txt
         try:
            files = listdir(wd)
         except:
            continue
         for f in files:
            if not f.endswith('.txt'): continue
            vm = {}
            for l in open('%s/%s' % (wd, f)):
               try:
                  k, v = l.split('=')
               except:
                  continue
               if k=='origdate':
                  # Convert to date object
                  vm[k] = datetime(int(v[-6:]), month[v[4:7]], int(v[8:10]),
                     int(v[11:13]), int(v[14:16]), int(v[17:19]))
               else:
                  vm[k] = v[:-1]
            vm['id'] = int(f[-8:-4])
            vm['mb'] = mb
            voicemails.append(vm)

      sort_key = lambda x : x[sidx]
      data = []
      total = 0
      for v in sorted(voicemails, key=sort_key,
            reverse = True if sord=='desc' else False):
         data.append({ 'id'  : v['id'], 'cell': row(v,folder) })
         total += 1

      return dict(page=page, total=total, rows=data)


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
      dir = '%s/%s/%s' % (dir_vm, mb, folder)
      try:
         chdir(dir)
      except:
         log.error('chdir %s\n' % dir)
         flash(u'Une erreur est survenue', 'error')
         redirect('/voicemail/?folder=%s' % folder)

      # Delete message
      for e in ('gsm', 'WAV', 'wav', 'txt'):
         try:
            unlink('msg%04d.%s' % (id, e))
         except:
            log.warning('unlink msg%04d.%s' % (id, e))

      # Rename following messages
      for f in sorted(listdir('.')):
         m = int(f[3:7])
         if m<id:
            try:
               rename(f, 'msg%04d.%s' % (m-1, f[-3:]))
            except:
               log.warning('rename %s\n' % f)

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

      redirect('/voicemail/?folder=%s' % folder)


   @expose()
   def listen(self, mb, folder, id, to):
      ''' Listen message
      '''
      name = 'msg%04d.wav' % int(id)
      fn = '%s/%d/%s/%s' % (dir_vm, mb, folder, name)
      try:
         st = stat(fn)
         f = open(fn)
      except:
         flash(u'Message introuvable: %s' % fn, 'error')
         redirect('/voicemail/?folder=%s' % folder)
      rh = response.headers
      rh['Pragma'] = 'public' # for IE
      rh['Expires'] = '0'
      rh['Cache-control'] = 'must-revalidate, post-check=0, pre-check=0' #for IE
      rh['Cache-control'] = 'max-age=0' #for IE
      rh['Content-Type'] = 'audio/wav'
      rh['Content-disposition'] = u'attachment; filename="%s"; size=%d;' % (
         name, st.st_size)
      rh['Content-Transfer-Encoding'] = 'binary'
      return f.read()

