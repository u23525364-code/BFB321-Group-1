import pytest

from models import capacity as cap


def test_cycles_per_driver_full_utilisation():
    # hand calculation: 480/90 = 5.333...
    assert cap.cycles_per_driver_per_day(90,480,1.0) == pytest.approx(480/90)

def test_cycles_per_driver_default_utilisation():
    # hand calculation: 480*0.85 = 408 productive minutes 
    # 408/90 = 4.5333...
    assert cap.cycles_per_driver_per_day() == pytest.approx(408/90)

def test_drivers_required_exact_fit():
    # hand calculation: 16*90 = 1440 minutes
    # one driver has 480 minutes 
    # 1440/480 = 3.0 drivers
    assert cap.drivers_required(16,90.480,1.0) == 3

def test_drivers_required_rounds_up():
    # hand calculation: 1440/(480*0.85) = 3.529 ; rounded up = 4 drivers
    assert cap.drivers_required(16) == 4

def test_drivers_required_zero_volume():
    # hand calculation: 0 deliveries requires 0 drivers
    assert cap.drivers_required(0) == 0

def test_daily_capacity_rounds_down():
    # hand calculation: 3 drivers * 4.5333 = 13.6 ; rounded down = 13 deliveries
    assert cap.daily_capacity(3) == 13
    # hand calculation: at 100% utilisation 3*5.333 = 16.0 
    assert cap.daily_capacity(3,90,480,1.0) == 16

def test_load_percent():
    # hand calculation: 13*90=1170 minutes; 3*480=1440 minutes; 1170/1440 = 81.25%
    assert cap.load_percent(17,3) == pytest.approx(81.25)
    # hand calculation: 1530/1440 = 106.25% ; more work than the shift allows
    assert cap.load_percent(17,3) == pytest.approx(106.25)

def test_capacity_gap():
    #hand calculation: 16 deliveries require 4 drivers and we have 3 thus a remainder of 1
    assert cap.capacity_gap(16,3) == 1
    # hand calculation: 10 deliveries require 3 drivers and we have 3 thus a remainder of 0
    assert cap.capacity_gap(10,3) == 0

def test_projected_volume():
    # hand calculation: 13*1.30 = 16.9 ; rounded up = 17
    assert cap.projected_volume(13,30) == 17
    # hand calculation: no chamge in volume scenario
    assert cap.projected_volume(13,0) == 13

def test_plan_scenario_byd_growth():
    # hand calculation: baseline=13/day; 30% increase in volume; 3 current drivers
    # projected = ceil(16.9) = 17
    # needed = ceil(17*90/408) = 4
    # current.capacity = floor(3*4.5333) = 13
    # additional = 4-3=1
    # load on current drivers = 1530/1440 = 106.25%
    # sufficient=17 and current is 13 thus insufficient (false) 
    r = cap.plan_scenario(13,30,3)
    assert r["projected_daily"] == 17
    assert r["drivers_required"] == 4
    assert r["current_capacity"] == 13
    assert r["additional_drivers"] == 1
    assert r["load_percent_current_fleet"] == pytest.approx(106.25)
    assert r["sufficient"] is False

def test_plan_scenario_no_extra_drivers_needed():
    # hand calculation: 10/day; 0% volume increase; 3 drivers; capacity=13 which is more than 10 thus sufficient(True); 0 extra
    r = cap.plan_scenario(10,0,3)
    assert r["sufficient"] is True
    assert r["additional_drivers"] == 0

def test_invalid_inputs():
    with pytest.raises(ValueError):
        cap.drivers_required(-1)
    with pytest.raises(ValueError):
        cap.drivers_required(10, cycle_minutes=0)
    with pytest.raises(ValueError):
        cap.drivers_required(10, utilisation=0)
    with pytest.raises(ValueError):
        cap.drivers_required(10, utilisation=1.2)
    with pytest.raises(ValueError):
        cap.daily_capacity(-1)
    with pytest.raises(ValueError):
        cap.projected_volume(10, -150)