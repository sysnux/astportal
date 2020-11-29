# -*- coding: utf-8 -*-
# Incidents controller

from tg import expose, config, tmpl_context
from tgext.menu import sidebar

try:
   from tg.predicates import in_any_group
except ImportError:
   from repoze.what.predicates import in_any_group

from tw.forms import TableForm, RadioButtonList

import logging
log = logging.getLogger(__name__)
import re

from astportal2.lib.app_globals import Globals
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.base import BaseController

from os import access, R_OK, W_OK, X_OK


def check_command(var):
   '''
   Check file from command is executable
   '''
   cmd = config.get(var)
   return(var, cmd, access(cmd[:cmd.index(' ')], X_OK))


def check_value(var):
   '''
   Check var is set
   '''
   val = config.get(var)
   return (var, val, True if val else False)


def check_dir(var, mode):
   '''
   Check dir is accessible
   '''
   dir = config.get(var)
   return (var, dir, access(dir, mode))


class Check_Config_ctrl(BaseController):

   allow_only = in_any_group('admin',
      msg=u'Vous devez appartenir au groupe "admin" pour visualiser la configuration')

   @sidebar(u'-- Administration || Configuration',
      icon = '/images/script-error.png', sortorder = 16)
   @expose(template="astportal2.templates.grid")
   def index(self):
      ''' Prepare grid of configuration variables
      '''

      grid = MyJqGrid( id='grid', url='fetch', caption=u"Configuration",
            sortname='var', sortorder='desc',
            colNames = [u'Variable', u'Valeur', u'Etat'],
            colModel = [ { 'name': 'variable', 'width': 80,},
               { 'name': 'value', 'width': 200 },
               { 'name': 'status', 'width': 10 } ],
            navbuttons_options = {'view': False, 'edit': False, 'add': False,
               'del': False, 'search': True, 'refresh': True, 
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None

      return dict( title=u'Configuration', debug='')


   @expose('json')
   def fetch(self, page, rows, sidx='date', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by FlexGrid
      '''

      offset = 0
      page = 1
      rows = 1000

      conf = []
      conf.append(check_value('prefix.src'))
      conf.append(check_value('default_dnis'))
      conf.append(check_value('default_cid'))
      conf.append(check_value('default_faxto'))
      conf.append(check_value('default_faxfrom'))
      conf.append(check_value('hide_numbers'))
      conf.append(check_value('company'))
#      conf.append(check_value('crm_url'))

      try:
         asterisk_manager = ', '.join([x[0] for x in \
            eval(config.get('asterisk.manager'))])
         asterisk_manager_status = True \
            if Globals.manager is not None else False
         conf.append(('asterisk_manager', asterisk_manager, 
               True if Globals.manager is not None else False))
      except:
         conf.append(('asterisk_manager', None, False))

      conf.append(check_value('server.sip'))
      conf.append(check_value('server.sip2'))
      conf.append(check_value('server.firmware'))
      conf.append(check_value('server.config'))
      conf.append(check_value('server.syslog'))
      conf.append(check_value('server.ntp'))
      conf.append(check_value('server.utc_diff'))
      conf.append(check_command('command.fping'))
      conf.append(check_command('command.arp'))
      conf.append(check_command('command.sendfax'))
      conf.append(check_command('command.sox8'))
      conf.append(check_command('command.sox16'))

      dir_tftp = config.get('directory.tftp', '')
      conf.append(('directory.tftp: firmware', dir_tftp + 'phones/firmware/',
         access(dir_tftp + 'phones/firmware/', R_OK)))
      conf.append(('directory.tftp: config', dir_tftp + 'phones/config/',
         access(dir_tftp + 'phones/config/', W_OK)))
      conf.append(check_dir('directory.asterisk', W_OK))
      conf.append(check_dir('directory.monitor', W_OK))
      conf.append(check_dir('directory.utils', R_OK))
      conf.append(check_dir('directory.tmp', W_OK))
      conf.append(check_dir('directory.fax', W_OK))

      dir_moh = config.get('directory.moh')

      try:
         sounds_languages = eval(config.get('sounds.languages'))
         sounds_languages_status = True
      except:
         sounds_languages = u'Invalide'
         sounds_languages_status = False
         directory_sounds_status = False
         directory_moh_status = False

      dir_sounds = []
      dir_moh = []
      if sounds_languages_status:
         if type(sounds_languages) is not tuple and \
               type(sounds_languages) is not list:
            sounds_languages = (sounds_languages, )
         for l in sounds_languages:
            directory_sounds = config.get('directory.sounds')
            if directory_sounds:
               directory_sounds_status = True
               dir = directory_sounds % l
               directory_sounds_status = \
                  directory_sounds_status and access(dir, W_OK)
               dir_sounds.append(dir)
            else:
               directory_sounds_status = False

            directory_moh = config.get('directory.moh')
            if directory_moh:
               directory_moh_status = True
               dir = directory_moh % l
               directory_moh_status = \
                  directory_moh_status and access(dir, W_OK)
               dir_moh.append(dir)
            else:
               directory_moh_status = False
      conf.append(('directory.moh', ', '.join(dir_moh), directory_moh_status))
      conf.append(('directory.sounds', ', '.join(dir_sounds), 
         directory_sounds_status))

      conf.append(check_value('asterisk.sip'))
      conf.append(check_value('server.vlan'))
      # Configuration Via Keypad Menu. 0 - Unrestricted, 
      # 1 - Basic settings only, 2 - Constraint mode
      try:
         gxp_keypad = (u'Non restreint', u'Réglage de base',
            u'Restreint')[int(config.get('gxp.keypad'))]
         gxp_keypad_status = True
      except:
         gxp_keypad = u'Invalide'
         gxp_keypad_status = False
      conf.append(('gxp.keypad', gxp_keypad, gxp_keypad_status))

      rows = [ { 'id'  : i, 
            'cell': (c[0],
               c[1], 
               '<img src="/images/%s.png" width="12" height="12">' % ('ok' if c[2] else 'error'))
            } for i, c in enumerate(conf) ]

      return dict(page=page, total=1, rows=rows)

