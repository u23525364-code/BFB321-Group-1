# BFB321-Semester-Project

- Uwen du Plessis u22631373
- Kadie Mc Intosh u23525364
- Luka Wood u24591344 
 u24591344-cyber (some commits may show as bfb321)
- Dean Zartmann u24595773

HPC delivery takt-time dashboard. It monitors every driver delivery cycle against HPC's
90-minute takt time and plans driver capacity for the BYD volume increase.

This repository is the **semester submission (26 October)**:

| Guide step | Deliverable | Where |
|---|---|---|
| Step 1 | Frontend: responsive HTML/CSS/Bootstrap pages | `templates/`, `static/` |
| Step 2 | Supply chain model: standalone, tested Python modules | `models/`, `tests/` |

The Flask API, MySQL database and frontend integration (Steps 3 to 5) belong to the final
project submission. The earlier Flask-rendered version of the frontend is kept on the
`flask-version` branch.

## Running the frontend

The pages are static HTML, so no server code is needed.

1. Open the project folder in VS Code and install the **Live Server** extension.
2. Right-click `templates/login.html` and choose **Open with Live Server**.
3. Sign in with any username and a password of at least 6 characters to reach the home page.

Bootstrap, Bootstrap Icons, Chart.js and the Montserrat font load from a CDN, so an
internet connection is needed.

## Running the model tests

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

`pytest.ini` puts the project root on the import path, so this works from the repository root.

## Project structure

```
models/                 Supply chain model (standalone: no Flask or database imports)
  takt_time.py          Cycle time, takt status, compliance KPIs
  capacity.py           Drivers required, fleet capacity and load, BYD scenario planning
tests/                  pytest suites
  test_takt_time.py     Unit tests against hand calculations
  test_capacity.py      Unit tests against hand calculations
templates/              One static HTML page per screen (login, home, live, reports, alerts, capacity, gatelog)
static/css, static/js   Halfway theme, Bootstrap theming, sorting/validation/toast JavaScript
static/img              Logo
```

## Supply chain model (Step 2)

Both modules are standalone and document their formulas, inputs and assumptions in their
docstrings. They import only the Python standard library.

| Module | Formula | Shown on |
|---|---|---|
| `takt_time.py` | cycle time = end scan − start scan (min) | Live deliveries |
| | takt used % = elapsed ÷ takt × 100 | Live deliveries progress bars |
| | status: on track < 80% of takt ≤ at risk ≤ takt < breached | Status badges |
| | compliance % = cycles ≤ takt ÷ total cycles × 100 | KPI cards (Home, Live) |
| `capacity.py` | drivers required = ⌈deliveries × cycle ÷ (shift × utilisation)⌉ | Capacity planning |
| | fleet capacity = ⌊drivers × shift × utilisation ÷ cycle⌋ | Capacity planning |
| | fleet load % = deliveries × cycle ÷ (drivers × shift) × 100 | Capacity chart |
| | projected volume = ⌈baseline × (1 + uplift %)⌉ | Capacity planning |

The tests check every function against hand-calculated results, including the BYD growth
scenario (13 deliveries a day, +30%, 3 drivers gives 17 deliveries, 4 drivers needed and
106% load).

The pages do not call the models yet. The figures on them are example data for the
demonstration. Connecting them to the models through a Flask API is part of the final
project.

## Frontend (Step 1)

- **Responsive:** the sidebar becomes an off-canvas drawer below 992px, grids collapse to one
  or two columns on phones, and wide tables scroll horizontally.
- **Bootstrap components:** navbar, offcanvas sidebar, cards, badges, tables, forms, modals,
  tabs and toasts. `static/css/style.css` only applies the Halfway colours and spacing to them.
- **Tables:** sortable columns (the headers are buttons, so sorting works by keyboard), with
  captions, status badges and a modal for logging a delivery exception.
- **Forms:** hints under each field, specific error messages, and focus moves to the first
  invalid field. Validation runs in the browser through `static/js/dashboard.js`.
- **Accessibility:** skip link, labelled form controls, `aria-sort` on sortable columns,
  labelled progress bars and charts.

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