# HPC Delivery Takt Dashboard: BFB321 Group 1

**BFB321 Supply Chain Technologies · University of Pretoria · Final Project 2026**

A Flask + MySQL web application for **Halfway Vehicle Preparation Centre (HPC)**.
RFID readers at HPC's gates and docks record every truck visit (GATE-IN → DOCK-A/DOCK-B → GATE-OUT).
The app turns those scans into delivery cycles, measures each cycle against HPC's
**90-minute takt time**, flags breaches so a reason can be logged, reports compliance by
carrier and truck, and models whether the current drivers can absorb the **BYD volume increase**.
Drivers capture nothing: all data comes from the RFID scans.

## Team

| Name | Student number | GitHub username | Main tasks |
|---|---|---|---|
| Kadie Mc Intosh | u23525364 | `u23525364-code` | Database (schema, seed, init_db, db.py), services layer, Live, Gate log, Alerts and Home pages, login |
| Luka Wood | u24591344 | `u24591344-cyber` (some commits show the author name `bfb321`, same account) | Capacity model tests, `config.py`, Reports page (compliance by carrier/truck), ERD, README |
| Dean Zartmann | u24595773 | `u24595773` | Takt-time model and tests, JSON API (Blueprint), error handling and logging, Capacity page, API tests and documentation |
| Uwen du Plessis | u22631373 | `u22631373` | Frontend restructure and theming (semester project), TODO: final-project task |

## Task allocation

| Area | Files | Who |
|---|---|---|
| Supply chain model: takt time | `models/takt_time.py`, `tests/test_takt_time.py` | Dean |
| Supply chain model: capacity | `models/capacity.py`, `tests/test_capacity.py` | Luka |
| Frontend pages and theme | `templates/`, `static/` | Kadie, Uwen |
| Database: schema, seed data, build script, connection | `schema.sql`, `seed.sql`, `init_db.py`, `db.py` | Kadie |
| Services (SQL and business rules) | `services.py` | Kadie, plus Luka (reports) and Dean (capacity, trucks) |
| Create flow: record a gate scan | `/scans`, Gate log page | Kadie |
| Update flow: reason code on a breach | `/deliveries/<id>/exception`, Alerts page | Kadie |
| Login and logout | `app.py`, `templates/login.html` | Kadie |
| Settings per environment | `config.py`, `.env.example` | Luka |
| Reports: compliance by carrier and truck | `services.compliance_by`, `templates/reports.html` | Luka, Uwen (html) |
| ERD | `docs/erd.png`, `docs/erd.mwb` | Luka |
| JSON API (6 endpoints) | `api.py`, `docs/API.md` | Dean |
| Error handlers and logging | `app.py`, `templates/error.html` | Dean, Uwen (html) |
| Capacity page (model-driven scenario) | `services.py`, `templates/capacity.html` | Dean, Uwen (html) |
| API integration tests | `tests/test_api.py` | Dean |
| README | `README.md` | Luka |

## Architecture

```
RFID readers (Yanzeo) → HPC gateway (Node.js) ─┐
Gate log form (browser) ───────────────────────┼─→ Flask app (app.py + api.py)
                                               │        │
                                               │        ├─ services.py ── SQL ──→ MySQL (Aiven)
                                               │        └─ models/ (takt_time, capacity)
Browser pages (Jinja2 + Bootstrap) ←───────────┘   KPIs, status badges, reports, capacity scenario
```

- **app.py**: page routes, login, error handlers, logging
- **api.py**: JSON API (Flask Blueprint, `/api/...`)
- **services.py**: all SQL and business rules (the role of `models.py` in the class sample; named
  `services.py` because `models/` already holds the supply chain model)
