"""Regimen selection-pressure state classification (methodology section 8).

Pure functions, no Streamlit. The headline output of v5.0: at each hour, how many
regimen components are still active, and therefore whether the patient is passing
through a functional-monotherapy window — the state that selects resistance.

This reverses the v4.0 direction: with no drug present there is no differential
advantage for a resistant variant (wild-type, fitter without drug, rebounds), so
NO_PRESSURE is not the maximum-risk state. One drug alone is the danger (§8.1).
"""

from . import pk

FULL_SUPPRESSION = "FULL_SUPPRESSION"
PARTIAL_SUPPRESSION = "PARTIAL_SUPPRESSION"
FUNCTIONAL_MONOTHERAPY = "FUNCTIONAL_MONOTHERAPY"
NO_PRESSURE = "NO_PRESSURE"
INDETERMINATE = "INDETERMINATE"

# Severity ordering for the composite score (§10.2): monotherapy highest.
STATE_SEVERITY = {
    FULL_SUPPRESSION: 0,
    NO_PRESSURE: 1,
    PARTIAL_SUPPRESSION: 2,
    FUNCTIONAL_MONOTHERAPY: 3,
}

DEFAULT_CUTOFF = 0.25  # class C, hand-chosen (§8.2)


def active_at(component, t_h, cutoff=DEFAULT_CUTOFF):
    """Is a component active at hour t? True, False, or None (indeterminate).

    component is a dict:
      {"kind": "A", "c_max": ..., "t_half": ..., "threshold": ...}
      {"kind": "B", "intra_t_half": ..., "cutoff": ...}
      {"kind": "indeterminate"}         # e.g. abacavir, no curve
    """
    kind = component["kind"]
    if kind == "A":
        conc = pk.concentration_at(t_h, component["c_max"], component["t_half"])
        return pk.inhibitory_quotient(conc, component["threshold"]) >= 1.0
    if kind == "B":
        return pk.exposure_fraction_at(t_h, component["intra_t_half"]) >= component.get("cutoff", cutoff)
    return None


def classify(components, t_h, cutoff=DEFAULT_CUTOFF):
    """State at a single hour. INDETERMINATE if any component cannot be classified."""
    flags = [active_at(c, t_h, cutoff) for c in components]
    if any(f is None for f in flags):
        return INDETERMINATE
    n = len(flags)
    active = sum(1 for f in flags if f)
    if active == n:
        return FULL_SUPPRESSION
    if active == 0:
        return NO_PRESSURE
    if active == 1:
        return FUNCTIONAL_MONOTHERAPY
    return PARTIAL_SUPPRESSION


def state_series(components, t_max_h, cutoff=DEFAULT_CUTOFF, step_h=1):
    """Hourly [(t, state), ...] over 0..t_max_h inclusive."""
    return [(t, classify(components, t, cutoff)) for t in range(0, int(t_max_h) + 1, step_h)]


def monotherapy_window(series):
    """First contiguous FUNCTIONAL_MONOTHERAPY run as (start_h, end_h, duration_h).

    end_h is the first hour after the run (exclusive), so duration = end - start.
    Returns None if there is no monotherapy hour.
    """
    start = None
    prev_t = None
    for t, state in series:
        if state == FUNCTIONAL_MONOTHERAPY:
            if start is None:
                start = t
            prev_t = t
        elif start is not None:
            step = series[1][0] - series[0][0] if len(series) > 1 else 1
            return start, prev_t + step, (prev_t + step) - start
    if start is not None:
        step = series[1][0] - series[0][0] if len(series) > 1 else 1
        return start, prev_t + step, (prev_t + step) - start
    return None


def worst_state(series, up_to_h=None):
    """Most severe state over the series (optionally only up to up_to_h)."""
    worst = None
    worst_sev = -1
    for t, state in series:
        if up_to_h is not None and t > up_to_h:
            break
        if state == INDETERMINATE:
            return INDETERMINATE
        sev = STATE_SEVERITY.get(state, 0)
        if sev > worst_sev:
            worst_sev, worst = sev, state
    return worst


def exposure_level(components, name, t_max_h, cutoff=DEFAULT_CUTOFF, step_h=1):
    """Mutation exposure level for one component over 0..t_max_h (methodology 9.2).

    0 = active throughout; 1 = fell below threshold; 2 = sole active agent at any
    point. Returns None if the named component is itself indeterminate.
    """
    named = next((c for c in components if c.get("name") == name), None)
    if named is None or named["kind"] == "indeterminate":
        return None
    ever_inactive = False
    ever_sole = False
    for t in range(0, int(t_max_h) + 1, step_h):
        flags = {c.get("name"): active_at(c, t, cutoff) for c in components}
        this = flags.get(name)
        if this is None:
            continue
        if not this:
            ever_inactive = True
        else:
            active_names = [nm for nm, f in flags.items() if f is True]
            if active_names == [name]:
                ever_sole = True
    if ever_sole:
        return 2
    if ever_inactive:
        return 1
    return 0


_BARRIER_LEVEL = {"high": 0, "intermediate": 1, "low": 2}
_INDEX_LABEL = {0: "Minimal", 1: "Low", 2: "Moderate", 3: "High", 4: "High"}


def barrier_level(genetic_barrier):
    """0 high, 1 intermediate, 2 low (methodology 9.2)."""
    return _BARRIER_LEVEL[genetic_barrier]


def mutation_index(exposure, barrier):
    """(exposure_level, barrier_level) -> (numeric 0..4, label). None exposure -> indeterminate."""
    if exposure is None:
        return None, "Indeterminate"
    total = exposure + barrier
    return total, _INDEX_LABEL[total]
