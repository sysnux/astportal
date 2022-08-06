# -*- coding: utf-8 -*-

"""The application's Globals object"""

__all__ = ['Globals']


import tgscheduler
import logging
log = logging.getLogger(__name__)
from tg import config
from astportal2.pyst import manager

from time import time
import re
import json
re_uri = re.compile('sip:(\w+)@([\w\.]+):?(\d+$)?')
# key  : /registrar/contact/6Ewwh7Jl;@sip:6Ewwh7Jl@172.22.6.17:5060
#re_contact_key = re.compile('key\s*:\s*/registrar/contact/(\w+);@sip:\w+@.+:\d+$')
# value: {"uri":"sip:6Ewwh7Jl@172.22.6.17:5060","qualify_timeout":"3000","outbound_proxy":"","expiration_time":"1432150792","qualify_frequency":"60","path":"","user_agent":"Grandstream GXP2140 1.0.4.23"}
re_contact_value = re.compile('value\s*:\s*({.*})')


def Markup(s):
    return s


def fetch_contacts():
    ''' Fetch phone information from Asterisk database
    Needed for PJSIP phones, else we don't have model and IP address
    '''

    if time() - Globals.last_refresh < 60:
       return

    if not Globals.manager:
       log.warning('Asterisk Manager not available')
       return

    # Refresh status
    log.info('fetch_contacts: refresh status')
    Globals.last_refresh = time()

    Globals.manager.send_action({'Action': 'DeviceStateList'})

    # Fetch contacts from AstDB
    log.debug('Fetching contacts from AstDB (PJSIP)')
    man = Globals.manager.command(
       '''database query "select key, value from astdb where key like '/registrar/contact/%'"''')
    names = []
    peers = Globals.asterisk.peers
    for i, r in enumerate(man.response):
       log.debug(' . %d: %s', i, r)
       m = re_contact_value.search(r)
       if m:
          d = json.loads(m.groups()[0])
          name, ip, port = re_uri.match(d['uri']).groups()
          log.debug('Contact %s @ %s is a "%s"', name, ip, d['user_agent'])
          name = 'PJSIP/' + name
          if name in peers:
             peers[name]['Address'] = ip
             peers[name]['UserAgent'] = d['user_agent']
          else:
             peers[name] = {'Address': ip, 'UserAgent': d['user_agent']}
          names.append(name)
 
    # Remove old entries
    for name in peers:
       if name not in names:
          peers[name]['Address'] = None
          peers[name]['UserAgent'] = None


def manager_check():
    '''Check manager connection and try to reconnect if needed
    
    Function called by tgscheduler
    '''

    from astportal2.lib.app_globals import Globals # Leave me here!

    if Globals.manager is not None and Globals.manager.connected():
       return

    # Start Asterisk manager thread(s)
    if Globals.asterisk is None:
       from astportal2.lib import asterisk
       Globals.asterisk = asterisk.Status()

    log.error('Not connected to manager, resetting global data')
    Globals.asterisk.reset()

    # Connect to manager
    try:
       man = eval(config.get('asterisk.manager'))
       log.debug(man[0])
       Globals.manager = manager.Manager()
       log.debug('Connect...')
       if ':' in man[0][0]:
          host, port = man[0][0].split(':')
          port = int(port)
       else:
          host, port = man[0][0], 5038
       Globals.manager.connect(host, port)
       log.debug('Login...')
       Globals.manager.login(man[0][1],man[0][2])
       log.debug('Register events...')
       Globals.manager.register_event('*', Globals.asterisk.handle_event)
       log.debug('Request status...')
       Globals.manager.status()
       Globals.manager.send_action({'Action': 'QueueStatus'})
       log.info('Connected to Asterisk manager on "%s"', man[0][0])
#       for m in man:
#          mt = astportal2.manager.manager_thread.manager_thread(m[0], m[1], m[2])
#          mt.start()
#          log.info('Connected to Asterisk manager on "%s"' % m[0])
    except manager.ManagerSocketException, (errno, reason):
       Globals.manager = None
       log.error('Error connecting to the manager: %s', reason)
    except manager.ManagerAuthException, reason:
       Globals.manager = None
       log.error('Error logging in to the manager: %s', reason)
    except manager.ManagerException, reason:
       Globals.manager = None
       log.error('Error: %s', reason)
    except:
       Globals.manager = None
       log.error('Configuration error, manager thread NOT STARTED (check asterisk.manager)')

    fetch_contacts()


class Globals(object):
   """Container for objects available throughout the life of the application.

   One instance of Globals is created during application initialization and
   is available during requests via the 'app_globals' variable.

   """

   last_refresh = 0
   asterisk = None # Asterisk objects (channels, queues, peers...)
   manager = None # AMI object
   ws_clients = {'channels': [], 'queues': []} # List of WebSocket subscriptions

   def __init__(self):
      """Start the scheduler."""

      tgscheduler.start_scheduler()

      tgscheduler.add_interval_task(action=manager_check,
         taskname='Manager check', interval=20, initialdelay=1)

#      from astportal2.controllers.websocket import update
#      tgscheduler.add_interval_task(action=update,
#         taskname='WebSocket ping', interval=1, initialdelay=10)

      from astportal2.controllers.callback import do
      tgscheduler.add_interval_task(action=do, 
         taskname='Callback do', interval=13, initialdelay=37)

#      from astportal2.controllers.grandstream import do
#      tgscheduler.add_interval_task(action=do, 
#         taskname='GXP action do', interval=3, initialdelay=17)

      from astportal2.lib.grandstream import do_gxp_actions
      tgscheduler.add_interval_task(action=do_gxp_actions, 
         taskname='GXP actions', interval=3, initialdelay=41)
