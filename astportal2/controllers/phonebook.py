# -*- coding: utf-8 -*-
# Department CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, request
from tg.controllers import RestController

from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, TextField, CheckBox, HiddenField
from tw.forms.validators import NotEmpty, Int

from sqlalchemy import or_

from genshi import Markup

from astportal2.model import DBSession, Phonebook, User
from astportal2.lib.myjqgrid import MyJqGrid

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
         CheckBox('private', not_empty = False, default = True,
            label_text=u'Contact privé', help_text=u'Cochez si privé'),
         ]
   submit_text = u'Valider...'
   action = 'create'
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
         CheckBox('private', not_empty = False, default = True,
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

   html =  u'<a href="'+ str(pb.pb_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   html += u'&nbsp;&nbsp;&nbsp;'
   html += u'<a href="#" onclick="del(\''+ str(pb.pb_id) + \
         u'\',\'Suppression du contact ' + pb.firstname + ' ' + pb.lastname + u'\')" title="Supprimer">'
   html += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   private = u'Oui' if pb.private else u'Non'

   return [Markup(html), pb.firstname, pb.lastname, pb.company, 
         pb.phone1, pb.phone2, pb.phone3, private]


class Phonebook_ctrl(RestController):
   

   @expose(template="astportal2.templates.grid")
   def get_all(self):
      ''' List all departments
      '''
      grid = MyJqGrid( 
            id='grid', url='fetch', caption=u'Services',
            colNames = [u'Action', u'Prénom', u'Nom', u'Société', u'Téléphone 1',
               u'Téléphone 2', u'Téléphone 3', u'Privé'],
            colModel = [ 
               { 'width': 80, 'align': 'center', 'sortable': False, 'search': False },
               { 'name': 'firstname', 'width': 100 },
               { 'name': 'lastname', 'width': 100 },
               { 'name': 'company', 'width': 100 },
               { 'name': 'phone1', 'width': 100,  },
               { 'name': 'phone2', 'width': 100,  },
               { 'name': 'phone3', 'width': 100,  },
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
   def fetch(self, page=1, rows=10, sidx='lastname', sord='asc', _search='false',
          searchOper=None, searchField=None, searchString=None, **kw):
      ''' Function called on AJAX request made by Grid JS component
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

      book = DBSession.query(Phonebook)
      if  searchOper and searchField and searchString:
         log.debug('fetch query <%s> <%s> <%s>' % \
            (searchField, searchOper, searchString))
         try:
            field = eval('Department.' + searchField)
         except:
            field = None
            log.error('eval: Department.' + searchField)
         if field and searchOper=='eq': 
            dptms = dptms.filter(field==searchString)
         elif field and searchOper=='ne':
            dptms = dptms.filter(field!=searchString)
         elif field and searchOper=='le':
            dptms = dptms.filter(field<=searchString)
         elif field and searchOper=='lt':
            dptms = dptms.filter(field<searchString)
         elif field and searchOper=='ge':
            dptms = dptms.filter(field>=searchString)
         elif field and searchOper=='gt':
            dptms = dptms.filter(field>searchString)
         elif field and searchOper=='bw':
            dptms = dptms.filter(field.ilike(searchString + '%'))
         elif field and searchOper=='bn':
            dptms = dptms.filter(~field.ilike(searchString + '%'))
         elif field and searchOper=='ew':
            dptms = dptms.filter(field.ilike('%' + searchString))
         elif field and searchOper=='en':
            dptms = dptms.filter(~field.ilike('%' + searchString))
         elif field and searchOper=='cn':
            dptms = dptms.filter(field.ilike('%' + searchString + '%'))
         elif field and searchOper=='nc':
            dptms = dptms.filter(~field.ilike('%' + searchString + '%'))
         elif field and searchOper=='in':
            dptms = dptms.filter(field.in_(str(searchString.split(' '))))
         elif field and searchOper=='ni':
            dptms = dptms.filter(~field.in_(str(searchString.split(' '))))

      total = book.count()/rows + 1
      column = getattr(Phonebook, sidx)
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
   def create(self, firstname, lastname, company, phone1, phone2, phone3, private):
      ''' Add new department to DB
      '''
      d = Phonebook()
      d.firstname = firstname
      d.lastname = lastname
      d.company = company
      d.phone1 = phone1
      d.phone2 = phone2
      d.phone3 = phone3
      d.private = private
      d.user_id = request.identity['user'].user_id
      DBSession.add(d)
      flash(u'Nouveau contact "%s %s" créé' % (firstname, lastname))
      redirect('/phonebook/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit phonebook form
      '''
      if not id: id = kw['dptm_id']
      pb = DBSession.query(Phonebook).get(id)
      v = {'pb_id': pb.pb_id, 'firstname': pb.firstname, 
            'lastname': pb.lastname, 'phone1': pb.phone1,
            'phone2': pb.phone2, 'phone3': pb.phone3,
            'company': pb.company, 'private': pb.private,
            '_method': 'PUT'}
      tmpl_context.form = edit_contact_form
      return dict(title = u'Modification contact ', debug='', values=v)


   @validate(edit_contact_form, error_handler=edit)
   @expose()
   def put(self, pb_id, firstname, lastname, company, phone1, phone2,
         phone3, private):
      ''' Update contact in DB
      '''
      log.info('update %d' % pb_id)
      pb = DBSession.query(phonebook).get(pb_id)
      pb.firstname = firstname
      flash(u'Contact modifié')
      redirect('/phonebook/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete contact from DB
      '''
      log.info('delete ' + kw['_id'])
      DBSession.delete(DBSession.query(Phonebook).get(kw['_id']))
      flash(u'Contact supprimé', 'notice')
      redirect('/phonebook/')


   @expose('XML') # format='xml; encoding="iso-8859-1"')
   def gs_phonebook_xml(self, number=None):
      ''' Export phonebook to Grandstream XML phonebook format
      '''
      list = DBSession.query(Phonebook).filter(\
            or_(Phonebook.phone1!=None, 
               Phonebook.phone2!=None,
               Phonebook.phone3!=None))
      xml = '<?xml version="1.0" encoding="iso-8859-1"?>\n<AddressBook>\n'
      for e in list:
         xml += '''<Contact>
<LastName>%s %s</LastName>
  <Phone>
   <phonenumber>%s</phonenumber>
   <accountindex>0</accountindex>
  </Phone>
</Contact>''' % (e.firstname, e.lastname, e.phone1)

      # Encoding to numeric entities is not (currently?) supported on Grandstream phones
      #  => can't use xxx.encode("ascii", "xmlcharrefreplace")

      xml += '</AddressBook>\n'
      return xml

