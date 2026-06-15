"""
Datos de ejemplo.

Ejecuta este script una vez (python seed.py) para llenar la base de datos con
un administrador, un socio y unas cuantas clases, y así poder probar la app
sin tener que crear todo a mano.

Credenciales creadas:
  admin@gym.cat  / admin123   (rol admin)
  pol@gym.cat    / pol123     (rol soci)
"""
from datetime import datetime, timedelta

from database import SessionLocal, engine, Base
import models
import auth

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Empezamos de cero para que el script se pueda repetir sin duplicar.
db.query(models.Reserva).delete()
db.query(models.Classe).delete()
db.query(models.Activitat).delete()
db.query(models.Usuario).delete()
db.commit()

# --- Usuarios ---
admin = models.Usuario(
    nom="Administrador",
    email="admin@gym.cat",
    password_hash=auth.hash_password("admin123"),
    rol="admin",
)
soci = models.Usuario(
    nom="Pol Garcia",
    email="pol@gym.cat",
    password_hash=auth.hash_password("pol123"),
    rol="soci",
)
db.add_all([admin, soci])
db.commit()

# --- Actividades ---
yoga = models.Activitat(nom="Yoga", descripcio="Classe dinàmica de yoga vinyasa.", durada_min=60)
spinning = models.Activitat(nom="Spinning", descripcio="Bici indoor d'alta intensitat.", durada_min=45)
pilates = models.Activitat(nom="Pilates", descripcio="Treball de força i flexibilitat.", durada_min=55)
db.add_all([yoga, spinning, pilates])
db.commit()

# --- Clases (próximos días) ---
ara = datetime.now().replace(minute=0, second=0, microsecond=0)
classes = [
    models.Classe(activitat_id=yoga.id, monitor="Ana García", sala="Sala 1",
                  data_hora=ara + timedelta(days=1, hours=2),
                  aforament_max=15, places_lliures=15),
    models.Classe(activitat_id=spinning.id, monitor="Marc Soler", sala="Sala 2",
                  data_hora=ara + timedelta(days=1, hours=4),
                  aforament_max=12, places_lliures=12),
    models.Classe(activitat_id=pilates.id, monitor="Laia Roca", sala="Sala 1",
                  data_hora=ara + timedelta(days=2, hours=3),
                  aforament_max=10, places_lliures=10),
    models.Classe(activitat_id=yoga.id, monitor="Ana García", sala="Sala 1",
                  data_hora=ara + timedelta(days=3, hours=1),
                  aforament_max=15, places_lliures=15),
]
db.add_all(classes)
db.commit()

print("Base de dades poblada correctament.")
print("  Admin:  admin@gym.cat / admin123")
print("  Soci:   pol@gym.cat   / pol123")
db.close()
