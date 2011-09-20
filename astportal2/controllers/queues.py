# -*- coding: utf-8 -*-
# Queue CReate / Update / Delete RESTful controller
# http://turbogears.org/2.0/docs/main/RestControllers.html

from tg import expose, flash, redirect, tmpl_context, validate, config
from tg.controllers import RestController
from tgext.menu import sidebar

from repoze.what.predicates import in_group

from tw.api import js_callback
from tw.forms import TableForm, Label, SingleSelectField, TextField, HiddenField
from tw.forms.validators import NotEmpty, Int

from genshi import Markup

from astportal2.model import DBSession, Queue, Sound, Group
from astportal2.lib.myjqgrid import MyJqGrid
from astportal2.lib.asterisk import asterisk_update_queue
from astportal2.lib.app_globals import Globals

import logging
log = logging.getLogger(__name__)

class Sounds_list(SingleSelectField):
   sound_type = 0
   def update_params(self,d):
      options = []
      for s in DBSession.query(Sound).filter(Sound.type==self.sound_type).order_by(Sound.name):
         c = s.name
         if s.comment is not None:
            c += u' : ' + s.comment if len(s.comment)<40 \
               else s.comment[:40] + '...'
         options.append((s.sound_id, c))
      d['options'] = options
      SingleSelectField.update_params(self, d)
      return d

common_fields = [
   TextField('comment', validator=NotEmpty,
      label_text=u'Descriptif',
      help_text=u'Entrez le descriptif du groupe d\'appel'),
   Sounds_list('music', sound_type=0, not_empty=False,
      label_text=u'Musique d\'attente',
      help_text=u'Choisissez une musique d\'attente'),
   Sounds_list('announce', sound_type=1, not_empty=False,
      label_text=u'Annonce agent',
      help_text=u'Choisissez une annonce à la prise d\'appel'),
   SingleSelectField('strategy',
      options = [('ringall', u'Tous les agents'),
         ('leastrecent', u'Dernier appel plus ancien'),
         ('fewestcalls', u'Moins d\'appels'),
         ('random', u'Aléatoire'),
         ('rrmemory', u'Circulaire'),
      ],
      label_text=u'Distribution des appels', help_text=u''),
   TextField('wrapuptime', validator=Int, size=4, default=0,
      label_text=u'Temps de réflexion (sec)', help_text=u''),
   TextField('announce_frequency', validator=Int, size=4, default=0,
      label_text=u'Fréquence d\'annonce (sec)', 
      help_text=u'Entrez "0" pour supprimer les annonces'),
   TextField('min_announce_frequency', validator=Int, size=4, default=0,
      label_text=u'Fréquence d\'annonce minimale (sec)', help_text=u''),
   SingleSelectField('announce_holdtime',
      options = [ ('no', u'Non'), ('yes', u'Oui'), ('once', u'Une fois')],
      label_text=u'Annonce temps d\'attente', help_text=u''),
   SingleSelectField('announce_position',
      options = [ ('no', u'Non'), ('yes', u'Oui')],
      label_text=u'Annonce position', help_text=u''),
   HiddenField('_method',validator=None), # Needed by RestController
   HiddenField('queue_id',validator=Int),
   ]

class New_queue_form(TableForm):
   ''' New queue form
   '''
   fields = []
   fields.extend(common_fields)
   fields.insert(0, TextField('name', validator=NotEmpty,
      label_text=u'Nom', help_text=u'Entrez le nom du groupe d\'appel'))
   submit_text = u'Valider...'
   action = 'create'
   hover_help = True
new_queue_form = New_queue_form('new_queue_form')


class Edit_queue_form(TableForm):
   ''' Edit Queue form
   '''
   fields = []
   fields.extend(common_fields)
   submit_text = u'Valider...'
   action = '/queues/'
   hover_help = True
edit_queue_form = Edit_queue_form('edit_queue_form')


def row(q):
   '''Displays a formatted row of the queues list
   Parameter: Queue object
   '''

   html =  u'<a href="'+ str(q.queue_id) + u'/edit" title="Modifier">'
   html += u'<img src="/images/edit.png" border="0" alt="Modifier" /></a>'
   html += u'&nbsp;&nbsp;&nbsp;'
   html += u'<a href="#" onclick="del(\''+ str(q.queue_id) + \
         u'\',\'Suppression du groupe d\\\'appels ' + q.name + u'\')" title="Supprimer">'
   html += u'<img src="/images/delete.png" border="0" alt="Supprimer" /></a>'

   return [Markup(html), q.name, q.comment ]


