# -*- coding: utf-8 -*-

from tg import config, expose
from tg.controllers import TGController

from repoze.what.predicates import in_group

#from astportal2.model import DBSession, User, Group, Application, Record, CDR
from astportal2.manager import manager

from time import sleep

import logging
log = logging.getLogger(__name__)


class Monitor_ctrl(TGController):
 
   allow_only = in_group('admin',msg=u'Veuiller vous connecter pour continuer')

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
         if float(manager.last_update) > last: break
      log.debug('monitor returns after sleeping %d sec', i)
      return dict(last_update=manager.last_update, channels=manager.channels)

