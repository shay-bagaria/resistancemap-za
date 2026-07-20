# ResistanceMap ZA — Methodology

**Document version:** 1.0
**Corresponds to:** ResistanceMap ZA v5.0 (specification; supersedes v4.0 as built)
**Status:** Research prototype. Not validated. Not a medical device.
**Author contact:** sbagaria2009@gmail.com

This is the authoritative methodology. It supersedes the earlier v0.1 genomic
draft. "As built" notes and the §17 commit column record the code that implements
each specified correction.

---

## 0. How to read this document

This document specifies every number the application produces. For each quantity it gives the formula, the inputs, the origin of each constant, a classification of how much confidence the quantity carries, and a worked example that a reviewer can check by hand.

Each computed quantity carries one of three confidence classifications, which appear both here and on screen next to the number:

| Class | Meaning |
|---|---|
| **A — Derived** | Computed from a published pharmacokinetic or pharmacodynamic parameter with a citation. The formula is standard. Uncertainty comes from population variability, not from the model structure. |
| **B — Ordinal** | The direction and ordering are defensible; the absolute value is not. Reported as a rank or category, never as a number implying precision. |
| **C — Heuristic** | Hand-assigned weights chosen for demonstration. No validation. Present for interface completeness. Must be labelled as such wherever displayed. |

Nothing in this application is class A end-to-end. The pharmacokinetic decay for dolutegravir and efavirenz is class A; everything built on top of it is class B or C.

---

## 1. What the system does and does not do

### 1.1 Scope

ResistanceMap ZA estimates, for a patient on a known antiretroviral regimen who has missed a known number of days of doses, which components of that regimen are likely to have fallen below their efficacy threshold, and whether the resulting pattern of remaining drug creates conditions favouring selection of resistant virus.

### 1.2 What it does not do

It does not analyse genetic sequence data. It does not detect mutations. It does not predict which mutation a given patient carries. Where mutation names appear, they identify the mutation most commonly associated with failure of that drug in the published literature, not a finding about the patient in front of the clinician.

It does not measure drug concentrations. Every concentration displayed is a model output from population-average parameters, not a measurement of the patient.

It is not a diagnostic. It is not a prescribing tool. It has not been validated against any patient outcome dataset.

### 1.3 Intended use

Teaching, illustration of pharmacokinetic principles, and as a specification against which a future retrospective validation study could be run.

---

## 2. Notation

| Symbol | Meaning | Units |
|---|---|---|
| t | Hours elapsed since the last ingested dose | h |
| t½ | Elimination half-life of the relevant moiety | h |
| ke | First-order elimination rate constant | h⁻¹ |
| C(t) | Modelled plasma concentration at time t | mg/L |
| Cmax,ss | Steady-state peak plasma concentration | mg/L |
| Cthresh | Efficacy threshold concentration | mg/L |
| IQ(t) | Inhibitory quotient, C(t) ÷ Cthresh | dimensionless |
| f(t) | Fraction of steady-state exposure remaining | dimensionless |
| W | Patient body weight | kg |

---

## 3. The pharmacokinetic model

### 3.1 Governing equation

Elimination is modelled as a single-compartment first-order process:

```
ke   = ln(2) / t½
C(t) = Cmax,ss · e^(−ke · t)
```

### 3.2 Assumptions, and what each one costs

| Assumption | Consequence |
|---|---|
| Single compartment | Real antiretroviral disposition is multi-phasic. Tenofovir plasma decay in particular is triphasic. A single exponential misfits both the early distribution phase and the terminal phase. |
| Decay begins at Cmax,ss | Ignores absorption. Concentrations in the first two to four hours are overestimated. |
| Population-average parameters | Efavirenz clearance varies several-fold with CYP2B6 genotype, and the 516G>T variant is common in South African populations. An individual patient may sit far from the modelled curve. |
| No accumulation modelling on restart | The model describes decay after cessation only. It says nothing about time to re-suppression after doses resume. It also does not simulate the inter-dose sawtooth, so a twice-daily schedule is represented by the adjusted half-life plus an annotation, not a re-dosing profile. |
| Adherence is a single integer | Real non-adherence is intermittent. A patient who takes four doses in seven days is not equivalent to a patient who takes none for three days, but the model cannot distinguish them. |

The last assumption is the largest limitation in practice. Intermittent partial adherence is the pattern most associated with resistance selection, and the current input model cannot represent it.

### 3.3 Compartment selection: the two-tier structure

Antiretrovirals in this application fall into two groups that cannot be modelled the same way.

**Tier A — drugs acting as the parent compound in plasma.** Dolutegravir and efavirenz inhibit their targets directly. Plasma concentration is the pharmacologically meaningful quantity, published efficacy thresholds exist in plasma units, and absolute concentrations can be modelled and compared to those thresholds.

**Tier B — nucleoside and nucleotide analogue prodrugs.** Tenofovir, lamivudine and abacavir are inactive as administered. Each is taken into the cell and phosphorylated by host kinases to an active anabolite: tenofovir diphosphate, lamivudine triphosphate, and carbovir triphosphate respectively. The active moiety is intracellular and persists far longer than the parent compound persists in plasma.

The difference is large:

