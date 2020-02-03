# -*- coding: utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

# Phone CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, require, config, session
from tg.controllers import RestController
from tgext.menu import sidebar

try:
   from tg.predicates import in_group
except ImportError:
   from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField, CheckBoxList, CheckBoxTable, BooleanRadioButtonList
from tw.jquery import AjaxForm
from tw.forms.validators import NotEmpty, Int, Invalid, Bool, StringBoolean

from astportal2.lib.app_globals import Markup

from astportal2.model import DBSession, Phone, Department, User, Pickup, Sound
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.grandstream import Grandstream
from astportal2.lib.cisco import Cisco
from astportal2.lib.mitel import Mitel
from astportal2.lib.app_globals import Globals, fetch_contacts
from astportal2.lib.asterisk import asterisk_update_phone

from string import letters, digits
from random import choice
from os import system, popen, rename, listdir, unlink, rmdir
import re
import logging
log = logging.getLogger(__name__)

server_sip = config.get('server.sip')
server_sip2 = config.get('server.sip2')
server_firmware = config.get('server.firmware')
server_config = config.get('server.config')
server_syslog = config.get('server.syslog')
server_ntp = config.get('server.ntp')
command_fping = config.get('command.fping')
command_arp = config.get('command.arp')
directory_tftp = config.get('directory.tftp')
directory_asterisk = config.get('directory.asterisk')
sip_type = config.get('asterisk.sip', 'sip')

_vendors = {
   '00:0b:82': 'Grandstream',
   'c0:74:ad': 'Grandstream', # GRP
   '00:04:f2': 'Polycom',
   '00:90:7a': 'Polycom',
   '1c:df:0f': 'Cisco',
   '54:7c:69': 'Cisco',
   '00:10:bc': 'Aastra',
   '00:08:5d': 'Aastra',
   '08:00:0f': 'Aastra', # Mitel == Aastra ?
}

_contexts = (('urgent', u'Urgences'), ('internal', u'Interne'), 
   ('services', u'Services'), ('shortcuts', u'Raccourcis'), ('tahitimoorea', u'Tahiti - Moorea'),
   ('pyf', u'Polynésie française'), ('international', u'International'))

def departments():
   a = [] # [('-9999',' - - - ')]
   for d in DBSession.query(Department).order_by(Department.comment):
       a.append((d.dptm_id,d.comment))
   return a

def users():
   a = [('-9999', ' - - - ')]
   for u in DBSession.query(User).order_by(User.display_name):
      a.append((u.user_id, u.display_name))
   return a

def ringtones():
   a = [('-1', u'Par défaut')]
   for r in DBSession.query(Sound). \
                      filter(Sound.type==2). \
                      order_by(Sound.name):
      a.append((r.sound_id, r.name))
   return a


# New phone page contains 2 forms, displayed in two tabs:
# the first form (ip_form) "discovers" the phone
ip_form = AjaxForm(
   id = 'ip_form',
   fields = [ 
      TextField('ip', label_text=u'Adresse IP'), 
#         help_text=u'ex. 192.168.123.234'),
      TextField('mac', label_text=u'Adresse matérielle (MAC)'),
#         help_text=u'ex. 01:23:45:68:89:ab'),
      TextField('pwd', label_text=u'Mot de passe', default='admin'),
      ],
#   hover_help = True,
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
         label_text=u'Poste'), # help_text=u'Entrez le numéro interne'),
      TextField('dnis', validator=Int,
         not_empty = False,
         label_text=u'Numéro direct'), # help_text=u'Entrez le numéro direct (SDA)'),
      BooleanRadioButtonList('fax',
         options = [ (False, u'Non'), (True, u'Oui')],
         default = False,
         label_text = u"Télécopieur",
         validator = Bool),
