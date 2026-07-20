"""'Understanding Your Results' — the plain-language patient guide.

Rewritten in Stage 6.3 to match what the application now does. The v4.0/Stage 1
version described a 0-100 "Resistance Risk Score", "Drugs Below MIC", and a
"Mutation & Resistance" tab that estimated a mutation probability — all three
were removed earlier in the remediation (methodology sections 9.1, 10.2), so a
guide still describing them would be actively misleading. This version
describes the composite risk band, the regimen state, the ordinal mutation
index, and the clinical-risk/support-needs split as they are actually
implemented, and replaces "MIC" throughout with the correct antiretroviral
terminology (methodology section 7.1: MIC is a bacteriology term from broth
dilution assays and does not apply to antiretrovirals).
"""

import streamlit as st

from resistancemap import config


def render():
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
            doctors think through whether your HIV medication is likely to still be working properly.<br><br>
            When you take your ARV pills every day, they keep the virus under control. But if doses are missed,
            the virus can start changing (we call these changes <strong>"mutations"</strong>). Once the virus changes,
            your current pills might stop working as well.<br><br>
            This tool helps your doctor think through those problems <strong>before</strong> they become serious — so
            they can adjust your treatment early and keep you healthy. It is a research prototype, not a finished
            medical device, and it does not replace your doctor's judgement.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Section 2: The Dashboard Numbers ──
    st.markdown("<p class='section-header'>What Do the Numbers on the Dashboard Mean?</p>", unsafe_allow_html=True)

    guide_items = [
        ("Composite Risk Band",
         "This is a general-picture indicator, shown as a word rather than a score.",
         "It combines the state of your regimen (see below), how likely a mutation is, your viral load and your CD4 "
         "count into one of four bands: <strong>Minimal, Low, Moderate or High.</strong> It is not a percentage and "
         "it is not a probability — it is a rough ranking, hand-built by the person who made this tool, and it has "
         "not been tested against real patient outcomes.",
         "The band is built from hand-chosen weights, clearly marked on screen as such. It is meant to help a "
         "clinician prioritise, not to predict anything with precision."),

        ("Regimen State",
         "This describes which of your ARV drugs are still working right now.",
         "<strong>Full suppression</strong> means every drug in your regimen is still active — the best state. "
         "<strong>Partial suppression</strong> means some drugs have dropped off. "
         "<strong>Functional monotherapy</strong> means only one drug is still active — this is actually the state "
         "most likely to let the virus learn to resist that one remaining drug, so it gets the most serious warning. "
         "<strong>No pressure</strong> means every drug has cleared from your body — the virus is likely to rebound "
         "and you need to restart treatment, but resistance is less likely to be selected in that particular window, "
         "because there's no drug left to \"push\" the virus into resisting anything.",
         "The system estimates how much of each drug is likely left in your body at each hour since your last dose, "
         "and counts how many are still above the level needed to work."),

        ("Days Defaulted",
         "This is simply how many days since you last took your medication.",
         "<strong>0 days = you took your pills today.</strong> Every extra day without pills means the medicine in "
         "your body is dropping. After a few days, some drugs will have completely left your system.",
         "Your doctor or pharmacy records show when you last collected your pills. The system uses this to estimate "
         "how much drug is left in your body."),

        ("Viral Load",
         "This blood test counts how much HIV is in your blood.",
         "<strong>Undetectable (below 50 copies/mL) = excellent.</strong> It means your treatment is working well. "
         "Above 1,000 copies/mL means the virus may be growing because the treatment is struggling. "
         "Your doctor may need to check for resistance.",
         "Viral load is measured from a blood sample sent to a laboratory. Results are reported in copies per "
         "millilitre of blood."),

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
                            letter-spacing: 0.1em; margin-bottom: 0.3rem;'>How it's worked out</div>
                <p style='font-size: 0.78rem; color: #94a3b8; line-height: 1.6; margin: 0;'>{calculation}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Section 3: The Tabs ──
    st.markdown("<p class='section-header'>What Are the Different Tabs?</p>", unsafe_allow_html=True)

    tabs_guide = [
        ("PK Decay Curves",
         "Shows how much of each medicine is estimated to be left in your body after a missed dose",
         "Think of it like a fuel gauge for each of your ARV drugs. For dolutegravir and efavirenz, the coloured "
         "lines show an estimated blood level dropping over time, compared against the level needed to keep the "
         "virus suppressed. Tenofovir, lamivudine and abacavir work differently: they are absorbed into your cells "
         "and changed into an active form that can stay there far longer than the drug stays in your blood, so for "
         "those three the chart instead shows a percentage of how much of that active, in-cell form is estimated to "
         "remain — never a blood level, because there's no equivalent \"below the line\" test for that form of the "
         "drug. A coloured band beneath the chart shows the regimen state described above."),

        ("Mutation & Resistance",
         "Shows an ordinal ranking, not a percentage, of how much a mutation risk is building for each drug",
         "HIV makes copies of itself very quickly, and sometimes those copies have small mistakes called mutations. "
         "Some mutations make the virus resistant to your medicine. For example, <strong>M184V</strong> makes "
         "Lamivudine less effective, and <strong>K65R</strong> does the same to Tenofovir. This tab ranks each drug "
         "as Minimal, Low, Moderate or High, based on how much that drug's level has dropped <em>and</em> how easily "
         "the virus can resist that particular drug in general (its \"genetic barrier\" — some drugs need only one "
         "small change to be resisted, others need several). It is explicitly labelled as a heuristic ranking, not "
         "a probability, and it has not been checked against real patient outcomes."),

        ("Clinical Directives",
         "Alerts and instructions for your healthcare team",
         "If you're also being treated for <strong>TB</strong>, the system warns your doctor that rifampicin speeds "
         "up how fast dolutegravir leaves your body, and that the usual response is to take dolutegravir twice a "
         "day instead of once. If you use <strong>traditional medicines</strong> like African Potato or St John's "
         "Wort, or if a kidney blood test (eGFR) comes back low, the system raises a separate note for your clinic "
         "team to consider — kidney function is flagged as a safety concern on its own, not folded into the "
         "resistance picture above."),

        ("Clinical Risk & Support Needs",
         "Splits your medical picture from your life circumstances, on purpose",
         "The left side repeats the composite risk band and regimen state, built only from your drug levels and lab "
         "results. The right side is separate: it looks at things like distance from the clinic, transport, missed "
         "appointments and food security, and turns them into offers of help — like a longer supply of medicine so "
         "you don't have to travel as often, or a referral for food support — rather than a score about you. Whether "
         "or not you've told others about your HIV status is asked only so your clinic can offer counselling; it is "
         "never shown on this screen or in any report, because that is private and, for some patients, could be "
         "unsafe to have visible."),

        ("Audit & Compliance",
         "A complete record of every check the system performs",
         "Every time a doctor uses ResistanceMap ZA, the system creates a <strong>tamper-evident</strong> record — "
         "if any earlier entry is changed, the records that follow it no longer match, so tampering shows up. "
         "This is not the same as tamper-proof: someone with permission to write to the records could rebuild them, "
         "so the record makes changes <em>detectable</em> rather than impossible. It helps make sure every alert was "
         "seen and every guideline was followed."),
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
        ("PA-IC90 / therapeutic threshold",
         "The blood level a drug needs to reach to reliably stop the virus. This tool used to use the term "
         "\"MIC\" (Minimum Inhibitory Concentration), but that is a bacteriology term from a laboratory test done "
         "on bacteria in a dish, and it does not apply to antiretrovirals or to HIV. The correct terms for ARVs are "
         "\"PA-IC90\" (protein-adjusted 90% inhibitory concentration) or simply \"therapeutic threshold\"."),
        ("Inhibitory quotient",
         "For dolutegravir and efavirenz, this is your estimated blood level divided by the therapeutic threshold. "
         "Above 1 means the estimated level is at or above what's needed; below 1 means it's fallen short."),
        ("Active moiety",
         "The form of a drug that actually does the work inside your cells. Tenofovir, lamivudine and abacavir are "
         "taken as one form but converted inside your cells into a different, active form — that active, in-cell "
         "form is what this tool tracks for those three drugs, because it lasts much longer than the drug does in "
         "your blood."),
        ("Half-life", "How long it takes for half of a drug (or its active, in-cell form) to leave your body. A longer half-life means it stays longer."),
        ("Functional monotherapy",
         "A situation where only one drug in your combination is still active while the others have cleared. "
         "This is the riskiest window for the virus to learn to resist that one remaining drug, because it's under "
         "pressure from a single drug rather than a combination."),
        ("Viral Load", "A blood test that measures how much HIV is in your body. Lower is better. 'Undetectable' is the goal."),
        ("CD4 Count", "A count of the immune cells that HIV attacks. Higher numbers mean a stronger immune system."),
        ("Resistance", "When the virus changes so that a drug can no longer stop it from growing."),
        ("First-line / Second-line / Third-line", "Treatment levels. First-line is the starting treatment. If it fails, you move to second-line (more expensive), then third-line (very expensive and limited options)."),
        ("TLD", "Tenofovir + Lamivudine + Dolutegravir — the most common first-line ARV combination in South Africa."),
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
        ResistanceMap ZA v{config.APP_VERSION} &nbsp;·&nbsp; Patient Education Module<br>
        Written in plain language for patients living with HIV in KwaZulu-Natal<br>
        This tool does not replace your doctor. Always follow your healthcare team's advice.<br>
        <span style='color:#1e3a5f;'>Research prototype — not an approved medical device. Not for clinical use.</span>
    </div>
    """, unsafe_allow_html=True)
