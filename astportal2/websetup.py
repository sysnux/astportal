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
    
   actions = ((u'Début', u''),
      (u'Annonce', u'Joue un fichier ou un message'),
      (u'Menu', u'Joue un fichier, saute vers choix'),
      (u'Saisie', u'Joue un fichier, attend entrée'),
      (u'Raccroché', u'Fin de communication'),
      (u'Synthèse', u'Lit le texte'),
      (u'Enregistrement', u'joue message, puis enregistre appelant'),
      (u'Transfert', u'appel nouveau numéro, puis transfert'),
      (u'Service', u'requête web'),
      (u'Boucle', u'Répétition action'),
      (u'Décision', u'Test variable, puis action'),
      (u'Planification', u'Décision basée sur date / heure'),
      (u'Bloc', u'Création nouveau bloc'),
      (u'Variable', u'Création / modification d\'une variable'),
      (u'Saut', u'Saut vers action'),
      (u'Sélection', u'Joue un fichier, stocke choix'),
      (u'Etiquette', u'Cible pour l\'application "saut"'),
      (u'En base', u'Sauvegarde variable en base de données'),
      (u'Jour férié', u'Vérification jour férié'),
      (u'Messagerie', u'Dépôt message vocal'),
      (u'Groupe', u'Transfert groupe d\'appel'),
   )
   for i, a in enumerate(actions):
      act = model.Action()
      act.action_id = i
      act.name = a[0]
      act.comment = a[1]
      model.DBSession.add(act)

   q_events = 'UNKOW ABANDON AGENTDUMP AGENTLOGIN AGENTCALLBACKLOGIN AGENTLOGOFF AGENTCALLBACKLOGOFF COMPLETEAGENT COMPLETECALLER CONFIGRELOAD CONNECT ENTERQUEUE EXITWITHKEY EXITWITHTIMEOUT QUEUESTART SYSCOMPAT TRANSFER PAUSE UNPAUSE RINGNOANSWER EXITEMPTY PAUSEALL UNPAUSEALL ADDMEMBER REMOVEMEMBER INCOMING CLOSED DISSUASION INFO'.split()
   for i, e in enumerate(q_events):
      qe = model.Queue_event()
      qe.qe_id = i+1
      qe.event = e
      model.DBSession.add(qe)

   model.DBSession.flush()
   transaction.commit()

   print "Successfully setup"
