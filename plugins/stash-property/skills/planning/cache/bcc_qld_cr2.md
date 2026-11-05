---
council_slug: bcc_qld
council_display: Brisbane City Council
state: QLD
zone_code: cr2
zone_display: Character Residential 2

verified_date: 2026-05-05
source_documents:
  - doc_name: "Brisbane City Plan 2014"
    doc_type: "Planning Scheme"
    source_url: "https://cityplan.brisbane.qld.gov.au/eplan/"
source_section: "5.5 (zone code), 8.2 (TBCO overlay)"

min_lot_size_m2: 300
min_lot_size_rear_m2: 450
min_avg_lot_m2: null
min_frontage_m: 7.5
min_avg_frontage_m: 7.5
min_rear_access_width_m: 3.5

max_height_m: 9.5
max_storeys: 2
density_cap: null
site_coverage_max_pct: 50
setback_front_m: 6
setback_side_m: 1.5
setback_rear_m: 6

character_overlay: yes
character_overlay_name: TBCO (Traditional Building Character Overlay)
heritage_overlay: conditional

ancillary_dwelling_rules: "Up to ~80m² permitted under Cl.6.2, but TBCO design compliance applies to all works."

state_overlays: []
---

# Brisbane City Council — Character Residential 2 (CR2)

## Notes

- **TBCO almost always applies in CR2** — confirm at the property level via
  Stash `planningInfo`, but treat as a hard blocker for demolition-dependent
  strategies (subdivision, KDR, multi-dwelling) until proven otherwise.
- **Smaller lot minimum than LDR** (300m² vs 400m²) reflects the older,
  tighter character lots typical of the zone — but TBCO restrictions
  generally make subdivision impractical even where the maths work.
- **Renovation and extension** are the dominant viable strategies in CR2.
  Character-sympathetic extension (matching materials, roof pitch, setbacks)
  permitted under TBCO subject to design compliance.
- **Pre-1947 buildings** in CR2 are essentially preserved by the overlay —
  demolition prohibited unless structural unsoundness is documented.
- **Per-property check is mandatory** — even within CR2, individual
  properties may have specific heritage listings on top of TBCO that
  further restrict works.

## Rule sources

- Brisbane City Plan 2014, Section 5.5 (Character Residential zone codes)
- Brisbane City Plan 2014, Section 8.2 (Traditional Building Character Overlay code)
- File: councils/bcc_qld.pdf (when uploaded)
- Last verified: 5 May 2026
