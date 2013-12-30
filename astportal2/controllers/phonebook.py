# -*- coding: utf-8 -*-
# Department CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request, response, session
from tg.controllers import RestController
from tgext.menu import sidebar

from repoze.what.predicates import in_group, not_anonymous

from tw.api import js_callback
from tw.forms import TableForm, TextField, CheckBox, HiddenField
from tw.forms.validators import NotEmpty, Int, Bool

from sqlalchemy import or_, func

from genshi import Markup

from astportal2.model import DBSession, Phonebook, User, View_phonebook
from astportal2.lib.app_globals import Globals
from astportal2.lib.myjqgrid import MyJqGrid

from tg import config
default_company = config.get('company')
default_cid = config.get('default_cid')

import logging
log = logging.getLogger(__name__)

class New_contact_form(TableForm):
   ''' New contact form
   '''
   fields = [
         TextField('firstname', validator=NotEmpty,
            label_text=u'Prénom', help_text=u'Entrez le prénom'),
         TextField('lastname', validator=NotEmpty,
            label_text=u'Nom', help_text=u'Entrez le nom de famille'),
         TextField('company', not_empty = False,
            label_text=u'Société', help_text=u'Entrez la société'),
         TextField('phone1', validator=NotEmpty,
            label_text=u'Téléphone 1', help_text=u'Premier numéro de téléphone'),
         TextField('phone2', not_empty = False,
            label_text=u'Téléphone 2', help_text=u'Deuxième numéro de téléphone'),
         TextField('phone3', not_empty = False,
            label_text=u'Téléphone 3', help_text=u'Troisième numéro de téléphone'),
         TextField('email', not_empty = False,
            label_text=u'@ email', help_text=u'Adresse email'),
         CheckBox('private', not_empty = False, default = True,
            label_text=u'Contact privé', help_text=u'Cochez si privé'),
         ]
   submit_text = u'Valider...'
   action = '/phonebook/create'
   hover_help = True
new_contact_form = New_contact_form('new_contact_form')


class Edit_contact_form(TableForm):
   ''' Edit department form
   '''
   fields = [
         TextField('firstname', validator=NotEmpty,
            label_text=u'Prénom', help_text=u'Entrez le prénom'),
         TextField('lastname', validator=NotEmpty,
            label_text=u'Nom', help_text=u'Entrez le nom de famille'),
         TextField('company', not_empty = False,
            label_text=u'Société', help_text=u'Entrez la société'),
         TextField('phone1', validator=NotEmpty,
            label_text=u'Téléphone 1', help_text=u'Premier numéro de téléphone'),
         TextField('phone2', not_empty = False,
            label_text=u'Téléphone 2', help_text=u'Deuxième numéro de téléphone'),
         TextField('phone3', not_empty = False,
            label_text=u'Téléphone 3', help_text=u'Troisième numéro de téléphone'),
         TextField('email', not_empty = False,
            label_text=u'@ email', help_text=u'Adresse email'),
         CheckBox('private', default = True, validator=Bool,
            label_text=u'Contact privé', help_text=u'Cochez si privé'),
         HiddenField('_method', validator=None), # Needed by RestController
         HiddenField('pb_id', validator=Int),
         ]
   submit_text = u'Valider...'
   action = '/phonebook/'
   hover_help = True
edit_contact_form = Edit_contact_form('edit_contact_form')


def row(pb):
   '''Displays a formatted row of the contacts
   Parameter: phonebook object
   '''

   if (int(pb.pb_id)>0):
      action =  u'<a href="'+ str(pb.pb_id) + u'/edit" title="Modifier">'
      action += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
      action += u'&nbsp;&nbsp;&nbsp;'
      action += u'<a href="#" onclick="del(\'%d\',\'Suppression du contact %s %s\')" title="Supprimer">' % \
         (pb.pb_id, pb.firstname.replace("'","\\'"), pb.lastname.replace("'","\\'"))
      action += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'
      company = pb.company
      private = u'Oui' if pb.private else u'Non'
   else:
      action = ''
      company = default_company
      private = ''

#   uphones = request.identity['user'].phone)
   uphones = DBSession.query(User).get(request.identity['user'].user_id).phone
   phones = []
   if pb.phone1:
      if len(uphones)<1:
         phones.append(pb.phone1)
      else:
         phones.append(u'''<a href="#" onclick="originate('%s')" title="Appeler">%s</a>''' % (pb.phone1, pb.phone1))

   if pb.phone2:
      if len(uphones)<1:
         phones.append(pb.phone2)
      else:
         phones.append(u'''<a href="#" onclick="originate('%s')" title="Appeler">%s</a>''' % (pb.phone2, pb.phone2))

   if pb.phone3:
      if len(uphones)<1:
         phones.append(pb.phone3)
      else:
         phones.append(u'''<a href="#" onclick="originate('%s')" title="Appeler">%s</a>''' % (pb.phone3, pb.phone3))

   email = u'<a href="mailto:%s">%s</a>' % (pb.email, pb.email) if pb.email is not None\
      else ''

   return [Markup(action), pb.firstname, pb.lastname, company, 
         Markup(u', '.join(phones)), Markup(email), private]


