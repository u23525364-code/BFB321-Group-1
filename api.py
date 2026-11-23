"""JSON API for the HPC takt dashboard, kept in a Flask Blueprint."""
from flask import Blueprint, jsonify, request

import services

# Every route in this file starts with /api
bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/kpis")
def kpis():
    """Headline takt KPIs as JSON: the same numbers as the Home page."""
    stats = services.dashboard_stats()
    stats.pop("breaches", None)  # drop the full list of breach rows
    return jsonify(stats)

# Status labels a delivery can have (from services.takt_status)
ALLOWED_STATUSES = {"On track", "At risk", "Breached", "On site"}


def _iso(value):
    """Turn a datetime into text like '2026-09-21T10:10:00' (JSON has no date type)."""
    return value.isoformat() if value else None


def _delivery_json(row):
    """One delivery as a dictionary with the same field names every time."""
    return {
        "id": row["id"],
        "delivery_code": row["delivery_code"],
        "truck_code": row["truck_code"],
        "carrier": row["carrier"],
        "dock": row["dock"],
        "gate_in_at": _iso(row["gate_in_at"]),
        "gate_out_at": _iso(row["gate_out_at"]),
        "turnaround_min": row["turnaround_min"],
        "status": row["status"],
        "exception_note": row["exception_note"],
    }


def _int_arg(name, default, minimum, maximum):
    """Read a whole number from the URL (?name=...). Returns (value, error message)."""
    raw = request.args.get(name, "").strip()
    if raw == "":
        return default, None
    try:
        value = int(raw)
    except ValueError:
        return None, f"'{name}' must be a whole number."
    if not minimum <= value <= maximum:
        return None, f"'{name}' must be between {minimum} and {maximum}."
    return value, None


@bp.get("/deliveries")
def deliveries():
    """List deliveries with pagination (?page, ?size) and filters (?q, ?carrier, ?status)."""
    page, error = _int_arg("page", 1, 1, 10000)
    if error:
        return jsonify(error=error), 400
    size, error = _int_arg("size", 20, 1, 100)
    if error:
        return jsonify(error=error), 400
    carrier_id, error = _int_arg("carrier", None, 1, 1000000)
    if error:
        return jsonify(error=error), 400
    status = request.args.get("status", "").strip()
    if status and status not in ALLOWED_STATUSES:
        return jsonify(error=f"'status' must be one of: {', '.join(sorted(ALLOWED_STATUSES))}."), 400
    search = request.args.get("q", "").strip()

    rows = services.list_deliveries(search, carrier_id)
    if status:
        rows = [r for r in rows if r["status"] == status]

    total = len(rows)
    start = (page - 1) * size
    items = [_delivery_json(r) for r in rows[start:start + size]]
    return jsonify(page=page, size=size, total=total, items=items)

@bp.get("/deliveries/<int:delivery_id>")
def delivery_detail(delivery_id):
    """One delivery by its id; 404 if it does not exist."""
    row = services.get_delivery(delivery_id)
    if row is None:
        return jsonify(error="Delivery not found."), 404
    return jsonify(_delivery_json(row))

@bp.get("/trucks")
def trucks():
    """All trucks with their carrier names."""
    items = [
        {
            "id": row["id"],
            "truck_code": row["truck_code"],
            "tag_epc": row["tag_epc"],
            "carrier_id": row["carrier_id"],
            "carrier": row["carrier"],
            "active": bool(row["active"]),
        }
        for row in services.list_trucks()
    ]
    return jsonify(total=len(items), items=items)