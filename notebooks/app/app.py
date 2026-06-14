import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------
# 1. PAGE CONFIGURATION & LAYOUT
# ----------------------------------------------------
st.set_page_config(
    page_title="ResistanceMap ZA",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 2. SIMULATED BASELINE SURVEILLANCE DATA & CORES
# ----------------------------------------------------
# Creating a baseline dataset for KZN sub-districts to ensure the dashboard renders immediately
@st.cache_data
def get_mock_kzn_data():
    sub_districts = [
        "eThekwini (Durban)", "uMkhanyakude (Hlabisa)", "King Cetshwayo", 
        "uGundlovu", "iLembe", "Amajuba", "Ugu", "Harry Gwala"
    ]
    data = {
        "Sub-District": sub_districts,
        "K103N_Frequency": [0.085, 0.112, 0.098, 0.074, 0.091, 0.065, 0.088, 0.079],
        "M184V_Frequency": [0.84, 0.89, 0.82, 0.80, 0.86, 0.78, 0.83, 0.81],
        "K65R_Frequency": [0.15, 0.18, 0.14, 0.11, 0.16, 0.10, 0.13, 0.12],
        "M41L_Frequency": [0.04, 0.06, 0.05, 0.03, 0.05, 0.02, 0.04, 0.03]
    }
    return pd.DataFrame(data)

kzn_df = get_mock_kzn_data()

# ----------------------------------------------------
# 3. SIDEBAR NAVIGATION SWITCH
# ----------------------------------------------------
st.sidebar.title("🧬 ResistanceMap ZA")
st.sidebar.markdown("---")
app_mode = st.sidebar.radio(
    "Navigation Menu:",
    ["About ResistanceMap ZA", "Interactive Surveillance Dashboard", "Technical Pipeline Specs"]
)
st.sidebar.markdown("---")
st.sidebar.info("Developed as a zero-cost public health utility to support clinical decision-making under the NHI framework.")

# ----------------------------------------------------
# PAGE 1: PLAIN-ENGLISH HOME PAGE FOR GENERAL PUBLIC
# ----------------------------------------------------
if app_mode == "About ResistanceMap ZA":
    st.title("🧬 ResistanceMap ZA")
    st.subheader("Tracking HIV-1 Drug Resistance to Protect Public Health in KwaZulu-Natal")
    
    st.markdown("---")
    
    # 3-Column Quick Metrics Layout
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Target Surveillance Region", value="KwaZulu-Natal (KZN)")
    with col2:
        st.metric(label="Primary System Goal", value="Therapeutic Protection")
    with col3:
        st.metric(label="System Operational Status", value="Active / Open Source")
        
    st.markdown("---")
    
    # Content Sections
    st.markdown("### 🔍 What is ResistanceMap ZA?")
    st.write(
        "ResistanceMap ZA is an open-source tracking system designed to monitor drug-resistant "
        "strains of HIV-1 across different sub-districts in KwaZulu-Natal. When people living "
        "with HIV miss treatment doses erratically, the virus can mutate and become resistant to "
        "standard, low-cost medications. This platform acts as an early-warning radar system, "
        "identifying where these drug-resistant mutation clusters are forming so health authorities "
        "can intervene before they spread."
    )
    
    st.markdown("### 💡 Why is this useful?")
    st.write(
        "South Africa is currently transitioning into a National Health Insurance (NHI) framework, "
        "which aims to provide equal medical care to everyone. However, drug resistance poses a major "
        "financial and clinical threat. If standard first-line treatments fail, patients must be moved "
        "to advanced medications that cost significantly more, draining public funds. By mapping out "
        "resistance risks in real time, our tool helps clinics allocate expensive diagnostic kits and "
        "specialized healthcare workers exactly where they are needed most, saving lives and protecting "
        "state healthcare budgets."
    )
    
    st.markdown("### 👥 Who is this platform for?")
    st.markdown(
        """
        * **Frontline Clinic Managers:** To see if their local community is experiencing an uptick in resistance pressure, allowing them to strengthen adherence support groups.
        * **Public Health Officials & NHI Planners:** To guide the distribution of high-genetic-barrier medications and diagnostic funding based on hard, localized data.
        * **Independent Researchers & Community Members:** To freely access open scientific data regarding the evolutionary patterns of the virus in South Africa.
        """
    )
    
    st.markdown("### 🛠️ How do you use this tool?")
    st.markdown(
        """
        1. **Explore the Map:** Click over to the **Interactive Surveillance Dashboard** using the menu on the left. This visualizes the regional risk tiers across KZN sub-districts.
        2. **Understand the Risk Tiers:** 
            * 🔴 **Critical Risk:** Highly elevated mutation frequencies paired with high-vulnerability drug regimes. Requires immediate clinical changes.
            * 🟠 **High Risk:** Shows early indicators of treatment failure. Demands targeted viral load checks.
            * 🟡 **Moderate Risk:** Indicates baseline resistance; handled with routine adherence tracking.
            * 🟢 **Low Risk:** Stable viral control and low mutation pressure.
        3. **Review the Data Core:** The **Technical Pipeline Specs** tab exposes the underlying biological sequence codes and scientific research papers backing the mathematical engine.
        """
    )

# ----------------------------------------------------
# PAGE 2: INTERACTIVE SURVEILLANCE DASHBOARD
# ----------------------------------------------------
elif app_mode == "Interactive Surveillance Dashboard":
    st.title("📊 Interactive Surveillance Dashboard")
    st.markdown("### Sub-District Mapping & Pharmacokinetic Vulnerability Engine")
    st.markdown("---")
    
    # User Input Selectors
    st.markdown("#### Step 1: Select Treatment Baseline Variables")
    layout_col1, layout_col2 = st.columns(2)
    
    with layout_col1:
        selected_regimen = st.selectbox(
            "Current Prescribed Regimen Profile:",
            ["Efavirenz (EFV) Baseline Monotherapy Tail", "Dolutegravir (DTG) Optimised High Barrier Layer"]
        )
    with layout_col2:
        selected_mutation = st.selectbox(
            "Target Mutation Strain to Filter:",
            ["K103N (NNRTI Resistance)", "M184V (3TC High-Frequency Failure)", "K65R (Tenofovir Breakdown)", "M41L (Historical TAM Profile)"]
        )
        
    # Map selection logic onto dataframe columns
    mut_col_map = {
        "K103N (NNRTI Resistance)": "K103N_Frequency",
        "M184V (3TC High-Frequency Failure)": "M184V_Frequency",
        "K65R (Tenofovir Breakdown)": "K65R_Frequency",
        "M41L (Historical TAM Profile)": "M41L_Frequency"
    }
    target_column = mut_col_map[selected_mutation]
    
    # Set dynamic Pharmacokinetic Vulnerability Score (PVS) based on choices
    if "Efavirenz" in selected_regimen:
        pvs_score = 0.93
        st.warning("⚠️ Warning: Efavirenz displays an asymmetric 8.1-day sub-inhibitory tail window during treatment dropouts.")
    else:
        pvs_score = 0.086
        st.success("✅ Protected: Dolutegravir maintains an ultra-low vulnerability footprint due to its high genetic barrier.")

    # Calculate dynamic Resistance Risk Index (RRI = MF * PVS)
    kzn_df["RRI"] = kzn_df[target_column] * pvs_score
    
    # Assign clear colors to classifications
    def assign_risk_tier(rri):
        if rri > 0.50: # Scale calibrated down relative to mock frequency sets
            return "🔴 Critical"
        elif rri >= 0.25:
            return "🟠 High"
        elif rri >= 0.10:
            return "🟡 Moderate"
        else:
            return "🟢 Low"
            
    kzn_df["Risk Tier"] = kzn_df["RRI"].apply(assign_risk_tier)
    
    st.markdown("---")
    st.markdown("#### Step 2: Regional Risk Stratification Matrix")
    
    # Render interactive chart visualizer using Plotly Express
    fig = px.bar(
        kzn_df, 
        x="Sub-District", 
        y="RRI", 
        color="Risk Tier",
        title=f"Calculated Resistance Risk Index (RRI) for {selected_mutation}",
        color_discrete_map={"🔴 Critical": "#ef5350", "🟠 High": "#ff9800", "🟡 Moderate": "#ffeb3b", "🟢 Low": "#66bb6a"},
        labels={"RRI": "Calculated RRI Value"},
        category_orders={"Risk Tier": ["🔴 Critical", "🟠 High", "🟡 Moderate", "🟢 Low"]}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Expose the tracking dataframe table natively
    st.markdown("#### Raw Calculated Metrics by Sub-District Location:")
    st.dataframe(
        kzn_df[["Sub-District", target_column, "RRI", "Risk Tier"]].rename(
            columns={target_column: "Mutation Frequency in Cohort"}
        ),
        use_container_width=True
    )

# ----------------------------------------------------
# PAGE 3: TECHNICAL SPECIFICATIONS (FOR YALE/NICD REVIEW)
# ----------------------------------------------------
elif app_mode == "Technical Pipeline Specs":
    st.title("💻 Technical Pipeline Architecture Specifications")
    st.markdown("### Backend Routines, Automation Core, & Reference Parameters")
    st.markdown("---")
    
    st.info("ℹ️ Note: This section contains the exact algorithmic specifications currently undergoing review by the NICD bioinformatics team and Yale faculty.")
    
    st.markdown("#### 1. Python Sequence Ingestion Logic")
    st.code("""
import os
from Bio import Entrez

Entrez.email = "sbagaria2009@gmail.com"
Entrez.tool = "ResistanceMapZA_v1"

def execute_ncbi_ingestion():
    # Programmatic target tracking query for KZN pol gene footprints
    search_query = '"HIV-1"[Organism] AND "South Africa"[Geo_Location] AND pol[Gene] AND 2015:2026[Publication Date]'
    handle = Entrez.esearch(db="nucleotide", term=search_query, retmax="5000")
    search_results = Entrez.read(handle)
    handle.close()
    return search_results["IdList"]
    """, language="python")
    
    st.markdown("#### 2. Local Alignment Parameter Matrix")
    st.write(
        "Pairwise mappings are calculated via a localized Smith-Waterman core sequence matrix against the "
        "international HXB2 genome (GenBank: K03455; coordinates 2085 to 5096 bp). The system penalizes frame shifts "
        "using an affine gap configuration where Gap Open = 10 and Gap Extend = 2."
    )
    
    st.markdown("#### 3. Stanford API Validation Routine")
    st.code("""
import requests

def query_stanford_hivdb(sequence_payload):
    # GraphQL architecture to extract specific mutations at RT points 41, 65, 103, and 184
    graphql_query = \"\"\"
    query AnalyzeHIVSequences($sequences: [String]!) {
      sequenceAnalysis(sequences: $sequences) {
        inputSequence { header }
        mutations { primaryType text }
        drugResistance { drug { name displayAbbr } score level }
      }
    }
    \"\"\"
    url = "https://hivdb.stanford.edu/graphql"
    response = requests.post(url, json={"query": graphql_query, "variables": {"sequences": sequence_payload}})
    return response.json()
    """, language="python")
