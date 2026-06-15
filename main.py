
"""
GymReserve — API i servidor de l'aplicació.

Aquest fitxer només defineix els endpoints (la "porta d'entrada" de l'API) i
serveix les pàgines HTML. Cada endpoint fa tres coses i prou:
  1. Rep la petició (i comprova el rol amb les dependències d'auth).
  2. Crida la funció corresponent de services.py (on viu la lògica de negoci).
  3. Retorna la resposta.

Tota la lògica (comprovar aforament, evitar duplicats, validar regles...) està
centralitzada a services.py. Així, si cal canviar una regla, es toca en un sol lloc.

Per arrencar:  uvicorn main:app --reload
Després obrir: http://127.0.0.1:8000
"""
from typing import Optional, List

from fastapi import FastAPI, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

import models
import schemas
import auth
import services
from database import engine, get_db, Base

# Crea les taules a la base de dades el primer cop que s'arrenca.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GymReserve API", version="1.0")


# ============================================================
#  1. AUTENTICACIÓ
# ============================================================

@app.post("/api/v1/auth/register", response_model=schemas.UsuariOut, status_code=201)
def register(dades: schemas.UsuariRegistre, db: Session = Depends(get_db)):
    """Registra un nou usuari amb rol 'soci'. L'email ha de ser únic."""
    return services.registrar_usuari(db, dades.nom, dades.email, dades.password)


@app.post("/api/v1/auth/login", response_model=schemas.LoginResposta)
def login(dades: schemas.UsuariLogin, db: Session = Depends(get_db)):
    """Comprova les credencials i retorna un token JWT."""
    usuari = services.autenticar_usuari(db, dades.email, dades.password)
    token = auth.crear_token(usuari.id, usuari.rol)
    return {"token": token, "usuari": usuari}


@app.post("/api/v1/auth/logout", status_code=204)
def logout(usuari: models.Usuario = Depends(auth.get_usuari_actual)):
    """
    Tanca la sessió. Amb JWT sense estat, el tancament real es fa al client
    esborrant el token; aquí només confirmem que el token era vàlid.
    """
    return


# ============================================================
#  2. USUARIS
# ============================================================

@app.get("/api/v1/usuaris/me", response_model=schemas.UsuariOut)
def get_perfil(usuari: models.Usuario = Depends(auth.get_usuari_actual)):
    """Retorna el perfil de l'usuari autenticat."""
    return usuari


@app.put("/api/v1/usuaris/me", response_model=schemas.UsuariOut)
def update_perfil(
    dades: schemas.UsuariUpdate,
    usuari: models.Usuario = Depends(auth.get_usuari_actual),
    db: Session = Depends(get_db),
):
    """Actualitza el nom i/o la contrasenya propis."""
    return services.actualitzar_perfil(db, usuari, dades.nom, dades.password)


