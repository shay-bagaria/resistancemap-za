import streamlit as st
import math
import numpy as np
import plotly.graph_objects as go
import datetime

# ==========================================
# 1. PAGE CONFIGURATION & HOSPITAL BRANDING
# ==========================================
st.set_page_config(page_title="ResistanceMap ZA | CDSS", layout="wide", page_icon="🏥")

st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Star_of_life2.svg/200px-Star_of_life2.svg.png", width=50)
st.sidebar.title("ResistanceMap ZA")
st.sidebar.caption("Clinical Decision Support System v2.1")
st.sidebar.divider()

# ==========================================
# 2. PATIENT METADATA & INPUT (SIDEBAR)
# ==========================================
st.sidebar.header("Patient Profile")
patient_id = st.sidebar.text_input("Patient ID / File Number", "KZN-8842-A")
weight = st.sidebar.number_input("Patient Weight (kg)", min_value=30, max_value=150, value=65)
renal_function = st.sidebar.selectbox("Renal Function (eGFR)", ["Normal (>90)", "Mild Impairment (60-89)", "Moderate (30-59)"])

st.sidebar.header("Adherence Parameters")
regimen = st.sidebar.selectbox("Current ART Regimen", [
    "TLD (Tenofovir + Lamivudine + Dolutegravir)", 
    "TEE (Tenofovir + Emtricitabine + Efavirenz)"
])
days_missed = st.sidebar.slider("Consecutive Days Missed", 0, 21, 5)
hours_missed = days_missed * 24

# ==========================================
# 3. PHARMACOKINETIC DATABASE
# ==========================================
# Format: t_half (hrs), C_max (mg/L), MIC (mg/L), Target Mutation
pk_db = {
    "Tenofovir": {"t_half": 17.0, "c_max": 0.3, "mic": 0.05, "mutation": "K65R"},
    "Lamivudine": {"t_half": 5.0, "c_max": 1.5, "mic": 0.5, "mutation": "M184V"},
    "Dolutegravir": {"t_half": 14.0, "c_max": 3.3, "mic": 0.5, "mutation": "R263K"},
    "Emtricitabine": {"t_half": 10.0, "c_max": 1.8, "mic": 0.1, "mutation": "M184V"},
    "Efavirenz": {"t_half": 45.0, "c_max": 4.0, "mic": 1.0, "mutation": "K103N"}
}

regimen_map = {
    "TLD (Tenofovir + Lamivudine + Dolutegravir)": ["Tenofovir", "Lamivudine", "Dolutegravir"],
    "TEE (Tenofovir + Emtricitabine + Efavirenz)": ["Tenofovir", "Emtricitabine", "Efavirenz"]
}

active_drugs = regimen_map[regimen]

# Adjust half-life based on renal function (basic proxy model)
renal_modifier = 1.0
if renal_function == "Moderate (30-59)":
    renal_modifier = 1.4  # Drugs clear 40% slower

# ==========================================
# 4. MAIN DASHBOARD UI
# ==========================================
st.title("🏥 Patient Resistance Risk Assessment")
st.write(f"**Date:** {datetime.date.today().strftime('%d %B %Y')} | **Patient:** {patient_id}")
st.divider()

col1, col2, col3 = st.columns(3)

# Calculate current levels and identify the "Tail" drug
current_levels = {}
for drug in active_drugs:
    stats = pk_db[drug]
    adjusted_t_half = stats["t_half"] * renal_modifier
    k_e = math.log(2) / adjusted_t_half
    current_levels[drug] = stats["c_max"] * math.exp(-k_e * hours_missed)

# Display Top-Line Metrics
col1.metric("Regimen Type", regimen.split(" ")[0])
col2.metric("Days Defaulted", days_missed)
col3.metric("Systemic Clearance Status", "Critical" if days_missed > 3 else "Stable", delta="-High Risk" if days_missed > 3 else "Low Risk", delta_color="inverse")

# ==========================================
# 5. DYNAMIC PLOTLY CHART (THE "WOW" FACTOR)
# ==========================================
st.write("### Pharmacokinetic Decay Trajectory (Simulated)")

time_array = np.arange(0, (days_missed * 24) + 48, 2)
fig = go.Figure()

colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

for idx, drug in enumerate(active_drugs):
    stats = pk_db[drug]
    k_e = math.log(2) / (stats["t_half"] * renal_modifier)
    decay_curve = stats["c_max"] * np.exp(-k_e * time_array)
    
    fig.add_trace(go.Scatter(
        x=time_array, y=decay_curve, 
        mode='lines', name=drug,
        line=dict(width=3, color=colors[idx])
    ))
    
    # Add horizontal dotted line for Minimum Inhibitory Concentration (MIC)
    fig.add_trace(go.Scatter(
        x=[0, max(time_array)], y=[stats["mic"], stats["mic"]],
        mode='lines', name=f"{drug} MIC",
        line=dict(width=1, dash='dash', color=colors[idx]),
        showlegend=False
    ))

fig.update_layout(
    xaxis_title="Hours Since Last Dose",
    yaxis_title="Plasma Concentration (mg/L) [Log Scale]",
    yaxis_type="log",
    height=400,
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Add a vertical red line showing EXACTLY where the patient is now
fig.add_vline(x=hours_missed, line_width=2, line_dash="solid", line_color="red", annotation_text="CURRENT STATUS")

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 6. CLINICAL PATHWAYS & ACTION PLAN
# ==========================================
st.write("### 🚨 Mutation Risk & Clinical Directives")

# Determine which drugs are in the sub-therapeutic tail
vulnerable_drugs = []
for drug in active_drugs:
    level = current_levels[drug]
    mic = pk_db[drug]["mic"]
    if (mic * 0.05) < level < mic:
        vulnerable_drugs.append(drug)

if days_missed == 0:
    st.success("**Status Normal:** Patient is adhering to treatment. No clinical action required.")
elif len(vulnerable_drugs) > 0:
    st.error(f"**CRITICAL VULNERABILITY DETECTED:** Pharmacokinetic tailing occurring.")
    for drug in vulnerable_drugs:
        mut = pk_db[drug]['mutation']
        st.warning(f"⚠️ **{drug}** is currently at sub-inhibitory levels. High selection pressure for the **{mut}** mutation.")
    
    st.write("#### Recommended Protocol:")
    st.markdown("""
    1. **Do not immediately restart regimen.** Monotherapy exposure risks fixing the mutation.
    2. **Order Viral Load Genotyping.** Test specifically for Reverse Transcriptase inhibitors.
    3. **Dispatch CHW.** Flag patient for Community Health Worker adherence counselling.
    """)
else:
    st.info("**Systemic Clearance:** All active compounds have fallen below mutational selection thresholds. Viral replication is uninhibited, but selection pressure is low.")
    st.write("#### Recommended Protocol:")
    st.markdown("1. Restart standard first-line regimen immediately.\n2. Schedule follow-up viral load test in 30 days to confirm re-suppression.")

st.divider()
st.caption("Powered by ResistanceMap ZA | KwaZulu-Natal Genomic Surveillance Engine")
