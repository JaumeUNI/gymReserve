# GymReserve

Aplicació web de reserva de classes per a un gimnàs. Projecte de l'assignatura
**Arquitectura de Sistemes Web** (ATWSM) — Grup 12.

- **Backend:** Flask (Python)
- **Base de dades:** MySQL (amb SQLAlchemy)
- **Frontend:** HTML + CSS + JavaScript (sense frameworks)
- **Autenticació:** JWT desat en una **cookie**

## Estructura del projecte

```
gymreserve/
├── main.py          # Rutes de l'API Flask (reben la petició i criden el servei)
├── services.py      # LÒGICA DE NEGOCI centralitzada (aforament, duplicats, regles...)
├── auth.py          # Hash de contrasenyes (bcrypt) + JWT en cookie + decoradors de rol
├── serialize.py     # Converteix els objectes de la BD en diccionaris (JSON)
├── errors.py        # Excepció APIError per als errors de negoci
├── database.py      # Connexió a la base de dades MySQL (SQLAlchemy)
├── models.py        # Models / taules: Usuario, Activitat, Classe, Reserva
├── seed.py          # Omple la BD amb dades d'exemple
├── test_api.py      # Proves de l'API (cookies, reserves, admin, permisos)
├── requirements.txt
├── templates/
│   └── index.html   # Pàgina única amb totes les vistes
└── static/
    ├── style.css
    └── app.js       # Lògica del frontend (crides a l'API + navegació)
```

## Arquitectura (separació de capes)

```
  Rutes (main.py)  →  Serveis (services.py)  →  Models / BBDD (models.py)
   "rep la petició"   "aplica les regles"       "fa les consultes SQL"
```

- **main.py** només rep la petició, valida les dades mínimes, comprova el rol
  (amb els decoradors `@login_requerit` / `@admin_requerit`) i crida el servei.
- **services.py** és el cor: comprova l'aforament, evita reserves duplicades, etc.
  Quan una regla falla, llança un `APIError` que main.py converteix en resposta JSON.
- **models.py** defineix les taules de la base de dades.

## Autenticació amb cookies

Quan l'usuari fa login, el servidor genera un token JWT i el desa en una **cookie**
(`Set-Cookie`). El navegador la guarda i la torna a enviar automàticament en cada
petició, així que el frontend no ha de gestionar el token a mà. Al fer logout, el
servidor esborra la cookie.

## Base de dades (MySQL)

La connexió a MySQL està definida a `database.py` (variable `SQLALCHEMY_DATABASE_URL`).
Format de la URL:

```
mysql+pymysql://usuari:contrasenya@servidor:port/nom_bd
```

## Posada en marxa (local o servidor)

```bash
# 1. Instal·lar dependències
pip install -r requirements.txt

# 2. Omplir la base de dades amb dades d'exemple (només el primer cop)
python seed.py

# 3. Arrencar el servidor
python main.py
#    (o bé:  flask --app main run --host 0.0.0.0 --port 8000)

# 4. Obrir al navegador
#    http://127.0.0.1:8000
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

## Funcionalitats

- Registre i login de socis (autenticació JWT en cookie).
- Calendari públic de classes amb filtres (activitat, dia, monitor).
- Reserva i cancel·lació de places amb control d'aforament (sense overbooking).
- Historial de reserves de cada soci.
- Panell d'administració: CRUD d'activitats i classes, veure ocupació.
- Edició del perfil propi.
