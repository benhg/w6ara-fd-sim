class PowerSource:
    def __init__(self, name, max_power_w, voltage_v, total_energy_wh=float('inf'), location=None):
        self.name = name
        self.max_power_w = max_power_w
        self.voltage_v = voltage_v
        self.total_energy_wh = total_energy_wh
        self.location = location  # (x, y) coordinate on the site

        # Track energy used per hour
        self.schedule = [0.0] * 24  # W per hour

    def can_supply(self, hour, load_w):
        return (self.schedule[hour] + load_w <= self.max_power_w)

    def assign_load(self, hour, load_w):
        if not self.can_supply(hour, load_w):
            raise ValueError(f"{self.name} cannot supply {load_w}W at hour {hour}")
        self.schedule[hour] += load_w

    def total_energy_used(self):
        return sum(self.schedule)

class PowerSink:
    def __init__(self, name, base_load_w, schedule=None, location=None):
        self.name = name
        self.base_load_w = base_load_w
        self.location = location  # (x, y) coordinate

        # load schedule: 24-element array, overrides base load if provided
        if schedule is None:
            self.schedule = [base_load_w] * 24
        else:
            self.schedule = schedule

class FieldDaySite:
    def __init__(self):
        self.sources = []
        self.sinks = []

    def add_source(self, source):
        self.sources.append(source)

    def add_sink(self, sink):
        self.sinks.append(sink)

    def distance(self, loc1, loc2):
        if loc1 is None or loc2 is None:
            return float('inf')
        x1, y1 = loc1
        x2, y2 = loc2
        return ((x2 - x1)**2 + (y2 - y1)**2)**0.5

