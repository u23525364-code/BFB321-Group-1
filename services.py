#Lecture Slides Class 5 pg 42: Edits = takt_status instead of stock_status, PRODUCT_SELECT becomes DELIVERY_SELECT etc., added list_scan_events function, added list_deliveries function, changed the name of the file to services.py instead of models.py as claude pointed out that the folder is already named models,

from db import query_all
from models import takt_time

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
       l.code AS dock, d.gate_in_at, d.gate_out_at,
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