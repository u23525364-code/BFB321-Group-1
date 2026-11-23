#Lecture Slides Class 5 pg 42: Edits = takt_status instead of stock_status, PRODUCT_SELECT becomes DELIVERY_SELECT etc., added list_scan_events function, added list_deliveries function, changed the name of the file to services.py instead of models.py as claude pointed out that the folder is already named models,
import math
from datetime import datetime
from db import query_all, query_one, execute, get_db
from models import takt_time, capacity

def takt_status(turnaround_min):
    if turnaround_min is None:
        return "On site", "secondary"
    status = takt_time.classify_status(turnaround_min)
    if status == takt_time.STATUS_BREACHED:
        return "Breached", "danger"
    if status == takt_time.STATUS_AT_RISK:
        return "At risk", "warning"
    return "On track", "success"

def _add_status(rows):
    for row in rows:
        row["status"], row["badge"] = takt_status(row["turnaround_min"])
    return rows

DELIVERY_SELECT = """
SELECT d.id, d.delivery_code, t.truck_code, c.name AS carrier,
        
         l.code AS dock, d.gate_in_at, d.gate_out_at, d.exception_note,
       TIMESTAMPDIFF(MINUTE, d.gate_in_at, d.gate_out_at) AS turnaround_min
FROM deliveries d
JOIN trucks t ON t.id = d.truck_id
JOIN carriers c ON c.id = t.carrier_id
LEFT JOIN locations l ON l.id = d.dock_location_id
"""

def list_deliveries(search="", carrier_id=None):
    sql = DELIVERY_SELECT + " WHERE 1=1"
    params = []
    if search:
        sql += " AND t.truck_code LIKE %s"
        params.append(f"%{search}%")
    if carrier_id:
        sql += " AND t.carrier_id = %s"
        params.append(carrier_id)
    sql += " ORDER BY d.gate_in_at DESC"
    return _add_status(query_all(sql, params))

def dashboard_stats():
    deliveries = list_deliveries()
    finished = [d["turnaround_min"] for d in deliveries
                if d["turnaround_min"] is not None]
    breaches = [d for d in deliveries if d["badge"] == "danger"]
    at_risk = [d for d in deliveries if d["badge"] == "warning"]
    on_site = [d for d in deliveries if d["badge"] == "secondary"]
    return dict(deliveries=len(deliveries),
                average_minutes=takt_time.average_cycle_time(finished) if finished else 0,
                compliance_pct=takt_time.compliance_rate(finished) if finished else 0,
                breached=len(breaches), at_risk=len(at_risk),
                on_site=len(on_site), breaches=breaches)

def list_scan_events(limit=100):
    return query_all("""
        SELECT s.scanned_at, s.reader_id, s.rssi_dbm,
               l.code AS location, l.location_type,
               t.truck_code, t.tag_epc, c.name AS carrier
        FROM scan_events s
        JOIN locations l ON l.id = s.location_id
        JOIN trucks t ON t.id = s.truck_id
        JOIN carriers c ON c.id = t.carrier_id
        ORDER BY s.scanned_at DESC
        LIMIT %s
    """, (limit,))

def list_carriers():
    return query_all("SELECT id, name FROM carriers ORDER BY name")

#  Reports: compliance by carrier or truck (Luka) 

# The only groupings allowed: name -> (column to show, columns to group by)
REPORT_GROUPS = {
    "carrier": ("c.name", "c.id, c.name"),
    "truck": ("t.truck_code", "t.id, t.truck_code"),
}


def compliance_by(group):
    """Takt compliance per carrier or per truck, for finished deliveries only.

    group: "carrier" or "truck".
    Returns rows with: label, cycles, avg_minutes, within_takt, breaches, compliance_pct
    compliance_pct = within_takt / cycles * 100 (same rule as takt_time.compliance_rate)
    """
    label_col, group_cols = REPORT_GROUPS[group]
    takt = takt_time.TAKT_TIME_MINUTES
    rows = query_all(f"""
        SELECT {label_col} AS label,
               COUNT(*) AS cycles,
               AVG(TIMESTAMPDIFF(MINUTE, d.gate_in_at, d.gate_out_at)) AS avg_minutes,
               SUM(TIMESTAMPDIFF(MINUTE, d.gate_in_at, d.gate_out_at) <= %s) AS within_takt,
               SUM(TIMESTAMPDIFF(MINUTE, d.gate_in_at, d.gate_out_at) > %s) AS breaches
        FROM deliveries d
        JOIN trucks t ON t.id = d.truck_id
        JOIN carriers c ON c.id = t.carrier_id
        WHERE d.gate_out_at IS NOT NULL
        GROUP BY {group_cols}
        ORDER BY breaches DESC
    """, (takt, takt))
    for row in rows:
        row["avg_minutes"] = float(row["avg_minutes"])
        row["within_takt"] = int(row["within_takt"])
        row["breaches"] = int(row["breaches"])
        row["compliance_pct"] = row["within_takt"] / row["cycles"] * 100
    return rows


