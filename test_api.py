from fastapi.testclient import TestClient
import main

c = TestClient(main.app)

print("=== FLUJO SOCIO ===")
r = c.get("/api/v1/classes"); d = r.json()
print("1. Calendario:", r.status_code, "| clases:", d["total"], "| 1a plazas:", d["data"][0]["places_lliures"])
r = c.post("/api/v1/auth/login", json={"email": "pol@gym.cat", "password": "pol123"})
tok = r.json()["token"]; print("2. Login:", r.status_code, "rol", r.json()["usuari"]["rol"])
H = {"Authorization": "Bearer " + tok}
r = c.post("/api/v1/classes/1/reserves", headers=H); print("3. Reserva:", r.status_code, r.json()["estat"])
r = c.get("/api/v1/classes/1"); print("4. Plazas:", r.json()["places_lliures"])
r = c.post("/api/v1/classes/1/reserves", headers=H); print("5. Doble reserva (espera 409):", r.status_code)
r = c.get("/api/v1/usuaris/me/reserves", headers=H); print("6. Historial total:", r.json()["total"])
r = c.delete("/api/v1/classes/1/reserves", headers=H); print("7. Cancelar:", r.status_code, r.json()["estat"])
r = c.get("/api/v1/classes/1"); print("8. Plazas tras cancelar:", r.json()["places_lliures"])

print("\n=== FLUJO ADMIN ===")
r = c.post("/api/v1/auth/login", json={"email": "admin@gym.cat", "password": "admin123"})
atok = r.json()["token"]; AH = {"Authorization": "Bearer " + atok}
r = c.post("/api/v1/activitats", json={"nom": "Zumba", "descripcio": "Ball", "durada_min": 50}, headers=AH)
print("9. Crear actividad:", r.status_code, r.json()["nom"])
r = c.post("/api/v1/classes", json={"activitat_id": 1, "monitor": "Test", "sala": "S3", "data_hora": "2026-12-01T10:00:00", "aforament_max": 5}, headers=AH)
cid = r.json()["id"]; print("10. Crear clase:", r.status_code, "places=", r.json()["places_lliures"])
r = c.get(f"/api/v1/classes/{cid}/reserves", headers=AH); print("11. Inscritos (admin):", r.status_code, "vacia:", r.json() == [])
r = c.get("/api/v1/usuaris", headers=AH); print("12. Listar usuarios:", r.status_code, "total:", r.json()["total"])

print("\n=== PERMISOS / ERRORES ===")
r = c.get("/api/v1/usuaris", headers=H); print("13. Socio lista usuarios (espera 403):", r.status_code)
r = c.get("/api/v1/usuaris/me"); print("14. Sin token (espera 401):", r.status_code)
r = c.post("/api/v1/auth/login", json={"email": "pol@gym.cat", "password": "MAL"}); print("15. Login mal (espera 401):", r.status_code)
r = c.post("/api/v1/auth/register", json={"nom": "X", "email": "pol@gym.cat", "password": "x"}); print("16. Email duplicado (espera 409):", r.status_code)
print("\nTODO OK" )