| Drug | Plasma t½ | Active moiety | Intracellular t½ |
|---|---|---|---|
| Tenofovir | ~17 h | TFV-DP | 48 h to >100 h in PBMC, depending on study and compartment |
| Lamivudine | 5–7 h | 3TC-TP | ~10.5–16 h |
| Abacavir | ~1.5 h | Carbovir-TP | long enough to support once-daily dosing |

Abacavir illustrates why this matters. Its plasma half-life of roughly 1.5 hours cannot support once-daily dosing on its own. The reason abacavir is dosed once daily is the persistence of carbovir triphosphate inside the cell.

**The v4.0 application modelled all five drugs in plasma.** This produced a decay curve for abacavir that fell to nothing within a few hours of a missed dose, and made tenofovir appear far less forgiving of imperfect adherence than it is. The published position is the opposite: long intracellular half-lives are the source of what the pharmacology literature calls pharmacokinetic forgiveness.

### 3.4 Why tier B is reported as relative exposure, not absolute concentration

An obvious fix would be to substitute intracellular half-lives into the same equation. This is not valid, for two reasons.

Intracellular anabolite concentrations are reported in femtomoles per million cells, not milligrams per litre. There is no conversion to plasma units.

There is no clinically established intracellular efficacy threshold for these anabolites analogous to a protein-adjusted IC90. Thresholds that exist, such as the TFV-DP concentrations used in pre-exposure prophylaxis adherence monitoring, are adherence benchmarks derived from directly observed dosing studies, not inhibitory concentrations.

So tier B drugs are modelled as **fraction of steady-state active-moiety exposure remaining**:

```
f(t) = e^(−ke,intracellular · t)
```

This is reported as a percentage of steady state and classified as **class B, ordinal**. No inhibitory quotient is computed for tier B drugs, and no absolute concentration is displayed. The interface must not present a tier B drug as "below MIC" or "below threshold", because the model cannot support that claim.

**As built.** `engine/pk.py` keeps the separation structural: `exposure_fraction_at(t, t½)` takes no threshold argument, so no inhibitory quotient can be formed for tier B. On the interface, tier B drugs are plotted only as f(t) on the exposure subplot and never as an absolute concentration on the plasma subplot.

The consequence for the regimen state classification in section 6 is set out there.

---

## 4. Drug parameter table

All values below are population averages for adults at steady state on standard dosing. Values live in `data/drugs.yaml`; each numeric value carries a `source`, and entries whose value is unsourced carry `source: "TODO — UNVERIFIED"` with the existing number preserved.

### 4.1 Dolutegravir (INSTI, tier A)

| Parameter | Value | Source |
|---|---|---|
| Plasma terminal t½ | 13–14 h | Cottrell, Hadzic & Kashuba, *Clin Pharmacokinet* 2013;52(11):981–94 |
| Cmax,ss (50 mg once daily) | 2.34 mg/L (IQR 1.84–3.04) | ClinicalTrials.gov NCT02924389, reported steady-state median |
| Cmin,ss (trough) | 0.56–0.83 mg/L | NCT02924389; Thai paediatric comparator study, *Pediatr Infect Dis J* 2024 |
| PA-IC90 (wild type) | **0.064 mg/L** | Cottrell et al. 2013; used as the primary target in Wasserman et al., *AAC* 2022;66(7) |
| Secondary target (EC90) | 0.3 mg/L | Wasserman et al., *AAC* 2022, citing the phase IIb 10 mg dose-ranging trough |
| Genetic barrier | High | Established in the INSTI literature |
| Signature mutation | R263K | |

**The v4.0 application used 0.50 mg/L as the dolutegravir threshold.** The published PA-IC90 is 0.064 mg/L. The v4.0 value is approximately eight times too high, which caused the model to declare dolutegravir sub-therapeutic at concentrations that are in fact well above the inhibitory target. Because dolutegravir is the anchor drug of the TLD regimen used by most patients in South Africa, this single constant inverted the model's conclusion for the most common clinical scenario.

The system uses 0.064 mg/L as the primary threshold and displays 0.3 mg/L as a secondary reference line, since the more conservative target has been proposed as the effective concentration for 90% response.

### 4.2 Efavirenz (NNRTI, tier A)

| Parameter | Value | Source |
|---|---|---|
| Plasma t½ | TODO — UNVERIFIED. The v4.0 value of 52 h is within the commonly quoted range but has not been traced to a primary source. Efavirenz half-life is strongly genotype-dependent. | |
| Mid-dose C, typical | 2.2–2.3 mg/L median (IQR approx. 1.5–4.6) | Sinxadi et al., *Int J Antimicrob Agents* 2016, South African cohort |
| Lower therapeutic threshold | **1.0 mg/L** | Recommended range 1–4 mg/L, Kappelhoff et al., *Clin Pharmacokinet* 2007;46(2):93–108 |
| Alternative empirical threshold | 0.7 mg/L | Sinxadi et al. 2016 found 0.7 mg/L most predictive of non-suppression in a South African cohort |
| Genetic barrier | Low | Single-mutation resistance is well documented |
| Signature mutation | K103N | |

**The v4.0 application used 0.51 mg/L.** The widely used lower therapeutic limit is 1.0 mg/L, with concentrations below that strongly associated with virological failure. In one South African cohort the odds ratio for virological failure with efavirenz below 1 mg/L was 12.5 (95% CI 2.7–57.3).

The system uses 1.0 mg/L as the threshold and displays 0.7 mg/L as a secondary line. Cmax,ss 4.07 mg/L and t½ 52 h remain UNVERIFIED (§18).

