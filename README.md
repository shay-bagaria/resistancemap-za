ResistanceMap ZA
An open-source molecular epidemiology pipeline for HIV-1 drug resistance surveillance in KwaZulu-Natal, South Africa.

![Status](https://img.shields.io/badge/Status-Phase%201%20In%20Progress-yellow)
![Licence](https://img.shields.io/badge/Licence-MIT-green)
![Cost](https://img.shields.io/badge/Build%20Cost-Zero-brightgreen)

Overview
ResistanceMap ZA is an automated computational framework that ingests HIV-1 pol gene sequences from NCBI GenBank, identifies drug-resistance mutations via Stanford HIVDB cross-referencing, models pharmacokinetic vulnerability windows for first-line antiretroviral regimens, and outputs a composite Resistance Risk Index (RRI) — a deterministic clinical risk score mapping which mutation and drug combinations pose the greatest immediate threat to treatment outcomes in KwaZulu-Natal.

This pipeline is designed to support frontline clinical decision-making under South Africa's National Health Insurance (NHI) framework and serves as the computational engine powering the ChromaTrace KZN paper-based diagnostic system.

The Problem We Are Solving
HIV/TB co-infection remains one of the most severe public health crises in KwaZulu-Natal, South Africa. Patients on antiretroviral (ARV) and TB drug regimens frequently miss doses inconsistently. By the time treatment failure is detected through standard viral load testing, drug-resistance mutations have already emerged and may have spread within the local population.

Existing resistance genotyping tools are expensive, slow, and inaccessible at the clinic level.

ResistanceMap ZA addresses this gap by providing a zero-cost, open-source, continuously updated resistance surveillance map built entirely from publicly available genomic data.

Scientific Framework
Parameter	Detail
Target gene	HIV-1 pol (protease + reverse transcriptase)
Reference strain	HXB2 (GenBank accession: K03455)
Mutation database	Stanford HIV Drug Resistance Database (HIVDB)
Genomic data source	NCBI GenBank
Temporal scope	2015–2026
Geographic focus	KwaZulu-Natal, South Africa
The Resistance Risk Index (RRI)
The RRI is the core output of this pipeline. It is a composite metric combining mutation prevalence with pharmacokinetic vulnerability:

RRI = Mutation Frequency × Pharmacokinetic Vulnerability Score

Where:

Mutation Frequency = proportion of KZN sequences carrying a given resistance mutation
Pharmacokinetic Vulnerability Score = a normalised score derived from the drug's elimination half-life and the duration of sub-inhibitory concentration exposure during a missed-dose window
RRI Classification
Score	Classification	Clinical Implication
RRI > 0.75	🔴 Critical	Immediate surveillance priority
RRI 0.50–0.75	🟠 High	Enhanced monitoring recommended
RRI 0.25–0.50	🟡 Moderate	Routine monitoring
RRI < 0.25	🟢 Low	Standard protocol
Pipeline Architecture
NCBI GenBank → Sequence Retrieval (Biopython Entrez) → Quality Filtering and Metadata Extraction → Alignment to HXB2 Reference → Mutation Identification (SNP Detection) → Stanford HIVDB Cross-Referencing → Pharmacokinetic Vulnerability Modelling → RRI Score Calculation → Output: Mutation Map and Risk Dashboard

Repository Structure
text

resistancemap-za/
│
├── README.md
├── LICENSE
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
│
├── notebooks/
│   ├── 01_data_acquisition.ipynb
│   ├── 02_mutation_analysis.ipynb
│   ├── 03_pk_modelling.ipynb
│   └── 04_rri_scoring.ipynb
│
├── scripts/
│   ├── fetch_sequences.py
│   ├── align_sequences.py
│   └── rri_calculator.py
│
├── results/
│   ├── figures/
│   ├── tables/
│   └── reports/
│
├── docs/
│   ├── methodology.md
│   ├── research_brief.md
│   └── chromatrace_concept.md
│
└── references/
    └── key_papers.md
Current Status
Phase	Status
Phase 1: Data Acquisition	🔄 In Progress
Phase 2: Mutation Analysis	⏳ Pending
Phase 3: PK Modelling	⏳ Pending
Phase 4: RRI Scoring	⏳ Pending
Phase 5: ChromaTrace Integration	⏳ Pending
Phase 6: Institutional Validation	⏳ Pending
Related Project
ChromaTrace KZN — A paper-based colorimetric diagnostic proxy strip designed to physically detect ARV drug concentration thresholds at the clinic level, informed by RRI outputs from this pipeline.

How To Use This Pipeline
Full usage instructions will be added as each notebook is completed.

Requirements:

Google Colab (free) or local Python 3.9+ environment
Biopython
Pandas
Matplotlib
NumPy
Project Lead
Shay Bagaria
Independent Researcher — KwaZulu-Natal, South Africa
NYAS Junior Academy Member
Founder, Hearts and Hands Foundation

📧 sbagaria2009@gmail.com

Licence
This project is licensed under the MIT Licence. Open source. Freely replicable. Zero cost.

Acknowledgements
Data sourced from NCBI GenBank, Stanford HIV Drug Resistance Database, and EMBL-EBI.

This project operates under a strict zero-cost mandate. No financial capital was used in its construction.
