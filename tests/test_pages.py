"""Integration tests: every page renders and the capacity page uses models/capacity.py."""
import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize("path", ["/login", "/home", "/live", "/reports",
                                  "/alerts", "/capacity", "/gatelog"])
def test_page_renders(client, path):
    assert client.get(path).status_code == 200


def test_root_redirects_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_capacity_defaults_match_model_hand_calc(client):
    # Same scenario as test_plan_scenario_byd_growth: 13/day, +30%, 3 drivers
    # -> 17 deliveries, 4 drivers needed, 1 additional, 106% load.
    html = client.get("/capacity").get_data(as_text=True)
    assert "Over capacity." in html
    assert "1 additional driver required" in html
    assert "106%" in html


def test_capacity_within_capacity(client):
    html = client.get("/capacity?baseline=10&uplift=0&drivers=3").get_data(as_text=True)
    assert "Within capacity." in html


def test_capacity_invalid_input_shows_errors(client):
    html = client.get("/capacity?baseline=abc&drivers=0").get_data(as_text=True)
    assert "Deliveries / day must be a whole number." in html
    assert "Current drivers must be between 1 and 100." in html
    assert "Check the inputs." in html


def test_live_badges_come_from_takt_model(client):
    # 74 min elapsed >= 72 min warning line -> at risk; 48 min -> on time.
    html = client.get("/live").get_data(as_text=True)
    assert 'badge-warn">At risk' in html
    assert 'badge-good">On time' in html
