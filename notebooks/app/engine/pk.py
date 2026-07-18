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
