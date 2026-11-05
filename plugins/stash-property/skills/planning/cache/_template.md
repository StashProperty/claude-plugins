---
# Cache file template — copy this and rename to {council_slug}_{zone_code}.md
# Save to /mnt/skills/user/planning/cache/
#
# REQUIRED fields below have a value or null. Do NOT leave a required field
# blank — if you don't know it, write `null` and add a note explaining why.
# OPTIONAL fields can be omitted entirely if not applicable.

council_slug: REPLACE_ME              # e.g. bcc_qld, melbourne_vic
council_display: REPLACE_ME           # e.g. Brisbane City Council
state: REPLACE_ME                     # QLD / VIC / NSW / SA / WA / ACT / TAS / NT
zone_code: REPLACE_ME                 # e.g. ldr, r1z, r2
zone_display: REPLACE_ME              # e.g. Low Density Residential, General Residential Zone

verified_date: YYYY-MM-DD             # date you last confirmed these rules
source_documents:                     # list of docs from Planning_Documents.xlsx
  - doc_name: "REPLACE_ME"            # exact name from xlsx Document Name column
    doc_type: "REPLACE_ME"            # e.g. Planning Scheme, LEP, DCP
    source_url: "REPLACE_ME"          # from xlsx Source URL column
source_section: "REPLACE_ME"          # section number(s) within those documents

# REQUIRED fields — subdivision rules
min_lot_size_m2: null                 # standard min lot size, e.g. 400
min_lot_size_rear_m2: null            # battle-axe / rear lot, e.g. 600 (or null if same as standard)
min_avg_lot_m2: null                  # VIC ResCode-style average test, null elsewhere
min_frontage_m: null                  # per lot, e.g. 10
min_avg_frontage_m: null              # averaging variant, null if not applicable
min_rear_access_width_m: null         # battle-axe handle width, e.g. 3.5

# REQUIRED fields — building envelope
max_height_m: null                    # outright maximum, e.g. 9.5
max_storeys: null                     # outright maximum, e.g. 2
density_cap: null                     # e.g. "1 dwelling per 600m²" — null for low density zones
site_coverage_max_pct: null           # e.g. 50
setback_front_m: null                 # e.g. 6
setback_side_m: null                  # e.g. 1.5
setback_rear_m: null                  # e.g. 6

# REQUIRED fields — overlays
character_overlay: null               # yes / no / conditional
character_overlay_name: null          # e.g. "TBCO (Traditional Building Character Overlay)" or null
heritage_overlay: null                # yes / no / conditional

# REQUIRED — ancillary dwellings
ancillary_dwelling_rules: null        # text description, e.g. "Up to 80m² permitted under Cl.6.2"

# REQUIRED — state-level overlays that apply
state_overlays: []                    # list, e.g. ["VIC ResCode Cl 55/56"], or [] if none
---

# {council_display} — {zone_display}

## Notes

(Free text — anything the calling skill should know that doesn't fit the
structured fields. Examples:
- Quirks of how this zone interacts with state overlays
- Recent or pending amendments
- Common interpretation gotchas (e.g. VIC's 400m² average test)
- Hard blockers worth highlighting
)

## Rule sources

- {Source PDF and section reference}
- File: councils/{slug}.pdf
- Last verified: {date}
