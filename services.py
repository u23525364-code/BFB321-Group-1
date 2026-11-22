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