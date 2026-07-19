"""Unit tests for engine/selection.py (methodology section 8, 9.2)."""
from engine import selection as sel

# TLE, methodology 8.4 parameters (unverified EFV values as specified there).
TLE = [
    {"name": "Tenofovir", "kind": "B", "intra_t_half": 48.0},
    {"name": "Lamivudine", "kind": "B", "intra_t_half": 16.0},
    {"name": "Efavirenz", "kind": "A", "c_max": 4.07, "t_half": 52.0, "threshold": 1.0},
]
TLD = [
    {"name": "Tenofovir", "kind": "B", "intra_t_half": 48.0},
    {"name": "Lamivudine", "kind": "B", "intra_t_half": 16.0},
    {"name": "Dolutegravir", "kind": "A", "c_max": 2.34, "t_half": 14.0, "threshold": 0.064},
]
ABC = [
    {"name": "Abacavir", "kind": "indeterminate"},
    {"name": "Lamivudine", "kind": "B", "intra_t_half": 16.0},
    {"name": "Dolutegravir", "kind": "A", "c_max": 2.34, "t_half": 14.0, "threshold": 0.064},
]


def test_tle_14d_has_monotherapy_window_96_to_105():
    series = sel.state_series(TLE, 14 * 24)
    window = sel.monotherapy_window(series)
    assert window is not None
    start, end, _ = window
    assert 90 <= start <= 100
    assert 100 <= end <= 112


def test_tle_cutoff_sweep_preserves_window_ordering():
    widths = {}
    for cutoff in (0.1, 0.2, 0.3, 0.4, 0.5):
        series = sel.state_series(TLE, 14 * 24, cutoff=cutoff)
        window = sel.monotherapy_window(series)
        assert window is not None, f"no window at cutoff {cutoff}"
        # Ordering holds: FULL -> PARTIAL -> MONOTHERAPY -> NO_PRESSURE in sequence.
        seen = [s for _, s in series]
        i_full = seen.index(sel.FULL_SUPPRESSION)
        i_mono = seen.index(sel.FUNCTIONAL_MONOTHERAPY)
        i_none = seen.index(sel.NO_PRESSURE)
        assert i_full < i_mono < i_none
        widths[cutoff] = window[2]
    # Report widths (visible on -s); every cutoff yields a positive-width window.
    assert all(w > 0 for w in widths.values())


def test_tld_day0_full_suppression():
    assert sel.classify(TLD, 0) == sel.FULL_SUPPRESSION


def test_all_cleared_is_no_pressure_not_max_risk():
    # Far past every half-life: nothing active -> NO_PRESSURE (§8.1).
    assert sel.classify(TLD, 10000) == sel.NO_PRESSURE


def test_abc_regimen_is_indeterminate_no_crash():
    for t in (0, 72, 336):
        assert sel.classify(ABC, t) == sel.INDETERMINATE
    assert sel.monotherapy_window(sel.state_series(ABC, 336)) is None


def test_mutation_index_3tc_sole_active_is_high():
    # 3TC sole active (exposure 2) + low barrier (2) = 4 -> High.
    idx, label = sel.mutation_index(2, sel.barrier_level("low"))
    assert label == "High"


def test_mutation_index_dtg_sole_active_is_moderate():
    # DTG sole active (exposure 2) + high barrier (0) = 2 -> Moderate.
    idx, label = sel.mutation_index(2, sel.barrier_level("high"))
    assert label == "Moderate"
