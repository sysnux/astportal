# -*- coding: utf-8 -*-
# User CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, require
from tg.controllers import RestController

from repoze.what.predicates import in_group, not_anonymous

from tw.jquery import FlexiGrid
from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, CheckBoxList, PasswordField, HiddenField
from tw.forms.validators import NotEmpty, Email, Int

from genshi import Markup

from astportal2.model import DBSession, User, Phone, Group, Department

import logging
log = logging.getLogger(__name__)


class New_user_form(TableForm):
   ''' New user form
   '''
   fields = [
         TextField('user_name', validator=NotEmpty,
            label_text=u'Compte',
            help_text=u'Entrez le nom d\'utilisateur'),
         TextField('firstname',
            label_text=u'Prénom',
            help_text=u'Entrez le prénom de l\'utilisateur'),
         TextField('lastname', validator=NotEmpty,
            label_text=u'Nom de famille',
            help_text=u'Entrez le nom de famille de l\'utilisateur'),
         TextField('email_address', validator=Email,
            label_text=u'Adresse email',
            help_text=u'Entrez l\'adresse email de l\'utisateur'),
         PasswordField('pwd1', validator=NotEmpty,
            label_text=u'Mot de passe',
            help_text=u'Entrez le mot de passe'),
         PasswordField('pwd2', validator=NotEmpty,
            label_text=u'Confirmation mot de passe',
            help_text=u'Entrez à nouveau le mot de passe'),
         SingleSelectField('phone_id',
            options=DBSession.query(Phone.phone_id, 
               Phone.number).filter(Phone.user_id==None).order_by(Phone.number),
            label_text=u'Téléphone', 
            help_text=u'Choisissez le téléphone de l\'utilisateur'),
         CheckBoxList('groups', validator=Int,
            options=DBSession.query(Group.group_id, 
               Group.group_name).order_by(Group.group_name),
            label_text=u'Groupes', 
            help_text=u'Cochez les groupes auxquels appartient l\'utilisateur'),
         ]
   submit_text = u'Valider...'
   action = 'create'
   hover_help = True
new_user_form = New_user_form('new_form_user')


class Edit_user_form(TableForm):
   ''' Edit user form
   '''
   fields = [
         TextField('firstname', validator=NotEmpty,
            label_text=u'Prénom',
            help_text=u'Entrez le prénom de l\'utilisateur'),
         TextField('lastname', validator=NotEmpty,
            label_text=u'Nom de famille',
            help_text=u'Entrez le nom de famille de l\'utilisateur'),
         TextField('email_address', validator=Email,
            label_text=u'Adresse email',
            help_text=u'Entrez l\'adresse email de l\'utisateur'),
         TextField('pwd1',
            label_text=u'Mot de passe',
            help_text=u'Entrez le mot de passe'),
         TextField('pwd2',
            label_text=u'Confirmation mot de passe',
            help_text=u'Entrez à nouveau le mot de passe'),
         SingleSelectField('phone_id',
            options=DBSession.query(Phone.phone_id, 
               Phone.number).order_by(Phone.number),
            label_text=u'Téléphone',
            help_text=u'Choisissez le téléphone de l\'utilisateur'),
         CheckBoxList('groups', validator=Int,
            options=DBSession.query(Group.group_id, 
               Group.group_name).order_by(Group.group_name),
            label_text=u'Groupes', 
            help_text=u'Cochez les groupes auxquels appartient l\'utilisateur'),
         HiddenField('_method', validator=None), # Needed by RestController
         HiddenField('user_id', validator=Int),
         ]
   submit_text = u'Valider...'
   action = '/users/'
   hover_help = True
edit_user_form = Edit_user_form('edit_form_user')


def row(u):
   '''Displays a formatted row of the users list
   Parameter: Phone object
   '''
   if u.phone:
      phone = u.phone[0].number
   else:
      phone = ''

   if u.groups:
      groups = ', '.join([g.group_name for g in u.groups])
   else:
      groups = ''
   action =  u'<a href="'+ str(u.user_id) + u'/edit" title="Modifier">'
   action += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   action += u'&nbsp;&nbsp;&nbsp;'
   action += u'<a href="#" onclick="del(\''+ str(u.user_id) + \
         u'\',\'Suppression de ' + u.display_name + u'\')" title="Supprimer">'
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   if u.email_address:
      email = u'<a href="mailto:' + u.email_address + '">' + u.email_address + '</a>'
   else:
      email = ''

   return [Markup(action), u.user_name, u.display_name, Markup(email), phone, groups]


