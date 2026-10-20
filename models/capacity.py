import math

#Default planning parameters
DEFAULT_CYCLE_MINUTES = 90.0  #takt time
DEFAULT_SHIFT_MINUTES = 480.0 #8-hour shift
DEFAULT_UTILISATION = 0.85  #part of shift the driver is productive

#Private helpers
def validate(cycle_minutes, shift_minutes, utilisation):
    if cycle_minutes <= 0:
        raise ValueError("cycle_minutes must be more than 0")
    if shift_minutes <= 0:
        raise ValueError("shift_minutes must be more than 0")
    if not 0<utilisation<=1:
        raise ValueError("utilisation must be between 0 and 1")

def ceil(value):
    """round up, ignoring tiny floating point noise. for example 3.00000000000000004 should give 3 and not 4 """
    return math.ceil(round(value,9))            

def floor(value):
    """round down, ignoring tiny floating point noise."""
    return math.floor(round(value,9))

#Capacacity calculations
def cycles_per_driver_per_day(cycle_minutes: float=DEFAULT_CYCLE_MINUTES,
                              shift_minutes: float=DEFAULT_SHIFT_MINUTES,
                              utilisation: float=DEFAULT_UTILISATION):
    """define how many delivery cycles one driver can do in a day. 
       formula: (shift minutes * utilisation)/cycle minutes"""
    validate(cycle_minutes, shift_minutes, utilisation)
    productive_minutes=shift_minutes * utilisation
    return productive_minutes/cycle_minutes

def drivers_required(daily_deliveries: int,                     
                     cycle_minutes: float=DEFAULT_CYCLE_MINUTES,
                     shift_minutes: float=DEFAULT_SHIFT_MINUTES,
                     utilisation: float=DEFAULT_UTILISATION):
    """define how many drivers are needed to complete the daily delivery volume.
       formula: daily deliveries / (shift minutes * utilisation)/cycle minutes
       Rounded up because you cannot have a fraction of a driver."""
    validate(cycle_minutes, shift_minutes, utilisation)
    if daily_deliveries<0:
        raise ValueError("daily deliveries must be more than 0")

    #Single driver's capacity
    per_driver_capacity=cycles_per_driver_per_day(cycle_minutes, shift_minutes, utilisation)
    return ceil(daily_deliveries/per_driver_capacity)  #total demand divided by one driver's capacity

def daily_capacity(num_drivers: int,            
                   cycle_minutes: float = DEFAULT_CYCLE_MINUTES,
                   shift_minutes: float = DEFAULT_SHIFT_MINUTES,
                   utilisation: float = DEFAULT_UTILISATION):
    """max number of deliveries the drivers can complete daily
    formula: floor(num_drivers * (shift_minutes * utilisation)/cycle_minutes)
    Rounded down because only whole deliveries count."""

    validate(cycle_minutes, shift_minutes, utilisation)
    if num_drivers<0:
        raise ValueError("number of drivers must be more than 0")

    per_driver_capacity=cycles_per_driver_per_day(cycle_minutes, shift_minutes, utilisation)
    return floor(num_drivers*per_driver_capacity) 

def load_percent(daily_deliveries: int,            
                 num_drivers: int,
                 cycle_minutes: float = DEFAULT_CYCLE_MINUTES,
                 shift_minutes: float = DEFAULT_SHIFT_MINUTES):
     """How busy the drivers are as a percentage of their shift time.
     Formula: (daily_deliveries * cycle_minutes)/(num_drivers*shift_minutes)*100)
     Compare it with the target utilisation (default is 85%). Above the target means the fleet is strechted
     """
     if cycle_minutes<=0 or shift_minutes<=0:
         raise ValueError("cycle and shift must be more than 0")
     if daily_deliveries<0:
         raise ValueError("daily deliveries must be more than 0")
     if num_drivers<=0:
         raise ValueError("number of drivers must be more than 0")

     demand_minutes=daily_deliveries*cycle_minutes
     available_minutes=num_drivers*shift_minutes
     return demand_minutes/available_minutes*100

def capacity_gap(daily_deliveries: int,
                 current_drivers: int,
                 cycle_minutes: float = DEFAULT_CYCLE_MINUTES,
                 shift_minutes: float = DEFAULT_SHIFT_MINUTES,
                 utilisation: float = DEFAULT_UTILISATION):
    """How many extra drivers are needed (positive) or how many spare drivers that are not needed (negative)
    formula: drivers_required - drivers_current
    Rounded up because you cannot have a fraction of a driver."""

    if current_drivers<0:
        raise ValueError("current drivers must be more than 0")
    needed = drivers_required(daily_deliveries, cycle_minutes, shift_minutes, utilisation)
    return needed-current_drivers


#Scenario planning for the BYD volume increase
def projected_volume(baseline_daily: int, uplift_percent: float):
    """daily deliveries after volume increases by a percentage
        formula: ceil(baseline_daily*(1+uplift_percent/100))
        Rounded up so the plan is not under-sized
        A negative uplift models a reduction in volume, but cannot be more than 100% (which would be negative deliveries)"""
    if baseline_daily<0:
        raise ValueError("baseline daily deliveries must be more than 0")
    if uplift_percent<-100:
        raise ValueError("uplift percent must be more than -100")
    return ceil(baseline_daily*(1+uplift_percent/100))

def plan_scenario(baseline_daily: int,
                  uplift_percent:float,
                  current_drivers:int,
                  cycle_minutes:float=DEFAULT_CYCLE_MINUTES,
                  shift_minutes:float=DEFAULT_SHIFT_MINUTES,
                  utilisation:float=DEFAULT_UTILISATION):
    """ Compare todays capacity with the projected volume after a percentage increase in deliveries.
            Returns a dict the capacity planning page can display:
            baseline_daily, projected_daily, current_drivers,
            current_capacity, drivers_required, additional_drivers,
            load_percent_current_fleet, target_utilisation_percent, sufficien"""
    #step1: what volume is expected after the uplift?
    projected=projected_volume(baseline_daily, uplift_percent)
    #step2: how many drivers are needed for that volume?
    needed=drivers_required(projected, cycle_minutes, shift_minutes, utilisation)
    #step3: how much can the current drivers do?
    capacity_now=daily_capacity(current_drivers,cycle_minutes,shift_minutes,utilisation)

    return {
        "baseline_daily": baseline_daily,
        "projected_daily": projected,
        "current_drivers": current_drivers,
        "current_capacity":capacity_now,
        "drivers_required":needed,
        #additional drivers should not be negative
        "additional_drivers":max(needed-current_drivers,0),
        #How would the increased volume affect the drivers' load
        "load_percent_current_fleet":load_percent(projected, current_drivers, cycle_minutes, shift_minutes),
        "target_utilisation_percent":utilisation*100.0,
        #Can the drivers absorb the increased volume? True if yes
        "sufficient":projected<=capacity_now
    }
