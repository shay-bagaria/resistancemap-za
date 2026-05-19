import streamlit as st
import math
import numpy as np
import plotly.graph_objects as go
import datetime

<!DOCTYPE html>

<html class="dark" lang="en"><head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>ResistanceMap ZA OS - Enterprise Infrastructure</title>
<!-- Material Symbols -->
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<style>
        .material-symbols-outlined {
            font-family: 'Material Symbols Outlined';
            font-weight: normal;
            font-style: normal;
            font-size: 24px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
        }
        /* Subtley inject the data-grid pattern */
        .bg-data-grid {
            background-image: radial-gradient(var(--tw-colors-outline-variant) 1px, transparent 1px);
            background-size: 32px 32px;
        }
    </style>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<script id="tailwind-config">
        tailwind.config = {
          darkMode: "class",
          theme: {
            extend: {
              "colors": {
                      "on-tertiary-fixed": "#2a1700",
                      "on-primary-container": "#798098",
                      "on-background": "#e0e3e5",
                      "primary-fixed": "#dae2fd",
                      "surface-container-highest": "#323537",
                      "tertiary-fixed-dim": "#ffb95f",
                      "tertiary-fixed": "#ffddb8",
                      "secondary-container": "#29a195",
                      "tertiary": "#ffb95f",
                      "on-primary": "#283044",
                      "surface-dim": "#101415",
                      "on-primary-fixed-variant": "#3f465c",
                      "error-container": "#93000a",
                      "error": "#ffb4ab",
                      "surface-tint": "#bec6e0",
                      "outline": "#909097",
                      "secondary-fixed": "#89f5e7",
                      "on-tertiary": "#472a00",
                      "surface-container-high": "#272a2c",
                      "surface": "#101415",
                      "outline-variant": "#45464d",
                      "on-secondary": "#003732",
                      "surface-container-lowest": "#0b0f10",
                      "on-error": "#690005",
                      "inverse-on-surface": "#2d3133",
                      "tertiary-container": "#251400",
                      "on-surface-variant": "#c6c6cd",
                      "on-tertiary-fixed-variant": "#653e00",
                      "primary": "#bec6e0",
                      "on-tertiary-container": "#b47300",
                      "primary-container": "#0f172a",
                      "primary-fixed-dim": "#bec6e0",
                      "inverse-surface": "#e0e3e5",
                      "on-primary-fixed": "#131b2e",
                      "surface-container-low": "#191c1e",
                      "on-secondary-container": "#00302b",
                      "inverse-primary": "#565e74",
                      "secondary-fixed-dim": "#6bd8cb",
                      "surface-variant": "#323537",
                      "on-error-container": "#ffdad6",
                      "on-secondary-fixed": "#00201d",
                      "surface-container": "#1d2022",
                      "secondary": "#6bd8cb",
                      "surface-bright": "#363a3b",
                      "on-secondary-fixed-variant": "#005049",
                      "on-surface": "#e0e3e5",
                      "background": "#101415"
              },
              "borderRadius": {
                      "DEFAULT": "0.125rem",
                      "lg": "0.25rem",
                      "xl": "0.5rem",
                      "full": "0.75rem"
              },
              "spacing": {
                      "sm": "8px",
                      "xs": "4px",
                      "md": "16px",
                      "margin-desktop": "32px",
                      "margin-mobile": "16px",
                      "gutter": "16px",
                      "xl": "40px",
                      "lg": "24px",
                      "base": "4px"
              },
              "fontFamily": {
                      "display-xl": ["Inter"],
                      "data-mono": ["JetBrains Mono"],
                      "body-md": ["Inter"],
                      "label-caps": ["Inter"],
                      "body-sm": ["Inter"],
                      "headline-md": ["Inter"],
                      "headline-lg-mobile": ["Inter"],
                      "headline-lg": ["Inter"],
                      "body-lg": ["Inter"]
              },
              "fontSize": {
                      "display-xl": ["48px", {"lineHeight": "56px", "letterSpacing": "-0.02em", "fontWeight": "700"}],
                      "data-mono": ["14px", {"lineHeight": "20px", "letterSpacing": "0.02em", "fontWeight": "500"}],
                      "body-md": ["16px", {"lineHeight": "24px", "fontWeight": "400"}],
                      "label-caps": ["12px", {"lineHeight": "16px", "letterSpacing": "0.05em", "fontWeight": "700"}],
                      "body-sm": ["14px", {"lineHeight": "20px", "fontWeight": "400"}],
                      "headline-md": ["24px", {"lineHeight": "32px", "fontWeight": "600"}],
                      "headline-lg-mobile": ["24px", {"lineHeight": "32px", "fontWeight": "600"}],
                      "headline-lg": ["32px", {"lineHeight": "40px", "letterSpacing": "-0.01em", "fontWeight": "600"}],
                      "body-lg": ["18px", {"lineHeight": "28px", "fontWeight": "400"}]
              }
            }
          }
        }
    </script>