### 4.3 Tenofovir disoproxil fumarate (NRTI prodrug, tier B)

| Parameter | Value | Source |
|---|---|---|
| Plasma t½ | ~17 h single dose; terminal median 69 h (IQR 58–77) reported in a radiolabelled single-dose study | Louissaint et al., *AIDS Res Hum Retroviruses* 2013 |
| Active moiety | Tenofovir diphosphate (TFV-DP) | |
| TFV-DP t½, PBMC | 48 h (range 38–76) in one single-dose study; 3–4 days elsewhere; in excess of 60–100 h in others | Louissaint et al. 2013; Anderson et al., *AAC* 2018 |
| Modelled value | 48 h, PBMC compartment | Chosen as the shortest defensible value, so the model errs towards flagging risk |
| Genetic barrier | Intermediate | |
| Signature mutation | K65R | |

The spread of published values here is a genuine finding rather than a gap in sourcing. Any single number is a simplification, and this is stated on the interface.

### 4.4 Lamivudine (NRTI prodrug, tier B)

| Parameter | Value | Source |
|---|---|---|
| Plasma t½ | 5–7 h in HIV-infected subjects (lower bound 5 h used in the model) | GSK clinical protocol for NCT00214890 |
| Active moiety | Lamivudine triphosphate (3TC-TP) | |
| 3TC-TP intracellular t½ | ~15–16 h in PBMC from HIV-infected subjects; modelled value 16 h | Hawkins et al., *JAIDS* 2005;39(4):406–11 |
| Genetic barrier | Low | M184V emerges rapidly under lamivudine pressure |
| Signature mutation | M184V | |

Note: the lamivudine anabolic pathway has a saturable diphosphate-to-triphosphate step, allowing the diphosphate to pool. Triphosphate can therefore continue to form after plasma concentrations have fallen. A simple exponential decay from the missed dose underestimates persistence.

### 4.5 Abacavir (NRTI prodrug, tier B)

| Parameter | Value | Source |
|---|---|---|
| Plasma t½ | ~1.5 h | TODO — UNVERIFIED |
| Active moiety | Carbovir triphosphate (CBV-TP) | |
| CBV-TP intracellular t½ | TODO — UNVERIFIED. Read from Hawkins et al. 2005 or Moyle et al., *AAC* 2009;53(4):1532–8 before use. | |
| Genetic barrier | Intermediate | |
| Signature mutation | L74V | |

Until the carbovir triphosphate half-life is sourced, abacavir carries `curve_available: false`: no decay curve, no concentration, no threshold-breach alert. Displaying a curve driven by the 1.5 h plasma value would repeat the v4.0 error.

### 4.6 Lower limit of quantification

Each drug carries an assay lower limit of quantification. Below this value the model output is displayed as "below limit of quantification" rather than as a number. This exists for a mathematical reason as well as an honest one: an unbounded logarithmic axis would otherwise span dozens of empty decades. Default value: 1 × 10⁻⁴ mg/L, marked class C.

**As built.** `clamp_to_lloq` in `engine/pk.py`; tier A plasma curves are clamped at the LLOQ and the status panel shows "below limit of quantification" when clamped.

---

## 5. Half-life modifiers

Each modifier adjusts the elimination rate for a named drug, applied multiplicatively to t½. Constants live in `data/interactions.yaml`.

### 5.1 Rifampicin and dolutegravir — **Class A**

Rifampicin induces UGT1A1, UGT1A9 and CYP3A4. In healthy adults co-administration reduces dolutegravir AUC by 54%, Cmax by 43%, and trough by 72%.

**Mechanism correction.** The v4.0 alert attributed this to CYP3A4 induction alone. Dolutegravir is metabolised principally by glucuronidation through UGT1A1, with CYP3A4 contributing less than 10%.

Derivation of the half-life multiplier, volume of distribution assumed unchanged:

```
AUC ∝ 1 / CL
AUC_rif / AUC_control = 0.46  ⇒  CL_rif / CL_control = 1/0.46 = 2.174
t½ = ln(2) · V / CL  ⇒  t½_rif / t½_control = 0.46  ⇒  t½_rif = 14 h × 0.46 = 6.44 h
```

**Dosing.** Management is dolutegravir 50 mg twice daily; BD with rifampicin achieves AUC/trough ~18–33% above once-daily without rifampicin.

**As built.** Multiplier 0.50 → 0.46 (commit 776fb9c). The BD schedule is annotated on the curve; the inter-dose sawtooth is not simulated (§3.2).

### 5.2 Rifampicin and efavirenz — **removed**

The v4.0 application applied a 0.74 multiplier. This is not supported by South African evidence: efavirenz can be used with rifampicin-based TB treatment without dose adjustment in that population, and CYP2B6 516G>T is a larger determinant of exposure than the interaction.

**As built.** Multiplier removed; replaced with an informational note (commit 776fb9c).

### 5.3 St John's Wort — **Class B, direction only**

*Hypericum perforatum* contains hyperforin, an inducer of CYP3A4 and P-glycoprotein. Direction of effect is established; magnitude for dolutegravir is unsourced.

**As built.** Separate input, multiplier 1.0, `status: direction_only`. Qualitative warning, no percentage (commit 776fb9c).

### 5.4 African Potato (*Hypoxis hemerocallidea*) — **Class C, no modelled effect**