#         help_text = u"Cocher pour ATA avec télécopieur "),
      CheckBoxTable('contexts',  validator=Int,
         options = _contexts,
         not_empty = False,
         default = ('urgent', 'internal', 'services', 'shortcuts'),
         label_text=u'Droits d\'appels'), # help_text='Autorisations pour les appels sortants'),
      CheckBoxTable('callgroups', validator=Int,
         options = DBSession.query(Pickup.pickup_id,Pickup.name).order_by(Pickup.pickup_id),
         label_text=u'Groupes d\'appels', 
         not_empty = False),
      CheckBoxTable('pickupgroups', validator=Int,
         options = DBSession.query(Pickup.pickup_id,Pickup.name).order_by(Pickup.pickup_id),
         label_text=u'Groupes d\'interception', 
         not_empty = False),
      SingleSelectField('dptm_id', options = departments,
         not_empty = False,
         label_text=u'Service facturé'),
      SingleSelectField('user_id', options=users,
         not_empty = False,
         label_text=u'Utilisateur'),
      SingleSelectField('ringtone_id', options=ringtones,
         not_empty = False,
         label_text = u'Sonnerie'),
      BooleanRadioButtonList('hide_from_phonebook',
         options = [ (False, u'Non'), (True, u'Oui')],
         default = False,
         label_text = u"Cacher de l'annuaire",
         validator = Bool),
#         help_text = u"Cocher pour ne pas montrer ce poste dans l'annuaire"),
#      TextField('timeout', validator=Int,
#         not_empty = True, default=25,
#         label_text=u'Durée de sonnerie'), # help_text=u'Attente avant non réponse / messagerie'),
      BooleanRadioButtonList('block_cid_in',
         options = [ (False, u'Non'), (True, u'Oui')],
         default = False,
         label_text = u"Bloquer l'affichage du numéro entrant",
         validator = Bool),
#         help_text = u"Cocher pour ne pas montrer l'identifiant des appels entrants"),
      BooleanRadioButtonList('block_cid_out',
         options = [ (False, u'Non'), (True, u'Oui')],
         default = False,
         label_text = u"Activation numéro secret",
         validator = Bool),
      BooleanRadioButtonList('priority',
         options = [ (False, u'Non'), (True, u'Oui')],
         default = False,
         label_text = u"Appel prioritaire",
         validator = Bool),
#         help_text = u"Cocher pour ne pas montrer l'identifiant des appels sortants"),
      TextField('phonebook_label',
         not_empty = False,
         label_text=u'Libellé pour annuaire'), # help_text=u'Attente avant non réponse / messagerie'),
      TextField('secretary',
         label_text=u'Numéro secrétaire'), # help_text=u'Numéro secrétaire pour filtrage'
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
#   hover_help = True
   beforeSubmit = js_callback('wait2')
   success = js_callback('created')
   action = '/phones/create'
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
         label_text=u'Poste'), # help_text=u'Entrez le numéro interne'),
      TextField('dnis', #validator=Int,
         not_empty = False,
         label_text=u'Numéro direct'), # help_text=u'Entrez le numéro direct (SDA, 6 chiffres)'),
      BooleanRadioButtonList('fax',
         options = [ (False, u'Non'), (True, u'Oui')],
         default = False,
         label_text = u"Télécopieur",
         validator = StringBoolean),
#         help_text = u"Cocher pour ATA avec télécopieur "),
      CheckBoxList('contexts',
         options = _contexts,
         label_text=u'Droits d\'appels'), # help_text='Autorisations pour les appels sortants'),
      CheckBoxList('callgroups', validator=Int,
         options = DBSession.query(Pickup.pickup_id,Pickup.name).order_by(Pickup.pickup_id),
         label_text=u'Groupes d\'appels'), 
#         help_text=u'Cochez les groupes d\'appel de l\'utilisateur'),
      CheckBoxList('pickupgroups', validator=Int,
         options = DBSession.query(Pickup.pickup_id,Pickup.name).order_by(Pickup.pickup_id),
         label_text=u'Groupes d\'interception'),
#         help_text=u'Cochez les groupes d\'interception de l\'utilisateur'),
      SingleSelectField('dptm_id',
         options= departments,
         label_text=u'Service', # help_text=u'Service facturé',
         validator=Int
         ),
      SingleSelectField('user_id',
         options= users,
         label_text=u'Utilisateur', # help_text=u'Utilisateur du téléphone',
         validator=Int
         ),
      SingleSelectField('ringtone_id',
         options=ringtones,
         label_text = u'Sonnerie',
         validator=Int
         ),
      BooleanRadioButtonList('hide_from_phonebook',
         options = [ (False, u'Non'), (True, u'Oui')],
         validator = StringBoolean,
         label_text = u"Cacher de l'annuaire"),
#         help_text = u"Cocher pour ne pas montrer ce poste dans l'annuaire"),
#      TextField('timeout', validator=Int,
#         not_empty = True, default=25,
#         label_text=u'Durée de sonnerie'), # help_text=u'Attente avant non réponse / messagerie'),
      BooleanRadioButtonList('block_cid_in',
         options = [ (False, u'Non'), (True, u'Oui')],
         default = False,
         label_text = u"Bloquer l'identifiant d'appelant",
         validator = StringBoolean),
