"""
capacity.py - Driver capacity planning for HPC (including the BYD volume scenario).

STANDALONE supply chain model: no Flask, no database imports.

Question answered
-----------------
"How many drivers do we need to complete a given number of deliveries per day
if every delivery cycle takes 90 minutes?"

Formulas
--------
productive_minutes_per_driver = shift_minutes * utilisation
cycles_per_driver_per_day     = productive_minutes_per_driver / cycle_minutes
drivers_required              = ceil(daily_deliveries * cycle_minutes
                                      / productive_minutes_per_driver)
daily_capacity (fleet)        = floor(drivers * cycles_per_driver_per_day)
load_%                        = daily_deliveries * cycle_minutes
                                / (drivers * shift_minutes) * 100
projected_volume              = ceil(baseline * (1 + uplift_% / 100))

Assumptions (all are parameters, so they can be changed and defended)
---------------------------------------------------------------------
1. Every delivery cycle takes the takt time (90 min). This is the planning
   value; real cycle times from the RFID data can be passed in instead.
2. A driver works one shift of 480 minutes (8 hours) per day.
3. Utilisation of 85%: drivers cannot be busy 100% of the shift because of
   breaks, handovers and waiting. 0.85 is a placeholder to confirm with HPC.
4. Drivers are interchangeable, and demand is spread evenly through the day.
5. Whole drivers and whole deliveries only, so we round UP for drivers
   needed (you cannot hire 0.5 of a driver) and DOWN for capacity (you
   cannot complete 0.6 of a delivery).
"""

import math

# --------------------------------------------------------------------------
# Default planning parameters
# --------------------------------------------------------------------------
DEFAULT_CYCLE_MINUTES = 90.0   # takt time used as the cycle length
DEFAULT_SHIFT_MINUTES = 480.0  # 8-hour shift
DEFAULT_UTILISATION = 0.85     # share of the shift a driver is productive


# --------------------------------------------------------------------------
# Private helpers
# --------------------------------------------------------------------------
def _validate(cycle_minutes, shift_minutes, utilisation):
    """Check the three planning parameters shared by every function."""
    if cycle_minutes <= 0:
        raise ValueError("cycle_minutes must be greater than 0")
    if shift_minutes <= 0:
        raise ValueError("shift_minutes must be greater than 0")
    # Utilisation of 0 would divide by zero; above 1 is physically impossible.
    if not 0 < utilisation <= 1:
        raise ValueError("utilisation must be greater than 0 and at most 1")


def _ceil(value):
    """
    Round up, ignoring tiny floating point noise.
    Example: 3.0000000000000004 should give 3, not 4.
    """
    return math.ceil(round(value, 9))


def _floor(value):
    """Round down, ignoring tiny floating point noise (e.g. 12.999999999)."""
    return math.floor(round(value, 9))


# --------------------------------------------------------------------------
# Core capacity calculations
# --------------------------------------------------------------------------
def cycles_per_driver_per_day(cycle_minutes: float = DEFAULT_CYCLE_MINUTES,
                              shift_minutes: float = DEFAULT_SHIFT_MINUTES,
                              utilisation: float = DEFAULT_UTILISATION) -> float:
    """
    How many delivery cycles ONE driver can complete in a day.

    Formula: (shift_minutes * utilisation) / cycle_minutes
    Returned as a float (e.g. 4.53); rounding happens at fleet level.
    """
    _validate(cycle_minutes, shift_minutes, utilisation)
    # Minutes a driver is actually productive, then how many cycles fit in.
    productive_minutes = shift_minutes * utilisation
    return productive_minutes / cycle_minutes


def drivers_required(daily_deliveries: int,
                     cycle_minutes: float = DEFAULT_CYCLE_MINUTES,
                     shift_minutes: float = DEFAULT_SHIFT_MINUTES,
                     utilisation: float = DEFAULT_UTILISATION) -> int:
    """
    Minimum number of drivers needed to complete a daily delivery volume.

    Formula: ceil(daily_deliveries / cycles_per_driver_per_day)
    Rounded UP because a partial driver is not possible.
    """
    _validate(cycle_minutes, shift_minutes, utilisation)
    if daily_deliveries < 0:
        raise ValueError("daily_deliveries cannot be negative")

    # Capacity of a single driver (float, not yet rounded).
    per_driver = cycles_per_driver_per_day(cycle_minutes, shift_minutes,
                                           utilisation)
    # Total demand divided by one driver's capacity, rounded up.
    return _ceil(daily_deliveries / per_driver)


