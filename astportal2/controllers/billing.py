# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context, request, response, validate
from astportal2.model import DBSession, CDR, Department, Phone, User
from tg.decorators import allow_only
from repoze.what.predicates import not_anonymous, in_group, in_any_group


from tw.api import WidgetsList
from tw.forms import TableForm, HiddenField, Label, CalendarDatePicker, SingleSelectField, TextField, TextArea, MultipleSelectField, Spacer
from tw.forms.validators import DateConverter

from astportal2.lib.myjqgrid import MyJqGrid

from sqlalchemy import func #, sql, types
import datetime

import logging
log = logging.getLogger(__name__)

def check_access(cdrs):
   '''Check access rights / group: admin=full access, boss=users from same department, user.
   Returns SA Query object for selected CDRs
   '''

   if in_group('admin'):
      return cdrs

   elif in_group('chefs'):
      # Find list of phones from the user's list of phones
      # user_phones -> departments -> phones
      phones = []
      for d in [d.department for d in request.identity['user'].phone]:
         for p in d.phones:
            phones.append(p)
      src = [p.number for p in phones]
      dst = [p.number for p in phones]
      cdrs = cdrs.filter( (CDR.src.in_(src)) | (CDR.dst.in_(dst)) )

   elif in_group('utilisateurs'):
      src = [p.number for p in request.identity['user'].phone]
      dst = [p.number for p in request.identity['user'].phone]
      cdrs = cdrs.filter( (CDR.src.in_(src)) | (CDR.dst.in_(dst)) )

   else:
      flash(u'Accès interdit')
      redirect('/')

   return cdrs


def phone_user_display_name(p):
   if p.user:
      return p.user.display_name
   else:
      return ''


class CSV_form(TableForm):
   name = 'csv_form'
   fields = [
         HiddenField('report_type'),
         HiddenField('message'),
         ]
   submit_text = u'Export CSV...'
   action = 'csv'
new_csv_form = CSV_form('new_csv_form')


class Billing_form(TableForm):
   '''Billing form :)
   '''

   dptms = [(d.dptm_id, d.comment) 
      for d in DBSession.query(Department).order_by(Department.name).all()]
   dptms.insert( 0, ('ALL',u'* - Tous les services') )
   m = [ u'Janvier', u'Février', u'Mars', u'Avril', u'Mai', u'Juin', 
      u'Juillet', u'Août', u'Septembre', u'Octobre', u'Novembre', u'Décembre' ]
   month = [ ('', u' - - - - - - ') ]
   today = datetime.datetime.now()
   for i in range(0,18):
      j = today.month-i-1
      if j<0:
         y = today.year-1
         j += 12
      else:
         y = today.year
      month.append( ( '%04d%02d01' % (y,j+1), m[j] + ' ' + str(y)) )

   interval = '30 min'
   name = 'search_form'
   fields = [
      Label( text = u'1. Choisissez un mois, ou des dates de début / fin'),
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
         validator = DateConverter(month_style='dd/mm/yyyy'),
         picker_shows_time = False ),
      CalendarDatePicker(
         id = 'end',
         label_text = u'Date fin',
         date_format =  '%d/%m/%Y',
         calendar_lang = 'fr',
         not_empty = False,
         validator = DateConverter(month_style='dd/mm/yyyy'),
         picker_shows_time = False ),
      Spacer(),
      Label( text = u'2. Choisissez le type de rapport, récapitulatif ou détail par poste'),
      SingleSelectField(
         name = 'report_type',
         label_text = u'Type',
         options = [('group',u'Récapitulatif'), ('detail', u'Détail')]),
      Spacer(),
      Label( text = u'3. Choisissez un service, ou un ou plusieurs téléphones'),
      SingleSelectField(
         name = 'department',
         label_text = u'Service',
         options = dptms),
      MultipleSelectField(
         help_text = u'Maintenez la touche "Ctrl" appuyée pour sélectionner plusieurs téléphones',
         name = 'phones',
         label_text = u'Téléphones',
         options = [(p.number, p.number + ' ' + phone_user_display_name(p)) 
            for p in DBSession.query(Phone).filter(Phone.number!=None).order_by(Phone.number)]),
      Spacer(),
      ]

   submit_text = u'Valider...'
   action = 'result'
   hover_help = True
new_billing_form = Billing_form('new_billing_form')


def f_bill(billsec):
   '''Formatted billing time
   '''
   h = billsec/3600
   s = billsec-3600*h
   m = s/60
   s = s%60
   return '%d:%02d:%02d' % (h, m, s)


from math import ceil
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
def f_cost(x):
   ''' Formatted cost
   '''
   if not x: x=0
   return locale.format('%d', ceil(x/100), grouping=True)


def user(dict,n):
   '''Number => user
   '''
   if dict.has_key(n):
      return dict[n][0]
   else:
      return u'Pas affecté'