class Phonebook_ctrl(RestController):
   
#   allow_only = not_anonymous( msg=u'Veuillez vous connecter pour continuer' )

   @sidebar(u'Annuaire',
         sortorder = 1,
         icon = '/images/phonebook-small.jpg')
   @expose(template="astportal2.templates.grid_phonebook")
   def get_all(self):
      ''' List all
      '''
      grid = MyJqGrid( 
            id='grid', url='fetch', caption=u'Services',
            colNames = [u'Action', u'Prénom', u'Nom', u'Société', u'Téléphone(s)',
               u'@ email', u'Privé'],
            colModel = [ 
               { 'width': 80, 'align': 'center', 'sortable': False, 'search': False },
               { 'name': 'firstname', 'width': 80 },
               { 'name': 'lastname', 'width': 80 },
               { 'name': 'company', 'width': 120 },
               { 'name': 'phones', 'width': 160,  },
               { 'name': 'email', 'width': 160,  },
               { 'name': 'private', 'width': 40,  },
            ],
            sortname = 'lastname',
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': True, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Annuaire téléphonique', debug='')


   @expose('json')
   def fetch(self, page, rows, sidx='lastname', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by Grid JS component
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

      book = DBSession.query(View_phonebook)
      book = book.filter(or_(View_phonebook.private==False, 
         View_phonebook.user_id==request.identity['user'].user_id))
      if  searchOper and searchField and searchString:
         searchString = searchString.lower()
         log.debug('fetch query <%s> <%s> <%s>' % \
            (searchField, searchOper, searchString))
         try:
            field = eval('View_phonebook.' + searchField)
         except:
            field = None
            log.error('eval: View_phonebook.' + searchField)
         if field and searchOper=='eq': 
            book = book.filter(func.lower(field)==searchString)
         elif field and searchOper=='ne':
            book = book.filter(field!=searchString)
         elif field and searchOper=='le':
            book = book.filter(field<=searchString)
         elif field and searchOper=='lt':
            book = book.filter(field<searchString)
         elif field and searchOper=='ge':
            book = book.filter(field>=searchString)
         elif field and searchOper=='gt':
            book = book.filter(field>searchString)
         elif field and searchOper=='bw':
            book = book.filter(field.ilike(searchString + '%'))
         elif field and searchOper=='bn':
            book = book.filter(~field.ilike(searchString + '%'))
         elif field and searchOper=='ew':
            book = book.filter(field.ilike('%' + searchString))
         elif field and searchOper=='en':
            book = book.filter(~field.ilike('%' + searchString))
         elif field and searchOper=='cn':
            book = book.filter(field.ilike('%' + searchString + '%'))
         elif field and searchOper=='nc':
            book = book.filter(~field.ilike('%' + searchString + '%'))
         elif field and searchOper=='in':
            book = book.filter(field.in_(str(searchString.split(' '))))
         elif field and searchOper=='ni':
            book = book.filter(~field.in_(str(searchString.split(' '))))
         log.debug(book)

      total = book.count()/rows + 1
      column = getattr(View_phonebook, sidx)
      book = book.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      data = [ { 'id'  : b.pb_id, 'cell': row(b) } for b in book ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new contact form
      '''
      tmpl_context.form = new_contact_form
      return dict(title = u'Nouveau contact', debug='', values='')
      
   @validate(new_contact_form, error_handler=new)
   @expose()
   def create(self, firstname, lastname, company, phone1, phone2, 
         phone3, email, private=None):
      ''' Add new phonebook entry to DB
      '''
      d = Phonebook()
      d.firstname = firstname
      d.lastname = lastname
      d.company = company
      d.phone1 = phone1
      d.phone2 = phone2
      d.phone3 = phone3
      d.email = email
      d.private = private
      d.user_id = request.identity['user'].user_id
      DBSession.add(d)
      flash(u'Nouveau contact "%s %s" créé' % (firstname, lastname))
      redirect('/phonebook/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit phonebook form
      '''
      if not id: id = kw['pb_id']
      pb = DBSession.query(Phonebook).get(id)
      v = {'pb_id': pb.pb_id, 'firstname': pb.firstname, 
            'lastname': pb.lastname, 'phone1': pb.phone1,
            'phone2': pb.phone2, 'phone3': pb.phone3,
            'company': pb.company, 'private': pb.private,
            'email': pb.email, '_method': 'PUT'}
      tmpl_context.form = edit_contact_form
      return dict(title = u'Modification contact ', debug='', values=v)


   @validate(edit_contact_form, error_handler=edit)
   @expose()
   def put(self, pb_id, firstname, lastname, company, phone1, phone2,
         phone3, email, private=False):
      ''' Update contact in DB
      '''
      log.info('update %d' % pb_id)
      pb = DBSession.query(Phonebook).get(pb_id)
      pb.firstname = firstname
      pb.lastname = lastname
      pb.company = company
      pb.phone1 = phone1
      pb.phone2 = phone2
      pb.phone3 = phone3
      pb.email = email
      pb.private = private
      flash(u'Contact modifié')
      redirect('/phonebook/%d/edit' % pb_id)


   @expose()
   def delete(self, id, **kw):
      ''' Delete contact from DB
      '''
      log.info('delete ' + kw['_id'])
      DBSession.delete(DBSession.query(Phonebook).get(kw['_id']))
      flash(u'Contact supprimé', 'notice')
      redirect('/phonebook/')


   @expose(content_type='text/xml; charset=utf-8')
   def gs_phonebook_xml(self, user=None):
      ''' Export phonebook to Grandstream XML phonebook format
      '''

      log.debug(u'Grandstream phonebook from=<%s> by <%s>' % (\
         request.environ['REMOTE_ADDR'], request.environ['HTTP_USER_AGENT']))
      log.debug(u'Grandstream phonebook user=<%s>' % user)

      xml = '<?xml version="1.0" encoding="utf-8"?>\n<AddressBook>\n'

      # Fist, look for entries in phonebook...
      list = DBSession.query(Phonebook)
      list = list.filter( or_(Phonebook.phone1!=None,
               Phonebook.phone2!=None,
               Phonebook.phone3!=None) )
      list = list.order_by(Phonebook.lastname, Phonebook.firstname)

      for e in list:
         if e.phone1:
            xml += '''<Contact>
<LastName>%s</LastName>
<FirstName>%s</FirstName>
  <Phone>
   <phonenumber>%s</phonenumber>
   <accountindex>0</accountindex>
  </Phone>
</Contact>''' % (e.lastname, e.firstname, e.phone1)

         if e.phone2:
            xml += '''<Contact>
<LastName>%s</LastName>
<FirstName>%s</FirstName>
  <Phone>
   <phonenumber>%s</phonenumber>
   <accountindex>0</accountindex>
  </Phone>
</Contact>''' % (e.lastname, e.firstname, e.phone2)

         if e.phone3:
            xml += '''<Contact>
<LastName>%s</LastName>
<FirstName>%s</FirstName>
  <Phone>
   <phonenumber>%s</phonenumber>
   <accountindex>0</accountindex>
  </Phone>
</Contact>''' % (e.lastname, e.firstname, e.phone3)


      # ...then add users
      list = DBSession.query(User).filter(User.phone!=None)
      list = list.order_by(User.display_name)

      for e in list:
         xml += '''<Contact>
<LastName>%s</LastName>
<FirstName>%s</FirstName>
  <Phone>
   <phonenumber>%s</phonenumber>
   <accountindex>0</accountindex>
  </Phone>
</Contact>''' % (e.lastname, e.firstname, e.phone[0].exten)

      xml += '</AddressBook>\n'

      return xml.encode('utf-8', 'replace')


   @expose('json')
   def echo(self):
#     uphones = request.identity['user'].phone)
      uphones = DBSession.query(User).get(request.identity['user'].user_id).phone
      if len(uphones)<1:
         return dict(status=2)
      chan = uphones[0].sip_id
      log.debug('Echo test for extension ' + chan)
      res = Globals.manager.originate(
            'SIP/' + chan.encode('iso-8859-1'), # Channel
            '*99', # Extension
            context=chan.encode('iso-8859-1'),
            priority='1',
            caller_id=default_cid
            )
      status = 0 if res=='Success' else 1
      return dict(status=status)


   @expose('json')
   def originate(self, exten):
      '''
      '''
#     uphones = request.identity['user'].phone)
      uphones = DBSession.query(User).get(request.identity['user'].user_id).phone
      if len(uphones)<1:
         return dict(status=2)
      chan = uphones[0].sip_id
      log.debug('Call from extension %s to %s' % (chan, exten))
      res = Globals.manager.originate(
            'SIP/' + chan.encode('iso-8859-1'), # Channel
            exten.encode('iso-8859-1'), # Extension
            context=chan.encode('iso-8859-1'),
            priority='1',
            caller_id=default_cid
            )
      log.debug(res)
      status = 0 if res=='Success' else 1
      return dict(status=status)


   @expose('json')
   def search(self, **kw):
      '''
      '''
      log.debug('kw=%s' % kw)
      auto = None
      if 'q' in kw and len(kw['q'])>3:
         from sqlalchemy import or_
         data = [u'%s %s (%s, %s, %s)' % (pb.firstname, pb .lastname, pb.phone1, pb.phone2, pb.phone3) \
            for pb in DBSession.query(Phonebook)]
      else:
         data=[]
      log.debug('data=%s' % data)
      return dict(data=['azerty', 'qwerty', 'toto', 'titi'])