</head>
<body class="bg-background text-on-surface font-body-md overflow-x-hidden antialiased selection:bg-secondary selection:text-on-secondary">
<!-- TopAppBar -->
<header class="fixed top-0 z-50 bg-surface dark:bg-surface border-b border-outline-variant flex justify-between items-center w-full px-margin-desktop h-16">
<div class="flex items-center gap-md">
<span class="font-display-xl text-display-xl font-bold text-secondary dark:text-secondary" style="font-size: 24px; line-height: 1;">ResistanceMap ZA OS</span>
</div>
<div class="flex items-center gap-sm">
<span class="material-symbols-outlined text-secondary dark:text-secondary hover:bg-surface-container-highest transition-colors p-sm rounded-full cursor-pointer" data-icon="sync">sync</span>
<span class="material-symbols-outlined text-secondary dark:text-secondary hover:bg-surface-container-highest transition-colors p-sm rounded-full cursor-pointer" data-icon="analytics">analytics</span>
<span class="material-symbols-outlined text-secondary dark:text-secondary hover:bg-surface-container-highest transition-colors p-sm rounded-full cursor-pointer" data-icon="settings">settings</span>
<div class="w-8 h-8 rounded-full bg-surface-container-highest border border-outline-variant ml-sm overflow-hidden flex items-center justify-center">
<span class="material-symbols-outlined text-on-surface-variant text-sm">person</span>
<span class="sr-only">Chief Medical Officer Profile</span>
</div>
</div>
</header>
<!-- SideNavBar -->
<nav class="hidden md:flex flex-col h-screen fixed left-0 top-0 pt-16 pb-8 bg-surface-container-low dark:bg-surface-container-low border-r border-outline-variant w-64 z-40 justify-between">
<div class="flex flex-col w-full">
<div class="p-md border-b border-outline-variant/50 mb-sm">
<div class="flex items-center gap-sm mb-xs">
<div aria-label="System Status Beacon" class="w-2 h-2 rounded-full bg-secondary animate-pulse"></div>
<span class="font-label-caps text-label-caps text-on-surface">System Health</span>
</div>
<span class="font-body-sm text-body-sm text-on-surface-variant">NHLS Sync: Active</span>
</div>
<ul class="flex flex-col w-full">
<!-- Genomic Pipeline (Active) -->
<li class="w-full">
<a class="flex items-center w-full px-md py-sm text-secondary border-r-2 border-secondary hover:bg-surface-container-high transition-all" href="#">
<span class="material-symbols-outlined mr-md" data-icon="dna" style="font-variation-settings: 'FILL' 1;">dns</span>
<span class="font-label-caps text-label-caps">Genomic Pipeline</span>
</a>
</li>
<!-- Comorbidity Engine -->
<li class="w-full">
<a class="flex items-center w-full px-md py-sm text-on-surface-variant hover:bg-surface-container-high transition-all hover:text-on-surface" href="#">
<span class="material-symbols-outlined mr-md" data-icon="query_stats">query_stats</span>
<span class="font-label-caps text-label-caps">Comorbidity Engine</span>
</a>
</li>
<!-- Predictive AI -->
<li class="w-full">
<a class="flex items-center w-full px-md py-sm text-on-surface-variant hover:bg-surface-container-high transition-all hover:text-on-surface" href="#">
<span class="material-symbols-outlined mr-md" data-icon="psychology">psychology</span>
<span class="font-label-caps text-label-caps">Predictive AI</span>
</a>
</li>
<!-- Edge Deployment -->
<li class="w-full">
<a class="flex items-center w-full px-md py-sm text-on-surface-variant hover:bg-surface-container-high transition-all hover:text-on-surface" href="#">
<span class="material-symbols-outlined mr-md" data-icon="hub">hub</span>
<span class="font-label-caps text-label-caps">Edge Deployment</span>
</a>
</li>
</ul>
<div class="px-md mt-lg">
<button class="w-full py-sm bg-primary-container text-primary font-label-caps text-label-caps rounded border border-primary/30 hover:bg-primary-container/80 transition-colors uppercase">
                    Clinical Strike
                </button>
