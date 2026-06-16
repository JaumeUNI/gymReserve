"""
Proves de l'API de GymReserve (versió Flask).

S'executa amb:  python test_api.py
Fa servir el client de proves de Flask, que guarda les cookies automàticament
entre peticions (com un navegador), així que no cal gestionar el token a mà.

Comprova: autenticació amb cookies, reserves amb control d'aforament,
panell d'admin i permisos (401 / 403 / 409).
"""
import main

c = main.app.test_client()

print("=== AUTENTICACIO AMB COOKIES ===")
r = c.get("/api/v1/usuaris/me")
print("1. /me sense login (espera 401):", r.status_code)
r = c.post("/api/v1/auth/login", json={"email": "pol@gym.cat", "password": "pol123"})
print("2. Login:", r.status_code, "| cookie rebuda:", "token" in r.headers.get("Set-Cookie", ""))
r = c.get("/api/v1/usuaris/me")
print("3. /me despres de login:", r.status_code, "| usuari:", r.get_json().get("nom"))

print("\n=== FLUX SOCI ===")
r = c.get("/api/v1/classes"); d = r.get_json()
print("4. Calendari:", r.status_code, "| classes:", d["total"])
r = c.post("/api/v1/classes/1/reserves"); print("5. Reserva:", r.status_code, r.get_json()["estat"])
r = c.get("/api/v1/classes/1"); print("6. Places lliures:", r.get_json()["places_lliures"])
r = c.post("/api/v1/classes/1/reserves"); print("7. Doble reserva (espera 409):", r.status_code)
r = c.get("/api/v1/usuaris/me/reserves"); print("8. Historial total:", r.get_json()["total"])
r = c.delete("/api/v1/classes/1/reserves"); print("9. Cancel·lar:", r.status_code, r.get_json()["estat"])

print("\n=== PERMISOS ===")
r = c.get("/api/v1/usuaris"); print("10. Soci llista usuaris (espera 403):", r.status_code)
r = c.post("/api/v1/auth/logout"); print("11. Logout:", r.status_code)
r = c.get("/api/v1/usuaris/me"); print("12. /me despres de logout (espera 401):", r.status_code)

print("\n=== ADMIN ===")
r = c.post("/api/v1/auth/login", json={"email": "admin@gym.cat", "password": "admin123"})
print("13. Login admin:", r.status_code)
r = c.post("/api/v1/activitats", json={"nom": "Zumba", "descripcio": "Ball", "durada_min": 50})
print("14. Crear activitat:", r.status_code, r.get_json()["nom"])
r = c.get("/api/v1/usuaris"); print("15. Llistar usuaris:", r.status_code, "total:", r.get_json()["total"])

print("\nTOT OK")
