# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context, response
from astportal2.model import DBSession, CDR, Department, Phone, User
from tg.decorators import allow_only
from tg.controllers import CUSTOM_CONTENT_TYPE
from repoze.what import predicates
#from pylons import tmpl_context
#from pylons import request
from sqlalchemy import func

import logging
log = logging.getLogger("astportal.controllers.cdr")

from tw.api import WidgetsList
from tw.forms import TableForm, HiddenField, Label, CalendarDatePicker, SingleSelectField, TextField, TextArea, MultipleSelectField
from tw.forms.datagrid import DataGrid, Column
from tw.jquery import FlexiGrid

import datetime

class Billing_form(TableForm):
   '''
   '''

   dptms = [(d.dptm_id, d.comment) 
      for d in DBSession.query(Department).order_by(Department.name).all()]
   dptms.insert( 0, ('ALL',u'* - Tous les services') )
   m = [ u'Janvier', u'Février', u'Mars', u'Avril', u'Mai', u'Juin', 
      u'Juillet', u'Août', u'Septembre', u'Octobre', u'Novembre', u'Décembre' ]
   month = [ ('', u' - - - - - - ') ]
   today = datetime.datetime.now()
   for i in range(0,12):
      j = today.month-i-2
      if j<0:
         y = today.year-1
         j += 12
      else:
         y = today.year
      month.append( ( '%04d%02d01' % (y,j+1), m[j] + ' ' + str(y)) )

   interval = '30 min'
   name = 'search_form'
   fields = [
      Label( text = u'Sélectionnez un ou plusieurs critères'),
      SingleSelectField(
         name = 'month',
         label_text = u'Mois',
         options = month),
      CalendarDatePicker(
         id = 'begin',
         label_text = u'Date début',
         date_format =  '%d/%m/%Y',
         calendar_lang = 'fr',
         not_empty = False,
         picker_shows_time = False ),
      CalendarDatePicker(
         id = 'end',
         label_text = u'Date fin',
         date_format =  '%d/%m/%Y',
         calendar_lang = 'fr',
         not_empty = False,
         picker_shows_time = False ),
      SingleSelectField(
         name = 'report_type',
         label_text = u'Type de rapport',
         options = [('group',u'Récapitulatif'), ('detail', u'Détail')]),
      SingleSelectField(
         name = 'department',
         label_text = u'Service',
         options = dptms),
      MultipleSelectField(
         name = 'phones',
         label_text = u'Téléphones',
         options = [(p.number, p.number + ' ' + p.user.display_name) 
            for p in DBSession.query(Phone)]),
   ]
   submit_text = u'Valider...'
   action = 'result'
   hover_help = True
new_billing_form = Billing_form('new_billing_form')



def f_bill(billsec):
   '''Formatted billing
   '''
   h = billsec/3600
   s = billsec-3600*h
   m = s/60
   s = s%60
   return '%d:%02d:%02d' % (h, m, s)


def user(dict,n):
   '''Number => user
   '''
   if dict.has_key(n[-4:]):
      return dict[n[-4:]][0]
   else:
      return ''


def dptm(dict,n):
   '''Number => department
   '''
   if dict.has_key(n[-4:]):
      return dict[n[-4:]][1]
   else:
      return ''


class Billing_ctrl:
   '''Billing controller
   '''

   #allow_only = predicates.not_anonymous('NOT ANONYMOUS')
   paginate_limit = 25
   filtered_cdrs = None
   phones_dict= None

   @expose(template="astportal2.templates.form_new")
   def index(self):
      '''Formulaire facturation
      '''
      tmpl_context.form = new_billing_form
      return dict( title=u'Facturation', debug='', values={'begin': None, 'end': None})

   @expose(template="astportal2.templates.flexigrid")
   def result(self, month=None, end=None, begin=None, report_type='group', 
         department='ALL', phones=None):

