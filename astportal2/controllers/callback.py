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
   ''' Call each queued call if not busy
   Called from scheduler (lib/app_globals)
   '''

   busy = [chan[-17:-9] for chan in Globals.asterisk.channels.keys()]
   log.debug('Do it: %s, busy=%s' % (callbacks.queue, busy))
   requeue = []

   while not callbacks.empty():
      chan, dst_chan, dst_exten, uid = callbacks.get_nowait()
      if dst_chan in busy:
         requeue.append((chan, dst_chan, dst_exten, uid))
         continue
      log.debug('Processing src=%s, dst=%s (%s), (uid %s)' % (chan, dst_exten, dst_chan, uid))
      res = Globals.manager.originate(
            'PJSIP/' + chan.encode('iso-8859-1'), # Channel
            dst_exten.encode('iso-8859-1'), # Extension
            context=chan.encode('iso-8859-1'),
            priority='1',
            caller_id=''
            )

   for chan, dst_chan, dst_exten, uid in requeue:
      callbacks.put_nowait((chan, dst_chan, dst_exten, uid))

class Callback_ctrl(BaseController):

   @expose()
   def _default(self, *args):

      log.error(u'_default: request=%s' % request.environ)
      log.error(args)

      return 'ko'

   @expose()
   def new(self, src, dstchan, dstexten, uid):
      ''' Queue calls for later automatic recall
      Called from Asterisk dialplan
      '''

      # Need better authentication?
      if request.environ['REMOTE_ADDR']!='127.0.0.1' or \
         not request.environ['HTTP_USER_AGENT'].startswith('asterisk-libcurl-agent'):
         log.error(u'Forbidden callback %s' % request.environ)
         return 'ko'

      log.info('New callback %s -> %s:%s (%s)' %(src, dstchan, dstexten, uid))
      callbacks.put_nowait((src, dstchan, dstexten, uid))

      return 'ok'

