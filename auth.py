"""
Autenticació i seguretat (versió Flask).

Aquí hi ha tot el relacionat amb contrasenyes i tokens:
  - hashejar / verificar contrasenyes amb bcrypt
  - crear i llegir tokens JWT
  - decoradors per protegir rutes: @login_requerit (soci) i @admin_requerit (admin)

El token JWT viatja dins d'una COOKIE anomenada "token". Quan l'usuari fa login,
el servidor desa el token a la cookie; el navegador la torna a enviar
automàticament en cada petició. Així no cal que el frontend gestioni el token a mà.
"""
from datetime import datetime, timedelta
from functools import wraps

from flask import request, g, jsonify
from jose import JWTError, jwt
import bcrypt

from database import SessionLocal
import models

# Clau per signar els tokens. En un projecte real aniria en una variable
# d'entorn; aquí la deixem fixa perquè l'exemple sigui autocontingut.
SECRET_KEY = "clau-secreta-gymreserve-2526"
ALGORITHM = "HS256"
TOKEN_DURADA_MIN = 60 * 24  # el token dura 24 hores
COOKIE_NAME = "token"       # nom de la cookie on viatja el JWT


def hash_password(password: str) -> str:
    """Converteix la contrasenya en un hash bcrypt, que és el que desem a la BD."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Comprova si una contrasenya en clar coincideix amb el hash desat."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def crear_token(usuari_id: int, rol: str) -> str:
    """Genera un JWT que desa l'id de l'usuari i el seu rol."""
    expira = datetime.utcnow() + timedelta(minutes=TOKEN_DURADA_MIN)
    dades = {"sub": str(usuari_id), "rol": rol, "exp": expira}
    return jwt.encode(dades, SECRET_KEY, algorithm=ALGORITHM)


def _usuari_des_de_cookie():
    """
    Llegeix el token de la cookie, el valida i retorna l'usuari de la BD.
    Retorna None si no hi ha token o no és vàlid.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        dades = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuari_id = int(dades.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None

    db = SessionLocal()
    try:
        return db.query(models.Usuario).filter(models.Usuario.id == usuari_id).first()
    finally:
        db.close()


def login_requerit(f):
    """
    Decorador per a rutes que necessiten estar autenticat.
    Si no hi ha sessió vàlida, retorna 401. Si n'hi ha, desa l'usuari a g.usuari
    perquè la ruta el pugui fer servir.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        usuari = _usuari_des_de_cookie()
        if usuari is None:
            return jsonify({"detail": "Token absent o invàlid"}), 401
        g.usuari = usuari
        return f(*args, **kwargs)
    return wrapper


def admin_requerit(f):
    """Igual que login_requerit però a més exigeix rol 'admin' (retorna 403 si no)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        usuari = _usuari_des_de_cookie()
        if usuari is None:
            return jsonify({"detail": "Token absent o invàlid"}), 401
        if usuari.rol != "admin":
            return jsonify({"detail": "Rol insuficient per a aquesta operació"}), 403
        g.usuari = usuari
        return f(*args, **kwargs)
    return wrapper