#      if not predicates.in_group('admin'):
#         flash(u'Accès interdit')
#         redirect('/')

      filter = []
      if report_type=='detail':
         cdrs = DBSession.query( CDR.calldate, CDR.src, CDR.dst, CDR.billsec, CDR.ht, CDR.ttc)
      else: # report_type=='group':
         cdrs = DBSession.query( CDR.src,
               func.sum(CDR.billsec).label('billsec'),
               func.sum(CDR.ht).label('ht'),
               func.sum(CDR.ttc).label('ttc'))

      # Outgoing calls go through Dahdi/g0
      cdrs = cdrs.filter("lastdata ILIKE 'Dahdi/g0/%'")
      cdrs = cdrs.filter(CDR.billsec>0)

      # month is prioritary on begin / end
      if month:
         filter.append(u'month='+str(month))
         cdrs = cdrs.filter("'%s'<=calldate::date" % month)
         cdrs = cdrs.filter("calldate::date<('%s'::date + interval '1 month')" % month)
      else:
         if begin:
            filter.append(u'begin='+begin)
            cdrs = cdrs.filter("'%s%s%s'<=calldate::date" % (begin[6:10], begin[3:5], begin[0:2]))
         if end:
            filter.append(u'end='+end)
            cdrs = cdrs.filter("calldate::date<='%s%s%s'" % (end[6:10], end[3:5], end[0:2]))

      # department is prioritary on phones
      if department!='ALL':
         filter.append(u'department='+str(department))
         phones = DBSession.query(Phone.number).filter(Phone.department_id==department).all()
         cdrs = cdrs.filter(CDR.src.in_(['47'+p.number for p in phones]))
      else:
         if phones:
            if type(phones)!=type([]):
               phones = ['47'+phones]
            else:
               phones = ['47'+p for p in phones]
            filter.append(u'phones='+', '.join(phones))
            cdrs = cdrs.filter(CDR.src.in_(phones))

      grid = FlexiGrid( id='flexi', fetchURL='fetch', title=None,
            sortname='src', sortorder='asc',
            colModel = [
               { 'display': u'Source', 'name': 'src', 'width': 80 },
               { 'display': u'Nom', 'name': '', 'width': 120 },
               { 'display': u'Service', 'width': 160 },
               { 'display': u'Durée', 'width': 60, 'align': 'right' },
               { 'display': u'CFP HT', 'width': 60, 'align': 'right' },
               { 'display': u'CFP TTC', 'width': 60, 'align': 'right' },
               ],
            usepager=True,
            useRp=True,
            rp=10,
            resizable=False,
            )

      if len(filter):
         if len(filter)>1: m = u'Critères: '
         else: m = u'Critère: '
         flash( m + ', et '.join(filter) + '.')

      if report_type!='detail':
         cdrs = cdrs.group_by(CDR.src)

      global filtered_cdrs
      filtered_cdrs = cdrs

      # phones['number'] = ('user_display_name','department_comment')
      global phones_dict
      phones_dict= dict([(p.number, (p.user.display_name,p.department.comment))
         for p in DBSession.query(Phone)])

      tmpl_context.grid = grid
      
      return dict( title=u'Facturation', debug='', form='')


   @expose('json')
   def fetch(self, page=1, rp=25, sortname='src', sortorder='desc', qtype=None, query=None):

      try:
         page = int(page)
         offset = (page-1) * int(rp)
      except:
         offset = 0
         page = 1
         rp = 25

      global phones_dict
      global filtered_cdrs
      cdrs = filtered_cdrs
      total = cdrs.count()
      column = getattr(CDR, sortname)
      cdrs = cdrs.order_by(getattr(column,sortorder)()).offset(offset).limit(rp)
      rows = [
            {
               'id'  : cdr.src,
               'cell': [
                  cdr.src,
                  user(phones_dict,cdr.src),
                  dptm(phones_dict,cdr.src),
                  f_bill(cdr.billsec),
                  cdr.ht,
                  cdr.ttc,
                  ]
               } for cdr in cdrs
            ]

      return dict(page=page, total=total, rows=rows)


   @expose(content_type=CUSTOM_CONTENT_TYPE)
   def csv(self):

      today = datetime.datetime.today()
      filename = 'telephone-' + today.strftime("%Y%m%d") + '.csv'
      import StringIO
      import csv
      csvdata = StringIO.StringIO()
      writer = csv.writer(csvdata)
      writer.writerow(['Service', 'Nom', 'Numéro', 'Durée', 'CFP HT', 'CFP TTC'])
      writer.writerow(['XXX', 'Xxx xxxx', '123654', '12:34', 123, 456])
      writer.writerow(['XYZ', 'Zorro xxxx', '546321', '1:34', 12, 45])

      rh = response.headers
      rh['Content-Type'] = 'text/csv; charset=utf-8'
      rh['Content-disposition'] = 'attachment; filename="%s"' % filename
      rh['Pragma'] = 'public' # for IE
      rh['Cache-control'] = 'max-age=0' #for IE

      return csvdata.getvalue()