The evidence base for *Hypoxis* is thinner than for St John's Wort, largely in vitro, and inconsistent on direction (some findings point to inhibition). The v4.0 build combined it with St John's Wort and asserted a 30–35% reduction, and advised FBC monitoring "if on TDF" on a bone-marrow-suppression basis — a zidovudine concern, not tenofovir.

**As built.** Separate input, multiplier 1.0, `status: no_effect`; counselling prompt retained; the FBC/bone-marrow line is deleted (commits d8505a4, 776fb9c).

### 5.5 Renal impairment — **Class C, scaling disabled**

The v4.0 model multiplied half-life by 1.15/1.40/1.85 per category, with no traced source. The physiologically appropriate approach scales clearance with eGFR:

```
t½_patient ≈ t½_normal × (eGFR_reference / eGFR_patient),  eGFR_reference = 90
```

This requires a fraction-renally-cleared term per drug, since only the renally cleared portion scales this way — and that term is unsourced (TODO).

**Renal option taken: (a) disable scaling pending the unsourced input.** The input is a numeric eGFR. The scaling formula is recorded in `interactions.yaml` with `scaling_enabled: false`, so renal does **not** modify the half-life or the resistance model. The clinical significance of renal impairment on tenofovir is accumulation-driven nephrotoxicity, not loss of efficacy, so renal is presented as a standalone **safety** alert (fires at eGFR < 60), separate from the resistance model (commit 776fb9c).

### 5.6 Paediatric weight adjustment — **Class B**

The v4.0 model used a linear factor `max(0.6, min(1.0, W/35))`. Paediatric clearance does not scale linearly. Standard allometric scaling gives:

```
t½_child = t½_adult × (W / 70)^0.25
```

At W = 15 kg this gives 0.68, against the v4.0 linear 0.43.

Allometric scaling does not capture enzyme maturation, which matters most in the first months of life (UGT1A1 matures within 3–6 months). The **decay curve** is therefore suppressed below six months.

**As built / deviation.** Curve suppressed below `curve_min_age_months` (6). The WHO weight-band **dose** lookup is *retained* below six months, because WHO/IMPAACT P1093 explicitly dose infants from four weeks (5 mg at 3–<6 kg; 10 mg at 6–<10 kg for 4 weeks to <6 months, 15 mg from 6 months). Suppressing guideline dosing for infants would be a safety regression, so only the modelled curve is suppressed, not the dose (commits d8505a4, 776fb9c). Reviewer confirmed this call in Stage 4.

---

## 6. Paediatric dolutegravir dosing bands — **Class A**

WHO weight-band dosing for dolutegravir dispersible tablets, in `data/rules.yaml`:

| Weight band | Age | Dose |
|---|---|---|
| 3 to <6 kg | ≥4 weeks | 5 mg |
| 6 to <10 kg | 4 weeks to <6 months | 10 mg |
| 6 to <10 kg | ≥6 months | 15 mg |
| 10 to <14 kg | | 20 mg |
| 14 to <20 kg | | 25 mg |
| ≥20 kg | | 30 mg dispersible, or 50 mg film-coated |

Source: WHO weight-band recommendations (IMPAACT P1093 + ODYSSEY population-PK analysis, PENTA-ID; Waalewijn et al., *Lancet HIV* 2020; Turkova et al., *Lancet HIV* 2022). Below four weeks, or outside the source table, no dose is shown and a referral message is displayed.

**The v4.0 ladder under-dosed every band above 6 kg** (10/15/20/25 vs WHO 15/20/25/30) and computed the next boundary as `weight + 5` rather than a lookup. Both are corrected (commits 97b121d, d8505a4).

---

## 7. The efficacy threshold and the inhibitory quotient — **Class A, tier A only**

### 7.1 Terminology correction

The v4.0 application used MIC throughout. Minimum inhibitory concentration is a bacteriology term and does not apply to antiretrovirals, which are assessed by inhibitory concentration values from cell culture (IC50, IC90, and protein-adjusted forms). The internal `mic` key was renamed `threshold_mg_L`; the user-facing terminology sweep completes in Stage 6.

### 7.2 Definition

For tier A drugs:

```
IQ(t) = C(t) / Cthresh
```

An inhibitory quotient above 1 indicates the modelled concentration exceeds the efficacy target.

### 7.3 Worked example

Patient on TLD. Last dose 72 hours ago. No modifiers.

```
Dolutegravir
  t½      = 14 h
  ke      = ln(2) / 14 = 0.0495105 h⁻¹
  Cmax,ss = 2.34 mg/L
  C(72)   = 2.34 × e^(−0.0495105 × 72)
          = 2.34 × e^(−3.564757)
          = 2.34 × 0.028304
          = 0.066231 mg/L
  IQ(72)  = 0.066231 / 0.064 = 1.03
```

Tests should assert against these figures with a relative tolerance of 1e-4. The modelled concentration is marginally above the PA-IC90 at three days. Against the more conservative 0.3 mg/L target it fell below at:

```
t = ln(2.34 / 0.3) / 0.0495105 = 2.0541 / 0.0495105 = 41.5 h
```

So the interface reports dolutegravir as above PA-IC90 but below the secondary EC90 target, having crossed that lower line at approximately 41.5 hours.

