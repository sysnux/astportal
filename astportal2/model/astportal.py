# -*- coding: utf-8 -*-
"""
AstPortal model
"""

from datetime import datetime

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import String, Unicode, Integer, DateTime
from sqlalchemy.orm import mapper, relation, backref

#from astportal2.model import metadata
from astportal2.model import DeclarativeBase, metadata, DBSession

__all__ = ['Phone','Department']


class CDR(DeclarativeBase):
   __tablename__ = 'cdr'
   acctid = Column(Integer, primary_key=True)
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


class Department(DeclarativeBase):
   __tablename__ = 'department'
   dptm_id = Column(Integer, primary_key=True)
   name = Column(Unicode(64), nullable=False, unique=True)
   comment = Column(Unicode())
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
   phone_id = Column(Integer, autoincrement=True, primary_key=True)
   ip = Column(Unicode(), nullable=False, unique=True)
   mac = Column(Unicode(), nullable=False, unique=True)
   password = Column(Unicode())
   number = Column(Unicode(16), unique=True)
   department_id = Column(Integer, ForeignKey('department.dptm_id'), nullable=False)
   user_id = Column(Integer, ForeignKey('tg_user.user_id'))
   created = Column(DateTime, nullable=False, default=datetime.now)
   department = relation('Department', backref=backref('phones', order_by=number))
   user = relation('User', backref=backref('phone'))

#   def __init__(self, num, did):
#      self.number = num
#      self.department_id = did
   def __repr__(self):
      return '<Phone: number="%s", department="%s">' % (
            self.number, self.department_id)


