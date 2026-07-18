# ResistanceMap ZA — Scientific Methodology

Version: 0.1 Draft
Author: Shay Bagaria

---

## 1. Target Biology

### The HIV-1 pol Gene

The human immunodeficiency virus type 1 (HIV-1) pol gene encodes three critical enzymes:

- Protease (PR): Cleaves viral polyproteins into functional units during viral maturation
- Reverse Transcriptase (RT): Converts viral RNA into DNA, the primary target of most antiretroviral drugs
- Integrase (IN): Inserts viral DNA into the host cell genome

The pol gene is the primary target of this pipeline because:

1. Most first-line antiretroviral drugs target RT and PR
2. Drug-resistance mutations in pol are the most clinically documented
3. The Stanford HIVDB resistance classification system is built around pol mutations
4. NCBI GenBank contains the largest volume of South African HIV pol sequences

### The HXB2 Reference Strain

All sequences in this pipeline are aligned against HXB2 (GenBank accession K03455), the internationally accepted HIV-1 reference genome. Mutation positions such as K103N and M184V are numbered relative to HXB2 coordinates.

---

## 2. Key Resistance Mutations

The following mutations are the primary targets of Phase 1 analysis, selected based on their prevalence in sub-Saharan African treatment cohorts and their clinical significance for first-line ARV regimens used in KwaZulu-Natal.

| Mutation | Gene Region | Drug Resistance | Clinical Significance |
|---|---|---|---|
| K103N | RT | Efavirenz, Nevirapine | Most common NNRTI resistance mutation in sub-Saharan Africa |
| M184V | RT | Lamivudine, Emtricitabine | High-level resistance, also reduces viral fitness |
| K65R | RT | Tenofovir | Emerging resistance to the backbone of first-line therapy |
| M41L | RT | Thymidine analogues | Thymidine Analogue Mutation that accumulates with treatment failure |
| V179D/E | RT | Low-level NNRTI resistance | Increasingly documented in KZN surveillance studies |

This list will be expanded as data analysis progresses.

---

## 3. Pharmacokinetic Framework

### The Core Equation

Drug concentration over time following a missed dose is modelled using a standard one-compartment open elimination model:

C(t) = C0 x e^(-Ke x t)

Where:

- C(t) is plasma drug concentration at time t in ng/mL
- C0 is the steady-state trough concentration at the time of the missed dose
- Ke is the elimination rate constant
- t is time elapsed since the missed dose in hours

The elimination rate constant is derived from the drug half-life:

Ke = ln(2) divided by half-life

### Drug Half-Life Values for First-Line KZN Regimens

| Drug | Half-Life | Relevance |
|---|---|---|
| Efavirenz | 40 to 55 hours | Long tail, sub-inhibitory levels persist for days |
| Tenofovir | 17 hours | Medium tail |
| Lamivudine | 5 to 7 hours | Short tail, concentration drops rapidly |

### The Clinical Implication

Efavirenz's exceptionally long half-life means that when a patient stops taking it, drug levels remain in the sub-inhibitory range for several days. This is the most dangerous pharmacokinetic window because the virus replicates in the presence of drug, driving selection pressure for resistance mutations.

This is the pharmacokinetic basis for the RRI scoring system.

---

## 4. The Resistance Risk Index Logic

The RRI converts two separate variables into a single actionable score.

### Variable 1: Mutation Frequency

- Derived from NCBI GenBank sequence analysis
- Calculated as the number of KZN sequences carrying the mutation divided by total KZN sequences analysed
- Range: 0.0 to 1.0

### Variable 2: Pharmacokinetic Vulnerability Score

- Derived from the drug half-life model
- Calculated as the normalised duration of sub-inhibitory concentration window during a standard 24-hour missed dose scenario
- Longer half-life equals higher PVS, paradoxically more dangerous
- Range: 0.0 to 1.0

### The RRI Formula

RRI = Mutation Frequency x Pharmacokinetic Vulnerability Score

### Classification Thresholds

| RRI Score | Classification | Action |
|---|---|---|
| Above 0.75 | Critical | Immediate clinical surveillance priority |
| 0.50 to 0.75 | High | Enhanced patient monitoring |
| 0.25 to 0.50 | Moderate | Routine monitoring protocols |
| Below 0.25 | Low | Standard treatment protocol |

---

