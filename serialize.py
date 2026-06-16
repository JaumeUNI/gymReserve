"""
Aquí convertim els objectes de la base de dades en diccionaris.

Quan demanem coses a la base de dades (un usuari, una classe...), ens tornen
objectes de Python que no es poden enviar directament al navegador. Aquestes
funcions agafen aquests objectes i els transformen en diccionaris senzills,
que després s'envien com a JSON.

També ens serveix per decidir què ensenyem i què no: per exemple, mai enviem
la contrasenya de l'usuari, encara que la tinguem guardada.
"""
from datetime import datetime


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
    """
    Reserva amb la informació de la classe inclosa (per a l'historial del soci).
    Si la reserva està confirmada i la classe ja ha passat, es mostra com a "assistida".
    """
    estat = r.estat
    if estat == "confirmada" and r.classe and r.classe.data_hora < datetime.now():
        estat = "assistida"

    return {
        "id": r.id,
        "classe": classe_dict(r.classe),
        "data_reserva": r.data_reserva.isoformat() if r.data_reserva else None,
        "estat": estat,
    }


def inscrit_dict(r):
    """El que veu l'admin en consultar qui està inscrit en una classe."""
    return {
        "reserva_id": r.id,
        "usuari": usuari_dict(r.usuari),
        "estat": r.estat,
        "data_reserva": r.data_reserva.isoformat() if r.data_reserva else None,
    }
