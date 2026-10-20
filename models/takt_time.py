"""
takt_time.py - Takt time compliance and cycle time calculations for HPC drivers.

This module is a STANDALONE supply chain model. It imports nothing from Flask
or from the database layer, so it can be tested on its own and later called
by the API layer (app/services) exactly as the BFB 321 guide requires.

Key terms
---------
cycle time : the elapsed minutes of one delivery cycle for a driver, measured
             from one RFID scan to another (e.g. GATE-IN to GATE-OUT).
takt time  : the maximum time one cycle is allowed to take. HPC's takt is
             90 minutes per cycle.

Formulas
--------
cycle_time          = (end_timestamp - start_timestamp) in minutes
takt_used_%         = cycle_time / takt_time * 100
minutes_remaining   = takt_time - cycle_time        (negative = overrun)
compliance_rate_%   = cycles with cycle_time <= takt_time / total cycles * 100

Status rules (applied to the elapsed time of a cycle)
-----------------------------------------------------
on_track : elapsed <  at_risk_fraction * takt   (default < 72 min)
at_risk  : at_risk_fraction * takt <= elapsed <= takt   (72 to 90 min)
breached : elapsed > takt                       (over 90 min)

Assumptions
-----------
1. A cycle that takes exactly the takt time is still compliant (not a breach).
2. The 80% "at risk" warning threshold is a design choice, not a given fact.
   It should be agreed with HPC (Terry) and can be changed via a parameter.
3. All timestamps are in the same time zone (RFID readers share one clock).
"""

from datetime import datetime

# --------------------------------------------------------------------------
# Constants (single source of truth, so the numbers are never hard-coded
# in several places)
# --------------------------------------------------------------------------
TAKT_TIME_MINUTES = 90.0   # HPC's allowed time per driver cycle
AT_RISK_FRACTION = 0.80    # warn once 80% of the takt time has been used

# Status labels. The dashboard and API will use these exact strings.
STATUS_ON_TRACK = "on_track"
STATUS_AT_RISK = "at_risk"
STATUS_BREACHED = "breached"


# --------------------------------------------------------------------------
# Small private helpers for input validation
# --------------------------------------------------------------------------
def _check_takt(takt_minutes):
    """Reject a takt time that is zero or negative (it would break the maths)."""
    if takt_minutes <= 0:
        raise ValueError("takt_minutes must be greater than 0")


def _check_fraction(at_risk_fraction):
    """The at-risk threshold must be a fraction strictly between 0 and 1."""
    if not 0 < at_risk_fraction < 1:
        raise ValueError("at_risk_fraction must be between 0 and 1 (exclusive)")


def _check_elapsed(elapsed_minutes):
    """Elapsed time cannot be negative (that would mean time ran backwards)."""
    if elapsed_minutes < 0:
        raise ValueError("elapsed_minutes cannot be negative")


# --------------------------------------------------------------------------
# Core calculations
# --------------------------------------------------------------------------
def cycle_time_minutes(start: datetime, end: datetime) -> float:
    """
    Calculate the elapsed time between two RFID scans, in minutes.

    Formula: (end - start) / 60 seconds

    Inputs : start, end - datetime objects (e.g. GATE-IN and GATE-OUT scans)
    Output : float, minutes elapsed
    Raises : ValueError if end is earlier than start (bad or mis-paired data)
    """
    # Subtracting two datetimes gives a timedelta (a duration).
    duration = end - start

    # A negative duration means the scans were paired incorrectly.
    # Failing loudly here is better than silently producing a wrong KPI.
    if duration.total_seconds() < 0:
        raise ValueError("end must not be earlier than start")

    # Convert seconds to minutes.
    return duration.total_seconds() / 60.0


def takt_used_percent(elapsed_minutes: float,
                      takt_minutes: float = TAKT_TIME_MINUTES) -> float:
    """
    Percentage of the takt time already used. Drives the progress bar on the
    driver status list (can exceed 100 when the cycle has overrun).

    Formula: elapsed / takt * 100
    """
    _check_elapsed(elapsed_minutes)
    _check_takt(takt_minutes)
    return elapsed_minutes / takt_minutes * 100.0


def minutes_remaining(elapsed_minutes: float,
                      takt_minutes: float = TAKT_TIME_MINUTES) -> float:
    """
    Minutes left before the takt time is breached.

    Formula: takt - elapsed
    A negative result means the cycle has overrun by that many minutes.
    """
    _check_elapsed(elapsed_minutes)
    _check_takt(takt_minutes)
    return takt_minutes - elapsed_minutes


