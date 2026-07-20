"""Versioned data-bundle loading, validation and derived lookups (methodology
section 13.2 fingerprint; section 2.6 startup validation).

Imported once at app start. Fails loudly via st.error()+st.stop() on a
malformed data bundle rather than mis-dosing or misclassifying silently.
"""

import hashlib
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
import yaml

APP_VERSION = "5.0"
PACKAGE_DIR = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_DIR / "data"
SAST = ZoneInfo("Africa/Johannesburg")

EXPECTED_SCHEMA_VERSION = "1.0"
DATA_FILES = ["drugs.yaml", "interactions.yaml", "rules.yaml"]

# Numeric mappings that, when present as a {value: ...} dict, must carry a source.
_SOURCED_FIELDS = (
    "plasma_t_half_h", "c_max_ss_mg_L", "threshold_mg_L",
    "secondary_threshold_mg_L", "intracellular_t_half_h", "activity_fraction_cutoff",
)


@st.cache_data
def load_yaml(filename):
    """Load a versioned data file from the data directory."""
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def file_sha256(filename):
    """SHA-256 of a data file, used for the ruleset fingerprint and audit rows."""
    return hashlib.sha256((DATA_DIR / filename).read_bytes()).hexdigest()


def _load_all():
    """Load and hash every data file. Returns (data, hashes, error)."""
    data, hashes = {}, {}
    for fn in DATA_FILES:
        try:
            data[fn] = load_yaml(fn)
            hashes[fn] = file_sha256(fn)
        except FileNotFoundError:
            return None, None, f"{fn}: file not found in {DATA_DIR}."
        except yaml.YAMLError as exc:
            return None, None, f"{fn}: YAML parse error: {exc}"
    return data, hashes, None


def _validate_data(data):
    """Fail loudly on a malformed data bundle rather than mis-dosing silently."""
    for fn in DATA_FILES:
        sv = data[fn].get("schema_version")
        if sv != EXPECTED_SCHEMA_VERSION:
            return f"{fn}: schema_version {sv!r} != expected {EXPECTED_SCHEMA_VERSION!r}."

    drugs = data["drugs.yaml"].get("drugs")
    if not isinstance(drugs, list) or not drugs:
        return "drugs.yaml: 'drugs' list is missing or empty."
    for d in drugs:
        nm = d.get("name", "?")
        for req in ("tier", "curve_available", "genetic_barrier", "signature_mutation"):
            if req not in d:
                return f"drugs.yaml: drug {nm} is missing '{req}'."
        tier = d["tier"]
        if tier == "A":
            if not isinstance(d.get("threshold_mg_L"), dict):
                return f"drugs.yaml: tier A drug {nm} is missing threshold_mg_L."
            if not isinstance(d.get("c_max_ss_mg_L"), dict):
                return f"drugs.yaml: tier A drug {nm} is missing c_max_ss_mg_L."
        elif tier == "B":
            if d.get("threshold_mg_L") is not None:
                return (f"drugs.yaml: tier B drug {nm} carries threshold_mg_L, "
                        "violating the section 3.4 separation.")
            if d.get("curve_available"):
                if not isinstance(d.get("intracellular_t_half_h"), dict):
                    return f"drugs.yaml: tier B drug {nm} is missing intracellular_t_half_h."
                if not isinstance(d.get("activity_fraction_cutoff"), dict):
                    return f"drugs.yaml: tier B drug {nm} is missing activity_fraction_cutoff."
        else:
            return f"drugs.yaml: drug {nm} has unknown tier {tier!r}."
        for key in _SOURCED_FIELDS:
            v = d.get(key)
            if isinstance(v, dict) and "value" in v and not v.get("source"):
                return f"drugs.yaml: {nm}.{key} is missing its 'source' key."

    ped = data["rules.yaml"].get("paediatric_dtg_dosing")
    if not isinstance(ped, dict):
        return "rules.yaml: 'paediatric_dtg_dosing' section is missing or malformed."
    bands = ped.get("bands")
    if not isinstance(bands, list) or not bands:
        return "rules.yaml: 'paediatric_dtg_dosing.bands' is missing or empty."
    for i, band in enumerate(bands):
        if "min_kg" not in band or "max_kg" not in band:
            return f"rules.yaml: band {i} is missing min_kg/max_kg."
        if not band.get("doses"):
            return f"rules.yaml: band {i} ({band.get('label', '?')}) has no doses."

    if not data["rules.yaml"].get("regimens"):
        return "rules.yaml: 'regimens' is missing or empty."
    if not isinstance(data["interactions.yaml"].get("interactions"), list) \
            or not data["interactions.yaml"]["interactions"]:
        return "interactions.yaml: 'interactions' is missing or empty."
    return None


