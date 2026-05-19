import streamlit as st
import math
import numpy as np
import plotly.graph_objects as go
import datetime

# ==========================================
# 1. ENTERPRISE PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="ResistanceMap ZA | Enterprise CDSS", layout="wide", page_icon="🏥")

st.sidebar.title("🧬 ResistanceMap ZA")
st.sidebar.caption("Clinical Decision Support System v3.0 | KZN DOH Prototype")
st.sidebar.divider()

# ==========================================
# 2. ADVANCED COMORBIDITY INPUTS
# ==========================================
st.sidebar.header("Advanced Patient Profile")
patient_id = st.sidebar.text_input("Patient ID (Anonymised)", "KZN-8842-A")
regimen = st.sidebar.selectbox("Current ART Regimen", ["TLD (Tenofovir + Lamivudine + Dolutegravir)"])

st.sidebar.subheader("Clinical Modifiers")
tb_coinfection = st.sidebar.checkbox("Active TB Co-Infection (On Rifampicin)")
traditional_meds = st.sidebar.checkbox("Concurrent Traditional Medicine (St. John's Wort / African Potato)")
renal_function = st.sidebar.selectbox("Renal Function (eGFR)", ["Normal (>90)", "Moderate Impairment (30-59)"])

days_missed = st.sidebar.slider("Consecutive Days Defaulted", 0, 14, 3)
hours_missed = days_missed * 24

# ==========================================
# 3. BIO-CLINICAL PROCESSING ENGINE
# ==========================================
# Baseline PK Data
pk_db = {
    "Tenofovir": {"t_half": 17.0, "c_max": 0.3, "mic": 0.05, "mutation": "K65R"},
    "Lamivudine": {"t_half": 5.0, "c_max": 1.5, "mic": 0.5, "mutation": "M184V"},
    "Dolutegravir": {"t_half": 14.0, "c_max": 3.3, "mic": 0.5, "mutation": "R263K"}
}

active_drugs = ["Tenofovir", "Lamivudine", "Dolutegravir"]
current_levels = {}
modifiers_applied = []

for drug in active_drugs:
    stats = pk_db[drug]
    adjusted_t_half = stats["t_half"]
    
    # Apply Enterprise Clinical Logic
    if tb_coinfection and drug == "Dolutegravir":
        adjusted_t_half *= 0.5  # Rifampicin is a CYP3A4 inducer, halving DTG half-life
        if "Rifampicin CYP3A4 Induction" not in modifiers_applied: modifiers_applied.append("Rifampicin CYP3A4 Induction")
        
    if traditional_meds and drug == "Dolutegravir":
        adjusted_t_half *= 0.6  # Traditional CYP450 interactions
        if "Traditional Medicine CYP450 Interaction" not in modifiers_applied: modifiers_applied.append("Traditional Medicine CYP450 Interaction")
        
    if renal_function == "Moderate Impairment (30-59)" and drug != "Dolutegravir":
        adjusted_t_half *= 1.4  # Renal impairment slows clearance
        if "Renal Clearance Delay" not in modifiers_applied: modifiers_applied.append("Renal Clearance Delay")
        
    k_e = math.log(2) / adjusted_t_half
    current_levels[drug] = stats["c_max"] * math.exp(-k_e * hours_missed)

# ==========================================
# 4. DASHBOARD UI & ALERTS
# ==========================================
st.title("🏥 Enterprise Resistance Risk Assessment")
st.write("### Pharmacokinetic Decay Trajectory (Comorbidity Adjusted)")

if modifiers_applied:
    st.info(f"**Active Metabolic Modifiers Applied:** {', '.join(modifiers_applied)}")

# Plotly Generation (The Visual Proof)
time_array = np.arange(0, (max(days_missed, 7) * 24) + 48, 2)
fig = go.Figure()
colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

for idx, drug in enumerate(active_drugs):
    stats = pk_db[drug]
    adjusted_t_half = stats["t_half"]
    if tb_coinfection and drug == "Dolutegravir": adjusted_t_half *= 0.5
    if traditional_meds and drug == "Dolutegravir": adjusted_t_half *= 0.6
    if renal_function == "Moderate Impairment (30-59)" and drug != "Dolutegravir": adjusted_t_half *= 1.4
    
    k_e = math.log(2) / adjusted_t_half
    decay_curve = stats["c_max"] * np.exp(-k_e * time_array)
    
    fig.add_trace(go.Scatter(x=time_array, y=decay_curve, mode='lines', name=drug, line=dict(width=3, color=colors[idx])))
    fig.add_trace(go.Scatter(x=[0, max(time_array)], y=[stats["mic"], stats["mic"]], mode='lines', name=f"{drug} MIC", line=dict(width=1, dash='dash', color=colors[idx]), showlegend=False))

fig.update_layout(xaxis_title="Hours Since Last Dose", yaxis_title="Plasma Concentration (mg/L) [Log Scale]", yaxis_type="log", height=400, margin=dict(l=0, r=0, t=30, b=0))
fig.add_vline(x=hours_missed, line_width=2, line_dash="solid", line_color="red", annotation_text="CURRENT STATUS")
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. CROSS-RESISTANCE PREDICTOR & PROTOCOLS
# ==========================================
st.write("### 🚨 Clinical Directives & Guideline Adherence")

vulnerable_drugs = [d for d in active_drugs if (pk_db[d]["mic"] * 0.05) < current_levels[d] < pk_db[d]["mic"]]

if tb_coinfection:
    st.error("**NDoH Guideline Alert:** Patient is on Rifampicin for TB. Dolutegravir standard dosage (50mg daily) is insufficient due to accelerated clearance. Must increase to 50mg BD (Twice Daily).")

if vulnerable_drugs:
    for drug in vulnerable_drugs:
        mut = pk_db[drug]['mutation']
        st.warning(f"⚠️ **{drug}** is currently at sub-inhibitory levels. High selection pressure for **{mut}**.")
        
        # Cross-Resistance Predictor Engine
        if mut == "M184V":
            st.success("💡 **Cross-Resistance Predictor:** While M184V causes high-level Lamivudine resistance, it induces *hypersusceptibility* to Tenofovir and delays the emergence of K65R. Maintain Tenofovir backbone in second-line regimen.")
else:
    st.info("Systemic Clearance Status: Stable based on current inputs.")
