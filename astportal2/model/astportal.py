# -*- coding: utf-8 -*-
"""
AstPortal model
"""

from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey, Sequence
from sqlalchemy import Unicode, Unicode, Integer, DateTime, Boolean
from sqlalchemy.orm import mapper, relation, backref

#from astportal2.model import metadata
from astportal2.model import DeclarativeBase, metadata, DBSession

__all__ = ['Phone','Department']


class CDR(DeclarativeBase):
   __tablename__ = 'cdr'
   acctid = Column(Integer, Sequence('cdr_seq'), primary_key=True)
   calldate = Column(DateTime, default=datetime.now)
   clid = Column(Unicode(80))
   src = Column(Unicode(80))
   dst = Column(Unicode(80))
   dcontext = Column(Unicode(80))
   channel = Column(Unicode(80))
   dstchannel = Column(Unicode(80))
   lastapp = Column(Unicode(80))
   lastdata = Column(Unicode(80))
   duration = Column(Integer)
   billsec = Column(Integer)
   disposition = Column(Unicode(45))
   amaflags = Column(Integer)
   accountcode = Column(Unicode(20))
   uniqueid = Column(Unicode(32))
   userfield = Column(Unicode(255))
   ut = Column(Integer)
   ht = Column(Integer)
   ttc = Column(Integer)
   department = Column(Integer)
   user = Column(Integer)

   def __repr__(self):
      return '<CDR: %s "%s" -> "%s" (%d sec)>' % (
            str(self.calldate), self.src, self.dst, self.billsec)


class Department(DeclarativeBase):
   __tablename__ = 'department'
   dptm_id = Column(Integer, Sequence('dptm_seq'), primary_key=True)
   name = Column(Unicode(64), nullable=False, unique=True)
   comment = Column(Unicode(80))
   created = Column(DateTime, nullable=False, default=datetime.now)
#mapper(Department, department_table,
#        properties=dict(phones=relation(Phone, backref='department')))

#   def __init__(self, name, comment):
#      self.name = name
#      self.comment = comment
   def __repr__(self):
      return '<Department: name="%s", comment="%s">' % (
            self.name, self.comment)

class Phone(DeclarativeBase):
   '''
   '''
   __tablename__ = 'phone'
   phone_id = Column(Integer, Sequence('phone_seq'), autoincrement=True, primary_key=True)
   sip_id = Column(Unicode(10), nullable=False, unique=True)
   mac = Column(Unicode(17)) # MAC can be null (eg. DECT)
   password = Column(Unicode(10))
   contexts = Column(Unicode(64))
   callgroups = Column(Unicode(64))
   pickupgroups = Column(Unicode(64))
   exten = Column(Unicode(16), unique=True)
   dnis = Column(Unicode(16), unique=True)
   department_id = Column(Integer, ForeignKey('department.dptm_id'), nullable=False)
   user_id = Column(Integer, ForeignKey('tg_user.user_id'))
   created = Column(DateTime, nullable=False, default=datetime.now)
   department = relation('Department', backref=backref('phones', order_by=exten))
   user = relation('User', backref=backref('phone'))

#   def __init__(self, num, did):
#      self.exten = num
#      self.department_id = did
   def __repr__(self):
      return '<Phone: exten="%s", user="%s">' % (
            self.exten, self.user_id)

class Phonebook(DeclarativeBase):
   '''
   '''
   __tablename__ = 'phonebook'
   pb_id = Column(Integer, Sequence('phonebook_seq'), autoincrement=True, primary_key=True)
   firstname = Column(Unicode(32), nullable=False)
   lastname = Column(Unicode(32), nullable=False)
   company = Column(Unicode(32))
   phone1 = Column(Unicode(16), nullable=False)
   phone2 = Column(Unicode(16))
   phone3 = Column(Unicode(16))
   private = Column(Boolean())
   email = Column(Unicode(64))
   created = Column(DateTime, nullable=False, default=datetime.now)
   user_id = Column(Integer, ForeignKey('tg_user.user_id'))
   user = relation('User', backref=backref('phonebook'))

