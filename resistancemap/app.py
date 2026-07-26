"""ResistanceMap ZA — entrypoint.

Research prototype — not an approved medical device. Not for clinical use.

Run with: streamlit run resistancemap/app.py
"""

import os
import sys

# Streamlit's script runner only adds this file's own directory (resistancemap/)
# to sys.path, not its parent — so the package-qualified imports below can't
# resolve `resistancemap` unless the repo root is added explicitly here.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import streamlit as st

# st.set_page_config must be the first Streamlit call in the process, so the
# theme module's page-config step runs before anything else — including the
# config import below, whose failure path can call st.error()/st.stop().
from resistancemap.ui import theme

theme.configure_page()

from resistancemap import config
from resistancemap.ui import dashboard, patient_guide

theme.apply()

st.sidebar.markdown("<p class='sidebar-label'>System View Mode</p>", unsafe_allow_html=True)
app_view = st.sidebar.radio(
    "Select Interface Page:",
    ["About ResistanceMap ZA", "Understanding Your Results", "Patient Assessment Dashboard"]
)
st.sidebar.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)

# Demo-mode banner and prototype disclaimer: shown here, at the top level, so
# they appear on every screen (About, patient guide, dashboard) rather than
# only within one view's own sidebar block (methodology section 7.1 / stage 7).
st.sidebar.markdown("""
<div style='background:#0a1628; border:1px solid #1e3a5f; border-radius:8px;
            padding:0.6rem 0.8rem; margin-bottom:0.8rem; font-size:0.72rem;'>
    <div style='color:#f59e0b; font-weight:600;'>DEMO MODE — SIMULATED DATA</div>
    <div style='color:#475569; margin-top:0.2rem;'>
        Research prototype. Not an approved medical device. Not for clinical use.
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# VIEW MODE A: ABOUT / MAIN FRONT PAGE
#
# Rewritten in Stage 6/7 to describe what the application actually does. The
# v4.0 text claimed the tool "tracks how HIV mutations cluster in different
# communities", "predicts resistance hotspots", and "bridges genomic sequence
# data (NCBI GenBank / Stanford HIVdb)" with local protocols — none of which
# this application does. It does not process sequence data, does not detect
# mutations, and does not do any geographic or population-level analysis; it
# models one patient's pharmacokinetics against a known missed-dose count
# (methodology section 1). Claiming otherwise would repeat the "capability
# claims for things that do not exist" failure this remediation removed
# elsewhere (visitor counters, NHLS auto-ingest, TIER.Net export, and so on).
# ------------------------------------------------------------
if app_view == "About ResistanceMap ZA":
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #0d1b2e 0%, #0d2542 100%);
                border: 1px solid #1e3a5f; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4); text-align: center;'>
        <h1 style='font-size: 2.5rem; font-weight: 700; color: #e2e8f0; margin: 0;'>ResistanceMap ZA</h1>
        <p style='font-size: 1.1rem; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.5rem;'>
            Pharmacokinetic Adherence Modelling — Research Prototype
        </p>
        <p style='font-size: 0.95rem; color: #94a3b8; max-width: 800px; margin: 1rem auto 0 auto; line-height: 1.6;'>
            For a single patient on a known antiretroviral regimen who has missed a known number of days
            of doses, this tool estimates which regimen components have likely fallen below their efficacy
            threshold, and whether the resulting pattern favours selection of drug-resistant virus. It does
            not analyse genetic sequence data, does not detect mutations, and has not been validated against
            any patient outcome dataset (see the Limitations note in every export).
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='metric-card' style='height: 100%;'>
            <h3 style='color: #3b82f6; font-size: 0.9rem;'>What is ResistanceMap ZA?</h3>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-top: 0.5rem;'>
                A single-patient decision-support prototype. It models how much of each drug in a regimen is
                likely left in the body after a missed-dose gap, and estimates whether the pattern of remaining
                drug creates a "functional monotherapy" window — the condition most associated with selecting
                resistant virus.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card' style='height: 100%;'>
            <h3 style='color: #3b82f6; font-size: 0.9rem;'>Why is it useful?</h3>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-top: 0.5rem;'>
                As a teaching aid, it makes the pharmacokinetic reasoning behind adherence counselling visible,
                and as a specification it sets out exactly what a future retrospective validation study would
                need to check before any clinical claim could be made.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card' style='height: 100%;'>
            <h3 style='color: #3b82f6; font-size: 0.9rem;'>Who is it for?</h3>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-top: 0.5rem;'>
                Built for teaching and for reviewers assessing the methodology, not for prescribing. Every
                screen and export states plainly that this is a research prototype, not an approved medical
                device, and must not be used for real clinical decisions.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><p class='section-header'>How to Navigate</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: #0d1b2e; border: 1px solid #1e3a5f; border-radius: 8px; padding: 1.2rem 1.5rem; font-size: 0.88rem; line-height: 1.7; color: #cbd5e1;'>
        <strong>Using the prototype:</strong><br>
        1. Use the <strong>System View Mode</strong> radio in the sidebar to switch pages.<br>
        2. Choose <strong>Patient Assessment Dashboard</strong> for the live pharmacokinetic model.<br>
        3. Adjust the regimen, comorbidities, and adherence inputs in the sidebar to see the model recompute.<br>
        4. Read the coloured class label (A/B/C) next to every number — it states how much confidence that
           figure carries, per <code>METHODOLOGY.md</code>.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='border-top:1px solid #1e3a5f; padding-top:1rem; text-align:center;
                font-size:0.65rem; color: #475569; line-height:2;'>
        ResistanceMap ZA v{config.APP_VERSION} &nbsp;·&nbsp; {config.RULESET_FINGERPRINT}<br>
        Contact: sbagaria2009@gmail.com<br>
        Research prototype for educational use only. Not an approved medical device. Not for clinical use.
    </div>
    """, unsafe_allow_html=True)

elif app_view == "Understanding Your Results":
    patient_guide.render()

elif app_view == "Patient Assessment Dashboard":
    dashboard.render()
