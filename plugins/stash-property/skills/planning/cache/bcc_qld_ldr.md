---
council_slug: bcc_qld
council_display: Brisbane City Council
state: QLD
zone_code: ldr
zone_display: Low Density Residential

verified_date: 2026-05-05
source_documents:
  - doc_name: "Brisbane City Plan 2014"
    doc_type: "Planning Scheme"
    source_url: "https://cityplan.brisbane.qld.gov.au/eplan/"
source_section: "5.5.1 (zone code), 6.2 (ancillary dwellings)"

min_lot_size_m2: 400
min_lot_size_rear_m2: 600
min_avg_lot_m2: null
min_frontage_m: 10
min_avg_frontage_m: 10
min_rear_access_width_m: 3.5

max_height_m: 9.5
max_storeys: 2
density_cap: null
site_coverage_max_pct: 50
setback_front_m: 6
setback_side_m: 1.5
setback_rear_m: 6

character_overlay: conditional
character_overlay_name: TBCO (Traditional Building Character Overlay)
heritage_overlay: conditional

ancillary_dwelling_rules: "Up to ~80m² permitted under Cl.6.2 — no subdivision required. Counts toward overall site coverage."

state_overlays: []
---

# Brisbane City Council — Low Density Residential (LDR)

## Notes

- **TBCO is the critical overlay** — pre-1947 dwellings under TBCO cannot be
  demolished, blocking subdivision and KDR strategies. Renovation and
  character-sympathetic extension remain viable. Per-property TBCO status
  must be checked via Stash `planningInfo` — it is conditional within
  the LDR zone, not zone-wide.
- **Battle-axe lots** require 600m² minimum (vs 400m² for standard lots).
- **Frontage averaging** is permitted but each lot still needs the
  individual minimum.
- **Pre-1947 + no TBCO** = full demolition flexibility despite the era.
  The overlay is the trigger, not the build year alone.
- **Subdivision: needs 800m² minimum** (2 × 400m²) plus reasonable geometry
  margin. Properties at 800–900m² are marginal — geometry needs checking
  even when raw maths pass.
- **Flood, bushfire, biodiversity** — pulled from Stash `get_planning_and_risks`
  per property, not from this scheme document.

## Rule sources

- Brisbane City Plan 2014, Section 5.5.1 (Low Density Residential zone code)
- Brisbane City Plan 2014, Section 6.2 (Ancillary dwelling acceptable outcomes)
- File: councils/bcc_qld.pdf (when uploaded)
- Last verified: 5 May 2026 (rules current as at this date; Brisbane City
  Plan 2014 has had multiple amendments — check current version before
  relying on for legal advice)
