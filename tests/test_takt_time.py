from datetime import datetime

import pytest

from models import takt_time as tt


# ---------------- cycle_time_minutes ----------------
def test_cycle_time_simple():
    # Hand calc: 10:00 -> 11:15 = 75 minutes
    start = datetime(2026, 10, 19, 10, 0)
    end = datetime(2026, 10, 19, 11, 15)
    assert tt.cycle_time_minutes(start, end) == 75.0


def test_cycle_time_with_seconds():
    # Hand calc: 90 seconds = 1.5 minutes
    start = datetime(2026, 10, 19, 10, 0, 0)
    end = datetime(2026, 10, 19, 10, 1, 30)
    assert tt.cycle_time_minutes(start, end) == pytest.approx(1.5)


def test_cycle_time_crosses_midnight():
    # Hand calc: 23:30 -> 00:45 next day = 30 + 45 = 75 minutes
    start = datetime(2026, 10, 19, 23, 30)
    end = datetime(2026, 10, 20, 0, 45)
    assert tt.cycle_time_minutes(start, end) == 75.0


def test_cycle_time_end_before_start_raises():
    start = datetime(2026, 10, 19, 11, 0)
    end = datetime(2026, 10, 19, 10, 0)
    with pytest.raises(ValueError):
        tt.cycle_time_minutes(start, end)


# ---------------- takt used / remaining / breach ----------------
def test_takt_used_percent():
    # Hand calc: 45 / 90 * 100 = 50%
    assert tt.takt_used_percent(45) == pytest.approx(50.0)
    # Overrun: 99 / 90 * 100 = 110%
    assert tt.takt_used_percent(99) == pytest.approx(110.0)


def test_minutes_remaining():
    assert tt.minutes_remaining(30) == 60.0   # 90 - 30
    assert tt.minutes_remaining(100) == -10.0  # overrun by 10


def test_is_breach_boundaries():
    assert tt.is_breach(89.99) is False
    assert tt.is_breach(90) is False   # exactly takt is compliant
    assert tt.is_breach(90.01) is True


# ---------------- classify_status ----------------
@pytest.mark.parametrize("elapsed, expected", [
    (0, tt.STATUS_ON_TRACK),
    (60, tt.STATUS_ON_TRACK),
    (71.9, tt.STATUS_ON_TRACK),    # just under the 72 min warning line
    (72, tt.STATUS_AT_RISK),       # 0.8 * 90 = 72 -> at risk starts here
    (85, tt.STATUS_AT_RISK),
    (90, tt.STATUS_AT_RISK),       # exactly takt is not yet a breach
    (90.01, tt.STATUS_BREACHED),
    (150, tt.STATUS_BREACHED),
])
def test_classify_status(elapsed, expected):
    assert tt.classify_status(elapsed) == expected


def test_classify_status_custom_threshold():
    # With a 0.5 warning fraction the line moves to 45 minutes.
    assert tt.classify_status(44, at_risk_fraction=0.5) == tt.STATUS_ON_TRACK
    assert tt.classify_status(45, at_risk_fraction=0.5) == tt.STATUS_AT_RISK


# ---------------- aggregates ----------------
def test_average_cycle_time():
    # Hand calc: (60 + 80 + 90 + 95 + 120) / 5 = 445 / 5 = 89.0
    assert tt.average_cycle_time([60, 80, 90, 95, 120]) == pytest.approx(89.0)


def test_compliance_rate():
    # Hand calc: 60, 80, 90 are within 90 -> 3 of 5 = 60%
    assert tt.compliance_rate([60, 80, 90, 95, 120]) == pytest.approx(60.0)


def test_summarise_cycles():
    # Hand calc for [60, 72, 80, 90, 95, 120]:
    #   count 6, sum = 517, average = 86.1666...
    #   on_track: 60 -> 1 | at_risk: 72, 80, 90 -> 3 | breached: 95, 120 -> 2
    #   compliance = 4 within takt / 6 = 66.67%
    result = tt.summarise_cycles([60, 72, 80, 90, 95, 120])
    assert result["count"] == 6
    assert result["average_minutes"] == pytest.approx(517 / 6)
    assert result["max_minutes"] == 120
    assert result["compliance_pct"] == pytest.approx(400 / 6)
    assert (result["on_track"], result["at_risk"], result["breached"]) == (1, 3, 2)
    assert result["breaches"] == 2


def test_summarise_empty_returns_empty_state():
    result = tt.summarise_cycles([])
    assert result["count"] == 0
    assert result["average_minutes"] is None
    assert result["compliance_pct"] is None


# ---------------- invalid inputs ----------------
def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        tt.classify_status(-1)
    with pytest.raises(ValueError):
        tt.classify_status(10, takt_min=0)
    with pytest.raises(ValueError):
        tt.classify_status(10, at_risk_fraction=1.5)
    with pytest.raises(ValueError):
        tt.average_cycle_time([])
    with pytest.raises(ValueError):
        tt.compliance_rate([])
