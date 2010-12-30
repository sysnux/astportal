# -*- coding: utf-8 -*-
# Phone CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, require
from tg.controllers import RestController

from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField
from tw.jquery import AjaxForm
from tw.forms.validators import NotEmpty, Int

from genshi import Markup

from astportal2.model import DBSession, Phone, Department, User
from astportal2.lib.myjqgrid import MyJqGrid

from os import system, popen #, rename
import logging
log = logging.getLogger(__name__)


def departments():
   a = [(-1,' - - - ')]
   for d in DBSession.query(Department).order_by(Department.comment):
       a.append((d.dptm_id,d.comment))
   return a
 
def users():
   a = [(-1,' - - - ')]
   for u in DBSession.query(User).order_by(User.display_name):
      a.append((u.user_id, u.display_name))
   return a
 
class New_phone_form(TableForm):
   ''' New phone form
   '''

   fields = [
         TextField('number', validator=Int,
            label_text=u'Numéro', help_text=u'Entrez le numéro du téléphone'),
         SingleSelectField('dptm_id', options = departments,
            label_text=u'Service', help_text=u'Service facturé'),
         SingleSelectField('user_id', options=users,
            label_text=u'Utilisateur', help_text=u'Utilisateur du téléphone'),
         HiddenField('mac', validator=Int),
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
         TextField('number', validator=Int,
            label_text=u'Numéro', help_text=u'Entrez le numéro du téléphone'),
         SingleSelectField('dptm_id', 
            options= departments,
            label_text=u'Service', help_text=u'Service facturé',
            valdator=Int
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


ip_form = AjaxForm(
      id = 'ip_form',
      fields = [ TextField('ip', validator=NotEmpty,
         label_text=u'Adresse IP', help_text=u'Entrez l\'adresse du téléphone')],
      beforeSubmit = js_callback('wait'),
      success = js_callback('phone_ok'),
      action = 'check_phone',
      dataType = 'JSON',
      target = None,
      clearForm = False,
      resetForm = False,
      timeout = '60000',
      )


def row(p):
   '''Displays a formatted row of the phones list
   Parameter: Phone object
   '''
   dptm = p.department.name if p.department else ''
   user = p.user.display_name if p.user else ''

   html =  u'<a href="'+ str(p.phone_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   html += u'&nbsp;&nbsp;&nbsp;'
   html += u'<a href="#" onclick="del(\''+ str(p.phone_id) + \
         u'\',\'Suppression du téléphone ' + str(p.number) + u'\')" title="Supprimer">'
   html += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(html), p.mac, p.number, user , dptm]


class Phone_ctrl(RestController):
   
   allow_only = in_group('admin', 
         msg=u'Vous devez appartenir au groupe "admin" pour gérer les téléphones')

   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all phones
      '''
      grid = MyJqGrid( id='grid', url='fetch', caption=u'Téléphones',
            sortname='number',
            colNames = [u'Action', u'Identifiant', u'Numéro', u'Utilisateur', u'Service'],
            colModel = [ 
               { 'display': u'Action', 'width': 80, 'align': 'center', 'search': False },
               { 'name': 'mac', 'width': 80 },
               { 'name': 'number', 'width': 80 },
               { 'name': 'user_id', 'width': 160, 'search': False },
               { 'name': 'department_id', 'width': 160, 'search': False } ],
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
   def check_phone(self, ip):
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
      vendors = {
            '00:0b:82': 'Grandstream',
            '00:04:f2': 'Polycom',
            '00:90:7a': 'Polycom',
            }

      if not vendors.has_key(vendor):
         return dict(status=4, msg=u"Téléphone inconnu")
      
      mac = '%s:%s' % (vendor,device)
      p = DBSession.query(Phone).filter(Phone.mac==mac).all()
      if len(p):
         return dict(status=5, 
               msg = u'Téléphone existant, voulez-vous le \
                     <a href="/phones/%s/edit">modifier</a>.' % p[0].phone_id)

      if vendors[vendor]=='Grandstream':
         return dict(status=0, mac=mac, 
               msg=u"Trouvé téléphone Grandstream, configuration en cours")
         # Generate conf file
         cfg_name = '/tmp/gs-cfg%s%s.cfg' % (
               vendor.replace(':',''),device.replace(':',''))
         cfg = open(cfg_name, 'w')
         template = \
'''## Configuration template for GXP2000/GXP2020/GXP1200/GXP2010/GXP280/GXP285 firmware version 1.2.5.2

# Admin password for web interface
P2 = %s

# No Key Entry Timeout. Default - 4 seconds.
P85 = 4

# Use # as Dial Key. 0 - no, 1 - yes
P72 = 1

# Local RTP port (1024-65535, default 5004)
P39 = 5004 

# Use Random Port. 0 - no, 1 - yes
P78 = 0

# Keep-alive interval (in seconds. default 20 seconds)
P84 = 20

# Firmware Upgrade. 0 - TFTP Upgrade,  1 - HTTP Upgrade.
P212 = 0

# Firmware Server Path
P192 = %s

# Config Server Path
P237 = %s

# XML Config File Password   (for GXP280/GXP285/GXP1200 only)
P1359 =

# Firmware File Prefix
P232 = 

# Firmware File Postfix
P233 = 

# Config File Prefix
P234 = gs-

# Config File Postfix
P235 = .cfg

# Automatic Upgrade. 0 - No, 1 - Yes. Default is No.
P194 = 1

# Check for new firmware every () minutes, unit is in minute, minimnu 60 minutes, default is 7 days.
P193 = 1440

# Use firmware pre/postfix to determine if f/w is required
# 0 = Always Check for New Firmware 
# 1 = Check New Firmware only when F/W pre/suffix changes
# 2 = Always Skip the Firmware Check
P238 = 0

# Authenticate Conf File. 0 - No, 1 - Yes. Default is No.
P240 = 0

#----------------------------------------
# XML Phonebook
#----------------------------------------
# Enable Phonebook XML Download
# 0 = No
# 1 = YES, HTTP
# 2 = YES, TFTP
P330 = 1

# Phonebook XML Server Path
# This is a string of up to 128 characters that should contain a path to the XML file.  
# It MUST be in the host/path format. For example: "directory.grandstream.com/engineering"
P331 = %s/phonebook

# Phonebook Download Interval
# This is an integer variable in hours.  
# Valid value range is 0-720 (default 0), and greater values will default to 720
P332 = 1

# Remove Manually-edited entries on Download
# 0 - No, 1 - Yes, other values ignored
P333 = 0

# LDAP Script Server Path
P1304 = 

#---------------------------------------
# XML Idle Screen 
# N/A for GXP1200 and GXP280
#---------------------------------------
# Enable Idle Screen XML Download
# 0 = No
# 1 = YES, HTTP
# 2 = YES, TFTP
P340 = 0

# Download Screen XML At Boot-up. 0 - no, 1 - yes 
P1349 = 0

# Use Custom File Name. 0 - no, 1 - yes 
# GXP20x0 only
P1343 = 0

# Idle Screen XML Server Path
# This is a string of up to 128 characters that should contain a path to the XML file.  
# It MUST be in the host/path format.  For example: "directory.grandstream.com/engineering"
P341 =

#---------------------------------------
# XML Application
# GXP2020 and GXP2010
#---------------------------------------
# Server Path
P337 =

# Softkey Label
P352 =

# Offhook Auto Dial
P71 =

# DTMF Payload Type
P79 = 101

# Onhook Threshold. Default 800ms.
# <value=0>Hookflash OFF
# <value=2>200 ms
# <value=4>400 ms
# <value=6>600 ms
# <value=8>800 ms
# <value=10>1000 ms
# <value=12>1200 ms
# GXP280 Only
P245 = 8

# Syslog Server (name of the server, max length is 64 charactors)
P207 = %s

# Syslog Level (Default setting is NONE)
# 0 - NONE, 1 - DEBUG, 2 - INFO, 3 - WARNING, 4 - ERROR
P208 = 3

# NTP Server
P30 = %s

# Distinctive Ring Tone
# Use custom ring tone 1 if incoming caller ID is the following:
P105 =

# Use custom ring tone 2 if incoming caller ID is the following:
P106 =

# Use custom ring tone 3 if incoming caller ID is the following:
P107 =

# System Ring Tone
P345 = f1=440,f2=480,c=200/400;

# Disable Call Waiting. 0 - no, 1 - yes
P91 = 0

# Disable Call-Waiting Tone. 0 - no, 1 - yes
P186 = 0

# Disable Direct IP Call. 0 - no, 1 - yes
P1310 = 1

# Use Quick IP-call mode. 0 - no, 1 - yes
P184 = 0

# Disable Conference. 0 - no, 1 - yes
P1311 = 0

# Lock Keypad Update. 0 - no, 1 - yes
P88 = 1

# Enable Muliti-Purpose-Key sending DTMF, 0 - no, 1 - yes
# For GXP2000/2010/2020 only
P1339 = 0

# Disable DND Button. 0 - no, 1 - yes
P1340 = 0

# Disable Transfer. 0 - no, 1 - yes
P1341 = 0

# Disable Multicast Filter; 0 - no, 1 - yes
P1350 = 0

# Send Flash Event. 0 - no, 1 - yes
# GXP280 Only
P74 = 0

# Display CID instead of Name. 0 - no, 1 - yes
# GXP280 only
P1344 = 0

# Enable Constraint Mode. 0 - no, 1 - yes
P1357 = 0

# Auto-Attended Transfer. 0 - no, 1 - yes
# For GXP1200 only
P1376 = 0

# Semi-attended Transfer Mode. 0 - RFC5589, 1 - Send REFER with early dialog 
P1358 = 0

# Disable Headset Button. Default 0 - no, 1 - yes
P1375 = 0

# Display Language. 0 - English, 3 - Secondary Language, 2 - Chinese
P342 = 3

# language file postfix
P399 = french

''' % ('0000', 'tiare.sysnux.pf/phones/firmware', 'tiare.sysnux.pf/phones/config', 'tiare.sysnux.pf:8080/phonebook', 'tiare.sysnux.pf', 'tiare.sysnux.pf' )
         cfg.write(template)
         cfg.close()

         # Call gsutil to update and reboot phone
         ret = system('gsutil -o -r %s < %s' % (ip,cfg_name))
         log.debug('gsutil -r -> %d',ret)
         ret = system('gsutil -p %s -b %s' % ('0000',ip))
         log.debug('gsutil -b -> %d',ret)


      elif vendors[vendor]=='Polycom':
         # XXX
         return u"Trouvé téléphone Polycom"

 
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

      # Save phone info to database
      p = Phone()
      p.mac = kw['mac']
      if kw['number']: p.number = kw['number']
      if kw['dptm_id']!='-1': p.department_id = kw['dptm_id']
      if kw['user_id']!='-1': p.user_id = kw['user_id']
      DBSession.add(p)
      flash(u'Nouveau téléphone "%s" créé' % (kw['number']))
      redirect('/phones/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit phone form
      '''
      if not id: id=kw['phone_id']
      p = DBSession.query(Phone).get(id)
      v = {'phone_id': p.phone_id, 
            'number': p.number, 
            'dptm_id': p.department_id, 
            'user_id': p.user_id, 
            '_method': 'PUT'}
      tmpl_context.form = edit_phone_form
      ident = ''
      if p.number: ident = p.number
      elif p.mac: ident = p.mac
      return dict(title = u'Modification téléphone ' + ident, debug='', values=v)


   @validate(edit_phone_form, error_handler=edit)
   @expose()
   def put(self, phone_id, dptm_id, user_id, number):
      ''' Update phone in DB
      '''
      log.info('update %d' % phone_id)
      p = DBSession.query(Phone).get(phone_id)
      p.department_id = dptm_id
      p.user_id = user_id
      p.number = number
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