def daily_capacity(num_drivers: int,
                   cycle_minutes: float = DEFAULT_CYCLE_MINUTES,
                   shift_minutes: float = DEFAULT_SHIFT_MINUTES,
                   utilisation: float = DEFAULT_UTILISATION) -> int:
    """
    Maximum deliveries per day the current drivers can complete.

    Formula: floor(num_drivers * cycles_per_driver_per_day)
    Rounded DOWN because only whole deliveries count.
    """
    _validate(cycle_minutes, shift_minutes, utilisation)
    if num_drivers < 0:
        raise ValueError("num_drivers cannot be negative")

    per_driver = cycles_per_driver_per_day(cycle_minutes, shift_minutes,
                                           utilisation)
    return _floor(num_drivers * per_driver)


def load_percent(daily_deliveries: int,
                 num_drivers: int,
                 cycle_minutes: float = DEFAULT_CYCLE_MINUTES,
                 shift_minutes: float = DEFAULT_SHIFT_MINUTES) -> float:
    """
    How busy the drivers are, as a percentage of their full shift time.

    Formula: (daily_deliveries * cycle_minutes) / (num_drivers * shift_minutes) * 100
    Compare with the target utilisation (default 85%). Above the target means
    the fleet is stretched; above 100% means the work cannot be completed.
    """
    if cycle_minutes <= 0 or shift_minutes <= 0:
        raise ValueError("cycle_minutes and shift_minutes must be greater than 0")
    if daily_deliveries < 0:
        raise ValueError("daily_deliveries cannot be negative")
    if num_drivers <= 0:
        raise ValueError("num_drivers must be greater than 0")

    # Minutes of driving work the deliveries create ...
    demand_minutes = daily_deliveries * cycle_minutes
    # ... versus the minutes the drivers have available.
    available_minutes = num_drivers * shift_minutes
    return demand_minutes / available_minutes * 100.0


def capacity_gap(daily_deliveries: int,
                 current_drivers: int,
                 cycle_minutes: float = DEFAULT_CYCLE_MINUTES,
                 shift_minutes: float = DEFAULT_SHIFT_MINUTES,
                 utilisation: float = DEFAULT_UTILISATION) -> int:
    """
    Extra drivers needed (positive) or spare drivers (negative or zero).

    Formula: drivers_required - current_drivers
    """
    if current_drivers < 0:
        raise ValueError("current_drivers cannot be negative")
    needed = drivers_required(daily_deliveries, cycle_minutes,
                              shift_minutes, utilisation)
    return needed - current_drivers


# --------------------------------------------------------------------------
# Scenario planning (the BYD volume increase)
# --------------------------------------------------------------------------
def projected_volume(baseline_daily: int, uplift_percent: float) -> int:
    """
    Daily deliveries after a percentage increase in volume.

    Formula: ceil(baseline * (1 + uplift_percent / 100))
    Rounded UP so the plan is not under-sized.
    A negative uplift models a drop in volume, but cannot go below -100%.
    """
    if baseline_daily < 0:
        raise ValueError("baseline_daily cannot be negative")
    if uplift_percent < -100:
        raise ValueError("uplift_percent cannot be below -100")
    return _ceil(baseline_daily * (1 + uplift_percent / 100.0))


def plan_scenario(baseline_daily: int,
                  uplift_percent: float,
                  current_drivers: int,
                  cycle_minutes: float = DEFAULT_CYCLE_MINUTES,
                  shift_minutes: float = DEFAULT_SHIFT_MINUTES,
                  utilisation: float = DEFAULT_UTILISATION) -> dict:
    """
    Compare today's capacity with a "what if volume grows" scenario.

    Returns a dict the capacity planning page can display:
        baseline_daily, projected_daily, current_drivers,
        current_capacity, drivers_required, additional_drivers,
        load_percent_current_fleet, target_utilisation_percent, sufficient
    """
    # Step 1: what volume do we expect after the uplift?
    projected = projected_volume(baseline_daily, uplift_percent)

    # Step 2: how many drivers does that volume need?
    needed = drivers_required(projected, cycle_minutes, shift_minutes,
                              utilisation)

    # Step 3: how much can the current drivers handle?
    capacity_now = daily_capacity(current_drivers, cycle_minutes,
                                  shift_minutes, utilisation)

    return {
        "baseline_daily": baseline_daily,
        "projected_daily": projected,
        "current_drivers": current_drivers,
        "current_capacity": capacity_now,
        "drivers_required": needed,
        # Never report a negative "additional" figure; spare drivers show as 0.
        "additional_drivers": max(needed - current_drivers, 0),
        # How loaded would today's drivers be under the new volume?
        "load_percent_current_fleet": load_percent(
            projected, current_drivers, cycle_minutes, shift_minutes),
        "target_utilisation_percent": utilisation * 100.0,
        # True when today's drivers can absorb the projected volume.
        "sufficient": projected <= capacity_now,
    }
