# -*- coding: utf-8 -*-
# Phone CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, require, config
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
from astportal2.lib.asterisk import asterisk_update

from string import letters, digits
from random import choice
from os import system, popen #, rename
import logging
log = logging.getLogger(__name__)

server_sip = config.get('server.sip')
server_firmware = config.get('server.firmware')
server_config = config.get('server.config')
server_syslog = config.get('server.syslog')
server_ntp = config.get('server.ntp')
command_fping = config.get('command.fping')
command_arp = config.get('command.arp')
directory_tftp = config.get('directory.tftp')
directory_asterisk = config.get('directory.asterisk')

_vendors = {
   '00:0b:82': 'Grandstream',
   '00:04:f2': 'Polycom',
   '00:90:7a': 'Polycom',
}

_contexts = (('urgent', u'Urgences'), ('internal', u'Interne'), 
   ('services', u'Services'), ('local', u'Local'), ('islands', u'Iles'), 
   ('gsm', u'GSM'), ('international_ip', u'International IP'),
   ('international_pstn', u'International RTC'))

_callgroups = ((1, u'Groupe 1'), (2, u'Groupe 2'), (3, u'Groupe 3'), 
   (4, u'Groupe 4'), (5, u'Groupe 5'), (6, u'Groupe 6'), 
   (7, u'Groupe 7'), (8, u'Groupe 8'), (9, 'Groupe 9'))

