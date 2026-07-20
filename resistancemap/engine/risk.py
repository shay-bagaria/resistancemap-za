"""Composite risk score (methodology section 10.2).

Pure functions, no Streamlit, unit-testable — separated out of the dashboard so
the ordinal-band arithmetic can be tested directly rather than only through
Streamlit's AppTest harness.

composite = w_state * state_severity + w_mut * max(mutation_index across drugs)
          + w_vl * viral_load_band + w_immune * cd4_band

state_severity uses the CURRENT classified state (see engine.selection), not the
worst state ever reached — using worst-ever saturates the score at its peak
forever once any monotherapy hour has occurred, which made every day from the
first monotherapy window onward indistinguishable (Stage 5 recalibration; see
METHODOLOGY.md section 10.2 "as built"). The cumulative "did this ever happen"
signal is preserved separately by the mutation index, whose exposure level is
explicitly defined over the whole elapsed window (section 9.2).
"""

from . import selection as sel


def viral_load_band(viral_load, bands):
    """0/1/2 from a {undetectable_below, high_above} bands dict."""
    if viral_load > bands["high_above"]:
        return 2
    if viral_load > bands["undetectable_below"]:
        return 1
    return 0


def cd4_band(cd4_count, bands):
    """0/1/2 from a {severe_below, low_below} bands dict."""
    if cd4_count < bands["severe_below"]:
        return 2
    if cd4_count < bands["low_below"]:
        return 1
    return 0


def band_for_raw(raw, bands):
    """Look up the ordinal band for a raw composite score.

    bands is a list of {min, label, colour} sorted ascending by min; the
    matching band is the highest one whose min is <= raw.
    """
    chosen = bands[0]
    for b in bands:
        if raw >= b["min"]:
            chosen = b
    return chosen


def composite_score(state_severity, max_mutation_index, vl_band, cd4_band_value, weights):
    """Raw weighted sum. weights is {state, mutation, viral_load, immune}."""
    return (weights["state"] * state_severity
            + weights["mutation"] * max_mutation_index
            + weights["viral_load"] * vl_band
            + weights["immune"] * cd4_band_value)


def compute_composite(current_state, max_mutation_index, viral_load, cd4_count,
                       composite_config, vl_bands, cd4_bands):
    """End-to-end composite computation. Returns a dict with raw/label/colour.

    Returns {"label": "Indeterminate"} without a raw score if current_state is
    INDETERMINATE or None (the regimen contains a no-curve component, or the
    decay model itself is suppressed) — the composite cannot be computed rather
    than guessed.
    """
    if current_state is None or current_state == sel.INDETERMINATE:
        return {"label": "Indeterminate", "colour": "#a855f7", "raw": None}

    state_sev = sel.STATE_SEVERITY.get(current_state, 0)
    vlb = viral_load_band(viral_load, vl_bands)
    cb = cd4_band(cd4_count, cd4_bands)
    raw = composite_score(state_sev, max_mutation_index, vlb, cb, composite_config["weights"])
    band = band_for_raw(raw, composite_config["bands"])
    return {
        "label": band["label"],
        "colour": band["colour"],
        "raw": raw,
        "state_sev": state_sev,
        "vl_band": vlb,
        "cd4_band": cb,
    }
