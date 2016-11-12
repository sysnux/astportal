# -*- coding: utf-8 -*-
"""
AstPortal model
"""

from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey, Sequence
from sqlalchemy import Unicode, Integer, DateTime, Boolean, LargeBinary
from sqlalchemy.orm import mapper, relation, backref, column_property

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
   vendor = Column(Unicode())
   model = Column(Unicode())
   password = Column(Unicode(10))
   contexts = Column(Unicode(64))
   callgroups = Column(Unicode(64))
   pickupgroups = Column(Unicode(64))
   phonebook_label = Column(Unicode(64))
   exten = Column(Unicode(16), unique=True)
   dnis = Column(Unicode(16), unique=True)
   secretary = Column(Unicode(16))
   department_id = Column(Integer, ForeignKey('department.dptm_id'), nullable=False)
   user_id = Column(Integer, ForeignKey('tg_user.user_id'))
   created = Column(DateTime, nullable=False, default=datetime.now)
   department = relation('Department', backref=backref('phones', order_by=exten))
   user = relation('User', backref=backref('phone'))
   hide_from_phonebook = Column(Boolean(), default=False)
   fax = Column(Boolean(), default=False) # Real fax machine connected via ATA
   block_cid_in = Column(Boolean(), default=False) # Block caller id on incoming calls
   block_cid_out = Column(Boolean(), default=False) # Block caller id on outgoing calls
   priority = Column(Boolean(), default=False) # This phone has priority (kill other calls if needed!)

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

   Must be manually created in the database:
CREATE VIEW view_pb as
 SELECT - phone.phone_id AS pb_id,
    tg_user.lastname,
    tg_user.firstname,
    '__COMPANY__'::text AS company,
    tg_user.email_address AS email,
    ''::text AS code,
    phone.exten AS phone1,
    phone.dnis AS phone2,
    ''::text AS phone3,
    false AS private,
    '-1'::integer AS user_id,
    phonebook_label
   FROM phone
     LEFT JOIN tg_user ON phone.user_id = tg_user.user_id
  WHERE phone.exten IS NOT NULL AND not hide_from_phonebook
