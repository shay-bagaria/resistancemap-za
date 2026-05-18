# ResistanceMap ZA

**An open-source molecular epidemiology pipeline for HIV-1 drug resistance surveillance in KwaZulu-Natal, South Africa.**

---

## Overview

ResistanceMap ZA is an automated computational framework that ingests HIV-1 pol gene sequences from NCBI GenBank, identifies drug-resistance mutations via Stanford HIVDB cross-referencing, models pharmacokinetic vulnerability windows for first-line antiretroviral regimens, and outputs a composite Resistance Risk Index (RRI).

This pipeline is designed to support frontline clinical decision-making under South Africa's National Health Insurance (NHI) framework and serves as the computational engine powering the ChromaTrace KZN paper-based diagnostic system.

---

## The Problem

HIV/TB co-infection remains one of the most severe public health crises in KwaZulu-Natal. Patients on antiretroviral regimens frequently miss doses inconsistently. By the time treatment failure is detected through standard viral load testing, drug-resistance mutations have already emerged and may have spread within the local population.

Existing resistance genotyping tools are expensive, slow, and inaccessible at the clinic level.

ResistanceMap ZA addresses this gap by providing a zero-cost, open-source, continuously updated resistance surveillance map built entirely from publicly available genomic data.

---

## Scientific Framework

| Parameter | Detail |
|---|---|
| Target gene | HIV-1 pol (protease + reverse transcriptase) |
| Reference strain | HXB2 (GenBank K03455) |
| Mutation database | Stanford HIV Drug Resistance Database |
| Genomic data source | NCBI GenBank |
| Temporal scope | 2015 to 2026 |
| Geographic focus | KwaZulu-Natal, South Africa |

---

## The Resistance Risk Index

RRI = Mutation Frequency x Pharmacokinetic Vulnerability Score

### Classification

| Score | Classification |
|---|---|
| Above 0.75 | Critical |
| 0.50 to 0.75 | High |
| 0.25 to 0.50 | Moderate |
| Below 0.25 | Low |

---

## Pipeline Architecture

NCBI GenBank to Sequence Retrieval to Quality Filtering to Alignment to HXB2 Reference to Mutation Identification to Stanford HIVDB Cross-Referencing to Pharmacokinetic Modelling to RRI Score Calculation to Output Dashboard.

---

## Current Status

| Phase | Status |
|---|---|
| Phase 1: Data Acquisition | In Progress |
| Phase 2: Mutation Analysis | Pending |
| Phase 3: PK Modelling | Pending |
| Phase 4: RRI Scoring | Pending |
| Phase 5: ChromaTrace Integration | Pending |
| Phase 6: Institutional Validation | Pending |

---

## Related Project

ChromaTrace KZN is a paper-based colorimetric diagnostic proxy strip designed to physically detect ARV drug concentration thresholds at the clinic level, informed by RRI outputs from this pipeline.

---

## Project Lead

Shay Bagaria
Contact: sbagaria2009@gmail.com

---

## Licence

This project is licensed under the MIT Licence. Open source. Freely replicable. Zero cost.

---

## Acknowledgements

Data sourced from NCBI GenBank, Stanford HIV Drug Resistance Database, and EMBL-EBI. This project operates under a strict zero-cost mandate.
