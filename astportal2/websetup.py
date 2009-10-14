# -*- coding: utf-8 -*-
"""Setup the astportal2 application"""

import logging

import transaction
from tg import config

from astportal2.config.environment import load_environment

__all__ = ['setup_app']

log = logging.getLogger(__name__)


def setup_app(command, conf, vars):
    """Place any commands to setup astportal2 here"""
    load_environment(conf.global_conf, conf.local_conf)
    # Load the models
    from astportal2 import model
    print "Creating tables"
    model.metadata.create_all(bind=config['pylons.app_globals'].sa_engine)

    manager = model.User()
    manager.user_id = -1
    manager.user_name = u'admin'
    manager.display_name = u'Administrateur'
    manager.email_address = u'admin@somedomain.com'
    manager.password = u'0000'

    model.DBSession.add(manager)

    group = model.Group()
    group.group_id = -1
    group.group_name = u'Admin'
    group.display_name = u'Groupe des dministrateurs'

    group.users.append(manager)

    model.DBSession.add(group)

    model.DBSession.flush()

    transaction.commit()
    print "Successfully setup"
