# Caja Diaria — Ripio Finance

Sistema web interno para visualizar y analizar la caja diaria de Ripio. Se sube un CSV diario con balances de Fireblocks, fiat y usuarios, y el sistema permite comparar fechas, ver gráficos y desglosar posiciones.

## Stack

- **Backend:** Django 5.1, Python 3.11
- **Frontend:** HTML/CSS/JS vanilla, Chart.js 4.4
- **DB:** SQLite (migrable a PostgreSQL)
- **Auth:** Django auth con gestión propia (sin Django admin)

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
| `/Dashboard/` | Dashboard — KPIs, gráfico BTC, donut por tipo y asset | Todos |
| `/balance/` | Tabla de balances Ripio con modo comparación | Todos |
| `/upload/` | Subir / reemplazar / eliminar CSVs | Admin |
| `/users/` | Gestión de usuarios del sistema | Admin |
| `/mi-cuenta/` | Cambio de contraseña | Todos |

## Formato del CSV

Columnas requeridas: `Workspace`, `Account Name`, `Account ID`, `Asset`, `Total Balance`, `From`, `Category`, `Type`, `Asset Group`, `Price`, `USD`

- Encoding: UTF-8 con BOM (`utf-8-sig`) o Latin-1 como fallback
- Los campos `Price` y `USD` pueden tener coma como separador de miles → se limpian automáticamente
- `Price` puede estar vacío → se guarda como `null`

### Regla clave — Ripio vs Usuarios

Las filas donde `From = 'User'` o `Category = 'User'` son **pasivos de Ripio** (balances de usuarios) y no se muestran. El resto son posiciones propias de Ripio y se muestran en `/balance/` y `/Dashboard/`.

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
