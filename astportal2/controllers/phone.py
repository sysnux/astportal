# -*- coding: utf-8 -*-
# Phone CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, require
from tg.controllers import RestController

from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, CheckBoxList
from tw.jquery import AjaxForm
from tw.forms.validators import NotEmpty, Int, Invalid

from genshi import Markup

from astportal2.model import DBSession, Phone, Department, User
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.grandstream import Grandstream

from os import system, popen #, rename
import logging
log = logging.getLogger(__name__)


vendors = {
   '00:0b:82': 'Grandstream',
   '00:04:f2': 'Polycom',
   '00:90:7a': 'Polycom',
}

contexts = ((-1, ' - - - '), (0, 'default'), (1, 'autorise-global'))
callgroups = ((1, 'Groupe 1'), (2, 'Groupe 2'), (3, 'Groupe 3'), (4, 'Groupe 4'),
   (5, 'Groupe 5'), (6, 'Groupe 6'), (7, 'Groupe 7'), (8, 'Groupe 8'), (9, 'Groupe 9'))
pickupgroups = ((1, 'Groupe 1'), (2, 'Groupe 2'), (3, 'Groupe 3'), (4, 'Groupe 4'),
   (5, 'Groupe 5'), (6, 'Groupe 6'), (7, 'Groupe 7'), (8, 'Groupe 8'), (9, 'Groupe 9'))

def departments():
   a = [('-9999',' - - - ')]
   for d in DBSession.query(Department).order_by(Department.comment):
       a.append((d.dptm_id,d.comment))
   return a

def users():
   a = [('-9999',' - - - ')]
   for u in DBSession.query(User).order_by(User.display_name):
      a.append((u.user_id, u.display_name))
   return a


# New phone page contains 2 forms, displayed in two tabs:
# the first form (ip_form) "discovers" the phone
ip_form = AjaxForm(
   id = 'ip_form',
   fields = [ 
      TextField('ip', validator=NotEmpty, label_text=u'Adresse IP', 
         help_text=u'Entrez l\'adresse du téléphone'),
      TextField('pwd', label_text=u'Mot de passe', 
         help_text=u'Entrez le mot de passe du téléphone')
      ],
   hover_help = True,
   beforeSubmit = js_callback('wait'),
   success = js_callback('phone_ok'),
   action = 'check_phone',
   dataType = 'JSON',
   target = None,
   clearForm = False,
   resetForm = False,
   timeout = '60000',
   submit_text = u'Rechercher...'
)

# The second form for related data
class New_phone_form(TableForm):
   ''' New phone form
   '''

   fields = [
         TextField('number', validator=Int,
            label_text=u'Numéro', help_text=u'Entrez le numéro du téléphone'),
         SingleSelectField('context', options = contexts,
            label_text=u'Contexte', help_text=u'Droits d\'appels'),
         CheckBoxList('callgroups', validator=Int,
            options=callgroups,
            label_text=u'Groupes d\'appels', 
            help_text=u'Cochez les groupes d\'appel de l\'utilisateur'),
         CheckBoxList('pickupgroups', validator=Int,
            options=pickupgroups,
            label_text=u'Groupes d\'interception', 
            help_text=u'Cochez les groupes d\'interception de l\'utilisateur'),
         SingleSelectField('dptm_id', options = departments,
            label_text=u'Service', help_text=u'Service facturé'),
         SingleSelectField('user_id', options=users,
            label_text=u'Utilisateur', help_text=u'Utilisateur du téléphone'),
         HiddenField('mac', validator=Int),
         HiddenField('ip', validator=Int),
         HiddenField('password', validator=Int),
         ]
   submit_text = u'Valider...'
   action = 'create'
   name = 'form_info'
   hover_help = True
new_phone_form = New_phone_form('new_form_phone')


class Edit_phone_form(TableForm):
   ''' Edit phone form
   '''
   fields = [
         TextField('number', #validator=Int,
            label_text=u'Numéro', help_text=u'Entrez le numéro du téléphone'),
         SingleSelectField('context', validator=Int, 
            options = contexts,
            label_text=u'Contexte', help_text=u'Droits d\'appels'),
         CheckBoxList('callgroups', validator=Int,
            options=callgroups,
            label_text=u'Groupes d\'appels', 
            help_text=u'Cochez les groupes d\'appel de l\'utilisateur'),
         CheckBoxList('pickupgroups', validator=Int,
            options=pickupgroups,
            label_text=u'Groupes d\'interception', 
            help_text=u'Cochez les groupes d\'interception de l\'utilisateur'),
         SingleSelectField('dptm_id',
            options= departments,
            label_text=u'Service', help_text=u'Service facturé',
            validator=Int
            ),
         SingleSelectField('user_id',
            options= users,
            label_text=u'Utilisateur', help_text=u'Utilisateur du téléphone',
            validator=Int
            ),
         HiddenField('_method', validator=None), # Needed by RestController
         HiddenField('phone_id', validator=Int),
         ]
   submit_text = u'Valider...'
   action = '/phones/'
   hover_help = True
