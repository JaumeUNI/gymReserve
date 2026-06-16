# GymReserve

Aplicació web de reserva de classes per a un gimnàs. Projecte de l'assignatura
**Arquitectura de Sistemes Web** (ATWSM) — Grup 12 (Pol Garcia i Jaume Casamitjana).

Els socis consulten el calendari de classes (yoga, spinning, pilates...), s'hi
inscriuen respectant l'aforament i consulten el seu historial d'assistència. Els
administradors gestionen activitats, classes i veuen l'ocupació de cada sessió.

- **Backend:** Flask (Python)
- **Base de dades:** MySQL (amb SQLAlchemy)
- **Frontend:** HTML + CSS + JavaScript (sense frameworks)
- **Autenticació:** JWT desat en una **cookie**
- **Desplegament:** màquina virtual Linux a Azure, amb HTTPS

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

El backend està organitzat en capes, cadascuna amb una única responsabilitat.
Una petició passa per aquestes capes:

```
  PETICIÓ
     │
     ▼
  main.py        rep la petició, comprova el rol i valida les dades mínimes
     │
     ▼
  services.py    aplica les REGLES DE NEGOCI (aforament, duplicats, dates...)
     │
     ▼
  models.py      les taules de la base de dades
     │
     ▼
  MySQL
```

- **main.py** no conté regles de negoci: només rep la petició, comprova el rol
  amb els decoradors `@login_requerit` / `@admin_requerit`, valida les dades
  mínimes i crida la funció corresponent de services.py.
- **services.py** és el cor de l'aplicació: hi viuen totes les regles (comprovar
  l'aforament, evitar reserves duplicades, no deixar reservar classes passades...).
  Quan una regla falla, llança un `APIError` amb el codi HTTP corresponent.
- **errors.py** defineix aquest `APIError`. main.py el captura i el converteix en
  una resposta JSON amb el codi adequat (404, 409, etc.).
- **serialize.py** converteix els objectes de la base de dades en diccionaris per
  enviar-los com a JSON, decidint quins camps s'exposen (mai la contrasenya).
- **models.py** defineix les quatre taules amb SQLAlchemy.

Gràcies a aquesta separació, la lògica de negoci està en un sol lloc: si cal
canviar una regla, es toca a services.py i només allà.

## Autenticació amb cookies

Quan l'usuari fa login, el servidor genera un token JWT i el desa en una **cookie**
(`Set-Cookie`). El navegador la guarda i la torna a enviar automàticament en cada
petició, així que el frontend no ha de gestionar el token a mà. Al fer logout, el
servidor esborra la cookie. Les contrasenyes es desen hashejades amb bcrypt, mai
en text pla.

## Regles de negoci destacades

- **Control d'aforament:** cada classe té un comptador `places_lliures`. En reservar
  baixa 1, en cancel·lar puja 1. No es permet reservar si està a 0 (sense overbooking).
- **Reserva única:** un mateix soci no es pot inscriure dues vegades a la mateixa
  classe (restricció UNIQUE a la base de dades).
- **Classes passades:** el calendari només mostra classes futures; les que ja han
  passat desapareixen i no es poden reservar.
- **Historial d'assistència:** una reserva confirmada compta com a "assistida"
  automàticament un cop ha passat la data de la classe, sense confirmació manual.

## Base de dades (MySQL)

La connexió a MySQL està definida a `database.py` (variable `SQLALCHEMY_DATABASE_URL`).
Format de la URL:

```
mysql+pymysql://usuari:contrasenya@servidor:port/nom_bd
```

Les quatre taules són: `usuarios`, `activitats`, `classes` i `reserves`. Les relacions:
un usuari té moltes reserves, una classe té moltes reserves i una activitat té moltes
classes (relacions 1 a N amb claus foranes).

## Posada en marxa (local)

```bash
# 1. Instal·lar dependències
pip install -r requirements.txt

# 2. Omplir la base de dades amb dades d'exemple (només el primer cop)
python seed.py

# 3. Arrencar el servidor
python main.py

# 4. Obrir al navegador
#    http://127.0.0.1:8000
```

## Desplegament a Azure (resum)

L'aplicació està desplegada en una màquina virtual Linux (Ubuntu) a Azure:

- El servidor s'executa com a **servei systemd**, de manera que arrenca sol i es
  reinicia si falla.
- Flask arrenca amb `threaded=True` per poder atendre diverses peticions alhora.
- **HTTPS** amb un certificat autofirmat generat amb OpenSSL, passat a Flask amb
  el paràmetre `ssl_context`. (Per ser autofirmat, el navegador mostra un avís;
  la connexió va xifrada igualment.)
- MySQL està instal·lat a la mateixa VM.

## Usuaris d'exemple

| Rol   | Email           | Contrasenya |
|-------|-----------------|-------------|
| Admin | admin@gym.cat   | admin123    |
| Soci  | pol@gym.cat     | pol123      |

## Provar l'API

```bash
python test_api.py
```

Comprova el flux complet: autenticació amb cookies, reserves amb control
d'aforament, panell d'admin i permisos (401 / 403 / 409).

## Funcionalitats

- Registre i login de socis (autenticació JWT en cookie).
- Calendari públic de classes amb filtres (activitat, dia, monitor), només futures.
- Reserva i cancel·lació de places amb control d'aforament (sense overbooking).
- Historial d'assistència de cada soci (les classes passades a què s'havia inscrit).
- Panell d'administració: CRUD d'activitats i classes, veure ocupació.
- Edició del perfil propi.
