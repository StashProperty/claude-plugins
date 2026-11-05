---
name: planning
description: >
  Provides council-level planning rules (zone minimum lot sizes, frontage,
  height limits, character overlays, ancillary dwelling rules) for Australian
  residential addresses. Used as a sub-skill by `cma` and `feaso` whenever
  development potential, subdivision viability, KDR eligibility, or
  multi-dwelling capacity needs to be assessed against the actual planning
  scheme. Not a feasibility skill — does not produce verdicts, financial
  models, or reports. Returns structured rule data only. Triggers when a
  user asks "what's the zoning at X", "what are the planning rules for Y",
  "is X subdividable under the rules", "what's the minimum lot size in Y",
  "TBCO check on X", or any direct planning-rule question. Auto-invoked by
  `feaso` STEP 2 and by `cma` Section 5 when needed. Backed by
  Planning_Documents.xlsx — a national index of 1,146 planning documents
  across 579 LGAs in all 8 Australian states/territories. Self-learning:
  caches extracted rules per council/zone the first time they're requested.
---

# Planning Skill — Council Rule Lookup (Phase 1)

This skill maps an Australian property to its council planning rules. It does
NOT make development decisions — feaso owns those. Planning's only job is to
return the numbers.

Phase 1 = manual rule entry with a structured template. Phase 2 (later) will
add automated PDF extraction.

---

## STEP 0 — Determine the council and zone

The skill is given one of three input shapes:

1. **From feaso/cma hand-off** — propertyId already resolved. The caller has
   already run `get_property_profile` with `planningInfo:true` and knows
   the council/LGA name and zone code. Use those directly. Skip to STEP 1.

2. **From a direct user query with an address** — run `suggest_entity` to
   get the propertyId, then `get_property_profile(include={planningInfo:true,
   zones:true})` to get the LGA name and zone code.

