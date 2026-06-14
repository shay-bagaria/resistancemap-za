import streamlit as st

# Configure the page layout
st.set_page_config(
    page_title="ResistanceMap ZA",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Navigation Control
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio(
    "Go to:",
    ["About ResistanceMap ZA", "Interactive Surveillance Dashboard", "Technical Pipeline Data"]
)

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
        st.metric(label="Target Region", value="KwaZulu-Natal")
    with col2:
        st.metric(label="Primary Goal", value="Therapeutic Protection")
    with col3:
        st.metric(label="System Status", value="Active / Open Source")
        
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
        3. **Review the Data Core:** The **Technical Pipeline Data** tab exposes the underlying biological sequence codes and scientific research papers backing the mathematical engine.
        """
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("Developed as a zero-cost public health utility to support the NHI framework.")

# ----------------------------------------------------
# PAGE 2: YOUR ORIGINAL DASHBOARD LOGIC (MAPS, CHARTS, CALCULATORS)
# ----------------------------------------------------
elif app_mode == "Interactive Surveillance Dashboard":
    st.title("📊 Interactive Surveillance Dashboard")
    st.write("### Sub-District Mapping & Pharmacokinetic Vulnerability Engine")
    
    # PASTE ALL YOUR ORIGINAL APP CODE HERE:
    # (e.g., st.plotly_chart, your RRI calculations, interactive user inputs)
    st.info("Displaying localized mutation tracking and dynamic RRI risk stratification engines.")

# ----------------------------------------------------
# PAGE 3: ADVANCED TECHNICAL/ACADEMIC SPECIFICATIONS
# ----------------------------------------------------
elif app_mode == "Technical Pipeline Data":
    st.title("💻 Technical Pipeline Architecture")
    st.write("### Ingestion Modules and Reference Alignment Core")
    
    # PASTE YOUR DATA WRANGLING, BIO.ENTREZ CHECKS, OR REPO DOCUMENTATION CODES HERE:
    st.info("System linked dynamically to NCBI GenBank and Stanford HIV Drug Resistance Databases.")
