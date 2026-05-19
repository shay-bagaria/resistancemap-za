import streamlit as st
import math
import numpy as np
import plotly.graph_objects as go
from datetime import date

# 1. PAGE CONFIGURATION (Must be the first command)
st.set_page_config(page_title="ResistanceMap ZA | Clinical Tool", layout="wide", page_icon="🧬")

# 2. SIDEBAR & CLINICAL INPUTS
st.sidebar.title("ResistanceMap ZA")
st.sidebar.caption("Clinical Decision Support System | Secure Build")
st.sidebar.divider()

st.sidebar.header("Patient Parameters")
patient_id = st.sidebar.text_input("Patient ID (Anonymised)", "KZN-8842-A")
regimen = st.sidebar.selectbox("Current ART Regimen", ["TLD (Tenofovir + Lamivudine + Dolutegravir)"])

st.sidebar.subheader("Clinical Modifiers")
tb_coinfection = st.sidebar.checkbox("Active TB Co-Infection (Rifampicin)")
traditional_meds = st.sidebar.checkbox("Concurrent Traditional Medicine")
renal_function = st.sidebar.selectbox("Renal Function (eGFR)", ["Normal (>90)", "Moderate Impairment (30-59)"])

days_missed = st.sidebar.slider("Consecutive Days Defaulted", 0, 14, 3)
hours_missed = days_missed * 24

# 3. PHARMACOKINETIC DATABASE
pk_db = {
    "Tenofovir": {"t_half": 17.0, "c_max": 0.3, "mic": 0.05, "mutation": "K65R"},
    "Lamivudine": {"t_half": 5.0, "c_max": 1.5, "mic": 0.5, "mutation": "M184V"},
    "Dolutegravir": {"t_half": 14.0, "c_max": 3.3, "mic": 0.5, "mutation": "R263K"}
}

active_drugs = ["Tenofovir", "Lamivudine", "Dolutegravir"]
current_levels = {}
modifiers_applied = []

# 4. MATHEMATICAL ENGINE
for drug in active_drugs:
    stats = pk_db[drug]
    adjusted_t_half = stats["t_half"]
    
    # Apply Modifiers
    if tb_coinfection and drug == "Dolutegravir":
        adjusted_t_half *= 0.5
        if "Rifampicin Induction" not in modifiers_applied: modifiers_applied.append("Rifampicin Induction")
        
    if traditional_meds and drug == "Dolutegravir":
        adjusted_t_half *= 0.6
        if "CYP450 Interaction" not in modifiers_applied: modifiers_applied.append("CYP450 Interaction")
        
    if renal_function == "Moderate Impairment (30-59)" and drug != "Dolutegravir":
        adjusted_t_half *= 1.4
        if "Renal Clearance Delay" not in modifiers_applied: modifiers_applied.append("Renal Clearance Delay")
        
    k_e = math.log(2) / adjusted_t_half
    current_levels[drug] = stats["c_max"] * math.exp(-k_e * hours_missed)

# 5. MAIN DASHBOARD UI
st.title("🏥 Clinical Resistance Risk Assessment")
st.write(f"**Date:** {date.today().strftime('%d %B %Y')} | **Patient:** {patient_id}")
st.divider()

if modifiers_applied:
    st.info(f"**Active Metabolic Modifiers:** {', '.join(modifiers_applied)}")

# 6. PLOTLY VISUALISATION
time_array = np.arange(0, (max(days_missed, 7) * 24) + 48, 2)
fig = go.Figure()
colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

for idx, drug in enumerate(active_drugs):
    stats = pk_db[drug]
    adjusted_t_half = stats["t_half"]
    
    # Re-apply modifiers for the graph projection
    if tb_coinfection and drug == "Dolutegravir": adjusted_t_half *= 0.5
    if traditional_meds and drug == "Dolutegravir": adjusted_t_half *= 0.6
    if renal_function == "Moderate Impairment (30-59)" and drug != "Dolutegravir": adjusted_t_half *= 1.4
    
    k_e = math.log(2) / adjusted_t_half
    decay_curve = stats["c_max"] * np.exp(-k_e * time_array)
    
    # Main drug line
    fig.add_trace(go.Scatter(x=time_array, y=decay_curve, mode='lines', name=drug, line=dict(width=3, color=colors[idx])))
    # MIC dashed line
    fig.add_trace(go.Scatter(x=[0, max(time_array)], y=[stats["mic"], stats["mic"]], mode='lines', name=f"{drug} MIC", line=dict(width=1, dash='dash', color=colors[idx]), showlegend=False))

# Configure graph layout
fig.update_layout(
    xaxis_title="Hours Since Last Dose", 
    yaxis_title="Plasma Concentration (mg/L) [Log Scale]", 
    yaxis_type="log", 
    height=400, 
    margin=dict(l=0, r=0, t=30, b=0)
)
fig.add_vline(x=hours_missed, line_width=2, line_dash="solid", line_color="red", annotation_text="CURRENT STATUS")

st.plotly_chart(fig, use_container_width=True)

# 7. CLINICAL DIRECTIVES
st.write("### 🚨 Mutation Risk & Clinical Directives")

vulnerable_drugs = [d for d in active_drugs if (pk_db[d]["mic"] * 0.05) < current_levels[d] < pk_db[d]["mic"]]
cleared_drugs = [d for d in active_drugs if current_levels[d] <= (pk_db[d]["mic"] * 0.05)]

if days_missed == 0:
    st.success("**Status Normal:** Full adherence detected. Maintain current dosing schedule.")
elif vulnerable_drugs:
    for drug in vulnerable_drugs:
        mut = pk_db[drug]['mutation']
        st.warning(f"⚠️ **{drug}** is at sub-inhibitory levels. High selection pressure for the **{mut}** mutation.")
        if mut == "M184V":
            st.success("💡 **Note:** M184V induces hypersusceptibility to Tenofovir. Maintain Tenofovir backbone if switching regimens.")
else:
    st.error("🔴 **Systemic Clearance:** All compounds have fallen below mutational selection thresholds. Viral replication is currently uninhibited.")