@app.get("/api/v1/usuaris")
def llistar_usuaris(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    rol: Optional[str] = None,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    """(Admin) Llista paginada d'usuaris, opcionalment filtrada per rol."""
    usuaris, total = services.llistar_usuaris(db, page, per_page, rol)
    return {
        "data": [schemas.UsuariOut.model_validate(u) for u in usuaris],
        "total": total, "page": page, "per_page": per_page,
    }


@app.get("/api/v1/usuaris/{id}", response_model=schemas.UsuariOut)
def get_usuari(
    id: int,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    """(Admin) Retorna un usuari pel seu ID."""
    return services.obtenir_usuari(db, id)


@app.delete("/api/v1/usuaris/{id}", status_code=204)
def delete_usuari(
    id: int,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    """(Admin) Elimina un usuari i les seves reserves."""
    services.eliminar_usuari(db, id)
    return


# ============================================================
#  3. ACTIVITATS
# ============================================================

@app.get("/api/v1/activitats", response_model=List[schemas.ActivitatOut])
def llistar_activitats(db: Session = Depends(get_db)):
    """Catàleg públic d'activitats."""
    return services.llistar_activitats(db)


@app.get("/api/v1/activitats/{id}", response_model=schemas.ActivitatOut)
def get_activitat(id: int, db: Session = Depends(get_db)):
    return services.obtenir_activitat(db, id)


@app.post("/api/v1/activitats", response_model=schemas.ActivitatOut, status_code=201)
def crear_activitat(
    dades: schemas.ActivitatIn,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    return services.crear_activitat(db, dades.nom, dades.descripcio, dades.durada_min)


@app.put("/api/v1/activitats/{id}", response_model=schemas.ActivitatOut)
def update_activitat(
    id: int,
    dades: schemas.ActivitatIn,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    return services.actualitzar_activitat(db, id, dades.nom, dades.descripcio, dades.durada_min)


@app.delete("/api/v1/activitats/{id}", status_code=204)
def delete_activitat(
    id: int,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    services.eliminar_activitat(db, id)
    return


# ============================================================
#  4. CLASSES
# ============================================================

@app.get("/api/v1/classes")
def llistar_classes(
    activitat_id: Optional[int] = None,
    data: Optional[str] = None,        # format YYYY-MM-DD
    monitor: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Calendari públic de classes, amb filtres opcionals."""
    classes, total = services.llistar_classes(db, activitat_id, data, monitor, page, per_page)
    return {
        "data": [schemas.ClasseOut.model_validate(c) for c in classes],
        "total": total, "page": page, "per_page": per_page,
    }


@app.get("/api/v1/classes/{id}", response_model=schemas.ClasseOut)
def get_classe(id: int, db: Session = Depends(get_db)):
    return services.obtenir_classe(db, id)


@app.post("/api/v1/classes", response_model=schemas.ClasseOut, status_code=201)
def crear_classe(
    dades: schemas.ClasseIn,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    return services.crear_classe(
        db, dades.activitat_id, dades.monitor, dades.sala, dades.data_hora, dades.aforament_max
    )


@app.put("/api/v1/classes/{id}", response_model=schemas.ClasseOut)
def update_classe(
    id: int,
    dades: schemas.ClasseUpdate,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    return services.actualitzar_classe(
        db, id, dades.monitor, dades.sala, dades.data_hora, dades.aforament_max
    )


@app.delete("/api/v1/classes/{id}", status_code=204)
def delete_classe(
    id: int,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    services.eliminar_classe(db, id)
    return


# ============================================================
#  5. RESERVES
# ============================================================

@app.post("/api/v1/classes/{id}/reserves", response_model=schemas.ReservaOut, status_code=201)
def inscriure(
    id: int,
    usuari: models.Usuario = Depends(auth.get_usuari_actual),
    db: Session = Depends(get_db),
):
    """Inscriu l'usuari autenticat a la classe."""
    return services.reservar_plaça(db, id, usuari)


@app.delete("/api/v1/classes/{id}/reserves", response_model=schemas.ReservaOut)
def cancelar(
    id: int,
    usuari: models.Usuario = Depends(auth.get_usuari_actual),
    db: Session = Depends(get_db),
):
    """Cancel·la la reserva pròpia a la classe."""
    return services.cancelar_reserva(db, id, usuari)


@app.get("/api/v1/usuaris/me/reserves")
def historial(
    estat: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    usuari: models.Usuario = Depends(auth.get_usuari_actual),
    db: Session = Depends(get_db),
):
    """Historial de reserves de l'usuari autenticat."""
    reserves, total = services.historial_reserves(db, usuari, estat, page, per_page)
    return {
        "data": [schemas.ReservaHistorial.model_validate(r) for r in reserves],
        "total": total, "page": page, "per_page": per_page,
    }


@app.get("/api/v1/classes/{id}/reserves", response_model=List[schemas.InscritOut])
def inscrits(
    id: int,
    admin: models.Usuario = Depends(auth.get_admin_actual),
    db: Session = Depends(get_db),
):
    """(Admin) Llista de socis inscrits en una classe."""
    reserves = services.llistar_inscrits(db, id)
    return [
        schemas.InscritOut(
            reserva_id=r.id,
            usuari=schemas.UsuariOut.model_validate(r.usuari),
            estat=r.estat,
            data_reserva=r.data_reserva,
        )
        for r in reserves
    ]


# ============================================================
#  FRONTEND (serveix les pàgines HTML)
# ============================================================

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("templates/index.html")