</div>
</div>
<div class="flex flex-col w-full border-t border-outline-variant/50 pt-sm mt-auto">
<ul class="flex flex-col w-full">
<li class="w-full">
<a class="flex items-center w-full px-md py-sm text-on-surface-variant hover:bg-surface-container-high transition-all hover:text-on-surface" href="#">
<span class="material-symbols-outlined mr-md" data-icon="payments">payments</span>
<span class="font-label-caps text-label-caps">Health Economics</span>
</a>
</li>
<li class="w-full">
<a class="flex items-center w-full px-md py-sm text-on-surface-variant hover:bg-surface-container-high transition-all hover:text-on-surface" href="#">
<span class="material-symbols-outlined mr-md" data-icon="verified_user">verified_user</span>
<span class="font-label-caps text-label-caps">Compliance</span>
</a>
</li>
</ul>
</div>
</nav>
<!-- Main Canvas -->
<main class="md:ml-64 pt-16 min-h-screen flex flex-col bg-data-grid relative">
<!-- Hero Section -->
<section class="relative w-full px-margin-desktop py-xl border-b border-outline-variant overflow-hidden flex items-center min-h-[409px]">
<div class="absolute inset-0 bg-primary-container/20 backdrop-blur-sm z-0"></div>
<div class="relative z-10 max-w-4xl">
<div class="inline-flex items-center gap-2 px-3 py-1 border border-secondary/30 bg-secondary-container/10 rounded-full mb-lg">
<span class="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
<span class="font-data-mono text-data-mono text-secondary">SYSTEM OPERATIONAL // OS v2.4.1</span>
</div>
<h1 class="font-display-xl text-display-xl text-on-surface mb-md">ResistanceMap ZA OS: The Macro-Level Infrastructure for Infectious Disease Defense.</h1>
<p class="font-body-lg text-body-lg text-on-surface-variant max-w-2xl border-l-2 border-outline-variant pl-md">
                    An autonomous CDSS protecting SA's antiretroviral rollout through real-time genomic surveillance and pharmacokinetic modeling. Designed for absolute reliability and precision.
                </p>
</div>
</section>
<!-- The 4 Pillars Section (Bento Grid) -->
<section class="w-full px-margin-desktop py-xl">
<h2 class="font-headline-lg text-headline-lg text-on-surface mb-lg flex items-center gap-sm">
<span class="material-symbols-outlined text-secondary" data-icon="memory">memory</span> Core OS Architecture
            </h2>