- **db.py**: one MySQL connection per request, parameterised queries (`%s`), commit and rollback
- **models/**: the standalone, tested supply chain model (no Flask or database imports)

## Pages and the three end-to-end flows

| Page | What it shows | Data |
|---|---|---|
| Home | Takt compliance, breaches, deliveries | MySQL + takt model |
| Live deliveries | Every delivery with takt status, search and carrier filter | MySQL + takt model |
| Gate log | Latest RFID scans; form to record a scan | MySQL |
| Breach alerts | Deliveries over 90 min; form to log a reason | MySQL + takt model |
| Reports | Compliance by carrier and truck, daily compliance chart | MySQL (GROUP BY) |
| Capacity | BYD scenario: drivers required, load %, over/under capacity | MySQL + capacity model |

1. **Scan → delivery cycle → dashboard:** record GATE-IN on the Gate log (or `POST /api/scan-events`). A delivery opens and shows "On site" on Live. GATE-OUT closes it and its takt status appears.
2. **Breach → reason code:** a cycle over 90 min appears on Alerts. Choose a reason and it is saved to the delivery (`PATCH /api/deliveries/<id>`), and the alert count drops.
3. **Capacity scenario (model-driven):** enter a volume uplift on Capacity. `models/capacity.py` calculates drivers required and load, and the page shows within/over capacity.

## Database

Five tables in third normal form, with primary and foreign keys, UNIQUE and CHECK constraints,
`created_at`/`updated_at` audit fields and indexes for the main lookups:

| Table | Holds | Key relationships |
|---|---|---|
| `carriers` | Transport companies | 1 carrier → many trucks |
| `trucks` | Truck code and RFID tag (EPC) | 1 truck → many scan_events and deliveries |
| `locations` | GATE-IN, DOCK-A, DOCK-B, GATE-OUT | 1 location → many scan_events and deliveries (dock) |
| `scan_events` | Every RFID read (time, reader, signal) | many → 1 truck, many → 1 location |
| `deliveries` | One truck visit: gate-in, dock, gate-out, status, exception note | many → 1 truck, many → 1 dock location |

Indexes: `idx_scans_truck_time (truck_id, scanned_at)`, `idx_deliveries_status (status)`,
`idx_deliveries_truck_time (truck_id, gate_in_at)`.

[Entity relationship diagram](docs/erd.png)

*Figure 1: ERD (MySQL Workbench). The editable model is in `docs/erd.mwb`.*

## Setup and run (exact commands)

You need Python 3.10+, Git and a free MySQL database on [Aiven](https://console.aiven.io/signup).

### 1. Get the code
```bash
git clone https://github.com/u23525364-code/BFB321-Group-1.git
cd BFB321-Group-1
```

### 2. Create the virtual environment and install packages

**Windows (PowerShell):**
```powershell
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
If activation says "running scripts is disabled", run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Create the MySQL database (Aiven)
1. Sign up at console.aiven.io → **Create service → MySQL**.
2. Choose the **Developer** tier (plan *Developer-1*, runs on trial credits). Check that the summary does not show the Professional tier.
3. Wait until the service shows **Running**, then open **Connection information**.

### 4. Settings (`.env`)
Copy the template and fill in your own Aiven values. `.env` is in `.gitignore` and is never committed.

Windows: `copy .env.example .env` · macOS/Linux: `cp .env.example .env`

| Variable | Value |
|---|---|
| `DB_HOST` / `DB_PORT` | Host and port from Aiven (the port is **not** 3306) |
| `DB_USER` / `DB_PASSWORD` | `avnadmin` and the password from Aiven |
| `DB_NAME` | `defaultdb` |
| `SECRET_KEY` | Any long random text |
| `APP_ENV` | `development`, `testing` or `production` (see `config.py`) |
| `DEMO_USER` / `DEMO_PASSWORD` | Demo login (defaults below) |

### 5. Build the database and load the sample data
```bash
python init_db.py --reset
```
(On macOS use `python3`.) This drops the tables, creates them from `schema.sql` and loads `seed.sql`.

### 6. Run the app
```bash
python app.py
```
Open **http://127.0.0.1:5000** and sign in.

## Demo login

| Username | Password |
| `manager` | `takt2026` |

All pages need a signed-in user. The JSON API does not, so it can be tested directly.
In production, set your own `DEMO_USER`, `DEMO_PASSWORD` and a long random `SECRET_KEY` in `.env`.

## Configuration per environment

`config.py` has `DevelopmentConfig` (debug on), `TestingConfig` and `ProductionConfig` (debug off,
so users never see error details). `APP_ENV` in `.env` chooses one. All secrets are read from `.env`.

## Logging and error handling

- Logs go to the terminal and to `logs/app.log` (time, level, message). Every failed request (status 400+) and every RFID scan received is logged. `logs/` is in `.gitignore`.
- Central handlers for 400, 404 and 500 return JSON for `/api/...` URLs and a friendly page otherwise. On a 500 the database transaction is rolled back, and no stack trace is shown to the user.

## Running the tests

```bash
python init_db.py --reset
pytest -v
```
- `tests/test_takt_time.py`, `tests/test_capacity.py`: unit tests of the supply chain model against hand calculations (33 tests)
- `tests/test_api.py`: integration tests through Flask and MySQL (21 tests). Write tests undo their own changes.

The integration tests expect the original sample data, which is why `init_db.py --reset` comes first.

## Backup, restore and rollback

**Backup** (needs the MySQL command-line client; use the values from your `.env`):
```bash
mysqldump --host=<DB_HOST> --port=<DB_PORT> --user=avnadmin -p --ssl-mode=REQUIRED --set-gtid-purged=OFF defaultdb > backup_YYYY-MM-DD.sql
```

**Restore:**
```bash
mysql --host=<DB_HOST> --port=<DB_PORT> --user=avnadmin -p --ssl-mode=REQUIRED defaultdb < backup_YYYY-MM-DD.sql
```

- **Aiven backups:** Aiven also backs up the service automatically. The retention depends on the plan; see the **Backups** tab of the service.
- **Reset to the demo data:** `python init_db.py --reset`.
- **Rollback of a failed change:**
  - *Code:* `git revert <commit>` undoes a bad commit without rewriting history.
  - *Database change:* take a backup first, apply the change, and restore the backup if it fails.
  - *Inside the app:* every multi-step write (e.g. recording a scan) runs in one transaction that is rolled back if any step fails.

## Data note

The sample data (`seed.sql`) is HPC's RFID sample from the gateway developer: 12 trucks, 4 carriers,
118 deliveries and 354 scan events, **21 September – 3 October 2026**. It is **simulated / sample
data, not live readings**. The RFID readers are not yet active. Each cycle is measured from gate-in to
gate-out at HPC.

## Folder structure

```
app.py              Page routes, login, error handlers, logging
api.py              JSON API (Flask Blueprint, /api)
services.py         SQL queries and business rules
db.py               MySQL connection helpers
config.py           Settings per environment
init_db.py          Builds the database from schema.sql and seed.sql
schema.sql          CREATE TABLE statements
seed.sql            HPC sample data
models/             Supply chain model: takt_time.py, capacity.py
tests/              pytest: model unit tests, API integration tests
templates/          Jinja2 pages (+ error.html)
static/             CSS, JavaScript, images
docs/               ERD (erd.png, erd.mwb), API documentation (API.md)
requirements.txt    Python packages
.env.example        Settings template (copy to .env)
```

## JSON API

The API is a Flask Blueprint in `api.py` (all paths start with `/api`). It returns JSON,
uses the same `services.py` functions as the web pages, and does not need a login.
Full documentation with request/response examples: [docs/API.md](docs/API.md).

| Method | Path | Purpose | Success | Errors |
|---|---|---|---|---|
| GET | `/api/kpis` | Takt KPIs: deliveries, average turnaround, compliance %, breaches | 200 | — |
| GET | `/api/deliveries` | List deliveries · `?page=1&size=20` · filters `?q=TRK-02&carrier=2&status=Breached` | 200 | 400 |
| GET | `/api/deliveries/<id>` | One delivery | 200 | 404 |
| PATCH | `/api/deliveries/<id>` | Log an exception note · body `{"exception_note": "Dock not ready"}` | 200 | 400, 404 |
| POST | `/api/scan-events` | Record an RFID scan · body `{"truck_code": "TRK-02", "location": "GATE-IN", "reader_id": "hpc-reader-01"}` | 201 | 400 |
| GET | `/api/trucks` | Trucks with carrier names | 200 | — |

Errors always look like `{"error": "message"}`. Invalid input gives 400, unknown records 404,
and unexpected failures 500 (details are written to `logs/app.log`, never shown to the user).
Integration tests: `tests/test_api.py`.

## Screenshots

TODO: add screenshots of Home, Live, Alerts, Reports, Capacity and Gate log in `docs/screenshots/`
and link them here, e.g. `![Capacity page](docs/screenshots/capacity.png)`.
