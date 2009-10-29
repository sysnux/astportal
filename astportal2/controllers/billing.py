# -*- coding: utf-8 -*-

from tg import expose, flash, redirect, tmpl_context, request, response, validate
from astportal2.model import DBSession, CDR, Department, Phone, User
from tg.decorators import allow_only
from tg.controllers import CUSTOM_CONTENT_TYPE
from repoze.what.predicates import not_anonymous, in_group, in_any_group

import logging
log = logging.getLogger("astportal.controllers.cdr")

from tw.api import WidgetsList
from tw.forms import TableForm, HiddenField, Label, CalendarDatePicker, SingleSelectField, TextField, TextArea, MultipleSelectField, Spacer
from tw.forms.validators import DateConverter
from tw.jquery import FlexiGrid

from sqlalchemy import func, sql, types
import datetime

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
      src = ['068947' + p.number for p in phones]
      dst = [p.number for p in phones]
      cdrs = cdrs.filter( (CDR.src.in_(src)) | (CDR.dst.in_(dst)) )

   elif in_group('utilisateurs'):
      src = ['068947' + p.number for p in request.identity['user'].phone]
      dst = [p.number for p in request.identity['user'].phone]
      cdrs = cdrs.filter( (CDR.src.in_(src)) | (CDR.dst.in_(dst)) )

   else:
      flash(u'Accès interdit')
      redirect('/')

   return cdrs


def phone_user_display_name(p):
   if p.user:
      return ' ' + p.user.display_name
   else:
      return ''


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
         options = [(p.number, p.number + phone_user_display_name(p)) 
            for p in DBSession.query(Phone).order_by(Phone.number)]),
      Spacer(),
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

