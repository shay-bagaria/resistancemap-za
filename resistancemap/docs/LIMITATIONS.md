# ResistanceMap ZA — Limitations

**Status: research prototype. Not validated. Not an approved medical device. Not for clinical use.**

This is a plain-language companion to `METHODOLOGY.md`, which has the formulas,
citations and worked examples. This page answers a narrower question: what
should a reader *not* assume this tool can do.

---

## 1. What this tool does not do

- **It does not read genetic sequence data and does not detect mutations.**
  Where a mutation name appears (K103N, M184V, and so on), it names the
  mutation most commonly associated with failure of that drug in the published
  literature — it is not a finding about the virus in the patient the tool is
  being used for.
- **It does not measure drug concentrations.** Every concentration or exposure
  percentage on screen is a model output from population-average
  pharmacokinetic parameters, not a measurement of any actual patient's blood.
- **It is not a diagnostic and not a prescribing tool.** It does not replace a
  viral load test, a resistance genotype, or a clinician's judgement.
- **It has not been checked against outcomes.** No component of this tool —
  the pharmacokinetic curves, the regimen-state classification, the mutation
  index, or the composite score — has been compared against what actually
  happened to real patients.

## 2. What each modelling choice costs

The pharmacokinetic model is a single-compartment exponential decay from the
last dose. That is a simplification with specific, known costs:

- **Real decay is often multi-phase, not single-phase.** Tenofovir's plasma
  decay in particular happens in three phases; a single exponential curve
  fits none of them exactly.
- **The model ignores absorption.** It assumes the concentration starts at its
  steady-state peak the moment a dose is taken, so it overestimates
  concentration in the first two to four hours after a dose.
- **Population-average parameters can be far from any individual patient.**
  Efavirenz clearance varies several-fold by CYP2B6 genotype, and the
  516G>T variant that slows clearance is common in South African populations
  — a patient with that variant could sit far from the modelled curve.
- **The model does not simulate restarting treatment.** It describes decay
  after a missed dose only; it says nothing about how quickly a patient
  re-suppresses once they resume dosing, and a twice-daily schedule is
  represented as an adjusted half-life plus a label, not a re-dosing curve
  with its own peaks and troughs.
- **Adherence is a single number of days.** A patient who took four of the
  last seven doses is not the same, pharmacologically, as a patient who took
  none for three days — but the model cannot tell them apart, because it only
  accepts "days since last dose." This is the single biggest gap: intermittent
  partial adherence is the pattern most associated with selecting resistant
  virus, and this input model cannot represent it.
- **The tier B (prodrug) activity cut-off is a guess.** For tenofovir,
  lamivudine and abacavir, the model decides a drug has "cleared" once its
  estimated remaining exposure drops below 25% of steady state. That number
  cannot be sourced from the literature; it is hand-chosen, labelled as such
  on screen, and the model's headline finding — the regimen-state
  classification — is sensitive to it in ways that are not always predictable
  (see `METHODOLOGY.md` §8.6 for a worked example where changing this cut-off
  changes *which drug* the model reports as the risk driver, not just how long
  the warning lasts).
- **Every ordinal ranking (mutation index, composite risk band) is hand-built,
  not fitted or learned.** The weights that combine drug levels, viral load
  and CD4 count into a single band were chosen by the person building this
  tool, not derived from data. They are labelled class C on screen for exactly
  this reason.

## 3. Validation status: none

No component of this tool has been validated. There is no completed or
in-progress study comparing its output to patient outcomes.

The validation study this tool is a specification for, but has not yet run:
a retrospective cohort using de-identified routine data (ART start date,
regimen, pharmacy collection dates as a proxy for adherence, sequential viral
load results), asking whether the presence and duration of a modelled
functional-monotherapy window predicts subsequent virological failure better
than "days since last collection" alone — the simplest comparator available.
That study would need to sweep the tier B activity cut-off and the
unverified efavirenz parameters as sensitivity analyses, because the model's
headline output is sensitive to both. It would require research ethics
approval (in KwaZulu-Natal, the University of KwaZulu-Natal Biomedical
Research Ethics Committee) and provincial Department of Health approval for
access to routine data. None of that has happened.

## 4. Data protection (POPIA)

Under the Protection of Personal Information Act 4 of 2013, health
information is "special personal information" and carries extra legal
protection.

This tool's identifiers are **pseudonymised, not anonymised** — a distinction
POPIA treats as legally significant. The combination of facility, clinician
code, weight, CD4 count, viral load, regimen and distance from clinic is
plausibly enough, taken together, to re-identify a patient within a small
clinic. Pseudonymised health data of that kind remains "personal information"
under the Act even without a name attached, so it carries the same
obligations real identified data would.

Consequences, as implemented in this build:

- The patient and clinician identifier fields accept pseudonymous references
  only; nothing links them back to a real identity within this application.
- Report export carries only the pseudonymous reference, never a real name.
- This build runs on synthetic demonstration data only, with a demo-mode
  banner on every screen, because the items below are not yet in place.
- **Not yet implemented, and required before any real patient data is
  processed:** a data retention policy, access control, and a named
  information officer for any deployment beyond a single researcher's own
  machine.

## 5. Regulatory position

Software intended to inform treatment decisions falls within the definition
of a medical device under South Africa's Medicines and Related Substances
Act, and would be subject to SAHPRA (South African Health Products Regulatory
Authority) licensing. Given that it would inform antiretroviral prescribing,
it would not sit in the lowest risk classification.

**Realistic path, in order, none of it completed:** research prototype (where
this tool is now) → the retrospective validation study described in section 3
→ publication of that study → only then a decision, with an appropriate
institutional sponsor, about whether to pursue formal device classification.
Deployment into a real clinical setting is not achievable on a timescale of
months from where this tool stands today, and nothing about this project
should be described as imminent in that respect.

Every screen and every export in this application states plainly that it is
a research prototype, is not an approved medical device, and must not be used
for clinical decisions. That statement is accurate as of this document and
should stay accurate — if a future version of this tool changes any of the
above, this page needs to change with it.
