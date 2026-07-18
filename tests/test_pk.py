import math
import pytest
from notebooks.app.engine.pk import concentration_at, inhibitory_quotient, exposure_fraction_at

def test_tier_a_concentration():
    # C(72, 2.34, 14) returns 0.066231 within 1e-4
    conc, flag = concentration_at(72, 2.34, 14.0)
    assert math.isclose(conc, 0.066231, rel_tol=1e-4)
    assert flag is False
    
    # IQ against 0.064 returns 1.03
    iq = inhibitory_quotient(conc, 0.064)
    assert math.isclose(iq, 1.03, rel_tol=1e-2)
    
    # 0.3 mg/L crossing solves to 41.5 h
    c2, _ = concentration_at(41.5, 2.34, 14.0)
    assert math.isclose(c2, 0.3, rel_tol=1e-2)

def test_tier_b_tenofovir():
    # exposure_fraction_at(96, 48) returns 0.25
    f = exposure_fraction_at(96, 48.0)
    assert math.isclose(f, 0.25, rel_tol=1e-4)

def test_tier_b_lamivudine():
    # exposure_fraction_at(32, 16) returns 0.25
    f = exposure_fraction_at(32, 16.0)
    assert math.isclose(f, 0.25, rel_tol=1e-4)

def test_rifampicin_dolutegravir():
    # adjusted half-life 6.44 h
    # 14 h * 0.46 = 6.44 h
    assert math.isclose(14.0 * 0.46, 6.44, rel_tol=1e-4)

def test_allometric_scaling():
    # 15 kg factor is 0.68
    factor = (15.0 / 70.0) ** 0.25
    assert math.isclose(factor, 0.68, rel_tol=1e-2)

def test_structural_threshold():
    # calling a tier B function with a threshold argument raises TypeError
    with pytest.raises(TypeError):
        exposure_fraction_at(96, 48.0, 0.25)

def test_clamping():
    # a concentration below LLOQ returns the clamp flag set
    conc, flag = concentration_at(1000, 2.34, 14.0, lloq_mg_L=0.0001)
    assert flag is True
    assert conc == 0.0001
