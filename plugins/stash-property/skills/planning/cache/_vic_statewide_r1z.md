---
council_slug: _vic_statewide
council_display: VIC Statewide (R1Z baseline — overridden by individual councils)
state: VIC
zone_code: r1z
zone_display: General Residential Zone

verified_date: 2026-05-05
source_documents:
  - doc_name: "Victoria Planning Provisions"
    doc_type: "State Planning Scheme"
    source_url: "https://www.planning.vic.gov.au/policy-and-strategy/planning-policies/the-vpp"
  - doc_name: "ResCode (Cl 55 + 56)"
    doc_type: "State Planning Scheme"
    source_url: "https://www.planning.vic.gov.au/policy-and-strategy/rescode-development-design-standards"
source_section: "Cl 32.08 (R1Z), Cl 55, Cl 56 (ResCode)"

min_lot_size_m2: 300
min_lot_size_rear_m2: 500
min_avg_lot_m2: 400
min_frontage_m: 7.5
min_avg_frontage_m: 7.5
min_rear_access_width_m: 3.5

max_height_m: 11
max_storeys: 3
density_cap: null
site_coverage_max_pct: 60
setback_front_m: 4
setback_side_m: 1
setback_rear_m: 3

character_overlay: conditional
character_overlay_name: Heritage Overlay (HO) or Neighbourhood Character Overlay (NCO) — council-specific
heritage_overlay: conditional

ancillary_dwelling_rules: "Secondary dwelling permitted on same lot subject to Cl.55 setback / site coverage rules. BPA areas trigger BAL assessment for any new dwelling including secondary."

state_overlays:
  - "VIC ResCode Cl 55 (one dwelling on a lot) and Cl 56 (subdivision)"
---

# VIC Statewide — General Residential Zone (R1Z) baseline

## Notes

This is a **statewide baseline** — most VIC councils inherit these rules
from the Planning and Environment Act / VPP / ResCode rather than writing
their own zone codes. Some councils add neighbourhood-specific overlays
on top (e.g. Stonnington heritage areas, Banyule character precincts).
Individual council cache entries should override only where the council
has a documented variation.

- **THE 400m² AVERAGE TEST IS THE PRIMARY BLOCKER** for VIC subdivisions.
  ResCode Cl.56 requires the average lot size across all proposed lots to
  be at least 400m². A block that passes the 300m² per-lot minimum can
  STILL fail this test. Always calculate average explicitly:
  `land_area / proposed_lot_count >= 400`.
- **Three-lot subdivision on a 1000m² block fails the average test** even
  though 1000/3 = 333m² which exceeds the 300m² minimum (333 < 400 average).
  Two lots on the same 1000m² passes (500m² average).
- **BPA (Bushfire Prone Area) overlays** apply across many VIC councils.
  Risk 5/5 = mandatory BAL assessment under AS 3959. Cost impact per
  dwelling: BAL-12.5 ~$5k, BAL-29 ~$30–60k, BAL-40/FZ ~$80–150k+.
  Applies to ALL new dwellings including secondary dwellings.
- **Heritage Overlay (HO)** is council-specific and generally treated as
  a hard blocker for demolition-dependent strategies. Always check per
  property via Stash `planningInfo`.
- **Neighbourhood Character Overlay (NCO)** softer than HO — typically
  requires sympathetic design rather than prohibiting works outright.
- **Frankston, Casey, Wyndham etc.** — confirm with council pre-application
  meeting before lodging. Outer-metro councils sometimes interpret
  ResCode more strictly than the planning instrument literally requires.

## Rule sources

- Planning and Environment Act 1987 (Vic)
- Victoria Planning Provisions (VPP) Cl.32.08 — General Residential Zone
- VPP Cl.55 — One dwelling on a lot
- VPP Cl.56 — Subdivision (the 400m² average test lives here)
- Last verified: 5 May 2026
