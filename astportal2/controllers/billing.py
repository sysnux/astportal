# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context, request, response, validate, session, config
from tgext.menu import sidebar
from astportal2.model import DBSession, CDR, Department, Phone, User
from tg.decorators import allow_only
from repoze.what.predicates import not_anonymous, in_group, in_any_group


from tw.api import WidgetsList
from tw.forms import TableForm, HiddenField, Label, CalendarDatePicker, SingleSelectField, TextField, TextArea, MultipleSelectField, Spacer
from tw.forms.validators import DateConverter

from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.base import BaseController

from sqlalchemy import func #, sql, types
import datetime

import logging
log = logging.getLogger(__name__)

from math import ceil
import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
prefix_src = config.get('prefix.src')

def check_access(cdrs):
   '''Check access rights / group: admin=full access, boss=users from same department, user.
   Returns SA Query object for selected CDRs
   '''

   if in_any_group('admin', 'DG', 'COMPTA'):
      return cdrs

   elif in_group('CDS'):
      # Find list of phones from the user's list of phones
      # user_phones -> departments -> phones
      phones = []
      for d in [d.department for d in request.identity['user'].phone]:
         for p in d.phones:
            phones.append(p)
      src = [p.exten for p in phones]
      dst = [p.exten for p in phones]
      cdrs = cdrs.filter( (CDR.src.in_(src)) | (CDR.dst.in_(dst)) )
      log.info('CDS source <%s>, destination <%s>' % (src,dst))

   elif in_group('Utilisateurs'):
      src = [p.exten for p in request.identity['user'].phone]
      dst = [p.exten for p in request.identity['user'].phone]
      cdrs = cdrs.filter( (CDR.src.in_(src)) | (CDR.dst.in_(dst)) )

   else:
      flash(u'Accès interdit')
      redirect('/')

   return cdrs


def phone_user_display_name(p):
   return p.user.display_name if p.user else ''


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
      month.append( ( '01/%02d/%04d' % (j+1,y), m[j] + ' ' + str(y)) )

   name = 'search_form'
   fields = [
      Label( text = u'1. Choisissez un mois, ou des dates de début / fin'),
      SingleSelectField(
         name = 'month',
         label_text = u'Mois',
         not_empty = False,
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
         options = [(p.exten, p.exten + ' ' + phone_user_display_name(p)) 
            for p in DBSession.query(Phone).filter(Phone.exten!=None).order_by(Phone.exten)]),
      Spacer(),
      ]

   submit_text = u'Valider...'
   action = 'result'
   hover_help = True
new_billing_form = Billing_form('new_billing_form')


def f_bill(billsec):
   '''Formatted billing time
   '''
   if billsec is not None:
      h = billsec/3600 
      s = billsec-3600*h
      m = s/60
      s = s%60
   else:
      h = m = s = 0
   return '%d:%02d:%02d' % (h, m, s)


def f_cost(x):
   ''' Formatted cost
   '''
   if not x: x=0
   return locale.format('%d', ceil(x/100), grouping=True)


def user(dict,n):
   '''Number => user
   '''
   return dict[n][0] if dict.has_key(n) else u'Pas affecté'


def dptm(dict,n):
   '''Number => department
   '''
   return dict[n][1] if dict.has_key(n) else u'Pas affecté'

filtered_cdrs = None
phones_dict= None
def fetch(report_type, page, rows):
   ''' Fetch data, group by department, user
   Called (indirectly) by jqGrid
   Returns JSON
   '''
   if not in_any_group('admin', 'DG', 'Compta', 'Chefs', 'Utilisateurs'):
      flash(u'Accès interdit')
      redirect('/')

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

   global phones_dict
   global filtered_cdrs
   cdrs = filtered_cdrs
   log.debug('fetch ' + str(filtered_cdrs))
   total = cdrs.count() / rows + 1
   cdrs = cdrs.order_by(CDR.department, CDR.user)
   if report_type=='detail':
      cdrs = cdrs.order_by(CDR.calldate.desc())
   cdrs = cdrs.offset(offset).limit(rows)

   old_u = old_d = ''
   sec_tot = ht_tot = ttc_tot = 0
   data = []
   d_id2name = dict([(d.dptm_id, u'%s (%s)' % (d.name, d.comment)) \
         for d in DBSession.query(Department)])
   u_id2name = dict([(u.user_id, u'%s (%s)' % (u.display_name, 
      u.phone[0].exten if u.phone else '')) \
         for u in DBSession.query(User)])

   for cdr in cdrs.all():
      d = d_id2name.get(cdr.department, u'Inconnu')
      u = u_id2name.get(cdr.user, u'Inconnu')
      if u==old_u: u=''
      else: old_u=u

      if d!=old_d:
         # Next departement
         if old_d:
            # Add sub total per department
            data.append({
               'id':  'total_%s' % d,
               'cell': [None, u'TOTAL SERVICE',
               f_bill(sec_tot), f_cost(ht_tot), f_cost(ttc_tot) ]})
            if report_type=='detail':
               data[-1]['cell'].insert(2, None)
               data[-1]['cell'].insert(3, None)
         old_d=d
         sec_tot = ht_tot = ttc_tot = 0
         # Header for new department
         data.append({
            'id':  d,
            'cell': [old_d, None, None, None, None]
         })
         if report_type=='detail':
            data[-1]['cell'].insert(2, None)
            data[-1]['cell'].insert(3, None)

      sec_tot += cdr.billsec
      ht_tot += cdr.ht or 0
      ttc_tot += cdr.ttc or 0

      data.append({
         'id':  cdr.user,
         'cell': [None,
         u,
         f_bill(cdr.billsec),
         f_cost(cdr.ht),
         f_cost(cdr.ttc) ]
      })
      if report_type=='detail':
         # Hide destination for privacy
         data[-1]['cell'].insert(2, cdr.calldate) 
         data[-1]['cell'].insert(3, cdr.dst[:3] + '***') 

   data.append({
      'id':  'total_%s' % old_d,
      'cell': [None, u'TOTAL SERVICE',
      f_bill(sec_tot), f_cost(ht_tot), f_cost(ttc_tot) ]})
   if report_type=='detail':
      data[-1]['cell'].insert(2, None)
      data[-1]['cell'].insert(3, None)
   return dict(page=page, total=total, rows=data)


