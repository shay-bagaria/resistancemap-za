# ResistanceMap ZA
## Research Methodology Brief — Version 0.1

Project Lead: Shay Bagaria
Affiliation: Kearsney College, KwaZulu-Natal
Contact: sbagaria2009@gmail.com
Repository: github.com/shay-bagaria/resistancemap-za

---

## Executive Summary

ResistanceMap ZA is an open-source, zero-cost computational pipeline that maps HIV-1 drug-resistance mutation clusters across KwaZulu-Natal using publicly available genomic data from NCBI GenBank, cross-referenced against the Stanford HIV Drug Resistance Database, and translated into a pharmacokinetically-informed Resistance Risk Index (RRI) for frontline clinical application.

This brief presents the scientific framework underpinning the pipeline and requests expert review of the pharmacokinetic assumptions and RRI scoring methodology from researchers with direct clinical experience in KZN HIV treatment outcomes.

---

## 1. The Clinical Problem

KwaZulu-Natal carries one of the highest HIV burdens globally. Patients on first-line antiretroviral regimens, predominantly efavirenz-based, frequently experience treatment failure driven by inconsistent adherence. The critical gap is not the absence of clinical knowledge but the absence of a zero-cost, continuously updated, clinic-deployable resistance surveillance tool.

By the time treatment failure is identified through viral load testing, drug-resistance mutations have frequently already emerged and clustered within the local transmission network.

---

## 2. The Computational Approach

ResistanceMap ZA ingests HIV-1 pol gene sequences from NCBI GenBank filtered for South African origin between 2015 and 2026, aligns them against the HXB2 reference genome, identifies resistance-associated mutations, and cross-references each mutation against the Stanford HIVDB scoring algorithm.

A pharmacokinetic vulnerability model based on standard one-compartment elimination kinetics is then applied to each mutation-drug pair to produce a composite Resistance Risk Index.

---

## 3. The Resistance Risk Index

RRI = Mutation Frequency x Pharmacokinetic Vulnerability Score

The RRI produces a single actionable risk classification (Critical, High, Moderate, Low) for each mutation and drug combination identified in the KZN sequence dataset.

---

## 4. Request for Expert Review

We are specifically seeking feedback on:

1. Whether the pharmacokinetic assumptions, particularly efavirenz half-life of 40 to 55 hours, reflect the clinical reality observed in KZN patient cohorts
2. Whether the mutation selection (K103N, M184V, K65R, M41L) represents the most clinically relevant targets for the current KZN treatment landscape
3. Whether the RRI classification thresholds (0.25, 0.50, 0.75) are clinically meaningful or require recalibration

---

## 5. The Broader Framework

ResistanceMap ZA serves as the computational engine for ChromaTrace KZN, a paper-based colorimetric diagnostic proxy strip designed to physically detect ARV drug concentration thresholds at the clinic level. ChromaTrace requires no laboratory equipment, no financial investment, and is deployable across South Africa's 4,000-plus public clinics under the National Health Insurance framework.

---

## Full Documentation

Complete methodology, pipeline architecture, and code are available at:

github.com/shay-bagaria/resistancemap-za

---

ResistanceMap ZA operates under a strict zero-cost mandate. All tools, data sources, and infrastructure are open-access or free-tier.
