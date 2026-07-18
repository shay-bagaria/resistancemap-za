import math

def concentration_at(t_h, c_max_ss, t_half_h, lloq_mg_L=None):
    """Tier A: Calculate plasma concentration at time t_h.
    
    Returns (concentration, clamp_flag).
    """
    ke = math.log(2) / t_half_h
    conc = c_max_ss * math.exp(-ke * t_h)
    
    clamp_flag = False
    if lloq_mg_L is not None and conc < lloq_mg_L:
        conc = lloq_mg_L
        clamp_flag = True
        
    return conc, clamp_flag

def inhibitory_quotient(conc, threshold):
    """Tier A: Calculate inhibitory quotient."""
    return conc / threshold

def exposure_fraction_at(t_h, t_half_h):
    """Tier B: Fraction of steady-state active-moiety exposure remaining.

    Returns a dimensionless fraction, not a concentration. Intracellular
    anabolites are measured in fmol/10^6 cells and no validated intracellular
    efficacy threshold exists in comparable units, so no inhibitory quotient
    can be computed (methodology 3.4).
    """
    ke = math.log(2) / t_half_h
    return math.exp(-ke * t_h)
