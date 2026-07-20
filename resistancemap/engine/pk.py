"""Pharmacokinetic core for ResistanceMap ZA (methodology section 3).

Pure functions, no Streamlit, unit-testable. The two tiers are kept structurally
separate:

  * Tier A (plasma-acting parent compounds) work in plasma concentration and the
    inhibitory quotient.
  * Tier B (nucleos(t)ide prodrugs) return a dimensionless exposure fraction.
    ``exposure_fraction_at`` deliberately cannot take a threshold, so the
    section 3.4 separation ("no inhibitory quotient exists for the intracellular
    anabolites") cannot be violated by a caller — it is structural, not a
    convention a future edit might forget.
"""

import math

LN2 = math.log(2)


def elimination_rate(t_half_h):
    """First-order elimination rate constant k_e = ln(2) / t_half (per hour)."""
    if t_half_h <= 0:
        raise ValueError("t_half_h must be positive")
    return LN2 / t_half_h


# ── Tier A: plasma-acting ────────────────────────────────────────────────────
def concentration_at(t_h, c_max_ss, t_half_h):
    """Plasma concentration C(t) = Cmax,ss * exp(-ke * t), in mg/L (methodology 3.1)."""
    return c_max_ss * math.exp(-elimination_rate(t_half_h) * t_h)


def inhibitory_quotient(conc, threshold):
    """Inhibitory quotient IQ = C(t) / C_threshold, dimensionless (methodology 7.2)."""
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    return conc / threshold


def concentration_crossing_time(target, c_max_ss, t_half_h):
    """Hours at which C(t) falls to ``target`` (target < c_max_ss)."""
    if not 0 < target < c_max_ss:
        raise ValueError("target must be between 0 and c_max_ss")
    return math.log(c_max_ss / target) / elimination_rate(t_half_h)


# ── Tier B: nucleos(t)ide prodrugs ───────────────────────────────────────────
def exposure_fraction_at(t_h, t_half_h):
    """Relative active-moiety exposure f(t) = exp(-ke_intra * t), dimensionless (0..1).

    Takes no threshold argument by design: intracellular anabolites are measured
    in fmol per 10^6 cells and have no plasma-comparable efficacy threshold, so no
    inhibitory quotient can be formed (methodology section 3.4).
    """
    return math.exp(-elimination_rate(t_half_h) * t_h)


# ── Shared helpers ───────────────────────────────────────────────────────────
def clamp_to_lloq(conc, lloq):
    """Clamp a concentration at the lower limit of quantification (methodology 4.6).

    Returns (value, below_lloq). Below the LLOQ the value is pinned to the LLOQ
    and the flag is set so the interface can render "below limit of quantification"
    instead of a spuriously precise number that would blow out a log axis.
    """
    if lloq is not None and conc < lloq:
        return lloq, True
    return conc, False


def allometric_half_life_factor(weight_kg, reference_kg=70.0, exponent=0.25):
    """Paediatric half-life scaling factor (W / W_ref) ** exponent (methodology 5.6).

    Allometric clearance scales with W^0.75 and volume with W^1.0, so half-life
    (ln2 * V / CL) scales with W^0.25. At 15 kg this gives 0.68, against the v4.0
    linear W/35 factor of 0.43.
    """
    if weight_kg <= 0 or reference_kg <= 0:
        raise ValueError("weights must be positive")
    return (weight_kg / reference_kg) ** exponent


# ── Paediatric dolutegravir dosing lookup (methodology section 6) ───────────
def paediatric_dtg_band(weight_kg, age_months, cfg):
    """Resolve the WHO dolutegravir dose for a weight and age.

    cfg is the parsed `paediatric_dtg_dosing` section of rules.yaml (a dict with
    `minimum_age_months` and `bands`, each band carrying `min_kg`/`max_kg` and a
    `doses` list, optionally age-split via `min_age_months`/`max_age_months`).

    Returns a dict with:
      status: one of "ok", "weight_below_bands", "age_below_coverage",
              "age_required", "age_outside_coverage"
      band:   the matched weight band dict (or None), carrying true boundaries
      dose:   the matched dose dict (or None)

    The 6 to <10 kg band is age-dependent (IMPAACT P1093): 10 mg from four weeks
    to under six months, 15 mg from six months. Other bands are age-independent.
    Pure function: no Streamlit, no module-level state — cfg is passed in.
    """
    min_age = cfg.get("minimum_age_months", 1)

    band = None
    for b in cfg["bands"]:
        lo, hi = b["min_kg"], b["max_kg"]
        if weight_kg >= lo and (hi is None or weight_kg < hi):
            band = b
            break
    if band is None:
        return {"status": "weight_below_bands", "band": None, "dose": None}

    doses = band["doses"]
    age_dependent = any("min_age_months" in d or "max_age_months" in d for d in doses)

    # Below the source table's youngest age, show no dose regardless of band.
    if age_months is not None and age_months < min_age:
        return {"status": "age_below_coverage", "band": band, "dose": None}

    if not age_dependent:
        return {"status": "ok", "band": band, "dose": doses[0]}

    if age_months is None:
        return {"status": "age_required", "band": band, "dose": None}

    for d in doses:
        lo = d.get("min_age_months", 0)
        hi = d.get("max_age_months")
        if age_months >= lo and (hi is None or age_months < hi):
            return {"status": "ok", "band": band, "dose": d}
    return {"status": "age_outside_coverage", "band": band, "dose": None}
