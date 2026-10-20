import pytest

from models import capacity as cap


def test_cycles_per_driver_full_utilisation():
    # Hand calc: 480 / 90 = 5.333...
    assert cap.cycles_per_driver_per_day(90, 480, 1.0) == pytest.approx(480 / 90)


def test_cycles_per_driver_default_utilisation():
    # Hand calc: 480 * 0.85 = 408 productive min; 408 / 90 = 4.5333...
    assert cap.cycles_per_driver_per_day() == pytest.approx(408 / 90)


def test_drivers_required_exact_fit():
    # Hand calc: 16 deliveries * 90 = 1440 min; one driver has 480 -> 1440/480 = 3.0
    assert cap.drivers_required(16, 90, 480, 1.0) == 3


def test_drivers_required_rounds_up():
    # Hand calc: 1440 / (480 * 0.85 = 408) = 3.529 -> 4 drivers
    assert cap.drivers_required(16) == 4


def test_drivers_required_zero_volume():
    assert cap.drivers_required(0) == 0


def test_daily_capacity_rounds_down():
    # Hand calc: 3 drivers * 4.5333 = 13.6 -> 13 deliveries
    assert cap.daily_capacity(3) == 13
    # At 100% utilisation: 3 * 5.333 = 16.0 -> 16
    assert cap.daily_capacity(3, 90, 480, 1.0) == 16


def test_load_percent():
    # Hand calc: 13 * 90 = 1170 min; 3 * 480 = 1440 min; 1170 / 1440 = 81.25%
    assert cap.load_percent(13, 3) == pytest.approx(81.25)
    # 17 deliveries: 1530 / 1440 = 106.25% -> more work than the shift allows
    assert cap.load_percent(17, 3) == pytest.approx(106.25)


def test_capacity_gap():
    # Hand calc: 16 deliveries needs 4 drivers; have 3 -> gap of 1
    assert cap.capacity_gap(16, 3) == 1
    # 10 deliveries: 900 / 408 = 2.2 -> 3 drivers; have 3 -> gap of 0
    assert cap.capacity_gap(10, 3) == 0


def test_projected_volume():
    # Hand calc: 13 * 1.30 = 16.9 -> rounded up to 17
    assert cap.projected_volume(13, 30) == 17
    # No change in volume
    assert cap.projected_volume(13, 0) == 13


def test_plan_scenario_byd_growth():
    # Hand calc, baseline 13/day, +30% volume, 3 current drivers:
    #   projected = ceil(16.9) = 17
    #   needed = ceil(17 * 90 / 408) = ceil(1530 / 408 = 3.75) = 4
    #   current capacity = floor(3 * 4.5333) = 13
    #   additional = 4 - 3 = 1
    #   load on current fleet = 1530 / 1440 = 106.25%
    #   sufficient = 17 <= 13 -> False
    r = cap.plan_scenario(13, 30, 3)
    assert r["projected_daily"] == 17
    assert r["drivers_required"] == 4
    assert r["current_capacity"] == 13
    assert r["additional_drivers"] == 1
    assert r["load_percent_current_fleet"] == pytest.approx(106.25)
    assert r["sufficient"] is False


def test_plan_scenario_no_extra_drivers_needed():
    # 10/day, no uplift, 3 drivers: capacity 13 >= 10 -> sufficient, 0 extra
    r = cap.plan_scenario(10, 0, 3)
    assert r["sufficient"] is True
    assert r["additional_drivers"] == 0


def test_invalid_inputs_raise():
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
