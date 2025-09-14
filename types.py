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

class LoadComponent:
    def __init__(self, name, power_w, duty_cycle=None):
        self.name = name
        self.power_w = power_w
        
        # If no schedule, assume always on
        if duty_cycle is None:
            self.duty_cycle = [1.0] * 24  # 100% on
        else:
            self.duty_cycle = duty_cycle  # list of floats [0.0–1.0], 24 elements

    def power_at_hour(self, hour):
        return self.power_w * self.duty_cycle[hour]



class PowerSink:
    def __init__(self, name, components=None, location=None):
        self.name = name
        self.components = components or []  # list of LoadComponent
        self.location = location

    def total_power_at_hour(self, hour):
        return sum(comp.power_at_hour(hour) for comp in self.components)

    def schedule(self):
        """Return a 24-element list of total power draw per hour"""
        return [self.total_power_at_hour(h) for h in range(24)]

    def add_component(self, component):
        self.components.append(component)

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