def list_trucks():
    """All trucks with their carrier name, ordered by truck code."""
    return query_all("""
        SELECT t.id, t.truck_code, t.tag_epc, t.active,
               c.id AS carrier_id, c.name AS carrier
        FROM trucks t
        JOIN carriers c ON c.id = t.carrier_id
        ORDER BY t.truck_code
    """)

def average_daily_deliveries():
    """Average deliveries per day in the data = total deliveries / number of days with deliveries."""
    row = query_one("""
        SELECT COUNT(*) AS deliveries,
               COUNT(DISTINCT DATE(gate_in_at)) AS days
        FROM deliveries
    """)
    if not row["days"]:
        return 0.0
    return row["deliveries"] / row["days"]


def capacity_defaults():
    """Starting values for the capacity form: volume and cycle time come from the real data."""
    stats = dashboard_stats()
    return {
        "baseline": math.ceil(average_daily_deliveries()),
        "uplift": 30.0,
        "drivers": 3,
        "cycle": round(stats["average_minutes"], 1) or capacity.DEFAULT_CYCLE_MINUTES,
        "shift": 8.0,
        "utilisation": 85.0,
    }


# Each form field: (label for error messages, number type, minimum, maximum)
CAPACITY_LIMITS = {
    "baseline": ("Deliveries / day", int, 0, 500),
    "uplift": ("Volume uplift (%)", float, -100, 500),
    "drivers": ("Current drivers", int, 1, 100),
    "cycle": ("Cycle time (min)", float, 1, 600),
    "shift": ("Shift length (hours)", float, 1, 24),
    "utilisation": ("Target utilisation (%)", float, 1, 100),
}


def read_capacity_inputs(args):
    """Check the form values (they arrive as text).

    Returns (values, errors). A missing field keeps its default; a bad one adds an error message.
    """
    values = capacity_defaults()
    errors = []
    for name, (label, kind, low, high) in CAPACITY_LIMITS.items():
        raw = args.get(name, "").strip()
        if raw == "":
            continue
        try:
            value = kind(raw)
        except ValueError:
            word = "a whole number" if kind is int else "a number"
            errors.append(f"{label} must be {word}.")
            continue
        if not low <= value <= high:
            errors.append(f"{label} must be between {low} and {high}.")
            continue
        values[name] = value
    return values, errors


def run_capacity_scenario(values):
    """Run the BYD scenario through models/capacity.py and add the current-state figures."""
    shift_minutes = values["shift"] * 60
    utilisation = values["utilisation"] / 100
    result = capacity.plan_scenario(values["baseline"], values["uplift"], values["drivers"],
                                    values["cycle"], shift_minutes, utilisation)
    result["load_percent_now"] = capacity.load_percent(
        values["baseline"], values["drivers"], values["cycle"], shift_minutes)
    result["drivers_required_now"] = capacity.drivers_required(
        values["baseline"], values["cycle"], shift_minutes, utilisation)
    return result

REASON_CODES = [
    "Dock not ready",
    "Waiting for paperwork",
    "Loading delay at HPC",
    "Carrier arrived late",
    "Vehicle not ready",
    "Other",
]


def breach_alerts():
    breaches = [d for d in list_deliveries() if d["badge"] == "danger"]
    for d in breaches:
        d["over_by"] = d["turnaround_min"] - int(takt_time.TAKT_TIME_MINUTES)
    new = [d for d in breaches if not d["exception_note"]]
    coded = [d for d in breaches if d["exception_note"]]
    by_reason = {}
    for d in coded:
        by_reason[d["exception_note"]] = by_reason.get(d["exception_note"], 0) + 1
    by_reason = sorted(by_reason.items(), key=lambda item: item[1], reverse=True)
    return dict(new=new, coded=coded, by_reason=by_reason, total=len(breaches))


def report_summary():
    finished = [d["turnaround_min"] for d in list_deliveries()
                if d["turnaround_min"] is not None]
    return takt_time.summarise_cycles(finished)


