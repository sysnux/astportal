# -*- coding: utf-8 -*-

"""The application's Globals object"""

__all__ = ['Globals']


import tgscheduler
import logging
log = logging.getLogger(__name__)
from tg import config


def manager_check():
    '''Check manager connection and try to reconnect if needed
    
    Function called by tgscheduler
    '''

    # Start Asterisk manager thread(s)
    from astportal2.pyst import manager
    from astportal2.lib.app_globals import Globals
    if Globals.manager is not None and Globals.manager.connected():
       return

    if Globals.asterisk is None:
       from astportal2.lib import asterisk
       Globals.asterisk = asterisk.Status()

    try:
       man = eval(config.get('asterisk.manager'))
       log.debug(man[0])
       Globals.manager = manager.Manager()
       log.debug('Connect...')
       Globals.manager.connect(man[0][0])
       log.debug('Login...')
       Globals.manager.login(man[0][1],man[0][2])
       log.debug('Register events...')
       Globals.manager.register_event('*', Globals.asterisk.handle_event)
       log.debug('Request status...')
       Globals.manager.status()
       Globals.manager.send_action({'Action': 'QueueStatus'})
       log.info('Connected to Asterisk manager on "%s"' % man[0][0])
#       for m in man:
#          mt = astportal2.manager.manager_thread.manager_thread(m[0], m[1], m[2])
#          mt.start()
#          log.info('Connected to Asterisk manager on "%s"' % m[0])
    except manager.ManagerSocketException, (errno, reason):
       Globals.manager = None
       log.error('Error connecting to the manager: %s' % reason)
    except manager.ManagerAuthException, reason:
       Globals.manager = None
       log.error('Error logging in to the manager: %s' % reason)
    except manager.ManagerException, reason:
       Globals.manager = None
       log.error('Error: %s' % reason)
    except:
       Globals.manager = None
       log.error('Configuration error, manager thread NOT STARTED (check asterisk.manager)')

class Globals(object):
   """Container for objects available throughout the life of the application.

   One instance of Globals is created during application initialization and
   is available during requests via the 'app_globals' variable.

   """

   manager = None
   asterisk = None

   def __init__(self):
      """Start the scheduler."""
        
      tgscheduler.start_scheduler()
      tgscheduler.add_interval_task(action=manager_check, 
         taskname='Manager check', interval=20, initialdelay=1)