## 5. Data Sources

| Source | URL | Usage |
|---|---|---|
| NCBI GenBank | ncbi.nlm.nih.gov | Primary genomic sequence repository |
| Stanford HIVDB | hivdb.stanford.edu | Mutation resistance classification |
| EMBL-EBI | ebi.ac.uk | Secondary sequence validation |
| HXB2 Reference | GenBank K03455 | Alignment reference genome |

---

## 6. Literature Foundation & Pharmacokinetic Parameters

### 6.1 Primary Literature Citations

*   **Manasa, J., Danaviah, S., Pillay, S., et al. (2017).** *Pre-treatment HIV drug resistance in a rural South African community.* Journal of Antimicrobial Chemotherapy, 72(4), 1178–1184. 
    *   **Relevance:** Establishes the baseline molecular epidemiology in KwaZulu-Natal. Validates that the K103N mutation is the most prevalent pre-treatment non-nucleoside reverse transcriptase inhibitor (NNRTI) variant within rural KZN cohorts, demonstrating its high baseline frequency before first-line regimen initiation.
*   **Steegen, K., Lombard, Z., Bronze, M., et al. (2017).** *HIV-1 drug resistance in patients failing NNRTI-based combinations in South Africa.* AIDS Research and Human Retroviruses, 33(8), 789–798.
    *   **Relevance:** Confirms mutation profiles under selective drug pressure in South Africa. Validates that K103N occurs in $>60\%$ of NNRTI treatment failures, M184V occurs in $>70\%$ of lamivudine (3TC) failures, and K65R emerges predictably within tenofovir (TDF) backbones. 

### 6.2 Consolidated Pharmacokinetic Reference Values

The one-compartment open elimination model utilizes the standard first-order decay expression:

$$C(t) = C_0 \times e^{-K_e \times t}$$

Where the elimination rate constant ($K_e$) is derived via:

$$K_e = \frac{\ln(2)}{t_{1/2}}$$

The pipeline maps the primary first-line antiretroviral (ARV) modalities utilizing the following verified physiological constants:

| Drug Name | Class | Plasma Half-Life ($t_{1/2}$) | Intracellular Half-Life | Elimination Rate ($K_e$) | Minimum Effective Concentration (MEC) | Sub-Therapeutic Vulnerability Window |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Efavirenz (EFV)** | NNRTI | 40–55 hours | N/A | $0.0126–0.0173\text{ h}^{-1}$ | $\approx 1000\text{ ng/mL}$ | 3–7 days post-missed dose (High PVS) |
| **Tenofovir (TDF)** | NRTI | 17 hours | 50–60 hours | $0.0407\text{ h}^{-1}$ (plasma) | $\approx 40\text{ ng/mL}$ | 2–3 days post-missed dose (Moderate PVS) |
| **Lamivudine (3TC)** | NRTI | 5–7 hours | 18–22 hours | $0.0990–0.1386\text{ h}^{-1}$ | $\approx 20\text{ ng/mL}$ | 1–2 days post-missed dose (Low PVS) |

### 6.3 Methodological Paradox: The Long Half-Life Vulnerability
While standard clinical paradigms prize long drug half-lives for forgiving minor adherence lapses, the RRI framework accounts for the selective pressure window. Efavirenz’s prolonged plasma half-life ($40–55\text{ hours}$) creates a protracted, multi-day sub-inhibitory concentration tail during extended adherence breaks. 

During this sub-therapeutic window, viral replication resumes under sub-lethal drug pressure, rapidly selecting for high-fitness single-nucleotide polymorphisms (SNPs) such as K103N. This structural reality increases the Pharmacokinetic Vulnerability Score (PVS), elevating the overall risk index.

---

This document is a living methodology record and will be updated as the pipeline develops.

## 5. Half-Life Modifiers
### 5.1 Rifampicin and Dolutegravir
Multiplier: 0.46 (updated from 0.50). 
Derivation: AUC ∝ 1/CL, and AUC_rif / AUC_control = 0.46 (54% reduction)
⇒ CL_rif / CL_control = 1/0.46 = 2.174
t½ = ln(2)·V/CL, V assumed unchanged
⇒ t½_rif = 14 h × 0.46 = 6.4 h
Rifampicin induces UGT1A1 (principal), UGT1A9 and CYP3A4 (<10%).

