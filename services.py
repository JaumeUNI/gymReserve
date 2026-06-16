"""
Capa de serveis (lògica de negoci).

Aquest fitxer concentra TOTES les regles de negoci de l'aplicació en un sol lloc.
Els endpoints de main.py no fan res més que rebre la petició i cridar la funció
de servei corresponent; aquí és on es comprova l'aforament, s'eviten reserves
duplicades, es valida que un email sigui únic, etc.

Cada funció rep la sessió de base de dades (db) com a primer paràmetre i s'encarrega
de fer les consultes i d'aplicar les regles. Quan alguna cosa no és vàlida, llança
un APIError amb el codi d'estat adequat (404, 409, etc.), que main.py converteix
automàticament en la resposta d'error.

Organització:
  - Usuaris i autenticació
  - Activitats
  - Classes
  - Reserves
"""
from datetime import datetime
from typing import Optional

from errors import APIError
from sqlalchemy.orm import Session

import models
import auth


# ============================================================
#  USUARIS I AUTENTICACIÓ
# ============================================================

def registrar_usuari(db: Session, nom: str, email: str, password: str) -> models.Usuario:
    """Crea un nou soci. Regla: l'email ha de ser únic al sistema."""
    if db.query(models.Usuario).filter(models.Usuario.email == email).first():
        raise APIError(409, "Aquest email ja està registrat")

    usuari = models.Usuario(
        nom=nom,
        email=email,
        password_hash=auth.hash_password(password),
        rol="soci",
    )
    db.add(usuari)
    db.commit()
    db.refresh(usuari)
    return usuari


def autenticar_usuari(db: Session, email: str, password: str) -> models.Usuario:
    """Comprova les credencials i retorna l'usuari. Regla: email + contrasenya correctes."""
    usuari = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuari or not auth.verify_password(password, usuari.password_hash):
        raise APIError(401, "Credencials incorrectes")
    return usuari


def actualitzar_perfil(db: Session, usuari: models.Usuario,
                       nom: Optional[str], password: Optional[str]) -> models.Usuario:
    """Actualitza el nom i/o la contrasenya. Regla: l'email i el rol no es poden canviar aquí."""
    if nom is not None:
        usuari.nom = nom
    if password is not None:
        usuari.password_hash = auth.hash_password(password)
    db.commit()
    db.refresh(usuari)
    return usuari


def llistar_usuaris(db: Session, page: int, per_page: int, rol: Optional[str]):
    """Llista paginada d'usuaris, opcionalment filtrada per rol."""
    query = db.query(models.Usuario)
    if rol:
        query = query.filter(models.Usuario.rol == rol)
    total = query.count()
    usuaris = query.offset((page - 1) * per_page).limit(per_page).all()
    return usuaris, total


def obtenir_usuari(db: Session, usuari_id: int) -> models.Usuario:
    """Retorna un usuari pel seu ID o llança 404 si no existeix."""
    usuari = db.query(models.Usuario).filter(models.Usuario.id == usuari_id).first()
    if not usuari:
        raise APIError(404, "Usuari no trobat")
    return usuari


def eliminar_usuari(db: Session, usuari_id: int) -> None:
    """Elimina un usuari. Regla: les seves reserves s'esborren juntament amb ell."""
    usuari = obtenir_usuari(db, usuari_id)
    db.query(models.Reserva).filter(models.Reserva.usuari_id == usuari_id).delete()
    db.delete(usuari)
    db.commit()


# ============================================================
#  ACTIVITATS
# ============================================================

def llistar_activitats(db: Session):
    return db.query(models.Activitat).all()


def obtenir_activitat(db: Session, activitat_id: int) -> models.Activitat:
    activitat = db.query(models.Activitat).filter(models.Activitat.id == activitat_id).first()
    if not activitat:
        raise APIError(404, "Activitat no trobada")
    return activitat


def crear_activitat(db: Session, nom: str, descripcio: str, durada_min: int) -> models.Activitat:
    activitat = models.Activitat(nom=nom, descripcio=descripcio, durada_min=durada_min)
    db.add(activitat)
    db.commit()
    db.refresh(activitat)
    return activitat


def actualitzar_activitat(db: Session, activitat_id: int,
                          nom: str, descripcio: str, durada_min: int) -> models.Activitat:
    activitat = obtenir_activitat(db, activitat_id)
    activitat.nom = nom
    activitat.descripcio = descripcio
    activitat.durada_min = durada_min
    db.commit()
    db.refresh(activitat)
    return activitat


def eliminar_activitat(db: Session, activitat_id: int) -> None:
    """Regla: només es pot eliminar si no té classes programades en el futur."""
    activitat = obtenir_activitat(db, activitat_id)
    te_classes_futures = db.query(models.Classe).filter(
        models.Classe.activitat_id == activitat_id,
        models.Classe.data_hora >= datetime.utcnow(),
    ).first()
    if te_classes_futures:
        raise APIError(409, "No es pot eliminar: té classes programades")
    db.delete(activitat)
    db.commit()


# ============================================================
#  CLASSES
# ============================================================

def llistar_classes(db: Session, activitat_id: Optional[int], data: Optional[str],
                    monitor: Optional[str], page: int, per_page: int):
    """Calendari de classes amb filtres opcionals (activitat, dia, monitor)."""
    query = db.query(models.Classe)
    # Només mostrem classes que encara no han passat (futures).
    query = query.filter(models.Classe.data_hora >= datetime.now())

    if activitat_id:
        query = query.filter(models.Classe.activitat_id == activitat_id)
    if monitor:
        query = query.filter(models.Classe.monitor.ilike(f"%{monitor}%"))
    if data:
        try:
            dia = datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            raise APIError(400, "Format de data invàlid")
        fi_del_dia = dia.replace(hour=23, minute=59, second=59)
        query = query.filter(models.Classe.data_hora >= dia,
                            models.Classe.data_hora <= fi_del_dia)

    query = query.order_by(models.Classe.data_hora)
    total = query.count()
    classes = query.offset((page - 1) * per_page).limit(per_page).all()
    return classes, total


