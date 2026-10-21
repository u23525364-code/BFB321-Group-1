from datetime import datetime

import pytest

from models import takt_time as tt

"""cycle time minutes calculations"""

def test_cycle_time_min():
    """Hand calc: 10:00 -> 11:15 = 75 minutes"""
    start = datetime(2026, 10, 19, 10, 0)
    end = datetime(2026, 10, 19, 11, 15)
    assert tt.cycle_time_minutes(start, end) == 75.0

def test_cycle_time_seconds():
    """Hand calc: 90 seconds = 1.5 minutes"""
    start = datetime(2026, 10, 19, 10, 0, 0)
    end = datetime(2026, 10, 19, 10, 1, 30)
    assert tt.cycle_time_minutes(start, end) == pytest.approx(1.5)

def test_cycle_time_crosses_midnight():
    """hand calc: 23:30 -> 00:45 the next day = 30 + 45 = 75 minutes"""
    start = datetime(2026,10,19,23,30)
    end = datetime(2026, 10, 20, 0, 45)
    assert tt.cycle_time_minutes(start, end) == 75.0 

def test_cycle_time_end_before_start_raises():
    start = datetime(2026, 10, 19, 11, 0)
    end = datetime(2026, 10, 19, 10, 0)
    with pytest.raises(ValueError):
        tt.cycle_time_minutes(start, end)

"""takt time/ remaining time/ breach status"""

def test_takt_used_percent():
    """Hand calc: 45/90 *100 = 50%"""
    assert tt.takt_used_percent(45) == pytest.approx(50.0)
    assert tt.takt_used_percent(99) == pytest.approx(110.0)