UNION
 SELECT phonebook.pb_id,
    phonebook.lastname,
    phonebook.firstname,
    phonebook.company,
    phonebook.email,
    phonebook.code,
    phonebook.phone1,
    phonebook.phone2,
    phonebook.phone3,
    phonebook.private,
    phonebook.user_id,
    ''::text AS phonebook_label
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
   phonebook_label = Column(Unicode())


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
   timeout = Column(Integer)
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
   ''' Fax data
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
   pdf = Column(LargeBinary)
   def __repr__(self):
      return '<Fax: id="%d">' % (self.fax_id)


class Report(DeclarativeBase):
   ''' Post call report
   '''
   __tablename__ = 'report'
   report_id = Column(Integer, Sequence('report_seq'), primary_key=True)
   uniqueid = Column(Unicode(32))
   member_id = Column(Integer)
   queue_id = Column(Integer)
   custom1 = Column(Unicode(80))
   custom2 = Column(Unicode(80))
   subject = Column(Unicode(80))
   customer = Column(Unicode(80))
   manager = Column(Unicode(3))
   message = Column(Unicode(255))
   email = Column(Unicode(80))
   cc = Column(Unicode(255))
   created = Column(DateTime, nullable=False, default=datetime.now)
   user_id = Column(Integer, ForeignKey('tg_user.user_id'))
   user = relation('User', backref=backref('report'))


class Campaign(DeclarativeBase):
   ''' Outgoing campaign
   '''
   __tablename__ = 'campaign'
   cmp_id =  Column(Integer, Sequence('campaign_seq'), primary_key=True)
   name = Column(Unicode(80))
   comment = Column(Unicode(255))
   type = Column(Integer) # 0=commerciale, 1=récurrente, 2=événementielle
   active = Column(Boolean, default=False)
   begin = Column(DateTime)
   end = Column(DateTime)
   created = Column(DateTime, nullable=False, default=datetime.now)
   deleted = Column(DateTime)


class Customer(DeclarativeBase):
   ''' Outgoing campaign targets
   '''
   __tablename__ = 'customer'
   cust_id = Column(Integer, Sequence('customer_seq'), primary_key=True)
   cmp_id = Column(Integer, ForeignKey('campaign.cmp_id'))
   campaign = relation('Campaign', backref=backref('customers'))
   code = Column(Unicode(7))
   gender = Column(Unicode(80))
   firstname = Column(Unicode(80))
   lastname = Column(Unicode(80))
   phone1 = Column(Unicode(20)) # Domicile
   phone2 = Column(Unicode(20)) # Bureau
   phone3 = Column(Unicode(20)) # Bureau 2
   phone4 = Column(Unicode(20)) # Vini perso
   phone5 = Column(Unicode(20)) # Vini pro
   email = Column(Unicode(80))
   created = Column(DateTime, nullable=False, default=datetime.now)
   active = Column(Boolean, default=True) # Faux quand il ne faut plus 
                                          # appeler le client
   filename = Column(Unicode(80))
   display_name = column_property(gender + ' ' + firstname + ' ' + lastname)

class Outcall(DeclarativeBase):
   ''' Outgoing campaign call
   '''
   __tablename__ = 'outcall'
   out_id = Column(Integer, Sequence('outcall_seq'), primary_key=True)
   cust_id = Column(Integer, ForeignKey('customer.cust_id'))
   customer = relation('Customer', backref=backref('outcalls'))
   user_id = Column(Integer, ForeignKey('tg_user.user_id'))
   user = relation('User', backref=backref('outcalls'))
   uniqueid = Column(Unicode(32))
   phone = Column(Unicode(32))
   cookie = Column(Integer)
   result = Column(Integer)
   message = Column(Unicode(255))
   comment = Column(Unicode(255))
   begin = Column(DateTime)
   duration = Column(Integer)
   alarm_type = Column(Integer)
   alarm_dest = Column(Unicode(255))
   alarm_sent = Column(DateTime)
   alarm_result_code = Column(Integer)
   alarm_result_msg = Column(Unicode(255))
   created = Column(DateTime, nullable=False, default=datetime.now)

class Voicemessages(DeclarativeBase):
   ''' Voice messages (ODBC voicemail)
   '''
   __tablename__ = 'voicemessages'
   uniqueid = Column(Integer, Sequence('voicemessages_uniqueid_seq'), primary_key=True)
   msgnum  = Column(Integer)
   msg_id = Column(Unicode(40))
   dir = Column(Unicode(80))
   context = Column(Unicode(80))
   macrocontext = Column(Unicode(80))
   callerid = Column(Unicode(40))
   origtime = Column(Unicode(40))
   duration = Column(Unicode(20))
   flag = Column(Unicode(8))
   mailboxuser = Column(Unicode(80))
   mailboxcontext = Column(Unicode(80))
   recording = Column(LargeBinary)
   label = Column(Unicode(30))
   read  = Column(Boolean)
   def __repr__(self):
      return '<Voicemessage %d: user="%s">' % (self.uniqueid, self.mailboxuser)


class Shortcut(DeclarativeBase):
   ''' Definition of shortcuts
   '''
   __tablename__ = 'shortcut'
   shortcut_id = Column(Integer, Sequence('shortcut_seq'), primary_key=True)
   exten = Column(Unicode(10), nullable=False, unique=True)
   number = Column(Unicode(30), nullable=False, unique=True)
   comment = Column(Unicode())
   phone = Column(Unicode()) # null if global, else sip_id
   created = Column(DateTime, nullable=False, default=datetime.now)

   def __repr__(self):
      return '<Shortcut: %s -> %s comment="%s">' % (
            self.exten, self.number, self.comment)


