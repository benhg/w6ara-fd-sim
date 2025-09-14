"""
Edit this file to control per-station duty multipliers for each hour.

Each value is a 24-element list of floats in [0.0, 1.0+] applied to the
station's computed per-hour load. 1.0 means full load, 0.0 means off.

Station names must match those in instances.py exactly.
"""

STATION_DUTY = {
    # Active all day by default. Example: turn off overnight by setting 0.0 for hours 0–6, 22–23.
    "Phone Station": [0.5] * 24,
    "CW Station": [0.7] * 24,
    "Satellite Station": [0.5] * 24,
    "GOTA Station": [0.3] * 24,
    "Digital Station": [0.75] * 24,
    "Hospitality Station": [1.0] * 24,
}

# Example pattern you can use:
# DAY_ON = [1.0 if 8 <= h <= 20 else 0.0 for h in range(24)]
# STATION_DUTY["GOTA Station"] = DAY_ON
