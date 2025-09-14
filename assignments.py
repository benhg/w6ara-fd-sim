"""
Edit this file to assign stations (sinks) to specific power sources.

Map each station name to a list of source names. Order matters: the scheduler
tries the first source, then the next, etc., until the station's hourly demand
is satisfied.

Station and source names must match instances.py exactly.
"""

ASSIGNMENTS = {
    # Example mapping:
    "CW Station": ["Honda Generator 1"],
    "Phone Station": ["Honda Generator 1"],
    "Satellite Station": ["F150 Lightning"],
    "GOTA Station": ["Polestar 2"],
    "Digital Station": ["Honda Generator 2"],
    "Hospitality Station": ["F150 Lightning"],
}

