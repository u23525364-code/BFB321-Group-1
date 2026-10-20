import math

#Default planning parameters
default_cycle_minutes = 90.0  #takt time
default_shift_minutes = 480.0 #8-hour shift
default_utilisation = 0.85  #part of shift the driver is productive

#Private helpers
def validate(cycle_minutes, shift_minutes, utilisation):
    if cycle_minutes <= 0:
        raise ValueError("cycle_minutes must be more than 0")
    if shift_minutes <= 0:
        raise ValueError("shift_minutes must be more than 0")
    if not 0<utilisation<=1:
        raise ValueError("utilisation must be between 0 and 1")

def ceil(value):
    return math.ceil(round(value,9))            

def floor(value):
    return math.floor(round(value,9))

#Capacacity calculations
def cycles_per_driver_per_day(cycle_minutes: float=default_cycle_minutes,
                              shift_minutes: float=default_shift_minutes,
                              utilisation: float=default_utilisation):
    validate(cycle_minutes, shift_minutes, utilisation)
    productive_minutes=shift_minutes * utilisation
    return productive_minutes/cycle_minutes

def drivers_required(daily_deliveries: int,                     #Minimum number of drivers needed for delivery volume
                     cycle_minutes: float=default_cycle_minutes,
                     shift_minutes: float=default_shift_minutes,
                     utilisation: float=default_utilisation):
    validate(cycle_minutes, shift_minutes, utilisation)
    if daily_deliveries<0:
        raise ValueError("daily deliveries must be more than 0")

    #Single driver's capacity
    per_driver_capacity=cycles_per_driver_per_day(cycle_minutes, shift_minutes, utilisation)
    return ceil(daily_deliveries/per_driver_capacity)  #total demand divided by one driver's capacity

def daily_capacity(num_drivers: int,            #max number of deliveries the drivers can complete in a day)
                   cycle_minutes: float = default_cycle_minutes,
                   shift_minutes: float = default_shift_minutes,
                   utilisation: float = default_utilisation):

    validate(cycle_minutes, shift_minutes, utilisation)
    if num_drivers<0:
        raise ValueError("number of drivers must be more than 0")

    per_driver_capacity=cycles_per_driver_per_day(cycle_minutes, shift_minutes, utilisation)
    return floor(num_drivers*per_driver_capacity) #total capacity is number of drivers multiplied by one driver's capacity

def load_percent(daily_deliveries: int,            #how busy drivers are as a percentage of their shift time
                 num_drivers: int,
                 cycle_minutes: float = default_cycle_minutes,
                 shift_minutes: float = default_shift_minutes):
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
                 cycle_minutes: float = default_cycle_minutes,
                 shift_minutes: float = default_shift_minutes,
                 utilisation: float = default_utilisation):
 #How many extra drivers are needed or how many spare drivers that are not needed
    if current_drivers<0:
        raise ValueError("current drivers must be more than 0")
    needed = drivers_required(daily_deliveries, cycle_minutes, shift_minutes, utilisation)
    return needed-current_drivers


#Scenario planning for the BYD volume increase
def projected_volume(baseline_daily: int, uplift_percent: float):
    #daily deliveries after volume increases by a percentage
    #Rounded up so the plan is not under-sized
    #A negative uplift models a reduction in volume, but cannot be more than 100% (which would be negative deliveries)
    if baseline_daily<0:
        raise ValueError("baseline daily deliveries must be more than 0")
    if uplift_percent<-100:
        raise ValueError("uplift percent must be more than -100")
    return ceil(baseline_daily*(1+uplift_percent/100))

def plan_scenario(baseline_daily: int,
                  uplift_percent:float,
                  current_drivers:int,
                  cycle_minutes:float=default_cycle_minutes,
                  shift_minutes:float=default_shift_minutes,
                  utilisation:float=default_utilisation):
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