def dptm(dict,n):
   '''Number => department
   '''
   if dict.has_key(n):
      return dict[n][1]
   else:
      return u'Pas affecté'

filtered_cdrs = None
phones_dict= None
def fetch(report_type, page, rows):
      if not in_any_group('admin', 'chefs', 'utilisateurs'):
         flash(u'Accès interdit')
         redirect('/')

      try:
         page = int(page)
         rows = int(rows)
         offset = (page-1) * rows
      except:
         offset = 0
         page = 1
         rows = 25

      global phones_dict
      global filtered_cdrs
      cdrs = filtered_cdrs
      log.debug('fetch ' + str(filtered_cdrs))
      total = cdrs.count() / rows + 1
      cdrs = cdrs.order_by(CDR.src)
      if report_type=='detail':
         cdrs = cdrs.order_by(CDR.calldate.desc())
      cdrs = cdrs.offset(offset).limit(rows)

      old_u = old_d = ''
      sec_tot = ht_tot = ttc_tot = 0
      data = []
      for cdr in cdrs.all():

         d = dptm(phones_dict,cdr.src)
         u = user(phones_dict,cdr.src)
         if u==old_u: u=''
         else: old_u=u
         log.debug(u'%s : department %s, user %s' % (cdr.src, d, u))

         if d!=old_d:
            # Next departement
            if old_d:
               # Add sub total per department
               data.append({
                  'id':  'total_' + d,
                  'cell': [None, u'TOTAL SERVICE', '',
                     f_bill(sec_tot), f_cost(ht_tot), f_cost(ttc_tot) ]})
               if report_type=='detail':
                  data[-1]['cell'].insert(3, None)
            old_d=d
            sec_tot = ht_tot = ttc_tot = 0
            # Department header
            data.append({
               'id':  d,
               'cell': [old_d, None, None, None, None, None]
               })
            if report_type=='detail':
               data[-1]['cell'].insert(6, None)

         sec_tot += cdr.billsec
         ht_tot += cdr.ht or 0
         ttc_tot += cdr.ttc or 0

         data.append({
               'id':  cdr.src,
               'cell': [None,
               u, # user(phones_dict,cdr.src),
               cdr.src,
               f_bill(cdr.billsec),
               f_cost(cdr.ht),
               f_cost(cdr.ttc) ]
               })
         if report_type=='detail':
            data[-1]['cell'].insert(3, cdr.dst) 
            # Hide destination for privacy cdr.dst[:3] + 'xxx')

      data.append({
         'id':  'total_' + old_d,
         'cell': [None, u'TOTAL', '',
            f_bill(sec_tot), f_cost(ht_tot), f_cost(ttc_tot) ]})
      if report_type=='detail':
         data[-1]['cell'].insert(3, None)
      return dict(page=page, total=total, rows=data)


class Billing_ctrl:
   '''Billing controller
   '''

   allow_only = not_anonymous('NOT ANONYMOUS')
   paginate_limit = 25


   @expose(template="astportal2.templates.form_new")
   def index(self, **kw):
      '''Formulaire facturation
      '''
      tmpl_context.form = new_billing_form

      return dict( title=u'Facturation', debug='', values={'begin': None, 'end': None})


   @validate(new_billing_form, error_handler=index)
   @expose(template="astportal2.templates.grid")
   def result(self, month=None, end=None, begin=None, report_type='group', 
         department='ALL', phones=None):


      filter = []
      if report_type=='detail':
         cdrs = DBSession.query(CDR.calldate, CDR.src, CDR.dst, 
               CDR.billsec, CDR.ht, CDR.ttc)
      else: # elif report_type=='group':
         # report_type 'group' is default
         cdrs = DBSession.query( CDR.src,
               func.sum(CDR.billsec).label('billsec'),
               func.sum(CDR.ht).label('ht'),
               func.sum(CDR.ttc).label('ttc'))

      cdrs = check_access(cdrs)

      # Outgoing calls go through:
#      OPT: dstchannel ~ E'Zap/(\\d|1\\d)-1'
#      Tikiphone: dstchannel LIKE 'SIP/gsm%' 
#      TelIAX: dstchannel LIKE 'IAX2/teliax%'
#      cdrs = cdrs.filter(''' (dstchannel ~ E'Zap/1?\\\\d-1' OR dstchannel LIKE 'SIP/gsm%' OR dstchannel LIKE 'IAX2/teliax%')''')
      cdrs = cdrs.filter(func.substr(CDR.dstchannel,0,8).in_( \
            ('DAHDI/4', 'DAHDI/i', 'IAX2/vo')))
      cdrs = cdrs.filter(CDR.billsec>0)

      # month is prioritary over begin / end
      if month:
         filter.append(u'mois='+str(month))
         cdrs = cdrs.filter("'%s'<=calldate::date" % month)
         cdrs = cdrs.filter("calldate::date<('%s'::date + interval '1 month')" % month)
      else:
         if begin:
            filter.append(u'début='+begin.strftime('%d/%m/%Y'))
            cdrs = cdrs.filter(CDR.calldate>=begin)
         if end:
            filter.append(u'fin='+end.strftime('%d/%m/%Y'))
            cdrs = cdrs.filter(CDR.calldate<=end)

      # department is prioritary over phones
      if department!='ALL':
         filter.append(u'service='+str(department))
         phones = DBSession.query(Phone.number).filter(Phone.department_id==department).all()
         cdrs = cdrs.filter(CDR.src.in_([p.number for p in phones]))
      elif phones:
            if type(phones)!=type([]):
               phones = [phones]
            else:
               phones = [p for p in phones]
            filter.append(u'phones='+', '.join(phones))
            cdrs = cdrs.filter(CDR.src.in_(phones))

      colNames = [u'Service', u'Nom', u'Appelant', u'Durée', u'CFP HT', u'CFP TTC']
      colModel = [
            { 'width': 200, 'sortable': False },
               { 'width': 200, 'sortable': False  },
               { 'name': 'src', 'width': 60, 'sortable': False  },
               { 'width': 60, 'align': 'right', 'sortable': False  },
               { 'width': 60, 'align': 'right', 'sortable': False  },
               { 'width': 60, 'align': 'right', 'sortable': False  },
            ]
      if report_type=='detail':
         fetchURL = 'fetch_detail'
         colNames.insert(3 , u'Appelé')
         colModel.insert(3 , { 'name': 'src', 'width': 60 })
      else:
         fetchURL = 'fetch_group'

      grid = MyJqGrid( id='grid', url=fetchURL, title=u'Facturation',
            sortname='src',
            colNames = colNames,
            colModel = colModel,
            report_type=report_type,
            out_of=u'sur'
            )

      msg = ''
      if len(filter):
         if len(filter)>1: msg = u'Critères: '
         else: msg = u'Critère: '
         msg += ', et '.join(filter) + '.'
         flash(msg)

      if report_type!='detail':
         cdrs = cdrs.group_by(CDR.src)

      global filtered_cdrs
      filtered_cdrs = cdrs

      global phones_dict
      phones_dict= dict([(p.number, (phone_user_display_name(p),
         p.department.comment)) 
         for p in DBSession.query(Phone)])

      tmpl_context.grid = grid
      tmpl_context.form = new_csv_form
      
      return dict( title=u'Facturation', debug='',
            values={'report_type': report_type, 'message': msg})


   @expose('json')
   def fetch_detail(self, page=1, rows=25, sidx='src', sord='asc', searchOper=None, 
         searchField=None, searchString=None, _search=None, nd=None):
      ''' Called by Grid JavaScript component
      '''
      return fetch('detail', page, rows)


   @expose('json')
   def fetch_group(self, page=1, rows=25, sidx='src', sord='asc', searchOper=None, 
         searchField=None, searchString=None, _search=None, nd=None):
      ''' Called by Grid JavaScript component
      '''
      return fetch('group', page, rows)


   @expose()
   def csv(self, report_type='group', message=None):

      if not in_any_group('admin', 'chefs', 'utilisateurs'):
         flash(u'Accès interdit')
         redirect('/')

      today = datetime.datetime.today()
      filename = 'telephone-' + today.strftime('%Y%m%d') + '.csv'
      import StringIO
      import csv
      csvdata = StringIO.StringIO()
      writer = csv.writer(csvdata)

      # Global header
      if report_type=='detail': rt = 'détaillé'
      else: rt = 'récapitulatif par poste'
      writer.writerow(['Consommation téléphonique'])
      writer.writerow(['Date', today.strftime('%d/%m/%Y')])
      writer.writerow(['Type de rapport', rt])
      if message: writer.writerow([unicode(message).encode('utf-8')])
      writer.writerow([])
      row = ['Service','Nom','Appelant','Durée','CFP HT','CFP TTC']
      if report_type=='detail':
         row.insert(3, 'Appelé')
      writer.writerow(row)

      # Add data lines
      for cdr in fetch(report_type, 1, 1000000)['rows']:
         cdr['cell'][0] = unicode(cdr['cell'][0]).encode('utf-8') \
               if cdr['cell'][0] else None
         cdr['cell'][1] = unicode(cdr['cell'][1]).encode('utf-8') \
               if cdr['cell'][1] else None
         writer.writerow(cdr['cell'])

      # Send response
      rh = response.headers
      rh['Content-Type'] = 'text/csv; charset=utf-8'
      rh['Content-disposition'] = 'attachment; filename="%s"' % filename
      rh['Pragma'] = 'public' # for IE
      rh['Cache-control'] = 'max-age=0' #for IE

      return csvdata.getvalue()