<div class="grid grid-cols-1 md:grid-cols-2 gap-md">
<!-- Pillar 1 -->
<div class="bg-surface-container-low border border-outline-variant p-lg rounded hover:border-secondary/50 transition-colors relative group overflow-hidden">
<div class="absolute top-0 left-0 w-full h-1 bg-secondary opacity-0 group-hover:opacity-100 transition-opacity"></div>
<div class="flex items-center justify-between mb-md">
<span class="material-symbols-outlined text-secondary text-4xl" data-icon="dna" style="font-variation-settings: 'FILL' 1;">dns</span>
<span class="font-data-mono text-data-mono text-on-surface-variant bg-surface px-2 py-1 rounded border border-outline-variant">PLR-01</span>
</div>
<h3 class="font-headline-md text-headline-md text-on-surface mb-sm">Autonomous Genomic Pipeline</h3>
<p class="font-body-sm text-body-sm text-on-surface-variant mb-md">Highlight NHLS HL7/FHIR API integration, zero data entry, and automated FASTA/VCF parsing.</p>
<div class="border-t border-outline-variant pt-sm mt-auto">
<div class="flex justify-between items-center font-data-mono text-data-mono text-xs">
<span class="text-on-surface-variant">API STATUS</span>
<span class="text-secondary">SYNCED</span>
</div>
</div>
</div>
<!-- Pillar 2 -->
<div class="bg-surface-container-low border border-outline-variant p-lg rounded hover:border-secondary/50 transition-colors relative group overflow-hidden">
<div class="absolute top-0 left-0 w-full h-1 bg-secondary opacity-0 group-hover:opacity-100 transition-opacity"></div>
<div class="flex items-center justify-between mb-md">
<span class="material-symbols-outlined text-secondary text-4xl" data-icon="query_stats">query_stats</span>
<span class="font-data-mono text-data-mono text-on-surface-variant bg-surface px-2 py-1 rounded border border-outline-variant">PLR-02</span>
</div>
<h3 class="font-headline-md text-headline-md text-on-surface mb-sm">Bio-Clinical Comorbidity Engine</h3>
<p class="font-body-sm text-body-sm text-on-surface-variant mb-md">TB Co-infection sync, Traditional Medicine Registry, and Paediatric Weight-Banding algorithms.</p>
<div class="border-t border-outline-variant pt-sm mt-auto">
<div class="flex justify-between items-center font-data-mono text-data-mono text-xs">
<span class="text-on-surface-variant">MODELS ACTIVE</span>
<span class="text-secondary">3/3</span>
</div>
</div>
</div>
<!-- Pillar 3 -->
<div class="bg-surface-container-low border border-outline-variant p-lg rounded hover:border-secondary/50 transition-colors relative group overflow-hidden">
<div class="absolute top-0 left-0 w-full h-1 bg-secondary opacity-0 group-hover:opacity-100 transition-opacity"></div>
<div class="flex items-center justify-between mb-md">
<span class="material-symbols-outlined text-secondary text-4xl" data-icon="psychology">psychology</span>
<span class="font-data-mono text-data-mono text-on-surface-variant bg-surface px-2 py-1 rounded border border-outline-variant">PLR-03</span>
</div>
<h3 class="font-headline-md text-headline-md text-on-surface mb-sm">Socio-Economic Predictive AI</h3>
<p class="font-body-sm text-body-sm text-on-surface-variant mb-md">ML models predicting default risk based on pharmacy dates, distance, and real-time taxi strike data.</p>
<div class="border-t border-outline-variant pt-sm mt-auto">
<div class="flex justify-between items-center font-data-mono text-data-mono text-xs">
<span class="text-on-surface-variant">PREDICTION CONFIDENCE</span>
<span class="text-secondary">94.2%</span>
</div>
</div>
</div>
<!-- Pillar 4 -->
<div class="bg-surface-container-low border border-outline-variant p-lg rounded hover:border-secondary/50 transition-colors relative group overflow-hidden">
<div class="absolute top-0 left-0 w-full h-1 bg-secondary opacity-0 group-hover:opacity-100 transition-opacity"></div>
<div class="flex items-center justify-between mb-md">
<span class="material-symbols-outlined text-secondary text-4xl" data-icon="hub">hub</span>
<span class="font-data-mono text-data-mono text-on-surface-variant bg-surface px-2 py-1 rounded border border-outline-variant">PLR-04</span>
</div>
<h3 class="font-headline-md text-headline-md text-on-surface mb-sm">Edge-Deployment</h3>
<p class="font-body-sm text-body-sm text-on-surface-variant mb-md">Offline-first architecture enabling full diagnostic capability in Zululand/deep rural sync zones.</p>
<div class="border-t border-outline-variant pt-sm mt-auto">
<div class="flex justify-between items-center font-data-mono text-data-mono text-xs">
<span class="text-on-surface-variant">NODES ONLINE</span>
<span class="text-secondary">1,402</span>
</div>
</div>
</div>
</div>
</section>
<!-- CFO Health Economics Dashboard -->
<section class="w-full px-margin-desktop py-xl border-t border-outline-variant bg-surface-dim">
<h2 class="font-headline-lg text-headline-lg text-on-surface mb-md flex items-center gap-sm">
<span class="material-symbols-outlined text-primary" data-icon="monitoring">monitoring</span> Economic Impact Analytics
            </h2>