#         help_text = u"Cocher pour ne pas montrer l'identifiant des appels entrants"),
      BooleanRadioButtonList('block_cid_out',
         options = [ (False, u'Non'), (True, u'Oui')],
         default = False,
         label_text = u"Bloquer l'identifiant d'appel",
         validator = StringBoolean),
      BooleanRadioButtonList('priority',
         options = [ (False, u'Non'), (True, u'Oui')],
         default = False,
         label_text = u"Appel prioritaire",
         validator = StringBoolean),
#         help_text = u"Cocher pour ne pas montrer l'identifiant des appels sortants"),
      TextField('phonebook_label',
         not_empty = False,
         label_text=u'Libellé pour annuaire'), # help_text=u'Attente avant non réponse / messagerie'),
      TextField('secretary',
         label_text=u'Numéro secrétaire'), # help_text=u'Numéro secrétaire pour filtrage'
      HiddenField('_method', validator=None), # Needed by RestController
      HiddenField('phone_id', validator=Int),
      ]
   submit_text = u'Valider...'
   action = '/phones/'
#   hover_help = True
edit_phone_form = Edit_phone_form('edit_form_phone')


def peer_info(sip_id=None, exten=None):
   '''Find peer by id or exten, return ip address and user agent
   '''

   tech = 'SIP/' if sip_type=='sip' else 'PJSIP/'
   if sip_id is not None and tech+sip_id in Globals.asterisk.peers:
      log.debug('peer_info sip_id  %s' % sip_id)
      peer = sip_id
   elif exten is not None and tech+exten in Globals.asterisk.peers:
      log.debug('peer_info exten  %s' % exten)
      peer = exten
   else:
      log.warning('%s:%s not registered ?' % (sip_id, exten))
      peer = None

   ip = ua = state = None
   if peer:
      log.debug('Peer status: %s', Globals.asterisk.peers[tech+peer])
      # Peer exists, try to find User agent
      if 'UserAgent' not in Globals.asterisk.peers[tech+peer]:
         res = Globals.manager.sipshowpeer(peer)
         ua = res.get_header('SIP-Useragent')
         Globals.asterisk.peers[tech+peer]['UserAgent'] = ua

      else:
         ua = Globals.asterisk.peers[tech+peer]['UserAgent']

      if 'Address' in Globals.asterisk.peers[tech+peer] and \
            Globals.asterisk.peers[tech+peer]['Address'] is not None:
            ip = (Globals.asterisk.peers[tech+peer]['Address']).split(':')[0]

      if 'State' in Globals.asterisk.peers[tech+peer] and \
            Globals.asterisk.peers[tech+peer]['State'] is not None:
         state = Globals.asterisk.peers[tech+peer]['State']

   log.debug('peer_info %s%s:%s -> %s, %s, %s', 
              tech,
              sip_id,
              exten,
              ip,
              ua,
              state)
   return ip, ua, state


def row(p, unavailable_only):
   '''Displays a formatted row of the phones list
   Parameter: Phone object
   '''

   ip, ua, st = peer_info(p.sip_id, p.exten)
   if unavailable_only and st!='UNAVAILABLE':
       return None

   try:
      dptm = Markup(u'<a href="/departments/%d/edit/">%s</a>' % \
         (p.department.dptm_id, p.department.comment))
   except:
      dptm = None
   try:
      user = Markup(u'<a href="/users/%d/edit/">%s</a>' % \
         (p.user.user_id, p.user.display_name))
   except:
      user = None

   if ua is None: ua = ''
   if ip is None: ip = ''

   action =  u'<a href="'+ str(p.phone_id) + u'/edit" title="Modifier">'
   action += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   action += u'&nbsp;&nbsp;&nbsp;'
   action += u'<a href="#" onclick="del(\''+ str(p.phone_id) + \
         u'\',\'Suppression du téléphone ' + str(p.exten) + u'\')" title="Supprimer">'
   action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'
   if st == 'UNAVAILABLE':
      ua = '<span style="color: red;">%s</span>' % ua
      exten = '<span style="color: red;">%s</span>' % p.exten
   elif st in ('RING', 'RINGING', 'BUSY', 'INUSE', 'ONHOLD'):
      ua = '<span style="color: blue;">%s</span>' % ua
      exten = '<span style="color: blue;">%s</span>' % p.exten
   elif st == 'NOT_INUSE':
      ua = '<span style="color: green;">%s</span>' % ua
      exten = '<span style="color: green;">%s</span>' % p.exten
   else:
      log.warning('Unknown phone state "%s" sip %s exten %s', st, p.sip_id, p.exten)
      exten = '<span style="color: orange;">%s</span>' % p.exten

   return [Markup(action), Markup(ua), Markup(exten), p.dnis, user , dptm]


