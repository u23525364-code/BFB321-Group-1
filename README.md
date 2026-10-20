# BFB321-Semester-Project

HPC delivery takt-time dashboard (Flask + Bootstrap 5.3). Monitors every driver
delivery cycle against HPC's 90-minute takt time and plans driver capacity for
the BYD volume increase.

## Running the dashboard

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 (redirects to the login page).

## Running the tests

```bash
pytest
```

`pytest.ini` puts the project root on the import path, so this works from the
repository root.

## Project structure

```
app.py                  Flask routes; calls the models and passes results to templates
models/                 Supply chain model (standalone: no Flask or database imports)
  takt_time.py          Cycle time, takt status, compliance KPIs
  capacity.py           Drivers required, fleet capacity and load, BYD scenario planning
tests/                  pytest suites
  test_takt_time.py     Unit tests against hand calculations
  test_capacity.py      Unit tests against hand calculations
  test_pages.py         Integration tests: pages render and use the models
templates/              Jinja2 pages; every page extends base.html
  partials/             Reusable components (KPI cards, status badge macro)
static/css, static/js   Halfway theme, shared components, sorting/validation/toast JS
```

## Supply chain model

Both modules are standalone and document their formulas, inputs and assumptions
in their docstrings. Flask imports them; they never import Flask.

| Module | Formula | Used on |
|---|---|---|
| `takt_time.py` | cycle time = end scan − start scan (min) | Live deliveries |
| | takt used % = elapsed ÷ takt × 100 | Live deliveries progress bars |
| | status: on track < 80% of takt ≤ at risk ≤ takt < breached | Status badges |
| | compliance % = cycles ≤ takt ÷ total cycles × 100 | KPI cards (Home, Live) |
| `capacity.py` | drivers required = ⌈deliveries × cycle ÷ (shift × utilisation)⌉ | Capacity planning |
| | fleet capacity = ⌊drivers × shift × utilisation ÷ cycle⌋ | Capacity planning |
| | fleet load % = deliveries × cycle ÷ (drivers × shift) × 100 | Capacity chart |
| | projected volume = ⌈baseline × (1 + uplift %)⌉ | Capacity planning |

Until the MySQL layer is added (Final Project), the pages use the demo data at
the top of `app.py`. All KPIs and badges are still calculated by the models
rather than typed into the HTML.

## Frontend

- Responsive Bootstrap layout: sidebar becomes an off-canvas drawer below 992px; grids
  collapse to one or two columns on phones; wide tables scroll horizontally.
- Accessibility: skip link, labelled form controls, `aria-sort` on sortable columns
  (sortable headers are buttons, so they work by keyboard), labelled progress bars and charts.
- Validation: every `form.needs-validation` gets Bootstrap feedback from
  `static/js/dashboard.js`, and focus moves to the first invalid field. The capacity form is
  also validated server-side, with field-level error messages.
- Reusable components: `base.html` (navbar/sidebar shell), `partials/kpi_summary.html`
  (KPI cards), `partials/macros.html` (`status_badge`), and panel, table and badge classes in `style.css`.

## Page formatting

Every page in `templates/` extends `base.html` and uses the Halfway theme
(`static/css/halfway-theme.css`) plus the shared components in `static/css/style.css`.
The rules are in `.claude/skills/halfway-dashboard/SKILL.md`.