<p class="font-body-md text-body-md text-on-surface-variant mb-lg max-w-3xl">High-fidelity tracking designed for Hospital CFOs and Department of Health officials to monitor macro-level efficiencies.</p>
<div class="flex flex-col md:flex-row gap-md">
<!-- Metric 1 -->
<div class="flex-1 bg-surface border border-outline-variant p-md rounded flex flex-col justify-between">
<div>
<div class="flex justify-between items-start mb-sm">
<span class="font-label-caps text-label-caps text-on-surface-variant">Mutation Prevention Rate</span>
<span class="material-symbols-outlined text-secondary text-sm" data-icon="trending_down">trending_down</span>
</div>
<div class="font-display-xl text-display-xl text-secondary font-data-mono tracking-tight">-24.8%</div>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-xs">Projected savings on 3rd-line salvage therapy.</p>
</div>
<div class="mt-md h-12 w-full bg-surface-container-highest flex items-end opacity-70">
<div class="w-1/5 h-[40%] bg-outline-variant border-r border-surface"></div>
<div class="w-1/5 h-[60%] bg-outline-variant border-r border-surface"></div>
<div class="w-1/5 h-[50%] bg-outline-variant border-r border-surface"></div>
<div class="w-1/5 h-[80%] bg-secondary/50 border-r border-surface"></div>
<div class="w-1/5 h-[100%] bg-secondary"></div>
</div>
</div>
<!-- Metric 2 -->
<div class="flex-1 bg-surface border border-outline-variant p-md rounded flex flex-col justify-between">
<div>
<div class="flex justify-between items-start mb-sm">
<span class="font-label-caps text-label-caps text-on-surface-variant">Stockout Redirection</span>
<span class="material-symbols-outlined text-primary text-sm" data-icon="swap_horiz">swap_horiz</span>
</div>
<div class="font-headline-lg text-headline-lg text-primary font-data-mono tracking-tight">Active Reroute</div>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-xs">Active Tenofovir supply redirection efficiency.</p>
</div>
<div class="mt-md flex flex-col gap-xs font-data-mono text-data-mono text-xs">
<div class="flex justify-between p-1 bg-surface-container-highest"><span>Zululand Node</span> <span class="text-secondary">Resolved</span></div>
<div class="flex justify-between p-1 bg-surface-container-highest"><span>Tshwane District</span> <span class="text-tertiary">Pending Auth</span></div>
</div>
</div>
<!-- Metric 3 -->
<div class="flex-1 bg-surface border border-outline-variant p-md rounded flex flex-col justify-between relative overflow-hidden">
<div class="absolute top-0 right-0 w-16 h-16 bg-primary-container/50 blur-xl rounded-full"></div>
<div class="relative z-10">
<div class="flex justify-between items-start mb-sm">
<span class="font-label-caps text-label-caps text-on-surface-variant">Automated Compliance</span>
<span class="material-symbols-outlined text-on-surface text-sm" data-icon="gavel">gavel</span>
</div>
<div class="font-display-xl text-display-xl text-on-surface font-data-mono tracking-tight">100%</div>
<p class="font-body-sm text-body-sm text-on-surface-variant mt-xs">Legal protection against medical negligence via automated auditing.</p>
</div>
<div class="mt-md pt-sm border-t border-outline-variant flex items-center gap-sm">
<span class="w-2 h-2 bg-secondary rounded-full"></span>
<span class="font-data-mono text-data-mono text-xs text-on-surface-variant">POPIA PROTOCOL ENFORCED</span>
</div>
</div>
</div>
</section>
<!-- Vision Call-to-Action -->
<section class="w-full px-margin-desktop py-xl mt-auto bg-surface border-t border-outline-variant text-center flex flex-col items-center justify-center">
<div class="max-w-2xl">
<h2 class="font-headline-lg text-headline-lg text-on-surface mb-sm">The Foundation of the NHI Framework</h2>
<p class="font-body-md text-body-md text-on-surface-variant mb-lg">ResistanceMap ZA OS is not just a tool; it is the structural requisite for National Health Insurance execution.</p>
<button class="bg-secondary text-on-secondary font-label-caps text-label-caps px-xl py-sm rounded hover:bg-secondary-fixed transition-colors">INITIATE STRATEGIC REVIEW</button>
</div>
</section>
<!-- Footer (JSON Execution) -->
<footer class="w-full py-md px-margin-desktop flex justify-between items-center bg-surface-container-lowest dark:bg-surface-container-lowest border-t border-outline-variant z-10 relative">
<div class="font-label-caps text-label-caps text-primary opacity-80 hover:opacity-100 transition-opacity">ResistanceMap ZA OS</div>
<div class="font-body-sm text-body-sm text-on-surface-variant dark:text-on-surface-variant">
                © 2024 ResistanceMap ZA. POPIA Compliant System.
            </div>
<div class="flex gap-md font-body-sm text-body-sm text-on-surface-variant">
<a class="hover:text-secondary transition-colors" href="#">Security Protocol</a>
<a class="hover:text-secondary transition-colors" href="#">Compliance Audit</a>
<a class="hover:text-secondary transition-colors" href="#">System Status</a>
</div>
</footer>
</main>
</body></html>
