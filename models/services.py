#changed name to services.py instead of models.py on slides as claude pointed out that the folder is already named models
from models.db import query_all
from models import takt_time

DELIVERY_SELECT = """
    SELECT d.id, d.delivery_code, t.truck_code, c.name AS carrier,
           d.scheduled_arrival, d.gate_in_at, d.gate_out_at, d.status,
           l.code AS dock,
           TIMESTAMPDIFF(MINUTE, d.gate_in_at, d.gate_out_at) AS turnaround_min
    FROM deliveries d
    JOIN trucks t ON t.id = d.truck_id
    JOIN carriers c ON c.id = t.carrier_id
    LEFT JOIN locations l ON l.id = d.dock_location_id
"""

def _add_takt_status(rows):
    for row in rows:
        if row["turnaround_min"] is None:
            row["takt_status"] = "on_site"
        else:
            row["takt_status"] = takt_time.classify_status(row["turnaround_min"])
    return rows

def list_deliveries():
    sql = DELIVERY_SELECT + " ORDER BY d.gate_in_at DESC"
    return _add_takt_status(query_all(sql))


def dashboard_stats():
    rows = list_deliveries()
    turnarounds = [r["turnaround_min"] for r in rows if r["turnaround_min"] is not None]
    return takt_time.summarise_cycles(turnarounds)