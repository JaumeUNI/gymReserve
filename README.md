# GymReserve

Aplicació web de reserva de classes per a un gimnàs. Projecte de l'assignatura
**Arquitectura de Sistemes Web** (ATWSM) — Grup 12.

- **Backend:** FastAPI (Python)
- **Base de dades:** SQLite (fitxer `gymreserve.db`)
- **Frontend:** HTML + CSS + JavaScript
- **Autenticació:** JWT (JSON Web Tokens)

## Estructura del projecte

```
gymreserve/
├── main.py          # Endpoints de l'API (només reben la petició i criden el servei)
├── services.py      # LÒGICA DE NEGOCI centralitzada (aforament, duplicats, regles...)
├── database.py      # Connexió a la base de dades (SQLAlchemy)
├── models.py        # Models / taules: Usuario, Activitat, Classe, Reserva
├── schemas.py       # Schemas Pydantic (validació d'entrada i sortida)
├── auth.py          # Hash de contrasenyes (bcrypt) i tokens JWT
├── seed.py          # Omple la BD amb dades d'exemple
├── test_api.py      # Proves de l'API (flux soci, admin, permisos)
├── requirements.txt
├── templates/
│   └── index.html   # Pàgina única amb totes les vistes
└── static/
    ├── style.css
    └── app.js       # Lògica del frontend (crides a l'API + navegació)
```

## Arquitectura (separació de capes)

El backend està organitzat en capes perquè la lògica de negoci estigui en un sol lloc:

```
  Endpoints (main.py)  →  Serveis (services.py)  →  Models / BBDD (models.py)
     "rep la petició"      "aplica les regles"       "fa les consultes SQL"
```

- **main.py** només rep la petició, comprova el rol i crida el servei. No conté regles.
- **services.py** és el cor: comprova l'aforament, evita reserves duplicades,
  valida que un email sigui únic, decrementa places, etc. Si una regla canvia,
  es toca aquí i només aquí.
- **models.py** defineix les taules de la base de dades.

## Com posar-lo en marxa

```bash
# 1. Instal·lar dependències
pip install -r requirements.txt

# 2. Omplir la base de dades amb dades d'exemple
python seed.py

# 3. Arrencar el servidor
uvicorn main:app --reload

# 4. Obrir al navegador
#    http://127.0.0.1:8000          → l'aplicació
#    http://127.0.0.1:8000/docs     → documentació interactiva de l'API (Swagger)
```

## Usuaris d'exemple

| Rol   | Email           | Contrasenya |
|-------|-----------------|-------------|
| Admin | admin@gym.cat   | admin123    |
| Soci  | pol@gym.cat     | pol123      |

## Provar l'API

```bash
python test_api.py
```

Comprova el flux complet: calendari públic, login, reserva amb control d'aforament,
historial, cancel·lació, CRUD d'admin i els permisos (401 / 403 / 409).

## Funcionalitats

- Registre i login de socis (autenticació JWT).
- Calendari públic de classes amb filtres (activitat, dia, monitor).
- Reserva i cancel·lació de places amb control d'aforament (sense overbooking).
- Historial de reserves de cada soci.
- Panell d'administració: CRUD d'activitats i classes, veure ocupació.
- Edició del perfil propi.
```
```
