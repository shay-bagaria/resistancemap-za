"""Page configuration and global CSS theme. No clinical logic lives here."""

import streamlit as st


def configure_page():
    """st.set_page_config — must run before any other Streamlit call."""
    st.set_page_config(
        page_title="ResistanceMap ZA | CDSS",
        layout="wide",
        page_icon=":material/biotech:",
        initial_sidebar_state="expanded"
    )


def apply():
    """Inject the global CSS theme."""
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