def compliance_by_day():
    rows = query_all("""
        SELECT DATE(gate_in_at) AS day, COUNT(*) AS cycles,
               SUM(TIMESTAMPDIFF(MINUTE, gate_in_at, gate_out_at) <= %s) AS within_takt
        FROM deliveries
        WHERE gate_out_at IS NOT NULL
        GROUP BY DATE(gate_in_at)
        ORDER BY day
    """, (takt_time.TAKT_TIME_MINUTES,))
    return [dict(label=r["day"].strftime("%d %b"),
                 pct=round(float(r["within_takt"]) / r["cycles"] * 100, 1))
            for r in rows]



NOTE_MAX_LENGTH = 255
SCAN_LOCATIONS = ("GATE-IN", "DOCK-A", "DOCK-B", "GATE-OUT")


def get_delivery(delivery_id):
    row = query_one(DELIVERY_SELECT + " WHERE d.id = %s", (delivery_id,))
    if row is None:
        return None
    return _add_status([row])[0]


def validate_note(note):
    note = (note or "").strip()
    if not note:
        return note, "Exception note is required."
    if len(note) > NOTE_MAX_LENGTH:
        return note, f"Exception note must be {NOTE_MAX_LENGTH} characters or fewer."
    return note, None


def update_delivery_note(delivery_id, note):
    note, error = validate_note(note)
    if error:
        return False, error
    delivery = get_delivery(delivery_id)
    if delivery is None:
        return False, "Delivery not found."
    execute("UPDATE deliveries SET exception_note = %s WHERE id = %s",
            (note, delivery_id))
    return True, f"Exception logged for {delivery['delivery_code']}."


def record_scan(truck_code, location_code, reader_id):
    truck_code = (truck_code or "").strip().upper()
    location_code = (location_code or "").strip().upper()
    reader_id = (reader_id or "").strip()
    if not truck_code or not location_code or not reader_id:
        return False, "Truck, location and reader are all required.", None
    if location_code not in SCAN_LOCATIONS:
        return False, (f"Unknown location '{location_code}'. "
                       f"Use one of: {', '.join(SCAN_LOCATIONS)}."), None

    now = datetime.now().replace(microsecond=0)
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT id, active FROM trucks WHERE truck_code = %s",
                        (truck_code,))
            truck = cur.fetchone()
            if truck is None or not truck["active"]:
                db.rollback()
                return False, f"Unknown or inactive truck '{truck_code}'.", None
            cur.execute("SELECT id FROM locations WHERE code = %s", (location_code,))
            location = cur.fetchone()
            cur.execute("SELECT id, delivery_code FROM deliveries "
                        "WHERE truck_id = %s AND status = 'open' "
                        "ORDER BY gate_in_at DESC LIMIT 1 FOR UPDATE", (truck["id"],))
            visit = cur.fetchone()

            
            if location_code == "GATE-IN" and visit:
                db.rollback()
                return False, f"{truck_code} is already on site ({visit['delivery_code']}).", None
            if location_code != "GATE-IN" and visit is None:
                db.rollback()
                return False, f"{truck_code} is not on site. Scan GATE-IN first.", None

            
            cur.execute("INSERT INTO scan_events (truck_id, location_id, reader_id, scanned_at) "
                        "VALUES (%s, %s, %s, %s)",
                        (truck["id"], location["id"], reader_id, now))
            if location_code == "GATE-IN":
                cur.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM deliveries")
                code = f"DEL-{cur.fetchone()['n']:04d}"
                cur.execute("INSERT INTO deliveries (delivery_code, truck_id, gate_in_at, status) "
                            "VALUES (%s, %s, %s, 'open')", (code, truck["id"], now))
                delivery_id = cur.lastrowid
                message = f"{truck_code} gated in. {code} opened."
            elif location_code == "GATE-OUT":
                cur.execute("UPDATE deliveries SET gate_out_at = %s, status = 'closed' "
                            "WHERE id = %s", (now, visit["id"]))
                delivery_id = visit["id"]
                message = f"{truck_code} gated out. {visit['delivery_code']} closed."
            else:
                cur.execute("UPDATE deliveries SET dock_location_id = %s, "
                            "dock_arrival_at = COALESCE(dock_arrival_at, %s) WHERE id = %s",
                            (location["id"], now, visit["id"]))
                delivery_id = visit["id"]
                message = f"{truck_code} arrived at {location_code} ({visit['delivery_code']})."
        db.commit()  
        return True, message, delivery_id
    except Exception:
        db.rollback()  
        raise