# -*- coding: utf-8 -*-
# Incidents controller

from tg import expose, flash, redirect, tmpl_context
from tgext.menu import sidebar

from repoze.what.predicates import in_group

from tw.forms import TableForm, CheckBoxList

import logging
log = logging.getLogger(__name__)
import re

from astportal2.lib.app_globals import Globals
from astportal2.lib.base import BaseController

re_db = re.compile(r'(\w*)\s*: (\S*)')

incidents = dict(
      PCA = u'Plan de continuité d\'activité',
      AUTOR = u'Autorisations cartes bancaires',
      AMEX = u'American Express',
      EMV = u'Europay MasterCard Visa',
      )


class Incident_ctrl(BaseController):


   allow_only = in_group('admin', 
         msg=u'Vous devez appartenir au groupe "admin" pour gérer les incidents')

   @sidebar(u'-- Administration || Incidents',
      icon = '/images/script-error.png', sortorder = 16)
   @expose(template="astportal2.templates.form_new")
   def index(self, **kw):
      ''' Display incident form
      '''

      checked = []
      man = Globals.manager.command('database show incidents')
      for i,r in enumerate(man.response[3:-2]):
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            log.debug('Line %d match: %s -> %s' % (i, k, v))
            if v == '1': checked.append(k)
         else:
            log.debug('Line %d no match: %s' % (i, r))

      tmpl_context.form = TableForm(
         name = 'incident_form',
         fields = [
            CheckBoxList('checked',
               options = [(k,v) for k,v in sorted(incidents.iteritems())], 
               label_text = u'Incidents en cours', 
               help_text = u'Cochez les incidents'),
            ],
         submit_text = u'Valider...',
         action = 'modify',
         hover_help = True,
         )

      return dict(title='Incidents', debug='',
            values={'checked': checked})


   @expose()
   def modify(self, checked=[], **kw):
      ''' Modify Asterisk database (incidents)
      '''

      for i in incidents.keys():
         v = 1 if i in checked else 0
         res = Globals.manager.command('database put %s %s %d' % (
            'incidents', i, v))
         log.debug('database put %s %s %s returns %s' % (
               'incidents', i, v, res))

      flash(u'Incidents modifiés', 'warning')
      redirect('/incidents/')