filtered_cdrs = None
phones_dict= None
def fetch(report_type, page, rp, sortname, sortorder, qtype, query):
      if not in_any_group('admin', 'chefs', 'utilisateurs'):
         flash(u'Accès interdit')
         redirect('/')

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
      if report_type=='detail':
         cdrs = cdrs.order_by(Department.name).order_by(Phone.number).order_by(CDR.calldate.desc()).offset(offset).limit(rp)
      else:
         cdrs = cdrs.order_by(Department.name).order_by(Phone.number).offset(offset).limit(rp)

      # Group by department
      by_dptm = {}
      for cdr in cdrs.all():
         d = dptm(phones_dict,cdr.src)
         if d=='':
            d = 'Inconnu ***'
         if not by_dptm.has_key(d):
            by_dptm[d] = []
         by_dptm[d].append({
            'src': cdr.src[4:],
            'billsec': cdr.billsec,
            'ht': cdr.ht,
            'ttc': cdr.ttc,
               })
         if report_type=='detail':
            by_dptm[d][-1]['dst'] = cdr.dst

      dptms = by_dptm.keys()
      dptms.sort()
      rows = []
      for d in dptms:
         old = d
         sec_tot = ht_tot = ttc_tot = 0
         for r in by_dptm[d]:
            sec_tot += r['billsec']
            ht_tot += r['ht'] or 0
            ttc_tot += r['ttc'] or 0
            rows.append({
               'id':  r['src'],
               'cell': [
                  old,
                  user(phones_dict,r['src']),
                  r['src'],
                  f_bill(r['billsec']),
                  r['ht'],
                  r['ttc']
                  ]
               })
            if report_type=='detail':
               rows[-1]['cell'].insert(3, r['dst'])
            old = ''

         # Sub total per department
         rows.append({
            'id': '',
            'cell': [
                  '',
                  '',
                  u'Totaux service',
                  f_bill(sec_tot),
                  ht_tot,
                  ttc_tot
               ]
            })

      return dict(page=page, total=total, rows=rows)


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
   @expose(template="astportal2.templates.flexigrid")
   def result(self, month=None, end=None, begin=None, report_type='group', 
         department='ALL', phones=None):


      filter = []
      if report_type=='detail':
         #cdrs = DBSession.query( CDR.calldate, CDR.src, CDR.dst, CDR.billsec, CDR.ht, CDR.ttc)
         cdrs = DBSession.query(CDR.calldate, CDR.src, CDR.dst, CDR.billsec, CDR.ht, CDR.ttc, Phone.number, Department.name).filter(CDR.src=='068947'+Phone.number).filter(Phone.department_id==Department.dptm_id)
      else: # elif report_type=='group':
         # report_type 'group' is default
         cdrs = DBSession.query( CDR.src,
               func.sum(CDR.billsec).label('billsec'),
               func.sum(CDR.ht).label('ht'),
               func.sum(CDR.ttc).label('ttc'),
               Phone.number,
               Department.name).filter(CDR.src=='068947'+Phone.number).filter(Phone.department_id==Department.dptm_id)

      cdrs = check_access(cdrs)

      # Outgoing calls go through Dahdi/g0
      cdrs = cdrs.filter("lastdata ILIKE 'Dahdi/g0/%'")
      cdrs = cdrs.filter(CDR.billsec>0)

      # month is prioritary on begin / end
      if month:
         filter.append(u'mois='+str(month))
         cdrs = cdrs.filter("'%s'<=calldate::date" % month)
         cdrs = cdrs.filter("calldate::date<('%s'::date + interval '1 month')" % month)
      else:
         if begin:
            filter.append(u'début='+begin.strftime('%d/%m/%Y'))
            cdrs = cdrs.filter(sql.cast(CDR.calldate, types.DATE)>=begin)
         if end:
            filter.append(u'fin='+end.strftime('%d/%m/%Y'))
            cdrs = cdrs.filter(sql.cast(CDR.calldate, types.DATE)<=end)

      # department is prioritary on phones
      if department!='ALL':
         filter.append(u'service='+str(department))
         phones = DBSession.query(Phone.number).filter(Phone.department_id==department).all()
         cdrs = cdrs.filter(CDR.src.in_(['47'+p.number for p in phones]))
      else:
         if phones:
            if type(phones)!=type([]):
               phones = ['068947'+phones]
            else:
               phones = ['068947'+p for p in phones]
            filter.append(u'phones='+', '.join(phones))
            cdrs = cdrs.filter(CDR.src.in_(phones))

      if report_type=='detail':
         fetchURL = 'fetch_detail'
         colModel = [
               { 'display': u'Service', 'width': 160 },
               { 'display': u'Nom', 'name': '', 'width': 120 },
               { 'display': u'Appelant', 'name': 'src', 'width': 80 },
               { 'display': u'Appelé', 'name': 'src', 'width': 80 },
               { 'display': u'Durée', 'width': 60, 'align': 'right' },
               { 'display': u'CFP HT', 'width': 60, 'align': 'right' },
               { 'display': u'CFP TTC', 'width': 60, 'align': 'right' },
               ]
      else:
         fetchURL = 'fetch_group'
         colModel = [
               { 'display': u'Service', 'width': 160 },
               { 'display': u'Nom', 'name': '', 'width': 120 },
               { 'display': u'Appelant', 'name': 'src', 'width': 80 },
               { 'display': u'Durée', 'width': 60, 'align': 'right' },
               { 'display': u'CFP HT', 'width': 60, 'align': 'right' },
               { 'display': u'CFP TTC', 'width': 60, 'align': 'right' },
               ]
      grid = FlexiGrid( id='flexi', fetchURL=fetchURL, title=None,
            sortname='src', sortorder='asc',
            colModel = colModel,
            usepager=True,
            useRp=True,
            rp=10,
            resizable=False,
            report_type=report_type,
            out_of=u'sur'
            )

      if len(filter):
         if len(filter)>1: m = u'Critères: '
         else: m = u'Critère: '
         flash( m + ', et '.join(filter) + '.')

      if report_type!='detail':
         cdrs = cdrs.group_by(CDR.src).group_by(Phone.number).group_by(Department.name)

      global filtered_cdrs
      filtered_cdrs = cdrs

      # phones['number'] = ('user_display_name','department_comment')
      global phones_dict
      phones_dict= dict([(p.number, (phone_user_display_name(p),p.department.comment))
         for p in DBSession.query(Phone)])

      tmpl_context.grid = grid
      
      return dict( title=u'Facturation', debug='', form='')


   @expose('json')
   def fetch_detail(self, page=1, rp=25, sortname='src', sortorder='asc', qtype=None, query=None):
      ''' Called by FlexiGrid JavaScript component
      '''
      return fetch('detail', page, rp, sortname, sortorder, qtype, query)


   @expose('json')
   def fetch_group(self, page=1, rp=25, sortname='src', sortorder='asc', qtype=None, query=None):
      ''' Called by FlexiGrid JavaScript component
      '''
      return fetch('group', page, rp, sortname, sortorder, qtype, query)

   @expose(content_type=CUSTOM_CONTENT_TYPE)
   def csv(self, report_type='group'):

      if not in_any_group('admin', 'chefs', 'utilisateurs'):
         flash(u'Accès interdit')
         redirect('/')

      today = datetime.datetime.today()
      filename = 'telephone-' + today.strftime("%Y%m%d") + '.csv'
      import StringIO
      import csv
      csvdata = StringIO.StringIO()
      writer = csv.writer(csvdata)

      global phones_dict
      global filtered_cdrs
      cdrs = filtered_cdrs
      total = cdrs.count()
      cdrs = cdrs.order_by(CDR.src).offset(0).limit(10000)

      # Group by department
      by_dptm = {}
      for cdr in cdrs.all():
         d = dptm(phones_dict,cdr.src)
         if d=='':
            d = 'Inconnu ***'
         if not by_dptm.has_key(d):
            by_dptm[d] = []
         by_dptm[d].append({
            'src': cdr.src[4:],
            'billsec': cdr.billsec,
            'ht': cdr.ht,
            'ttc': cdr.ttc,
               })
         if report_type=='detail':
            by_dptm[d][-1]['dst'] = cdr.dst

      dptms = by_dptm.keys()
      dptms.sort()
      rows = []
      for d in dptms:
         old = d
         sec_tot = ht_tot = ttc_tot = 0
         for r in by_dptm[d]:
            sec_tot += r['billsec']
            ht_tot += r['ht'] or 0
            ttc_tot += r['ttc'] or 0
            row = [
                  old,
                  user(phones_dict,r['src']),
                  r['src'],
                  f_bill(r['billsec']),
                  r['ht'],
                  r['ttc']
                  ]
            if report_type=='detail':
               row.insert(3, r['dst'])
            writer.writerow(row)
            old = ''

         # Sub total per department
         row = [
                  '',
                  '',
                  u'Totaux service',
                  f_bill(sec_tot),
                  ht_tot,
                  ttc_tot
               ]
         if report_type=='detail':
            row.insert(3, r['dst'])
         writer.writerow(row)

      rh = response.headers
      rh['Content-Type'] = 'text/csv; charset=utf-8'
      rh['Content-disposition'] = 'attachment; filename="%s"' % filename
      rh['Pragma'] = 'public' # for IE
      rh['Cache-control'] = 'max-age=0' #for IE

      return csvdata.getvalue()