Under the v4.0 threshold of 0.50 mg/L, the same patient's dolutegravir would have been declared sub-inhibitory from about 15 hours after the missed dose. That is the practical cost of the incorrect constant.

---

## 8. Regimen state classification — **Class B.** This is the primary output.

### 8.1 Rationale

The v4.0 risk model treated "all drugs cleared" as maximum risk and awarded 15 points for each drug below threshold. This inverts the mechanism.

Resistance is selected when a resistant variant has a fitness advantage over wild-type. That requires drug present at a concentration that suppresses wild-type but not the resistant variant. With no drug present there is no differential advantage: wild-type, generally fitter without drug, rebounds. The clinical outcome is bad, but the resistance outcome is not.

The condition of concern is **functional monotherapy**: one component remaining active while the others have cleared. This is why a treatment interruption on a regimen containing a long-half-life NNRTI is a recognised concern.

### 8.2 Classification

At each hour t, let A(t) be the set of regimen components still active, and n the total number of components.

For tier A drugs, active means IQ(t) ≥ 1.
For tier B drugs, active means f(t) ≥ 0.25, i.e. at least a quarter of steady-state active-moiety exposure remains. **This 0.25 cut-off is class C, hand-chosen, and is the weakest element in the primary output.** It is labelled class C on the interface, adjacent to the band, and is the first thing a reviewer should comment on.

| \|A(t)\| | State | Interpretation |
|---|---|---|
| n | FULL_SUPPRESSION | All components active |
| 2 to n−1 | PARTIAL_SUPPRESSION | Reduced barrier to resistance |
| 1 | FUNCTIONAL_MONOTHERAPY | Highest resistance selection risk |
| 0 | NO_PRESSURE | Viral rebound risk; minimal selection pressure |

**Abacavir / indeterminate case.** A drug with `curve_available: false` (abacavir) counts as neither active nor inactive: no curve, no f(t). For a regimen containing such a component the state is reported as **INDETERMINATE** rather than guessed.

**As built** (commit 159bfc3). `engine/selection.py`: `classify`, `state_series`, `monotherapy_window`, `worst_state`. The state band renders beneath the decay curves with the class C cutoff label adjacent; the ABC/3TC/DTG regimen returns INDETERMINATE at every hour and the composite band is Indeterminate for it.

### 8.3 Display

The state is rendered as a coloured band along the time axis beneath the decay curves, so the duration and position of any monotherapy window is directly visible. The system reports the start time, end time and duration of the monotherapy window when one exists. The 0.25 cut-off's class C label sits adjacent to the band.

### 8.4 Worked example

Patient on TLE (tenofovir, lamivudine, efavirenz), 14 days missed, no modifiers:

- Lamivudine, 3TC-TP t½ 16 h. f falls below 0.25 at ~32 h.
- Tenofovir, TFV-DP t½ 48 h. f falls below 0.25 at t = ln(4)/(ln2/48) = 96 h.
- Efavirenz, plasma t½ 52 h (unverified), Cmax,ss 4.07 (unverified), threshold 1.0 mg/L. Falls below threshold at t = ln(4.07)/(ln2/52) ≈ 105 h.

| Window | Active components | State |
|---|---|---|
| 0–32 h | TFV, 3TC, EFV | FULL_SUPPRESSION |
| 32–96 h | TFV, EFV | PARTIAL_SUPPRESSION |
| 96–105 h | EFV only | **FUNCTIONAL_MONOTHERAPY** |
| 105 h onward | none | NO_PRESSURE |

A monotherapy window of roughly nine hours. The width is highly sensitive to the tier B cut-off and to the unverified efavirenz parameters, so the number of hours is not a finding. The existence and ordering of the window is the finding.

### 8.5 TLD produces a tenofovir monotherapy window too

TLE is not the only regimen with a monotherapy window; TLD does too, with a different mechanism. Patient on TLD, no modifiers:

- Lamivudine, 3TC-TP t½ 16 h. f falls below 0.25 at t = ln(4)/(ln2/16) = 32 h.
- Dolutegravir, plasma t½ 14 h, Cmax,ss 2.34 mg/L, PA-IC90 0.064 mg/L. IQ falls below 1 at t = ln(2.34/0.064)/(ln2/14) ≈ 72.7 h.
- Tenofovir, TFV-DP t½ 48 h. f falls below 0.25 at t = ln(4)/(ln2/48) = 96 h.

| Window | Active components | State |
|---|---|---|
| 0–32 h | TFV, 3TC, DTG | FULL_SUPPRESSION |
| 32–73 h | TFV, DTG | PARTIAL_SUPPRESSION |
| 73–96 h | TFV only | **FUNCTIONAL_MONOTHERAPY** |
| 96 h onward | none | NO_PRESSURE |

Dolutegravir crosses its inhibitory threshold (≈73 h) before tenofovir's exposure fraction falls below the tier B cut-off (96 h), because DTG's plasma t½ (14 h) is much shorter than TFV-DP's intracellular t½ (48 h), even though DTG has the higher genetic barrier. So the anchor drug of the regimen is not the last one standing — the NRTI backbone outlasts it. This is the pharmacokinetic-forgiveness point from §3.3 in reverse: the same long intracellular persistence that protects against missed doses also creates a tenofovir-alone window once the anchor drug has cleared.

### 8.6 The tier B cut-off sweep is non-monotonic, not just sensitive

