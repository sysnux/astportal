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


from astportal2.controllers.cdr import Display_CDR
from astportal2.controllers.billing import Billing_ctrl
from astportal2.controllers.user import User_ctrl
from astportal2.controllers.phone import Phone_ctrl
from astportal2.controllers.department import Dptm_ctrl
from astportal2.controllers.groups import Group_ctrl
from astportal2.controllers.monitor import Monitor_ctrl
from astportal2.controllers.phonebook import Phonebook_ctrl
from astportal2.controllers.db_schema import DB_schema


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
   users = User_ctrl()
   phones = Phone_ctrl()
   departments = Dptm_ctrl()
   groups = Group_ctrl()
   monitor = Monitor_ctrl()
   phonebook = Phonebook_ctrl()

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
      return dict(page='login', login_counter=str(login_counter),
          came_from=came_from)
 
   @expose()
   def post_login(self, came_from='/'):
      """
      Redirect the user to the initially requested page on successful
      authentication or redirect her back to the login page if login failed.
       
      """
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

   @expose('astportal2.templates.tabs')
   def tabs(self):
      from tw.jquery.ui import ui_tabs_js
      from tw.uitheme import uilightness_css
      uilightness_css.inject()
      ui_tabs_js.inject()
      return dict(title=u'Test tabs', debug=None)