class Phone_ctrl(RestController):
 
   allow_only = in_group('admin', 
      msg=u'Vous devez appartenir au groupe "admin" pour gérer les téléphones')

   @sidebar(u'-- Administration || Téléphones', sortorder = 10,
      icon = '/images/internet-telephony.png')
   @expose('astportal2.templates.grid_phone')
   def get_all(self):
      ''' List all phones
      '''

      if Globals.manager is None:
         flash(u'Vérifier la connexion Asterisk', 'error')
#      else:
#         # Refresh Asterisk peers
#         Globals.manager.sippeers()
#         Globals.manager.send_action({'Action': 'DeviceStateList'})

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
         postData = {'unavailable_only': 
               js_callback('''\
                  function() { return $('#unavailable_only').attr('checked');}\
               ''')}, # Don't display deleted campaigns by default
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
#      tmpl_context.form = None
#      tmpl_context.count = u'Total : %d téléphones' % DBSession.query(Phone).count()
      return dict( title=u'Liste des téléphones', debug='')


   @expose('json')
   def fetch_detail(self, **kw):
      log.debug('fetch_detail')
      log.debug(kw)
      p = DBSession.query(Phone).get(kw['id'])
      ip, ua, st = peer_info(p.sip_id, p.exten)
      if ip == 'None': 
         ip = ''
      else:
         ip = Markup('''<a href="https://%s/" title="Connexion interface t&eacute;l&eacute;phone" target='_blank'>%s</a>''' % (ip, ip))
      data = [ { 'id'  : p.phone_id, 
         'cell': (p.sip_id, p.password, ip, p.mac) }]
      return dict(page=1, total=1, rows=data)

   @expose('json')
   @require(in_group('admin',
      msg=u'Seul un membre du groupe administrateur peut afficher la liste des téléphones'))
   def fetch(self, rows, page, sidx='user_name', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, unavailable_only='false', **kw):
      ''' Function called on AJAX request made by FlexGrid
      Fetch data from DB, return the list of rows + total + current page
      '''

      unavailable_only = True if unavailable_only=='true' else False

      fetch_contacts()
