# ChromaTrace KZN — Concept Document

Version: 0.1 Concept
Author: Shay Bagaria
Status: Conceptual design phase, physical prototyping pending Phase 2

---

## Overview

ChromaTrace KZN is a paper-based colorimetric diagnostic proxy system designed to provide frontline healthcare workers with a visual, zero-cost indicator of whether a patient's antiretroviral drug levels are likely to be within the therapeutic range, without requiring laboratory equipment, trained technicians, or financial investment.

---

## The Scientific Link to ResistanceMap ZA

ChromaTrace is not a standalone project. It is the physical embodiment of the computational outputs from ResistanceMap ZA.

The RRI pipeline identifies which drug and mutation combinations are most dangerous in KZN. ChromaTrace is designed to detect the precise drug concentration threshold that corresponds to the highest-risk window identified by the RRI model.

The logical flow is:

1. ResistanceMap ZA identifies efavirenz combined with K103N as Critical RRI
2. Efavirenz PK model identifies that the sub-inhibitory window begins below a defined concentration
3. ChromaTrace is designed to produce a visible colour change at that threshold
4. The clinic worker sees a colour signal without any laboratory equipment

---

## The Chemistry Concept

ChromaTrace uses food-safe, naturally derived organic reagents that undergo visible colour changes in the presence of functional groups present in ARV drug metabolites or their chemical proxies.

### Reagent Candidates

| Reagent | Source | Chemistry | Colour Change |
|---|---|---|---|
| Anthocyanins | Red cabbage extract | pH-sensitive electron transfer | Red to Blue to Green |
| Curcumin | Turmeric powder | Coordination complex formation | Yellow to Orange-Red |
| Bromothymol Blue | Laboratory indicator | pH indicator | Yellow to Blue |

### The Substrate

- Whatman No. 1 filter paper, a standard school laboratory supply
- Cut into strips approximately 5mm by 50mm
- Reagent applied by dipping or pipetting
- Dried at room temperature

---

## The Detection Logic

The strip is designed to detect a proxy chemical that mimics the functional group behaviour of an ARV metabolite at a defined concentration.

Note: ChromaTrace does not directly detect ARV drugs in patient samples in this prototype phase. It demonstrates the proof-of-concept that a paper-based colorimetric system can be calibrated to a specific biochemical threshold derived from pharmacokinetic modelling.

---

## The Smartphone Analysis Method

Colour change intensity is quantified using:

- A standard smartphone camera photograph
- Free image analysis software such as ImageJ
- RGB value extraction from the reaction zone
- Comparison against a pre-built calibration curve

This eliminates the need for a spectrophotometer.

---

## Deployment Vision

A single ChromaTrace strip:

- Costs less than R0.50 to produce
- Requires no electricity
- Requires no laboratory equipment
- Produces a result in under 10 minutes
- Can be read by any healthcare worker using a smartphone

Scaled across 4,000-plus public clinics under the NHI framework:

- Zero procurement cost
- Zero training infrastructure required
- Directly informed by real-time KZN resistance data from ResistanceMap ZA

---

## Current Status

- Concept design complete
- Reagent chemistry literature review in progress
- School laboratory access pending
- First prototype strips planned for Phase 2 Month 6
- Smartphone colour analysis calibration planned for Phase 2 Month 7
- Hillcrest AIDS Centre pilot planned for Phase 2 Month 8

---

Full prototyping documentation will be added as Phase 2 begins.
