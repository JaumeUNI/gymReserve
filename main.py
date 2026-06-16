"""
GymReserve — API i servidor de l'aplicació (versió Flask).

Aquest fitxer defineix totes les rutes de l'API i serveix les pàgines HTML.
Cada ruta fa tres coses:
  1. Rep la petició (i comprova el rol amb els decoradors d'auth).
  2. Crida la funció corresponent de services.py (on viu la lògica de negoci).
  3. Retorna la resposta en JSON.

Tota la lògica de negoci està centralitzada a services.py. Les rutes només validen
les dades mínimes d'entrada i deleguen.

Per arrencar:  flask --app main run   (o bé:  python main.py)
Després obrir: http://127.0.0.1:8000
"""
from flask import Flask, request, jsonify, g, send_from_directory, make_response

import models
import auth
import services
import serialize as S
from errors import APIError
from database import engine, SessionLocal, Base

# Crea les taules a la base de dades el primer cop.
Base.metadata.create_all(bind=engine)

app = Flask(__name__, static_folder="static", template_folder="templates")


# Obrim una sessió de BD per a cada petició i la tanquem en acabar.
@app.before_request
def obrir_db():
    g.db = SessionLocal()


@app.teardown_request
def tancar_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# Quan un servei llança un APIError, el convertim en una resposta JSON amb el codi.
@app.errorhandler(APIError)
def gestionar_api_error(err):
    return jsonify({"detail": err.message}), err.status_code


# ============================================================
#  1. AUTENTICACIÓ
# ============================================================

@app.post("/api/v1/auth/register")
def register():
    dades = request.get_json(silent=True) or {}
    nom = dades.get("nom")
    email = dades.get("email")
    password = dades.get("password")
    if not nom or not email or not password:
        raise APIError(422, "Falten camps obligatoris (nom, email, password)")

    usuari = services.registrar_usuari(g.db, nom, email, password)
    return jsonify(S.usuari_dict(usuari)), 201


@app.post("/api/v1/auth/login")
def login():
    dades = request.get_json(silent=True) or {}
    email = dades.get("email")
    password = dades.get("password")
    if not email or not password:
        raise APIError(422, "Falten l'email o la contrasenya")

    usuari = services.autenticar_usuari(g.db, email, password)
    token = auth.crear_token(usuari.id, usuari.rol)

    # Desa el token en una cookie. El navegador la tornarà a enviar sola.
    resposta = make_response(jsonify({"token": token, "usuari": S.usuari_dict(usuari)}))
    resposta.set_cookie(
        auth.COOKIE_NAME, token,
        httponly=True,                       # el JS del navegador no pot llegir-la
        max_age=auth.TOKEN_DURADA_MIN * 60,  # durada en segons
        samesite="Lax",
    )
    return resposta


@app.post("/api/v1/auth/logout")
@auth.login_requerit
def logout():
    """Tanca la sessió esborrant la cookie del token."""
    resposta = make_response("", 204)
    resposta.delete_cookie(auth.COOKIE_NAME)
    return resposta


# ============================================================
#  2. USUARIS
# ============================================================

@app.get("/api/v1/usuaris/me")
@auth.login_requerit
def get_perfil():
    return jsonify(S.usuari_dict(g.usuari))


@app.put("/api/v1/usuaris/me")
@auth.login_requerit
def update_perfil():
    dades = request.get_json(silent=True) or {}
    usuari = services.actualitzar_perfil(g.db, g.usuari, dades.get("nom"), dades.get("password"))
    return jsonify(S.usuari_dict(usuari))


@app.get("/api/v1/usuaris")
@auth.admin_requerit
def llistar_usuaris():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    rol = request.args.get("rol")
    usuaris, total = services.llistar_usuaris(g.db, page, per_page, rol)
    return jsonify({
        "data": [S.usuari_dict(u) for u in usuaris],
        "total": total, "page": page, "per_page": per_page,
    })


@app.get("/api/v1/usuaris/<int:id>")
@auth.admin_requerit
def get_usuari(id):
    return jsonify(S.usuari_dict(services.obtenir_usuari(g.db, id)))


@app.delete("/api/v1/usuaris/<int:id>")
@auth.admin_requerit
def delete_usuari(id):
    services.eliminar_usuari(g.db, id)
    return "", 204


# ============================================================
#  3. ACTIVITATS
# ============================================================

@app.get("/api/v1/activitats")
def llistar_activitats():
    activitats = services.llistar_activitats(g.db)
    return jsonify([S.activitat_dict(a) for a in activitats])


@app.get("/api/v1/activitats/<int:id>")
def get_activitat(id):
    return jsonify(S.activitat_dict(services.obtenir_activitat(g.db, id)))


