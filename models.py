"""
Modelos de datos (tablas de la base de datos).

Estas cuatro clases se corresponden con el diagrama de clases del diseño:
Usuario, Activitat, Classe y Reserva. SQLAlchemy crea una tabla por clase.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship

from database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), default="soci")          # 'soci' o 'admin'
    data_alta = Column(DateTime, default=datetime.utcnow)

    # Un usuario tiene muchas reservas.
    reserves = relationship("Reserva", back_populates="usuari")


class Activitat(Base):
    __tablename__ = "activitats"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(80), nullable=False)           # Ej.: Yoga, Spinning
    descripcio = Column(Text, default="")
    durada_min = Column(Integer, default=60)

    # Una actividad tiene muchas clases programadas.
    classes = relationship("Classe", back_populates="activitat")


class Reserva(Base):
    __tablename__ = "reserves"

    id = Column(Integer, primary_key=True, index=True)
    usuari_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    classe_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    data_reserva = Column(DateTime, default=datetime.utcnow)
    estat = Column(String(20), default="confirmada")   # confirmada/cancel·lada/assistida

    usuari = relationship("Usuario", back_populates="reserves")
    classe = relationship("Classe", back_populates="reserves")

    # Un mismo socio no puede inscribirse dos veces en la misma clase.
    __table_args__ = (
        UniqueConstraint("usuari_id", "classe_id", name="uq_usuari_classe"),
    )


class Classe(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    activitat_id = Column(Integer, ForeignKey("activitats.id"), nullable=False)
    monitor = Column(String(100), nullable=False)
    sala = Column(String(50), nullable=False)
    data_hora = Column(DateTime, nullable=False)
    aforament_max = Column(Integer, nullable=False)
    places_lliures = Column(Integer, nullable=False)   # contador anti-overbooking

    activitat = relationship("Activitat", back_populates="classes")
    reserves = relationship("Reserva", back_populates="classe")
