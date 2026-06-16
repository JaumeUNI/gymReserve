"""
Configuració de la base de dades.

Ens connectem a MySQL mitjançant SQLAlchemy. La URL de connexió té el format:
    mysql+pymysql://usuari:contrasenya@servidor:port/nom_de_la_bd
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Dades de connexió a la base de dades MySQL.
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://pol:Pol123!!!@localhost:3306/gymreserve"

# pool_pre_ping comprova que la connexió segueix viva abans de fer-la servir
# (evita errors si MySQL ha tancat una connexió inactiva).
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# Cada SessionLocal() és una sessió/connexió a la base de dades.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tots els models heretaran d'aquesta classe Base.
Base = declarative_base()


def get_db():
    """Obre una sessió de BD i la tanca en acabar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