3. **From a user query with no address** ("what's the minimum lot size in
   Brisbane LDR?") — the user has stated the council and zone explicitly.
   Use those values; no Stash call needed.

The output of STEP 0 is two strings: `council_slug` and `zone_code`,
where the slug is derived from the council name + state per the rules in
STEP 2 ("Slugs are derived, not stored"). The zone code is the council's
own short code, lowercased:

- QLD: `ldr`, `cr2`, `lmr`, `mdr`, `mu1`, etc.
- VIC: `r1z`, `r2z`, `r3z`, `gru`, `nrz`, etc.
- NSW: `r1`, `r2`, `r3`, `r4`, `e2`, `e3`, etc.
- SA / WA / ACT / TAS / NT: lowercase council-native code as encountered.

Cache keys combine slug + zone: `bcc_qld_ldr`, `melbourne_vic_r1z`, etc.

---

## STEP 1 — Check the cache

Look for a cache file in this priority order:

1. **Council-specific entry** — `cache/{council_slug}_{zone_code}.md` (e.g.
   `bcc_qld_ldr.md`). Most accurate when present.
2. **Statewide baseline** — `cache/_{state}_statewide_{zone_code}.md` (e.g.
   `_vic_statewide_r1z.md`). Used when council-specific entry doesn't exist
   AND the zone code is a state-level standard (VIC R1Z, NSW R2, etc.) that
   most councils inherit from the state planning provisions.
3. **No match** → STEP 2.

When a statewide baseline is used, mark the response with
`baseline_match: true` so the calling skill can add a note: "Rules from
VIC statewide baseline (ResCode); confirm any council-specific variations
with [council name] before relying on for legal advice."

If a council-specific entry exists, it ALWAYS overrides the baseline.
If both exist (e.g. `melbourne_vic_r1z.md` AND `_vic_statewide_r1z.md`),
the calling skill gets the council-specific version only.

For all matches, check `verified_date`:
- Within last 24 months → return rules with `verification_stale: false`
- Older than 24 months → return rules with `verification_stale: true`

The slug `_{state}_statewide` is a reserved convention. Council slugs
must NEVER start with an underscore — that prefix is reserved for
baseline entries.

---

## STEP 2 — Look up the planning document(s)

The source of truth for what planning documents exist is
`/mnt/skills/user/planning/Planning_Documents.xlsx`. This file holds 1,146
documents across 579 LGAs covering all 8 Australian states/territories.

### Reading the xlsx

```python
import openpyxl
wb = openpyxl.load_workbook(
    '/mnt/skills/user/planning/Planning_Documents.xlsx',
    data_only=True
)
ws = wb['Sheet1']
# Columns: State, Council/LGA, Document Name, Document Type,
#          File Format, Amended On, Source URL
rows = list(ws.iter_rows(min_row=2, values_only=True))
```

Filter rows where:
- `State` matches the target state (e.g. `'QLD'`)
- `Council/LGA` matches the target council (case-insensitive contains-match,
  not strict equality — see "Council name matching" below)

A single LGA typically has multiple documents — a Local Environmental Plan
(LEP) or Planning Scheme, plus one or more Development Control Plans (DCPs)
or Local Policies. Read ALL of them: the LEP/Scheme defines the zones, the
DCPs add specific rules.

Document type priority for residential zone rules:

| Priority | Document type | Use for |
|---|---|---|
| 1 | Planning Scheme | QLD primary instrument — zones, lot minimums, overlays |
| 1 | Local Environmental Plan | NSW primary instrument — zones, FSR, height |
| 1 | Development_Plan | SA primary instrument |
| 1 | Town Plan / Territory_Plan | NT, ACT primary instruments |
| 1 | Interim Planning Scheme | TAS primary instrument |
| 2 | Development Control Plan | NSW supplementary — detailed controls |
| 2 | Local Policies | WA supplementary — discretionary rules |
| 3 | State Environmental Planning Policy | NSW state-level overrides |
| 3 | Tech_Spec / Bep | Specialist technical instruments |

Always read priority 1 first. Read priority 2 only if priority 1 doesn't
cover the rule you need (frontage minimums, setbacks, etc. often live in
DCPs, not the LEP).

### Council name matching

The xlsx's `Council/LGA` column is heterogeneous:

- Most rows have a clean council name: `'Brisbane'`, `'City of Sydney'`,
  `'Inner West'`, `'Bellingen'`
- NSW rows sometimes contain precincts or addresses instead of councils:
  `'Green Square'`, `'Rural Lands'`, `'327-335 Burley Road Horsley Park'`.
  These are site-specific DCPs that apply within a parent council. When
  matching, check the Source URL — it usually identifies the parent council
  in its domain (e.g. `cityofsydney.nsw.gov.au`).
- 387 rows have NO council/LGA — these are state-level instruments
  (mostly VIC VPP clauses, NSW SEPPs, WA state policies). Treat these as
  applying to ALL councils in their state. Always include matching
  state-level rows alongside council-specific rows.

Match strategy:
1. Exact case-insensitive match on `Council/LGA` first
2. If no match, try contains-match (`'City of Sydney'` matches `'Sydney'`
   query and vice versa)
3. Always include rows in the same state where `Council/LGA` is empty
   (state-level instruments)
4. If still nothing → STEP 4 (gap handling)

### Reading the actual document

Once relevant rows are identified, follow the `Source URL` (online) or
look in `councils/` for a downloaded copy. PDF reading is Phase 2 — for
Phase 1, prompt the user to paste the relevant rules manually using the
template. The xlsx tells us WHICH document to read; the user (or Phase 2
automation) extracts the rules.

If the user has placed the PDF locally at
`/mnt/skills/user/planning/councils/{slug}.pdf`, read it via the `pdf-reading`
skill at `/mnt/skills/public/pdf-reading/SKILL.md`.

### Slugs are derived, not stored

The xlsx doesn't have a slug column. Derive slugs at query time using:

```
slug = (council_name or '_state_statewide').lower()
slug = slug.replace('city of ', '').replace('shire of ', '')
slug = slug.replace(' council', '').replace(' shire', '')
slug = re.sub(r'[^a-z0-9]+', '_', slug).strip('_')
slug = f"{slug}_{state.lower()}"
```

So `'City of Brisbane'` + `'QLD'` → `brisbane_qld`. `'Inner West Council'` +
`'NSW'` → `inner_west_nsw`. Cache file names use these derived slugs.

If the council doesn't appear in the xlsx → STEP 4.

---

## STEP 3 — Extract rules, write cache entry, return

After STEP 2 has identified the relevant document(s), extract rules for
the requested zone. Phase 1 = manual entry by the user via the template.
Phase 2 = automated PDF extraction.

### Required fields to extract

For each zone, capture:

**Subdivision rules:**
- `min_lot_size_m2` — minimum lot size for standard subdivision
- `min_lot_size_rear_m2` — for battle-axe / rear lots if specified separately
- `min_avg_lot_m2` — VIC ResCode-style average test, or null
- `min_frontage_m` — per lot
- `min_avg_frontage_m` — for averaging tests
- `min_rear_access_width_m` — handle width for battle-axe

**Building envelope:**
- `max_height_m` — outright maximum
- `max_storeys` — outright maximum
- `density_cap` — e.g. "1 dwelling per 600m²" for medium-density zones; null for low-density
- `site_coverage_max_pct` — for multi-dwelling viability
- `setback_front_m`, `setback_side_m`, `setback_rear_m` — minimum setbacks

**Overlays:**
- `character_overlay` — yes/no/conditional + overlay name (TBCO, HCA, NCO etc.)
- `heritage_overlay` — yes/no + how it interacts with the zone
- `ancillary_dwelling_rules` — granny flat / secondary dwelling permission

**State-level overlays:**
- `state_overlays` — list (e.g. `["VIC ResCode Cl 55/56"]`, `["NSW SEPP ARH"]`)

**Provenance:**
- `source_documents` — list of `{doc_name, doc_type, source_url}` entries from xlsx
- `source_section` — section number(s) within those documents
- `verified_date` — today's date when written

If extraction fails or rules are ambiguous → STEP 4.

### Writing the cache entry

Write the extracted rules to
`/mnt/skills/user/planning/cache/{council_slug}_{zone_code}.md` using the
template below. Then return the parsed rule set to the caller.

### Cache file template

```markdown
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
source_section: "5.5.1, 6.2"

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
ancillary_dwelling_rules: "Up to ~80m² permitted under Cl.6.2 — no subdivision required"
state_overlays: []
---

# Brisbane City Council — Low Density Residential (LDR) zone

## Notes

- TBCO check is critical: pre-1947 dwellings under TBCO cannot be demolished
  even where zoning otherwise permits, blocking subdivision and KDR strategies.
  Renovation and character-sympathetic extension remain viable.
- Battle-axe lots permitted but require 600m² minimum (vs 400m² standard).
- Flood: subject to Brisbane River planning area, creek waterway, and overland
  flow overlays — these are pulled separately from Stash hazards, not from
  the planning scheme PDF.

## Rule sources

- Brisbane City Plan 2014, Section 5.5.1 (zone code) and 6.2 (ancillary
  dwelling rules)
- File: councils/bcc_qld.pdf
- Last verified: 5 May 2026
```

### Returning to the caller

Return a structured object containing all the YAML fields plus:
- `verification_stale: false` (or true if from STEP 1 stale-cache path)
- `manual_entry_required: false` (or true if from STEP 4 gap path)
- `notes` (the markdown body, parsed)

---

## STEP 4 — Gap handling

If the council isn't found in `Planning_Documents.xlsx`, OR the source
documents can't be parsed reliably, return a structured "manual entry
required" response and prompt the calling skill to ask the user.

The response shape:

```
{
  manual_entry_required: true,
  reason: "council_not_in_xlsx" | "doc_extraction_failed" | "zone_not_found",
  council_slug: "...",
  zone_code: "...",
  candidate_documents: [<rows from xlsx that might apply, even if no exact match>],
  fallback_message: "Planning rules for [council] [zone] are not yet
    cached in the planning skill. To proceed, please confirm the
    following manually: ...",
  required_fields: [<list of required field names>],
  template_path: "/mnt/skills/user/planning/cache/_template.md"
}
```

The calling skill (feaso, cma) is responsible for surfacing this to the
user. Recommended pattern: ask the user to fill in the template, then save
it to `cache/{council_slug}_{zone_code}.md` so the next query is instant.

If candidate documents exist in the xlsx (e.g. the council is there but
extraction failed), point the user at the relevant Source URL — let them
read the planning scheme themselves and paste the key numbers back.

If the user can't provide the rules, fall back to the generic disclaimer:
"Confirm planning rules with a registered town planner before any
investment decision. This report does not include verified council-level
rules for [council]."

DO NOT invent rules. DO NOT guess values from neighbouring councils.
Planning errors propagate into wrong feasibility verdicts and can cause
real financial harm.

---

## Critical rules

- **Never invent or guess planning rules.** If the cache is empty and the
  source documents can't be extracted, return `manual_entry_required: true`
  and let the caller handle it. Do not fall back to "typical" rules from
  another council.
- **The xlsx is the source of truth for what documents exist.** The cache
  is the source of truth for what rules have been extracted. Don't try to
  derive rules from cache without first checking the xlsx — and don't try
  to bypass the xlsx with hardcoded paths.
- **Cache extracts are valid for 24 months.** After that, flag
  `verification_stale: true` and let the calling skill warn the user.
- **The skill does not produce reports.** It returns structured rule data
  to be consumed by feaso, cma, or any other caller.
- **State-level overlays must be returned alongside zone rules.** A VIC
  R1Z extract without ResCode Cl.55/56 is incomplete. The xlsx flags
  state-level instruments by leaving `Council/LGA` blank — always include
  matching state rows in the lookup.
- **TBCO / character / heritage overlays are conditional, not zone-level.**
  Set `character_overlay: conditional` when the overlay applies to some
  parcels in the zone but not all. The actual property check is done by
  feaso/cma using Stash's per-property `planningInfo`.
- **Flood, bushfire, biodiversity hazards are NOT this skill's job.**
  They come from Stash's `get_planning_and_risks` per property. This skill
  only handles zone-scheme rules.
- **Cache files are markdown, not JSON.** Easier to read, easier to edit
  by hand, easier to grep. The YAML frontmatter is the machine-readable
  part; the body is human notes.
- **Council slugs are stable.** Once you set `bcc_qld`, never rename it
  — other skills may have hardcoded references. Add new councils, don't
  rename existing ones.
- **One zone per cache file.** Don't combine LDR + CR2 in one file even
  though they share a source PDF. Separate files = atomic updates.
- **Don't modify `Planning_Documents.xlsx` from inside the skill.** It is
  read-only here. If amendments are needed (new councils, updated dates),
  the user maintains the xlsx separately and re-uploads it.

---

## Phase 2 (future, not yet built)

- Automated PDF extraction — Claude reads the relevant section of a
  council document and writes the cache entry without user intervention
- Smart matching for messy NSW rows — when `Council/LGA` is a precinct or
  address, derive parent council from the source URL automatically
- State-overlay extraction (ResCode, SEPPs) into dedicated cache entries
  that are auto-merged with council-specific rules at read time
- Cross-council comparison ("how does this zone compare to neighbouring
  council X?")
- Planning amendment alerts when `Amended On` dates change in the xlsx

These are NOT built. Phase 1 is manual entry with structured caching,
backed by the xlsx as a directory of available documents.
