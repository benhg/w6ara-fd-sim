# Define sources
gen = PowerSource("Honda Generator", max_power_w=2000, voltage_v=120)
truck = PowerSource("F150 Lightning", max_power_w=2000, voltage_v=240, total_energy_wh=120_000)

# Define sinks
radio = LoadComponent("Radio", 50)
amp = LoadComponent("Amplifier", 500, duty_cycle=[0.5 if 8 <= h <= 20 else 0 for h in range(24)])
computer = LoadComponent("Computer", 20)
network = LoadComponent("Network", 20)

cw_station = PowerSink("CW Station", components=[radio, amp, computer, network], location=(0, 0))
phone_station = PowerSink("Phone Station", base_load_w=600, location=(1, 0))
satellite_station = PowerSink("Phone Station", base_load_w=600, location=(1, 0))
digital_station = PowerSink("Digital Station", base_load_w=800, location=(20, 0))
tent = PowerSink("Hospitality Tent", base_load_w=300, schedule=[300 if h != 20 else 1500 for h in range(24)], location=(1, 2))