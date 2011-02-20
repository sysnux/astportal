# -*- coding: utf-8 -*-
# Phone CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, require
from tg.controllers import RestController
from tgext.menu import sidebar

from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, CheckBoxList, CheckBoxTable
from tw.jquery import AjaxForm
from tw.forms.validators import NotEmpty, Int, Invalid

from genshi import Markup

from astportal2.model import DBSession, Phone, Department, User
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.grandstream import Grandstream
from astportal2.lib.app_globals import Globals

from string import letters, digits
from random import choice
from os import system, popen #, rename
import logging
log = logging.getLogger(__name__)

from tg import config

server_sip = config.get('server.sip')
server_firmware = config.get('server.firmware')
server_config = config.get('server.config')
server_syslog = config.get('server.syslog')
server_ntp = config.get('server.ntp')
command_fping = config.get('command.fping')
command_arp = config.get('command.arp')
directory_tftp = config.get('directory.tftp')
directory_asterisk = config.get('directory.asterisk')

vendors = {
   '00:0b:82': 'Grandstream',
   '00:04:f2': 'Polycom',
   '00:90:7a': 'Polycom',
}

contexts = ((1, u'Urgences'), (2, u'Interne'), (3, u'Services'), 
   (4, u'Local'), (5, u'Iles'), (6, u'GSM'), 
   (7, u'International IP'), (8, u'International RTC'))

callgroups = ((1, u'Groupe 1'), (2, u'Groupe 2'), (3, u'Groupe 3'), 
   (4, u'Groupe 4'), (5, u'Groupe 5'), (6, u'Groupe 6'), 
   (7, u'Groupe 7'), (8, u'Groupe 8'), (9, 'Groupe 9'))

pickupgroups = ((1, u'Groupe 1'), (2, u'Groupe 2'), (3, u'Groupe 3'), 
   (4, u'Groupe 4'), (5, u'Groupe 5'), (6, u'Groupe 6'), 
   (7, u'Groupe 7'), (8, u'Groupe 8'), (9, 'Groupe 9'))


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
      TextField('ip', label_text=u'Adresse IP'),
      TextField('mac', label_text=u'Adresse matérielle (MAC)'),
      TextField('pwd', label_text=u'Mot de passe', default='admin'),
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
class New_phone_form(AjaxForm):
   ''' New phone form
   '''
   fields = [
      TextField('number', validator=Int,
         not_empty = False,
         label_text=u'Numéro', help_text=u'Entrez le numéro du téléphone'),
      CheckBoxTable('context',  validator=Int,
         options = contexts,
         not_empty = False,
         default = (1,2,3),
         label_text=u'Contexte', help_text=u'Droits d\'appels'),
      CheckBoxTable('callgroups', validator=Int,
         options = callgroups,
         label_text=u'Groupes d\'appels', 
         not_empty = False,
         help_text=u'Cochez les groupes d\'appel de l\'utilisateur'),
      CheckBoxTable('pickupgroups', validator=Int,
         options=pickupgroups,
         label_text=u'Groupes d\'interception', 
         not_empty = False,
         help_text=u'Cochez les groupes d\'interception de l\'utilisateur'),
      SingleSelectField('dptm_id', options = departments,
         not_empty = False,
         label_text=u'Service', help_text=u'Service facturé'),
      SingleSelectField('user_id', options=users,
         not_empty = False,
         label_text=u'Utilisateur', help_text=u'Utilisateur du téléphone'),
      HiddenField('mac', 
         not_empty = False,
         validator=Int),
      HiddenField('ip', 
         not_empty = False,
         validator=Int),
      HiddenField('password', 
         not_empty = False,
         validator=Int),
      ]
   submit_text = u'Valider...'
   name = 'form_info'
   hover_help = True
   beforeSubmit = js_callback('wait2')
   success = js_callback('created')
   action = 'create'
   dataType = 'JSON'
   target = None
   clearForm = False
   resetForm = False
   timeout = '60000'
new_phone_form = New_phone_form('new_form_phone')