class User_ctrl(RestController):
   
   allow_only = not_anonymous(msg=u'Veuiller vous connecter pour continuer')

   @expose(template="astportal2.templates.flexigrid")
   def get_all(self):
      ''' List all users
      '''
      if not in_group('admin'):
         redirect( str(request.identity['user'].user_id) + '/edit')

      grid = FlexiGrid( id='flexi', fetchURL='fetch', title=None,
            sortname='user_name', sortorder='asc',
            colModel = [
               { 'display': u'Action', 'width': 80, 'align': 'center' },
               { 'display': u'Compte', 'name': 'user_name', 'width': 80 },
               { 'display': u'Nom', 'name': 'display_name', 'width': 120 },
               { 'display': u'email', 'name': 'email_address', 'width': 180 },
               { 'display': u'Téléphone', 'width': 60 },
               { 'display': u'Groupes', 'width': 160 } ],
            searchitems = [{'display': u'Nom', 'name': 'user_name'} ],
            buttons = [  {'name': u'Ajouter', 'bclass': 'add', 'onpress': js_callback('add')},
               {'separator': True} ],
            usepager=True,
            useRp=True,
            rp=10,
            resizable=False,
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des utilisateurs', debug='')


   @expose('json')
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut afficher la liste des utilisateurs'))
   def fetch(self, page=1, rp=25, sortname='user_name', sortorder='asc',
         qtype=None, query=None):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      try:
         page = int(page)
         offset = (page-1) * int(rp)
      except:
         offset = 0
         page = 1
         rp = 25

      if (query):
         d = {str(qtype): query}
         users = DBSession.query(User).filter_by(**d)
      else:
         users = DBSession.query(User)

      total = users.count()
      column = getattr(User, sortname)
      users = users.order_by(getattr(column,sortorder)()).offset(offset).limit(rp)
      rows = [ { 'id'  : u.user_id, 'cell': row(u) } for u in users ]

      return dict(page=page, total=total, rows=rows)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new user form
      '''
      tmpl_context.form = new_user_form
      return dict(title = u'Nouvel utilisateur', debug='', values='')
      
   @validate(new_user_form, error_handler=new)
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut créer un utilisateur'))
   @expose()
   def create(self, **kw):
      ''' Add new user to DB
      '''
      log.info('new ' + kw['user_name'])
      u = User()
      u.user_name = kw['user_name']
      u.display_name = kw['lastname'] + ' ' + kw['firstname']
      u.email_address = kw['email_address']
      u.password = kw['pwd1']
      u.phone = [DBSession.query(Phone).get(kw['phone_id'])]
      u.groups = DBSession.query(Group).filter(Group.group_id.in_(kw['groups'])).all()
      flash(u'Nouvel utilisateur "%s" créé' % (kw['user_name']))
      redirect('/users/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit user form
      '''
      if not id: id=kw['user_id']
      if not in_group('admin') and request.identity['user'].user_id != int(id):
         flash(u'Accès interdit !', 'error')
         redirect('/')
      u = DBSession.query(User).get(id)
      ln = u.display_name.split(' ')[0]
      fn = u.display_name.split(' ')[1:]
      if type(fn)==type([]):
         fn = ' '.join(fn)
      if u.phone: phone = u.phone[0].phone_id
      else: phone=None

      v = {'user_id': u.user_id, 
            'firstname': fn,
            'lastname': ln,
            'email_address': u.email_address,
            'phone_id': phone,
            'groups': [g.group_id for g in u.groups],
            '_method': 'PUT'}
      tmpl_context.form = edit_user_form
      return dict(title = u'Modification utilisateur ' + u.user_name, debug='', values=v)


   @validate(edit_user_form, error_handler=edit)
   @expose()
   def put(self, user_id, lastname, firstname, pwd1, pwd2, 
         email_address=None, groups=None, phone_id=None ):
      ''' Update user in DB
      '''
      if not in_group('admin') and request.identity['user'].user_id != kw['user_id']:
         flash(u'Accès interdit !', 'error')
         redirect('/')
      log.info('update %d' % user_id)
      u = DBSession.query(User).get(user_id)
      u.display_name = lastname + ' ' + firstname
      u.email_address = email_address
      if pwd1: u.password = pwd1
      p = DBSession.query(Phone).get(phone_id)
      u.phone = [p]
      u.groups = DBSession.query(Group).filter(Group.group_id.in_(groups)).all()
      flash(u'Utilisateur modifié')
      redirect('/users/')


   @expose()
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut supprimer un utilisateur'))
   def delete(self, id, **kw):
      ''' Delete user from DB
      '''
      log.info('delete ' + kw['_id'])
      DBSession.delete(DBSession.query(User).get(kw['_id']))
      flash(u'Utilisateur supprimé', 'notice')
      redirect('/users/')