DATA, DATA_HASHES, _load_error = _load_all()
if _load_error:
    st.error(_load_error)
    st.stop()

_data_error = _validate_data(DATA)
if _data_error:
    st.error(_data_error)
    st.stop()

DRUGS = DATA["drugs.yaml"]["drugs"]
RULES = DATA["rules.yaml"]
INTERACTIONS = {x["id"]: x for x in DATA["interactions.yaml"]["interactions"]}
REGIMENS = {r["display"]: r["components"] for r in RULES["regimens"]}
COMPOSITE = RULES["composite_score"]
VL_BANDS = RULES["viral_load_bands"]
CD4_BANDS = RULES["cd4_bands"]
PAEDIATRIC_CFG = RULES["paediatric_dtg_dosing"]

RULESET_VERSION = RULES.get("ruleset_version", "unknown")
DRUGS_HASH = DATA_HASHES["drugs.yaml"]
INTER_HASH = DATA_HASHES["interactions.yaml"]
RULES_HASH = DATA_HASHES["rules.yaml"]
RULESET_FINGERPRINT = (
    f"ruleset v{RULESET_VERSION} · drugs {DRUGS_HASH[:8]} · "
    f"interactions {INTER_HASH[:8]} · rules {RULES_HASH[:8]}"
)


def _internal_drug(d):
    """Map a drugs.yaml entry to the internal shape the engine/UI consume.

    Tier B drugs deliberately receive no threshold_mg_L (methodology section 3.4),
    so downstream code that keys on threshold presence skips them.
    """
    entry = {
        "name": d["name"],
        "abbreviation": d.get("abbreviation"),
        "tier": d["tier"],
        "curve_available": bool(d.get("curve_available")),
        "is_prodrug": bool(d.get("is_prodrug")),
        "active_moiety": d.get("active_moiety"),
        "class": d.get("drug_class"),
        "mutation": d.get("signature_mutation"),
        "cross_resistance": d.get("cross_resistance", []),
        "genetic_barrier": d.get("genetic_barrier"),
        "renal_sensitive": bool(d.get("renally_cleared")),
        "color": d.get("colour"),
        "lloq": d.get("lloq_mg_L"),
    }
    if isinstance(d.get("plasma_t_half_h"), dict):
        entry["t_half"] = d["plasma_t_half_h"]["value"]
    if isinstance(d.get("c_max_ss_mg_L"), dict):
        entry["c_max"] = d["c_max_ss_mg_L"]["value"]
    if isinstance(d.get("threshold_mg_L"), dict):
        entry["threshold_mg_L"] = d["threshold_mg_L"]["value"]
    if isinstance(d.get("secondary_threshold_mg_L"), dict):
        entry["secondary_threshold"] = d["secondary_threshold_mg_L"]["value"]
        entry["secondary_label"] = d["secondary_threshold_mg_L"].get("label", "secondary")
    if isinstance(d.get("intracellular_t_half_h"), dict):
        entry["intracellular_t_half"] = d["intracellular_t_half_h"]["value"]
        entry["intracellular_compartment"] = d["intracellular_t_half_h"].get("compartment")
    if isinstance(d.get("activity_fraction_cutoff"), dict):
        entry["activity_fraction_cutoff"] = d["activity_fraction_cutoff"]["value"]
    return entry


PK_DB = {d["name"]: _internal_drug(d) for d in DRUGS}