### 5.2 Rifampicin and Efavirenz
Status: removed. South African data support use of efavirenz with rifampicin-based tuberculosis treatment without dose adjustment in that population, and CYP2B6 516G>T, which is common locally, is a larger determinant of efavirenz exposure than the rifampicin interaction.

### 5.3 St John's Wort
Multiplier: 1.0. Status: direction_only.

### 5.4 African Potato (Hypoxis hemerocallidea)
Multiplier: 1.0. Status: `no_effect` (no modelled effect). Separate input from St John's Wort. Evidence is largely in vitro and does not consistently support induction (some findings point to inhibition). A counselling prompt is retained.

### 5.5 Renal Function
Renal option taken: **(a) disable scaling pending an unsourced input.** The fixed per-category multipliers are removed and the input is a numeric eGFR. The eGFR-scaling formula t½_patient ≈ t½_normal × (90 / eGFR_patient) is recorded in `interactions.yaml` but `scaling_enabled: false`, because the per-drug `fraction_renally_cleared` term is unsourced (marked TODO — UNVERIFIED). Renal therefore does **not** modify the half-life or the resistance model; it is presented as a standalone accumulation-nephrotoxicity **safety** alert (fires at eGFR < 60), which is the physiologically relevant concern for tenofovir.

### 5.6 Paediatric Scaling
Allometric scaling: t½_child = t½_adult × (W / 70) ** 0.25 (0.68 at 15 kg, vs the v4.0 linear 0.43). Below `curve_min_age_months` (6) the allometric model is not applicable (UGT1A1 maturation) and the **decay curve is suppressed**. Implementation note / deviation: the WHO weight-band **dose** lookup is retained below six months (it explicitly doses infants from four weeks — e.g. 5 mg at 3–<6 kg, 10 mg at 6–<10 kg for 4 weeks to <6 months per IMPAACT P1093); suppressing guideline dosing for infants would be a safety regression, so only the modelled curve is suppressed, not the dose. Flagged for reviewer confirmation.

## 17. Correction Table

Maps the methodology §17 corrections to the commit that addressed each. Stages 4–7 items are pending.

| # | Item | Stage | Commit |
|---|---|---|---|
| 1 | Paediatric DTG bands (WHO 5/15/20/25/30; age split) | 1, 1b | 97b121d, d8505a4 |
| 2 | DTG threshold 0.50 → 0.064 mg/L PA-IC90 | 1 | 97b121d |
| 3 | NRTI compartment: plasma → intracellular anabolite (tier B) | 2, 3 | eba20f6, 776fb9c |
| 4 | Mutation probability (fabricated %) removed | 1 | 97b121d |
| 5 | Audit hash: real SHA-256 chain | 1 | 97b121d |
| 6 | Efavirenz threshold 0.51 → 1.0 mg/L | 1 | 97b121d |
| 7 | Risk direction (monotherapy = highest) | 4 | pending |
| 8 | Rifampicin mechanism → UGT1A1 principal | 3 | 776fb9c |
| 9 | DTG dose-doubling applied to the curve (BD) | 3 | 776fb9c |
| 10 | Herbals separated (SJW / African Potato) | 3 | 776fb9c |
| 11 | Hypoxis FBC-on-TDF advice removed | 1b | d8505a4 |
| 12 | Paediatric scaling linear → allometric ^0.25 | 3 | 776fb9c |
| 13 | MIC terminology → PA-IC90 / threshold (key rename) | 1b, 6 | d8505a4, pending |
| 14 | Genetic barrier in mutation index | 4 | pending |
| 15 | Adherence model → support-needs framing | 5 | pending |
| 16 | Efavirenz–rifampicin 0.74 multiplier removed | 3 | 776fb9c |
| 17 | Renal fixed multipliers → numeric eGFR (scaling disabled) | 3 | 776fb9c |
| 18 | Timestamps → Africa/Johannesburg, store UTC | 1 | 97b121d |
| 19 | Log axis clamped at LLOQ | 3 | 776fb9c |
| 20 | Resistance-window shading (0.85×–1.3×) removed | 7 | pending |
| 21 | HTML injection escaped (html.escape) | 1 | 97b121d |
| 22 | Visitor counter removed | 1 | 97b121d |
| 23 | Unimplemented integration claims removed | 1 | 97b121d |