Sweeping the tier B activity cut-off for the §8.4 TLE example gives:

| Cut-off | Monotherapy window | Width | Surviving drug |
|---|---|---|---|
| 0.1 | 106–159 h | 54 h | Tenofovir |
| 0.2 | 106–111 h | 6 h | Tenofovir |
| 0.25 | 97–105 h | 8 h | Efavirenz |
| 0.3 | 84–105 h | 21 h | Efavirenz |
| 0.4 | 64–105 h | 41 h | Efavirenz |
| 0.5 | 49–105 h | 56 h | Efavirenz |

Width does not vary monotonically with the cut-off: it falls from 54 h to 6 h between 0.1 and 0.2, then rises again to 56 h between 0.25 and 0.5. There is a single monotherapy episode at every cut-off — the non-monotonicity is not caused by a second episode appearing. It is caused by a **swap in which drug is the survivor**.

Efavirenz's IQ = 1 crossing is fixed at ≈105.3 h regardless of the tier B cut-off (it is tier A). Tenofovir's exposure-fraction crossing moves with the cut-off: t = ln(1/cutoff) / (ln2/48). The two curves cross each other at a **critical cut-off of ≈0.219** — solving ln(1/c)·48/ln2 = 105.3 h. Above that critical value (cut-off ≥ 0.25 in the swept set) tenofovir falls out first and efavirenz is the lone survivor until its own fixed crossing at 105.3 h, so the window widens as the cut-off rises (tenofovir exits earlier, leaving efavirenz alone for longer). Below the critical value (cut-off ≤ 0.2) efavirenz clears first at its fixed 105.3 h and tenofovir — now taking longer to fall below the more lenient cut-off — becomes the survivor instead, so the window widens as the cut-off falls further (tenofovir now persists as the sole active drug for longer past 105.3 h). At the critical cut-off itself the window width goes to zero: the two crossings coincide and there is a single instant, not a window, at which the state passes directly from PARTIAL_SUPPRESSION to NO_PRESSURE.

This is stronger evidence of structural sensitivity than a monotonic "wider cut-off, wider window" relationship would be: the *identity* of the drug driving the resistance-selection warning changes with an unsourced constant, not merely the duration of the warning. A clinician reading "efavirenz monotherapy" versus "tenofovir monotherapy" would reasonably reach for different second-line reasoning (K103N versus K65R), and which one the model reports depends on a cut-off this document cannot source. The §14 sensitivity analysis should therefore report, for each swept cut-off, not just window width but which component survives, and should treat a change in surviving component as a finding in its own right, distinct from a change in width.

---

## 9. Mutation risk index — **Class B, ordinal**

### 9.1 What changed

The v4.0 application computed `risk_pct = 45 + days_missed * 4` (and three sibling branches) and displayed the result as a probability against a 50% "clinical threshold". No derivation, no calibration, no validation. A decision support system presenting a fabricated number as a probability is the failure mode that discredits the category. The percentage output was removed.

### 9.2 Replacement

For each drug, a four-level ordinal index combining two ordered inputs.

**Exposure level** over the elapsed window:

| Condition | Level |
|---|---|
| Active throughout | 0 |
| Fell below threshold during the window | 1 |
| Sole active agent at any point (functional monotherapy) | 2 |

**Genetic barrier** (read from `genetic_barrier` in `drugs.yaml`):

| Barrier | Level |
|---|---|
| High (dolutegravir) | 0 |
| Intermediate (tenofovir, abacavir) | 1 |
| Low (lamivudine, efavirenz) | 2 |

Index = exposure level + barrier level, mapped: 0 → Minimal, 1 → Low, 2 → Moderate, 3–4 → High. Displayed with the contributing levels itemised, and labelled "Ordinal heuristic. Not a probability. Not validated against outcome data."

**As built** (commit 159bfc3). `engine/selection.py`: `exposure_level`, `barrier_level`, `mutation_index`. Barrier is read from `genetic_barrier` in `drugs.yaml`. Because barrier is a standing property, a low-barrier drug (3TC, EFV) reads at least Moderate even when suppressed — this is intended (§9.3).

### 9.3 Why genetic barrier must be included

The v4.0 model gave every drug the same risk curve. M184V emerges readily under lamivudine pressure; R263K under dolutegravir is rare, and dolutegravir's high barrier is a principal reason it anchors first-line treatment. Treating those two as equally likely at the same inhibitory quotient misrepresents the pharmacology.

---

## 10. Composite score — **Class C**

### 10.1 The v4.0 formula

The v4.0 score summed `days_missed*6 + len(below_mic)*15 + len(vulnerable)*10 + 12·TB + 8·herbal + 10·(VL>1000) + 8·(CD4<200) + 5·paediatric`, capped at 100. Problems: the below-threshold term rewarded the lower-risk state (§8.1); `days_missed*6` saturated the score on one input; weights unsourced; the "n/100" gauge implied calibration; and paediatric status is not a resistance risk factor.

### 10.2 Replacement

```
composite = w_state × state_severity
          + w_mut   × max(mutation_index across drugs)
          + w_vl    × viral_load_band
          + w_immune × cd4_band
```

with `state_severity` from §8, ordered so FUNCTIONAL_MONOTHERAPY carries the highest weight. Paediatric status is removed. Tuberculosis co-infection and herbal use are removed as direct terms, since their effect already enters through the decay curves; double-counting them inflates the score. Weights remain hand-chosen, in `data/rules.yaml`, class C. The output is an ordinal band, not a number out of 100, with the class C label adjacent to the value.

