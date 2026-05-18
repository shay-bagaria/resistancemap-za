# ResistanceMap ZA — Scientific Methodology

Version: 0.1 Draft
Author: Shay Bagaria

---

## 1. Target Biology

### The HIV-1 pol Gene

The human immunodeficiency virus type 1 (HIV-1) pol gene encodes three critical enzymes:

- Protease (PR): Cleaves viral polyproteins into functional units during viral maturation
- Reverse Transcriptase (RT): Converts viral RNA into DNA — the primary target of most antiretroviral drugs
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
| M41L | RT | Thymidine analogues | TAM that accumulates with treatment failure |
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

Ke = ln(2) / t-half

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
- Longer half-life equals higher PVS (paradoxically more dangerous)
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
| EMBL-EBI |