class View_phonebook(DeclarativeBase):
   '''
   View used to include users in phonebook.

   Built like:
CREATE VIEW view_pb AS
   SELECT -phone_id as pb_id, lastname, firstname, '__COMPANY__' AS company, 
   exten AS phone1, dnis AS phone2, '' AS phone3, 0 AS private, -1 as user_id
   FROM phone LEFT OUTER JOIN tg_user ON phone.user_id=tg_user.user_id 
   WHERE exten is not null
UNION
   SELECT pb_id, lastname, firstname, company, phone1, phone2, phone3, private, user_id
   FROM phonebook;
   '''
   __tablename__ = 'view_pb'
   pb_id = Column(Integer, primary_key=True)
   firstname = Column(Unicode())
   lastname = Column(Unicode())
   company = Column(Unicode())
   phone1 = Column(Unicode())
   phone2 = Column(Unicode())
   phone3 = Column(Unicode())
   email = Column(Unicode())
   private = Column(Boolean())
   user_id = Column(Integer)


class Sound(DeclarativeBase):
   ''' Definition of a sound
   '''
   __tablename__ = 'sound'
   sound_id = Column(Integer, Sequence('sound_seq'), primary_key=True)
   name = Column(Unicode(64), nullable=False, unique=True)
   language = Column(Unicode(2), default=u'fr')
   type = Column(Integer, default=0) # 0=moh (class?), 1=sound
   comment = Column(Unicode(80))
   owner_id = Column(Integer, ForeignKey('tg_user.user_id'))
   created = Column(DateTime, nullable=False, default=datetime.now)
   def __repr__(self):
      return '<Sound: name="%s", comment="%s", type="%s">' % (
            self.name, self.comment, self.type)


class Queue(DeclarativeBase):
   ''' Definition of a queue
   '''
   __tablename__ = 'queue'
   queue_id = Column(Integer, Sequence('queue_seq'), primary_key=True)
   name = Column(Unicode(64), nullable=False, unique=True)
   comment = Column(Unicode(80))
   created = Column(DateTime, nullable=False, default=datetime.now)
   music_id = Column(Integer, ForeignKey('sound.sound_id'))
   announce_id = Column(Integer, ForeignKey('sound.sound_id'))
   strategy  = Column(Unicode(16))
   connectdelay = Column(Integer)
   connecturl = Column(Unicode(160))
   wrapuptime = Column(Integer)
   hangupurl = Column(Unicode(160))
   announce_frequency = Column(Integer)
   min_announce_frequency = Column(Integer)
   min_announce_frequency = Column(Integer)
   announce_holdtime  = Column(Integer)
   announce_position  = Column(Integer)
   priority = Column(Integer)
   monitor = Column(Boolean)
   def __repr__(self):
      return '<Queue: name="%s", comment="%s">' % (
            self.name, self.comment)


class Queue_log(DeclarativeBase):
   ''' Definition of a queue
   '''
   __tablename__ = 'queue_log'
   ql_id = Column(Integer, Sequence('queuelog_seq'), primary_key=True)
   timestamp = Column(DateTime)
   uniqueid = Column(Unicode(32))
   queue = Column(Unicode(45))
   channel = Column(Unicode(80))
   data1 = Column(Unicode(80))
   data2 = Column(Unicode(80))
   data3 = Column(Unicode(80))
   queue_event_id = Column(Integer, name='event_qe_id')
   department = Column(Integer)
   user = Column(Integer)

   def __repr__(self):
      return '<Queue_log: ql_id="%d", uniqueid="%s">' % (
            self.ql_id, self.uniqueid)


class Queue_event(DeclarativeBase):
   ''' List of queue events
   '''
   __tablename__ = 'queue_event'
   qe_id = Column(Integer, primary_key=True)
   event = Column(Unicode(80), nullable=False, unique=True)
   def __repr__(self):
      return '<Queue_event: qe_id="%d", event="%s">' % (
            self.qe_id, self.event)


class Pickup(DeclarativeBase):
   ''' Definition of pickup groups (Asterisk supports groups 0-63)
   '''
   __tablename__ = 'pickup'
   pickup_id = Column(Integer, Sequence('pickup_seq'), primary_key=True)
   name = Column(Unicode(64), nullable=False, unique=True)
   comment = Column(Unicode(80))
   created = Column(DateTime, nullable=False, default=datetime.now)
   def __repr__(self):
      return '<Pickup: name="%s", comment="%s">' % (
            self.name, self.comment)


