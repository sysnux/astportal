# -*- coding: utf-8 -*-

from tg import config, expose
from tg.controllers import TGController

try:
   from tg.predicates import in_group
except ImportError:
   from repoze.what.predicates import in_group

#from astportal2.model import DBSession, User, Group, Application, Record, CDR

import logging
log = logging.getLogger(__name__)


class DB_schema(TGController):
   
   allow_only = in_group('admin',msg=u'Veuiller vous connecter pour continuer')

   @expose(template="astportal2.templates.db_schema")
   def index(self):
      '''
      '''
      return dict( title=u'Schéma de la base de données', debug='')


   @expose('json')
   def fetch_db(self):
      ''' Function called on AJAX request made by template.
      Fetch information from DB
      '''

      db_url = config.get('sqlalchemy.url')
      log.debug(u'fetch_db ' + db_url)
      from sqlalchemy import MetaData
      metadata=MetaData(db_url)
      metadata.reflect()
      db_tables = metadata.tables.values()
         
      tables = {} # Dict of tables
      fk = [] # Foreign keys
      for t in db_tables:
         log.debug(u'Table %s' % t.name)
         tables[t.name] = {}
         tables[t.name]['cols'] = []
         for c in t.columns:
            log.debug(u' . Champ %s (%s)' % (c.name, c.type))
            tables[t.name]['cols'].append({'name': c.name, 
               'type': str(c.type).lower()})
         for k in t.foreign_keys:
            from_ = '%s_%s'  % (t.name, k.column.name)
            to =  k.target_fullname.replace('.','_')
            log.debug(u' + Clé %s -> %s' % (from_, to))
            fk.append({'from': from_, 'to': to})

      return dict(tables=tables, fk=fk)


