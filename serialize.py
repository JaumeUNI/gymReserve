"""
Serialització (objectes -> diccionaris).

A FastAPI els schemas de Pydantic s'encarregaven de convertir els objectes de la
base de dades en JSON i de decidir quins camps es mostraven. A Flask ho fem amb
aquestes funcions: reben un objecte de SQLAlchemy i retornen un diccionari net
(per exemple, mai retornem el password_hash de l'usuari).
"""


def usuari_dict(u):
    return {
        "id": u.id,
        "nom": u.nom,
        "email": u.email,
        "rol": u.rol,
        "data_alta": u.data_alta.isoformat() if u.data_alta else None,
    }


def activitat_dict(a):
    return {
        "id": a.id,
        "nom": a.nom,
        "descripcio": a.descripcio,
        "durada_min": a.durada_min,
    }


def classe_dict(c):
    return {
        "id": c.id,
        "activitat_id": c.activitat_id,
        "monitor": c.monitor,
        "sala": c.sala,
        "data_hora": c.data_hora.isoformat() if c.data_hora else None,
        "aforament_max": c.aforament_max,
        "places_lliures": c.places_lliures,
        "activitat": activitat_dict(c.activitat) if c.activitat else None,
    }


def reserva_dict(r):
    return {
        "id": r.id,
        "usuari_id": r.usuari_id,
        "classe_id": r.classe_id,
        "data_reserva": r.data_reserva.isoformat() if r.data_reserva else None,
        "estat": r.estat,
    }


def reserva_historial_dict(r):
    """Reserva amb la informació de la classe inclosa (per a l'historial del soci)."""
    return {
        "id": r.id,
        "classe": classe_dict(r.classe),
        "data_reserva": r.data_reserva.isoformat() if r.data_reserva else None,
        "estat": r.estat,
    }


def inscrit_dict(r):
    """El que veu l'admin en consultar qui està inscrit en una classe."""
    return {
        "reserva_id": r.id,
        "usuari": usuari_dict(r.usuari),
        "estat": r.estat,
        "data_reserva": r.data_reserva.isoformat() if r.data_reserva else None,
    }