class Edit_phone_form(TableForm):
   ''' Edit phone form
   '''
   fields = [
      TextField('number', #validator=Int,
         label_text=u'Numéro', help_text=u'Entrez le numéro du téléphone'),
      CheckBoxList('context', validator=Int, 
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
   dptm = Markup(u'<a href="/departments/%d/edit/">%s</a>' % \
      (p.department.dptm_id, p.department.comment)) if p.department else None
   user = Markup(u'<a href="/users/%d/edit/">%s</a>' % \
      (p.user.user_id, p.user.display_name)) if p.user else None

   # Find peer
   if p.sip_id and 'SIP/'+p.sip_id in Globals.asterisk.peers:
      peer = p.sip_id
   elif p.number and 'SIP/'+p.number in Globals.asterisk.peers:
      peer = p.number
   else:
      log.warning('%s not registered ?' % p.sip_id)
      peer = None

   if peer:
      # Peer exists, try to find User agent
      if 'UserAgent' not in Globals.asterisk.peers['SIP/'+peer]:
         log.debug('SIPshowPeer(%s)' % peer)
         res = Globals.manager.sipshowpeer(peer)
         Globals.asterisk.peers['SIP/'+peer]['UserAgent'] = res.get_header('SIP-Useragent')
      if Globals.asterisk.peers['SIP/'+peer]['Address']:
         p_ip = (Globals.asterisk.peers['SIP/'+peer]['Address']).split(':')[0]
         ua = Globals.asterisk.peers['SIP/'+peer]['UserAgent']
         if ua and ua.startswith('Grandstream GXP'):
            ip = Markup('''<a href="#" title="Connexion interface t&eacute;l&eacute;phone" onclick="phone_open('%s','%s', '%s');">%s</a>''' % (p_ip, p.password, 'GXP', p_ip))

         else:
            ip = Markup('''<a href="http://%s/" title="Connexion interface t&eacute;l&eacute;phone" target='_blank'>%s</a>''' % (p_ip, p_ip))
      else:
         ip = ua = None

   else: 
      ip = ua = None

   action =  u'<a href="'+ str(p.phone_id) + u'/edit" title="Modifier">'
   action += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   action += u'&nbsp;&nbsp;&nbsp;'
   action += u'<a href="#" onclick="del(\''+ str(p.phone_id) + \
         u'\',\'Suppression du téléphone ' + str(p.number) + u'\')" title="Supprimer">'
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(action), ip, ua, p.password, p.number, user , dptm]


class Phone_ctrl(RestController):
 
   new_phone = ''
   allow_only = in_group('admin', 
      msg=u'Vous devez appartenir au groupe "admin" pour gérer les téléphones')

   @sidebar(u'-- Administration || Téléphones', sortorder = 10,
      icon = '/images/internet-telephony.png')
   @expose('genshi:astportal2.templates.grid_phone')
   def get_all(self):
      ''' List all phones
      '''
      # Refresh Asterisk peers
      Globals.manager.sippeers()
      #Globals.manager.send_action('IAXpeers')

      grid = MyJqGrid( id='grid', url='fetch', caption=u'Téléphones',
         sortname='number',
         colNames = [u'Action', u'Adresse IP', u'Modèle', u'Mot de passe',
            u'Numéro', u'Utilisateur', u'Service'],
         colModel = [ 
            { 'display': u'Action', 'width': 80, 'align': 'center', 'search': False },
            { 'name': 'ip', 'width': 80 },
            { 'name': 'ua', 'width': 100 },
            { 'name': 'password', 'width': 80 },
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
   def check_phone(self, ip, pwd=None, mac=None):
      # Check phone is connected,  get hardware address
      log.debug('%s %s &> /dev/null' % (command_fping, ip))
      ret = system('%s %s &> /dev/null' % (command_fping, ip))
      if ret:
         return dict(status=1, msg=u"Téléphone injoignable, vérifiez l'adresse")
      if not mac:
         ret = popen('%s %s' % (command_arp, ip)).readlines()
         log.debug('arp -> ' + str(ret))
         if len(ret)!=2:
            return dict(status=2, msg=u"Téléphone injoignable, vérifiez l'adresse")
         mac = ret[1]
      import re
      match = re.compile('(\w\w:\w\w:\w\w):(\w\w:\w\w:\w\w)').search(mac.lower())
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
      gs.pre_configure(server_sip, server_firmware, server_config,
            server_config + ':8080/phonebook/gs_phonebook_xml', server_ntp)
      return dict(status=0, model=infos['model'], version=infos['version'])

 
#   class user_form_valid(object):
#      def validate(self, params, state):
#         f = admin_edit_user_form if in_group('admin') else edit_user_form
#         return f.validate(params, state)
#
#   @validate(user_form_valid(), error_handler=edit)

#   @validate(new_phone_form, error_handler=new)
   @expose('json')
   def create(self, **kw):
      ''' Create phone:
      Create provisionning file.
      If a number is attached to the phone, create exten in Asterisk database.
      If a user is attached to the phone, add callerid to phone ; if the user has
      email, add voicemail info to sip.conf and add entry in voicemail.conf
      Create entry in Asterisk sip.conf.
      '''

      # Check phone number is not already used
      if kw['number']:
         log.debug('Check number ' +  kw['number'])
         p = DBSession.query(Phone).filter(Phone.number==kw['number']).all()
         if len(p):
            return dict(status='bad_number')

      # Generate SIP id and secret
      while True:
         sip_id = ''.join([choice(letters + digits) for i in xrange(8)])
         log.debug('Generate SIP id: ' + sip_id)
         try:
            DBSession.query(Phone).filter(Phone.sip_id==sip_id).one()
         except:
            pwd = ''.join([choice(letters + digits) for i in xrange(8)])
            break

      # Configure phone
      sip_display_name = None
      mwi_subscribe = 0
      need_voicemail_update = False
      sip_server = server_sip
      sip_display_name = ''
      mwi_subscribe = 0
      if kw['user_id']!='-9999':
         u = DBSession.query(User).get(kw['user_id'])
         sip_display_name = u.display_name
         if u.email_address:
            mwi_subscribe = 1
            need_voicemail_update = True
 
      # Save phone info to database
      log.debug('Save to database ' +  kw['mac'])
      p = Phone()
      p.sip_id = sip_id
      p.mac = kw['mac']
      p.password = pwd
      if kw['number']: p.number = kw['number']
      if kw['dptm_id']!='-9999': p.department_id = kw['dptm_id']
      if kw['user_id']!='-9999': p.user_id = kw['user_id']
      if 'callgroups' in kw:
         p.callgroups = ','.join([str(x) for x in kw['callgroups']])
      if 'pickupgroups' in kw:
         p.pickupgroups = ','.join([str(x) for x in kw['pickupgroups']])
      if 'contexts' in kw:
         p.context = ','.join([str(x) for x in kw['contexts']])
      DBSession.add(p)

      # Build Asterisk UpdateConfig action list...
      actions = [
            ('NewCat', sip_id),
            ('Append', sip_id, 'secret', pwd),
            ('Append', sip_id, 'type', 'friend'),
            ('Append', sip_id, 'host', 'dynamic'),
            ('Append', sip_id, 'context', sip_id),
            ('Append', sip_id, 'allow', 'g722'),
            ]
      if p.callgroups:
         actions.append(('Append', sip_id, 'callgroups', p.callgroups))
      if p.pickupgroups:
         actions.append(('Append', sip_id, 'pickupgroups', p.pickupgroups))
      if p.user_id:
         u = DBSession.query(User).get(p.user_id)
         cidname = u.display_name
      else:
         cidname = ''      
      cidnum = p.number if p.number else ''
      if cidname or cidnum:
         actions.append(('Append', sip_id, 'callerid', '%s <%s>' % (cidname,cidnum)))
      if mwi_subscribe and p.number:
         actions.append(('Append', sip_id, 'mailbox', '%s@astportal' % p.number))
      # ... then really update
      res = Globals.manager.update_config(directory_asterisk  + 'sip.conf', 
            'chan_sip', actions)
      log.debug('Update sip.conf returns %s' % res)

      if p.number:
         # Update Asterisk DataBase
         Globals.manager.send_action({'Action': 'DBput',
            'Family': 'exten', 'Key': p.number, 'Val': sip_id})

      if need_voicemail_update:
         vm = '>%s,%s,%s' \
               % (u.password, cidname, u.email_address)
         actions = [
            # XXX ('Delete', 'astportal', p.number),
            ('Append', 'astportal', p.number, vm),
            ]
         res = Globals.manager.update_config(
               directory_asterisk  + 'voicemail.conf', 
               'app_voicemail_plain', actions)
         log.debug('Update voicemail.conf returns %s' % res)

      if 'context' in kw:
         # Create contexts
         log.debug('Contexts %s' % kw['context'])
         actions = [
            ('NewCat', sip_id),
            ]
         for c in kw['context']:
            actions.append(('Append', sip_id, 'include', '>%s' % c))
         res = Globals.manager.update_config(
               directory_asterisk  + 'extensions.conf', 'dialplan', actions)
         log.debug('Update extensions.conf returns %s' % res)

      if kw['mac']:
         # Create provisionning file if MAC exists
         global new_phone
         log.debug('Configure ' +  kw['mac'])
         new_phone.configure( pwd, directory_tftp,
            server_firmware + '/phones/firmware', 
            server_config + '/phones/config', server_syslog,
            server_config + ':8080/phonebook/gs_phonebook_xml', '', '', '',
            sip_server, sip_id, sip_display_name, mwi_subscribe)

      flash(u'Nouveau téléphone "%s" créé' % (kw['number']))
      return {'status': 'created'}


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, phone_id=None, dptm_id=None, user_id=None, 
         number=None, **kw):
      ''' Display edit phone form
      '''
      ident = ''
      log.debug('Edit')
      p = DBSession.query(Phone).get(id)
      v = {'phone_id': p.phone_id,
         'number': p.number,
         'contexts': p.context.split(',') if  p.context else None,
         'callgroups': p.callgroups.split(',') if  p.callgroups else None,
         'pickupgroups': p.pickupgroups.split(',') if  p.pickupgroups else None,
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
         callgroups=None, pickupgroups=None):
      ''' Update phone in DB
      '''
      context += 1
      log.info('update %d' % phone_id)
      log.debug('Context %s (%d)' % (contexts[context][1],context))
      log.debug('Callgroups %s' % callgroups)
      log.debug('Pickupgroups %s' % pickupgroups)
      p = DBSession.query(Phone).get(phone_id)

      if p.ip and p.mac:
         gs = Grandstream(p.ip, p.mac)
         gs.login(p.password)
      else:
         gs = None

      server = '192.168.0.5'
      sip_server = None
      sip_user = None
      sip_display_name = None
      mwi_subscribe = False
      need_sip_update = False
      need_voicemail_update = False
      need_phone_update = False

      if number and number!=p.number:
         log.debug('%s!=%s' % (number,p.number))
         need_sip_update = need_phone_update = True

         sip_server = '192.168.0.5'
         sip_user = number
         sip_display_name = ''
         mwi_subscribe = False

         if user_id!=-9999:
            u = DBSession.query(User).get(user_id)
            sip_display_name = u.display_name
            if u.email_address:
               need_voicemail_update = True
               mwi_subscribe = False

      if need_phone_update and gs:
         gs.configure( p.password, server + '/phones/firmware', 
            server + '/phones/config', '192.168.0.5',
            server + ':8080/phonebook/gs_phonebook_xml', '', '192.168.0.5', '192.168.0.5',
            sip_server, sip_user, sip_display_name, mwi_subscribe)

      # Save phone info to database
      if p.department_id!=dptm_id:
         if dptm_id==-9999:
            p.department_id = None
         else:
            p.department_id = dptm_id

      if p.user_id!=user_id:
         need_sip_update = True
         if user_id==-9999:
            p.user_id = None
         else:
            p.user_id = user_id
            u = DBSession.query(User).get(user_id)
            if u.email_address:
               need_voicemail_update = True
               mwi_subscribe = 1

      if p.number!=number:
         need_sip_update = True
         if number=='':
            p.number = None
         else:
            p.number = number

      if p.context!=contexts[context][1]:
         log.debug('New context %s' % contexts[context][1])
         need_sip_update = True
         p.context = contexts[context][1]

      x = ','.join([str(x) for x in callgroups])
      if p.callgroups!=x:
         need_sip_update = True
         p.callgroups = x

      x = ','.join([str(x) for x in pickupgroups])
      if p.pickupgroups!=x:
         need_sip_update = True
         p.pickupgroups = x

      if need_sip_update:
         # XXX sip_update()
         pass

      if need_voicemail_update:
         # XXX voicemail_update()
         pass

      flash(u'Téléphone modifié')
      redirect('/phones/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete phone from DB
      '''
      log.info('delete ' + kw['_id'])
      p = DBSession.query(Phone).get(kw['_id'])
      number = p.number
      sip_id = p.sip_id
      DBSession.delete(p)
      flash(u'Téléphone supprimé', 'notice')

      if number:
         # Update Asterisk DataBase
         Globals.manager.send_action({'Action': 'DBdel',
            'Family': 'exten', 'Key': number})

      # Update Asterisk config files
      actions = [ ('DelCat', sip_id) ]
      Globals.manager.update_config(directory_asterisk  + 'sip.conf', 
         'chan_sip', actions)
      Globals.manager.update_config(directory_asterisk  + 'extensions.conf', 
         'dialplan', actions)
      if number:
         actions = [ ('Delete', 'astportal', number) ]
         Globals.manager.update_config(directory_asterisk  + 'voicemail.conf', 
            'app_voicemail_plain', actions)

      redirect('/phones/')