class Queue_ctrl(RestController):
   
   allow_only = in_group('admin', 
         msg=u'Vous devez appartenir au groupe "admin" pour gérer les groupes d\'appels')

   @sidebar(u'-- Administration || Groupes ACD',
      icon = '/images/kdf.png', sortorder = 13)
   @expose("genshi:astportal2.templates.grid")
   def get_all(self):
      ''' List all queues
      '''
      grid = MyJqGrid( 
            id='grid', url='fetch', caption=u'Groupes ACD',
            colNames = [u'Action', u'Nom', u'Description'],
            colModel = [ 
               { 'width': 80, 'align': 'center', 'sortable': False, 'search': False },
               { 'display': u'Nom', 'name': 'name', 'width': 80 },
               { 'display': u'Description', 'name': 'comment', 'width': 160 },
            ],
            sortname = 'name',
            navbuttons_options = {'view': False, 'edit': False, 'add': True,
               'del': False, 'search': False, 'refresh': True, 
               'addfunc': js_callback('add'),
               }
            )
      tmpl_context.grid = grid
      tmpl_context.form = None
      return dict( title=u'Liste des groupes d\'appels', debug='')


   @expose('json')
   def fetch(self, page=1, rows=10, sidx='user_name', sord='asc', _search='false',
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

      queue = DBSession.query(Queue)
      total = queue.count()/rows + 1
      column = getattr(Queue, sidx)
      queue = queue.order_by(getattr(column,sord)()).offset(offset).limit(rows)
      data = [ { 'id'  : q.queue_id, 'cell': row(q) } for q in queue ]

      return dict(page=page, total=total, rows=data)


   @expose(template="astportal2.templates.form_new")
   def new(self, **kw):
      ''' Display new queue form
      '''
      tmpl_context.form = new_queue_form
      return dict(title = u'Nouveau groupe d\'appel', debug='', values='')
      
   @validate(new_queue_form, error_handler=new)
   @expose()
   def create(self, **kw):
      ''' Add new queue to DB
      '''
      q = Queue()
      q.name = kw['name']
      q.comment = kw['comment']
      q.music_id = int(kw['music'])
      q.announce_id = int(kw['announce'])
      q.strategy = kw['strategy']
      q.wrapuptime = int(kw['wrapuptime'])
      q.announce_frequency = int(kw['announce_frequency'])
      q.min_announce_frequency = int(kw['min_announce_frequency'])
      q.announce_holdtime = 1 if kw['announce_holdtime']=='yes' else 0
      q.announce_position = 1 if kw['announce_position']=='yes' else 0
      DBSession.add(q)

      # Create new group for supervisors
      g = Group()
      g.group_name = u'SV %s' % q.name
      g.display_name = u'Superviseurs groupe d\'appels %s' % q.name
      DBSession.add(g)

      # Create new group for members
      g = Group()
      g.group_name = u'AG %s' % q.name
      g.display_name = u'Agents groupe d\'appels %s' % q.name
      DBSession.add(g)

      # Create Asterisk queue
      asterisk_update_queue(q)
      
      # Add to list of queues
      Globals.asterisk.queues[q.name] = {}
      Globals.manager.send_action({'Action': 'QueueStatus'})

      flash(u'Nouveau groupe d\'appel "%s" créé' % (kw['name']))
      redirect('/queues/')


   @expose(template="astportal2.templates.form_new")
   def edit(self, id=None, **kw):
      ''' Display edit queue form
      '''
      if not id: id = kw['queue_id']
      q = DBSession.query(Queue).get(id)
      v = {'queue_id': q.queue_id, 'comment': q.comment, '_method': 'PUT',
            'music': q.music_id, 'announce': q.announce_id, 'strategy': q.strategy, 
            'wrapuptime': q.wrapuptime, 'announce_frequency': q.announce_frequency, 
            'announce_holdtime': q.announce_holdtime, 'announce_position': q.announce_position}
      tmpl_context.form = edit_queue_form
      return dict(title = u'Modification groupe d\'appels ' + q.name, debug='', values=v)


   @validate(edit_queue_form, error_handler=edit)
   @expose()
   def put(self, queue_id, **kw):
      ''' Update queue in DB
      '''
      log.info('update %d' % queue_id)
      q = DBSession.query(Queue).get(queue_id)
      q.comment = kw['comment']
      q.music_id = int(kw['music'])
      q.announce_id = int(kw['announce'])
      q.strategy = kw['strategy']
      q.wrapuptime = int(kw['wrapuptime'])
      q.announce_frequency = int(kw['announce_frequency'])
      q.min_announce_frequency = int(kw['min_announce_frequency'])
      q.announce_holdtime = 1 if kw['announce_holdtime']=='yes' else 0
      q.announce_position = 1 if kw['announce_position']=='yes' else 0
      flash(u'Groupe d\'appel modifié')

      # Update Asterisk queue
      asterisk_update_queue(q)
      Globals.manager.send_action({'Action': 'QueueStatus'})

      redirect('/queues/')


   @expose()
   def delete(self, id, **kw):
      ''' Delete queue from DB
      '''
      log.info(u'delete ' + kw['_id'])
      q = DBSession.query(Queue).get(kw['_id'])
      gn = (u'SV %s' % q.name, u'AG %s' % q.name)
      log.info(u'delete ' + kw['_id'])
      DBSession.delete(q)

      # Delete supervisor and members groups
      for g in DBSession.query(Group).filter(Group.group_name.in_(gn)):
         log.info(u'delete group "%s"' % g)
         DBSession.delete(g)

      # Delete Asterisk queue
      res = Globals.manager.update_config(
         config.get('directory.asterisk') + 'queues.conf', 
         None, [('DelCat', q.name)])
      log.debug('Delete queue "%s" returns %s' % (q.name, res))
      Globals.manager.send_action({'Action': 'QueueReload'})
      if q.name in Globals.asterisk.queues.keys():
         # Delete from list of queues
         del(Globals.asterisk.queues[q.name])
      Globals.manager.send_action({'Action': 'QueueStatus'})

      flash(u'Groupe d\'appels supprimé', 'notice')
      redirect('/queues/')


