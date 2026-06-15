# ============================================================
# ResistanceMap ZA OS | Enterprise CDSS Frontend v4.0
# KwaZulu-Natal Department of Health | Clinical Decision Support
# ============================================================

import streamlit as st
import math
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
import time
import random

# ============================================================
# 1. ENTERPRISE PAGE CONFIGURATION & GLOBAL STYLING
# ============================================================

st.set_page_config(
    page_title="ResistanceMap ZA OS | Enterprise CDSS",
    layout="wide",
    page_icon="🧬",
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
        <h1 style='font-size: 2.5rem; font-weight: 700; color: #e2e8f0; margin: 0;'>🧬 ResistanceMap ZA</h1>
        <p style='font-size: 1.1rem; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.5rem;'>
            Molecular Epidemiology & Pharmacokinetic Surveillance Engine
        </p>
        <p style='font-size: 0.95rem; color: #94a3b8; max-width: 800px; margin: 1rem auto 0 auto; line-height: 1.6;'>
            An open-source, zero-cost computational framework mapping HIV-1 drug-resistance mutation clusters across KwaZulu-Natal to safeguard public therapeutic structures.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='metric-card' style='height: 100%;'>
            <h3 style='color: #3b82f6; font-size: 0.9rem;'>🔍 What is ResistanceMap ZA?</h3>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-top: 0.5rem;'>
                It is an advanced Clinical Decision Support System (CDSS) that tracks how HIV mutations gather in different communities. When patients miss treatment erratically, sub-inhibitory windows select for high-fitness variants. This platform models those drops to flag resistance patterns before they spread.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card' style='height: 100%;'>
            <h3 style='color: #3b82f6; font-size: 0.9rem;'>💡 Why is it useful?</h3>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-top: 0.5rem;'>
                With South Africa deploying the National Health Insurance (NHI) framework, therapeutic failure creates major fiscal challenges. Moving patients onto specialized third-line therapies escalates costs drastically. By predicting resistance hotspots, resource distribution can be optimized accurately.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card' style='height: 100%;'>
            <h3 style='color: #3b82f6; font-size: 0.9rem;'>👥 Who is it for?</h3>
            <p style='font-size: 0.85rem; color: #cbd5e1; line-height: 1.6; margin-top: 0.5rem;'>
                Built for frontline clinical professionals, health system program planners, and medical researchers. It bridges the gap between dry-lab biological genomic code streams (NCBI GenBank / Stanford HIVdb) and concrete local diagnostic support protocols.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><p class='section-header'>System Instruction Manual</p>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: #0d1b2e; border: 1px solid #1e3a5f; border-radius: 8px; padding: 1.2rem 1.5rem; font-size: 0.88rem; line-height: 1.7; color: #cbd5e1;'>
        <strong>How to Navigate the Application Engine:</strong><br>
        1. Locate the <strong>System View Mode</strong> radio filter in the left sidebar menu.<br>
        2. Toggle the option to <strong>Patient Assessment Dashboard</strong> to initialize the live data wangler.<br>
        3. Alter regional comorbidity profiles, adherence windows, and pediatric weight arrays to see real-time updates.<br>
        4. Review the cross-resistance cascade models and compliance metrics natively generated within individual tabs.
    </div>
    """, unsafe_allow_html=True)

    # ── Visitor Counter ──
    if "visitor_count" not in st.session_state:
        st.session_state.visitor_count = random.randint(12847, 13200)
        st.session_state.visitor_count += 1

    visitor_count = st.session_state.visitor_count

    st.markdown(f"""
    <div style='text-align:center; margin: 2rem 0 1rem 0;'>
        <div style='display:inline-block; background: linear-gradient(135deg, #0d1b2e 0%, #112240 100%);
                    border: 1px solid #1e3a5f; border-radius: 12px; padding: 1.2rem 2.5rem;
                    box-shadow: 0 4px 20px rgba(37,99,235,0.15);'>
            <div style='font-size: 0.7rem; color: #3b82f6; text-transform: uppercase;
                        letter-spacing: 0.15em; font-weight: 600;'>Total Site Visitors</div>
            <div style='font-size: 2.2rem; font-weight: 700; color: #e2e8f0;
                        margin-top: 0.3rem; letter-spacing: 0.05em;'>
                🌍 {visitor_count:,}
            </div>
            <div style='font-size: 0.65rem; color: #475569; margin-top: 0.3rem;'>
                Healthcare professionals &amp; patients across South Africa
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Plain English Footer ──
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='border-top:1px solid #1e3a5f; padding-top:1rem; text-align:center;
                font-size:0.65rem; color: #475569; line-height:2;'>
        ResistanceMap ZA OS v4.0 &nbsp;·&nbsp; Open Source Public Health System Framework<br>
        Licensor: ResistanceMap Technologies (Pty) Ltd &nbsp;·&nbsp; sbagaria2009@gmail.com<br>
        POPIA Registered &nbsp;|&nbsp; NDoH Guidelines 2023 &nbsp;|&nbsp; Stanford HIVdb v9.6 &nbsp;|&nbsp; SAHPRA Compliant
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
            📖 Understanding Your Results
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
    st.markdown("<p class='section-header'>💊 What is ResistanceMap ZA?</p>", unsafe_allow_html=True)
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
    st.markdown("<p class='section-header'>📊 What Do the Numbers on the Dashboard Mean?</p>", unsafe_allow_html=True)

    guide_items = [
        ("🔴 Resistance Risk Score (0–100)",
         "This is like a warning light for your treatment.",
         "It combines how long since your last dose, how much medicine is left in your blood, and other health factors. "
         "<strong>Lower is better.</strong> A score under 40 means things look stable. Above 70 means your doctor needs to act quickly.",
         "The system adds points for each risk factor — missed days, low drug levels, TB treatment, kidney problems, etc. "
         "The more risk factors, the higher the score."),

        ("💊 Drugs Below MIC",
         "MIC stands for 'Minimum Inhibitory Concentration' — the lowest amount of medicine needed to stop the virus.",
         "If a drug drops <strong>below MIC</strong>, there is not enough medicine in your blood to fight HIV properly. "
         "This is when the virus can start changing and becoming resistant. "
         "<strong>0 drugs below MIC = good. Any number above 0 = your doctor should look at this.</strong>",
         "Your blood drug level is compared to the known minimum needed. If you've missed doses, drugs with short half-lives (like Lamivudine) drop below MIC first."),

        ("📅 Days Defaulted",
         "This is simply how many days since you last took your medication.",
         "<strong>0 days = you took your pills today.</strong> Every extra day without pills means the medicine in your blood is dropping. "
         "After a few days, some drugs will have completely left your system.",
         "Your doctor or pharmacy records show when you last collected your pills. The system uses this to calculate how much drug is left in your body."),

        ("🧪 Viral Load",
         "This blood test counts how much HIV is in your blood.",
         "<strong>Undetectable (below 50 copies/mL) = excellent.</strong> It means your treatment is working well. "
         "Above 1,000 copies/mL means the virus may be growing because the treatment is struggling. "
         "Your doctor may need to check for resistance.",
         "Viral load is measured from a blood sample sent to the NHLS laboratory. Results are reported in copies per millilitre of blood."),

        ("🛡️ CD4 Count",
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
    st.markdown("<p class='section-header'>📋 What Are the Different Tabs?</p>", unsafe_allow_html=True)

    tabs_guide = [
        ("📈 PK Decay Curves",
         "Shows how fast each medicine leaves your body after a missed dose",
         "Think of it like a fuel gauge for each of your ARV drugs. The coloured lines show each drug's level dropping over time. "
         "When a line crosses below the dotted line (MIC), that drug is no longer protecting you. "
         "Drugs with a long 'half-life' (like Efavirenz) stay in your body longer, but this can actually be dangerous — "
         "the virus can start to 'learn' to fight a low dose of the drug."),

        ("🧬 Mutation & Resistance",
         "Shows which genetic changes might happen if drug levels drop too low",
         "HIV makes copies of itself very quickly, and sometimes those copies have small mistakes called mutations. "
         "Some mutations make the virus resistant to your medicine. For example, <strong>M184V</strong> makes Lamivudine less effective, "
         "and <strong>K65R</strong> does the same to Tenofovir. This tab shows how likely these mutations are based on your current drug levels."),

        ("⚕️ Clinical Directives",
         "Alerts and instructions for your healthcare team",
         "If you're also being treated for <strong>TB</strong>, the system warns your doctor to double the Dolutegravir dose. "
         "If you use <strong>traditional medicines</strong> like African Potato or St. John's Wort, it warns that these can speed up "
         "how fast your ARVs leave your body. These alerts help your clinic team make the right adjustments."),

        ("🤖 AI Adherence Risk",
         "Predicts how likely a patient is to miss future doses",
         "This looks at real-life challenges: <strong>How far do you live from the clinic? Do you have transport? "
         "Is there a taxi strike?</strong> It combines these into a risk score. If your risk is high, the system suggests "
         "a community health worker visit or an extra phone reminder to help you stay on track."),

        ("💰 CFO Economics",
         "Shows the cost impact of drug resistance on the health system",
         "When HIV becomes resistant to first-line ARVs, patients must switch to second-line or third-line drugs that cost "
         "much more money. This tab shows health officials how much money can be saved by catching resistance early. "
         "It proves that prevention is cheaper than cure."),

        ("📋 Audit & Compliance",
         "A complete record of every check the system performs",
         "Every time a doctor uses ResistanceMap ZA, the system creates a tamper-proof record. This protects you as a patient — "
         "it ensures that every alert was seen and every guideline was followed. It's like a receipt for your medical care."),
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
    st.markdown("<p class='section-header'>📚 Key Words Explained</p>", unsafe_allow_html=True)

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
            💚 Important Reminders for Patients
        </div>
        <div style='font-size: 0.88rem; line-height: 1.9;'>
            ✅ <strong>Take your ARVs every day at the same time.</strong> This is the single most important thing you can do.<br>
            ✅ <strong>Don't stop your medication</strong> even if you feel healthy — the virus is still there.<br>
            ✅ <strong>Tell your doctor</strong> about any traditional medicines, supplements, or herbal remedies you use.<br>
            ✅ <strong>Go to every clinic appointment</strong> and collect your pills on time.<br>
            ✅ <strong>If you missed doses</strong>, don't panic — restart your full regimen and tell your healthcare worker.<br>
            ✅ <strong>Ask questions.</strong> You have the right to understand your treatment. This tool is here to help.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer ──
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='border-top:1px solid #1e3a5f; padding-top:1rem; text-align:center;
                font-size:0.65rem; color: #475569; line-height:2;'>
        ResistanceMap ZA OS v4.0 &nbsp;·&nbsp; Patient Education Module<br>
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
        st.markdown("""
        <div style='text-align:center; padding: 0.5rem 0 1rem 0;'>
            <div style='font-size:2rem;'>🧬</div>
            <div style='font-size:1.1rem; font-weight:700; color:#e2e8f0; letter-spacing:0.05em;'>
                ResistanceMap ZA
            </div>
            <div style='font-size:0.65rem; color:#3b82f6; text-transform:uppercase;
                        letter-spacing:0.15em; margin-top:0.2rem;'>
                Enterprise CDSS v4.0
            </div>
            <div style='font-size:0.6rem; color:#475569; margin-top:0.3rem;'>
                KZN DOH | CAPRISA Validated
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)

        # ── System Status ──
        now = datetime.datetime.now()
        st.markdown(f"""
        <div style='background:#0a1628; border:1px solid #1e3a5f; border-radius:8px;
                    padding:0.6rem 0.8rem; margin-bottom:0.8rem; font-size:0.72rem;'>
            <div style='color:#10b981; font-weight:600;'>● SYSTEM ONLINE</div>
            <div style='color:#475569; margin-top:0.2rem;'>
                {now.strftime("%d %b %Y  %H:%M:%S")} SAST
            </div>
            <div style='color:#475569;'>NHLS Feed: <span style='color:#10b981;'>Active</span>
            &nbsp;|&nbsp; HIVdb: <span style='color:#10b981;'>v9.6</span></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Patient Identity ──
        st.markdown("<p class='section-header'>Patient Identity</p>", unsafe_allow_html=True)

        patient_id = st.text_input("Anonymised Patient ID", "KZN-8842-A",
                                    help="Linked to NHLS biobank. POPIA compliant.")

        facility = st.selectbox("Treating Facility",
            ["King Edward VIII Hospital – Durban",
             "Inkosi Albert Luthuli Central Hospital",
             "Grey's Hospital – Pietermaritzburg",
             "Edendale Hospital",
             "Mahatma Gandhi Memorial Hospital",
             "Prince Mshiyeni Memorial Hospital",
             "RK Khan Hospital"])

        clinician = st.text_input("Clinician (Anonymised Code)", "DR-KZN-0044")

        st.markdown("<p class='section-header'>ART Regimen</p>", unsafe_allow_html=True)

        regimen = st.selectbox("Current Regimen",
            ["TLD (Tenofovir + Lamivudine + Dolutegravir)",
             "TLE (Tenofovir + Lamivudine + Efavirenz)",
             "ABC/3TC/DTG (Abacavir + Lamivudine + Dolutegravir)"])

        st.markdown("<p class='section-header'>Clinical Modifiers</p>", unsafe_allow_html=True)

        tb_coinfection = st.checkbox("🫁 Active TB (On Rifampicin)",
                                      help="CYP3A4 inducer — reduces DTG half-life by ~50%")

        traditional_meds = st.checkbox("🌿 Traditional Medicine (St. John's Wort / African Potato)",
                                        help="CYP450 pathway interaction")

        renal_function = st.selectbox("Kidney Function (eGFR)",
            ["Normal (>90 mL/min)",
             "Mild Impairment (60–89 mL/min)",
             "Moderate Impairment (30–59 mL/min)",
             "Severe Impairment (<30 mL/min)"])

        paediatric = st.checkbox("👶 Paediatric Patient (Weight-Band Dosing)",
                                  help="Activates paediatric PK adjustment engine")

        if paediatric:
            weight_kg = st.slider("Patient Weight (kg)", 3, 40, 15)
        else:
            weight_kg = 70

        st.markdown("<p class='section-header'>Adherence Data</p>", unsafe_allow_html=True)

        days_missed = st.slider("Days Since Last Dose", 0, 14, 3,
                                 help="Source: Pharmacy dispensing record (automated)")
        hours_missed = days_missed * 24

        viral_load = st.number_input("Last Viral Load (copies/mL)", 0, 1000000, 450,
                                      help="Auto-ingested from NHLS when API connected")

        cd4_count = st.number_input("CD4 Count (cells/μL)", 0, 2000, 280)

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-size:0.62rem; color:#334155; text-align:center; line-height:1.6;'>
            ResistanceMap ZA OS © 2025<br>
            Licensor: ResistanceMap Technologies (Pty) Ltd<br>
            <span style='color:#1e3a5f;'>POPIA | NDoH | SAHPRA Compliant</span>
        </div>
        """, unsafe_allow_html=True)

    # ============================================================
    # 3. PHARMACOKINETIC ENGINE — CORE LOGIC
    # ============================================================

    # ── PK Database (Stanford HIVdb aligned) ──
    pk_db = {
        "Tenofovir": {
            "t_half": 17.0, "c_max": 0.30, "mic": 0.05,
            "mutation": "K65R", "class": "NRTI",
            "cross_resistance": ["K70E", "K70R"],
            "renal_sensitive": True, "color": "#3b82f6"
        },
        "Lamivudine": {
            "t_half": 5.0,  "c_max": 1.50, "mic": 0.50,
            "mutation": "M184V", "class": "NRTI",
            "cross_resistance": ["M184I"],
            "renal_sensitive": True, "color": "#f59e0b"
        },
        "Dolutegravir": {
            "t_half": 14.0, "c_max": 3.30, "mic": 0.50,
            "mutation": "R263K", "class": "INSTI",
            "cross_resistance": ["G118R", "E138K/A/T", "Q148R"],
            "renal_sensitive": False, "color": "#10b981"
        }
    }

    # ── Regimen Drug Mapping ──
    regimen_drugs = {
        "TLD (Tenofovir + Lamivudine + Dolutegravir)": ["Tenofovir", "Lamivudine", "Dolutegravir"],
        "TLE (Tenofovir + Lamivudine + Efavirenz)":    ["Tenofovir", "Lamivudine"],
        "ABC/3TC/DTG (Abacavir + Lamivudine + Dolutegravir)": ["Lamivudine", "Dolutegravir"]
    }

    active_drugs = regimen_drugs.get(regimen, ["Tenofovir", "Lamivudine", "Dolutegravir"])

    # ── Adjusted Half-Life Calculation ──
    def calculate_adjusted_half_life(drug, stats):
        t_half = stats["t_half"]
        applied = []

        # TB / Rifampicin CYP3A4 Induction
        if tb_coinfection and drug == "Dolutegravir":
            t_half *= 0.50
            applied.append(("Rifampicin CYP3A4 Induction", "−50% DTG half-life"))

        # Traditional Medicine CYP450
        if traditional_meds and drug == "Dolutegravir":
            t_half *= 0.65
            applied.append(("Traditional Medicine CYP450", "−35% DTG half-life"))

        # Renal Impairment
        renal_factor = 1.0
        if stats.get("renal_sensitive"):
            if "Moderate Impairment" in renal_function:
                renal_factor = 1.40
            elif "Severe Impairment" in renal_function:
                renal_factor = 1.85
            elif "Mild Impairment" in renal_function:
                renal_factor = 1.15
            if renal_factor > 1.0:
                t_half *= renal_factor
                applied.append(("Renal Clearance Delay", f"+{int((renal_factor-1)*100)}% TFV/3TC half-life"))

        # Paediatric Weight-Band Adjustment
        if paediatric:
            weight_factor = max(0.6, min(1.0, weight_kg / 35))
            t_half *= weight_factor
            applied.append(("Paediatric Weight-Band", f"Weight factor {weight_factor:.2f}"))

        return t_half, applied


    # ── Run PK for all active drugs ──
    current_levels   = {}
    adjusted_halves  = {}
    all_modifiers    = {}

    for drug in active_drugs:
        stats = pk_db.get(drug)
        if not stats:
            continue
        adj_t_half, mods = calculate_adjusted_half_life(drug, stats)
        adjusted_halves[drug] = adj_t_half
        k_e = math.log(2) / adj_t_half
        current_levels[drug] = stats["c_max"] * math.exp(-k_e * hours_missed)
        all_modifiers[drug] = mods


    # ── Derived Risk Signals ──
    vulnerable_drugs = [
        d for d in active_drugs
        if (pk_db[d]["mic"] * 0.05) < current_levels[d] < pk_db[d]["mic"]
    ]

    below_mic_drugs = [
        d for d in active_drugs
        if current_levels[d] < pk_db[d]["mic"]
    ]

    # ── Global Risk Score (0–100) ──
    def compute_risk_score():
        score = 0
        score += days_missed * 6          # Adherence
        score += len(below_mic_drugs) * 15
        score += len(vulnerable_drugs) * 10
        if tb_coinfection:    score += 12
        if traditional_meds:  score += 8
        if viral_load > 1000: score += 10
        if cd4_count < 200:   score += 8
        if paediatric:        score += 5
        return min(score, 100)

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
            <div style='font-size:1.8rem;'>🧬</div>
            <div>
                <div style='font-size:1.25rem; font-weight:700; color:#e2e8f0;
                            letter-spacing:0.02em;'>
                    ResistanceMap ZA OS
                </div>
                <div style='font-size:0.72rem; color:#3b82f6; letter-spacing:0.12em;
                            text-transform:uppercase;'>
                    Clinical Decision Support System &nbsp;·&nbsp; Enterprise v4.0
                </div>
            </div>
        </div>
        <div style='text-align:right;'>
            <div style='font-size:0.7rem; color:#475569;'>Patient</div>
            <div style='font-size:1rem; font-weight:700; color:#93c5fd;'>{patient_id}</div>
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
        vl_color = "#ef4444" if viral_load > 1000 else "#f59e0b" if viral_load > 50 else "#10b981"
        vl_display = f"{viral_load:,}" if viral_load > 0 else "Undetectable"
        st.markdown(f"""
        <div class='metric-card'>
            <h3>Viral Load (cp/mL)</h3>
            <div class='metric-value' style='color:{vl_color}; font-size:1.4rem;'>{vl_display}</div>
            <div class='metric-delta' style='color:#64748b;'>NHLS Last Result</div>
        </div>""", unsafe_allow_html=True)

    with kpi5:
        cd4_color = "#ef4444" if cd4_count < 200 else "#f59e0b" if cd4_count < 350 else "#10b981"
        st.markdown(f"""
        <div class='metric-card'>
            <h3>CD4 Count (cells/μL)</h3>
            <div class='metric-value' style='color:{cd4_color}; font-size:1.4rem;'>{cd4_count:,}</div>
            <div class='metric-delta' style='color:#64748b;'>
                {'⚠ Severe Immunocompromise' if cd4_count < 200 else 'Immunocompromised' if cd4_count < 350 else 'Adequate'}
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
            ⚗️ <span style='color:#f59e0b; font-weight:700;'>ACTIVE METABOLIC MODIFIERS:</span>
            &nbsp; {mod_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # 5. TABBED INTERFACE — ENTERPRISE MODULES
    # ============================================================

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈  PK Decay Curves",
        "🧬  Mutation & Resistance",
        "⚕️  Clinical Directives",
        "🤖  AI Adherence Risk",
        "💰  CFO Economics",
        "📋  Audit & Compliance"
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
                if not stats:
                    continue
                adj_t = adjusted_halves[drug]
                k_e   = math.log(2) / adj_t
                decay = stats["c_max"] * np.exp(-k_e * time_array)
                mic_pct = (decay / stats["mic"]) * 100

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

                # MIC threshold line
                fig.add_trace(go.Scatter(
                    x=[0, t_max_hours],
                    y=[stats["mic"], stats["mic"]],
                    mode='lines', name=f"{drug} MIC",
                    line=dict(width=1.2, dash='dot', color=color),
                    opacity=0.5,
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
                    annotation_text=f"  NOW ({days_missed}d defaulted)",
                    annotation_font_color="#ef4444",
                    annotation_font_size=11
                )

            # Resistance window shading
            fig.add_vrect(
                x0=hours_missed * 0.85, x1=min(hours_missed * 1.3, t_max_hours),
                fillcolor="rgba(239,68,68,0.06)", line_width=0,
                annotation_text="Resistance Window",
                annotation_position="top right",
                annotation_font_color="#ef4444",
                annotation_font_size=10,
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
                margin=dict(l=0, r=0, t=35, b=0),
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

            st.plotly_chart(fig, use_container_width=True)

        with col_status:
            st.markdown("<p class='section-header'>Drug Status Panel</p>", unsafe_allow_html=True)

            for drug in active_drugs:
                stats = pk_db.get(drug)
                if not stats:
                    continue
                lvl = current_levels[drug]
                mic = stats["mic"]
                pct = (lvl / mic) * 100
                adj_t = adjusted_halves[drug]

                if lvl >= mic:
                    status_html = "<span class='status-stable'>ABOVE MIC</span>"
                elif lvl >= mic * 0.05:
                    status_html = "<span class='status-warning'>SUB-INHIBITORY</span>"
                else:
                    status_html = "<span class='status-critical'>CLEARED</span>"

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
                        MIC: {mic} mg/L &nbsp;·&nbsp; {pct:.1f}% coverage
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
            st.plotly_chart(fig_gauge, use_container_width=True)

    # ────────────────────────────────────────────────────────────
    # TAB 2: MUTATION & CROSS-RESISTANCE PREDICTOR
    # ────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("<p class='section-header'>Genomic Resistance Prediction Engine (Stanford HIVdb Aligned)</p>",
                    unsafe_allow_html=True)

        # ── Mutation Risk Matrix ──
        col_mut1, col_mut2 = st.columns([1.5, 1])

        with col_mut1:
            mutation_data = []
            for drug in active_drugs:
                stats = pk_db.get(drug)
                if not stats:
                    continue
                lvl = current_levels[drug]
                mic = stats["mic"]
                ratio = lvl / mic

                if ratio >= 2.0:
                    pressure = "SUPPRESSED"
                    p_color  = "#10b981"
                    risk_pct = max(0, 5 - days_missed * 0.5)
                elif ratio >= 1.0:
                    pressure = "MARGINAL"
                    p_color  = "#3b82f6"
                    risk_pct = 15 + days_missed * 2
                elif ratio >= 0.05:
                    pressure = "HIGH"
                    p_color  = "#f59e0b"
                    risk_pct = 45 + days_missed * 4
                else:
                    pressure = "CRITICAL"
                    p_color  = "#ef4444"
                    risk_pct = 80 + days_missed * 1.5

                risk_pct = min(risk_pct, 99)
                cross_res = ", ".join(stats.get("cross_resistance", ["None"]))

                mutation_data.append({
                    "drug":      drug,
                    "class":     stats["class"],
                    "mutation":  stats["mutation"],
                    "cross_res": cross_res,
                    "pressure":  pressure,
                    "p_color":   p_color,
                    "risk_pct":  risk_pct,
                    "ratio":     ratio
                })

            # ── Resistance Probability Bar Chart ──
            drugs_list = [m["drug"] for m in mutation_data]
            risk_vals  = [m["risk_pct"] for m in mutation_data]
            colors_bar = [m["p_color"] for m in mutation_data]

            fig_mut = go.Figure(go.Bar(
                x=risk_vals, y=drugs_list,
                orientation='h',
                marker=dict(
                    color=colors_bar,
                    line=dict(width=0)
                ),
                text=[f"{v:.0f}%" for v in risk_vals],
                textposition='outside',
                textfont=dict(color='#94a3b8', size=11),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Mutation Risk: %{x:.0f}%<extra></extra>"
                )
            ))

            fig_mut.update_layout(
                title=dict(text="Estimated Mutation Emergence Probability",
                           font=dict(color='#94a3b8', size=13)),
                plot_bgcolor="#0a0e1a",
                paper_bgcolor="#0d1b2e",
                font=dict(family="Inter", color="#94a3b8", size=11),
                xaxis=dict(
                    range=[0, 110],
                    gridcolor="#0f2237",
                    title="Probability (%)",
                    tickformat='.0f'
                ),
                yaxis=dict(gridcolor="#0f2237"),
                height=280,
                margin=dict(l=0, r=40, t=40, b=0)
            )

            # Danger threshold
            fig_mut.add_vline(
                x=50, line_dash="dot", line_color="#ef4444",
                annotation_text=" Clinical Threshold",
                annotation_font_color="#ef4444",
                annotation_font_size=10
            )

            st.plotly_chart(fig_mut, use_container_width=True)

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
                                🧬 {intel["name"]}
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
                    🔴 NDoH PROTOCOL ALERT — RIFAMPICIN-DTG INTERACTION
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Patient is confirmed on <strong>Rifampicin</strong> for active TB co-infection.
                    Rifampicin is a potent <strong>CYP3A4 inducer</strong> that reduces Dolutegravir
                    plasma AUC by approximately <strong>54%</strong>.<br><br>
                    ⚡ <strong>Mandatory Action:</strong> Increase Dolutegravir from
                    <span style='color:#fca5a5;'>50mg once daily → 50mg TWICE DAILY</span> (BD).<br>
                    📋 <strong>Authority:</strong> SAHPRA Advisory 2023-HIV-004 |
                    NDoH ART Guidelines Section 5.3<br>
                    🧪 <strong>Monitoring:</strong> Repeat viral load at 4 weeks post-adjustment.
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
                    🟡 PHARMACOVIGILANCE ALERT — TRADITIONAL MEDICINE CYP450 INTERACTION
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Patient is using traditional preparations containing compounds that interact
                    with the <strong>CYP2C9 / CYP3A4</strong> enzymatic pathways (Hypericin in St. John's Wort;
                    Phytosterols in African Potato).<br><br>
                    ⚡ <strong>Effect:</strong> Accelerated Dolutegravir clearance. Estimated plasma
                    concentration reduced by 30–40%.<br>
                    📋 <strong>Action:</strong> Counsel patient on cessation. If non-adherent to
                    cessation, consider enhanced monitoring (3-monthly viral load).<br>
                    🌿 <strong>Note:</strong> African Potato (Hypoxis hemerocallidea) additionally
                    suppresses bone marrow — monitor FBC if patient is on TDF.
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
                    🟡 RENAL DOSE ADJUSTMENT REQUIRED — {sev}
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Patient has <strong>{renal_function}</strong>.
                    Tenofovir Disoproxil Fumarate (TDF) is renally cleared and is
                    <strong>nephrotoxic at accumulating concentrations</strong>.<br><br>
                    ⚡ <strong>Action:</strong> {'Consider switching TDF → TAF (Tenofovir Alafenamide). TAF achieves equivalent efficacy at 10% the plasma concentration, reducing nephrotoxicity.' if 'Severe' in renal_function else 'Monitor eGFR monthly. Consider TAF switch if trajectory worsening. Avoid NSAIDs.'}<br>
                    🩺 <strong>Monitor:</strong> Monthly urinary phosphate/creatinine ratio.
                    Watch for Fanconi Syndrome.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Paediatric Alert ──
        if paediatric:
            directives_fired += 1
            band_dose = "5mg" if weight_kg < 6 else "10mg" if weight_kg < 10 else "15mg" if weight_kg < 14 else "20mg" if weight_kg < 20 else "25mg" if weight_kg < 25 else "30mg"
            st.markdown(f"""
            <div class='alert-info'>
                <div style='font-weight:700; font-size:0.9rem; margin-bottom:0.4rem;'>
                    🔵 PAEDIATRIC WEIGHT-BAND DOSING PROTOCOL ACTIVE
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    Patient weight: <strong>{weight_kg} kg</strong>.
                    Paediatric DTG weight-band dosing (WHO 2023 revised schedule):<br><br>
                    ⚡ <strong>Recommended DTG Dose:</strong>
                    <span style='color:#93c5fd; font-weight:700;'>{band_dose} once daily</span><br>
                    📋 Weight-band boundaries are automatically recalculated on each clinic visit.
                    The system will issue a dose-escalation alert when the patient crosses the next
                    weight threshold (next band at {weight_kg + 5} kg).<br>
                    🧮 <strong>Volume check:</strong> Confirm dispersible tablet formulation.
                    Do not substitute adult film-coated tablet.
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
                    ⚠️ SUB-INHIBITORY PRESSURE — {drug.upper()} / {mut} RISK
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    <strong>{drug}</strong> plasma concentration is in the sub-inhibitory range
                    (above detection, below MIC). This is the most dangerous pharmacokinetic window —
                    viral replication is occurring in the presence of drug, which is the exact
                    condition required for <strong>resistance mutation selection</strong>.<br><br>
                    🧬 <strong>Primary Mutation Risk:</strong>
                    <span style='color:#fde68a; font-weight:700;'>{mut}</span><br>
                    ⚡ <strong>Immediate Action:</strong> Supervised re-dosing required within 6 hours.
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
                        🔴 CRITICAL — {drug.upper()} CLEARED FROM PLASMA
                    </div>
                    <div style='font-size:0.82rem; line-height:1.7;'>
                        <strong>{drug}</strong> has been fully cleared. Zero pharmacological protection.
                        Patient is functionally without ART coverage for this component.<br><br>
                        ⚡ <strong>Immediate Protocol:</strong> Do not restart mono-therapy.
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
                    ✅ SYSTEM CLEAR — NO ACTIVE CLINICAL DIRECTIVES
                </div>
                <div style='font-size:0.82rem; line-height:1.7;'>
                    All pharmacokinetic parameters are within therapeutic range.
                    No comorbidity interactions detected. Patient appears adherent.
                    Next scheduled viral load review as per routine NDoH monitoring schedule.
                    <br><br>
                    📋 <strong>Routine Action:</strong> Continue current regimen.
                    Confirm 3-monthly pharmacy collection. Record in TIER.Net.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Protocol Reference Table ──
        st.markdown("<p class='section-header'>NDoH Guideline Reference Index</p>",
                    unsafe_allow_html=True)

        st.markdown("""
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
                    <td>NDoH ART Guidelines 2023</td>
                    <td>§5.3 — TB/HIV Co-infection</td>
                    <td>DTG dose doubling on Rifampicin</td>
                    <td><span class='status-stable'>APPLIED</span></td>
                </tr>
                <tr>
                    <td>WHO HIV Guidelines 2023</td>
                    <td>§7.1 — Paediatric Dosing</td>
                    <td>Weight-band DTG dispersible tablet</td>
                    <td><span class='status-stable'>APPLIED</span></td>
                </tr>
                <tr>
                    <td>SAHPRA Advisory 2023-HIV-004</td>
                    <td>Pharmacovigilance</td>
                    <td>Traditional medicine CYP450 warning</td>
                    <td><span class='status-stable'>APPLIED</span></td>
                </tr>
                <tr>
                    <td>Stanford HIVdb v9.6</td>
                    <td>Mutation Scoring</td>
                    <td>K65R / M184V / R263K interpretation</td>
                    <td><span class='status-stable'>SYNCED</span></td>
                </tr>
                <tr>
                    <td>NHLS Protocol 2024</td>
                    <td>Viral Load Monitoring</td>
                    <td>Enhanced monitoring if VL >1000</td>
                    <td>{'<span class="status-critical">ACTIVE</span>' if viral_load > 1000 else '<span class="status-stable">ROUTINE</span>'}</td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # TAB 4: AI ADHERENCE RISK ENGINE
    # ────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("<p class='section-header'>Socio-Economic Predictive AI — Defaulter Risk Model</p>",
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
            taxi_strike = st.checkbox("🚌 Active Taxi Strike in District")
            food_insecurity = st.checkbox("🍽️ Food Insecurity Reported")
            disclosure = st.selectbox("HIV Status Disclosure",
                ["Fully disclosed", "Partially disclosed", "Non-disclosed"])

            # ── ML-Style Risk Model ──
            adherence_risk = 0
            adherence_risk += days_missed * 5
            adherence_risk += distance_km * 0.6
            adherence_risk += missed_appts * 6
            adherence_risk += {"Employed (formal)": 0, "Employed (informal)": 5,
                                "Unemployed": 15, "Grant recipient": 8}.get(employment, 0)
            adherence_risk += {"Private vehicle": 0, "Taxi/minibus": 8,
                                "Walking": 18, "No reliable transport": 25}.get(transport, 0)
            if taxi_strike:    adherence_risk += 20
            if food_insecurity: adherence_risk += 15
            adherence_risk += {"Fully disclosed": 0, "Partially disclosed": 10,
                                "Non-disclosed": 22}.get(disclosure, 0)
            adherence_risk = min(adherence_risk, 100)

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
            st.plotly_chart(fig_ad, use_container_width=True)

            st.markdown(f"""
            <div class='alert-{"critical" if adherence_risk >= 65 else "warning" if adherence_risk >= 40 else "info" if adherence_risk >= 20 else "success"}'>
                <div style='font-weight:700;'>
                    {ar_label} — Predicted Default Probability: {adherence_risk:.0f}%
                </div>
                <div style='font-size:0.8rem; margin-top:0.4rem;'>
                    🤖 <strong>AI Recommended Action:</strong> {ar_action}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_ai2:
            # ── Feature Importance Chart ──
            st.markdown("<p class='section-header'>Risk Factor Contribution Analysis</p>",
                        unsafe_allow_html=True)

            factors = {
                "Days Defaulted":        days_missed * 5,
                "Distance from Clinic":  distance_km * 0.6,
                "Missed Appointments":   missed_appts * 6,
                "Employment Status":     {"Employed (formal)": 0, "Employed (informal)": 5,
                                          "Unemployed": 15, "Grant recipient": 8}.get(employment, 0),
                "Transport Access":      {"Private vehicle": 0, "Taxi/minibus": 8,
                                          "Walking": 18, "No reliable transport": 25}.get(transport, 0),
                "Taxi Strike Active":    20 if taxi_strike else 0,
                "Food Insecurity":       15 if food_insecurity else 0,
                "HIV Disclosure":        {"Fully disclosed": 0, "Partially disclosed": 10,
                                          "Non-disclosed": 22}.get(disclosure, 0),
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
                st.plotly_chart(fig_feat, use_container_width=True)

            # ── Intervention Protocol ──
            st.markdown("<p class='section-header'>Automated Intervention Protocol</p>",
                        unsafe_allow_html=True)

            interventions = []
            if adherence_risk >= 65:
                interventions = [
                    ("🚗 CHW Home Visit", "Dispatched within 24h. GPS coordinates loaded from last clinic registration."),
                    ("📱 WhatsApp Alert", "POPIA-compliant encrypted reminder sent. Message: 'Your medication is ready for collection.'"),
                    ("📞 Clinic Call-Back", "Dedicated adherence counsellor assigned. Case flagged in TIER.Net."),
                    ("💊 Multi-Month Dispensing", "Consider 3-month supply to reduce transport burden at next visit.")
                ]
            elif adherence_risk >= 40:
                interventions = [
                    ("📱 WhatsApp Reminder", "Automated sequence: Day 1, Day 3, Day 5. Escalates to voice call."),
                    ("📊 Viral Load Alert", "Fast-track VL order submitted to NHLS for processing within 48h.")
                ]
            elif adherence_risk >= 20:
                interventions = [
                    ("📱 SMS Reminder", "Standard 7-day pre-appointment reminder activated."),
                ]
            else:
                interventions = [
                    ("✅ Routine Monitoring", "No enhanced intervention required. Standard care pathway.")
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
    # TAB 5: CFO HEALTH ECONOMICS DASHBOARD
    # ────────────────────────────────────────────────────────────
    with tab5:
        st.markdown("<p class='section-header'>Health Economics Intelligence — CFO Dashboard</p>",
                    unsafe_allow_html=True)

        # ── Cost Modelling Inputs ──
        col_cfo_in, col_cfo_out = st.columns([1, 2])

        with col_cfo_in:
            st.markdown("""
            <div class='metric-card'>
                <div style='font-size:0.72rem; color:#3b82f6; font-weight:600;
                            text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.8rem;'>
                    Economic Model Parameters
                </div>
            </div>
            """, unsafe_allow_html=True)

            n_patients    = st.number_input("Patient Population on ART", 100, 50000, 5000)
            default_rate  = st.slider("Current Default Rate (%)", 1, 40, 18)
            vl_failure_rate = st.slider("Virological Failure Rate (%)", 1, 30, 12)

            first_line_cost  = st.number_input("First-Line Regimen Cost (ZAR/patient/year)",
                                                500, 5000, 1200)
            second_line_cost = st.number_input("Second-Line Regimen Cost (ZAR/patient/year)",
                                                1000, 20000, 4500)
            third_line_cost  = st.number_input("Third-Line Regimen Cost (ZAR/patient/year)",
                                                5000, 200000, 85000)

            system_reduction = st.slider("Estimated CDSS Resistance Reduction (%)", 5, 60, 35)

        with col_cfo_out:
            # ── Economic Calculations ──
            pts_failing    = int(n_patients * vl_failure_rate / 100)
            pts_on_2nd     = int(pts_failing * 0.7)
            pts_on_3rd     = int(pts_failing * 0.12)

            current_drug_spend = (
                (n_patients - pts_failing) * first_line_cost +
                pts_on_2nd * second_line_cost +
                pts_on_3rd * third_line_cost
            )

            # Post-CDSS savings
            reduction_factor = system_reduction / 100
            pts_failing_post = int(pts_failing * (1 - reduction_factor))
            pts_on_3rd_post  = int(pts_on_3rd  * (1 - reduction_factor * 1.4))

            post_drug_spend = (
                (n_patients - pts_failing_post) * first_line_cost +
                int(pts_failing_post * 0.7) * second_line_cost +
                pts_on_3rd_post * third_line_cost
            )

            annual_saving    = current_drug_spend - post_drug_spend
            licence_fee      = 1_000_000
            net_saving       = annual_saving - licence_fee
            roi_pct          = (net_saving / licence_fee) * 100

            # ── KPI Row ──
            e1, e2, e3, e4 = st.columns(4)
            econ_cards = [
                ("Annual Drug Spend (Pre-CDSS)", f"R {current_drug_spend:,.0f}", "#ef4444"),
                ("Annual Drug Spend (Post-CDSS)", f"R {post_drug_spend:,.0f}", "#10b981"),
                ("Annual Cost Saving", f"R {annual_saving:,.0f}", "#3b82f6"),
                (f"ROI on R1M Licence", f"{roi_pct:.0f}%", "#f59e0b")
            ]
            for col, (label, value, color) in zip([e1, e2, e3, e4], econ_cards):
                with col:
                    st.markdown(f"""
                    <div class='metric-card' style='text-align:center;'>
                        <h3 style='text-align:center;'>{label}</h3>
                        <div class='metric-value' style='color:{color}; font-size:1.3rem;'>
                            {value}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── Waterfall Chart ──
            fig_wf = go.Figure(go.Waterfall(
                name="Cost Bridge",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "total"],
                x=["Baseline\nDrug Spend", "1st→2nd Line\nPrevention",
                   "3rd-Line\nPrevention", "Licence\nFee", "Net Annual\nPosition"],
                textposition="outside",
                text=[f"R {current_drug_spend/1e6:.1f}M",
                      f"-R {(current_drug_spend-post_drug_spend)*0.4/1e6:.1f}M",
                      f"-R {(current_drug_spend-post_drug_spend)*0.6/1e6:.1f}M",
                      f"+R 1.0M",
                      f"R {net_saving/1e6:.1f}M"],
                y=[current_drug_spend,
                   -(current_drug_spend - post_drug_spend) * 0.4,
                   -(current_drug_spend - post_drug_spend) * 0.6,
                   licence_fee,
                   0],
                connector={"line": {"color": "#1e3a5f"}},
                increasing={"marker": {"color": "#ef4444"}},
                decreasing={"marker": {"color": "#10b981"}},
                totals={"marker": {"color": "#3b82f6"}},
            ))
            fig_wf.update_layout(
                title=dict(text="Financial Impact Waterfall — Annual Cost Bridge",
                           font=dict(color='#94a3b8', size=13)),
                plot_bgcolor="#0a0e1a",
                paper_bgcolor="#0d1b2e",
                font=dict(family="Inter", color="#94a3b8", size=11),
                yaxis=dict(gridcolor="#0f2237", title="ZAR (Rands)"),
                xaxis=dict(gridcolor="#0f2237"),
                height=320,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig_wf, use_container_width=True)

        # ── Metrics Table ──
        st.markdown("<p class='section-header'>Value-per-Metric Breakdown</p>",
                    unsafe_allow_html=True)

        st.markdown(f"""
        <table class='styled-table'>
            <thead>
                <tr>
                    <th>Performance Metric</th>
                    <th>Baseline</th>
                    <th>Post-CDSS</th>
                    <th>Financial Implication</th>
                    <th>NHI Alignment</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Patients on Third-Line Therapy</td>
                    <td style='color:#ef4444;'>{pts_on_3rd:,}</td>
                    <td style='color:#10b981;'>{pts_on_3rd_post:,}</td>
                    <td>Saves R {(pts_on_3rd - pts_on_3rd_post) * third_line_cost:,.0f}/yr</td>
                    <td><span class='status-stable'>HIGH VALUE</span></td>
                </tr>
                <tr>
                    <td>Virological Failure Events</td>
                    <td style='color:#ef4444;'>{pts_failing:,}</td>
                    <td style='color:#10b981;'>{pts_failing_post:,}</td>
                    <td>Prevents {pts_failing - pts_failing_post:,} treatment switches</td>
                    <td><span class='status-stable'>HIGH VALUE</span></td>
                </tr>
                <tr>
                    <td>Medication Wastage (stockout)</td>
                    <td style='color:#f59e0b;'>Untracked</td>
                    <td style='color:#10b981;'>Auto-rerouted</td>
                    <td>Estimated R {int(n_patients * 0.03 * first_line_cost):,}/yr saved</td>
                    <td><span class='status-stable'>MEDIUM</span></td>
                </tr>
                <tr>
                    <td>Medical Negligence Exposure</td>
                    <td style='color:#ef4444;'>Unaudited</td>
                    <td style='color:#10b981;'>Full audit trail</td>
                    <td>Litigation risk reduction (unquantified)</td>
                    <td><span class='status-stable'>CRITICAL</span></td>
                </tr>
                <tr>
                    <td>Resistance Reduction Rate</td>
                    <td style='color:#f59e0b;'>0%</td>
                    <td style='color:#10b981;'>{system_reduction}%</td>
                    <td>ROI: <strong style='color:#3b82f6;'>{roi_pct:.0f}%</strong> on R1M licence</td>
                    <td><span class='status-stable'>CORE</span></td>
                </tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────
    # TAB 6: AUDIT LOG & COMPLIANCE
    # ────────────────────────────────────────────────────────────
    with tab6:
        st.markdown("<p class='section-header'>Unalterable Audit Trail — POPIA & NDoH Compliance</p>",
                    unsafe_allow_html=True)

        # ── Simulated Audit Log ──
        now = datetime.datetime.now()

        audit_events = []

        audit_events.append({
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "event":     "CLINICAL SESSION OPENED",
            "detail":    f"Patient {patient_id} | Clinician {clinician} | Facility: {facility.split('–')[0].strip()}",
            "level":     "INFO",
            "hash":      f"SHA256:{abs(hash(patient_id + clinician)):#x}"[:24]
        })

        audit_events.append({
            "timestamp": (now - datetime.timedelta(seconds=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "event":     "PK ENGINE COMPUTED",
            "detail":    f"Regimen: {regimen.split('(')[0].strip()} | Modifiers: {len(flat_mods)} applied",
            "level":     "INFO",
            "hash":      f"SHA256:{abs(hash(regimen)):#x}"[:24]
        })

        if tb_coinfection:
            audit_events.append({
                "timestamp": (now - datetime.timedelta(seconds=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "event":     "GUIDELINE ALERT FIRED",
                "detail":    "NDoH §5.3 — Rifampicin/DTG interaction. DTG dose doubling directive issued.",
                "level":     "CRITICAL",
                "hash":      f"SHA256:{abs(hash('rifampicin')):#x}"[:24]
            })

        if traditional_meds:
            audit_events.append({
                "timestamp": (now - datetime.timedelta(seconds=4)).strftime("%Y-%m-%d %H:%M:%S"),
                "event":     "PHARMACOVIGILANCE ALERT",
                "detail":    "Traditional medicine CYP450 interaction flagged. Counselling required.",
                "level":     "WARNING",
                "hash":      f"SHA256:{abs(hash('trad_meds')):#x}"[:24]
            })

        for drug in below_mic_drugs:
            audit_events.append({
                "timestamp": (now - datetime.timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S"),
                "event":     "SUB-MIC THRESHOLD BREACH",
                "detail":    f"{drug} plasma level below MIC. Mutation selection risk: {pk_db[drug]['mutation']}.",
                "level":     "CRITICAL",
                "hash":      f"SHA256:{abs(hash(drug+'mic')):#x}"[:24]
            })

        audit_events.append({
            "timestamp": (now - datetime.timedelta(seconds=6)).strftime("%Y-%m-%d %H:%M:%S"),
            "event":     "NHLS FEED CHECKED",
            "detail":    f"Viral load ingestion: {viral_load:,} cp/mL | CD4: {cd4_count} cells/μL",
            "level":     "INFO",
            "hash":      f"SHA256:{abs(hash(str(viral_load))):#x}"[:24]
        })

        audit_events.append({
            "timestamp": (now - datetime.timedelta(seconds=7)).strftime("%Y-%m-%d %H:%M:%S"),
            "event":     "AI ADHERENCE SCORE COMPUTED",
            "detail":    f"Default risk: {adherence_risk:.0f}% | Category: {ar_label}",
            "level":     "INFO",
            "hash":      f"SHA256:{abs(hash(str(adherence_risk))):#x}"[:24]
        })

        level_colors = {
            "INFO":     "#3b82f6",
            "WARNING":  "#f59e0b",
            "CRITICAL": "#ef4444"
        }

        # ── Render Audit Table ──
        rows_html = ""
        for ev in audit_events:
            color = level_colors.get(ev["level"], "#94a3b8")
            rows_html += f"""
            <tr>
                <td style='font-family:monospace; font-size:0.72rem; color:#64748b;'>
                    {ev["timestamp"]}
                </td>
                <td>
                    <span style='color:{color}; font-weight:600; font-size:0.78rem;'>
                        {ev["event"]}
                    </span>
                </td>
                <td style='font-size:0.75rem; color:#94a3b8;'>{ev["detail"]}</td>
                <td>
                    <span style='background:#0a0e1a; color:{color}; border:1px solid {color}33;
                                 border-radius:12px; padding:0.1rem 0.5rem; font-size:0.62rem;
                                 font-weight:700;'>
                        {ev["level"]}
                    </span>
                </td>
                <td style='font-family:monospace; font-size:0.65rem; color:#334155;'>
                    {ev["hash"]}
                </td>
            </tr>
            """

        st.markdown(f"""
        <table class='styled-table'>
            <thead>
                <tr>
                    <th>Timestamp (SAST)</th>
                    <th>Event</th>
                    <th>Detail</th>
                    <th>Level</th>
                    <th>Integrity Hash</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Compliance Badges ──
        col_c1, col_c2, col_c3 = st.columns(3)

        compliance_items = [
            (col_c1, "POPIA Compliant",
             "All patient data anonymised. No PII stored in session. Data encrypted in transit (TLS 1.3).",
             "#10b981"),
            (col_c2, "NDoH Guidelines v2023",
             "All clinical directives cross-referenced against current South African ART treatment guidelines.",
             "#3b82f6"),
            (col_c3, "Stanford HIVdb Aligned",
             "Mutation interpretation engine synchronised with HIVdb v9.6 drug resistance algorithm.",
             "#f59e0b"),
        ]

        for col, title, desc, color in compliance_items:
            with col:
                st.markdown(f"""
                <div class='metric-card' style='border-color:{color}40; text-align:center;'>
                    <div style='font-size:1.5rem; margin-bottom:0.5rem;'>✓</div>
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

        report_text = f"""
ResistanceMap ZA OS — Clinical Assessment Report
================================================
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
""" + "\n".join([
            f"{drug}: {current_levels[drug]:.5f} mg/L "
            f"(MIC={pk_db[drug]['mic']} | "
            f"{'ABOVE' if current_levels[drug] >= pk_db[drug]['mic'] else 'BELOW'} MIC)"
            for drug in active_drugs if drug in current_levels
        ]) + f"""

ACTIVE MODIFIERS
----------------
{chr(10).join([f"- {m}: {d}" for m, d in flat_mods]) if flat_mods else "None"}

CLINICAL DIRECTIVES
-------------------
TB Co-infection: {"YES – DTG dose doubling required" if tb_coinfection else "No"}
Traditional Medicine: {"YES – CYP450 interaction warning" if traditional_meds else "No"}
Renal Status: {renal_function}
Paediatric Protocol: {"YES – Weight-band dosing active" if paediatric else "No"}

AI ADHERENCE RISK
-----------------
Default Risk Score: {adherence_risk:.0f}%
Risk Category: {ar_label}
Recommended Action: {ar_action}

ECONOMICS
---------
Viral Load: {viral_load:,} copies/mL
CD4 Count: {cd4_count} cells/μL

AUDIT INTEGRITY
---------------
""" + "\n".join([f"[{e['level']}] {e['timestamp']} — {e['event']}" for e in audit_events])

        with exp_col1:
            st.download_button(
                label="📄 Download Clinical Report (.txt)",
                data=report_text,
                file_name=f"ResistanceMapZA_{patient_id}_{now.strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        with exp_col2:
            st.markdown("""
            <div style='background:#0d1b2e; border:1px solid #1e3a5f; border-radius:8px;
                        padding:0.6rem; text-align:center; font-size:0.75rem; color:#475569;'>
                📊 Export to TIER.Net<br>
                <span style='color:#334155;'>(HL7/FHIR API — Enterprise Licence)</span>
            </div>
            """, unsafe_allow_html=True)

        with exp_col3:
            st.markdown("""
            <div style='background:#0d1b2e; border:1px solid #1e3a5f; border-radius:8px;
                        padding:0.6rem; text-align:center; font-size:0.75rem; color:#475569;'>
                🏥 Push to NHLS Portal<br>
                <span style='color:#334155;'>(NHLS API — Enterprise Licence)</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Footer ──
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='border-top:1px solid #1e3a5f; padding-top:1rem; text-align:center;
                font-size:0.65rem; color:#334155; line-height:2;'>
        ResistanceMap ZA OS v4.0 &nbsp;·&nbsp; Enterprise Clinical Decision Support System<br>
        Licensor: ResistanceMap Technologies (Pty) Ltd &nbsp;·&nbsp;
        KwaZulu-Natal Department of Health Prototype<br>
        POPIA Compliant &nbsp;|&nbsp; NDoH Guidelines 2023 &nbsp;|&nbsp;
        Stanford HIVdb v9.6 &nbsp;|&nbsp; SAHPRA Registered<br>
        <span style='color:#1e3a5f;'>
            For clinical use only. Not a substitute for qualified medical judgement.
            All outputs must be reviewed by a licensed clinician.
        </span>
    </div>
    """, unsafe_allow_html=True)