_pickupgroups = ((1, u'Groupe 1'), (2, u'Groupe 2'), (3, u'Groupe 3'), 
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
      TextField('exten', validator=Int,
         not_empty = False,
         label_text=u'Poste', help_text=u'Entrez le numéro interne'),
      TextField('dnis', validator=Int,
         not_empty = False,
         label_text=u'Numéro direct', help_text=u'Entrez le numéro direct (SDA)'),
      CheckBoxTable('contexts',  validator=Int,
         options = _contexts,
         not_empty = False,
         default = ('urgent','internal','services'),
         label__text=u'Droits d\'appels'),
      CheckBoxTable('callgroups', validator=Int,
         options = _callgroups,
         label_text=u'Groupes d\'appels', 
         not_empty = False),
      CheckBoxTable('pickupgroups', validator=Int,
         options = _pickupgroups,
         label_text=u'Groupes d\'interception', 
         not_empty = False),
      SingleSelectField('dptm_id', options = departments,
         not_empty = False,
         label_text=u'Service facturé'),
      SingleSelectField('user_id', options=users,
         not_empty = False,
         label_text=u'Utilisateur'),
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
      TextField('exten', #validator=Int,
         label_text=u'Numéro', help_text=u'Entrez le numéro du téléphone'),
      TextField('dnis', #validator=Int,
         not_empty = False,
         label_text=u'Numéro direct', help_text=u'Entrez le numéro direct (SDA)'),
      CheckBoxList('contexts',
         options = _contexts,
         label_text=u'Contexte', help_text=u'Droits d\'appels'),
      CheckBoxList('callgroups', validator=Int,
         options = _callgroups,
         label_text=u'Groupes d\'appels', 
         help_text=u'Cochez les groupes d\'appel de l\'utilisateur'),
      CheckBoxList('pickupgroups', validator=Int,
         options = _pickupgroups,
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


def peer_info(sip_id=None, exten=None):
   '''Find peer by id or exten return ip address and user agent
   '''

   if sip_id is not None and 'SIP/'+sip_id in Globals.asterisk.peers:
      log.debug('peer_info sip_id  %s' % sip_id)
      peer = sip_id
   elif exten is not None and 'SIP/'+exten in Globals.asterisk.peers:
      log.debug('peer_info exten  %s' % exten)
      peer = exten
   else:
      log.warning('%s not registered ?' % sip_id)
      peer = None

   if peer:
      # Peer exists, try to find User agent
      if 'UserAgent' not in Globals.asterisk.peers['SIP/'+peer]:
         log.debug('SIPshowPeer(%s)' % peer)
         res = Globals.manager.sipshowpeer(peer)
         Globals.asterisk.peers['SIP/'+peer]['UserAgent'] = res.get_header('SIP-Useragent')
      if Globals.asterisk.peers['SIP/'+peer]['Address']:
         ip = (Globals.asterisk.peers['SIP/'+peer]['Address']).split(':')[0]
         ua = Globals.asterisk.peers['SIP/'+peer]['UserAgent']
      else:
         ip = ua = None

   else: 
      ip = ua = None

   return ip, ua


def row(p):
   '''Displays a formatted row of the phones list
   Parameter: Phone object
   '''
   dptm = Markup(u'<a href="/departments/%d/edit/">%s</a>' % \
      (p.department.dptm_id, p.department.comment)) if p.department else None
   user = Markup(u'<a href="/users/%d/edit/">%s</a>' % \
      (p.user.user_id, p.user.display_name)) if p.user else None

   ip, ua = peer_info(p.sip_id, p.exten)

   action =  u'<a href="'+ str(p.phone_id) + u'/edit" title="Modifier">'
   action += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   action += u'&nbsp;&nbsp;&nbsp;'
   action += u'<a href="#" onclick="del(\''+ str(p.phone_id) + \
         u'\',\'Suppression du téléphone ' + str(p.exten) + u'\')" title="Supprimer">'
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(action), ua, p.exten, p.dnis, user , dptm]


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
         sortname='exten',
         colNames = [u'Action', u'Modèle', u'Poste',
            u'Numéro direct', u'Utilisateur', u'Service'],
         colModel = [
            { 'width': 80, 'align': 'center', 'search': False, 'sortable': False },
            { 'name': 'ua', 'width': 140, 'search': False, 'sortable': False },
            { 'name': 'exten', 'width': 60 },
            { 'name': 'dnis', 'width': 60 },
            { 'name': 'user_id', 'width': 120, 'search': False },
            { 'name': 'department_id', 'width': 120, 'search': False },
            ],
         navbuttons_options = {'view': False, 'edit': False, 'add': True,
            'del': False, 'search': True, 'refresh': True, 
            'addfunc': js_callback('add'),
            },
         subGrid = True,
         subGridUrl = 'fetch_detail',
         subGridModel = [{
            'name': [u'Compte SIP', u'Secret SIP', u'Adresse IP', u'Adresse MAC'],
            'width': [100, 100, 100, 100]
            }],
         )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des téléphones', debug='')


   @expose('json')
   def fetch_detail(self, **kw):
      log.debug('fetch_detail')
      log.debug(kw)
      p = DBSession.query(Phone).get(kw['id'])
      ip, ua = peer_info(p.sip_id)
      if ip == 'None': 
         ip = ''
      else:
         if ua and ua.startswith('Grandstream GXP'):
            ip = Markup('''<a href="#" title="Connexion interface t&eacute;l&eacute;phone" onclick="phone_open('%s','%s', '%s');">%s</a>''' % (ip, p.password, 'GXP', ip))
         else:
            ip = Markup('''<a href="http://%s/" title="Connexion interface t&eacute;l&eacute;phone" target='_blank'>%s</a>''' % (ip, ip))
      data = [ { 'id'  : p.phone_id, 
         'cell': (p.sip_id, p.password, ip, p.mac) }]
      return dict(page=1, total=1, rows=data)

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
      if vendor not in _vendors.keys():
         return dict(status=4, msg=u"Type de téléphone inconnu")

      mac = '%s:%s' % (vendor,device)
      p = DBSession.query(Phone).filter(Phone.mac==mac).all()
      if len(p):
         return dict(status=5, 
               msg = u'Téléphone existant, voulez-vous le \
                     <a href="/phones/%s/edit">modifier</a>.' % p[0].phone_id)

      global new_phone
      if _vendors[vendor]=='Grandstream':
         new_phone = Grandstream(ip, mac)
         msg = u"Trouvé téléphone Grandstream : "
         if not new_phone.login(pwd):
            return dict(status=6, msg=msg+u'erreur login')
         infos = new_phone.infos()
         if not infos:
            return dict(status=6, msg=msg+u'erreur login')
         return dict(status = 0, ip = ip, mac = mac, conf = 'grandstream_configure',
               msg = msg + infos['model'] + ', ' + infos['version'])
      elif _vendors[vendor]=='Polycom':
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
      If a exten is attached to the phone, create exten in Asterisk database.
      If a user is attached to the phone, add callerid to phone ; if the user has
      email, add voicemail info to sip.conf and add entry in voicemail.conf
      Create entry in Asterisk sip.conf.
      '''

      # Check exten is not already used
      if kw['exten']:
         log.debug('Check exten ' +  kw['exten'])
         p = DBSession.query(Phone).filter(Phone.exten==kw['exten']).all()
         if len(p):
            return dict(status='bad_exten')

      # Check dnis is not already used
      if kw['dnis']:
         log.debug('Check dnis ' +  kw['dnis'])
         p = DBSession.query(Phone).filter(Phone.dnis==kw['dnis']).all()
         if len(p):
            return dict(status='bad_dnis')

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
      if kw['exten']: p.exten = kw['exten']
      if kw['dnis']: p.dnis = kw['dnis']
      if kw['dptm_id']!='-9999': p.department_id = kw['dptm_id']
      if kw['user_id']!='-9999': p.user_id = kw['user_id']
      if 'callgroups' in kw:
         p.callgroups = ','.join([str(x) for x in kw['callgroups']])
      if 'pickupgroups' in kw:
         p.pickupgroups = ','.join([str(x) for x in kw['pickupgroups']])
      if 'contexts' in kw:
         p.contexts = ','.join([str(x) for x in kw['contexts']])
      DBSession.add(p)

      asterisk_update(p)

      if kw['mac']:
         # Create provisionning file if MAC exists
         global new_phone
         log.debug('Configure ' +  kw['mac'])
         new_phone.configure( pwd, directory_tftp,
            server_firmware + '/phones/firmware', 
            server_config + '/phones/config', server_syslog,
            server_config + ':8080/phonebook/gs_phonebook_xml', '', '', '',
            sip_server, sip_id, sip_display_name, mwi_subscribe)

      flash(u'Nouveau téléphone "%s" créé' % (kw['exten']))
      return {'status': 'created'}


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, phone_id=None, dptm_id=None, user_id=None, 
         exten=None, **kw):
      ''' Display edit phone form
      '''
      ident = ''
      log.debug('Edit')
      p = DBSession.query(Phone).get(id) if id else DBSession.query(Phone).get(phone_id)
      v = {'phone_id': p.phone_id,
         'exten': p.exten,
         'dnis': p.dnis,
         'contexts': p.contexts.split(',') if  p.contexts else None,
         'callgroups': p.callgroups.split(',') if  p.callgroups else None,
         'pickupgroups': p.pickupgroups.split(',') if  p.pickupgroups else None,
         'dptm_id': p.department_id,
         'user_id': p.user_id,
         '_method': 'PUT'}
      if p.exten: ident = p.exten
      elif p.mac: ident = p.mac

      tmpl_context.form = edit_phone_form
      return dict(title = u'Modification téléphone ' + ident, debug='', values=v)

   class edit_form_valid(object):
      def validate(self, params, state):
         log.debug(params)
         f = edit_phone_form
         # Check phone exten
         if params['exten']: 
            p = DBSession.query(Phone).filter(Phone.exten==params['exten'])
            p = p.filter(Phone.phone_id!=params['phone_id']).all()
            if len(p):
               log.warning('Number exists %s, cannot update phone %s' % (params['exten'],params['phone_id']))
               flash(u'Le numéro "%s" est déjà utilisé' % (params['exten']),'error')
               raise Invalid('XXXX', 'ZZZ', state)
         return f.validate(params, state)

   @validate(edit_form_valid(), error_handler=edit)
   @expose()
   def put(self, phone_id, dptm_id, user_id, exten, dnis, contexts,
         callgroups=None, pickupgroups=None):
      ''' Update phone 

      User and exten information is independant from phone, there is no need
      to modify provisionning file.
      Create or update entry in Asterisk sip.conf.
      If a exten is attached to the phone, create exten in Asterisk database.
      If a user is attached to the phone, add callerid to SIP account ; if 
      the user has email, add voicemail info to sip.conf and add entry in 
      voicemail.conf.
      '''
      log.info('update %d' % phone_id)
      log.debug('Contexts %s' % contexts)
      log.debug('Callgroups %s' % callgroups)
      log.debug('Pickupgroups %s' % pickupgroups)

      p = DBSession.query(Phone).get(phone_id)
      old_exten = p.exten
      old_dnis = p.dnis

      if exten!=p.exten:
         log.debug('Exten has changed, %s -> %s' % (p.exten, exten))
         if exten=='':
            p.exten = None
         else:
            p.exten = exten

      if dnis!=p.dnis:
         log.debug('DNIS has changed, %s -> %s' % (p.dnis, dnis))
         if dnis=='':
            p.dnis = None
         else:
            p.dnis = dnis

      if p.department_id!=dptm_id:
         if dptm_id==-9999:
            p.department_id = None
         else:
            p.department_id = dptm_id

      if p.user_id!=user_id:
         if user_id==-9999:
            p.user_id = None
         else:
            p.user_id = user_id

      x = ','.join([str(x) for x in contexts])
      if p.contexts != x:
         log.debug('New contexts !')
         p.contexts = x

      x = ','.join([str(x) for x in callgroups])
      if p.callgroups != x:
         p.callgroups = x

      x = ','.join([str(x) for x in pickupgroups])
      if p.pickupgroups != x:
         p.pickupgroups = x

      asterisk_update(p, old_exten, old_dnis)

      flash(u'Téléphone modifié')
      redirect('/phones/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete phone from DB
      '''
      log.info('delete ' + kw['_id'])
      p = DBSession.query(Phone).get(kw['_id'])
      exten = p.exten
      DBSession.delete(p)
      flash(u'Téléphone supprimé', 'notice')

      if exten:
         # Update Asterisk DataBase
         Globals.manager.send_action({'Action': 'DBdel',
            'Family': 'exten', 'Key': exten})

      # Update Asterisk config files
      actions = [ ('DelCat', p.sip_id) ]
      Globals.manager.update_config(directory_asterisk  + 'sip.conf', 
         'chan_sip', actions)
      Globals.manager.update_config(directory_asterisk  + 'extensions.conf', 
         'dialplan', actions)
      if exten:
         actions = [ ('Delete', 'astportal', exten) ]
         Globals.manager.update_config(directory_asterisk  + 'voicemail.conf', 
            'app_voicemail_plain', actions)

      redirect('/phones/')