def is_breach(elapsed_minutes: float,
              takt_minutes: float = TAKT_TIME_MINUTES) -> bool:
    """
    True if the cycle took LONGER than the takt time.
    Exactly equal to the takt time is NOT a breach (see Assumption 1).
    """
    _check_elapsed(elapsed_minutes)
    _check_takt(takt_minutes)
    return elapsed_minutes > takt_minutes


def classify_status(elapsed_minutes: float,
                    takt_minutes: float = TAKT_TIME_MINUTES,
                    at_risk_fraction: float = AT_RISK_FRACTION) -> str:
    """
    Classify a cycle as on_track, at_risk or breached.

    Used for the colour-coded driver status on the dashboard
    (green / amber / red).
    """
    _check_elapsed(elapsed_minutes)
    _check_takt(takt_minutes)
    _check_fraction(at_risk_fraction)

    # Work out where the warning line sits (default 0.8 * 90 = 72 minutes).
    at_risk_limit = takt_minutes * at_risk_fraction

    # Check the worst case first: over the takt time is a breach.
    if elapsed_minutes > takt_minutes:
        return STATUS_BREACHED
    # Between the warning line and the takt time (inclusive) is at risk.
    if elapsed_minutes >= at_risk_limit:
        return STATUS_AT_RISK
    # Anything below the warning line is fine.
    return STATUS_ON_TRACK


# --------------------------------------------------------------------------
# Aggregate KPIs (many cycles at once, e.g. a driver, a day, a week)
# --------------------------------------------------------------------------
def average_cycle_time(cycle_times: list) -> float:
    """
    Mean cycle time in minutes.

    Formula: sum(cycle_times) / number of cycles
    Raises ValueError on an empty list (an average of nothing is undefined).
    """
    if len(cycle_times) == 0:
        raise ValueError("cycle_times must not be empty")
    return sum(cycle_times) / len(cycle_times)


def compliance_rate(cycle_times: list,
                    takt_minutes: float = TAKT_TIME_MINUTES) -> float:
    """
    Percentage of cycles completed within the takt time (the "on-time %" card).

    Formula: cycles with time <= takt / total cycles * 100
    Raises ValueError on an empty list.
    """
    _check_takt(takt_minutes)
    if len(cycle_times) == 0:
        raise ValueError("cycle_times must not be empty")

    # Count only the cycles that finished inside the takt time.
    within = sum(1 for t in cycle_times if t <= takt_minutes)
    return within / len(cycle_times) * 100.0


def summarise_cycles(cycle_times: list,
                     takt_minutes: float = TAKT_TIME_MINUTES,
                     at_risk_fraction: float = AT_RISK_FRACTION) -> dict:
    """
    Build the full KPI summary for a set of cycle times.

    Returns a dict the API can send straight to the dashboard:
        count, average_minutes, max_minutes, compliance_pct, breaches,
        on_track, at_risk, breached

    An empty list is allowed (e.g. a quiet day) and returns zero counts with
    None for the averages, so the dashboard can show an "empty state"
    instead of crashing.
    """
    _check_takt(takt_minutes)
    _check_fraction(at_risk_fraction)

    # Quiet period: nothing to calculate, so return a safe "empty" result.
    if len(cycle_times) == 0:
        return {
            "count": 0,
            "average_minutes": None,
            "max_minutes": None,
            "compliance_pct": None,
            "breaches": 0,
            "on_track": 0,
            "at_risk": 0,
            "breached": 0,
        }

    # Classify every cycle once, then count how many fall in each status.
    statuses = [classify_status(t, takt_minutes, at_risk_fraction)
                for t in cycle_times]

    return {
        "count": len(cycle_times),
        "average_minutes": average_cycle_time(cycle_times),
        "max_minutes": max(cycle_times),
        "compliance_pct": compliance_rate(cycle_times, takt_minutes),
        # "breaches" and "breached" are the same number; "breaches" matches the
        # dashboard card name, "breached" completes the three-status breakdown.
        "breaches": statuses.count(STATUS_BREACHED),
        "on_track": statuses.count(STATUS_ON_TRACK),
        "at_risk": statuses.count(STATUS_AT_RISK),
        "breached": statuses.count(STATUS_BREACHED),
    }