#      if Globals.manager is not None:
#         # Refresh Asterisk peers
#         if sip_type=='sip':
#            Globals.manager.sippeers()
#         Globals.manager.send_action({'Action': 'DeviceStateList'})
#         Globals.manager.send_action({'Action': 'IAXpeers'})
#         resp = Globals.manager.send_action({'Action': 'Command', 'Command': 'pjsip show contacts'})
#         log.debug('PJSIP Contacs returns:\n%s' % resp)

      log.debug('Fetch : Globals.asterisk.peers= %s ' % Globals.asterisk.peers)

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
      log.debug('sidx=%s, col=%s' % (sidx,column))
      phones = phones.order_by(getattr(column, sord)())
      if not unavailable_only:
         phones = phones.offset(offset).limit(rows)

      data = []
      for p in phones:
         cell = row(p, unavailable_only)
         if cell is None:
             continue
         data.append({ 'id': p.phone_id, 'cell': cell })

      return dict(page=page, total=total, rows=data)


   @expose('astportal2.templates.form_new_phone')
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
      match = re.search('(\w\w:\w\w:\w\w):(\w\w:\w\w:\w\w)', mac.lower())
      if not match:
         return dict(status=3, msg=u"Téléphone injoignable, vérifiez l'adresse")
      vendor, device = match.groups()
      log.debug('vendor=%s, device=%s' % (vendor,device))
      if vendor not in _vendors.keys():
         return dict(status=4, msg=u"Type de téléphone inconnu")

      mac = '%s:%s' % (vendor,device)
      p = DBSession.query(Phone).filter(Phone.mac==mac).all()
      if len(p):
         return dict(status=5, 
               msg = u'Téléphone existant, voulez-vous le \
                     <a href="/phones/%s/edit">modifier</a>.' % p[0].phone_id)

      if _vendors[vendor]=='Grandstream':
         new_phone = Grandstream(ip, mac)
         msg = u"Trouvé téléphone Grandstream : "
         if not new_phone.login(pwd):
            return dict(status=6, msg=msg+u'erreur login')
         infos = new_phone.infos()
         if not infos:
            return dict(status=6, msg=msg+u'erreur login')

         session['new_phone'] = new_phone
         session.save()

         return dict(status = 0, ip = ip, mac = mac, conf = 'grandstream_configure',
               msg = msg + infos['model'] + ', ' + infos['version'])

      elif _vendors[vendor]=='Cisco':
         new_phone = Cisco(ip, mac)
         msg = u"Trouvé téléphone Cisco : "
         if not new_phone.login(pwd):
            return dict(status=6, msg=msg+u'erreur login')
         infos = new_phone.infos()
         if not infos:
            return dict(status=6, msg=msg+u'erreur login')

         session['new_phone'] = new_phone
         session.save()

         return dict(status=0, ip=ip, mac=mac, conf='cisco_configure',
            msg = msg + infos['model'] + ', ' + infos['version'])

      elif _vendors[vendor]=='Polycom':
         return dict(status=0, ip=ip, mac=mac, conf='polycom_configure',
               msg=u"Trouvé téléphone Polycom")

      elif _vendors[vendor] == 'Aastra':
         new_phone = Mitel(ip, mac)
         msg = u"Trouvé téléphone Aastra / Mitel : "

         if not new_phone.login(pwd):
            return dict(status=6, msg=msg+u'erreur login')

         infos = new_phone.infos()

         if not infos:
            return dict(status=6, msg=msg+u'erreur login')

         session['new_phone'] = new_phone
         session.save()

         return dict(status = 0, ip = ip, mac = mac, conf = 'mitel_configure',
               msg = msg + infos['model'] + ', ' + infos['version'])


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
      If an extension is attached to the phone, create exten in Asterisk database.
      If a user is attached to the phone, add callerid to phone; if the user has
      email, add voicemail info to sip.conf and add entry in voicemail.conf
      Create entry in Asterisk sip.conf.
      '''

      # Check exten is not already used
      if kw['exten']:
         log.debug('Check exten ' +  kw['exten'])
         p = DBSession.query(Phone).filter(Phone.exten==kw['exten']).all()
         if len(p):
            return dict(status='bad_exten')
         exten = re.sub(r'\D', '', kw['exten'])

      # Check dnis is not already used
      if kw['dnis']:
         log.debug('Check dnis ' +  kw['dnis'])
         p = DBSession.query(Phone).filter(Phone.dnis==kw['dnis']).all()
         if len(p):
            return dict(status='bad_dnis')
         dnis = re.sub(r'\D', '', kw['dnis'])

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
      need_voicemail_update = False
      sip_server = server_sip
      sip_server2 = server_sip2
      sip_display_name = ''
      mwi_subscribe = 0
      if kw['user_id']!='-9999':
         u = DBSession.query(User).get(kw['user_id'])
         sip_display_name = u.ascii_name
         if u.email_address:
            mwi_subscribe = 1
            need_voicemail_update = True
 
      # Save phone info to database
      log.debug('Save to database ' +  kw['mac'])
      p = Phone()
      p.sip_id = sip_id
      new_phone = None
      if kw['mac']:
         new_phone = session['new_phone']
         p.mac = kw['mac']
         p.vendor = new_phone.vendor
         p.model = new_phone.model
         log.debug('%s %s', new_phone.vendor, new_phone.model)
      p.password = pwd
      if kw['exten']: p.exten = exten
      if kw['dnis']: p.dnis = dnis
      if kw['dptm_id']!='-9999': p.department_id = kw['dptm_id']
      if kw['user_id']!='-9999': p.user_id = kw['user_id']
      ringtone = None
      if kw['ringtone_id']!='-1':
          p.ringtone_id = kw['ringtone_id']
          try:
              ringtone = DBSession.query(Sound).get(int(kw['ringtone_id'])).name
          except:
              pass
      if 'callgroups' in kw:
         p.callgroups = ','.join([str(x) for x in kw['callgroups']])
      if 'pickupgroups' in kw:
         p.pickupgroups = ','.join([str(x) for x in kw['pickupgroups']])
      if 'contexts' in kw:
         p.contexts = ','.join([str(x) for x in kw['contexts']])
      p.hide_from_phonebook = True if kw['hide_from_phonebook']==u'True' else False
      p.fax = True if kw['fax']==u'True' else False
      p.block_cid_in = True if kw['block_cid_in']==u'True' else False
      p.block_cid_out = True if kw['block_cid_out']==u'True' else False
      p.priority = True if kw['priority']==u'True' else False
      p.phonebook_label = kw['phonebook_label'] 
      p.secretary = kw['secretary'] 
      DBSession.add(p)

      asterisk_update_phone(p)

      if new_phone:
         # Create provisionning file if MAC exists

         log.debug('Configure ' +  kw['mac'])
         new_phone.configure( pwd, directory_tftp,
            server_firmware + '/phones/firmware', 
            server_config + '/phones/config', server_ntp,
            server_config, '', '', '',
            sip_server, sip_id, sip_display_name, mwi_subscribe,
            screen_url = server_config, exten=p.exten,
            sip_server2=sip_server2, secretary=kw['secretary'],
            ringtone=ringtone)

         session.save()

      flash(u'Nouveau téléphone "%s" créé' % (kw['exten']))
      return {'status': 'created'}


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, phone_id=None, dptm_id=None, user_id=None, 
         exten=None, **kw):
      ''' Display edit phone form
      '''
      ident = ''
      p = DBSession.query(Phone).get(id) if id else DBSession.query(Phone).get(phone_id)
      log.debug('Edit fax=%s, hide_from_phonebook=%s' % \
         (p.fax, p.hide_from_phonebook))
      v = {'phone_id': p.phone_id,
         'exten': p.exten,
         'dnis': p.dnis,
         'contexts': p.contexts.split(',') if  p.contexts else None,
         'callgroups': p.callgroups.split(',') if  p.callgroups else None,
         'pickupgroups': p.pickupgroups.split(',') if  p.pickupgroups else None,
         'dptm_id': p.department_id,
         'user_id': p.user_id,
         'hide_from_phonebook': p.hide_from_phonebook,
         'fax': p.fax,
         'block_cid_in': p.block_cid_in,
         'block_cid_out': p.block_cid_out,
         'priority': p.priority,
         'ringtone_id': p.ringtone_id,
         'phonebook_label': p.phonebook_label,
         'secretary': p.secretary,
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
   def put(self, phone_id, dptm_id, user_id, exten, dnis,
         hide_from_phonebook, fax, block_cid_in, block_cid_out,
         priority, phonebook_label, secretary, ringtone_id,
          contexts=None,callgroups=None, pickupgroups=None):
      ''' Update phone 

      User and exten information is independant from phone, there is no need
      to modify provisionning file.
      Create or update entry in Asterisk sip.conf.
      If a exten is attached to the phone, create exten in Asterisk database.
      If a user is attached to the phone, add callerid to SIP account ; if 
      the user has email, add voicemail info to sip.conf and add entry in 
      voicemail.conf.
      '''
      log.info('update %d', phone_id)
      log.debug('Contexts %s', contexts)
      log.debug('Callgroups %s', callgroups)
      log.debug('Pickupgroups %s', pickupgroups)
      log.debug('Hide from phonebook %s', hide_from_phonebook)
      log.debug('Fax %s', fax)
      log.debug('Block cid in %s', block_cid_in)
      log.debug('Block cid out %s', block_cid_out)

      p = DBSession.query(Phone).get(phone_id)
      old_exten = p.exten
      old_dnis = p.dnis

      if exten!=p.exten:
         exten = re.sub(r'\D', '', exten)
         log.debug('Exten has changed, %s -> %s' % (p.exten, exten))
         if exten=='':
            p.exten = None
         else:
            p.exten = exten

      if dnis!=p.dnis:
         dnis = re.sub(r'\D', '', dnis) if dnis is not None else ''
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
      ringtone_id = int(ringtone_id)
      log.debug('before ringtone = %s', ringtone_id)
      if ringtone_id==-1:
          p.ringtone_id = None
          ringtone = None
      else:
          p.ringtone_id = ringtone_id
          try:
              ringtone = DBSession.query(Sound).get(int(ringtone_id)).name
          except:
              ringtone = None
              p.ringtone_id = None
      log.debug('after ringtone = %s (%s)', ringtone, ringtone_id)

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

      p.hide_from_phonebook = hide_from_phonebook
      p.fax = fax
      p.block_cid_in = block_cid_in
      p.block_cid_out = block_cid_out
      p.priority = priority
      p.phonebook_label = phonebook_label 
      p.secretary = secretary 

      asterisk_update_phone(p, old_exten, old_dnis)

      if p.vendor == 'Grandstream':
         # Create provisionning file and configure phone
         ip, ua, state = peer_info(p.sip_id, p.exten)
         log.info('Configure %s %s %s %s', p.mac, ip, ua, state)
         gs = Grandstream(ip, p.mac)
         gs.login(p.password)
         gs.infos()
         mwi_subscribe = 0
         sip_display_name = None
         if p.user_id!='-9999':
            try:
               u = DBSession.query(User).get(p.user_id)
               sip_display_name = u.ascii_name
               if u.email_address:
                  mwi_subscribe = 1
            except:
               pass
         gs.configure( p.password, directory_tftp,
            server_firmware + '/phones/firmware', 
            server_config + '/phones/config', server_ntp,
            server_config, '', '', '',
            server_sip, p.sip_id, sip_display_name, mwi_subscribe,
            screen_url = server_config, exten=p.exten,
            sip_server2=server_sip2, secretary=secretary,
            ringtone=ringtone)

      flash(u'Téléphone modifié')
      redirect('/phones/%d/edit' % phone_id)


   @expose()
   def delete(self, id, **kw):
      ''' Delete phone from DB
      '''
      p = DBSession.query(Phone).get(kw['_id'])
      log.info('delete %s (exten=%s, dnis=%s, sip=%s' % \
            (kw['_id'], p.exten, p.dnis, p.sip_id))

      # Remove from database
      DBSession.delete(p)

      # Update Asterisk config files
      if p.exten:
         # Update Asterisk DataBase
         Globals.manager.send_action({'Action': 'DBdel',
            'Family': 'exten', 'Key': p.exten})
         Globals.manager.send_action({'Action': 'DBdel',
            'Family': 'netxe', 'Key': p.sip_id})

         # Delete context, hint...
         actions = [ ('DelCat', p.sip_id),
               ('Delete', 'hints', 'exten', None, 
               '%s,hint,%s/%s' % (
                   p.exten,
                   'SIP' if sip_type=='sip' else 'PJSIP', 
                   p.sip_id))]

         # ... and DNIS
         if p.dnis is not None:
            actions.append(('Delete', 'dnis', 'exten', None, 
               '%s,1,Gosub(stdexten,%s,1)' % (p.dnis[-4:], p.exten)))

         res = Globals.manager.update_config(
            directory_asterisk  + 'extensions.conf', 
            'dialplan', actions)
         log.debug('Delete context, hint (DNIS) from extensions.conf returns %s' % res)

         # Delete voicemail entry
         res = Globals.manager.update_config(directory_asterisk  + 'voicemail.conf', 
            'app_voicemail', [ ('Delete', 'astportal', p.exten) ])
         log.debug('Delete entry from voicemail.conf returns %s' % res)

      # Delete SIP entry
      actions = [ ('DelCat', p.sip_id) ]
      if sip_type=='sip':
         res = Globals.manager.update_config(directory_asterisk  + 'sip.conf', 
            'chan_sip', actions)
      else:
         res = Globals.manager.update_config(directory_asterisk  + 'pjsip_wizard.conf', 
            'res_pjsip', actions)
      log.debug('Delete entry from SIP returns %s' % res)

      mac = p.mac.replace(':', '') if p.mac is not None else ''

      if p.vendor=='Grandstream':
         # Remove private firmware directory
         tftp = directory_tftp + 'phones/firmware'
         try:
            for f in listdir('%s/%s' % (tftp, mac)):
               unlink('%s/%s/%s' % (tftp, mac, f))
            rmdir('%s/%s' % (tftp, mac))
         except:
            log.error('rmdir error %s/%s' % (tftp, mac))

      # Backup phone configuration
      try:
         config = directory_tftp + 'phones/config/cfg%s' % mac
         rename(config, config + '.BAK')
         rename(config + '.txt', config + '.txt.BAK')
         log.warning('%s Config files saved' % mac)
      except:
         log.error('%s Config files save (%s)' % (mac, config))

      flash(u'Téléphone supprimé', 'notice')
      redirect('/phones/')


