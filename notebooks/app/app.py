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

# ============================================================
# DATA BUNDLE LOADING (versioned rules, methodology section 13.2)
# ============================================================
APP_VERSION = "5.0"
DATA_DIR = Path(__file__).resolve().parent / "data"
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
RISK_W = RULES["risk_score_weights"]
ADH_W = RULES["adherence_weights"]
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
                                      help="CYP3A4 inducer — reduces DTG half-life by ~50%")

        traditional_meds = st.checkbox("Traditional Medicine (St. John's Wort / African Potato)",
                                        help="CYP450 pathway interaction")

        renal_function = st.selectbox("Kidney Function (eGFR)",
            ["Normal (>90 mL/min)",
             "Mild Impairment (60–89 mL/min)",
             "Moderate Impairment (30–59 mL/min)",
             "Severe Impairment (<30 mL/min)"])

        paediatric = st.checkbox("Paediatric Patient (Weight-Band Dosing)",
                                  help="Activates paediatric PK adjustment engine")

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

        # Rifampicin (via the TB co-infection flag)
        if tb_coinfection and drug == "Dolutegravir":
            ix = INTERACTIONS["rifampicin_dtg"]
            t_half *= ix["multiplier"]
            applied.append((ix["display_name"], ix["display_desc"]))

        if tb_coinfection and drug == "Efavirenz":
            ix = INTERACTIONS["rifampicin_efv"]
            t_half *= ix["multiplier"]
            applied.append((ix["display_name"], ix["display_desc"]))

        # Traditional medicine (single combined toggle; SJW multipliers applied)
        if traditional_meds and drug == "Dolutegravir":
            ix = INTERACTIONS["sjw_dtg"]
            t_half *= ix["multiplier"]
            applied.append((ix["display_name"], ix["display_desc"]))

        if traditional_meds and drug == "Efavirenz":
            ix = INTERACTIONS["sjw_efv"]
            t_half *= ix["multiplier"]
            applied.append((ix["display_name"], ix["display_desc"]))

        # Renal impairment
        renal_factor = 1.0
        if stats.get("renal_sensitive"):
            rmul = INTERACTIONS["renal_tdf_3tc"]["multipliers"]
            if "Moderate Impairment" in renal_function:
                renal_factor = rmul["moderate"]
            elif "Severe Impairment" in renal_function:
                renal_factor = rmul["severe"]
            elif "Mild Impairment" in renal_function:
                renal_factor = rmul["mild"]
            if renal_factor > 1.0:
                t_half *= renal_factor
                applied.append((INTERACTIONS["renal_tdf_3tc"]["display_name"],
                                f"+{int((renal_factor - 1) * 100)}% TFV/3TC half-life"))

        # Paediatric weight-band adjustment (linear W/W_ref)
        if paediatric:
            pw = INTERACTIONS["paediatric_weight"]
            weight_factor = max(pw["floor"], min(pw["cap"], weight_kg / pw["weight_reference_kg"]))
            t_half *= weight_factor
            applied.append((pw["display_name"], f"Weight factor {weight_factor:.2f}"))

        return t_half, applied


    # ── Run PK for all active drugs ──
    current_levels   = {}
    adjusted_halves  = {}
    all_modifiers    = {}

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
        k_e = math.log(2) / adj_t_half
        current_levels[drug] = stats["c_max"] * math.exp(-k_e * hours_missed)
        all_modifiers[drug] = mods


    # ── Derived Risk Signals ──
    # Only tier A drugs carry a threshold_mg_L (methodology section 3.4); tier B
    # prodrugs are excluded from these plasma-threshold comparisons until the
    # Stage 3 two-tier engine provides their relative-exposure classification.
    vulnerable_drugs = [
        d for d in active_drugs
        if d in current_levels and "threshold_mg_L" in pk_db[d]
        and (pk_db[d]["threshold_mg_L"] * 0.05) < current_levels[d] < pk_db[d]["threshold_mg_L"]
    ]

    below_mic_drugs = [
        d for d in active_drugs
        if d in current_levels and "threshold_mg_L" in pk_db[d]
        and current_levels[d] < pk_db[d]["threshold_mg_L"]
    ]

    # ── Global Risk Score (0–100) ──
    # Weights relocated to rules.yaml (methodology section 10). Class C. The whole
    # score is restructured in Stage 4 (section 10.2); the arithmetic is unchanged.
    def compute_risk_score():
        w = RISK_W
        score = 0
        score += days_missed * w["per_day_missed"]
        score += len(below_mic_drugs) * w["per_below_threshold_drug"]
        score += len(vulnerable_drugs) * w["per_vulnerable_drug"]
        if tb_coinfection:                        score += w["tb_coinfection"]
        if traditional_meds:                      score += w["traditional_meds"]
        if viral_load > VL_BANDS["high_above"]:   score += w["viral_load_gt_1000"]
        if cd4_count < CD4_BANDS["severe_below"]: score += w["cd4_lt_200"]
        if paediatric:                            score += w["paediatric"]
        return min(score, w["cap"])

    risk_score = compute_risk_score()

    if risk_score >= 70:
        risk_label = "CRITICAL"
        risk_color = "#ef4444"
    elif risk_score >= 40:
        risk_label = "ELEVATED"
        risk_color = "#f59e0b"
    else:
        risk_label = "STABLE"
        risk_color = "#10b981"

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

    # ── Top KPI Strip ──
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    with kpi1:
        st.markdown(f"""
        <div class='metric-card'>
            <h3>Resistance Risk Score</h3>
            <div class='metric-value' style='color:{risk_color};'>{risk_score}/100</div>
            <div class='metric-delta' style='color:{risk_color};'>● {risk_label}</div>
        </div>""", unsafe_allow_html=True)

    with kpi2:
        below_count = len(below_mic_drugs)
        bc_color = "#ef4444" if below_count > 0 else "#10b981"
        st.markdown(f"""
        <div class='metric-card'>
            <h3>Drugs Below MIC</h3>
            <div class='metric-value' style='color:{bc_color};'>{below_count}/{len(active_drugs)}</div>
            <div class='metric-delta' style='color:#64748b;'>Sub-inhibitory level</div>
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
                subplot_titles=("Plasma Concentration vs. Time (Log Scale)",
                                "% MIC Coverage Remaining"),
                vertical_spacing=0.12,
                row_heights=[0.65, 0.35]
            )

            for drug in active_drugs:
                stats = pk_db.get(drug)
                if not stats or not stats.get("curve_available"):
                    continue
                adj_t = adjusted_halves[drug]
                k_e   = math.log(2) / adj_t
                decay = stats["c_max"] * np.exp(-k_e * time_array)

                color = stats["color"]

                # Main decay line
                fig.add_trace(go.Scatter(
                    x=time_array, y=decay,
                    mode='lines', name=drug,
                    line=dict(width=2.5, color=color),
                    hovertemplate=(
                        f"<b>{drug}</b><br>"
                        "Time: %{x:.0f}h<br>"
                        "Conc: %{y:.4f} mg/L<extra></extra>"
                    )
                ), row=1, col=1)

                # Threshold line, secondary line and % coverage only exist for tier A
                # drugs (methodology section 3.4); tier B prodrugs carry no threshold.
                if "threshold_mg_L" in stats:
                    mic_pct = (decay / stats["threshold_mg_L"]) * 100

                    # Primary efficacy threshold line
                    fig.add_trace(go.Scatter(
                        x=[0, t_max_hours],
                        y=[stats["threshold_mg_L"], stats["threshold_mg_L"]],
                        mode='lines', name=f"{drug} threshold",
                        line=dict(width=1.2, dash='dot', color=color),
                        opacity=0.5,
                        showlegend=False,
                        hoverinfo='skip'
                    ), row=1, col=1)

                    # Secondary reference line (e.g. DTG EC90, EFV SA-cohort limit)
                    if stats.get("secondary_threshold"):
                        fig.add_trace(go.Scatter(
                            x=[0, t_max_hours],
                            y=[stats["secondary_threshold"], stats["secondary_threshold"]],
                            mode='lines',
                            name=f"{drug} {stats.get('secondary_label', 'secondary')}",
                            line=dict(width=1.0, dash='dash', color=color),
                            opacity=0.3,
                            showlegend=False,
                            hoverinfo='skip'
                        ), row=1, col=1)

                    # MIC % coverage
                    fig.add_trace(go.Scatter(
                        x=time_array, y=mic_pct,
                        mode='lines', name=f"{drug} MIC%",
                        line=dict(width=2, color=color),
                        fill='tozeroy', fillcolor=f"rgba{tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) + (0.08,)}",
                        showlegend=False,
                        hovertemplate=(
                            f"<b>{drug}</b><br>"
                            "Time: %{x:.0f}h<br>"
                            "MIC Coverage: %{y:.1f}%<extra></extra>"
                        )
                    ), row=2, col=1)

            # 100% MIC reference on subplot 2
            fig.add_trace(go.Scatter(
                x=[0, t_max_hours], y=[100, 100],
                mode='lines', name="100% MIC",
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

            # Resistance window shading
            fig.add_vrect(
                x0=hours_missed * 0.85, x1=min(hours_missed * 1.3, t_max_hours),
                fillcolor="rgba(239,68,68,0.06)", line_width=0,
                annotation_text="Resistance Window",
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
                title_text="% MIC Coverage", row=2, col=1
            )

            st.plotly_chart(fig, width="stretch")

        with col_status:
            st.markdown("<p class='section-header'>Drug Status Panel</p>", unsafe_allow_html=True)

            for drug in active_drugs:
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

                lvl = current_levels[drug]
                adj_t = adjusted_halves[drug]

                # Tier A drugs carry a threshold and get an above/below classification.
                if "threshold_mg_L" in stats:
                    mic = stats["threshold_mg_L"]
                    pct = (lvl / mic) * 100
                    if lvl >= mic:
                        status_html = "<span class='status-stable'>ABOVE MIC</span>"
                    elif lvl >= mic * 0.05:
                        status_html = "<span class='status-warning'>SUB-INHIBITORY</span>"
                    else:
                        status_html = "<span class='status-critical'>CLEARED</span>"
                    threshold_line = f"MIC: {mic} mg/L &nbsp;·&nbsp; {pct:.1f}% coverage"
                else:
                    # Tier B prodrug: plasma shown, but no plasma threshold (section 3.4).
                    status_html = "<span class='status-warning'>PRODRUG</span>"
                    threshold_line = ("No plasma threshold — intracellular anabolite model "
                                      "arrives in Stage 3 (&sect;3.4)")

                st.markdown(f"""
                <div class='metric-card' style='margin-bottom:0.6rem;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;
                                margin-bottom:0.5rem;'>
                        <span class='drug-badge'>{drug}</span>
                        {status_html}
                    </div>
                    <div style='font-size:0.72rem; color:#64748b;'>Plasma Level</div>
                    <div style='font-size:1.3rem; font-weight:700; color:{stats["color"]};'>
                        {lvl:.4f} mg/L
                    </div>
                    <div style='font-size:0.72rem; color:#64748b; margin-top:0.3rem;'>
                        {threshold_line}
                    </div>
                    <div style='font-size:0.72rem; color:#64748b;'>
                        Adj. t½: {adj_t:.1f}h &nbsp;·&nbsp; {stats["class"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ── Mini Risk Gauge ──
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Risk Score", 'font': {'color': '#94a3b8', 'size': 12}},
                number={'font': {'color': risk_color, 'size': 28}},
                gauge={
                    'axis': {
                        'range': [0, 100],
                        'tickcolor': '#334155',
                        'tickfont': {'size': 9, 'color': '#475569'}
                    },
                    'bar': {'color': risk_color, 'thickness': 0.25},
                    'bgcolor': '#0a0e1a',
                    'bordercolor': '#1e3a5f',
                    'steps': [
                        {'range': [0, 40],  'color': '#022c22'},
                        {'range': [40, 70], 'color': '#2d1b00'},
                        {'range': [70, 100],'color': '#2d0000'},
                    ],
                    'threshold': {
                        'line': {'color': '#ef4444', 'width': 2},
                        'thickness': 0.8,
                        'value': risk_score
                    }
                }
            ))
            fig_gauge.update_layout(
                plot_bgcolor="#0d1b2e",
                paper_bgcolor="#0d1b2e",
                height=200,
                margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig_gauge, width="stretch")

    # ────────────────────────────────────────────────────────────
    # TAB 2: MUTATION & CROSS-RESISTANCE PREDICTOR
    # ────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<p class='section-header'>Genomic Resistance Prediction Engine</p>",
                    unsafe_allow_html=True)

        # ── Mutation Risk Matrix ──
        col_mut1, col_mut2 = st.columns([1.5, 1])

        with col_mut1:
            mutation_data = []
            for drug in active_drugs:
                stats = pk_db.get(drug)
                # A concentration ratio needs both a modelled level and a threshold,
                # so only tier A drugs appear here (methodology section 3.4).
                if not stats or drug not in current_levels or "threshold_mg_L" not in stats:
                    continue
                lvl = current_levels[drug]
                mic = stats["threshold_mg_L"]
                ratio = lvl / mic

                # Ordinal selection-pressure label (direction only, no probability).
                if ratio >= 2.0:
                    pressure = "SUPPRESSED"
                    p_color  = "#10b981"
                elif ratio >= 1.0:
                    pressure = "MARGINAL"
                    p_color  = "#3b82f6"
                elif ratio >= 0.05:
                    pressure = "HIGH"
                    p_color  = "#f59e0b"
                else:
                    pressure = "CRITICAL"
                    p_color  = "#ef4444"

                cross_res = ", ".join(stats.get("cross_resistance", ["None"]))

                mutation_data.append({
                    "drug":      drug,
                    "class":     stats["class"],
                    "mutation":  stats["mutation"],
                    "cross_res": cross_res,
                    "pressure":  pressure,
                    "p_color":   p_color,
                    "ratio":     ratio
                })

            # The fabricated "Estimated Mutation Emergence Probability" bar chart and its
            # 50% "Clinical Threshold" line were removed in v5.0 (methodology 9.1). A
            # validated ordinal mutation-risk index replaces it in a later stage; until
            # then this space intentionally shows no number.
            st.markdown("""
            <div class='alert-info'>
                <div style='font-weight:600; font-size:0.82rem;'>
                    Mutation-risk index pending
                </div>
                <div style='font-size:0.78rem; margin-top:0.3rem; line-height:1.6;'>
                    The previous percentage output has been removed because it was not derived
                    from any data (methodology &sect;9.1). An ordinal, clearly labelled index
                    replaces it in a later release. No probability is shown here in the interim.
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Cross-Resistance Map ──
            st.markdown("<p class='section-header'>Cross-Resistance Cascade Analysis</p>",
                        unsafe_allow_html=True)

            for m in mutation_data:
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                        <div>
                            <span class='drug-badge'>{m["drug"]}</span>
                            <span style='background:#1a0a2e; color:#c084fc; border:1px solid #7c3aed;
                                         border-radius:20px; padding:0.2rem 0.7rem; font-size:0.72rem;
                                         font-weight:600; margin-left:0.4rem;'>{m["class"]}</span>
                            <div style='margin-top:0.5rem; font-size:0.88rem;'>
                                <span style='color:#64748b;'>Primary Mutation Risk: </span>
                                <span style='color:#fbbf24; font-weight:700; font-size:1rem;'>
                                    {m["mutation"]}
                                </span>
                            </div>
                            <div style='font-size:0.78rem; color:#64748b; margin-top:0.2rem;'>
                                Cross-resistance cascade → &nbsp;
                                <span style='color:#94a3b8;'>{m["cross_res"]}</span>
                            </div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='font-size:0.65rem; color:#64748b;'>Selection Pressure</div>
                            <div style='color:{m["p_color"]}; font-weight:700; font-size:1.1rem;'>
                                {m["pressure"]}
                            </div>
                            <div style='font-size:0.7rem; color:#64748b;'>
                                Conc/MIC ratio: {m["ratio"]:.3f}×
                            </div>
                        </div>
                    </div>
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
            st.markdown("""
            <div class='alert-critical'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   PROTOCOL ALERT — RIFAMPICIN-DTG INTERACTION
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Patient is confirmed on <strong>Rifampicin</strong> for active TB co-infection.
                    Rifampicin is a potent <strong>CYP3A4 inducer</strong> that reduces Dolutegravir
                    plasma AUC by approximately <strong>54%</strong>.<br><br>
                   <strong>Mandatory Action:</strong> Increase Dolutegravir from
                    <span style='color:#fca5a5;'>50mg once daily → 50mg TWICE DAILY</span> (BD).<br>
                   <strong>Rationale:</strong> Standard clinical guidance for concurrent
                    Rifampicin-based TB treatment and Dolutegravir-based ART.<br>
                   <strong>Monitoring:</strong> Repeat viral load at 4 weeks post-adjustment.
                    Do not use NVP-based regimens concurrently.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Traditional Medicine Alert ──
        if traditional_meds:
            directives_fired += 1
            st.markdown("""
            <div class='alert-warning'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   PHARMACOVIGILANCE ALERT — TRADITIONAL MEDICINE CYP450 INTERACTION
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Patient is using traditional preparations containing compounds that interact
                    with the <strong>CYP2C9 / CYP3A4</strong> enzymatic pathways (Hyperforin in St. John's Wort;
                    Phytosterols in African Potato).<br><br>
                   <strong>Effect:</strong> Accelerated Dolutegravir clearance. Estimated plasma
                    concentration reduced by 30–40%.<br>
                   <strong>Action:</strong> Counsel patient on cessation. If non-adherent to
                    cessation, consider enhanced monitoring (3-monthly viral load).
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Renal Alert ──
        if "Moderate Impairment" in renal_function or "Severe Impairment" in renal_function:
            directives_fired += 1
            sev = "SEVERE RENAL IMPAIRMENT" if "Severe" in renal_function else "MODERATE RENAL IMPAIRMENT"
            st.markdown(f"""
            <div class='alert-warning'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   RENAL DOSE ADJUSTMENT REQUIRED — {sev}
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Patient has <strong>{renal_function}</strong>.
                    Tenofovir Disoproxil Fumarate (TDF) is renally cleared and is
                    <strong>nephrotoxic at accumulating concentrations</strong>.<br><br>
                   <strong>Action:</strong> {'Consider switching TDF → TAF (Tenofovir Alafenamide). TAF achieves equivalent efficacy at 10% the plasma concentration, reducing nephrotoxicity.' if 'Severe' in renal_function else 'Monitor eGFR monthly. Consider TAF switch if trajectory worsening. Avoid NSAIDs.'}<br>
                   <strong>Monitor:</strong> Monthly urinary phosphate/creatinine ratio.
                    Watch for Fanconi Syndrome.
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

        # ── Sub-MIC Mutation Pressure Alerts ──
        for drug in vulnerable_drugs:
            directives_fired += 1
            stats = pk_db[drug]
            mut = stats["mutation"]
            st.markdown(f"""
            <div class='alert-warning'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   SUB-INHIBITORY PRESSURE — {drug.upper()} / {mut} RISK
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    <strong>{drug}</strong> plasma concentration is in the sub-inhibitory range
                    (above detection, below MIC). This is the most dangerous pharmacokinetic window —
                    viral replication is occurring in the presence of drug, which is the exact
                    condition required for <strong>resistance mutation selection</strong>.<br><br>
                   <strong>Primary Mutation Risk:</strong>
                    <span style='color:#fde68a; font-weight:700;'>{mut}</span><br>
                   <strong>Immediate Action:</strong> Supervised re-dosing required within 6 hours.
                    Order point-of-care viral load to establish current replication status.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Below Detection Alerts ──
        for drug in below_mic_drugs:
            if drug not in vulnerable_drugs:
                directives_fired += 1
                st.markdown(f"""
                <div class='alert-critical'>
                    <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                       CRITICAL — {drug.upper()} CLEARED FROM PLASMA
                    </div>
                    <div style='font-size:0.82rem; line-height:1.7;'>
                        <strong>{drug}</strong> has been fully cleared. Zero pharmacological protection.
                        Patient is functionally without ART coverage for this component.<br><br>
                       <strong>Immediate Protocol:</strong> Do not restart mono-therapy.
                        Restart full regimen simultaneously. If defaulted >72h and CD4 <200,
                        initiate enhanced OI prophylaxis. Alert community health worker for
                        home visit.
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── All Clear ──
        if directives_fired == 0:
            st.markdown("""
            <div class='alert-success'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                   SYSTEM CLEAR — NO ACTIVE CLINICAL DIRECTIVES
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    All pharmacokinetic parameters are within therapeutic range.
                    No comorbidity interactions detected. Patient appears adherent.
                    Next scheduled viral load review as per routine NDoH monitoring schedule.
                    <br><br>
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
    # TAB 4: ADHERENCE RISK ENGINE
    # ────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("<p class='section-header'>Adherence & Support Screening — Heuristic (Class C)</p>",
                    unsafe_allow_html=True)

        col_ai1, col_ai2 = st.columns([1, 1])

        with col_ai1:
            # ── Simulated Risk Factor Inputs ──
            st.markdown("""
            <div class='metric-card'>
                <div style='font-size:0.72rem; color:#3b82f6; font-weight:600;
                            text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.8rem;'>
                    Patient Risk Factor Profile
                </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            distance_km = st.slider("Distance from Clinic (km)", 0, 80, 22)
            missed_appts = st.slider("Missed Appointments (last 12m)", 0, 12, 2)
            employment = st.selectbox("Employment Status",
                ["Employed (formal)", "Employed (informal)", "Unemployed", "Grant recipient"])
            transport = st.selectbox("Primary Transport",
                ["Private vehicle", "Taxi/minibus", "Walking", "No reliable transport"])
            taxi_strike = st.checkbox("Active Taxi Strike in District")
            food_insecurity = st.checkbox("Food Insecurity Reported")
            disclosure = st.selectbox("HIV Status Disclosure",
                ["Fully disclosed", "Partially disclosed", "Non-disclosed"])

            # ── Hand-weighted heuristic screen (class C, not a trained model) ──
            # Weights relocated to rules.yaml (methodology section 11); arithmetic
            # unchanged. Restructured into a support-needs panel in Stage 5.
            aw = ADH_W
            adherence_risk = 0
            adherence_risk += days_missed * aw["per_day_missed"]
            adherence_risk += distance_km * aw["per_km_distance"]
            adherence_risk += missed_appts * aw["per_missed_appt"]
            adherence_risk += aw["employment"].get(employment, 0)
            adherence_risk += aw["transport"].get(transport, 0)
            if taxi_strike:     adherence_risk += aw["taxi_strike"]
            if food_insecurity: adherence_risk += aw["food_insecurity"]
            adherence_risk += aw["disclosure"].get(disclosure, 0)
            adherence_risk = min(adherence_risk, aw["cap"])

            if adherence_risk >= 65:
                ar_label = "VERY HIGH RISK"
                ar_color = "#ef4444"
                ar_action = "Immediate community health worker dispatch"
            elif adherence_risk >= 40:
                ar_label = "ELEVATED RISK"
                ar_color = "#f59e0b"
                ar_action = "WhatsApp reminder + call-back within 48h"
            elif adherence_risk >= 20:
                ar_label = "MODERATE RISK"
                ar_color = "#3b82f6"
                ar_action = "Automated WhatsApp reminder sequence"
            else:
                ar_label = "LOW RISK"
                ar_color = "#10b981"
                ar_action = "Standard appointment reminder"

            # Adherence risk gauge
            fig_ad = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=adherence_risk,
                delta={'reference': 40, 'increasing': {'color': '#ef4444'},
                       'decreasing': {'color': '#10b981'}},
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Predicted Default Risk Score", 'font': {'color': '#94a3b8', 'size': 13}},
                number={'font': {'color': ar_color, 'size': 40}, 'suffix': '%'},
                gauge={
                    'axis': {'range': [0, 100], 'tickfont': {'size': 9, 'color': '#475569'}},
                    'bar': {'color': ar_color},
                    'bgcolor': '#0a0e1a',
                    'bordercolor': '#1e3a5f',
                    'steps': [
                        {'range': [0, 20],  'color': '#022c22'},
                        {'range': [20, 40], 'color': '#0c2340'},
                        {'range': [40, 65], 'color': '#2d1b00'},
                        {'range': [65, 100],'color': '#2d0000'},
                    ],
                }
            ))
            fig_ad.update_layout(
                plot_bgcolor="#0d1b2e",
                paper_bgcolor="#0d1b2e",
                height=260,
                margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_ad, width="stretch")

            st.markdown(f"""
            <div class='alert-{"critical" if adherence_risk >= 65 else "warning" if adherence_risk >= 40 else "info" if adherence_risk >= 20 else "success"}'>
                <div style='font-weight:700;'>
                    {ar_label} — Predicted Default Probability: {adherence_risk:.0f}%
                </div>
                <div style='font-size:0.8rem; margin-top:0.4rem;'>
                   <strong>Recommended Action:</strong> {ar_action}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_ai2:
            # ── Feature Importance Chart ──
            st.markdown("<p class='section-header'>Risk Factor Contribution Analysis</p>",
                        unsafe_allow_html=True)

            factors = {
                "Days Defaulted":        days_missed * aw["per_day_missed"],
                "Distance from Clinic":  distance_km * aw["per_km_distance"],
                "Missed Appointments":   missed_appts * aw["per_missed_appt"],
                "Employment Status":     aw["employment"].get(employment, 0),
                "Transport Access":      aw["transport"].get(transport, 0),
                "Taxi Strike Active":    aw["taxi_strike"] if taxi_strike else 0,
                "Food Insecurity":       aw["food_insecurity"] if food_insecurity else 0,
                "HIV Disclosure":        aw["disclosure"].get(disclosure, 0),
            }
            factors = {k: v for k, v in sorted(factors.items(), key=lambda x: x[1], reverse=True) if v > 0}

            if factors:
                fig_feat = go.Figure(go.Bar(
                    x=list(factors.values()),
                    y=list(factors.keys()),
                    orientation='h',
                    marker=dict(
                        color=list(factors.values()),
                        colorscale=[[0, '#1d4ed8'], [0.5, '#f59e0b'], [1, '#ef4444']],
                        showscale=False
                    ),
                    text=[f"+{v:.0f}" for v in factors.values()],
                    textposition='outside',
                    textfont=dict(color='#94a3b8', size=10)
                ))
                fig_feat.update_layout(
                    plot_bgcolor="#0a0e1a",
                    paper_bgcolor="#0d1b2e",
                    font=dict(family="Inter", color="#94a3b8", size=10),
                    xaxis=dict(gridcolor="#0f2237", title="Risk Score Contribution"),
                    yaxis=dict(gridcolor="#0f2237"),
                    height=300,
                    margin=dict(l=0, r=40, t=10, b=0)
                )
                st.plotly_chart(fig_feat, width="stretch")

            # ── Intervention Protocol ──
            st.markdown("<p class='section-header'>Automated Intervention Protocol</p>",
                        unsafe_allow_html=True)

            # These are suggested actions for the clinic team. The prototype does not
            # dispatch messages, contact workers, or submit laboratory orders.
            interventions = []
            if adherence_risk >= 65:
                interventions = [
                    ("CHW Home Visit", "Consider a community health worker home visit."),
                    ("Appointment Reminder", "Consider a reminder for medication collection."),
                    ("Clinic Call-Back", "Consider assigning an adherence counsellor."),
                    ("Multi-Month Dispensing", "Consider a 3-month supply to reduce transport burden.")
                ]
            elif adherence_risk >= 40:
                interventions = [
                    ("Appointment Reminder", "Consider a staged reminder sequence."),
                    ("Viral Load Review", "Consider reviewing whether a repeat viral load is due.")
                ]
            elif adherence_risk >= 20:
                interventions = [
                    ("Appointment Reminder", "Consider a standard pre-appointment reminder."),
                ]
            else:
                interventions = [
                    ("Routine Monitoring", "No enhanced intervention indicated. Standard care pathway.")
                ]

            for title, desc in interventions:
                st.markdown(f"""
                <div class='metric-card' style='margin-bottom:0.5rem;'>
                    <div style='font-weight:600; color:#e2e8f0; font-size:0.85rem;'>{title}</div>
                    <div style='font-size:0.75rem; color:#94a3b8; margin-top:0.3rem; line-height:1.5;'>
                        {desc}
                    </div>
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
        for drug in below_mic_drugs:
            raw_events.append((
                "EFFICACY THRESHOLD BREACH",
                f"{drug} modelled concentration below its efficacy threshold. "
                f"Signature mutation: {pk_db[drug]['mutation']}.",
                "CRITICAL"))
        raw_events.append((
            "LABORATORY VALUES RECORDED",
            f"Viral load: {viral_load:,} cp/mL | CD4: {cd4_count} cells/uL",
            "INFO"))
        raw_events.append((
            "ADHERENCE SCREEN COMPUTED",
            f"Heuristic default score: {adherence_risk:.0f} | Category: {ar_label}",
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
Risk Score: {risk_score}/100 ({risk_label})

DRUG LEVELS AT ASSESSMENT
--------------------------
{drug_level_text}

ACTIVE MODIFIERS
----------------
{chr(10).join([f"- {m}: {d}" for m, d in flat_mods]) if flat_mods else "None"}

CLINICAL DIRECTIVES
-------------------
TB Co-infection: {"YES – DTG dose doubling required" if tb_coinfection else "No"}
Traditional Medicine: {"YES – CYP450 interaction warning" if traditional_meds else "No"}
Renal Status: {renal_function}
Paediatric Protocol: {"YES – Weight-band dosing active" if paediatric else "No"}

ADHERENCE RISK
--------------
Default Risk Score: {adherence_risk:.0f}%
Risk Category: {ar_label}
Recommended Action: {ar_action}

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
