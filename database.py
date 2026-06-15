"""
Configuración de la base de datos.

Usamos SQLite (un único fichero gymreserve.db) para que el proyecto se pueda
arrancar sin instalar ningún servidor de base de datos. SQLAlchemy se encarga
de traducir nuestras clases Python a tablas SQL.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# La base de datos es un fichero local llamado gymreserve.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./gymreserve.db"

# check_same_thread=False es necesario en SQLite cuando se usa con FastAPI,
# porque cada petición puede atenderse desde un hilo distinto.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Cada SessionLocal() es una sesión/conexión a la base de datos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Todos los modelos heredarán de esta clase Base.
Base = declarative_base()


def get_db():
    """
    Dependencia de FastAPI: abre una sesión de BD para la petición y la cierra
    al terminar. Se usa con Depends(get_db) en cada endpoint que toque la BD.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
