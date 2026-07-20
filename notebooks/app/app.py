# ============================================================
# ResistanceMap ZA OS | CDSS Frontend v5.0
# Research prototype — not an approved medical device
# ============================================================

import streamlit as st
import math
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import hashlib
import html
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

# Make the app directory importable so the pure engine package resolves under
# both `streamlit run` and pytest/AppTest.
import sys
_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))
from engine import pk
from engine import selection as sel

# ============================================================
# DATA BUNDLE LOADING (versioned rules, methodology section 13.2)
# ============================================================
APP_VERSION = "5.0"
DATA_DIR = _APP_DIR / "data"
SAST = ZoneInfo("Africa/Johannesburg")


@st.cache_data
def load_yaml(filename):
    """Load a versioned data file from the data directory."""
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def file_sha256(filename):
    """SHA-256 of a data file, used for the ruleset fingerprint and audit rows."""
    return hashlib.sha256((DATA_DIR / filename).read_bytes()).hexdigest()


EXPECTED_SCHEMA_VERSION = "1.0"
DATA_FILES = ["drugs.yaml", "interactions.yaml", "rules.yaml"]

# Numeric mappings that, when present as a {value: ...} dict, must carry a source.
_SOURCED_FIELDS = (
    "plasma_t_half_h", "c_max_ss_mg_L", "threshold_mg_L",
    "secondary_threshold_mg_L", "intracellular_t_half_h", "activity_fraction_cutoff",
)


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


def chain_entry(prev_hash, entry):
    """Return the SHA-256 chain hash of an audit entry (methodology section 13.2).

    entry_hash = SHA-256(prev_hash + canonical_json(entry)). Altering any row
    invalidates every subsequent hash. This gives tamper evidence, not tamper
    proofing: an actor with write access can rebuild the whole chain.
    """
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev_hash + payload).encode("utf-8")).hexdigest()


GENESIS_HASH = "0" * 64


def paediatric_dtg_band(weight_kg, age_months=None):
    """Resolve the WHO dolutegravir dose for a weight and age (methodology section 6).

    Returns (result, config). result is a dict with:
      status: one of "ok", "weight_below_bands", "age_below_coverage",
              "age_required", "age_outside_coverage"
      band:   the matched weight band dict (or None), carrying true boundaries
      dose:   the matched dose dict (or None)

    The 6 to <10 kg band is age-dependent (IMPAACT P1093): 10 mg from four weeks
    to under six months, 15 mg from six months. Other bands are age-independent.
    """
    cfg = RULES["paediatric_dtg_dosing"]
    min_age = cfg.get("minimum_age_months", 1)

    band = None
    for b in cfg["bands"]:
        lo, hi = b["min_kg"], b["max_kg"]
        if weight_kg >= lo and (hi is None or weight_kg < hi):
            band = b
            break
    if band is None:
        return {"status": "weight_below_bands", "band": None, "dose": None}, cfg

    doses = band["doses"]
    age_dependent = any(
        "min_age_months" in d or "max_age_months" in d for d in doses
    )

    # Below the source table's youngest age, show no dose regardless of band.
    if age_months is not None and age_months < min_age:
        return {"status": "age_below_coverage", "band": band, "dose": None}, cfg

    if not age_dependent:
        return {"status": "ok", "band": band, "dose": doses[0]}, cfg

    if age_months is None:
        return {"status": "age_required", "band": band, "dose": None}, cfg

    for d in doses:
        lo = d.get("min_age_months", 0)
        hi = d.get("max_age_months")
        if age_months >= lo and (hi is None or age_months < hi):
            return {"status": "ok", "band": band, "dose": d}, cfg
    return {"status": "age_outside_coverage", "band": band, "dose": None}, cfg

# ============================================================
# 1. ENTERPRISE PAGE CONFIGURATION & GLOBAL STYLING
# ============================================================

st.set_page_config(
    page_title="ResistanceMap ZA OS | Enterprise CDSS",
    layout="wide",
    page_icon=":material/biotech:",
    initial_sidebar_state="expanded"
)