**As built, Stage 4** (commit 159bfc3). `state_severity` used the *worst* state over the elapsed window [0, hours_missed]. This saturated: once any monotherapy hour had occurred, the worst-ever state was pinned at FUNCTIONAL_MONOTHERAPY for every later hour, so TLD read the same "High" band at 3, 7 and 14 days missed — the composite could not distinguish a three-day defaulter from a fortnight one. This is the same failure shape as the v4.0 `days_missed × 6` term, reached by a different route.

**As built, Stage 5 recalibration** (commit — see §17). `state_severity` now uses the **current** classified state at `hours_missed`, not the worst state ever reached. This is not a loss of information: the cumulative "did this ever happen" signal is still carried by the mutation index, whose exposure level is explicitly defined over "the elapsed window" / "at any point" (§9.2), so a component that was once the sole active agent keeps a high mutation index even after the whole regimen has cleared. Splitting the two terms this way — state reflecting *live* risk, mutation index reflecting *historical* risk — lets the composite fall again once a regimen has fully cleared, which is correct: full clearance is NO_PRESSURE (§8.1, low resistance-selection risk), not the peak, even though it carries a real and separately-flagged rebound risk. Weights changed from `state:3, mutation:2, viral_load:1, immune:1` to `state:3, mutation:1, viral_load:1, immune:1`, and the bands were retuned from `0/3/7/11` to `0/6/10/13` against the required scenario matrix (TLD at 0/1/3/5/7/14 days missed, TLE at 0/3/7/14, each with and without rifampicin, default labs). The resulting raw scores span {4, 8, 9, 11, 14} and reach all four bands: Minimal (day 0–1, both regimens), Moderate (day 3 partial suppression), High (TLD day 3 with rifampicin — the tenofovir/dolutegravir-crossing monotherapy window of §8.5, reached earlier because rifampicin shortens DTG's half-life), and Low (every scenario once the regimen has fully cleared, day 5 onward for TLD, day 7 onward for TLE). The full per-scenario table is in the Stage 5 commit message and the final report.

---

## 11. Adherence and support needs — **Class C**

The v4.0 model scored socio-economic disadvantage (unemployment, walking, non-disclosure, etc.) into a "VERY HIGH RISK" label with an itemised chart. Objections: it encodes poverty as patient risk; non-disclosure carries safeguarding weight and should not be a scored demerit on a shared screen; and the explanation shown to the patient is a ranked list of their disadvantages.

Replacement (Stage 5): a clinical risk panel from PK/lab inputs, and a separate support-needs panel expressing socio-economic inputs as service entitlements (multi-month dispensing, transport support, community-health-worker contact, nutritional referral). Non-disclosure contributes no score and gets no itemised display. The itemised contribution chart is not rendered in any patient-visible view.

---

## 12. Clinical directive rules — **mixed, each rule carries its class**

| Rule | Trigger | Class |
|---|---|---|
| Dolutegravir dose doubling (BD) | Rifampicin | A |
| Rifampicin mechanism (UGT1A1 principal) | Rifampicin | A |
| Efavirenz with rifampicin (informational) | Rifampicin | B |
| Paediatric weight band | Paediatric | A |
| Renal safety | eGFR < 60 | C |
| St John's Wort (direction only) | SJW | B |
| African Potato (counselling only) | Hypoxis | C |
| Regimen state / monotherapy window | §8 state | B |

Every directive rendered on screen displays its class and the ruleset version.

---

## 13. Audit trail — **Class A (standard cryptography)**

The v4.0 `hash()` labelled `SHA256:` was a non-cryptographic, per-process-randomised hash, and the "log" was rebuilt each rerun with synthetic timestamps. Replaced with an append-only chain:

```python
def chain_entry(prev_hash, entry):
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev_hash + payload).encode("utf-8")).hexdigest()
```

This is tamper *evidence*, not tamper proofing: an actor with write access can rebuild the chain. The interface claims only tamper evidence. Timestamps display in Africa/Johannesburg and store UTC. Full SQLite persistence is scheduled for Stage 6.

---

## 14. Validation status

Nothing in this application has been validated against patient outcomes. The proposed retrospective cohort study would ask whether the presence and duration of a modelled functional monotherapy window predicts subsequent virological failure (VL > 1000 copies/mL) better than days-missed alone, with sensitivity analyses across the tier B cut-off, the TFV-DP half-life range, and efavirenz parameters. It would require research ethics approval (UKZN BREC) and provincial Department of Health approval.

---

## 15. Data protection

Under POPIA (Act 4 of 2013), health information is special personal information. The combination of facility, clinician code, weight, CD4, viral load, regimen and distance is likely re-identifying within a small clinic, so the application handles **pseudonymised**, not anonymised, data — and pseudonymised health data remains personal information under the Act. The identifier field accepts a pseudonymous reference only; report export is restricted to authenticated sessions and carries the pseudonymous reference only. A retention policy, access control and an information officer are required before any real data is processed; until then the application runs on synthetic data with a demo-mode banner.

---

## 16. Regulatory position

Software informing antiretroviral prescribing falls within the medical-device definition under the Medicines and Related Substances Act and would be subject to SAHPRA licensing, not in the lowest risk class. The realistic path is research prototype → retrospective validation → publication → a decision about device classification. Every screen and export states that the software is a research prototype, not an approved medical device, and must not be used for clinical decisions.

---

## 17. Corrections from v4.0

| # | Item | v4.0 | Corrected | Stage | Commit |
|---|---|---|---|---|---|
| 1 | Paediatric DTG bands | 10/15/20/25 mg | 15/20/25/30 mg per WHO; age split | 1, 1b | 97b121d, d8505a4 |
| 2 | Dolutegravir threshold | 0.50 mg/L | 0.064 mg/L PA-IC90 | 1 | 97b121d |
| 3 | NRTI compartment | Plasma half-life | Intracellular anabolite (tier B) | 2, 3 | eba20f6, 776fb9c |
| 4 | Mutation probability | Fabricated percentage | Ordinal index | 1, 4 | 97b121d, 159bfc3 |
| 5 | Audit hash | `hash()` labelled SHA256 | Real SHA-256 chain | 1 | 97b121d |
| 6 | Efavirenz threshold | 0.51 mg/L | 1.0 mg/L | 1 | 97b121d |
| 7 | Risk direction | Cleared drug = highest risk | Monotherapy = highest risk | 4 | 159bfc3 |
| 8 | Rifampicin mechanism | CYP3A4 | UGT1A1 principal | 3 | 776fb9c |
| 9 | Dose doubling not modelled | Directive only | Applied to curve (BD) | 3 | 776fb9c |
| 10 | Herbal preparations | Combined, magnitude asserted | Separated, magnitude removed | 3 | 776fb9c |
| 11 | Hypoxis FBC advice | Attributed to TDF | Removed | 1b | d8505a4 |
| 12 | Paediatric scaling | Linear | Allometric ^0.25 | 3 | 776fb9c |
| 13 | MIC terminology | Throughout | PA-IC90 / threshold | 1b, 6 | d8505a4, pending |
| 14 | Genetic barrier | Absent | Included in mutation index | 4 | 159bfc3 |
| 15 | Adherence model | Scored social disadvantage | Support-needs framing | 5 | pending |
| 16 | Efavirenz–rifampicin | 0.74 multiplier | Removed | 3 | 776fb9c |
| 17 | Renal multipliers | Fixed per category | eGFR input, scaling disabled | 3 | 776fb9c |
| 18 | Timestamps | Server local, labelled SAST | Africa/Johannesburg, UTC stored | 1 | 97b121d |
| 19 | Log axis | Unbounded | Clamped at LLOQ | 3 | 776fb9c |
| 20 | Resistance window shading | 0.85× to 1.3× elapsed | Derived from state classification | 4 | 159bfc3 |
| 21 | HTML injection | Unescaped free text | `html.escape()` | 1 | 97b121d |
| 22 | Visitor counter | Seeded and floored at 322 | Removed | 1 | 97b121d |
| 23 | Unimplemented integrations | Presented as features | Removed or marked | 1 | 97b121d |

---

## 18. Outstanding items requiring sourcing

| Item | Section | Needed |
|---|---|---|
| Efavirenz plasma half-life | 4.2 | Primary source; note genotype dependence |
| Efavirenz Cmax,ss | 4.2 | Primary source |
| Abacavir plasma half-life | 4.5 | Product information |
| Carbovir triphosphate half-life | 4.5 | Hawkins 2005; Moyle 2009 |
| Tenofovir Cmax,ss | 4.3 | Primary source |
| Lamivudine Cmax,ss | 4.4 | Primary source |
| St John's Wort magnitude for DTG | 5.3 | Interaction study, if one exists |
| Fraction renally cleared, per drug | 5.5 | Product information (blocks eGFR scaling) |
| Tier B activity cut-off | 8.2 | Cannot be sourced; requires sensitivity analysis |
| Assay lower limits of quantification | 4.6 | NHLS laboratory methods |
| Current WHO / SA guideline versions | 6, 12 | Confirm against current consolidated guidelines |

---

## 19. References

1. Cottrell ML, Hadzic T, Kashuba ADM. *Clin Pharmacokinet.* 2013;52(11):981–94.
2. Wasserman S, et al. *Antimicrob Agents Chemother.* 2022;66(7).
3. Kappelhoff BS, et al. *Clin Pharmacokinet.* 2007;46(2):93–108.
4. Sinxadi PZ, et al. *Int J Antimicrob Agents.* 2016.
5. Cohen K, et al. Rifampicin/CYP2B6 and efavirenz in a South African population. PMC3837290.
6. Hawkins T, et al. *J Acquir Immune Defic Syndr.* 2005;39(4):406–11.
7. Louissaint NA, et al. *AIDS Res Hum Retroviruses.* 2013.
8. Anderson PL, et al. *Antimicrob Agents Chemother.* 2018.
9. Turkova A, et al. *Lancet HIV.* 2022.
10. Bollen P, et al. *Clin Infect Dis.* 2024;78(3):702.
11. Waalewijn H, et al. *Lancet HIV.* 2020.
12. Combined IMPAACT P1093 and ODYSSEY population-PK analysis, PENTA-ID.
13. Moyle G, et al. *Antimicrob Agents Chemother.* 2009;53(4):1532–8.

References located during preparation; the specific claim attributed to each should be checked against the full text before this document is submitted anywhere.
