# -*- coding: utf-8 -*-
# Callback controller

from tg import expose, request #, redirect, tmpl_context

import logging
log = logging.getLogger(__name__)
from Queue import Queue

from astportal2.lib.app_globals import Globals
from astportal2.model import DBSession
from astportal2.lib.base import BaseController

callbacks = Queue()

def do():
   ''' Called from scheduler (lib/app_globals)
   '''
   log.debug('Do it!')
   while not callbacks.empty():
      c = callbacks.get_nowait()
      log.debug('Processing src=%s, dst=%s, (uid %s)' % (c[0], c[1], c[2]))

class Callback_ctrl(BaseController):

   @expose()
   def _default(self, *args):

      log.error(u'_default: request=%s' % request.environ)
      log.error(args)

      return 'ko'

   @expose()
   def new(self, src, dst, uid):
      ''' Called from Asterisk dialplan
      Need better authentication?
      '''

      if request.environ['REMOTE_ADDR']!='127.0.0.1' or \
         not request.environ['HTTP_USER_AGENT'].startswith('asterisk-libcurl-agent'):
	 log.error(u'Forbidden callback %s' % request.environ)
         return 'ko'

      log.info('New callback %s -> %s (%s)' %(src, dst, uid))
      callbacks.put_nowait((src, dst, uid))

      return 'ok'

