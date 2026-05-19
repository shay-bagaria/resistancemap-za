import streamlit as st
import math

# 1. THE TITLE AND HEADER
st.set_page_config(page_title="ResistanceMap ZA Clinical Tool", page_icon="🧬")
st.title("🧬 ResistanceMap ZA")
st.subheader("Frontline ARV Adherence & Mutation Risk Monitor")
st.write("This tool helps clinic workers predict HIV drug resistance based on missed medication days.")

st.divider()

# 2. THE INPUT MENU (For the Nurse)
st.write("### Patient Data Input")
drug = st.selectbox("Which medication is the patient taking?", 
                    ["Efavirenz (EFV)", "Tenofovir (TDF)", "Lamivudine (3TC)"])

days_missed = st.slider("How many days has the patient missed their medication?", 0, 14, 0)
hours_missed = days_missed * 24

# 3. THE DRUG SCIENCE (The Math)
# [Half-life in hours, Max blood level, Minimum safe level, Target Mutation]
drug_database = {
    "Efavirenz (EFV)": {"half_life": 45.0, "c_max": 4.0, "mic": 1.0, "mutation": "K103N"},
    "Tenofovir (TDF)": {"half_life": 17.0, "c_max": 0.3, "mic": 0.05, "mutation": "K65R"},
    "Lamivudine (3TC)": {"half_life": 5.0,  "c_max": 1.5, "mic": 0.5, "mutation": "M184V"}
}

# Pull the specific numbers for the chosen drug
stats = drug_database[drug]

# Calculate how much drug is left in the blood using exponential decay
elimination_rate = math.log(2) / stats["half_life"]
current_level = stats["c_max"] * math.exp(-elimination_rate * hours_missed)

st.divider()

# 4. THE OUTPUT (The Traffic Light System)
st.write("### Clinical Risk Assessment")

# Display the calculated drug level
st.metric(label="Estimated Drug Level in Blood (mg/L)", value=round(current_level, 3))

# GREEN: The patient is safe
if current_level >= stats["mic"]:
    st.success("🟢 SAFE: The drug level is still high enough to fight the virus.")

# ORANGE: The danger zone (Sub-therapeutic tail)
elif current_level < stats["mic"] and current_level > (stats["mic"] * 0.1):
    st.warning(f"🟠 DANGER ZONE: Drug level is too low to kill the virus, but high enough to cause mutations. High risk of the **{stats['mutation']}** mutation developing.")
    st.write("**Action required:** Counsel patient on strict adherence. Consider viral load testing if this happens often.")

# RED: The drug is completely gone
else:
    st.error("🔴 COMPLETELY CLEARED: The drug has essentially left the patient's system. The virus is now multiplying freely.")
    st.write("**Action required:** Immediate clinical intervention to restart therapy.")