# ── Enterprise CSS Theme ─────────────────────────────────────
st.markdown("""
<style>
/* ── Global Font & Background ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0e1a;
    color: #e2e8f0;
}

/* ── Main Container ── */
.main .block-container {
    padding: 1.5rem 2rem;
    background-color: #0a0e1a;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #111827 100%);
    border-right: 1px solid #1e3a5f;
}

section[data-testid="stSidebar"] .block-container {
    padding: 1rem;
}

/* ── Metric Cards ── */
.metric-card {
    background: linear-gradient(135deg, #0d1b2e 0%, #112240 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

.metric-card:hover {
    border-color: #2563eb;
    box-shadow: 0 4px 25px rgba(37,99,235,0.2);
    transform: translateY(-2px);
}

.metric-card h3 {
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}

.metric-card .metric-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
}

.metric-card .metric-delta {
    font-size: 0.75rem;
    margin-top: 0.3rem;
}

/* ── Alert Banners ── */
.alert-critical {
    background: linear-gradient(135deg, #1a0000, #2d0000);
    border-left: 4px solid #ef4444;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    color: #fca5a5;
}

.alert-warning {
    background: linear-gradient(135deg, #1a1200, #2d2000);
    border-left: 4px solid #f59e0b;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    color: #fde68a;
}

.alert-info {
    background: linear-gradient(135deg, #001a2d, #002040);
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    color: #93c5fd;
}

.alert-success {
    background: linear-gradient(135deg, #001a0d, #002d1a);
    border-left: 4px solid #10b981;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    color: #6ee7b7;
}

/* ── Section Headers ── */
.section-header {
    font-size: 0.7rem;
    font-weight: 600;
    color: #3b82f6;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin: 1.5rem 0 0.8rem 0;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1e3a5f;
}

/* ── Drug Badges ── */
.drug-badge {
    display: inline-block;
    background: #1e3a5f;
    color: #93c5fd;
    border: 1px solid #2563eb;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0.15rem;
    letter-spacing: 0.05em;
}

/* ── Risk Gauge Container ── */
.risk-gauge-container {
    background: linear-gradient(135deg, #0d1b2e, #112240);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}

/* ── Status Pills ── */
.status-stable {
    background: #064e3b;
    color: #6ee7b7;
    border: 1px solid #10b981;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.status-warning {
    background: #451a03;
    color: #fde68a;
    border: 1px solid #f59e0b;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

.status-critical {
    background: #450a0a;
    color: #fca5a5;
    border: 1px solid #ef4444;
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ── Tab Styling ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1117;
    border-bottom: 1px solid #1e3a5f;
    gap: 0;
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #64748b;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 0.6rem 1.2rem;
    font-size: 0.8rem;
    font-weight: 500;
}

.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #3b82f6 !important;
    border-bottom: 2px solid #3b82f6 !important;
}

/* ── Sidebar Text ── */
.sidebar-label {
    font-size: 0.7rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    margin-bottom: 0.2rem;
}

/* ── Streamlit Overrides ── */
.stSelectbox > div > div {
    background: #0d1b2e !important;
    border: 1px solid #1e3a5f !important;
    color: #e2e8f0 !important;
}

.stSlider > div > div > div {
    background: #1e3a5f !important;
}

div[data-testid="stMetricValue"] {
    color: #e2e8f0;
}

h1, h2, h3, h4 {
    color: #e2e8f0 !important;
}

/* ── Data Table ── */
.styled-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    background: #0d1b2e;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #1e3a5f;
}

.styled-table th {
    background: #112240;
    color: #93c5fd;
    padding: 0.7rem 1rem;
    text-align: left;
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-bottom: 1px solid #1e3a5f;
}

.styled-table td {
    padding: 0.65rem 1rem;
    color: #cbd5e1;
    border-bottom: 1px solid #0f2237;
}

.styled-table tr:hover td {
    background: #112240;
}

/* ── Blink Animation for Critical ── */
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.blink-red {
    animation: blink 1.5s infinite;
    color: #ef4444;
}

/* ── Logo / Header Bar ── */
.top-header {
    background: linear-gradient(90deg, #0d1117 0%, #0a1628 50%, #0d1117 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
}

/* ── Progress Bar Override ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #1d4ed8, #2563eb) !important;
}

/* ── Checkbox & Radio ── */
.stCheckbox > label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
}

.stRadio > label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
}

/* ── Divider ── */
hr {
    border-color: #1e3a5f !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2563eb; }

/* Input text */
.stTextInput > div > div > input {
    background: #0d1b2e !important;
    border: 1px solid #1e3a5f !important;
    color: #e2e8f0 !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. MASTER MENU NAVIGATION CONTROL
# ============================================================

st.sidebar.markdown("<p class='sidebar-label'>System View Mode</p>", unsafe_allow_html=True)
app_view = st.sidebar.radio(
    "Select Interface Page:",
    ["About ResistanceMap ZA", "Understanding Your Results", "Patient Assessment Dashboard"]
)
st.sidebar.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)

# ------------------------------------------------------------
# VIEW MODE A: ABOUT / MAIN FRONT PAGE
# ------------------------------------------------------------
if app_view == "About ResistanceMap ZA":
    st.markdown("""
    <div style='background: linear-gradient(135deg, #0d1b2e 0%, #0d2542 100%); 
                border: 1px solid #1e3a5f; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4); text-align: center;'>
        <h1 style='font-size: 2.5rem; font-weight: 700; color: #e2e8f0; margin: 0;'>ResistanceMap ZA</h1>
        <p style='font-size: 1.1rem; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.5rem;'>
            Molecular Epidemiology & Pharmacokinetic Surveillance Engine
        </p>
        <p style='font-size: 0.95rem; color: #94a3b8; max-width: 800px; margin: 1rem auto 0 auto; line-height: 1.6;'>
            An open-source, zero-cost computational framework mapping HIV-1 drug-resistance mutation clusters across KwaZulu-Natal to safeguard public treatment programmes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='metric-card' style='height: 100%;'>
            <h3 style='color: #3b82f6; font-size: 0.9rem;'>What is ResistanceMap ZA?</h3>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-top: 0.5rem;'>
                It is an advanced Clinical Decision Support System (CDSS) that tracks how HIV mutations cluster in different communities. When patients miss treatment erratically, sub-inhibitory windows select for drug-resistant variants. This platform models those drops to flag resistance patterns before they spread.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card' style='height: 100%;'>
            <h3 style='color: #3b82f6; font-size: 0.9rem;'>Why is it useful?</h3>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-top: 0.5rem;'>
                With South Africa deploying the National Health Insurance (NHI) framework, therapeutic failure creates major fiscal challenges. Moving patients onto specialized third-line therapies escalates costs drastically. By predicting resistance hotspots, resource distribution can be optimized accurately.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card' style='height: 100%;'>
            <h3 style='color: #3b82f6; font-size: 0.9rem;'>Who is it for?</h3>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-top: 0.5rem;'>
                Built for frontline clinical professionals, health system programme planners, and medical researchers. It bridges the gap between raw genomic sequence data (NCBI GenBank / Stanford HIVdb) and concrete local diagnostic support protocols.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><p class='section-header'>System Instruction Manual</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: #0d1b2e; border: 1px solid #1e3a5f; border-radius: 8px; padding: 1.2rem 1.5rem; font-size: 0.88rem; line-height: 1.7; color: #cbd5e1;'>
        <strong>How to Navigate the Application Engine:</strong><br>
        1. Locate the <strong>System View Mode</strong> radio filter in the left sidebar menu.<br>
        2. Toggle the option to <strong>Patient Assessment Dashboard</strong> to initialise the live assessment engine.<br>
        3. Alter regional comorbidity profiles, adherence windows, and pediatric weight arrays to see real-time updates.<br>
        4. Review the cross-resistance cascade models and compliance metrics natively generated within individual tabs.
    </div>
    """, unsafe_allow_html=True)

    # ── Plain English Footer ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='border-top:1px solid #1e3a5f; padding-top:1rem; text-align:center;
                font-size:0.65rem; color: #475569; line-height:2;'>
        ResistanceMap ZA OS v{APP_VERSION} &nbsp;·&nbsp; Open Source Public Health System Framework<br>
        Contact: sbagaria2009@gmail.com<br>
        Prototype for educational and research use only. Not an approved medical device.
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# VIEW MODE B: UNDERSTANDING YOUR RESULTS (PATIENT GUIDE)
# ------------------------------------------------------------
elif app_view == "Understanding Your Results":

    st.markdown("""
    <div style='background: linear-gradient(135deg, #0d1b2e 0%, #0d2542 100%);
                border: 1px solid #1e3a5f; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4); text-align: center;'>
        <h1 style='font-size: 2.2rem; font-weight: 700; color: #e2e8f0; margin: 0;'>
           Understanding Your Results
        </h1>
        <p style='font-size: 1rem; color: #10b981; margin-top: 0.5rem; font-weight: 500;'>
            A plain-language guide written for patients living with HIV
        </p>
        <p style='font-size: 0.88rem; color: #94a3b8; max-width: 700px; margin: 0.8rem auto 0 auto; line-height: 1.7;'>
            This page explains every part of ResistanceMap ZA in simple, everyday language.
            No medical degree needed — just honest information to help you understand your treatment better.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Section 1: What is this tool? ──
    st.markdown("<p class='section-header'>What is ResistanceMap ZA?</p>", unsafe_allow_html=True)
    st.markdown("""
    <div class='metric-card'>
        <p style='font-size: 0.92rem; color: #cbd5e1; line-height: 1.85;'>
            <strong style='color:#3b82f6;'>In simple terms:</strong> ResistanceMap ZA is a free computer tool that helps
            doctors check whether your HIV medication is still working properly.<br><br>
            When you take your ARV pills every day, they keep the virus under control. But if doses are missed,
            the virus can start changing (we call these changes <strong>"mutations"</strong>). Once the virus changes,
            your current pills might stop working as well.<br><br>
            This tool helps your doctor spot those problems <strong>before</strong> they become serious — so they
            can adjust your treatment early and keep you healthy.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Section 2: The Dashboard Numbers ──
    st.markdown("<p class='section-header'>What Do the Numbers on the Dashboard Mean?</p>", unsafe_allow_html=True)

    guide_items = [
        ("Resistance Risk Score (0–100)",
         "This is like a warning light for your treatment.",
         "It combines how long since your last dose, how much medicine is left in your blood, and other health factors. "
         "<strong>Lower is better.</strong> A score under 40 means things look stable. Above 70 means your doctor needs to act quickly.",
         "The system adds points for each risk factor — missed days, low drug levels, TB treatment, kidney problems, etc. "
         "The more risk factors, the higher the score."),

        ("Drugs Below MIC",
         "MIC stands for 'Minimum Inhibitory Concentration' — the lowest amount of medicine needed to stop the virus.",
         "If a drug drops <strong>below MIC</strong>, there is not enough medicine in your blood to fight HIV properly. "
         "This is when the virus can start changing and becoming resistant. "
         "<strong>0 drugs below MIC = good. Any number above 0 = your doctor should look at this.</strong>",
         "Your blood drug level is compared to the known minimum needed. If you've missed doses, drugs with short half-lives (like Lamivudine) drop below MIC first."),

        ("Days Defaulted",
         "This is simply how many days since you last took your medication.",
         "<strong>0 days = you took your pills today.</strong> Every extra day without pills means the medicine in your blood is dropping. "
         "After a few days, some drugs will have completely left your system.",
         "Your doctor or pharmacy records show when you last collected your pills. The system uses this to calculate how much drug is left in your body."),

        ("Viral Load",
         "This blood test counts how much HIV is in your blood.",
         "<strong>Undetectable (below 50 copies/mL) = excellent.</strong> It means your treatment is working well. "
         "Above 1,000 copies/mL means the virus may be growing because the treatment is struggling. "
         "Your doctor may need to check for resistance.",
         "Viral load is measured from a blood sample sent to the NHLS laboratory. Results are reported in copies per millilitre of blood."),

        ("CD4 Count",
         "CD4 cells are the soldiers of your immune system that fight infections.",
         "<strong>Above 500 = healthy immune system.</strong> Between 200–350 = your immune system needs support. "
         "<strong>Below 200 = your immune system is very weak</strong> and you're at risk for serious infections like TB or pneumonia.",
         "CD4 is measured from a blood sample. A rising CD4 count over time means your ARVs are working and your body is recovering."),
    ]

    for title, subtitle, explanation, calculation in guide_items:
        st.markdown(f"""
        <div class='metric-card' style='margin-bottom: 1rem;'>
            <h3 style='color: #3b82f6; font-size: 1rem; margin-bottom: 0.3rem;'>{title}</h3>
            <p style='font-size: 0.82rem; color: #f59e0b; font-weight: 500; margin-bottom: 0.6rem;'>{subtitle}</p>
            <p style='font-size: 0.88rem; color: #cbd5e1; line-height: 1.8; margin-bottom: 0.8rem;'>{explanation}</p>
            <div style='background: #0a1628; border-radius: 8px; padding: 0.7rem 1rem; border-left: 3px solid #3b82f6;'>
                <div style='font-size: 0.65rem; color: #3b82f6; font-weight: 700; text-transform: uppercase;
                            letter-spacing: 0.1em; margin-bottom: 0.3rem;'>How it's calculated</div>
                <p style='font-size: 0.78rem; color: #94a3b8; line-height: 1.6; margin: 0;'>{calculation}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Section 3: The Tabs ──
    st.markdown("<p class='section-header'>What Are the Different Tabs?</p>", unsafe_allow_html=True)

    tabs_guide = [
        ("PK Decay Curves",
         "Shows how fast each medicine leaves your body after a missed dose",
         "Think of it like a fuel gauge for each of your ARV drugs. The coloured lines show each drug's level dropping over time. "
         "When a line crosses below the dotted line (MIC), that drug is no longer protecting you. "
         "Drugs with a long 'half-life' (like Efavirenz) stay in your body longer, but this can actually be dangerous — "
         "the virus can start to 'learn' to fight a low dose of the drug."),

        ("Mutation & Resistance",
         "Shows which genetic changes might happen if drug levels drop too low",
         "HIV makes copies of itself very quickly, and sometimes those copies have small mistakes called mutations. "
         "Some mutations make the virus resistant to your medicine. For example, <strong>M184V</strong> makes Lamivudine less effective, "
         "and <strong>K65R</strong> does the same to Tenofovir. This tab shows how likely these mutations are based on your current drug levels."),

        ("Clinical Directives",
         "Alerts and instructions for your healthcare team",
         "If you're also being treated for <strong>TB</strong>, the system warns your doctor to double the Dolutegravir dose. "
         "If you use <strong>traditional medicines</strong> like African Potato or St. John's Wort, it warns that these can speed up "
         "how fast your ARVs leave your body. These alerts help your clinic team make the right adjustments."),

        ("Adherence Risk",
         "Predicts how likely a patient is to miss future doses",
         "This looks at real-life challenges: <strong>How far do you live from the clinic? Do you have transport? "
         "Is there a taxi strike?</strong> It combines these into a risk score. If your risk is high, the system suggests "
         "a community health worker visit or an extra phone reminder to help you stay on track."),

        ("Audit & Compliance",
         "A complete record of every check the system performs",
         "Every time a doctor uses ResistanceMap ZA, the system creates a <strong>tamper-evident</strong> record — "
         "if any earlier entry is changed, the records that follow it no longer match, so tampering shows up. "
         "This is not the same as tamper-proof: someone with permission to write to the records could rebuild them, "
         "so the record makes changes <em>detectable</em> rather than impossible. It helps make sure every alert was seen "
         "and every guideline was followed."),
    ]

    for tab_name, tab_summary, tab_detail in tabs_guide:
        st.markdown(f"""
        <div class='metric-card' style='margin-bottom: 0.8rem;'>
            <div style='display: flex; align-items: flex-start; gap: 1rem;'>
                <div style='flex: 1;'>
                    <h3 style='color: #e2e8f0; font-size: 0.95rem; margin-bottom: 0.2rem;'>{tab_name}</h3>
                    <p style='font-size: 0.8rem; color: #10b981; font-weight: 500; margin-bottom: 0.5rem;'>{tab_summary}</p>
                    <p style='font-size: 0.85rem; color: #94a3b8; line-height: 1.75;'>{tab_detail}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Section 4: Key Medical Terms ──
    st.markdown("<p class='section-header'>Key Words Explained</p>", unsafe_allow_html=True)

    glossary = [
        ("ARV / ART", "Antiretroviral drugs — the daily pills that keep HIV under control."),
        ("Mutation", "A change in the virus's genetic code. Some mutations make the virus resistant to certain drugs."),
        ("MIC", "Minimum Inhibitory Concentration — the smallest amount of drug needed in your blood to stop the virus from growing."),
        ("Half-life", "How long it takes for half of a drug to leave your body. A long half-life means the drug stays longer."),
        ("Viral Load", "A blood test that measures how much HIV is in your body. Lower is better. 'Undetectable' is the goal."),
        ("CD4 Count", "A count of the immune cells that HIV attacks. Higher numbers mean a stronger immune system."),
        ("Resistance", "When the virus changes so that a drug can no longer stop it from growing."),
        ("Sub-inhibitory", "When drug levels are too low to stop the virus but still high enough to push it to mutate. This is the most dangerous zone."),
        ("First-line / Second-line / Third-line", "Treatment levels. First-line is the starting treatment. If it fails, you move to second-line (more expensive), then third-line (very expensive and limited options)."),
        ("TLD", "Tenofovir + Lamivudine + Dolutegravir — the most common first-line ARV combination in South Africa."),
        ("NDoH", "National Department of Health — the government body that sets treatment guidelines in South Africa."),
        ("POPIA", "Protection of Personal Information Act — a South African law that protects your private medical data."),
    ]

    glossary_rows = ""
    for term, definition in glossary:
        glossary_rows += f"""
        <tr>
            <td style='color: #3b82f6; font-weight: 600; white-space: nowrap; vertical-align: top;'>{term}</td>
            <td style='color: #cbd5e1; line-height: 1.7;'>{definition}</td>
        </tr>"""

    st.markdown(f"""
    <table class='styled-table'>
        <thead><tr><th>Term</th><th>What It Means</th></tr></thead>
        <tbody>{glossary_rows}</tbody>
    </table>
    """, unsafe_allow_html=True)

    # ── Section 5: Important Reminders ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class='alert-success'>
        <div style='font-weight: 700; font-size: 0.95rem; margin-bottom: 0.5rem;'>
           Important Reminders for Patients
        </div>
        <div style='font-size: 0.88rem; line-height: 1.9;'>
           <strong>Take your ARVs every day at the same time.</strong> This is the single most important thing you can do.<br>
           <strong>Don't stop your medication</strong> even if you feel healthy — the virus is still there.<br>
           <strong>Tell your doctor</strong> about any traditional medicines, supplements, or herbal remedies you use.<br>
           <strong>Go to every clinic appointment</strong> and collect your pills on time.<br>
           <strong>If you missed doses</strong>, don't panic — restart your full regimen and tell your healthcare worker.<br>
           <strong>Ask questions.</strong> You have the right to understand your treatment. This tool is here to help.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer ──
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='border-top:1px solid #1e3a5f; padding-top:1rem; text-align:center;
                font-size:0.65rem; color: #475569; line-height:2;'>
        ResistanceMap ZA OS v{APP_VERSION} &nbsp;·&nbsp; Patient Education Module<br>
        Written in plain language for patients living with HIV in KwaZulu-Natal<br>
        This tool does not replace your doctor. Always follow your healthcare team's advice.
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# VIEW MODE C: PATIENT ASSESSMENT DASHBOARD
# ------------------------------------------------------------
elif app_view == "Patient Assessment Dashboard":

    # ============================================================
    # SIDEBAR — ENTERPRISE PATIENT PROFILE
    # ============================================================

    with st.sidebar:
        # ── Logo Block ──
        st.markdown(f"""
        <div style='text-align:center; padding: 0.5rem 0 1rem 0;'>
            <div style='font-size:1.1rem; font-weight:700; color:#e2e8f0; letter-spacing:0.05em;'>
                ResistanceMap ZA
            </div>
            <div style='font-size:0.65rem; color:#3b82f6; text-transform:uppercase;
                        letter-spacing:0.15em; margin-top:0.2rem;'>
                CDSS v{APP_VERSION}
            </div>
            <div style='font-size:0.6rem; color:#475569; margin-top:0.3rem;'>
                Educational Prototype
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)

        # ── System Status ──
        now = datetime.datetime.now(SAST)
        st.markdown(f"""
        <div style='background:#0a1628; border:1px solid #1e3a5f; border-radius:8px;
                    padding:0.6rem 0.8rem; margin-bottom:0.8rem; font-size:0.72rem;'>
            <div style='color:#f59e0b; font-weight:600;'>DEMO MODE — SIMULATED DATA</div>
            <div style='color:#475569; margin-top:0.2rem;'>
                {now.strftime("%d %b %Y  %H:%M:%S")} SAST
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Patient Identity ──
        st.markdown("<p class='section-header'>Patient Identity</p>", unsafe_allow_html=True)

        patient_id = st.text_input("Pseudonymised Patient ID", "KZN-8842-A",
                                    help="Pseudonymous reference only. Pseudonymised health data "
                                         "remains personal information under POPIA (methodology 15). "
                                         "Demo data only — no real patient information.")

        facility = st.selectbox("Treating Facility",
            ["King Edward VIII Hospital – Durban",
             "Inkosi Albert Luthuli Central Hospital",
             "Grey's Hospital – Pietermaritzburg",
             "Edendale Hospital",
             "Mahatma Gandhi Memorial Hospital",
             "Prince Mshiyeni Memorial Hospital",
             "RK Khan Hospital"])

        clinician = st.text_input("Clinician (Pseudonymised Code)", "DR-KZN-0044")

        # Escape free-text before it is interpolated into any unsafe_allow_html markup.
        patient_id_safe = html.escape(patient_id)
        clinician_safe = html.escape(clinician)

        st.markdown("<p class='section-header'>ART Regimen</p>", unsafe_allow_html=True)

        regimen = st.selectbox("Current Regimen", list(REGIMENS.keys()))

        st.markdown("<p class='section-header'>Clinical Modifiers</p>", unsafe_allow_html=True)

        tb_coinfection = st.checkbox("Active TB (On Rifampicin)",
                                      help="Rifampicin induces UGT1A1 (principal) and CYP3A4 (<10%); "
                                           "DTG t½ ×0.46, manage with 50 mg twice daily (methodology §5.1).")

        st_johns_wort = st.checkbox("St John's Wort",
                                    help="Enzyme inducer (hyperforin). Direction of effect only — "
                                         "no modelled magnitude (methodology §5.3).")

        african_potato = st.checkbox("African Potato (Hypoxis hemerocallidea)",
                                     help="No modelled effect; record and counsel (methodology §5.4).")

        # Derived flag preserved for the (class C, pending_restructure) composite score.
        traditional_meds = st_johns_wort or african_potato

        egfr = st.number_input("Kidney Function — eGFR (mL/min/1.73m²)", 5, 150, 95,
                               help="Numeric eGFR. Renal status is an accumulation-nephrotoxicity "
                                    "safety alert, separate from the resistance model (methodology §5.5).")

        paediatric = st.checkbox("Paediatric Patient (Weight-Band Dosing)",
                                  help="Activates paediatric PK adjustment (allometric, methodology §5.6)")

        if paediatric:
            weight_kg = st.slider("Patient Weight (kg)", 3, 40, 15)
            age_months = st.number_input(
                "Patient Age (months)", 0, 216, 24,
                help="Used for the 6 to <10 kg dolutegravir dose split "
                     "(10 mg from 4 weeks to <6 months, 15 mg from 6 months; IMPAACT P1093).")
        else:
            weight_kg = 70
            age_months = None

        st.markdown("<p class='section-header'>Adherence Data</p>", unsafe_allow_html=True)

        days_missed = st.slider("Days Since Last Dose", 0, 14, 3,
                                 help="Demo input — days since the last ingested dose.")
        hours_missed = days_missed * 24

        viral_load = st.number_input("Last Viral Load (copies/mL)", 0, 1000000, 450,
                                      help="Demo input — most recent laboratory viral load.")

        cd4_count = st.number_input("CD4 Count (cells/μL)", 0, 2000, 280)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-size:0.62rem; color:#334155; text-align:center; line-height:1.6;'>
            ResistanceMap ZA OS © 2025<br>
            <span style='color:#1e3a5f;'>Educational prototype — not for clinical use</span>
        </div>
        """, unsafe_allow_html=True)

    # ============================================================
    # 3. PHARMACOKINETIC ENGINE — CORE LOGIC
    # ============================================================

    # ── PK database and regimen mapping (loaded from YAML at startup) ──
    pk_db = PK_DB
    regimen_drugs = REGIMENS

    active_drugs = regimen_drugs.get(regimen, ["Tenofovir", "Lamivudine", "Dolutegravir"])

    # ── Adjusted Half-Life Calculation ──
    # Multipliers relocated to interactions.yaml (methodology section 5). The
    # arithmetic is unchanged from v4.0; pending_removal entries are actioned in
    # Stage 3, not here.
    def calculate_adjusted_half_life(drug, stats):
        t_half = stats["t_half"]
        applied = []

        # Rifampicin + DTG only: derived 0.46 multiplier, UGT1A1 principal (§5.1).
        # The EFV interaction was removed in Stage 3 (§5.2), so no EFV branch.
        if tb_coinfection and drug == "Dolutegravir":
            ix = INTERACTIONS["rifampicin_dtg"]
            t_half *= ix["multiplier"]
            applied.append((ix["display_name"], ix["display_desc"]))

        # Herbals carry no modelled magnitude (§5.3 direction only, §5.4 no effect):
        # multiplier 1.0, nothing applied to the half-life. They surface as alerts.

        # Renal: eGFR scaling is disabled pending an unsourced renally-cleared
        # fraction (§5.5). Renal is a standalone safety alert; it does not modify
        # the half-life or the resistance model.

        # Paediatric allometric scaling t½_child = t½_adult × (W/70)^0.25 (§5.6).
        # Below curve_min_age_months the curve is suppressed upstream, so this
        # branch only runs for ages the allometric model covers.
        if paediatric:
            pw = INTERACTIONS["paediatric_weight"]
            weight_factor = pk.allometric_half_life_factor(
                weight_kg, pw["reference_weight_kg"], pw["exponent"])
            t_half *= weight_factor
            applied.append((pw["display_name"], f"Weight factor {weight_factor:.2f}"))

        return t_half, applied


    # ── Run PK for all active drugs ──
    current_levels   = {}
    adjusted_halves  = {}
    all_modifiers    = {}

    # Below curve_min_age_months the allometric model is not applicable (UGT1A1
    # maturation, §5.6): suppress the whole decay model, not just the dose.
    curve_min_age = INTERACTIONS["paediatric_weight"].get("curve_min_age_months", 6)
    curve_suppressed = bool(paediatric and age_months is not None and age_months < curve_min_age)

    if not curve_suppressed:
        for drug in active_drugs:
            stats = pk_db.get(drug)
            if not stats:
                continue
            # Drugs without an available curve (e.g. abacavir, methodology section 4.5)
            # are not modelled: no concentration, no curve, no threshold-breach alert.
            if not stats.get("curve_available"):
                continue
            adj_t_half, mods = calculate_adjusted_half_life(drug, stats)
            adjusted_halves[drug] = adj_t_half
            current_levels[drug] = pk.concentration_at(hours_missed, stats["c_max"], adj_t_half)
            all_modifiers[drug] = mods


    # ── Regimen state, mutation index, composite (methodology sections 8–10) ──
    t_max_hours = max(days_missed * 24 + 72, 168)
    ACTIVITY_CUTOFF = sel.DEFAULT_CUTOFF   # 0.25, class C (§8.2)

    components = []
    for drug in active_drugs:
        stats = pk_db.get(drug)
        if not stats:
            continue
        if not stats.get("curve_available"):
            components.append({"name": drug, "kind": "indeterminate"})
        elif "threshold_mg_L" in stats:
            components.append({"name": drug, "kind": "A",
                               "c_max": stats["c_max"],
                               "t_half": adjusted_halves.get(drug, stats["t_half"]),
                               "threshold": stats["threshold_mg_L"]})
        else:
            components.append({"name": drug, "kind": "B",
                               "intra_t_half": stats["intracellular_t_half"],
                               "cutoff": stats.get("activity_fraction_cutoff", ACTIVITY_CUTOFF)})

    has_indeterminate = any(c["kind"] == "indeterminate" for c in components)

    state_series = []
    current_state = None
    mono_window = None
    worst_state = None
    mutation_rows = []
    composite_label = None
    composite_colour = "#64748b"
    composite_contribs = {}
    state_available = bool(components) and not curve_suppressed

    if state_available:
        state_series = sel.state_series(components, t_max_hours, cutoff=ACTIVITY_CUTOFF)
        current_state = sel.classify(components, hours_missed, cutoff=ACTIVITY_CUTOFF)
        mono_window = sel.monotherapy_window(state_series)
        worst_state = sel.worst_state(state_series, up_to_h=hours_missed)

        for drug in active_drugs:
            stats = pk_db.get(drug)
            if not stats:
                continue
            if has_indeterminate:
                mutation_rows.append({"name": drug, "label": "Indeterminate",
                                      "exposure": None, "barrier": None, "numeric": None})
                continue
            exp = sel.exposure_level(components, drug, hours_missed, cutoff=ACTIVITY_CUTOFF)
            barrier = sel.barrier_level(stats["genetic_barrier"])
            numeric, label = sel.mutation_index(exp, barrier)
            mutation_rows.append({"name": drug, "label": label, "exposure": exp,
                                  "barrier": barrier, "numeric": numeric})

        if has_indeterminate or current_state == sel.INDETERMINATE:
            composite_label = "Indeterminate"
        else:
            vl_band = (2 if viral_load > VL_BANDS["high_above"]
                       else 1 if viral_load > VL_BANDS["undetectable_below"] else 0)
            cd4_band = (2 if cd4_count < CD4_BANDS["severe_below"]
                        else 1 if cd4_count < CD4_BANDS["low_below"] else 0)
            # state_sev uses the CURRENT state, not the worst state ever reached.
            # The mutation index already carries the cumulative "did this ever
            # happen" signal (§9.2: exposure level 2 = sole active agent at any
            # point), so state here can reflect live risk. Using worst-ever state
            # for severity pins the score at its peak forever once any monotherapy
            # hour has occurred, which is what made Stage 4's composite saturate
            # by day 3-5 and made every later day indistinguishable (methodology
            # §10.2, Stage 5 recalibration).
            state_sev = sel.STATE_SEVERITY.get(current_state, 0)
            max_mut = max((r["numeric"] for r in mutation_rows if r["numeric"] is not None),
                          default=0)
            w = COMPOSITE["weights"]
            composite_raw = (w["state"] * state_sev + w["mutation"] * max_mut
                             + w["viral_load"] * vl_band + w["immune"] * cd4_band)
            band = COMPOSITE["bands"][0]
            for b in COMPOSITE["bands"]:
                if composite_raw >= b["min"]:
                    band = b
            composite_label = band["label"]
            composite_colour = band["colour"]
            composite_contribs = {"state": current_state, "peak_state": worst_state,
                                  "state_sev": state_sev, "mutation": max_mut,
                                  "viral_load": vl_band, "cd4": cd4_band, "raw": composite_raw}

    # Human-readable state labels / colours for display.
    STATE_META = {
        sel.FULL_SUPPRESSION:       ("Full suppression", "#10b981"),
        sel.PARTIAL_SUPPRESSION:    ("Partial suppression", "#f59e0b"),
        sel.FUNCTIONAL_MONOTHERAPY: ("Functional monotherapy", "#ef4444"),
        sel.NO_PRESSURE:            ("No pressure (rebound risk)", "#64748b"),
        sel.INDETERMINATE:          ("Indeterminate", "#a855f7"),
    }

    # ============================================================
    # 4. MAIN DASHBOARD — HEADER
    # ============================================================

    st.markdown(f"""
    <div class='top-header'>
        <div style='display:flex; align-items:center; gap:1rem;'>
            <div>
                <div style='font-size:1.25rem; font-weight:700; color:#e2e8f0;
                            letter-spacing:0.02em;'>
                    ResistanceMap ZA OS
                </div>
                <div style='font-size:0.72rem; color:#3b82f6; letter-spacing:0.12em;
                            text-transform:uppercase;'>
                    Clinical Decision Support System &nbsp;·&nbsp; v{APP_VERSION}
                </div>
            </div>
        </div>
        <div style='text-align:right;'>
            <div style='font-size:0.7rem; color:#475569;'>Patient</div>
            <div style='font-size:1rem; font-weight:700; color:#93c5fd;'>{patient_id_safe}</div>
            <div style='font-size:0.7rem; color:#475569; margin-top:0.2rem;'>
                {facility.split("–")[0].strip()}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Coverage disclosure ──
    # Tier B now contributes to the state classification (§8). Only components with
    # NO curve at all (abacavir) remain outside the model, making the whole regimen
    # state indeterminate — that is the only case that is now "partial".
    unscored_components = [d for d in active_drugs if not pk_db.get(d, {}).get("curve_available")]
    partial_note = "Partial assessment" if unscored_components else ""

    if unscored_components:
        st.markdown(f"""
        <div class='alert-warning' style='margin-bottom:0.9rem;'>
            <div style='font-weight:700; font-size:0.82rem;'>
               PARTIAL ASSESSMENT — regimen state is indeterminate
            </div>
            <div style='font-size:0.78rem; margin-top:0.3rem; line-height:1.6;'>
                <strong>{', '.join(unscored_components)}</strong>
                {'has' if len(unscored_components) == 1 else 'have'} no decay curve (active-moiety
                half-life unsourced; methodology &sect;4.5), so {'it counts' if len(unscored_components) == 1 else 'they count'}
                as neither active nor inactive. The regimen state and composite band are reported
                as <strong>indeterminate</strong> rather than guessed (methodology &sect;8.2).
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Top KPI Strip ──
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    with kpi1:
        comp_display = composite_label if composite_label else "—"
        st.markdown(f"""
        <div class='metric-card'>
            <h3>Composite Risk Band</h3>
            <div class='metric-value' style='color:{composite_colour}; font-size:1.5rem;'>{comp_display}</div>
            <div class='metric-delta' style='color:#64748b; font-size:0.66rem;'>Ordinal band · Class C</div>
            <div class='metric-delta' style='color:#f59e0b; font-size:0.66rem;'>{partial_note}</div>
        </div>""", unsafe_allow_html=True)

    with kpi2:
        if current_state:
            state_txt, state_col = STATE_META.get(current_state, ("—", "#64748b"))
        else:
            state_txt, state_col = ("Not modelled", "#64748b")
        st.markdown(f"""
        <div class='metric-card'>
            <h3>Regimen State (now)</h3>
            <div class='metric-value' style='color:{state_col}; font-size:1.15rem;'>{state_txt}</div>
            <div class='metric-delta' style='color:#64748b;'>at {hours_missed}h · Class B</div>
        </div>""", unsafe_allow_html=True)

    with kpi3:
        d_color = "#ef4444" if days_missed >= 5 else "#f59e0b" if days_missed >= 2 else "#10b981"
        st.markdown(f"""
        <div class='metric-card'>
            <h3>Days Defaulted</h3>
            <div class='metric-value' style='color:{d_color};'>{days_missed}d</div>
            <div class='metric-delta' style='color:#64748b;'>{hours_missed}h since last dose</div>
        </div>""", unsafe_allow_html=True)

    with kpi4:
        vl_color = ("#ef4444" if viral_load > VL_BANDS["high_above"]
                    else "#f59e0b" if viral_load > VL_BANDS["undetectable_below"] else "#10b981")
        vl_display = f"{viral_load:,}" if viral_load > 0 else "Undetectable"
        st.markdown(f"""
        <div class='metric-card'>
            <h3>Viral Load (cp/mL)</h3>
            <div class='metric-value' style='color:{vl_color}; font-size:1.4rem;'>{vl_display}</div>
            <div class='metric-delta' style='color:#64748b;'>NHLS Last Result</div>
        </div>""", unsafe_allow_html=True)

    with kpi5:
        cd4_color = ("#ef4444" if cd4_count < CD4_BANDS["severe_below"]
                     else "#f59e0b" if cd4_count < CD4_BANDS["low_below"] else "#10b981")
        cd4_note = ('Severe Immunocompromise' if cd4_count < CD4_BANDS["severe_below"]
                    else 'Immunocompromised' if cd4_count < CD4_BANDS["low_below"] else 'Adequate')
        st.markdown(f"""
        <div class='metric-card'>
            <h3>CD4 Count (cells/μL)</h3>
            <div class='metric-value' style='color:{cd4_color}; font-size:1.4rem;'>{cd4_count:,}</div>
            <div class='metric-delta' style='color:#64748b;'>
                {cd4_note}
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Active Modifiers Banner ──
    flat_mods = []
    for drug, mods in all_modifiers.items():
        for mod_name, mod_desc in mods:
            if mod_name not in [m[0] for m in flat_mods]:
                flat_mods.append((mod_name, mod_desc))

    if flat_mods:
        mod_html = " &nbsp;|&nbsp; ".join([
            f"<span style='color:#fde68a; font-weight:600;'>{m}</span> "
            f"<span style='color:#94a3b8;'>({d})</span>"
            for m, d in flat_mods
        ])
        st.markdown(f"""
        <div style='background:#1a1200; border:1px solid #f59e0b33; border-left:4px solid #f59e0b;
                    border-radius:8px; padding:0.7rem 1rem; margin:0.5rem 0; font-size:0.78rem;'>
           <span style='color:#f59e0b; font-weight:700;'>ACTIVE METABOLIC MODIFIERS:</span>
            &nbsp; {mod_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # 5. TABBED INTERFACE — ENTERPRISE MODULES
    # ============================================================

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "PK Decay Curves",
        "Mutation & Resistance",
        "Clinical Directives",
        "Adherence Risk",
        "Audit & Compliance"
    ])

    # ────────────────────────────────────────────────────────────
    # TAB 1: PHARMACOKINETIC DECAY VISUALISATION
    # ────────────────────────────────────────────────────────────
    with tab1:
        col_chart, col_status = st.columns([3, 1])

        with col_chart:
            st.markdown("<p class='section-header'>Plasma Concentration Decay — Comorbidity Adjusted</p>",
                        unsafe_allow_html=True)

            # ── Build Decay Curves ──
            t_max_hours = max(days_missed * 24 + 72, 168)
            time_array = np.arange(0, t_max_hours, 1)

            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Tier A plasma concentration vs time (log scale)",
                                "Tier A % threshold coverage · Tier B % steady-state exposure"),
                vertical_spacing=0.12,
                row_heights=[0.6, 0.4]
            )

            lloq_flags = {}
            for drug in (active_drugs if not curve_suppressed else []):
                stats = pk_db.get(drug)
                if not stats or not stats.get("curve_available"):
                    continue
                color = stats["color"]

                if "threshold_mg_L" in stats:
                    # Tier A: plasma concentration on top, clamped at the LLOQ (§4.6)
                    # so the log axis cannot span dozens of empty decades.
                    adj_t = adjusted_halves[drug]
                    k_e = math.log(2) / adj_t
                    raw = stats["c_max"] * np.exp(-k_e * time_array)
                    lloq = stats.get("lloq") or 1e-4
                    decay = np.clip(raw, lloq, None)
                    lloq_flags[drug] = bool(current_levels[drug] <= lloq)

                    fig.add_trace(go.Scatter(
                        x=time_array, y=decay, mode='lines', name=drug,
                        line=dict(width=2.5, color=color),
                        hovertemplate=(f"<b>{drug}</b><br>Time: %{{x:.0f}}h<br>"
                                       "Conc: %{y:.4f} mg/L<extra></extra>")
                    ), row=1, col=1)

                    fig.add_trace(go.Scatter(
                        x=[0, t_max_hours], y=[stats["threshold_mg_L"]] * 2,
                        mode='lines', name=f"{drug} threshold",
                        line=dict(width=1.2, dash='dot', color=color),
                        opacity=0.5, showlegend=False, hoverinfo='skip'
                    ), row=1, col=1)

                    if stats.get("secondary_threshold"):
                        fig.add_trace(go.Scatter(
                            x=[0, t_max_hours], y=[stats["secondary_threshold"]] * 2,
                            mode='lines', name=f"{drug} {stats.get('secondary_label', 'secondary')}",
                            line=dict(width=1.0, dash='dash', color=color),
                            opacity=0.3, showlegend=False, hoverinfo='skip'
                        ), row=1, col=1)

                    cov = (decay / stats["threshold_mg_L"]) * 100
                    fig.add_trace(go.Scatter(
                        x=time_array, y=cov, mode='lines', name=f"{drug} coverage",
                        line=dict(width=2, color=color),
                        fill='tozeroy',
                        fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.08,)}",
                        showlegend=False,
                        hovertemplate=(f"<b>{drug}</b> (tier A)<br>Time: %{{x:.0f}}h<br>"
                                       "Coverage: %{y:.1f}%<extra></extra>")
                    ), row=2, col=1)
                else:
                    # Tier B: relative exposure f(t)*100 on the bottom subplot only.
                    # Never plotted as an absolute concentration on top (§3.4).
                    intra = stats["intracellular_t_half"]
                    frac = np.exp(-(math.log(2) / intra) * time_array) * 100
                    fig.add_trace(go.Scatter(
                        x=time_array, y=frac, mode='lines', name=f"{drug} exposure",
                        line=dict(width=2, dash='dash', color=color),
                        hovertemplate=(f"<b>{drug}</b> (tier B, {stats.get('active_moiety', '')})<br>"
                                       "Time: %{x:.0f}h<br>"
                                       "Exposure: %{y:.1f}% of steady state<extra></extra>")
                    ), row=2, col=1)

            # 100% reference on subplot 2
            fig.add_trace(go.Scatter(
                x=[0, t_max_hours], y=[100, 100],
                mode='lines', name="100%",
                line=dict(width=1, dash='dot', color='#475569'),
                showlegend=False, hoverinfo='skip'
            ), row=2, col=1)

            # Current time marker
            if hours_missed > 0:
                fig.add_vline(
                    x=hours_missed, row="all",
                    line_width=2, line_dash="solid", line_color="#ef4444",
                    annotation_text=f"NOW ({days_missed}d defaulted)",
                    annotation_position="top left",
                    annotation_font_color="#ef4444",
                    annotation_font_size=11,
                    annotation_yshift=10
                )

            # The v4.0 "resistance window" shading (hours_missed × 0.85 to × 1.3) had no
            # pharmacological basis and is removed (§4.4). The functional-monotherapy
            # window, when one exists, is shaded from the state classification instead.
            if mono_window:
                fig.add_vrect(
                    x0=mono_window[0], x1=min(mono_window[1], t_max_hours),
                    fillcolor="rgba(239,68,68,0.10)", line_width=0,
                    annotation_text="Monotherapy window",
                    annotation_position="top right",
                    annotation_font_color="#ef4444",
                    annotation_font_size=10,
                    annotation_yshift=-12,
                    row=1, col=1
                )

            fig.update_layout(
                plot_bgcolor="#0a0e1a",
                paper_bgcolor="#0d1b2e",
                font=dict(family="Inter", color="#94a3b8", size=11),
                legend=dict(
                    bgcolor="#0a0e1a",
                    bordercolor="#1e3a5f",
                    borderwidth=1,
                    font=dict(size=10),
                    x=0.01, y=0.99
                ),
                hovermode="x unified",
                margin=dict(l=0, r=0, t=48, b=0),
                height=520
            )
            fig.update_xaxes(
                gridcolor="#0f2237", zerolinecolor="#1e3a5f",
                title_text="Hours Since Last Dose", row=2, col=1
            )
            fig.update_yaxes(
                gridcolor="#0f2237", zerolinecolor="#1e3a5f",
                type="log", title_text="Concentration (mg/L)", row=1, col=1
            )
            fig.update_yaxes(
                gridcolor="#0f2237", zerolinecolor="#1e3a5f",
                title_text="% exposure / coverage", row=2, col=1
            )

            if curve_suppressed:
                st.markdown(f"""
                <div class='alert-warning'>
                    <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                       DECAY CURVE SUPPRESSED — AGE BELOW {curve_min_age} MONTHS
                    </div>
                    <div style='font-size:0.82rem; line-height:1.7;'>
                        The allometric half-life model is not applicable below {curve_min_age} months
                        of age (UGT1A1 maturation, methodology &sect;5.6), so no decay curve is shown.
                        Dolutegravir dosing still follows the WHO weight-band lookup in the Clinical
                        Directives tab. Refer to specialist paediatric guidance.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.plotly_chart(fig, width="stretch")

                # ── Regimen-state band along the time axis (methodology §8.3) ──
                st.markdown("<p class='section-header'>Regimen State — Selection Pressure</p>",
                            unsafe_allow_html=True)
                # Contiguous runs of state across the modelled window.
                runs = []
                for t, state in state_series:
                    if runs and runs[-1][2] == state:
                        runs[-1][1] = t
                    else:
                        runs.append([t, t, state])
                total = max((r[1] for r in runs), default=1) or 1
                segs = ""
                for t0, t1, state in runs:
                    span = (t1 - t0) + 1
                    txt, col = STATE_META.get(state, ("—", "#64748b"))
                    segs += (
                        f"<div title='{txt}: {t0}–{t1}h' style='flex:{span}; background:{col};"
                        f" height:26px; border-right:1px solid #0a0e1a;'></div>"
                    )
                st.markdown(f"""
                <div style='display:flex; width:100%; border-radius:6px; overflow:hidden;
                            border:1px solid #1e3a5f;'>{segs}</div>
                <div style='display:flex; justify-content:space-between; font-size:0.62rem;
                            color:#64748b; margin-top:0.2rem;'>
                    <span>0 h</span><span>{int(total)} h</span>
                </div>
                <div style='font-size:0.66rem; color:#f59e0b; margin-top:0.4rem;'>
                    Tier B active cut-off f(t) ≥ {ACTIVITY_CUTOFF:.2f} is <strong>Class C</strong>,
                    hand-chosen and the weakest element of this output (methodology §8.2).
                </div>
                """, unsafe_allow_html=True)

                # Legend + monotherapy window summary.
                legend = " &nbsp; ".join(
                    f"<span style='color:{col};'>■</span> {txt}"
                    for txt, col in [STATE_META[s] for s in
                                     (sel.FULL_SUPPRESSION, sel.PARTIAL_SUPPRESSION,
                                      sel.FUNCTIONAL_MONOTHERAPY, sel.NO_PRESSURE)]
                )
                st.markdown(f"<div style='font-size:0.66rem; color:#94a3b8; margin-top:0.3rem;'>{legend}</div>",
                            unsafe_allow_html=True)
                if mono_window:
                    ms, me, md = mono_window
                    st.markdown(f"""
                    <div class='alert-critical' style='margin-top:0.5rem;'>
                        <strong>Functional monotherapy window:</strong> {ms}–{me} h
                        (duration {md} h). One component active while the others have cleared —
                        the highest resistance-selection risk (methodology §8.1).
                    </div>
                    """, unsafe_allow_html=True)

        with col_status:
            st.markdown("<p class='section-header'>Drug Status Panel</p>", unsafe_allow_html=True)

            for drug in (active_drugs if not curve_suppressed else []):
                stats = pk_db.get(drug)
                if not stats:
                    continue

                # Drug with no available curve (abacavir, methodology section 4.5).
                if not stats.get("curve_available"):
                    st.markdown(f"""
                    <div class='metric-card' style='margin-bottom:0.6rem;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;
                                    margin-bottom:0.5rem;'>
                            <span class='drug-badge'>{drug}</span>
                            <span class='status-warning'>PARAMETER UNAVAILABLE</span>
                        </div>
                        <div style='font-size:0.78rem; color:#94a3b8; line-height:1.5;'>
                            No decay curve. The active-moiety (carbovir triphosphate) half-life is
                            unsourced, and the plasma value would misrepresent the drug
                            (methodology &sect;4.5).
                        </div>
                        <div style='font-size:0.72rem; color:#64748b; margin-top:0.3rem;'>
                            Signature mutation: {stats["mutation"]} &nbsp;·&nbsp; {stats["class"]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    continue

                adj_t = adjusted_halves[drug]

                # Tier B prodrug: report relative active-moiety exposure f(t), never an
                # absolute concentration or inhibitory quotient (methodology section 3.4).
                if "threshold_mg_L" not in stats:
                    intra_t = stats.get("intracellular_t_half")
                    f_t = math.exp(-math.log(2) / intra_t * hours_missed)
                    moiety = stats.get("active_moiety", "active moiety")
                    compartment = stats.get("intracellular_compartment", "")
                    st.markdown(f"""
                    <div class='metric-card' style='margin-bottom:0.6rem;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;
                                    margin-bottom:0.5rem;'>
                            <span class='drug-badge'>{drug}</span>
                            <span class='status-warning'>PRODRUG — EXPOSURE ONLY</span>
                        </div>
                        <div style='font-size:0.72rem; color:#64748b;'>Active-moiety exposure remaining</div>
                        <div style='font-size:1.3rem; font-weight:700; color:{stats["color"]};'>
                            {f_t * 100:.1f}% of steady state
                        </div>
                        <div style='font-size:0.72rem; color:#64748b; margin-top:0.3rem;'>
                            {moiety} &nbsp;·&nbsp; intracellular t½ {intra_t:.0f} h ({compartment})
                        </div>
                        <div style='font-size:0.7rem; color:#f59e0b; margin-top:0.3rem; line-height:1.4;'>
                            No inhibitory quotient computed: the active moiety is intracellular
                            with no plasma-comparable efficacy threshold (methodology &sect;3.4).
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    continue

                # Tier A drug: plasma concentration and above/below classification.
                lvl = current_levels[drug]
                mic = stats["threshold_mg_L"]
                pct = (lvl / mic) * 100
                if lvl >= mic:
                    status_html = "<span class='status-stable'>ABOVE MIC</span>"
                elif lvl >= mic * 0.05:
                    status_html = "<span class='status-warning'>SUB-INHIBITORY</span>"
                else:
                    status_html = "<span class='status-critical'>CLEARED</span>"

                # Below the LLOQ, show the honest label rather than a spurious number (§4.6).
                if lloq_flags.get(drug):
                    level_html = "below limit of quantification"
                else:
                    level_html = f"{lvl:.4f} mg/L"

                st.markdown(f"""
                <div class='metric-card' style='margin-bottom:0.6rem;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;
                                margin-bottom:0.5rem;'>
                        <span class='drug-badge'>{drug}</span>
                        {status_html}
                    </div>
                    <div style='font-size:0.72rem; color:#64748b;'>Plasma Level</div>
                    <div style='font-size:1.3rem; font-weight:700; color:{stats["color"]};'>
                        {level_html}
                    </div>
                    <div style='font-size:0.72rem; color:#64748b; margin-top:0.3rem;'>
                        MIC: {mic} mg/L &nbsp;·&nbsp; {pct:.1f}% coverage
                    </div>
                    <div style='font-size:0.72rem; color:#64748b;'>
                        Adj. t½: {adj_t:.1f}h &nbsp;·&nbsp; {stats["class"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ── Composite band (ordinal, no gauge — §10.2) ──
            if composite_contribs:
                c = composite_contribs
                state_txt = STATE_META.get(c["state"], ("—", "#64748b"))[0]
                peak_txt = STATE_META.get(c["peak_state"], ("—", "#64748b"))[0]
                peak_note = (f" (peak so far: {peak_txt})" if c["peak_state"] != c["state"] else "")
                contrib_html = (
                    f"current state {state_txt} (severity {c['state_sev']}){peak_note} · "
                    f"max mutation index {c['mutation']} · VL band {c['viral_load']} · "
                    f"CD4 band {c['cd4']}"
                )
            else:
                contrib_html = "Not computable (regimen contains an indeterminate component or the curve is suppressed)."
            st.markdown(f"""
            <div class='metric-card' style='text-align:center;'>
                <div style='font-size:0.7rem; color:#64748b; text-transform:uppercase;
                            letter-spacing:0.1em;'>Composite Risk Band</div>
                <div style='font-size:1.6rem; font-weight:700; color:{composite_colour}; margin:0.3rem 0;'>
                    {composite_label if composite_label else '—'}
                </div>
                <div style='font-size:0.66rem; color:#f59e0b;'>Class C — hand-chosen weights, not a calibrated 0–100 score</div>
                <div style='font-size:0.66rem; color:#94a3b8; margin-top:0.4rem; line-height:1.5;'>
                    {contrib_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # TAB 2: MUTATION & CROSS-RESISTANCE PREDICTOR
    # ────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<p class='section-header'>Genomic Resistance Prediction Engine</p>",
                    unsafe_allow_html=True)

        # ── Mutation Risk Matrix ──
        col_mut1, col_mut2 = st.columns([1.5, 1])

        with col_mut1:
            st.markdown("<p class='section-header'>Mutation Risk Index — Ordinal (§9.2)</p>",
                        unsafe_allow_html=True)

            _INDEX_COLOR = {"Minimal": "#10b981", "Low": "#3b82f6", "Moderate": "#f59e0b",
                            "High": "#ef4444", "Indeterminate": "#a855f7"}
            _EXP_TXT = {0: "0 — active throughout", 1: "1 — fell below threshold",
                        2: "2 — sole active agent at some point"}
            _BAR_TXT = {0: "0 — high", 1: "1 — intermediate", 2: "2 — low"}
            index_by_drug = {r["name"]: r for r in mutation_rows}

            if not mutation_rows:
                st.markdown("""
                <div class='alert-info'>
                    <div style='font-size:0.8rem;'>No mutation index: the decay model is
                    suppressed for this patient (see the PK Decay tab).</div>
                </div>
                """, unsafe_allow_html=True)

            for drug in active_drugs:
                stats = pk_db.get(drug)
                row = index_by_drug.get(drug)
                if not stats or row is None:
                    continue
                cross_res = ", ".join(stats.get("cross_resistance", ["None"]))
                col = _INDEX_COLOR.get(row["label"], "#64748b")
                if row["numeric"] is None:
                    items = ("Indeterminate — this regimen contains a component with no decay "
                             "curve (methodology §4.5), so exposure level cannot be determined.")
                else:
                    items = (f"Exposure level {_EXP_TXT.get(row['exposure'], '—')} "
                             f"&nbsp;+&nbsp; barrier level {_BAR_TXT.get(row['barrier'], '—')} "
                             f"&nbsp;=&nbsp; <strong>{row['numeric']}</strong>")
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                        <div>
                            <span class='drug-badge'>{drug}</span>
                            <span style='background:#1a0a2e; color:#c084fc; border:1px solid #7c3aed;
                                         border-radius:20px; padding:0.2rem 0.7rem; font-size:0.72rem;
                                         font-weight:600; margin-left:0.4rem;'>{stats["class"]}</span>
                            <div style='margin-top:0.5rem; font-size:0.88rem;'>
                                <span style='color:#64748b;'>Signature mutation: </span>
                                <span style='color:#fbbf24; font-weight:700;'>{stats["mutation"]}</span>
                            </div>
                            <div style='font-size:0.75rem; color:#64748b; margin-top:0.2rem;'>
                                Cross-resistance → <span style='color:#94a3b8;'>{cross_res}</span>
                            </div>
                            <div style='font-size:0.72rem; color:#94a3b8; margin-top:0.4rem;'>{items}</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='font-size:0.65rem; color:#64748b;'>Mutation index</div>
                            <div style='color:{col}; font-weight:700; font-size:1.15rem;'>{row["label"]}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div style='font-size:0.68rem; color:#f59e0b; margin-top:0.5rem;'>
                Ordinal heuristic. Not a probability. Not validated against outcome data.
                Genetic barrier is included deliberately: M184V under lamivudine and R263K under
                dolutegravir cannot share a risk curve (methodology §9.3).
            </div>
            """, unsafe_allow_html=True)

        with col_mut2:
            st.markdown("<p class='section-header'>Mutation Intelligence Cards</p>",
                        unsafe_allow_html=True)

            mutation_intel = {
                "K65R": {
                    "name": "K65R (Tenofovir Resistance)",
                    "description": "Lysine→Arginine substitution at codon 65 of reverse transcriptase. Reduces Tenofovir affinity by >10-fold. Associated with multi-NRTI cross-resistance.",
                    "second_line": "Switch to Zidovudine (AZT) backbone. K65R hypersensitises HIV to AZT.",
                    "severity": "HIGH"
                },
                "M184V": {
                    "name": "M184V (Lamivudine Resistance)",
                    "description": "Methionine→Valine at codon 184. Confers high-level 3TC/FTC resistance. Paradoxically reduces viral fitness and INCREASES susceptibility to Tenofovir.",
                    "second_line": "Maintain 3TC in regimen — residual M184V preserves fitness cost benefit. Prioritise Tenofovir intensification.",
                    "severity": "MODERATE"
                },
                "R263K": {
                    "name": "R263K (Dolutegravir Resistance)",
                    "description": "Rare integrase mutation. DTG has extremely high genetic barrier — R263K requires pre-existing INSTI resistance background (G118R, E138K) to achieve clinical resistance.",
                    "second_line": "Consider Bictegravir or Cabotegravir. Genotypic resistance testing mandatory before switch.",
                    "severity": "SEVERE"
                },
                "K103N": {
                    "name": "K103N (Efavirenz Resistance)",
                    "description": "Lysine→Asparagine substitution at codon 103 of reverse transcriptase. Confers high-level resistance to all first-generation NNRTIs (Efavirenz, Nevirapine). Most common NNRTI resistance mutation globally.",
                    "second_line": "Switch to INSTI-based regimen (DTG). K103N does not affect second-generation NNRTIs like Etravirine but INSTI switch preferred per NDoH guidelines.",
                    "severity": "HIGH"
                },
                "L74V": {
                    "name": "L74V (Abacavir Resistance)",
                    "description": "Leucine→Valine substitution at codon 74. Reduces Abacavir susceptibility by 3–5 fold. Often emerges with Didanosine use. Does not significantly affect Tenofovir.",
                    "second_line": "Switch to Tenofovir-based backbone. L74V increases susceptibility to Zidovudine. Genotypic testing recommended.",
                    "severity": "MODERATE"
                }
            }

            for drug in active_drugs:
                mut_key = pk_db[drug]["mutation"]
                if mut_key in mutation_intel:
                    intel = mutation_intel[mut_key]
                    sev_color = {
                        "HIGH": "#f59e0b",
                        "MODERATE": "#3b82f6",
                        "SEVERE": "#ef4444"
                    }.get(intel["severity"], "#94a3b8")

                    st.markdown(f"""
                    <div class='metric-card'>
                        <div style='display:flex; justify-content:space-between;'>
                            <div style='font-size:0.8rem; font-weight:700; color:#e2e8f0;'>
                               {intel["name"]}
                            </div>
                            <span style='background:#0a0e1a; color:{sev_color};
                                         border:1px solid {sev_color}; border-radius:12px;
                                         padding:0.1rem 0.5rem; font-size:0.65rem; font-weight:700;'>
                                {intel["severity"]}
                            </span>
                        </div>
                        <div style='font-size:0.75rem; color:#94a3b8; margin-top:0.6rem;
                                    line-height:1.6;'>
                            {intel["description"]}
                        </div>
                        <div style='margin-top:0.7rem; background:#0a1628; border-radius:6px;
                                    padding:0.5rem 0.7rem; border-left:3px solid #10b981;'>
                            <div style='font-size:0.65rem; color:#10b981; font-weight:700;
                                        text-transform:uppercase; letter-spacing:0.1em;'>
                                Second-Line Directive
                            </div>
                            <div style='font-size:0.73rem; color:#6ee7b7; margin-top:0.3rem;
                                        line-height:1.5;'>
                                {intel["second_line"]}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # TAB 3: CLINICAL DIRECTIVES
    # ────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("<p class='section-header'>NDoH Guideline Adherence & Clinical Alerts</p>",
                    unsafe_allow_html=True)

        directives_fired = 0

        # ── TB / Rifampicin Alert ──
        if tb_coinfection:
            directives_fired += 1
            rif = INTERACTIONS["rifampicin_dtg"]
            st.markdown(f"""
            <div class='alert-critical'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   PROTOCOL ALERT — RIFAMPICIN–DTG INTERACTION
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Patient is confirmed on <strong>Rifampicin</strong> for active TB co-infection.
                    Rifampicin induces <strong>UGT1A1, UGT1A9 and CYP3A4</strong>. Dolutegravir is
                    metabolised principally by <strong>UGT1A1 glucuronidation</strong>, with CYP3A4
                    contributing <strong>less than 10%</strong> — so this is chiefly a UGT1A1 effect,
                    not CYP3A4 alone. Rifampicin reduces DTG plasma AUC by approximately
                    <strong>54%</strong> (t½ ×{rif['multiplier']} → 6.4 h).<br><br>
                   <strong>Mandatory Action:</strong> Increase Dolutegravir to
                    <span style='color:#fca5a5;'>50 mg TWICE DAILY (BD)</span>. Twice-daily dosing with
                    rifampicin achieves AUC/trough approximately 18–33% above once-daily without
                    rifampicin. The decay curve is modelled on the BD schedule when this flag is set.<br>
                   <strong>Monitoring:</strong> Repeat viral load at 4 weeks post-adjustment.<br>
                   <span style='color:#94a3b8;'>Class A (Derived) &middot; {RULESET_FINGERPRINT}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Rifampicin + EFV informational note (interaction removed, §5.2) ──
        if tb_coinfection and "Efavirenz" in active_drugs:
            st.markdown(f"""
            <div class='alert-info'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   RIFAMPICIN–EFAVIRENZ — NO DOSE ADJUSTMENT
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    South African data support using efavirenz with rifampicin-based TB treatment
                    <strong>without dose adjustment</strong>. The <strong>CYP2B6 516G&gt;T</strong>
                    polymorphism, common locally and associated with higher efavirenz concentrations,
                    is a larger determinant of exposure than the rifampicin interaction. The v4.0
                    0.74 half-life multiplier has been removed (methodology &sect;5.2).<br>
                    <span style='color:#94a3b8;'>Informational (Class B) &middot; {RULESET_FINGERPRINT}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── St John's Wort Alert (direction only, §5.3) ──
        if st_johns_wort:
            directives_fired += 1
            st.markdown(f"""
            <div class='alert-warning'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   HERBAL INTERACTION — ST JOHN'S WORT
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    <strong>Hyperforin</strong> induces CYP3A4 and P-glycoprotein, which would tend to
                    <strong>lower</strong> antiretroviral concentrations. The <strong>direction</strong>
                    of effect is established; the <strong>magnitude for dolutegravir is not sourced</strong>,
                    so no percentage is applied to the model (methodology &sect;5.3).<br>
                   <strong>Action:</strong> Counsel on cessation; record use.<br>
                    <span style='color:#94a3b8;'>Class B (direction only) &middot; {RULESET_FINGERPRINT}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── African Potato Alert (no modelled effect, §5.4) ──
        if african_potato:
            directives_fired += 1
            st.markdown(f"""
            <div class='alert-info'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   HERBAL USE — AFRICAN POTATO (HYPOXIS HEMEROCALLIDEA)
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    The evidence base for <em>Hypoxis</em> is <strong>thinner than for St John's Wort</strong>,
                    is largely <strong>in vitro</strong>, and is <strong>inconsistent on direction</strong>
                    (some findings point towards inhibition, which would move concentrations the other way).
                    <strong>No effect is modelled</strong> (methodology &sect;5.4).<br>
                   <strong>Action:</strong> Record and discuss traditional medicine use as good practice.<br>
                    <span style='color:#94a3b8;'>Class C (no modelled effect) &middot; {RULESET_FINGERPRINT}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Renal Safety Alert (eGFR; separate from the resistance model, §5.5) ──
        if egfr < 60:
            directives_fired += 1
            severe = egfr < 30
            sev = "SEVERE (eGFR <30)" if severe else "MODERATE (eGFR 30–59)"
            action = ("Consider switching TDF → TAF (tenofovir alafenamide), which achieves "
                      "equivalent efficacy at roughly 10% of the plasma concentration."
                      if severe else
                      "Monitor eGFR monthly; consider a TAF switch if the trajectory worsens; avoid NSAIDs.")
            st.markdown(f"""
            <div class='alert-warning'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   RENAL SAFETY ALERT — {sev}
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    eGFR <strong>{egfr} mL/min/1.73m²</strong>. This is a
                    <strong>safety alert, separate from the resistance model</strong>: the concern with
                    tenofovir in renal impairment is <strong>accumulation nephrotoxicity, not loss of
                    efficacy</strong> (methodology &sect;5.5). Half-life is not scaled here, because the
                    per-drug renally-cleared fraction is unsourced.<br>
                   <strong>Action:</strong> {action}<br>
                   <strong>Monitor:</strong> Monthly urinary phosphate/creatinine ratio; watch for Fanconi syndrome.<br>
                    <span style='color:#94a3b8;'>Class C (safety) &middot; {RULESET_FINGERPRINT}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Paediatric Alert ──
        if paediatric:
            directives_fired += 1
            result, ped_cfg = paediatric_dtg_band(weight_kg, age_months)
            status = result["status"]
            band = result["band"]
            min_age = ped_cfg.get("minimum_age_months", 1)
            class_line = (
                f"<span style='color:#94a3b8;'>Class A (Derived) &middot; "
                f"ruleset v{RULESET_VERSION}</span>"
            )
            age_display = f"{age_months} months" if age_months is not None else "not entered"

            if status == "ok":
                dose = result["dose"]
                band_dose = html.escape(dose["dose"])
                band_label = html.escape(band.get("label", ""))
                dose_source = html.escape(dose.get("source", band.get("label", "")))
                hi = band["max_kg"]
                if hi is None:
                    boundary_text = (
                        f"Current band: <strong>{band_label}</strong>. This is the highest band. "
                        f"From 20 kg, adult 50 mg film-coated tablets once daily are appropriate."
                    )
                else:
                    boundary_text = (
                        f"Current band: <strong>{band_label}</strong>. "
                        f"The next weight-based dose change is due at <strong>{hi} kg</strong>."
                    )
                st.markdown(f"""
                <div class='alert-info'>
                    <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                       PAEDIATRIC WEIGHT-BAND DOSING PROTOCOL ACTIVE
                    </div>
                    <div style='font-size:0.82rem; line-height:1.7;'>
                        Patient weight: <strong>{weight_kg} kg</strong> &middot; age: <strong>{age_display}</strong>.
                        WHO weight-band dosing for dolutegravir dispersible tablets:<br><br>
                       <strong>Recommended DTG Dose:</strong>
                        <span style='color:#93c5fd; font-weight:700;'>{band_dose} once daily</span>
                        <span style='color:#64748b;'>({dose_source})</span><br>
                       {boundary_text}<br>
                       <strong>Volume check:</strong> Confirm dispersible tablet formulation.
                        Do not substitute adult film-coated tablet below 20 kg.<br>
                        {class_line}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                if status == "weight_below_bands":
                    headline = "PAEDIATRIC DOSING — WEIGHT BELOW LOWEST BAND"
                    body = (
                        f"Patient weight <strong>{weight_kg} kg</strong> is below the lowest "
                        f"WHO weight band (3 kg)."
                    )
                elif status == "age_below_coverage":
                    headline = "PAEDIATRIC DOSING — AGE BELOW SOURCE COVERAGE"
                    body = (
                        f"Patient age <strong>{age_display}</strong> is below four weeks. "
                        f"The dosing table used here does not cover neonates."
                    )
                elif status == "age_required":
                    headline = "PAEDIATRIC DOSING — AGE REQUIRED"
                    body = (
                        f"Weight <strong>{weight_kg} kg</strong> falls in an age-dependent band "
                        f"(6 to &lt;10 kg). Enter the patient's age in months to resolve the dose "
                        f"(10 mg below six months, 15 mg from six months)."
                    )
                else:  # age_outside_coverage
                    headline = "PAEDIATRIC DOSING — AGE OUTSIDE SOURCE COVERAGE"
                    body = (
                        f"No modelled dose is available for weight <strong>{weight_kg} kg</strong> "
                        f"at age <strong>{age_display}</strong>."
                    )
                st.markdown(f"""
                <div class='alert-warning'>
                    <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                       {headline}
                    </div>
                    <div style='font-size:0.82rem; line-height:1.7;'>
                        {body} No modelled dose is shown. Refer to current paediatric guidelines
                        and specialist advice.<br>
                        {class_line}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── State-driven directives (replaces the sub-MIC / cleared alerts, §8) ──
        if state_available and current_state == sel.FUNCTIONAL_MONOTHERAPY and mono_window:
            directives_fired += 1
            ms, me, md = mono_window
            sole = [c["name"] for c in components if sel.active_at(c, hours_missed, ACTIVITY_CUTOFF) is True]
            sole_name = sole[0] if len(sole) == 1 else ", ".join(sole)
            st.markdown(f"""
            <div class='alert-critical'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   FUNCTIONAL MONOTHERAPY — HIGHEST RESISTANCE-SELECTION RISK
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Only <strong>{sole_name}</strong> remains active; the other components have
                    cleared. A single active agent under continued replication is the exact
                    condition that selects resistance (methodology &sect;8.1). Monotherapy window
                    approximately <strong>{ms}–{me} h</strong> (duration {md} h).<br>
                   <strong>Action:</strong> Restart the full regimen simultaneously; do not restart
                    a single component. Order a viral load.<br>
                    <span style='color:#94a3b8;'>Class B &middot; {RULESET_FINGERPRINT}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif state_available and current_state == sel.NO_PRESSURE:
            directives_fired += 1
            st.markdown(f"""
            <div class='alert-warning'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   NO ACTIVE DRUG — VIRAL REBOUND RISK (LOW SELECTION PRESSURE)
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Every modelled component has cleared. There is no differential advantage for a
                    resistant variant, so <strong>selection risk is low</strong>, but the patient is
                    without antiretroviral cover and wild-type virus will rebound (methodology &sect;8.1).<br>
                   <strong>Action:</strong> Restart the full regimen; assess for OI risk if CD4 is low.<br>
                    <span style='color:#94a3b8;'>Class B &middot; {RULESET_FINGERPRINT}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif state_available and current_state == sel.PARTIAL_SUPPRESSION and mono_window:
            # Not currently in monotherapy, but the window lies ahead in the modelled horizon.
            directives_fired += 1
            ms, me, md = mono_window
            st.markdown(f"""
            <div class='alert-warning'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   MONOTHERAPY WINDOW AHEAD — REDUCED BARRIER TO RESISTANCE
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Components are clearing at different rates. On the modelled trajectory a
                    functional-monotherapy window opens at approximately <strong>{ms}–{me} h</strong>
                    (duration {md} h) since the last dose.<br>
                   <strong>Action:</strong> Re-establish full adherence before that window; counsel on
                    the resistance risk of partial re-dosing.<br>
                    <span style='color:#94a3b8;'>Class B &middot; {RULESET_FINGERPRINT}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── No directives ──
        # Never render a green all-clear while any regimen component is outside the
        # score: silence would read as reassurance the assessment cannot support.
        if directives_fired == 0:
            if unscored_components:
                st.markdown(f"""
                <div class='alert-info'>
                    <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                       NO DIRECTIVES FROM MODELLED COMPONENTS — ASSESSMENT PARTIAL
                    </div>
                    <div style='font-size:0.82rem; line-height:1.7;'>
                        No directive fired for the components currently in the model. This is
                        <strong>not an all-clear</strong>:
                        <strong>{', '.join(unscored_components)}</strong>
                        {'is' if len(unscored_components) == 1 else 'are'} outside the score
                        (nucleos(t)ide prodrug — intracellular anabolite, no plasma-comparable
                        threshold; methodology &sect;3.4). Interpret the tier B exposure percentages
                        in the drug status panel alongside this.<br>
                       <strong>Routine Action:</strong> Continue current regimen; confirm 3-monthly
                        pharmacy collection.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='alert-success'>
                    <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                       NO ACTIVE CLINICAL DIRECTIVES
                    </div>
                    <div style='font-size:0.82rem; line-height:1.7;'>
                        Every regimen component is modelled and none triggered a directive.<br>
                       <strong>Routine Action:</strong> Continue current regimen.
                        Confirm 3-monthly pharmacy collection. Record in the facility register.
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Protocol Reference Table ──
        st.markdown("<p class='section-header'>Clinical Guideline Reference Index</p>",
                    unsafe_allow_html=True)

        st.markdown(f"""
        <table class='styled-table'>
            <thead>
                <tr>
                    <th>Guideline</th>
                    <th>Section</th>
                    <th>Directive</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>South African ART Guidelines</td>
                    <td>TB/HIV Co-infection</td>
                    <td>DTG dose doubling on Rifampicin</td>
                    <td><span class='status-stable'>APPLIED</span></td>
                </tr>
                <tr>
                    <td>WHO HIV Guidelines</td>
                    <td>Paediatric Dosing</td>
                    <td>Weight-band DTG dispersible tablet</td>
                    <td><span class='status-stable'>APPLIED</span></td>
                </tr>
                <tr>
                    <td>Pharmacovigilance Reference</td>
                    <td>Traditional Medicine</td>
                    <td>Traditional medicine CYP450 warning</td>
                    <td><span class='status-stable'>APPLIED</span></td>
                </tr>
                <tr>
                    <td>Stanford HIVdb Algorithm</td>
                    <td>Mutation Scoring</td>
                    <td>K65R / M184V / R263K interpretation</td>
                    <td><span class='status-stable'>REFERENCED</span></td>
                </tr>
                <tr>
                    <td>Viral Load Monitoring Guidance</td>
                    <td>Laboratory Monitoring</td>
                    <td>Enhanced monitoring if VL >{VL_BANDS["high_above"]}</td>
                    <td>{'<span class="status-critical">ACTIVE</span>' if viral_load > VL_BANDS["high_above"] else '<span class="status-stable">ROUTINE</span>'}</td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # TAB 4: CLINICAL RISK & SUPPORT NEEDS
    #
    # Restructured in Stage 5 (methodology §11.2). The v4.0 / Stage-1-4 tab
    # summed socio-economic facts (unemployment, walking to clinic, no
    # transport, non-disclosure, food insecurity, a taxi strike) into a single
    # "Predicted Default Risk" percentage and rendered a bar chart itemising
    # which disadvantages produced it. Three objections drove the redesign
    # (§11.1): it encodes poverty as patient risk (a patient who is unemployed,
    # walks to the clinic and has not disclosed accumulates points before any
    # clinical fact enters the calculation); non-disclosure carries safeguarding
    # weight (a patient may not have disclosed because of intimate-partner-
    # violence risk, and scoring that on a screen that may be visible in a
    # shared consulting space is a potential safety issue independent of any
    # question about model accuracy); and the itemised chart makes the
    # reasoning visible in the wrong direction — the explanation shown to the
    # patient was a ranked list of their disadvantages.
    #
    # This tab now has two panels. Clinical risk draws only on the
    # pharmacokinetic and laboratory inputs already computed above (the same
    # composite band as Tab 1 — nothing new is calculated here). Support needs
    # draws on the socio-economic inputs, retained because the underlying
    # observation is sound (transport, cost and disclosure genuinely affect
    # whether people collect medication), but expressed as service
    # entitlements rather than a risk score. Non-disclosure contributes no
    # score and gets no itemised display anywhere patient-visible: adherence
    # counselling is shown as a standing offer to every patient regardless of
    # what they answered, so its presence on screen cannot be read as a signal
    # of any individual patient's disclosure status.
    # ────────────────────────────────────────────────────────────
    with tab4:
        col_ai1, col_ai2 = st.columns([1, 1])

        with col_ai1:
            st.markdown("<p class='section-header'>Clinical Risk — PK & Laboratory Only</p>",
                        unsafe_allow_html=True)
            st.markdown(f"""
            <div class='metric-card' style='text-align:center;'>
                <div style='font-size:0.7rem; color:#64748b; text-transform:uppercase;
                            letter-spacing:0.1em;'>Composite Risk Band</div>
                <div style='font-size:1.6rem; font-weight:700; color:{composite_colour}; margin:0.3rem 0;'>
                    {composite_label if composite_label else '—'}
                </div>
                <div style='font-size:0.66rem; color:#f59e0b;'>Class C — see the PK Decay Curves tab for the full derivation</div>
                <div style='font-size:0.72rem; color:#94a3b8; margin-top:0.6rem; text-align:left; line-height:1.7;'>
                    Regimen state: <strong>{STATE_META.get(current_state, ('not modelled', ''))[0] if current_state else 'not modelled'}</strong><br>
                    Viral load: <strong>{viral_load:,} cp/mL</strong><br>
                    CD4 count: <strong>{cd4_count:,} cells/&micro;L</strong><br>
                    Days since last dose: <strong>{days_missed}</strong>
                </div>
                <div style='font-size:0.68rem; color:#64748b; margin-top:0.6rem;'>
                    Draws only on pharmacokinetic and laboratory inputs. No socio-economic
                    factor contributes to this panel (methodology &sect;11.2).
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_ai2:
            st.markdown("<p class='section-header'>Support Needs — Entitlements, Not a Score</p>",
                        unsafe_allow_html=True)

            distance_km = st.slider("Distance from Clinic (km)", 0, 80, 22)
            missed_appts = st.slider("Missed Appointments (last 12m)", 0, 12, 2)
            transport = st.selectbox("Primary Transport",
                ["Private vehicle", "Taxi/minibus", "Walking", "No reliable transport"])
            taxi_strike = st.checkbox("Active Taxi Strike in District")
            food_insecurity = st.checkbox("Food Insecurity Reported")
            disclosure = st.selectbox("HIV Status Disclosure",
                ["Fully disclosed", "Partially disclosed", "Non-disclosed"],
                help="Recorded for the clinician's own counselling notes. This answer "
                     "does not appear anywhere else on screen or in any export "
                     "(methodology §11.1).")

            sn = RULES.get("support_needs", {})
            trig = sn.get("triggers", {})
            transport_trigger = (
                distance_km >= trig.get("distance_km_threshold", 20)
                or transport in ("Walking", "No reliable transport")
                or taxi_strike
            )
            chw_trigger = missed_appts >= trig.get("missed_appts_threshold", 2)

            entitlements = []
            if transport_trigger:
                entitlements.append(("Multi-month dispensing", "Eligible — reduces transport burden at future visits."))
                entitlements.append(("Transport support", "Indicated — distance, transport mode or a local disruption."))
            if chw_trigger:
                entitlements.append(("Community health worker contact", "May benefit this patient — missed-appointment history."))
            if food_insecurity:
                entitlements.append(("Nutritional support referral", "Indicated — food insecurity reported."))
            # Standing offer: rendered unconditionally, see the module note above.
            entitlements.append(("Adherence counselling", "Available to every patient on request."))

            for title, desc in entitlements:
                st.markdown(f"""
                <div class='metric-card' style='margin-bottom:0.5rem;'>
                    <div style='font-weight:600; color:#e2e8f0; font-size:0.85rem;'>{title}</div>
                    <div style='font-size:0.75rem; color:#94a3b8; margin-top:0.3rem; line-height:1.5;'>
                        {desc}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("""
            <div style='font-size:0.66rem; color:#64748b; margin-top:0.4rem; line-height:1.5;'>
                Triggers are class C (hand-chosen thresholds, methodology &sect;11.2). This
                panel lists what may help; it does not score the patient, and no
                itemised contribution chart is rendered anywhere in the application.
            </div>
            """, unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # TAB 5: AUDIT LOG & COMPLIANCE
    # ────────────────────────────────────────────────────────────
    with tab5:
        st.markdown("<p class='section-header'>Session Audit Trail</p>",
                    unsafe_allow_html=True)

        # ── Audit trail — real SHA-256 chain (methodology section 13.2) ──
        # All rows belong to a single assessment recorded at one instant.
        # Display time is SAST; the hashed entry stores UTC. Full SQLite
        # persistence is deferred to Stage 6; this session builds the chain
        # in memory so the displayed hashes are genuine and verifiable.
        now = datetime.datetime.now(SAST)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        ts_sast = now.strftime("%Y-%m-%d %H:%M:%S")
        ts_utc = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        facility_short = facility.split("–")[0].strip()

        raw_events = [
            ("CLINICAL SESSION OPENED",
             f"Patient {patient_id} | Clinician {clinician} | Facility: {facility_short}",
             "INFO"),
            ("PK ENGINE COMPUTED",
             f"Regimen: {regimen.split('(')[0].strip()} | Modifiers: {len(flat_mods)} applied",
             "INFO"),
        ]
        if tb_coinfection:
            raw_events.append((
                "GUIDELINE ALERT FIRED",
                "Rifampicin/DTG interaction. DTG dose doubling directive issued.",
                "CRITICAL"))
        if traditional_meds:
            raw_events.append((
                "PHARMACOVIGILANCE ALERT",
                "Traditional medicine interaction flagged. Counselling required.",
                "WARNING"))
        if state_available and current_state:
            state_txt = STATE_META.get(current_state, (current_state, ""))[0]
            level = "CRITICAL" if current_state == sel.FUNCTIONAL_MONOTHERAPY else "INFO"
            detail = f"Regimen state at {hours_missed}h: {state_txt}."
            if mono_window:
                detail += f" Monotherapy window {mono_window[0]}-{mono_window[1]}h."
            raw_events.append(("REGIMEN STATE CLASSIFIED", detail, level))
        raw_events.append((
            "LABORATORY VALUES RECORDED",
            f"Viral load: {viral_load:,} cp/mL | CD4: {cd4_count} cells/uL",
            "INFO"))
        raw_events.append((
            "SUPPORT NEEDS SCREENED",
            f"Entitlements: {', '.join(t for t, _ in entitlements)}",
            "INFO"))

        data_hashes = dict(DATA_HASHES)
        audit_events = []
        prev_hash = GENESIS_HASH
        for seq, (event, detail, level) in enumerate(raw_events, start=1):
            entry = {
                "seq": seq,
                "timestamp_utc": ts_utc,
                "sast_offset": "+02:00",
                "patient_ref": patient_id,
                "clinician_ref": clinician,
                "facility_code": facility_short,
                "event": event,
                "detail": detail,
                "level": level,
                "ruleset_version": RULESET_VERSION,
                "data_hashes": data_hashes,
                "prev_hash": prev_hash,
            }
            entry_hash = chain_entry(prev_hash, entry)
            audit_events.append({
                "seq": seq,
                "timestamp": ts_sast,
                "event": event,
                "detail": detail,
                "level": level,
                "prev_hash": prev_hash,
                "hash": entry_hash,
            })
            prev_hash = entry_hash

        level_colors = {
            "INFO":     "#3b82f6",
            "WARNING":  "#f59e0b",
            "CRITICAL": "#ef4444"
        }

        # ── Render Audit Table ──
        rows_html = ""
        for ev in audit_events:
            color = level_colors.get(ev["level"], "#94a3b8")
            hash_short = ev["hash"][:16] + "…"
            rows_html += f"""<tr>
                <td style='font-family:monospace; font-size:0.72rem; color:#64748b;'>
                    {ev["timestamp"]}
                </td>
                <td>
                    <span style='color:{color}; font-weight:600; font-size:0.78rem;'>
                        {html.escape(ev["event"])}
                    </span>
                </td>
                <td style='font-size:0.75rem; color:#94a3b8;'>{html.escape(ev["detail"])}</td>
                <td>
                    <span style='background:#0a0e1a; color:{color}; border:1px solid {color}33;
                                 border-radius:12px; padding:0.1rem 0.5rem; font-size:0.62rem;
                                 font-weight:700;'>
                        {ev["level"]}
                    </span>
                </td>
                <td style='font-family:monospace; font-size:0.65rem; color:#334155;'
                    title='{ev["hash"]}'>
                    {hash_short}
                </td>
            </tr>"""

        st.markdown(f"""
        <table class='styled-table'>
            <thead>
                <tr>
                    <th>Timestamp (SAST)</th>
                    <th>Event</th>
                    <th>Detail</th>
                    <th>Level</th>
                    <th>Entry Hash (SHA-256 chain)</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='margin-top:0.6rem; font-size:0.7rem; color:#64748b; line-height:1.6;'>
            Each row's hash is <strong>SHA-256(previous hash + canonical JSON of the row)</strong>,
            seeded from a genesis hash of {GENESIS_HASH[:8]}…. Altering any row changes every
            hash after it, so the chain is <strong>tamper-evident</strong>. It is <strong>not
            tamper-proof</strong>: an actor with write access can rebuild the whole chain.
            Genuine tamper resistance would require publishing the chain head outside this system.
            {RULESET_FINGERPRINT}.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Design Notes ──
        col_c1, col_c2, col_c3 = st.columns(3)

        design_notes = [
            (col_c1, "Pseudonymised Demo Data",
             "Patient identifiers here are pseudonymous placeholders. Pseudonymised health data "
             "remains personal information under POPIA (methodology §15); this build uses demo data "
             "only, with no real patient information.",
             "#10b981"),
            (col_c2, "Guideline-Informed Logic",
             "Clinical directives are modelled on publicly available South African and WHO ART treatment guidance, for educational purposes only.",
             "#3b82f6"),
            (col_c3, "Stanford HIVdb-Inspired",
             "Mutation interpretation logic is inspired by the public Stanford HIVdb resistance algorithm, for educational purposes only.",
             "#f59e0b"),
        ]

        for col, title, desc, color in design_notes:
            with col:
                st.markdown(f"""
                <div class='metric-card' style='border-color:{color}40; text-align:center;'>
                    <div style='font-weight:700; color:{color}; font-size:0.85rem;
                                margin-bottom:0.5rem;'>
                        {title}
                    </div>
                    <div style='font-size:0.73rem; color:#64748b; line-height:1.6;'>
                        {desc}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Export Section ──
        st.markdown("<p class='section-header'>Report Export</p>", unsafe_allow_html=True)

        exp_col1, exp_col2, exp_col3 = st.columns(3)

        # Drug-level lines: tier A shows level vs threshold; tier B prodrugs show
        # plasma only (no threshold, section 3.4); no-curve drugs are marked so.
        drug_level_rows = []
        for drug in active_drugs:
            stats = pk_db.get(drug, {})
            if not stats.get("curve_available"):
                drug_level_rows.append(f"{drug}: parameter unavailable — no decay curve (prodrug, unsourced)")
            elif drug in current_levels and "threshold_mg_L" in stats:
                lvl = current_levels[drug]
                thr = stats["threshold_mg_L"]
                state = "ABOVE" if lvl >= thr else "BELOW"
                drug_level_rows.append(f"{drug}: {lvl:.5f} mg/L (MIC={thr} | {state} MIC)")
            elif drug in current_levels:
                drug_level_rows.append(f"{drug}: {current_levels[drug]:.5f} mg/L plasma "
                                       "(prodrug — no plasma threshold, section 3.4)")
        drug_level_text = "\n".join(drug_level_rows)

        report_text = f"""
ResistanceMap ZA OS — Clinical Assessment Report
================================================
Software: ResistanceMap ZA OS v{APP_VERSION} · {RULESET_FINGERPRINT}
Research prototype — not an approved medical device. Not for clinical use.
Generated: {now.strftime("%d %B %Y %H:%M:%S")} SAST
Patient ID: {patient_id}
Facility: {facility}
Clinician: {clinician}

PHARMACOKINETIC SUMMARY
-----------------------
Regimen: {regimen}
Days Defaulted: {days_missed}
Composite Risk Band: {composite_label or 'n/a'} (ordinal, Class C — not a calibrated 0-100 score)
Regimen State (at {hours_missed}h): {STATE_META.get(current_state, ('not modelled', ''))[0] if current_state else 'not modelled'}
Monotherapy Window: {f'{mono_window[0]}-{mono_window[1]}h (duration {mono_window[2]}h)' if mono_window else 'none in the modelled horizon'}

DRUG LEVELS AT ASSESSMENT
--------------------------
{drug_level_text}

ACTIVE MODIFIERS
----------------
{chr(10).join([f"- {m}: {d}" for m, d in flat_mods]) if flat_mods else "None"}

CLINICAL DIRECTIVES
-------------------
TB Co-infection: {"YES – DTG 50 mg BD (rifampicin, UGT1A1)" if tb_coinfection else "No"}
St John's Wort: {"YES – direction only, no magnitude" if st_johns_wort else "No"}
African Potato: {"YES – no modelled effect; counsel" if african_potato else "No"}
Renal (eGFR): {egfr} mL/min/1.73m2 {"— safety alert" if egfr < 60 else ""}
Paediatric Protocol: {"YES – Weight-band dosing active" if paediatric else "No"}

SUPPORT NEEDS (entitlements, not a score — methodology section 11.2)
--------------------------------------------------------------------
{chr(10).join(f"- {t}: {d}" for t, d in entitlements)}

LABORATORY VALUES
-----------------
Viral Load: {viral_load:,} copies/mL
CD4 Count: {cd4_count} cells/μL

AUDIT INTEGRITY
---------------
""" + "\n".join([f"[{e['level']}] {e['timestamp']} — {e['event']}" for e in audit_events])

        with exp_col1:
            st.download_button(
                label="Download Clinical Report (.txt)",
                data=report_text,
                file_name=f"ResistanceMapZA_{patient_id}_{now.strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

        with exp_col2:
            st.markdown("""
            <div style='background:#0d1b2e; border:1px solid #1e3a5f; border-radius:8px;
                        padding:0.6rem; text-align:center; font-size:0.75rem; color:#475569;
                        opacity:0.5;'>
               Export to TIER.Net<br>
                <span style='color:#334155;'>Not implemented — planned</span>
            </div>
            """, unsafe_allow_html=True)

        with exp_col3:
            st.markdown("""
            <div style='background:#0d1b2e; border:1px solid #1e3a5f; border-radius:8px;
                        padding:0.6rem; text-align:center; font-size:0.75rem; color:#475569;
                        opacity:0.5;'>
               Push to NHLS Portal<br>
                <span style='color:#334155;'>Not implemented — planned</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Footer ──
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='border-top:1px solid #1e3a5f; padding-top:1rem; text-align:center;
                font-size:0.65rem; color:#334155; line-height:2;'>
        ResistanceMap ZA OS v{APP_VERSION} &nbsp;·&nbsp; Clinical Decision Support System Prototype<br>
        {RULESET_FINGERPRINT}<br>
        Contact: sbagaria2009@gmail.com<br>
        <span style='color:#1e3a5f;'>
            Educational and research prototype only — not an approved medical device.
            Not a substitute for qualified medical judgement.
            Do not use for real clinical decisions.
        </span>
    </div>
    """, unsafe_allow_html=True)
