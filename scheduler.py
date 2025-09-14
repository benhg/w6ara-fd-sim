"""
Simple scheduler for w6ara-fd-sim.

Generates a 24-hour allocation of sink loads to power sources while tracking
each source's state of charge (SOC) based on `total_energy_wh` and `max_power_w`.

Usage (from repo root):
    python -m scheduler

This will run a small demo if executed directly. For real scenarios, construct
`FieldDaySite` with your `PowerSource` and `PowerSink` instances and call
`generate_schedule(site)`.
"""

from typing import Dict, List, Tuple, Optional
import sys
import importlib.util
import pathlib


def _import_types_module():
    """Load local types.py as a real module and register it under `types`.

    This avoids collision with stdlib `types` and ensures instances.py imports
    the local classes with identical identity for isinstance checks.
    """
    types_path = pathlib.Path(__file__).with_name("types.py")
    spec = importlib.util.spec_from_file_location("fd_types", types_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to locate local types.py")
    module = importlib.util.module_from_spec(spec)
    # Make available as both fd_types and types
    sys.modules.setdefault("fd_types", module)
    sys.modules["types"] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


TYPES = _import_types_module()


def compute_sink_loads_by_hour(
    sinks: List["TYPES.PowerSink"],
    hours: int = 24,
    station_duty: Optional[Dict[str, List[float]]] = None,
) -> Tuple[List[float], Dict[str, List[float]]]:
    """Return total site demand per hour and per-sink breakdown.

    - sinks: list of PowerSink
    - hours: typically 24
    """
    per_sink: Dict[str, List[float]] = {}
    total = [0.0 for _ in range(hours)]
    for sink in sinks:
        base = [sink.total_power_at_hour(h) for h in range(hours)]
        # Apply optional per-station duty multiplier per hour
        if station_duty and sink.name in station_duty:
            duty = station_duty[sink.name]
            if len(duty) != hours:
                raise ValueError(f"Duty list for {sink.name} must have {hours} elements")
            sched = [base[h] * float(duty[h]) for h in range(hours)]
        else:
            sched = base
        per_sink[sink.name] = sched
        for h, w in enumerate(sched):
            total[h] += w
    return total, per_sink


def reset_source_schedules(sources: List["TYPES.PowerSource"], hours: int = 24) -> None:
    """Zero out per-hour schedules for a fresh solve."""
    for s in sources:
        s.schedule = [0.0 for _ in range(hours)]


def generate_schedule(
    site: "TYPES.FieldDaySite",
    hours: int = 24,
    policy: str = "battery_last",
    station_duty: Optional[Dict[str, List[float]]] = None,
    assignments: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Dict[str, List[float]]]:
    """Allocate hourly loads to sources and track SOC.

    Returns a dict with keys:
    - source_power_w: {source_name: [W_per_hour]}
    - source_energy_remaining_wh: {source_name: [remaining_Wh_after_hour]}
    - unmet_load_w: [W_per_hour_unserved]

    Policy:
    - "battery_last": prioritize infinite-energy sources first (e.g., generators).
    - "battery_first": prioritize finite-energy sources first (e.g., batteries).

    Assignments:
    - Optional mapping {sink_name: [source_name, ...]} to constrain which sources
      power a given sink. Order matters; allocation follows the list.
    """

    sources = list(site.sources)
    sinks = list(site.sinks)

    reset_source_schedules(sources, hours)
    _, per_sink_loads = compute_sink_loads_by_hour(sinks, hours, station_duty)

    # Determine ordering based on policy for sinks without explicit assignment
    def is_infinite(s: "TYPES.PowerSource") -> bool:
        return s.total_energy_wh == float("inf")

    if policy == "battery_last":
        default_ordered_sources = sorted(sources, key=lambda s: is_infinite(s), reverse=True)
    elif policy == "battery_first":
        default_ordered_sources = sorted(sources, key=lambda s: is_infinite(s))
    else:
        default_ordered_sources = sources

    # Map names to instances
    sources_by_name: Dict[str, "TYPES.PowerSource"] = {s.name: s for s in sources}
    sinks_by_name: Dict[str, "TYPES.PowerSink"] = {sk.name: sk for sk in sinks}

    # Track remaining energy per source across hours
    remaining_wh: Dict[str, float] = {
        s.name: (float("inf") if is_infinite(s) else float(s.total_energy_wh)) for s in sources
    }

    source_power_w: Dict[str, List[float]] = {s.name: [0.0 for _ in range(hours)] for s in sources}
    source_energy_remaining_wh: Dict[str, List[float]] = {s.name: [remaining_wh[s.name]] for s in sources}
    unmet_load_w: List[float] = [0.0 for _ in range(hours)]

    for h in range(hours):
        unmet_this_hour = 0.0

        # Allocate per sink based on explicit assignments
        for sink_name, sink in sinks_by_name.items():
            demand_w = per_sink_loads[sink_name][h]
            if demand_w <= 0:
                continue

            # Determine candidate source list
            if assignments and sink_name in assignments:
                candidate_names = assignments[sink_name]
                candidate_sources: List["TYPES.PowerSource"] = []
                for name in candidate_names:
                    if name not in sources_by_name:
                        raise ValueError(f"Assignment references unknown source: {name}")
                    candidate_sources.append(sources_by_name[name])
            else:
                candidate_sources = default_ordered_sources

            remaining_demand = demand_w

            for s in candidate_sources:
                name = s.name
                # Headroom remaining for this hour on this source
                hourly_headroom_w = max(0.0, s.max_power_w - s.schedule[h])
                # Energy constraint bounds power this hour
                energy_limit_w = remaining_wh[name] if remaining_wh[name] != float("inf") else float("inf")
                available_w = min(hourly_headroom_w, energy_limit_w)

                if available_w <= 0 or remaining_demand <= 0:
                    continue

                assign_w = min(remaining_demand, available_w)
                s.assign_load(h, assign_w)
                source_power_w[name][h] += assign_w
                if remaining_wh[name] != float("inf"):
                    remaining_wh[name] = max(0.0, remaining_wh[name] - assign_w)
                remaining_demand -= assign_w

            if remaining_demand > 0:
                unmet_this_hour += remaining_demand

        unmet_load_w[h] = unmet_this_hour

        # After hour h, record remaining energy snapshot for all sources
        for s in sources:
            name = s.name
            source_energy_remaining_wh[name].append(remaining_wh[name])

    # Normalize snapshots to `hours`
    for name in source_energy_remaining_wh:
        seq = source_energy_remaining_wh[name]
        source_energy_remaining_wh[name] = seq[1 : hours + 1]

    return {
        "source_power_w": source_power_w,
        "source_energy_remaining_wh": source_energy_remaining_wh,
        "unmet_load_w": unmet_load_w,
    }


def build_site_from_instances() -> "TYPES.FieldDaySite":
    """Import sources and sinks from instances.py and return a FieldDaySite."""
    # Ensure local types are loaded and registered under 'types'
    _ = TYPES
    inst_path = pathlib.Path(__file__).with_name("instances.py")
    spec = importlib.util.spec_from_file_location("fd_instances", inst_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to locate local instances.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("fd_instances", module)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]

    site = TYPES.FieldDaySite()
    # Collect sources and sinks
    for attr in vars(module).values():
        if isinstance(attr, TYPES.PowerSource):
            site.add_source(attr)
        elif isinstance(attr, TYPES.PowerSink):
            site.add_sink(attr)
    return site


def summarize(result: Dict[str, Dict[str, List[float]]]) -> str:
    """Return a brief human-readable summary of allocation and unmet load."""
    out: List[str] = []
    total_unmet = sum(result["unmet_load_w"]) if result.get("unmet_load_w") else 0.0
    out.append(f"Unmet load (Wh across horizon): {total_unmet:.1f}")
    for name, sched in result["source_power_w"].items():
        energy = sum(sched)
        out.append(f"- {name}: {energy:.1f} Wh used, peak {max(sched):.1f} W")
    return "\n".join(out)


if __name__ == "__main__":
    # Build from instances.py and apply per-station duty cycles and assignments
    try:
        import station_duty  # user-editable dict STATION_DUTY
        duty = getattr(station_duty, "STATION_DUTY", None)
    except Exception:
        duty = None

    try:
        import assignments  # user-editable dict ASSIGNMENTS
        mapping = getattr(assignments, "ASSIGNMENTS", None)
    except Exception:
        mapping = None

    site = build_site_from_instances()
    result = generate_schedule(
        site,
        policy="battery_last",
        station_duty=duty,
        assignments=mapping,
    )
    print(summarize(result))
