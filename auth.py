"""
Autenticación y seguridad.

Aquí está todo lo relacionado con contraseñas y tokens:
  - hashear / verificar contraseñas con bcrypt
  - crear y leer tokens JWT
  - dependencias de FastAPI para exigir login (soci) o rol admin
"""
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from database import get_db
import models

# Clave para firmar los tokens. En un proyecto real iría en una variable de
# entorno; aquí la dejamos fija para que el ejemplo sea autocontenido.
SECRET_KEY = "clau-secreta-gymreserve-2526"
ALGORITHM = "HS256"
TOKEN_DURADA_MIN = 60 * 24  # el token dura 24 horas

# Le dice a FastAPI de dónde sacar el token (cabecera Authorization: Bearer ...)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def hash_password(password: str) -> str:
    """Convierte la contraseña en un hash bcrypt que es lo que guardamos en la BD."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Comprueba si una contraseña en claro coincide con el hash guardado."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def crear_token(usuari_id: int, rol: str) -> str:
    """Genera un JWT que guarda el id del usuario y su rol."""
    expira = datetime.utcnow() + timedelta(minutes=TOKEN_DURADA_MIN)
    dades = {"sub": str(usuari_id), "rol": rol, "exp": expira}
    return jwt.encode(dades, SECRET_KEY, algorithm=ALGORITHM)


def get_usuari_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Usuario:
    """
    Lee el token, comprueba que es válido y devuelve el usuario de la BD.
    Se usa en los endpoints que requieren estar autenticado.
    """
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token absent o invàlid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        dades = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuari_id = int(dades.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise error

    usuari = db.query(models.Usuario).filter(models.Usuario.id == usuari_id).first()
    if usuari is None:
        raise error
    return usuari


def get_admin_actual(
    usuari: models.Usuario = Depends(get_usuari_actual),
) -> models.Usuario:
    """Igual que la anterior pero además exige rol 'admin' (devuelve 403 si no)."""
    if usuari.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rol insuficient per a aquesta operació",
        )
    return usuari
