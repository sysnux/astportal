"""Example of a simplistic, importable authenticator plugin

Intended to work like a quick-started SQLAlchemy plugin"""
from repoze.who.plugins.sa import (
    SQLAlchemyAuthenticatorPlugin,
    SQLAlchemyUserMDPlugin,
)
from repoze.what.plugins.sql import configure_sql_adapters
from repoze.what.middleware import AuthorizationMetadata

from astportal2 import model
auth_plugin = SQLAlchemyAuthenticatorPlugin(model.User, model.DBSession)
md_plugin = SQLAlchemyUserMDPlugin(model.User, model.DBSession )
_source_adapters = configure_sql_adapters(
    model.User,
    model.Group,
    model.Permission,
    model.DBSession,
)
md_group_plugin = AuthorizationMetadata(
    {'sqlauth': _source_adapters['group']},
    {'sqlauth': _source_adapters['permission']},
)

# THIS IS CRITICALLY IMPORTANT!  Without this your site will
# consider every repoze.what predicate True!
from repoze.what.plugins.pylonshq import booleanize_predicates
booleanize_predicates()

#class CAS_metadata(object):
#   print ' * * * class CAS_metadata'
#
#   def __init__(self):
#      print ' * * * class CAS_metadata __init__'
#      self.mapping = {}
#
#   def register_user( self, open_id, sreg_data ):
#      """Add SReg extension data to our mapping information"""
#      print ' * * * class CAS_metadata register_user'
#      self.mapping[ open_id ] = sreg_data
#      current = model.User.by_user_name( open_id )
#      if current:
#          # TODO: could update the in-db values...
#          if current.password:
#              return False
#          return True
#      else:
#          values = self.as_user_values( sreg_data, {} )
#          model.DBSession.add(
#              model.User(
#                  user_name = open_id,
#                  **values
#              )
#          )
#          transaction.commit()
#          return True
#
#   def as_user_values( self, values, identity ):
#      """Given sreg values, convert to User properties"""
#      print ' * * * class CAS_metadata as_user_values'
#      for id_key,sreg_key in self.key_map.items():
#          value = values.get( sreg_key )
#          if value is not None:
#              identity[id_key] = value
#      return identity
#
#   def add_metadata( self, environ, identity ):
#      """Add our stored metadata to given identity if available"""
#      key = identity.get('repoze.who.userid')
#      u = model.User.by_user_name(key)
#      print ' * * * class CAS_metadata add_metadata User "%s"=%s' % (key, u)
#      if u:
#         identity['user_id'] = u.user_id
#         identity['user_name'] = u.user_name
#         identity['display_name'] = u.display_name
#         identity['groups'] = u.groups
##      if key:
##         values = self.mapping.get( key )
##         if values:
##            identity = self.as_user_values( values, identity )
#      return identity
#
