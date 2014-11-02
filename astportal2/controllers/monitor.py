# -*- coding: utf-8 -*-

from tg import config, expose
from tg.controllers import TGController
from tgext.menu import navbar, sidebar, menu

try:
   from tg.predicates import in_group
except ImportError:
   from repoze.what.predicates import in_group

from astportal2.lib.app_globals import Globals

from time import time, sleep

import logging
log = logging.getLogger(__name__)

class Monitor_ctrl(TGController):
 
   allow_only = in_group('admin', 
      msg=u'Vous devez être membre du groupe "admin" pour accéder à cette page')

   @sidebar(u'-- Administration || Surveillance', sortorder = 11,
      icon = '/images/astronomy_section.png')
   @expose(template="astportal2.templates.monitor")
   def index(self):
      '''
      '''
      return dict( title=u'Appels en cours', debug='')


   @expose('json')
   def update_channels(self, last=0.0):
      ''' Function called on AJAX request made by template.
      Return when new updates available, or timeout
      '''
      last = float(last)
      log.debug('monitor request last=%f' % last)
      for i in xrange(50):
         sleep(1)
         if Globals.asterisk.last_update > last:
            break
      log.debug('monitor returns after sleeping %d sec', i)
      return dict(
         last_update=Globals.asterisk.last_update,
         time=time(),
         channels=Globals.asterisk.channels)

   @expose('json')
   def originate(self, channel, exten):
      '''
      '''
      log.debug('Call from extension %s to %s' % (channel, exten))
      res = Globals.manager.originate(
            channel.encode('iso-8859-1'), # Channel
            exten, # Extension
            context='stdexten',
            priority='1',
            caller_id='Standard'
            )
      log.debug(res)
      status = 0 if res=='Success' else 1
      return dict(status=status)

   @expose('json')
   def redirect(self, channel, exten):
      '''
      '''
      log.debug('Redirect %s to %s' % (channel, exten))
      res = Globals.manager.redirect( 
      #channel, exten, priority='1', extra_channel='', context=''):
            channel.encode('iso-8859-1'), # Channel
            exten, # Extension
            context='stdexten',
            priority='1',
            )
      log.debug(res)
      status = 0 if res=='Success' else 1
      return dict(status=status)



