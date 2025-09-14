from types import PowerSource, LoadComponent, PowerSink

# Define sources
gen_1 = PowerSource("Honda Generator 1", max_power_w=2000, voltage_v=120)
gen_2 = PowerSource("Honda Generator 2", max_power_w=2000, voltage_v=120)
truck = PowerSource(
    "F150 Lightning", max_power_w=2000, voltage_v=240, total_energy_wh=120_000
)
p2 = PowerSource(
    "Polestar 2", max_power_w=100, voltage_v=120, total_energy_wh=78_000
)

# Shared components
computer = LoadComponent("Computer", 20)
network = LoadComponent("Network", 20)

# CW Station
cw_radio = LoadComponent("CW Radio", 50)
cw_amp = LoadComponent(
    "CW Amplifier", 500, duty_cycle=[0.5 if 8 <= h <= 20 else 0 for h in range(24)]
)
cw_station = PowerSink(
    "CW Station", components=[cw_radio, cw_amp, computer, network], location=(0, 0)
)

# Phone Station
phone_rig = LoadComponent("Phone Rig", 200)
phone_amp = LoadComponent("Phone Amp", 400)
phone_station = PowerSink(
    "Phone Station", components=[phone_rig, phone_amp, computer, network], location=(1, 0)
)

# Satellite Station
sat_rig = LoadComponent("Satellite Rig", 120)
equipment = LoadComponent("Other satellite equipment", 100)
satellite_station = PowerSink(
    "Satellite Station",
    components=[sat_rig, equipment, computer, network],
    location=(2, 0),
)

# GOTA Station
gota_rig = LoadComponent("GOTA Rig", 120)
gota_station = PowerSink(
    "GOTA Station", components=[gota_rig, computer, network], location=(3, 0)
)

# Digital Station
digital_rig = LoadComponent("Digital Rig", 120)
extra_computer = LoadComponent("Extra Computer", 50)
digital_station = PowerSink(
    "Digital Station",
    components=[digital_rig, extra_computer, computer, network],
    location=(4, 0),
)

# Hospitality Station (tent)
lights = LoadComponent("Lights", 150)
coffee_spike = LoadComponent(
    "Coffee/Heater",
    1200,
    duty_cycle=[0.0 if h != 20 else 1.0 for h in range(24)],
)
hospitality_station = PowerSink(
    "Hospitality Station", components=[lights, coffee_spike], location=(1, 2)
)