def obtenir_classe(db: Session, classe_id: int) -> models.Classe:
    classe = db.query(models.Classe).filter(models.Classe.id == classe_id).first()
    if not classe:
        raise APIError(404, "Classe no trobada")
    return classe


def crear_classe(db: Session, activitat_id: int, monitor: str, sala: str,
                 data_hora: datetime, aforament_max: int) -> models.Classe:
    """Programa una classe nova. Regla: l'activitat ha d'existir; places_lliures comença ple."""
    if not db.query(models.Activitat).filter(models.Activitat.id == activitat_id).first():
        raise APIError(422, "L'activitat no existeix")

    classe = models.Classe(
        activitat_id=activitat_id,
        monitor=monitor,
        sala=sala,
        data_hora=data_hora,
        aforament_max=aforament_max,
        places_lliures=aforament_max,
    )
    db.add(classe)
    db.commit()
    db.refresh(classe)
    return classe


def actualitzar_classe(db: Session, classe_id: int, monitor: str, sala: str,
                       data_hora: datetime, aforament_max: int) -> models.Classe:
    """
    Modifica una classe.
    Regla: no es pot baixar l'aforament per sota de les reserves ja confirmades.
    """
    classe = obtenir_classe(db, classe_id)

    reserves_actuals = db.query(models.Reserva).filter(
        models.Reserva.classe_id == classe_id,
        models.Reserva.estat == "confirmada",
    ).count()
    if aforament_max < reserves_actuals:
        raise APIError(409, "L'aforament no pot ser menor que les reserves actuals")

    classe.monitor = monitor
    classe.sala = sala
    classe.data_hora = data_hora
    classe.aforament_max = aforament_max
    classe.places_lliures = aforament_max - reserves_actuals
    db.commit()
    db.refresh(classe)
    return classe


def eliminar_classe(db: Session, classe_id: int) -> None:
    """Regla: en esborrar una classe, les seves reserves s'esborren també."""
    classe = obtenir_classe(db, classe_id)
    db.query(models.Reserva).filter(models.Reserva.classe_id == classe_id).delete()
    db.delete(classe)
    db.commit()


# ============================================================
#  RESERVES
# ============================================================

def reservar_plaça(db: Session, classe_id: int, usuari: models.Usuario) -> models.Reserva:
    """
    Inscriu un usuari a una classe.
    Regles de negoci:
      1. La classe ha d'existir.
      2. L'usuari no pot tenir ja una reserva confirmada en aquesta classe.
      3. Hi ha d'haver places lliures.
    Si tot va bé, es decrementa places_lliures en 1.
    """
    classe = obtenir_classe(db, classe_id)

    # Regla 2: ja inscrit?
    ja_inscrit = db.query(models.Reserva).filter(
        models.Reserva.usuari_id == usuari.id,
        models.Reserva.classe_id == classe_id,
        models.Reserva.estat == "confirmada",
    ).first()
    if ja_inscrit:
        raise APIError(409, "Ja estàs inscrit en aquesta classe")

    # Regla 3: hi ha lloc?
    if classe.places_lliures <= 0:
        raise APIError(409, "La classe està plena")

    # Si abans havia cancel·lat, reactivem la reserva en comptes de duplicar-la.
    reserva_previa = db.query(models.Reserva).filter(
        models.Reserva.usuari_id == usuari.id,
        models.Reserva.classe_id == classe_id,
    ).first()
    if reserva_previa:
        reserva_previa.estat = "confirmada"
        reserva_previa.data_reserva = datetime.utcnow()
        reserva = reserva_previa
    else:
        reserva = models.Reserva(usuari_id=usuari.id, classe_id=classe_id, estat="confirmada")
        db.add(reserva)

    classe.places_lliures -= 1
    db.commit()
    db.refresh(reserva)
    return reserva


def cancelar_reserva(db: Session, classe_id: int, usuari: models.Usuario) -> models.Reserva:
    """
    Cancel·la la reserva pròpia d'un usuari en una classe.
    Regla: ha d'existir una reserva confirmada; en cancel·lar-la s'allibera una plaça.
    """
    reserva = db.query(models.Reserva).filter(
        models.Reserva.usuari_id == usuari.id,
        models.Reserva.classe_id == classe_id,
        models.Reserva.estat == "confirmada",
    ).first()
    if not reserva:
        raise APIError(404, "No tens cap reserva activa aquí")

    reserva.estat = "cancel·lada"
    classe = db.query(models.Classe).filter(models.Classe.id == classe_id).first()
    if classe:
        classe.places_lliures += 1
    db.commit()
    db.refresh(reserva)
    return reserva


def historial_reserves(db: Session, usuari: models.Usuario,
                       estat: Optional[str], page: int, per_page: int):
    """Historial de reserves d'un usuari (confirmades, cancel·lades, assistides)."""
    query = db.query(models.Reserva).filter(models.Reserva.usuari_id == usuari.id)
    if estat:
        query = query.filter(models.Reserva.estat == estat)
    query = query.order_by(models.Reserva.data_reserva.desc())
    total = query.count()
    reserves = query.offset((page - 1) * per_page).limit(per_page).all()
    return reserves, total


def llistar_inscrits(db: Session, classe_id: int):
    """Llista d'inscrits en una classe (per a l'administrador)."""
    obtenir_classe(db, classe_id)   # valida que la classe existeix (404 si no)
    return db.query(models.Reserva).filter(models.Reserva.classe_id == classe_id).all()
