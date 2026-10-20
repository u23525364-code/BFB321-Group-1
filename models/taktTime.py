""""
taktTime.py serves as a takt time compliance and cycle time calculator for drivers at HPC.

Key terms: 
-Cycle time: the elapsed time of one delivery cycle for a driver, measured from one RFID scan to another. 
-Takt time: the maximum time one cycle is allowed to take. HPC takt time is defined as 90 minutes per cycle. 

Status Rules: 
on_track : elapsed time less than a defined fraction (80%) of the takt time.
at_risk : elapsed time more than 80% of the takt time, possibly might run over time.
breached : the elapsed time is already greater than takt time.
"""
from datetime import datetime

TAKT_TIME_MINUTES = 90.0
AT_RISK_FRACTION = 0.8

STATUS_ON_TRACK = "on_track"
STATUS_AT_RISK = "at_risk"
STATUS_BREACHED = "breached"

"""The Following 3 functions are Value checks to ensure the inputted values down the line are within the correct ranges."""

def check_takt(takt_min):
    if takt_min <= 0:
        raise ValueError("takt_min must be greater than 0.")

def check_fraction(at_risk_fraction):
    if not 0 < at_risk_fraction < 1:
        raise ValueError("at_risk_fraction must be between 0 and 1 exclusive")

def check_elapsed(elapsed_min):
    if elapsed_min < 0: 
        raise ValueError("elapsed_min can not be negative.")

"""The following 5 functions address the core calculations needed in the model."""

def cycle_time_minutes(start: datetime, 
                       end: datetime) -> float: 

    """The time between the start and the end is calculated as the duration of the cycle."""
    duration = end - start
    """The following checks that the end and start time were inputted in the correct order."""
    if duration.total_seconds() < 0: 
        raise ValueError("end must not be earlier than start.")

    return duration.total_seconds()/ 60

def takt_used_percent(elapsed_min: float, 
                      takt_min: float = TAKT_TIME_MINUTES) -> float:
    
    check_elapsed(elapsed_min)
    check_takt(takt_min)
    """Simple percentage calculation showing the amout of the takt time used by the cycle"""
    return elapsed_min/ takt_min *100

def minutes_remaining(elapsed_min: float, 
                      takt_min: float = TAKT_TIME_MINUTES) -> float:
    check_elapsed(elapsed_min)
    check_takt(takt_min)
    """Calculation for how much time out of the takt time is remaining."""
    return takt_min - elapsed_min

def is_breach(elapsed_min: float, takt_min: float = TAKT_TIME_MINUTES) -> bool:
    check_elapsed(elapsed_min)
    check_takt(takt_min)
    """Logical check of whether the cycle time exceeds the takt time."""
    return elapsed_min > takt_min

def classify_status(elapsed_min: float, 
                    takt_min: float = TAKT_TIME_MINUTES,
                    at_risk_fraction: float = AT_RISK_FRACTION) -> str:
   
    check_elapsed(elapsed_min)
    check_takt(takt_min)
    check_fraction(at_risk_fraction)
    """this function classifies the cycle times according to the defined criteria."""
    at_risk_limit = takt_min * at_risk_fraction

    if elapsed_min > takt_min:
        return STATUS_BREACHED
    if elapsed_min >= at_risk_limit:
        return STATUS_AT_RISK
    return STATUS_ON_TRACK

"""These are further support calculations and data display functions"""

def average_cycle_time(cycle_times: list) -> float:
    if len(cycle_times) == 0:
        raise ValueError("cycle_times must not be empty.")
    return sum(cycle_times)/ len(cycle_times)

def compliance_rate(cycle_times: list,
                    takt_min: float = TAKT_TIME_MINUTES) -> float:
    
    check_takt(takt_min)
    if len(cycle_times) == 0:
            raise ValueError("cycle_times must not be empty.")

    within = sum(1 for t in cycle_times if t <= takt_min)
    return within/ len(cycle_times) * 100

def summarise_cycles(cycle_times:list,
                     takt_min: float = TAKT_TIME_MINUTES,
                     at_risk_fraction: float = AT_RISK_FRACTION) -> dict:

    check_takt(takt_min)
    check_fraction(at_risk_fraction)

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

    statuses = [classify_status(t, takt_min, at_risk_fraction) 
                for t in cycle_times]

    return {
        "count": len(cycle_times),
        "average_minutes": average_cycle_time(cycle_times),
        "max_minutes": max(cycle_times),
        "compliance_pct": compliance_rate(cycle_times, takt_min),
        "breaches": statuses.count(STATUS_BREACHED),
        "on_track": statuses.count(STATUS_ON_TRACK),
        "at_risk": statuses.count(STATUS_AT_RISK),
        "breached": statuses.count(STATUS_BREACHED),
    }
    


