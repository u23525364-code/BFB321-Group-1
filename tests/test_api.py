"""Integration tests for the JSON API: request -> Flask -> services -> MySQL -> JSON.

Read tests expect the HPC sample data, so run `python init_db.py --reset` first.
Write tests (PATCH, POST) undo their own changes at the end.
"""
import pytest

from app import app
from db import execute


@pytest.fixture
def client():
    """A test browser: calls the app directly, no need to run python app.py."""
    app.config["TESTING"] = True
    return app.test_client()


# ---------------- GET /api/kpis ----------------

def test_kpis_returns_summary(client):
    response = client.get("/api/kpis")
    assert response.status_code == 200
    data = response.get_json()
    assert data["deliveries"] == 118
    assert data["breached"] == 30
    assert "breaches" not in data  # the long list is left out on purpose


# ---------------- GET /api/deliveries ----------------

def test_deliveries_first_page(client):
    data = client.get("/api/deliveries").get_json()
    assert (data["page"], data["size"], data["total"]) == (1, 20, 118)
    assert len(data["items"]) == 20


def test_deliveries_last_page(client):
    # 118 deliveries, 20 per page: page 6 holds the last 18
    data = client.get("/api/deliveries?page=6&size=20").get_json()
    assert len(data["items"]) == 18


def test_deliveries_filter_by_status(client):
    assert client.get("/api/deliveries?status=Breached").get_json()["total"] == 30


def test_deliveries_filter_by_truck(client):
    assert client.get("/api/deliveries?q=TRK-02").get_json()["total"] == 16


@pytest.mark.parametrize("url, message", [
    ("/api/deliveries?size=500", "'size' must be between 1 and 100."),
    ("/api/deliveries?page=abc", "'page' must be a whole number."),
    ("/api/deliveries?page=0", "'page' must be between 1 and 10000."),
])
def test_deliveries_bad_input_returns_400(client, url, message):
    response = client.get(url)
    assert response.status_code == 400
    assert response.get_json()["error"] == message


def test_deliveries_unknown_status_returns_400(client):
    assert client.get("/api/deliveries?status=Late").status_code == 400


# ---------------- GET /api/deliveries/<id> ----------------

def test_delivery_detail(client):
    # Hand check from Dave's data: DEL-0002, TRK-09, 13:04 -> 14:47 = 103 min, over 90
    data = client.get("/api/deliveries/2").get_json()
    assert data["delivery_code"] == "DEL-0002"
    assert data["turnaround_min"] == 103
    assert data["status"] == "Breached"


def test_delivery_detail_unknown_returns_404(client):
    response = client.get("/api/deliveries/9999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Delivery not found."}


# ---------------- PATCH /api/deliveries/<id> ----------------

def test_patch_note_is_saved(client):
    try:
        response = client.patch("/api/deliveries/2", json={"exception_note": "Dock not ready"})
        assert response.status_code == 200
        # read it back: the change really is in MySQL
        assert client.get("/api/deliveries/2").get_json()["exception_note"] == "Dock not ready"
    finally:
        with app.app_context():
            execute("UPDATE deliveries SET exception_note = NULL WHERE id = %s", (2,))


def test_patch_empty_note_returns_400(client):
    response = client.patch("/api/deliveries/2", json={"exception_note": ""})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Exception note is required."


def test_patch_without_json_returns_400(client):
    assert client.patch("/api/deliveries/2", data="not json").status_code == 400


def test_patch_unknown_delivery_returns_404(client):
    response = client.patch("/api/deliveries/9999", json={"exception_note": "Dock not ready"})
    assert response.status_code == 404


# ---------------- POST /api/scan-events ----------------

def _scan(client, location, truck="TRK-01"):
    """Send one scan from a test reader."""
    return client.post("/api/scan-events", json={
        "truck_code": truck, "location": location, "reader_id": "pytest"})


def test_scan_full_visit(client):
    """GATE-IN opens a delivery, a second GATE-IN is refused, GATE-OUT closes it."""
    first = _scan(client, "GATE-IN")
    assert first.status_code == 201
    delivery_id = first.get_json()["delivery"]["id"]
    try:
        assert first.get_json()["delivery"]["status"] == "On site"
        assert _scan(client, "GATE-IN").status_code == 400  # already on site
        closed = _scan(client, "GATE-OUT")
        assert closed.status_code == 201
        assert closed.get_json()["delivery"]["gate_out_at"] is not None
    finally:
        with app.app_context():
            execute("DELETE FROM scan_events WHERE reader_id = %s", ("pytest",))
            execute("DELETE FROM deliveries WHERE id = %s", (delivery_id,))


def test_scan_unknown_truck_returns_400(client):
    response = _scan(client, "GATE-IN", truck="TRK-99")
    assert response.status_code == 400
    assert "Unknown or inactive truck" in response.get_json()["error"]


def test_scan_missing_field_returns_400(client):
    response = client.post("/api/scan-events", json={"truck_code": "TRK-01"})
    assert response.status_code == 400


# ---------------- GET /api/trucks and errors ----------------

def test_trucks_list(client):
    data = client.get("/api/trucks").get_json()
    assert data["total"] == 12
    assert data["items"][0]["truck_code"] == "TRK-01"
    assert data["items"][0]["carrier"] == "Barloworld"


def test_unknown_api_url_returns_json_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not found."}


# ---------------- Capacity page (needs a signed-in user) ----------------

def test_capacity_page_shows_validation_errors(client):
    with client.session_transaction() as session:
        session["user"] = "manager"  # pretend we logged in
    html = client.get("/capacity?drivers=abc").get_data(as_text=True)
    assert "Current drivers must be a whole number." in html
    