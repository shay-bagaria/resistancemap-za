"""Tests for the paediatric dolutegravir weight-band dosing lookup (methodology
section 6, and the 6-<10 kg age split from Stage 1b / IMPAACT P1093)."""
from pathlib import Path

import yaml

from resistancemap.engine import pk

CFG = yaml.safe_load(
    (Path(__file__).resolve().parent.parent / "data" / "rules.yaml").read_text()
)["paediatric_dtg_dosing"]


def dose_at(weight_kg, age_months=24):
    result = pk.paediatric_dtg_band(weight_kg, age_months, CFG)
    assert result["status"] == "ok", result["status"]
    return result["dose"]["dose"]


def test_bands_at_reference_weights():
    # 4/8/12/17/22 kg, adult-age default -> WHO bands (methodology section 6).
    assert dose_at(4) == "5 mg"
    assert dose_at(8) == "15 mg"          # >=6 months by default age=24
    assert dose_at(12) == "20 mg"
    assert dose_at(17) == "25 mg"
    assert "30 mg" in dose_at(22)


def test_8kg_age_split():
    # IMPAACT P1093: 10 mg from 4 weeks to <6 months, 15 mg from 6 months.
    assert dose_at(8, age_months=3) == "10 mg"
    assert dose_at(8, age_months=9) == "15 mg"
    # Exactly at the 6-month boundary: falls into the >=6mo band.
    assert dose_at(8, age_months=6) == "15 mg"


def test_weight_below_lowest_band():
    result = pk.paediatric_dtg_band(2, 24, CFG)
    assert result["status"] == "weight_below_bands"
    assert result["dose"] is None


def test_age_below_source_coverage():
    result = pk.paediatric_dtg_band(8, 0, CFG)
    assert result["status"] == "age_below_coverage"
    assert result["dose"] is None


def test_age_required_for_age_dependent_band():
    result = pk.paediatric_dtg_band(8, None, CFG)
    assert result["status"] == "age_required"
    assert result["dose"] is None


def test_age_independent_bands_do_not_require_age():
    # 12 kg band has a single dose regardless of age.
    result = pk.paediatric_dtg_band(12, None, CFG)
    assert result["status"] == "ok"
    assert result["dose"]["dose"] == "20 mg"


def test_top_band_has_no_upper_boundary():
    result = pk.paediatric_dtg_band(25, 24, CFG)
    assert result["status"] == "ok"
    assert result["band"]["max_kg"] is None
