# -*- coding: utf-8 -*-
# User CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, require, config, session
from tg.controllers import RestController
from tgext.menu import sidebar

from repoze.what.predicates import in_group, not_anonymous

from tw.api import js_callback
from tw.forms import TableForm, LabelHiddenField, SingleSelectField, TextField, CheckBoxList, PasswordField, HiddenField, TextArea, Label
from tw.forms.validators import Schema, NotEmpty, Email, Int, Regex, FieldsMatch

from genshi import Markup

from astportal2.model import DBSession, User, Phone, Group, Department
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.app_globals import Globals

import unicodedata
from shutil import rmtree

import logging
log = logging.getLogger(__name__)

dir_ast = config.get('directory.asterisk')
dir_vm = config.get('directory.voicemail')

# Common fields for user form, used by admin or not
common_fields = [
#   TextField('firstname',
#      label_text=u'Prénom', validator=NotEmpty,
#      help_text=u'Entrez le prénom de l\'utilisateur'),
#   TextField('lastname', validator=NotEmpty,
#      label_text=u'Nom de famille',
#      help_text=u'Entrez le nom de famille de l\'utilisateur'),
#   TextField('email_address', validator=Email,
#      label_text=u'Adresse email',
#      help_text=u'Entrez l\'adresse email de l\'utisateur'),
   PasswordField('pwd1', validator=Regex(r'\d{4,16}', not_empty=True),
      label_text=u'Mot de passe',
      help_text=u'Entrez le mot de passe'),
   PasswordField('pwd2', validator=Regex(r'\d{4,16}', not_empty=True),
      label_text=u'Confirmation mot de passe',
      help_text=u'Entrez à nouveau le mot de passe'),
   Label( text = u'(Le mot de passe ne doit contenir que des chiffres ; il est visible par les administrateurs)'),
   HiddenField('user_id', validator=Int),
   ]


# Fields for admin
admin_form_fields = [
   TextField('user_name', validator=NotEmpty,
      label_text=u'Compte',
      help_text=u'Entrez le nom d\'utilisateur'),
   TextField('firstname',
      label_text=u'Prénom', validator=NotEmpty,
      help_text=u'Entrez le prénom de l\'utilisateur'),
   TextField('lastname', validator=NotEmpty,
      label_text=u'Nom de famille',
      help_text=u'Entrez le nom de famille de l\'utilisateur'),
   TextField('email_address', validator=Email,
      label_text=u'Adresse email',
      help_text=u'Entrez l\'adresse email de l\'utisateur'),
   CheckBoxList('groups', validator=Int,
   options=DBSession.query(Group.group_id, 
      Group.group_name).order_by(Group.group_name),
   label_text=u'Groupes', 
   help_text=u'Cochez les groupes auxquels appartient l\'utilisateur')
]
admin_form_fields[4:2] = common_fields

# New user form (only for admin)
new_user_form = TableForm(
   validator = Schema(
      chained_validators = [FieldsMatch('pwd1', 'pwd2')]
   ),
   fields = admin_form_fields,
   submit_text = u'Valider...',
   action = '/users/create',
   hover_help = True
)

# Edit user form for admin
admin_edit_user_form = TableForm(
   validator = Schema(
      chained_validators = [FieldsMatch('pwd1', 'pwd2')]
   ),
   fields = admin_form_fields + 
      [HiddenField('_method', validator=None)], # Needed by RestController
   submit_text = u'Valider...',
   action = '/users/',
   hover_help = True
)

# Edit user form for normal user (not admin)
user_fields = [
   LabelHiddenField('firstname', suppress_label=False,
      label_text=u'Prénom',
      help_text=u'Entrez le prénom de l\'utilisateur'),
   LabelHiddenField('lastname',
      label_text=u'Nom de famille', suppress_label=False,
      help_text=u'Entrez le nom de famille de l\'utilisateur'),
   LabelHiddenField('email_address', suppress_label=False,
      label_text=u'Adresse email',
      help_text=u'Entrez l\'adresse email de l\'utisateur'),
   LabelHiddenField( 'groups',
      label_text=u'Groupes', suppress_label=False),
   HiddenField('_method', validator=None) # Needed by RestController
]
user_fields[3:2] = common_fields[:]
edit_user_form = TableForm(
   validator = Schema(
      chained_validators = [FieldsMatch('pwd1', 'pwd2')]
   ),
   fields = user_fields,
   submit_text = u'Valider...',
   action = '/users/',
   hover_help = True
)

