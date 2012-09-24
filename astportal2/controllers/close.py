# -*- coding: utf-8 -*-
# Open / Close controller

from tg import expose, flash, redirect, tmpl_context
from tgext.menu import sidebar

from repoze.what.predicates import in_any_group

from tw.forms import TableForm, CheckBoxList

import logging
log = logging.getLogger(__name__)
import re

from astportal2.lib.app_globals import Globals
from astportal2.lib.base import BaseController

re_db = re.compile(r'(\w*)\s*: (\S*)')

closed = dict(
      AGENCE30 = u'agence Pomare 06730',
      AGENCE38 = u'agence Mamao 06738',
      AGENCE46 = u'agence Fare Ute 06746',
      AGENCE43 = u'agence Pirae 06743',
      AGENCE50 = u'agence Arue 06750',
      AGENCE34 = u'agence Mahina 06734',
      AGENCE44 = u'agence Cathédrale 06744',
      AGENCE32 = u'agence Bruat 06732',
      AGENCE33 = u'agence Faa\'a 06733',
      AGENCE36 = u'agence Moana Nui 06736',
      AGENCE51 = u'agence Punaauia plaine 06751',
      AGENCE31 = u'agence Maharepa 06731',
      AGENCE49 = u'agence Tiahura 06749',
      AGENCE39 = u'agence Paea 06739',
      AGENCE41 = u'agence Papara 06741',
      AGENCE37 = u'agence Taravao 06737',
      AGENCE35 = u'agence Raiatea 06735',
      AGENCE40 = u'agence Bora-Bora 06740',
      )


class Close_ctrl(BaseController):


   @sidebar(u'-- Groupes d\'appels || Fermeture',
      icon = '/images/script-error.png', sortorder = 16)
   @expose(template="astportal2.templates.form_new")
   def index(self, **kw):
      ''' Display closed form
      '''

      sv = ['admin']
      for q in Globals.asterisk.queues:
         sv.append('SV ' + q)
      if not in_any_group(*sv):
         tmpl_context.form = TableForm(submit_text=None)
         flash(u'Accès interdit !', 'error')
         redirect('/')

      checked = None
      man = Globals.manager.command('database show closed')
      checked = []
      for i,r in enumerate(man.response[3:-2]):
         match = re_db.search(r)
         if match:
            k, v = match.groups()
            log.debug('Line %d match: %s -> %s' % (i, k, v))
            if v == '1': checked.append(k)
         else:
            log.debug('Line %d no match: %s' % (i, r))

      tmpl_context.form = TableForm(
         name = 'close_form',
         fields = [
            CheckBoxList('checked',
               options = [(k,v) for k,v in sorted(closed.iteritems())], 
               label_text = u'Agences fermées', 
               help_text = u'Cochez une agence'),
            ],
         submit_text = u'Valider...',
         action = 'modify',
         hover_help = True,
         )

      return dict(title='Fermeture d\'agence', debug='',
            values={'checked': checked})


   @expose()
   def modify(self, checked=[], **kw):
      ''' Modify Asterisk database (closed)
      '''

      for i in closed.keys():
         v = 1 if i in checked else 0
         res = Globals.manager.command('database put %s %s %d' % (
            'closed', i, v))
         log.debug('database put %s %s %s returns %s' % (
               'closed', i, v, res))

      flash(u'Fermetures d\'agence modifiées', 'warning')
      redirect('/closed/')

