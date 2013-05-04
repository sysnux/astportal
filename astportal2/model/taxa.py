# -*- coding: utf-8 -*-
"""
Modèle pour la taxation
"""

from sqlalchemy import Table, Column, ForeignKey, Sequence
from sqlalchemy import Unicode, Integer, Numeric
from sqlalchemy.orm import mapper, relation, backref, column_property

from astportal2.model import DeclarativeBase, metadata, DBSession


class Prix(DeclarativeBase):
   __tablename__ = 'table_prix'
   prix_id = Column(Integer, Sequence('prix_seq'), primary_key=True)
   zone_destination = Column(Unicode())
   ctm = Column(Integer())
   prix_ctm = Column(Numeric(precision=2))
   cta = Column(Integer())
   prix_cta = Column(Numeric(precision=2))
   prix_hc = Column(Numeric(precision=2))
   prix_hp = Column(Numeric(precision=2))
   step_hc = Column(Integer())
   step_hp = Column(Integer())

class Zone(DeclarativeBase):
   __tablename__ = 'table_zonage'
   zone_id = Column(Integer, Sequence('zone_seq'), primary_key=True)
   prefixe = Column(Unicode())
   code_geo = Column(Unicode())
   zone_tarifaire = Column(Unicode())
   zaa = Column(Unicode())
   zam = Column(Unicode())
   zna = Column(Unicode())
   ile_ou_pays = Column(Unicode())
   surtaxe_pcv = Column(Numeric(precision=2))

class OptimumTime(DeclarativeBase):
   __tablename__ = 'optimum_time'
   opt_id = Column(Integer, Sequence('opt_seq'), primary_key=True)
   offre = Column(Unicode())
   destination = Column(Unicode())
   ctm = Column(Numeric(precision=2))
   prix_ctm1 = Column(Numeric(precision=2))
   prix_ctm2 = Column(Numeric(precision=2))
   prix_hp1 = Column(Numeric(precision=2))
   prix_hp2 = Column(Numeric(precision=2))
   prix_hc1 = Column(Numeric(precision=2))
   prix_hc2 = Column(Numeric(precision=2))
   prix_df = Column(Numeric(precision=2))
   prix_hf = Column(Numeric(precision=2))

class Pays(DeclarativeBase):
   __tablename__ = 'liste_pays'
   pays_id = Column(Integer, Sequence('pays_seq'), primary_key=True)
   code = Column(Unicode())
   libelle = Column(Unicode())

