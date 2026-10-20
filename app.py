from flask import Flask, redirect, render_template, request, url_for

# The supply chain models are standalone (no Flask imports). Flask only calls them.
from models import capacity as cap
from models import takt_time as tt

app = Flask(__name__)

# Sidebar navigation, grouped into sections. base.html renders this on every page.
NAV_SECTIONS = [
    ("Overview", [
        {"endpoint": "home", "label": "Home", "icon": "bi-grid-1x2"},
    ]),
    ("Operations", [
        {"endpoint": "live", "label": "Live deliveries", "icon": "bi-broadcast"},
        {"endpoint": "alerts", "label": "Breach alerts", "icon": "bi-bell", "count": 4},
        {"endpoint": "gatelog", "label": "Gate log", "icon": "bi-upc-scan"},
    ]),
    ("Planning", [
        {"endpoint": "reports", "label": "Reports", "icon": "bi-bar-chart-line"},
        {"endpoint": "capacity", "label": "Capacity", "icon": "bi-sliders"},
    ]),
]

# --------------------------------------------------------------------------
# Demo data. Stands in for the RFID scan data until the MySQL layer exists
# (Final Project). All KPIs below are calculated by the models, not typed in.
# --------------------------------------------------------------------------
# Cycle times (minutes) of today's completed deliveries.
TODAY_CYCLE_TIMES = [62, 71, 78, 85, 88, 90, 94, 101]
PLANNED_DELIVERIES_TODAY = 12
TRUCKS_TOTAL = 2

# Cycles currently in progress. elapsed=None means the driver is idle.
ACTIVE_CYCLES = [
    {"driver": "Driver A", "initials": "DA", "truck": "TRK-1",
     "destination": "Dealership 2", "departed": "13:18", "elapsed": 74},
    {"driver": "Driver B", "initials": "DB", "truck": "TRK-2",
     "destination": "Dealership 4", "departed": "13:44", "elapsed": 48},
    {"driver": "Driver C", "initials": "DC", "truck": None,
     "destination": None, "departed": None, "elapsed": None},
]


def today_kpis():
    """Headline KPIs for the summary cards, calculated by models/takt_time.py."""
    summary = tt.summarise_cycles(TODAY_CYCLE_TIMES)
    completed = summary["count"]
    trucks_in_use = sum(1 for c in ACTIVE_CYCLES if c["truck"])
    return {
        **summary,
        "completed": completed,
        "planned": PLANNED_DELIVERIES_TODAY,
        "remaining": max(PLANNED_DELIVERIES_TODAY - completed, 0),
        "completed_pct": round(completed / PLANNED_DELIVERIES_TODAY * 100),
        "trucks_in_use": trucks_in_use,
        "trucks_total": TRUCKS_TOTAL,
        "trucks_pct": round(trucks_in_use / TRUCKS_TOTAL * 100),
        # Fleet-level status uses the same thresholds as a single cycle:
        # at least 80% compliance is fine, anything lower needs attention.
        "compliance_status": (tt.STATUS_ON_TRACK
                              if summary["compliance_pct"] >= tt.AT_RISK_FRACTION * 100
                              else tt.STATUS_AT_RISK),
    }


def active_cycles():
    """Add takt status and progress (from the model) to each active cycle."""
    rows = []
    for cycle in ACTIVE_CYCLES:
        row = dict(cycle)
        if cycle["elapsed"] is None:
            row["status"] = None
            row["takt_used"] = 0
        else:
            row["status"] = tt.classify_status(cycle["elapsed"])
            row["takt_used"] = round(tt.takt_used_percent(cycle["elapsed"]))
        rows.append(row)
    return rows


@app.context_processor
def inject_globals():
    return {
        "nav_sections": NAV_SECTIONS,
        "takt_minutes": int(tt.TAKT_TIME_MINUTES),
        "at_risk_fraction": tt.AT_RISK_FRACTION,
    }


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/home")
def home():
    return render_template("home.html", kpis=today_kpis())


@app.route("/live")
def live():
    return render_template("live.html", kpis=today_kpis(), cycles=active_cycles())


@app.route("/reports")
def reports():
    return render_template("reports.html")


@app.route("/alerts")
def alerts():
    return render_template("alerts.html")


# --------------------------------------------------------------------------
# Capacity planning: form inputs -> models/capacity.py -> results
# --------------------------------------------------------------------------
# name: (label, type, default, min, max)
CAPACITY_FIELDS = {
    "baseline": ("Deliveries / day", int, 13, 0, 500),
    "uplift": ("Volume uplift (%)", float, 30, -100, 500),
    "drivers": ("Current drivers", int, 3, 1, 100),
    "cycle": ("Cycle time (min)", float, cap.DEFAULT_CYCLE_MINUTES, 1, 600),
    "shift": ("Shift length (hours)", float, cap.DEFAULT_SHIFT_MINUTES / 60, 1, 24),
    "utilisation": ("Target utilisation (%)", float, cap.DEFAULT_UTILISATION * 100, 1, 100),
}


def parse_capacity_form(args):
    """Read and validate the scenario inputs. Returns (values, errors)."""
    values, errors = {}, {}
    for name, (label, kind, default, low, high) in CAPACITY_FIELDS.items():
        raw = args.get(name, "").strip()
        if raw == "":
            values[name] = default
            continue
        try:
            value = kind(raw)
        except ValueError:
            errors[name] = f"{label} must be a {'whole ' if kind is int else ''}number."
            values[name] = raw
            continue
        if not low <= value <= high:
            errors[name] = f"{label} must be between {low:g} and {high:g}."
        values[name] = value
    return values, errors


@app.route("/capacity")
def capacity():
    values, errors = parse_capacity_form(request.args)
    result = None
    if not errors:
        shift_minutes = values["shift"] * 60
        utilisation = values["utilisation"] / 100
        result = cap.plan_scenario(values["baseline"], values["uplift"], values["drivers"],
                                   values["cycle"], shift_minutes, utilisation)
        result["load_percent_current"] = cap.load_percent(
            values["baseline"], values["drivers"], values["cycle"], shift_minutes)
        result["baseline_drivers_required"] = cap.drivers_required(
            values["baseline"], values["cycle"], shift_minutes, utilisation)
    return render_template("capacity.html", fields=CAPACITY_FIELDS,
                           values=values, errors=errors, result=result,
                           scenario_name=request.args.get("scenario", "BYD onboarding"))


@app.route("/gatelog")
def gatelog():
    return render_template("gatelog.html")


if __name__ == "__main__":
    app.run(debug=True)