edit_phone_form = Edit_phone_form('edit_form_phone')


def row(p):
   '''Displays a formatted row of the phones list
   Parameter: Phone object
   '''
   if p.department:
      dptm = Markup(u'<a href="/departments/%d/edit/">%s</a>' % \
            (p.department.dptm_id, p.department.comment))
   else: 
      dptm = None
   if p.user:
      user = Markup(u'<a href="/users/%d/edit/">%s</a>' % \
            (p.user.user_id, p.user.display_name))
   else:
      user = None
   if p.ip: 
      ip = Markup('<a href="http://%s/index.htm" target="_blank" title="Interface t&eacute;l&eacute;phone">%s</a>' % (p.ip,p.ip)) 
   else: 
      ip = None

   html =  u'<a href="'+ str(p.phone_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   html += u'&nbsp;&nbsp;&nbsp;'
   html += u'<a href="#" onclick="del(\''+ str(p.phone_id) + \
         u'\',\'Suppression du téléphone ' + str(p.number) + u'\')" title="Supprimer">'
   html += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(html), ip, p.mac, p.number, user , dptm]


class Phone_ctrl(RestController):
   
   new_phone = None
   allow_only = in_group('admin', 
         msg=u'Vous devez appartenir au groupe "admin" pour gérer les téléphones')

   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all phones
      '''
      grid = MyJqGrid( id='grid', url='fetch', caption=u'Téléphones',
            sortname='number',
            colNames = [u'Action', u'Adresse IP', u'Identifiant',
               u'Numéro', u'Utilisateur', u'Service'],
            colModel = [ 
               { 'display': u'Action', 'width': 80, 'align': 'center', 'search': False },
               { 'name': 'ip', 'width': 80 },
               { 'name': 'mac', 'width': 100 },
               { 'name': 'number', 'width': 80 },
               { 'name': 'user_id', 'width': 120, 'search': False },
               { 'name': 'department_id', 'width': 120, 'search': False } ],
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': True, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des téléphones', debug='')


   @expose('json')
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut afficher la liste des utilisateurs'))
   def fetch(self, page=1, rows=10, sidx='user_name', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * rows
      except:
         offset = 0
         page = 1
         rows = 25

      phones = DBSession.query(Phone)
      if  searchOper and searchField and searchString:
         log.debug('fetch query <%s> <%s> <%s>' % \
            (searchField, searchOper, searchString))
         try:
            field = eval('Phone.' + searchField)
         except:
            field = None
            log.error('eval: Phone.' + searchField)
         if field and searchOper=='eq': 
            phones = phones.filter(field==searchString)
         elif field and searchOper=='ne':
            phones = phones.filter(field!=searchString)
         elif field and searchOper=='le':
            phones = phones.filter(field<=searchString)
         elif field and searchOper=='lt':
            phones = phones.filter(field<searchString)
         elif field and searchOper=='ge':
            phones = phones.filter(field>=searchString)
         elif field and searchOper=='gt':
            phones = phones.filter(field>searchString)
         elif field and searchOper=='bw':
            phones = phones.filter(field.ilike(searchString + '%'))
         elif field and searchOper=='bn':
            phones = phones.filter(~field.ilike(searchString + '%'))
         elif field and searchOper=='ew':
            phones = phones.filter(field.ilike('%' + searchString))
         elif field and searchOper=='en':
            phones = phones.filter(~field.ilike('%' + searchString))
         elif field and searchOper=='cn':
            phones = phones.filter(field.ilike('%' + searchString + '%'))
         elif field and searchOper=='nc':
            phones = phones.filter(~field.ilike('%' + searchString + '%'))
         elif field and searchOper=='in':
            phones = phones.filter(field.in_(str(searchString.split(' '))))
         elif field and searchOper=='ni':
            phones = phones.filter(~field.in_(str(searchString.split(' '))))

      total = phones.count()/rows + 1
      column = getattr(Phone, sidx)
      phones = phones.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      data = [ { 'id'  : p.phone_id, 'cell': row(p) } for p in phones ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new_phone")
   def new(self, **kw):
      ''' Display new phone form
      '''
      tmpl_context.ip_form = ip_form
      tmpl_context.form = new_phone_form
      from tw.uitheme import uilightness_css
      uilightness_css.inject()
      from tw.jquery.ui import ui_tabs_js
      ui_tabs_js.inject()
      return dict(title = u'Nouveau téléphone', debug='', values='')

   @expose('json')
   @validate(ip_form)
   def check_phone(self, ip, pwd=None):
      # Check phone is connected,  get hardware address
      ret = system('fping -q %s &> /dev/null' % ip)
      if ret:
         return dict(status=1, msg=u"Téléphone injoignable, vérifiez l'adresse")
      ret = popen('/sbin/arp %s' % ip).readlines()
      log.debug('arp -> ' + str(ret))
      if len(ret)!=2:
         return dict(status=2, msg=u"Téléphone injoignable, vérifiez l'adresse")
      import re
      match = re.compile('(\w\w:\w\w:\w\w):(\w\w:\w\w:\w\w)').search(ret[1].lower())
      if not match:
         return dict(status=3, msg=u"Téléphone injoignable, vérifiez l'adresse")
      (vendor,device) = match.groups()
      log.debug('vendor=%s, device=%s' % (vendor,device))
      if not vendors.has_key(vendor):
         return dict(status=4, msg=u"Type de téléphone inconnu")

      mac = '%s:%s' % (vendor,device)
      p = DBSession.query(Phone).filter(Phone.mac==mac).all()
      if len(p):
         return dict(status=5, 
               msg = u'Téléphone existant, voulez-vous le \
                     <a href="/phones/%s/edit">modifier</a>.' % p[0].phone_id)

      global new_phone
      if vendors[vendor]=='Grandstream':
         new_phone = Grandstream(ip, mac)
         msg = u"Trouvé téléphone Grandstream : "
         if not new_phone.login(pwd):
            return dict(status=6, msg=msg+u'erreur login')
         infos = new_phone.infos()
         if not infos:
            return dict(status=6, msg=msg+u'erreur login')
         return dict(status = 0, ip = ip, mac = mac, conf = 'grandstream_configure',
               msg = msg + infos['model'] + ', ' + infos['version'])
      elif vendors[vendor]=='Polycom':
         return dict(status=0, ip=ip, mac=mac, conf='polycom_configure',
               msg=u"Trouvé téléphone Polycom")


   @expose('json')
   def grandstream_configure(self, ip, mac):
      gs = Grandstream(ip, mac)
      if not gs.login():
         return dict(status=1, msg=u'Erreur login')
      infos = gs.infos()
      server = 'tiare.sysnux.pf'
      gs.pre_configure(server, server, server,
            server + ':8080/phonebook', server)
      return dict(status=0, model=infos['model'], version=infos['version'])

 
#   class user_form_valid(object):
#      def validate(self, params, state):
#         f = admin_edit_user_form if in_group('admin') else edit_user_form
#         return f.validate(params, state)
#
#   @validate(user_form_valid(), error_handler=edit)

#   @validate(new_phone_form, error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new phone to DB
      '''

      # Check phone number
      if kw['number']: 
         log.debug('Check number ' +  kw['number'])
         p = DBSession.query(Phone).filter(Phone.number==kw['number']).all()
         if len(p):
            flash(u'Le numéro "%s" est déjà utilisé' % (kw['number']),'error')
            redirect('new')

      # Configure phone
      server = 'tiare.sysnux.pf'
      pwd = '0000'
      sip_server = None
      sip_user = None
      sip_display_name = None
      mwi_subscribe = 0
      if kw['number']:
         sip_server = 'asterisk.sysnux.pf'
         sip_user = kw['number']
         sip_display_name = ''
         mwi_subscribe = 0
         if kw['user_id']!='-9999':
            u = DBSession.query(User).get(kw['user_id'])
            sip_display_name = u.display_name
            if u.email_address:
               mwi_subscribe = 1
 
      global new_phone
      new_phone.configure( pwd, server + '/phones/firmware', 
            server + '/phones/config', server,
            server + ':8080/phonebook', server,
            sip_server, sip_user, sip_display_name, mwi_subscribe)

      # Save phone info to database
      p = Phone()
      p.ip = kw['ip']
      p.mac = kw['mac']
      p.password = pwd
      if kw['number']: p.number = kw['number']
      if kw['number']: p.number = kw['number']
      if kw['dptm_id']!='-9999': p.department_id = kw['dptm_id']
      if kw['user_id']!='-9999': p.user_id = kw['user_id']
      DBSession.add(p)
      flash(u'Nouveau téléphone "%s" créé' % (kw['number']))
      redirect('/phones/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, phone_id=None, dptm_id=None, user_id=None, 
         number=None, **kw):
      ''' Display edit phone form
      '''
      ident = ''
      log.debug(kw)
      if phone_id:
         v = {'phone_id': phone_id, 
            'number': None,
            'dptm_id': None if dptm_id=='-9999' else int(dptm_id),
            'user_id': None if user_id=='-9999' else int(user_id),
            '_method': 'PUT'}
         if number: ident = number
         elif mac: ident = mac

      else:
         if not id: id=kw['phone_id']
         p = DBSession.query(Phone).get(id)
         v = {'phone_id': p.phone_id, 
            'number': p.number, 
            'dptm_id': p.department_id, 
            'user_id': p.user_id, 
            '_method': 'PUT'}
         if p.number: ident = p.number
         elif p.mac: ident = p.mac

      tmpl_context.form = edit_phone_form
      return dict(title = u'Modification téléphone ' + ident, debug='', values=v)


   class edit_form_valid(object):
      def validate(self, params, state):
         log.debug(params)
         f = edit_phone_form
         # Check phone number
         if params['number']: 
            p = DBSession.query(Phone).filter(Phone.number==params['number'])
            p = p.filter(Phone.phone_id!=params['phone_id']).all()
            if len(p):
               log.warning('Number exists %s, cannot update phone %s' % (params['number'],params['phone_id']))
               flash(u'Le numéro "%s" est déjà utilisé' % (params['number']),'error')
               raise Invalid('XXXX', 'ZZZ', state)
         return f.validate(params, state)

   @validate(edit_form_valid(), error_handler=edit)
   @expose()
   def put(self, phone_id, dptm_id, user_id, number, context,
         callgroups, pickupgroups):
      ''' Update phone in DB
      '''
      log.info('update %d' % phone_id)
      log.debug(callgroups)
      log.debug(pickupgroups)
      p = DBSession.query(Phone).get(phone_id)

      gs = Grandstream(p.ip, p.mac)
      gs.login(p.password)

      server = 'tiare.sysnux.pf'
      sip_server = None
      sip_user = None
      sip_display_name = None
      mwi_subscribe = 0
      need_sip_update = False
      need_voicemail_update = False
      if number:
         need_sip_update = True

         sip_server = 'asterisk.sysnux.pf'
         sip_user = number
         sip_display_name = ''
         mwi_subscribe = 0

         if user_id!=-9999:
            u = DBSession.query(User).get(user_id)
            sip_display_name = u.display_name
            if u.email_address:
               need_voicemail_update = True
               mwi_subscribe = 1
 
      gs.configure( p.password, server + '/phones/firmware', 
            server + '/phones/config', server,
            server + ':8080/phonebook', server,
            sip_server, sip_user, sip_display_name, mwi_subscribe)

      # Save phone info to database
      if dptm_id:
         if dptm_id==-9999:
            p.department_id = None
         else:
            p.department_id = dptm_id
      if user_id:
         if user_id==-9999:
            p.user_id = None
         else:
            p.user_id = user_id
      if number=='':
         p.number = None
      else:
         p.number = number
      p.context = contexts[context][1]
      p.callgroups = ','.join([str(x) for x in callgroups])
      p.pickupgroups = ','.join([str(x) for x in pickupgroups])

      if need_sip_update:
         # Update Asterisk's sip.conf
         sip = open('/tmp/sip-osb.conf','w')
         for friend in DBSession.query(Phone).filter(Phone.number!=None):
            context = friend.context if friend.context else 'default'
            callgroups = friend.callgroups if friend.callgroups else ''
            pickupgroups = friend.pickupgroups if friend.pickupgroups else ''
            sip.write('''[%s]!osb
secret=%s
context=%s
callgroups=%s
pickupgroups=%s

''' % (friend.number, friend.password, context, callgroups, pickupgroups))
         sip.close()

      if need_voicemail_update:
         # Update Asterisk's voicemail.conf
         pass

      flash(u'Téléphone modifié')
      redirect('/phones/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete phone from DB
      '''
      log.info('delete ' + kw['_id'])
      DBSession.delete(DBSession.query(Phone).get(kw['_id']))
      flash(u'Téléphone supprimé', 'notice')
      redirect('/phones/')