class Action(DeclarativeBase):
   ''' List of an IVR actions
   '''
   __tablename__ = 'action'
   action_id = Column(Integer, primary_key=True)
   name = Column(Unicode(64), nullable=False, unique=True)
   comment = Column(Unicode(80))
   def __repr__(self):
      return '<Action: name="%s", comment="%s">' % (
            self.name, self.comment)


class Application(DeclarativeBase):
   ''' Definition of an IVR application
   Application is defined by name and phone number
   It belongs to a client, and is created by an administrator
   '''
   __tablename__ = 'application'
   app_id = Column(Integer, Sequence('application_seq'), primary_key=True)
   name = Column(Unicode(64), nullable=False, unique=True)
   dnis = Column(Unicode(16)) # External number
   exten = Column(Unicode(16)) # Intrenal extension
   comment = Column(Unicode(80))
   begin = Column(DateTime, default=datetime.now)
   end = Column(DateTime)
   active = Column(Boolean)
   owner_id = Column(Integer, ForeignKey('tg_user.user_id'))
#   owner = relation('User', backref='applications')
#   owner = relation('User', primaryjoin=('User.user_id'==owner_id), backref='applications')
   created_by = Column(Integer, ForeignKey('tg_user.user_id'))
   created = Column(DateTime, nullable=False, default=datetime.now)
   def __repr__(self):
      return '<Application: name="%s", comment="%s">' % (
            self.name, self.comment)

class Scenario(DeclarativeBase):
   ''' Scenario is the application's dialplan
   '''
   __tablename__ = 'scenario'
   sce_id = Column(Integer, Sequence('scenario_seq'), primary_key=True)
   app_id = Column(Integer, ForeignKey('application.app_id'))
   context = Column(Unicode(64), nullable=False)
   extension = Column(Unicode(64), nullable=False)
   step = Column(Integer, nullable=False)
   action = Column(Integer, nullable=False)
   parameters = Column(Unicode(64))
   comments = Column(Unicode(64))
   top = Column(Integer)
   left = Column(Integer)
   application = relation('Application', backref='scenario')


# This is the association table for the many-to-many relationship between
# sounds and applications
sound_application_table = Table('sound_application', metadata,
    Column('sound_id', Integer, ForeignKey('sound.sound_id',
        onupdate="CASCADE", ondelete="CASCADE")),
    Column('app_id', Integer, ForeignKey('application.app_id',
        onupdate="CASCADE", ondelete="CASCADE"))
)


class Holiday(DeclarativeBase):
   ''' Definition of holidays
   '''
   __tablename__ = 'holiday'
   holiday_id = Column(Integer, Sequence('holiday_seq'), primary_key=True)
   name = Column(Unicode(64), nullable=False, unique=True)
   day = Column(Integer, nullable=False)
   month = Column(Integer, nullable=False)
   created = Column(DateTime, nullable=False, default=datetime.now)
   def __repr__(self):
      return '<Holiday: name="%s", date="%d/%d">' % (
            self.name, self.day, self.month)


class Record(DeclarativeBase):
   ''' Definition of records
   '''
   __tablename__ = 'record'
   record_id = Column(Integer, Sequence('record_seq'), primary_key=True)
   uniqueid = Column(Unicode(32))
   queue_id = Column(Integer)
   member_id = Column(Integer)
   user_id = Column(Integer)
   custom1 = Column(Unicode(32))
   custom2 = Column(Unicode(32))
   created = Column(DateTime, nullable=False, default=datetime.now)
   def __repr__(self):
      return '<Record: uniqueid="%d">' % (self.uniqueid)


class Fax(DeclarativeBase):
   ''' Definition of records
   '''
   __tablename__ = 'fax'
   fax_id = Column(Integer, Sequence('fax_seq'), primary_key=True)
   hyla_id = Column(Integer)
   hyla_status = Column(Integer)
   type = Column(Integer) # 0=Sent, 1=Received
   user_id = Column(Integer) # relation('User', backref=backref('fax'))
   dest = Column(Unicode(60))
   src = Column(Unicode(60))
   filename = Column(Unicode(60))
   comment = Column(Unicode(80))
   created = Column(DateTime, nullable=False, default=datetime.now)
   def __repr__(self):
      return '<Record: uniqueid="%d">' % (self.uniqueid)

