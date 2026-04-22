# Caja Diaria — Ripio Finance

Sistema web interno para visualizar y analizar la caja diaria de Ripio. Se sube un CSV diario con balances de Fireblocks, fiat y usuarios, y el sistema permite comparar fechas, ver gráficos y desglosar posiciones.

## Stack

- **Backend:** Django 5.1, Python 3.11
- **Frontend:** HTML/CSS/JS vanilla, Chart.js 4.4
- **DB:** SQLite (migrable a PostgreSQL)
- **Auth:** Django auth con gestión propia (sin Django admin)

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Crear superusuario inicial:
```bash
python manage.py createsuperuser
```

Acceder en `http://127.0.0.1:8000/`

## Estructura del proyecto

```
daily-assets/
├── core/
│   ├── models.py           # UserProfile, DailyUpload, BalanceRow
│   ├── views/
│   │   ├── dashboard.py    # Dashboard con gráficos
│   │   ├── balance.py      # Tabla de balances Ripio
│   │   ├── upload.py       # Carga y gestión de CSVs
│   │   ├── usuarios.py     # Balances de usuarios
│   │   └── users.py        # Gestión de usuarios (admin)
│   └── templatetags/
│       └── finance_filters.py  # fmt_usd, fmt_num, fmt_var
├── templates/
├── static/
└── media/                  # CSVs subidos (gitignored)
```

## Páginas

| URL | Descripción | Acceso |
|-----|-------------|--------|
| `/` | Dashboard — KPIs, gráfico BTC, donut por tipo y asset | Todos |
| `/balance/` | Tabla de balances Ripio con modo comparación | Todos |
| `/usuarios/` | Balances de usuarios (pasivos) | Todos |
| `/upload/` | Subir / reemplazar / eliminar CSVs | Admin |
| `/users/` | Gestión de usuarios del sistema | Admin |
| `/mi-cuenta/` | Cambio de contraseña | Todos |

## Formato del CSV

Columnas requeridas: `Workspace`, `Account Name`, `Account ID`, `Asset`, `Total Balance`, `From`, `Category`, `Type`, `Asset Group`, `Price`, `USD`

- Encoding: UTF-8 con BOM (`utf-8-sig`) o Latin-1 como fallback
- Los campos `Price` y `USD` pueden tener coma como separador de miles → se limpian automáticamente
- `Price` puede estar vacío → se guarda como `null`

### Regla clave — Ripio vs Usuarios

Las filas donde `From = 'User'` o `Category = 'User'` son **pasivos de Ripio** (balances de usuarios) y se muestran **exclusivamente** en `/usuarios/`. El resto son posiciones propias de Ripio y se muestran en `/balance/` y `/`.

### Tipos de asset

| Type | Descripción |
|------|-------------|
| Fiat | ARS, BRL, USD, CLP… |
| Stablecoin | USDC, USDT… |
| Crypto | BTC, ETH, SOL… |
| Shitcoin | Altcoins de baja liquidez |
| No Liquid | Sin liquidez real (LAC, RPC, HEX…) — siempre al fondo, excluido de totales |

## Roles

- **Admin** — puede subir/eliminar CSVs y gestionar usuarios
- **Viewer** — solo lectura

## Colores

```
Navy       #0b5394
Blue mid   #3d85c6
Blue light #9fc5e8
Blue pale  #d0e2f3
Positivo   #27AE60
Negativo   #C0392B
```