@app.post("/api/v1/activitats")
@auth.admin_requerit
def crear_activitat():
    dades = request.get_json(silent=True) or {}
    nom = dades.get("nom")
    if not nom:
        raise APIError(422, "El nom de l'activitat és obligatori")
    activitat = services.crear_activitat(
        g.db, nom, dades.get("descripcio", ""), int(dades.get("durada_min", 60))
    )
    return jsonify(S.activitat_dict(activitat)), 201


@app.put("/api/v1/activitats/<int:id>")
@auth.admin_requerit
def update_activitat(id):
    dades = request.get_json(silent=True) or {}
    nom = dades.get("nom")
    if not nom:
        raise APIError(422, "El nom de l'activitat és obligatori")
    activitat = services.actualitzar_activitat(
        g.db, id, nom, dades.get("descripcio", ""), int(dades.get("durada_min", 60))
    )
    return jsonify(S.activitat_dict(activitat))


@app.delete("/api/v1/activitats/<int:id>")
@auth.admin_requerit
def delete_activitat(id):
    services.eliminar_activitat(g.db, id)
    return "", 204


# ============================================================
#  4. CLASSES
# ============================================================

@app.get("/api/v1/classes")
def llistar_classes():
    activitat_id = request.args.get("activitat_id", type=int)
    data = request.args.get("data")
    monitor = request.args.get("monitor")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    classes, total = services.llistar_classes(g.db, activitat_id, data, monitor, page, per_page)
    return jsonify({
        "data": [S.classe_dict(c) for c in classes],
        "total": total, "page": page, "per_page": per_page,
    })


@app.get("/api/v1/classes/<int:id>")
def get_classe(id):
    return jsonify(S.classe_dict(services.obtenir_classe(g.db, id)))


@app.post("/api/v1/classes")
@auth.admin_requerit
def crear_classe():
    dades = request.get_json(silent=True) or {}
    obligatoris = ("activitat_id", "monitor", "sala", "data_hora", "aforament_max")
    if not all(dades.get(camp) for camp in obligatoris):
        raise APIError(422, "Falten camps obligatoris de la classe")
    classe = services.crear_classe(
        g.db, int(dades["activitat_id"]), dades["monitor"], dades["sala"],
        dades["data_hora"], int(dades["aforament_max"]),
    )
    return jsonify(S.classe_dict(classe)), 201


@app.put("/api/v1/classes/<int:id>")
@auth.admin_requerit
def update_classe(id):
    dades = request.get_json(silent=True) or {}
    obligatoris = ("monitor", "sala", "data_hora", "aforament_max")
    if not all(dades.get(camp) for camp in obligatoris):
        raise APIError(422, "Falten camps obligatoris de la classe")
    classe = services.actualitzar_classe(
        g.db, id, dades["monitor"], dades["sala"],
        dades["data_hora"], int(dades["aforament_max"]),
    )
    return jsonify(S.classe_dict(classe))


@app.delete("/api/v1/classes/<int:id>")
@auth.admin_requerit
def delete_classe(id):
    services.eliminar_classe(g.db, id)
    return "", 204


# ============================================================
#  5. RESERVES
# ============================================================

@app.post("/api/v1/classes/<int:id>/reserves")
@auth.login_requerit
def inscriure(id):
    reserva = services.reservar_plaça(g.db, id, g.usuari)
    return jsonify(S.reserva_dict(reserva)), 201


@app.delete("/api/v1/classes/<int:id>/reserves")
@auth.login_requerit
def cancelar(id):
    reserva = services.cancelar_reserva(g.db, id, g.usuari)
    return jsonify(S.reserva_dict(reserva))


@app.get("/api/v1/usuaris/me/reserves")
@auth.login_requerit
def historial():
    estat = request.args.get("estat")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    reserves, total = services.historial_reserves(g.db, g.usuari, estat, page, per_page)
    return jsonify({
        "data": [S.reserva_historial_dict(r) for r in reserves],
        "total": total, "page": page, "per_page": per_page,
    })


@app.get("/api/v1/classes/<int:id>/reserves")
@auth.admin_requerit
def inscrits(id):
    reserves = services.llistar_inscrits(g.db, id)
    return jsonify([S.inscrit_dict(r) for r in reserves])


# ============================================================
#  FRONTEND (serveix les pàgines HTML)
# ============================================================

@app.get("/")
def home():
    return send_from_directory("templates", "index.html")


if __name__ == "__main__":
    # Arrencada directa amb: python main.py
    app.run(host="0.0.0.0", port=8000, debug=True)
