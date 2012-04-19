# -*- coding: utf-8 -*-
"""
Global configuration file for TG2-specific settings in astportal2.

This file complements development/deployment.ini.

Please note that **all the argument values are strings**. If you want to
convert them into boolean, for example, you should use the
:func:`paste.deploy.converters.asbool` function, as in::
    
    from paste.deploy.converters import asbool
    setting = asbool(global_conf.get('the_setting'))
 
"""

from tg.configuration import AppConfig

import astportal2
from astportal2 import model
from astportal2.lib import app_globals, helpers 

base_config = AppConfig()
base_config.renderers = []

base_config.package = astportal2

#Set the default renderer
base_config.default_renderer = 'genshi'
base_config.renderers.append('genshi')
# if you want raw speed and have installed chameleon.genshi
# you should try to use this renderer instead.
# warning: for the moment chameleon does not handle i18n translations
#base_config.renderers.append('chameleon_genshi')

#Configure the base SQLALchemy Setup
base_config.use_sqlalchemy = True
base_config.model = astportal2.model
base_config.DBSession = astportal2.model.DBSession


# YOU MUST CHANGE THIS VALUE IN PRODUCTION TO SECURE YOUR APP
base_config.sa_auth.cookie_secret = "AstPortal (c) SysNux \o/"

import tgext.menu
base_config.variable_provider = tgext.menu.menu_variable_provider
# base_config.tgext_menu = {}
# base_config.tgext_menu['inject_css'] = True

