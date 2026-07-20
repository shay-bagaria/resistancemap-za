"""Tests for engine/risk.py: composite score monotonicity, bounds, band reach
(methodology section 10.2, Stage 5 recalibration)."""
from pathlib import Path

import yaml

from resistancemap.engine import risk, selection as sel

RULES = yaml.safe_load((Path(__file__).resolve().parent.parent / "data" / "rules.yaml").read_text())
COMPOSITE = RULES["composite_score"]
VL_BANDS = RULES["viral_load_bands"]
CD4_BANDS = RULES["cd4_bands"]
WEIGHTS = COMPOSITE["weights"]
BANDS = COMPOSITE["bands"]


def test_viral_load_band_monotonic():
    assert risk.viral_load_band(10, VL_BANDS) == 0
    assert risk.viral_load_band(200, VL_BANDS) == 1
    assert risk.viral_load_band(5000, VL_BANDS) == 2


def test_cd4_band_monotonic_inverse():
    # Lower CD4 is worse -> higher band.
    assert risk.cd4_band(500, CD4_BANDS) == 0
    assert risk.cd4_band(300, CD4_BANDS) == 1
    assert risk.cd4_band(100, CD4_BANDS) == 2


def test_composite_score_monotonic_in_state_severity():
    base = dict(max_mutation_index=0, vl_band=0, cd4_band_value=0, weights=WEIGHTS)
    scores = [risk.composite_score(sev, **base) for sev in range(4)]
    assert scores == sorted(scores)
    assert len(set(scores)) == 4  # strictly increasing, not just non-decreasing


def test_composite_score_monotonic_in_mutation_index():
    scores = [risk.composite_score(0, mut, 0, 0, WEIGHTS) for mut in range(5)]
    assert scores == sorted(scores)


def test_composite_score_monotonic_in_vl_band():
    scores = [risk.composite_score(0, 0, vl, 0, WEIGHTS) for vl in range(3)]
    assert scores == sorted(scores)


def test_composite_score_monotonic_in_cd4_band():
    scores = [risk.composite_score(0, 0, 0, cd4, WEIGHTS) for cd4 in range(3)]
    assert scores == sorted(scores)


def test_composite_score_bounded():
    # Worst case: max severity (3), max mutation index (4), max VL/CD4 bands (2,2).
    worst = risk.composite_score(3, 4, 2, 2, WEIGHTS)
    best = risk.composite_score(0, 0, 0, 0, WEIGHTS)
    assert best == 0
    assert worst == max(
        risk.composite_score(sev, mut, vl, cd4, WEIGHTS)
        for sev in range(4) for mut in range(5) for vl in range(3) for cd4 in range(3)
    )


def test_all_four_bands_reachable_and_ordered():
    labels_in_order = [b["label"] for b in BANDS]
    assert labels_in_order == ["Minimal", "Low", "Moderate", "High"]
    # Each band's own minimum must resolve to that band (bands cover 0..max cleanly).
    seen = set()
    for b in BANDS:
        resolved = risk.band_for_raw(b["min"], BANDS)
        assert resolved["label"] == b["label"], f"raw={b['min']} resolved to {resolved['label']!r}, expected {b['label']!r}"
        seen.add(resolved["label"])
    assert seen == {"Minimal", "Low", "Moderate", "High"}


def test_compute_composite_indeterminate_when_state_missing():
    result = risk.compute_composite(None, 0, 450, 280, COMPOSITE, VL_BANDS, CD4_BANDS)
    assert result["label"] == "Indeterminate"
    assert result["raw"] is None

    result2 = risk.compute_composite(sel.INDETERMINATE, 0, 450, 280, COMPOSITE, VL_BANDS, CD4_BANDS)
    assert result2["label"] == "Indeterminate"


def test_compute_composite_full_suppression_is_minimal_band():
    result = risk.compute_composite(sel.FULL_SUPPRESSION, 0, 0, 500, COMPOSITE, VL_BANDS, CD4_BANDS)
    assert result["label"] == "Minimal"


def test_compute_composite_monotherapy_is_high_band():
    # Highest severity + highest mutation index + worst labs -> High.
    result = risk.compute_composite(sel.FUNCTIONAL_MONOTHERAPY, 4, 5000, 100,
                                     COMPOSITE, VL_BANDS, CD4_BANDS)
    assert result["label"] == "High"
