"""Unit tests for engine/pk.py (methodology sections 3, 4.6, 5.1, 5.6, 7.3).

Where a value in the Stage 3 test table is a display-rounded figure (IQ 1.03,
crossing 41.5 h, allometric 0.68), the assertion targets the precise value the
formula produces and the rounded figure is noted in a comment. Relative
tolerance is 1e-4 unless stated.
"""
import math

import pytest

from resistancemap.engine import pk

REL = 1e-4


def test_concentration_at_worked_example():
    # Methodology 7.3: C(72) with Cmax 2.34, t_half 14 h.
    c = pk.concentration_at(72, 2.34, 14)
    assert math.isclose(c, 0.066231, rel_tol=REL)


def test_inhibitory_quotient_worked_example():
    c = pk.concentration_at(72, 2.34, 14)
    iq = pk.inhibitory_quotient(c, 0.064)
    assert math.isclose(iq, 1.0349, rel_tol=REL)  # displays as 1.03


def test_secondary_threshold_crossing():
    # 0.3 mg/L secondary line crossed at ~41.5 h (precise 41.489 h).
    t = pk.concentration_crossing_time(0.3, 2.34, 14)
    assert math.isclose(t, 41.489, rel_tol=1e-3)


def test_exposure_fraction_two_half_lives_tfv():
    # 96 h with a 48 h intracellular half-life is exactly two half-lives -> 0.25.
    assert math.isclose(pk.exposure_fraction_at(96, 48), 0.25, rel_tol=REL)


def test_exposure_fraction_two_half_lives_3tc():
    # 32 h with a 16 h intracellular half-life is exactly two half-lives -> 0.25.
    assert math.isclose(pk.exposure_fraction_at(32, 16), 0.25, rel_tol=REL)


def test_dtg_half_life_on_rifampicin():
    # Methodology 5.1: derived multiplier 0.46 -> 14 h * 0.46 = 6.44 h.
    assert math.isclose(14.0 * 0.46, 6.44, rel_tol=REL)


def test_allometric_factor_15kg():
    # (15/70)**0.25 = 0.6804 (displays as 0.68), vs the v4.0 linear 0.43.
    assert math.isclose(pk.allometric_half_life_factor(15), 0.6804, rel_tol=REL)


def test_exposure_fraction_rejects_threshold_argument():
    # Section 3.4: the tier B function must not accept a threshold — structural.
    with pytest.raises(TypeError):
        pk.exposure_fraction_at(96, 48, 0.25)


def test_sub_lloq_sets_clamp_flag():
    value, below = pk.clamp_to_lloq(1e-6, 1e-4)
    assert below is True
    assert value == 1e-4


def test_above_lloq_no_clamp():
    value, below = pk.clamp_to_lloq(0.5, 1e-4)
    assert below is False
    assert value == 0.5
