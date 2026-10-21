from datetime import datetime

import pytest

from models import takt_time as tt

#cycle time minutes calculations

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
    """testing the logical test of end occurring before the start"""
    start = datetime(2026, 10, 19, 11, 0)
    end = datetime(2026, 10, 19, 10, 0)
    with pytest.raises(ValueError):
        tt.cycle_time_minutes(start, end)

#takt time/ remaining time/ breach status

def test_takt_used_percent():
    """Hand calc: 45/90 *100 = 50%"""
    assert tt.takt_used_percent(45) == pytest.approx(50.0)
    assert tt.takt_used_percent(99) == pytest.approx(110.0)

def test_minutes_remaining():
    """testing the remaining minutes and overflow. hand calc: 90 - 30 = 60. 90 - 100 = -10"""
    assert tt.minutes_remaining(30) == 60.0 
    assert tt.minutes_remaining(100) == -10.0

def test_is_breach_boundaries():
    """exactly 90 minutes is not a breach, anything more is"""
    assert tt.is_breach(89.99) is False
    assert tt.is_breach(90) is False
    assert tt.is_breach(90.01) is True

#Status Classification

@pytest.mark.parametrize("elapsed, expected", [
    (0, tt.STATUS_ON_TRACK), 
    (60, tt.STATUS_ON_TRACK), 
    (71.9, tt.STATUS_ON_TRACK), 
    (72, tt.STATUS_AT_RISK), 
    (85, tt.STATUS_AT_RISK),
    (90, tt.STATUS_AT_RISK),
    (90.01, tt.STATUS_BREACHED),
    (150, tt.STATUS_BREACHED),
])

def test_classify_status(elapsed, expected):
    assert tt.classify_status(elapsed) == expected

def test_classify_status_custom_threshold():
    """with warning fraction of 0.5, the at risk status line moves to 45 minutes"""
    assert tt.classify_status(44, at_risk_fraction= 0.5) == tt.STATUS_ON_TRACK
    assert tt.classify_status(45, at_risk_fraction= 0.5) == tt.STATUS_AT_RISK

#Aggregate testing of many cycles in a set

def test_average_cycle_time():
    """hand calc: (60 + 80 + 90 + 95 + 120)/ 5 = 445/5 = 89.0"""
    assert tt.average_cycle_time([60, 80, 90, 95, 120]) == pytest.approx(89.0)

def test_compliance_rate(): 
    """hand calc: of 60, 80, 90, 95, 120; 3 of 5 are within takt time = 60%"""
    assert tt.compliance_rate([60, 80, 90, 95, 120]) == pytest.approx(60.0)

def test_summarise_cycles(): 
    """hand calc for [60, 72, 80, 90, 95, 120]: 
    count = 6, sum = 517, average = 86.166666...
    on_track: 60 -> 1 | at_risk: 72, 80, 90 -> 3 | breached: 95, 120 -> 2
    compliance = 4 within takt = 4/6 = 66.67% """
    result = tt.summarise_cycles([60, 72, 80, 90, 95, 120])
   
    assert result["count"] == 6
    assert result["average_minutes"] == pytest.approx(517/6)
    assert result["max_minutes"] == 120
    assert result["compliance_pct"] == pytest.approx(400/6)
    assert (result["on_track"], result["at_risk"], result["breached"]) == (1, 3, 2)    
    assert result["breaches"] == 2

def test_summarise_empty_returns_empty_state(): 
    """ensuring the summary is not broken by an empty list"""
    result = tt.summarise_cycles([])
    assert result["count"] == 0
    assert result["average_minutes"] is None
    assert result["compliance_pct"] is None

#Invalid inputs

def test_invalid_inputs_raise():
    """further testing for input value errors"""
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


