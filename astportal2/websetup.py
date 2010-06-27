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

    u = model.User()
    u.user_id = -1
    u.user_name = u'admin'
    u.display_name = u'Administrateur'
    u.email_address = u'admin@somedomain.com'
    u.password = u'0000'
    model.DBSession.add(u)

    g = model.Group()
    g.group_id = -1
    g.group_name = u'admin'
    g.display_name = u'Groupe des administrateurs'
    g.users.append(u)
    model.DBSession.add(g)

    d = model.Department()
    d.dptm_id = -1
    d.name = u'Divers'
    d.comment = u'Téléphones divers'
    model.DBSession.add(d)

    model.DBSession.flush()
    transaction.commit()

    print "Successfully setup"