class Billing_ctrl(BaseController):
   '''Billing controller
   '''

   allow_only = not_anonymous('Veuillez vous connecter pour continuer')
   paginate_limit = 25


   @sidebar(u'Facturation', sortorder = 4, icon = '/images/ktimetracker.png')
   @expose('genshi:astportal2.templates.form_new')
   def index(self, **kw):
      '''Formulaire facturation
      '''
      tmpl_context.form = new_billing_form

      return dict( title=u'Facturation', debug='', values={'begin': None, 'end': None})


   @validate(new_billing_form, error_handler=index)
   @expose(template="astportal2.templates.grid")
   def result(self, month=None, end=None, begin=None, report_type='group', 
         department='ALL', phones=None):
      ''' Process form, create sqlalchemy filter
      Returns jqGrid
      '''

      crit = [] # list of criterion

      if report_type=='detail':
         cdrs = DBSession.query(CDR.calldate, CDR.user, CDR.dst, 
            CDR.billsec, CDR.ht, CDR.ttc, CDR.department)

      else: # report_type 'group' is default
         cdrs = DBSession.query( CDR.user,
            func.sum(CDR.billsec).label('billsec'),
            func.sum(CDR.ht).label('ht'),
            func.sum(CDR.ttc).label('ttc'),
            CDR.department)

      cdrs = check_access(cdrs)

      # Billed calls only
      cdrs = cdrs.filter(CDR.ht>0)

      # month is prioritary over begin / end
      if month:
         begin = datetime.datetime.strptime(month, '%d/%m/%Y')
         if begin.month==12:
            end = datetime.datetime(begin.year+1, 1, 1)
         else:
            end = datetime.datetime(begin.year, begin.month+1, 1)
         crit.append(u'mois=%s' % begin.strftime('%B %Y').decode('utf-8'))
         cdrs = cdrs.filter(CDR.calldate>=begin)
         cdrs = cdrs.filter(CDR.calldate<end)

      else:
         if begin:
            crit.append(u'début=%s'  % begin.strftime('%d/%m/%Y').decode('utf-8'))
            cdrs = cdrs.filter(CDR.calldate>=begin)
         if end:
            crit.append(u'fin=%s' % end.strftime('%d/%m/%Y').decode('utf-8'))
            cdrs = cdrs.filter(CDR.calldate<=end)

      # department is prioritary over phones
      if department!='ALL':
         d = DBSession.query(Department).get(department)
         crit.append(u'service=%s' % d.name)
         cdrs = cdrs.filter(CDR.department==department)

      elif phones:
            if type(phones)!=type([]):
               phones = ['%ss' % (prefix_src, phones)]
               crit.append(u'téléphone='+phones)
            else:
               phones = ['%s%s' % (prefix_src, p) for p in phones]
               crit.append(u'téléphones='+', '.join(phones))
            cdrs = cdrs.filter(CDR.src.in_(phones))

      # jqGrid common definition
      colNames = [u'Service', u'Nom (poste)', u'Durée', u'CFP HT', u'CFP TTC']
      colModel = [
            { 'width': 200, 'sortable': False },
               { 'width': 200, 'sortable': False  },
               { 'width': 60, 'align': 'right', 'sortable': False  },
               { 'width': 60, 'align': 'right', 'sortable': False  },
               { 'width': 60, 'align': 'right', 'sortable': False  },
            ]

      if report_type=='detail':
         # More columns when displaying detail
         fetchURL = 'fetch_detail'
         colNames.insert(2 , u'Date')
         colModel.insert(2 , { 'width': 150, 'align': 'left', 'sortable': False })
         colNames.insert(3 , u'Appelé')
         colModel.insert(3 , { 'width': 60, 'sortable': False })
      else:
         fetchURL = 'fetch_group'

      grid = MyJqGrid( id='grid', url=fetchURL, title=u'Facturation',
            sortname='src',
            colNames = colNames,
            colModel = colModel,
            report_type = report_type,
            out_of = u'sur'
            )

      msg = ''
      if len(crit):
         if len(crit)>1: msg = u'Critères: '
         else: msg = u'Critère: '
         msg += ', et '.join(crit) + '.'
         flash(msg)

      if report_type!='detail':
         # Group to sum by src
         cdrs = cdrs.group_by(CDR.user,CDR.department)

      # Initialize global data
      global filtered_cdrs
      filtered_cdrs = cdrs

      global phones_dict
      phones_dict = {}
      for p in DBSession.query(Phone):
         dptm = p.department.comment if p.department else u'Non affecté'
         phones_dict[p.exten] = (phone_user_display_name(p), dptm)

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
      ''' Export data
      '''

      if not in_any_group('admin', 'DG', 'Compta', 'Chefs', 'Utilisateurs'):
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
      row = ['Service', 'Nom (poste)', 'Durée', 'CFP HT', 'CFP TTC']
      if report_type=='detail':
         row.insert(2, 'Date')
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