def row(u):
   '''Displays a formatted row of the users list
   Parameter: User object
   '''
   if u.phone:
      phone = ', '.join(['<a href="/phones/%s/edit">%s (%s)</a>' % (
         p.phone_id, p.exten, p.dnis) for p in u.phone])
   else:
      phone = ''

   if u.groups:
      groups = ', '.join([g.group_name for g in u.groups])
   else:
      groups = ''
   js_name = u.display_name.replace("'","\\'") if u.display_name is not None else ''
   action =  u'<a href="'+ str(u.user_id) + u'/edit" title="Modifier">'
   action += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   action += u'&nbsp;&nbsp;&nbsp;'
   action += u'<a href="#" onclick="del(\''+ str(u.user_id) + \
         u'\',\'Suppression de ' + js_name + u'\')" title="Supprimer">'
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   if u.email_address:
      email = u'<a href="mailto:' + u.email_address 
      email += '">' + u.email_address + '</a>'
   else:
      email = ''

   return [Markup(action), u.user_name, u.display_name, 
         Markup(email), Markup(phone), groups]


class User_ctrl(RestController):

   allow_only = not_anonymous(msg=u'Veuiller vous connecter pour continuer')
   
   @sidebar(u'-- Administration || Utilisateurs', sortorder = 12,
      icon = '/images/preferences-desktop-user.png',
      permission = in_group('admin'))
   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all users
      '''
      if not in_group('admin'):
         redirect( str(request.identity['user'].user_id) + '/edit')

      grid = MyJqGrid( id='grid', url='fetch', caption=u'Utilisateurs',
            colNames = [u'Action', u'Compte', u'Nom', u'email', u'Poste', u'Groupes'],
            colModel = [
               { 'sortable': False, 'search': False, 'width': 80, 'align': 'center' },
               { 'name': 'user_name', 'width': 80 },
               { 'name': 'display_name', 'width': 120 },
               { 'name': 'email_address', 'width': 180 },
               { 'name': 'phone', 'width': 60, 'sortable': False, 'search': False },
               { 'name': 'groups', 'width': 160, 'sortable': False, 'search': False } ],
            sortname = 'user_name',
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': True, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des utilisateurs', debug='')


   @expose('json')
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut afficher la liste des utilisateurs'))
   def fetch(self, rows, page, sidx='user_name', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      # Try and use grid preference
      grid_rows = session.get('grid_rows', None)
      if rows=='-1': # Default value
         rows = grid_rows if grid_rows is not None else 25

      # Save grid preference
      session['grid_rows'] = rows
      session.save()
      rows = int(rows)

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * rows
      except:
         offset = 0
         page = 1
         rows = 25

      users = DBSession.query(User)
      if  searchOper and searchField and searchString:
         log.debug('fetch query <%s> <%s> <%s>' % \
            (searchField, searchOper, searchString))
         try:
            field = eval('User.' + searchField)
         except:
            field = None
            log.error('eval: User.' + searchField)
         if field and searchOper=='eq': 
            users = users.filter(field==searchString)
         elif field and searchOper=='ne':
            users = users.filter(field!=searchString)
         elif field and searchOper=='le':
            users = users.filter(field<=searchString)
         elif field and searchOper=='lt':
            users = users.filter(field<searchString)
         elif field and searchOper=='ge':
            users = users.filter(field>=searchString)
         elif field and searchOper=='gt':
            users = users.filter(field>searchString)
         elif field and searchOper=='bw':
            users = users.filter(field.ilike(searchString + '%'))
         elif field and searchOper=='bn':
            users = users.filter(~field.ilike(searchString + '%'))
         elif field and searchOper=='ew':
            users = users.filter(field.ilike('%' + searchString))
         elif field and searchOper=='en':
            users = users.filter(~field.ilike('%' + searchString))
         elif field and searchOper=='cn':
            users = users.filter(field.ilike('%' + searchString + '%'))
         elif field and searchOper=='nc':
            users = users.filter(~field.ilike('%' + searchString + '%'))
         elif field and searchOper=='in':
            users = users.filter(field.in_(str(searchString.split(' '))))
         elif field and searchOper=='ni':
            users = users.filter(~field.in_(str(searchString.split(' '))))

      total = users.count()/rows + 1
      column = getattr(User, sidx)
      users = users.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      data = [ { 'id'  : u.user_id, 'cell': row(u) } for u in users ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new")
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut créer un utilisateur'))
   def new(self, **kw):
      ''' Display new user form
      '''
      tmpl_context.form = new_user_form
      return dict(title = u'Nouvel utilisateur', debug=None, values=None)
 
   @validate(new_user_form, error_handler=new)
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut créer un utilisateur'))
   @expose()
   def create(self, pwd1, pwd2, **kw):
      ''' Add new user to DB
      '''
      log.info('new ' + kw['user_name'])
      u = User()
      u.user_name = kw['user_name']
      u.firstname = kw['firstname']
      u.lastname = kw['lastname']
      u.email_address = kw['email_address']
      u.password = pwd1
      #u.phone = [DBSession.query(Phone).get(kw['phone_id'])]
      if 'groups' in kw.keys():
         u.groups = DBSession.query(Group).\
               filter(Group.group_id.in_(kw['groups'])).all()
      DBSession.add(u)
      flash(u'Nouvel utilisateur "%s" créé' % (kw['user_name']))
      redirect('/users/')


   @sidebar('Compte', sortorder = 6, icon = '/images/user-identity.png')
   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit user form
      '''
      if not id: 
         if 'user_id' in kw:
            id = kw['user_id']
         else:
            id = request.identity['user'].user_id
      if not in_group('admin') and request.identity['user'].user_id != int(id):
         flash(u'Accès interdit !', 'error')
         redirect('/')

      u = DBSession.query(User).get(id)
      if not u:
         flash(u'Une erreur est survenue !', 'warning')
         log.info('user not found %d !' % id)
         redirect('/users/')

      try:
         ln = u.display_name.split(' ')[0]
         fn = u.display_name.split(' ')[1:]
         if type(fn)==type([]):
            fn = ' '.join(fn)
      except:
         ln = u.display_name
         fn = ''
      if u.phone: phone = u.phone[0].phone_id
      else: phone=None

      if in_group('admin'):
         groups = [g.group_id for g in u.groups]
      else:
         groups = ', '.join([g.group_name for g in u.groups])

      v = {'user_id': u.user_id, 
            'user_name': u.user_name,
            'firstname': fn,
            'lastname': ln,
            'email_address': u.email_address,
            'pwd1': u.password,
            'pwd2': u.password,
            'phone_id': phone,
            'groups': groups,
            '_method': 'PUT' }
      if in_group('admin'): tmpl_context.form = admin_edit_user_form
      else: tmpl_context.form = edit_user_form
      return dict(title = u'Modification utilisateur ' + u.user_name, debug='', values=v)

   class user_form_valid(object):
      def validate(self, params, state):
         log.debug(params)
         f = admin_edit_user_form if in_group('admin') else edit_user_form
         return f.validate(params, state)

   @validate(user_form_valid(), error_handler=edit)
   @expose()
   def put(self, **kw):
      ''' Update user in DB
      '''
      if not in_group('admin') and request.identity['user'].user_id != kw['user_id']:
         flash(u'Accès interdit !', 'error')
         redirect('/')
      uid = int(kw['user_id'])
      log.info('update %d' % uid)
      u = DBSession.query(User).get(uid)
      u.firstname = kw['firstname']
      u.lastname = kw['lastname']
      u.email_address = kw['email_address']
      u.password = kw['pwd1'] 
      u.display_name = u.lastname + ' ' + u.firstname

      # Update voicemail
      cidname = unicodedata.normalize('NFKD', u.display_name). \
            encode('ascii','ignore')
      if u.email_address:
         for p in u.phone:
            vm = u'>%s,%s,%s' \
               % (u.password, cidname, u.email_address)
            actions = [
               ('Append', 'astportal', p.exten, vm),
            ]
            Globals.manager.update_config(
               dir_ast  + 'voicemail.conf', 
               None, [('Delete', 'astportal', p.exten)])
            rmtree('%s/%s' % (dir_vm, p.exten), True)
            log.info('Delete voicemail directory %s/%s' % (dir_vm, p.exten))
            res = Globals.manager.update_config(
               dir_ast  + 'voicemail.conf', 
               'app_voicemail_plain', actions)
            log.debug('Update voicemail.conf returns %s' % res)

            Globals.manager.send_action({'Action': 'Command',
               'command': 'voicemail reload'})

      if kw.has_key('user_name'): # Modification par administrateur
         u.user_name = kw['user_name']
         u.groups = DBSession.query(Group). \
               filter(Group.group_id.in_(kw['groups'])).all()
      flash(u'Utilisateur modifié')
      redirect('/users/%d/edit' % uid)


   @expose()
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut supprimer un utilisateur'))
   def delete(self, id, **kw):
      ''' Delete user from DB
      '''

      u = DBSession.query(User).get(kw['_id'])

      # Delete voicemail
      cidname = unicodedata.normalize('NFKD', u.display_name). \
            encode('ascii','ignore')
      if u.email_address:
         for p in u.phone:
            res = Globals.manager.update_config(
               dir_ast  + 'voicemail.conf', 
               None, [('Delete', 'astportal', p.exten)])
            log.debug('Delete voicemail.conf returns %s' % res)
            rmtree('%s/%s' % (dir_vm, p.exten), True)
            log.info('Delete voicemail directory %s/%s' % (dir_vm, p.exten))
            Globals.manager.send_action({'Action': 'Command',
               'command': 'voicemail reload'})

      # Then delete user
      log.info('delete ' + kw['_id'])
      DBSession.delete(u)
      flash(u'Utilisateur supprimé', 'notice')
      redirect('/users/')


   @expose('json')
   def set_prefs(self, menu=None):

      log.debug('menu -> %s' % menu)
      if menu is not None:
         grid_rows = session.get('grid_rows', None)
         session['menu'] = menu
         session.save()

      return dict(status='ok')

