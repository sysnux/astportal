# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from tgext.menu import sidebar
from pylons.i18n import ugettext as _, lazy_ugettext as l_

from repoze.what.predicates import is_anonymous, in_group

from astportal2.lib.base import BaseController

from astportal2.controllers.error import ErrorController
from astportal2.controllers.secure import SecureController

__all__ = ['RootController']

import logging
log = logging.getLogger(__name__)


from astportal2.controllers.cdr import Display_CDR
from astportal2.controllers.billing import Billing_ctrl
from astportal2.controllers.user import User_ctrl
from astportal2.controllers.voicemail import Voicemail_ctrl
from astportal2.controllers.phone import Phone_ctrl
from astportal2.controllers.department import Dptm_ctrl
from astportal2.controllers.groups import Group_ctrl
from astportal2.controllers.monitor import Monitor_ctrl
from astportal2.controllers.phonebook import Phonebook_ctrl
from astportal2.controllers.moh import MOH_ctrl
from astportal2.controllers.stats import Stats_ctrl
from astportal2.controllers.db_schema import DB_schema
from astportal2.controllers.queues import Queue_ctrl
from astportal2.controllers.pickups import Pickup_ctrl
from astportal2.controllers.holidays import Holiday_ctrl
from astportal2.controllers.cc_monitor import CC_Monitor_ctrl
from astportal2.controllers.cc_stats import CC_Stats_ctrl
from astportal2.controllers.application import Application_ctrl
from astportal2.controllers.forward import Forward_ctrl
from astportal2.controllers.record import Record_ctrl
from astportal2.controllers.incident import Incident_ctrl


class RootController(BaseController):
   """
   The root controller for the astportal2 application.
   
   All the other controllers and WSGI applications should be mounted on this
   controller. For example::
   
       panel = ControlPanelController()
       another_app = AnotherWSGIApplication()
   
   Keep in mind that WSGI applications shouldn't be mounted directly: They
   must be wrapped around with :class:`tg.controllers.WSGIAppController`.
   
   """

   cdr = Display_CDR()
   billing = Billing_ctrl()
   voicemail = Voicemail_ctrl()
   users = User_ctrl()
   phones = Phone_ctrl()
   departments = Dptm_ctrl()
   groups = Group_ctrl()
   monitor = Monitor_ctrl()
   phonebook = Phonebook_ctrl()
   moh = MOH_ctrl()
   stats = Stats_ctrl()
   queues = Queue_ctrl()
   pickups = Pickup_ctrl()
   holidays = Holiday_ctrl()
   applications = Application_ctrl()
   cc_monitor = CC_Monitor_ctrl()
   cc_stats = CC_Stats_ctrl()
   forwards = Forward_ctrl()
   records = Record_ctrl()
   incidents = Incident_ctrl()

   db_schema = DB_schema()

   error = ErrorController()

   @sidebar(u'Accueil', sortorder = 0,
      icon = '/images/home-mdk.png')
   @expose('astportal2.templates.index')
   def index(self):
      """Handle the front-page."""
      if is_anonymous(msg=u'Veuiller vous connecter pour continuer'):
         redirect('/login')
      return dict(page='index')

   @expose('astportal2.templates.login')
   def login(self, came_from=url('/')):
      """Start the user login."""
      login_counter = request.environ['repoze.who.logins']
      if login_counter > 0:
          flash(_("Erreur d'authentification"), 'warning')
      log.debug('login: counter=%d, from=%s' % (login_counter, came_from))
      return dict(page='login', login_counter=str(login_counter),
          came_from=came_from)
 
   @expose()
   def post_login(self, came_from='/'):
      """
      Redirect the user to the initially requested page on successful
      authentication or redirect her back to the login page if login failed.
       
      """
      log.debug('post_login: from=%s' % (came_from))
      if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect('/login', came_from=came_from, __logins=login_counter)
      userid = request.identity['repoze.who.userid']
      flash(u'Bienvenue, %s !' % userid)
      redirect(came_from)

   @expose()
   def post_logout(self, came_from=url('/')):
      """
      Redirect the user to the initially requested page on logout and say
      goodbye as well.
       
      """
      flash(u'A bientôt')
      redirect('/login')

