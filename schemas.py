"""
Schemas de Pydantic.

FastAPI usa estas clases para dos cosas:
  - Validar el JSON que entra en cada petición (los campos y sus tipos).
  - Definir qué campos salen en la respuesta (nunca devolvemos password_hash).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


# ---------- Usuarios / Auth ----------

class UsuariRegistre(BaseModel):
    nom: str
    email: EmailStr
    password: str


class UsuariLogin(BaseModel):
    email: EmailStr
    password: str


class UsuariUpdate(BaseModel):
    nom: Optional[str] = None
    password: Optional[str] = None


class UsuariOut(BaseModel):
    id: int
    nom: str
    email: EmailStr
    rol: str
    data_alta: datetime

    class Config:
        from_attributes = True   # permite crear el schema desde un objeto SQLAlchemy


class LoginResposta(BaseModel):
    token: str
    usuari: UsuariOut


# ---------- Actividades ----------

class ActivitatIn(BaseModel):
    nom: str
    descripcio: str = ""
    durada_min: int = 60


class ActivitatOut(BaseModel):
    id: int
    nom: str
    descripcio: str
    durada_min: int

    class Config:
        from_attributes = True


# ---------- Clases ----------

class ClasseIn(BaseModel):
    activitat_id: int
    monitor: str
    sala: str
    data_hora: datetime
    aforament_max: int


class ClasseUpdate(BaseModel):
    monitor: str
    sala: str
    data_hora: datetime
    aforament_max: int


class ClasseOut(BaseModel):
    id: int
    activitat_id: int
    monitor: str
    sala: str
    data_hora: datetime
    aforament_max: int
    places_lliures: int
    activitat: Optional[ActivitatOut] = None

    class Config:
        from_attributes = True


# ---------- Reservas ----------

class ReservaOut(BaseModel):
    id: int
    usuari_id: int
    classe_id: int
    data_reserva: datetime
    estat: str

    class Config:
        from_attributes = True


class ReservaHistorial(BaseModel):
    id: int
    classe: ClasseOut
    data_reserva: datetime
    estat: str

    class Config:
        from_attributes = True


class InscritOut(BaseModel):
    """Lo que ve el admin al consultar quién está inscrito en una clase."""
    reserva_id: int
    usuari: UsuariOut
    estat: str
    data_reserva: datetime
