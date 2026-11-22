"""JSON API for the HPC takt dashboard, kept in a Flask Blueprint."""
from flask import Blueprint, jsonify

import services

# Every route in this file starts with /api
bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/kpis")
def kpis():
    """Headline takt KPIs as JSON: the same numbers as the Home page."""
    stats = services.dashboard_stats()
    stats.pop("breaches", None)  # drop the full list of breach rows
    return jsonify(stats)