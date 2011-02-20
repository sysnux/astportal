# -*- coding: utf-8 -*-

from tg import config, expose
from tg.controllers import TGController
from tgext.menu import navbar, sidebar, menu

from repoze.what.predicates import in_group

from astportal2.lib.app_globals import Globals

from time import sleep

import logging
log = logging.getLogger(__name__)


class Monitor_ctrl(TGController):
 
   allow_only = in_group('admin',msg=u'Veuiller vous connecter pour continuer')

   @sidebar(u'-- Administration || Surveillance', sortorder = 11,
      icon = '/images/astronomy_section.png')
   @expose(template="astportal2.templates.monitor")
   def index(self):
      '''
      '''
      return dict( title=u'Appels en cours', debug='')


   @expose('json')
   def update_channels(self, last):
      ''' Function called on AJAX request made by template.
      Return when new updates available, or timeout
      '''
      last = float(last) or 0;
      i = 0
      for i in xrange(50):
         sleep(1)
         last_update = float(Globals.asterisk.last_update)
         if last_update > last: break
      log.debug('monitor returns after sleeping %d sec', i)
      return dict(last_update=last_update, channels=Globals.asterisk.channels)

