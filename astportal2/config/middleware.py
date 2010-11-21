# -*- coding: utf-8 -*-
"""WSGI middleware initialization for the astportal2 application."""

from astportal2.config.app_cfg import base_config
from astportal2.config.environment import load_environment


__all__ = ['make_app']

# Use base_config to setup the necessary PasteDeploy application factory. 
# make_base_app will wrap the TG2 app with all the middleware it needs. 
make_base_app = base_config.setup_tg_wsgi_app(load_environment)


def make_app(global_conf, full_stack=True, **app_conf):
    """
    Set astportal2 up with the settings found in the PasteDeploy configuration
    file used.
    
    :param global_conf: The global settings for astportal2 (those
        defined under the ``[DEFAULT]`` section).
    :type global_conf: dict
    :param full_stack: Should the whole TG2 stack be set up?
    :type full_stack: str or bool
    :return: The astportal2 application with all the relevant middleware
        loaded.
    
    This is the PasteDeploy factory for the astportal2 application.
    
    ``app_conf`` contains all the application-specific settings (those defined
    under ``[app:main]``.
    
   
    """
    app = make_base_app(global_conf, full_stack=True, **app_conf)
    
    # Wrap your base TurboGears 2 application with custom middleware here
    
    # Start Asterisk manager thread(s)
    import astportal2.manager.manager_thread
    mt1 = astportal2.manager.manager_thread.manager_thread('asterisk.sysnux.pf', 'cel', 'cel')
    mt1.start()
#    mt2 = astportal2.manager.manager_thread.manager_thread('asterisk.sysnux.pf', 'astmaster', 'astman')
#    mt2.start()


    return app
