# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_

from tgext.admin import AdminController
from tgext.admin.tgadminconfig import TGAdminConfig, CrudRestControllerConfig

from repoze.what import predicates

from astportal2.lib.base import BaseController
from astportal2.model import DBSession, metadata, User, Group, Phone, Department

from astportal2.controllers.error import ErrorController
from astportal2.controllers.secure import SecureController

from astportal2.controllers.cdr import Display_CDR
from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

__all__ = ['RootController']


from astportal2.controllers.user import User_ctrl
from astportal2.controllers.phone import Phone_ctrl
from astportal2.controllers.department import Dptm_ctrl
from astportal2.controllers.groups import Group_ctrl


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
    secc = SecureController()
 
    users = User_ctrl()
    phones = Phone_ctrl()
    departments = Dptm_ctrl()
    groups = Group_ctrl()


    error = ErrorController()

    cdr = Display_CDR()

    @expose('astportal2.templates.index')
    def index(self):
        """Handle the front-page."""
        return dict(page='index')

    @expose('astportal2.templates.welcome')
    def welcome(self):
        """Handle the front-page."""
        return dict(page='index')

    @expose('astportal2.templates.login')
    def login(self, came_from=url('/')):
        """Start the user login."""
        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        return dict(page='login', login_counter=str(login_counter),
                    came_from=came_from)
    
    @expose()
    def post_login(self, came_from=url('/')):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.
        
        """
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect(url('/login', came_from=came_from, __logins=login_counter))
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
