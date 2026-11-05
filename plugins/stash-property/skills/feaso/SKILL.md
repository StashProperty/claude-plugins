---
name: feaso
description: "Development and subdivision feasibility (subdivide, KDR, buy + renovate): planning verdict, GDV and costs, exported as PDF, Word or Canva with your branding, plus optional Excel model."
---

# Feasibility Skill — Development & Subdivision Analysis

**Use this skill when** a user mentions feasibility, feaso, subdivide,
subdivision, knockdown rebuild, KDR, development potential, "can I
subdivide", "how many lots", "what can I build", "development feasibility",
"is it worth developing", or any request to assess a property's development
or subdivision viability.

**Full workflow:** resolve the property, pull planning rules, assess the
feasibility verdict, model GDV and costs, and produce a client-ready report.

**Output modes:**

- **Client report (always):** PDF, Word (.docx) or a Canva design, in the
  user's branding. Format and brand are chosen via the `report-export` skill.
- **Excel model (optional):** an .xlsx development feasibility model with
  GDV, costs, sensitivity tables and lot schedule, produced only when the user
  asks for a "feaso spreadsheet" or "Excel model".

Always ask the feasibility type before pulling data.

---

## STEP 0 — Ask Feasibility Type + Export (REQUIRED FIRST)

Before any data lookup, ask ONE card (AskUserQuestion / ask_user_input_v0)
with up to three questions, skipping any already answered (e.g. feasibility
type handed over from the `cma` skill, or format/brand chosen earlier in the
conversation):

1. **What type of feasibility are you assessing?**
   Subdivide the block | Knockdown-rebuild (KDR) | Buy + renovate | Just a quick price guide
2. **How would you like the report?** PDF | Word (.docx) | Canva design
3. **Branding:** Stash (default) | my saved brand | paste a brand URL | unbranded

If "Just a quick price guide" → escalate to the `cma` skill quickval instead
(skip questions 2–3).

Resolve the brand into tokens (PRIMARY, ACCENT, TINT, ALT, TEXT) using
`report-export` before building. Then proceed with the selected type.

---

## STEP 1 — Resolve Subject Property

```
suggest_entity(query="[full address]", type="property")
-> capture propertyId, lat, lon

get_property_profile(propertyId, include={salesHistory:true, valuations:true,
  planningInfo:true, hazards:true, nearby:true, zones:true})
-> bed, bath, car, land area, frontage, building area, year built,
   last sale date + price, corner lot flag, dual access flag,
   zone, TBCO, minLotSize, minRear, minFrontage, minAvgWidth,
   floodingRisk, bushfireRisk, heritageRisk, biodiversityRisk,
   flood detail (river, creek, overland flow, storm tide)

get_property_avm(propertyId)
-> low, mid, high, confidence
```

If handed off from `cma`, reuse the propertyId, lat/lon and AVM already in
context; still pull the planning/hazard profile above.

CRITICAL: Capture lat/lon from this suggest_entity result. Use these exact
coordinates in all subsequent get_market_activity calls — do not use cached
coordinates from a previous property in the same session.

---

## STEP 2 — Planning Rules by State / Zone

### QLD (BCC) — LDR Zone
- Min lot size: 400m2 standard, 600m2 rear/battle-axe
- Min frontage: 10m, min avg width: 10m, min rear access width: 3.5m
- Max height: 9.5m / 2 storeys
- TBCO check: locatedWithinTraditionalBuildingCharacterOverlay
  - TBCO = true -> pre-1947 demolition prohibited; character compliance for all works
  - TBCO = false -> demolition unrestricted; full design flexibility
- Flood risk >= 4: development viability significantly impaired; note DFL requirements

### QLD (BCC) — CR2 Zone
- Min lot size: 300m2 standard, 450m2 rear/battle-axe
- Min frontage: 7.5m, min avg width: 7.5m
- TBCO almost always applies in CR2 — confirm and treat as hard blocker if true

### VIC — General Residential Zone (R1Z) / ResCode Clause 56
- Min lot size: 300m2 per lot (standard), 500m2 if no street frontage
- Min AVERAGE lot size: 400m2 across all proposed lots — THIS IS THE CRITICAL TEST
  A block that passes the 300m2 per-lot test can still fail if the average falls below 400m2
- Min frontage: 7.5m per lot
- Battle-axe access handle: min 3.5m width
- BPA (Bushfire Prone Area) risk 5/5: mandatory BAL assessment under AS 3959
  Construction cost impact: BAL-12.5 ~$5k, BAL-29 ~$30–60k, BAL-40/FZ ~$80–150k+ per dwelling
  Applies to ALL new dwellings including secondary dwellings and granny flats
- No character overlay equivalent in VIC (unless council-specific heritage overlay applies)
- Frankston City / similar councils: confirm with BCC pre-application meeting before lodging

### Other states
Note applicable planning scheme and minimum lot sizes. Recommend registered town
planner confirmation before any investment decision. Use the `planning` skill
for council-level rules where available.

---

## STEP 3 — Feasibility Verdict

### SUBDIVISION VERDICT LOGIC

Run through these blockers in order. Stop at the first hard blocker.

**Hard blockers (any one = NOT FEASIBLE):**
1. TBCO = true AND year built < 1947 AND no structural unsoundness evidence
   -> "Character overlay prohibits demolition — cannot create blank development site"
2. Land area < (zone min lot x 2) + reasonable geometry margin
   -> "Insufficient land area — cannot create two compliant lots"
3. VIC: (land area / proposed lot count) < 400m2
   -> "ResCode average lot size requirement not met — planning permit likely refused"
4. Flood risk >= 4 AND land area only barely meets minimum
   -> "High flood risk materially impairs development viability"

**Marginal flags (note but not automatic fail):**
- Land area meets minimums but only barely (within 10%)
- BPA risk 5/5 in VIC (adds cost but doesn't block)
- Battle-axe required (acceptable but adds cost and reduces lot value)
- No heritage blocker but pre-war building (check TBCO carefully)

**Verdict categories:**
- HIGHLY FEASIBLE: No blockers, clear geometry, clean risk profile
- FEASIBLE: No blockers, minor constraints noted
- MARGINAL: One soft blocker or borderline geometry — professional advice required
- NOT FEASIBLE: One or more hard blockers — state each clearly

### KDR VERDICT LOGIC
- TBCO = true -> "Cannot demolish — KDR not available under current planning"
- Flood risk >= 4 -> "KDR viable but floor level compliance adds material cost"
- Otherwise: FEASIBLE — note any BPA, heritage or overlay constraints

### RENOVATE VERDICT LOGIC
- Always feasible from a planning perspective
- Note TBCO compliance costs if applicable
- Note BPA construction requirements if applicable
- Focus output on value-add potential vs cost vs holding period

---

## STEP 4 — Pull Comparable Sales (for GDV benchmarking)

For SUBDIVISION:
```
get_market_activity(
  where={ lat:[lat], lon:[lon], radius:2000 },
  category="sold", days=730, limit=15,
  propertyType=["Land"]
)
```
Filter to same suburb or immediately adjacent suburb.
Exclude: $0 sales, subdivided lots from larger parcels, land >3x subject lot size.
Calculate $/m2 for each usable sale.
Derive: low / mid / high land rate per m2 -> apply to proposed lot sizes -> GDV range.

For KDR or renovate:
```
get_market_activity(
  where={ lat:[lat], lon:[lon], radius:1000 },
  category="sold", days=365, limit=15,
  minBed=[subject_bed], propertyType=["House"]
)
```
Find best renovated / new build comparable -> KDR end value or renovated ceiling.

---

## STEP 5 — Financial Model (SUBDIVISION)

### Lot geometry
- Calculate proposed lot count: floor(land_area / zone_min_lot)
- Check average: land_area / lot_count >= 400m2 (VIC) or N/A (QLD LDR uses per-lot min)
- Check frontage: total_frontage / lot_count >= min_frontage_per_lot
- Note corner lot premium if applicable (~8–15% above mid-block)

### GDV calculation
For each proposed lot:
  lot_value = lot_area_m2 x land_rate_per_m2 x (1 + corner_premium if applicable)
Total GDV = sum of all lot values

Run three scenarios: LOW (conservative rate), MID (blended rate), HIGH (premium auction rate)

### Cost categories
| Category | Typical Range | Notes |
|---|---|---|
| Purchase price | Market | Assumed — no public sale = estimate from QVAS + dev premium |
| Stamp duty | State rate | QLD: sliding scale; VIC: ~5.25% general rate |
| Legal / DD | $20–35k | Solicitor, title search, due diligence |
| Demo (if required) | $30–60k | Add asbestos survey for pre-1987 construction |
| Asbestos survey + removal | $10–30k | Mandatory for pre-1987 buildings |
| Surveying + scheme plan | $20–35k | Licensed surveyor |
| Planning / ROL application | $25–50k | Town planner + council fees |
| Title creation | $3–5k per lot | Titles office |
| Legal (subdivision) | $20–30k | Solicitor — contracts + ROL |
| Infrastructure contributions | $30–65k per new lot | QLD/VIC — confirm with council |
| Site services / utilities | $25–40k | Connections for new lots |
| Contingency | 5% of dev costs | |
| Finance / holding | Purchase x rate/12 x months | 12–18 months typical |
| Land tax | $15–25k | During hold — confirm with accountant |
| Agent commission | ~2% of GDV | Per lot |
| Marketing | $40–60k total | Photography, digital, print x N lots |
| Conveyancing (vendor) | $8–15k | N x settlements |

### Margin calculation
Net profit = Total GDV - Total costs (excl. tax)
Margin on cost = Net profit / Total costs
Margin on GDV = Net profit / Total GDV

Developer threshold: 20%+ margin on cost is generally considered acceptable for
a land subdivision without construction risk. Below 15% is typically not worth
the effort and risk for most operators.

---

## STEP 6 — Alternative Strategies

When verdict is NOT FEASIBLE or MARGINAL, always suggest alternatives:

**Secondary dwelling / granny flat:**
- QLD LDR: ancillary dwelling up to ~80m2 permitted under Cl.6.2 — no subdivision required
- VIC R1Z: secondary dwelling on same lot subject to Cl.55 setback / site coverage rules
- BPA applies to new dwelling even if secondary — BAL assessment required (VIC)
- Best play when land is undersized or TBCO blocks demolition

**Boundary realignment:**
- Requires neighbour cooperation + planning approval
- Only viable if adjacent lot also benefits from reconfiguration
- Very rare — do not plan around this unless neighbour engagement is confirmed

**Renovation + hold:**
- Almost always viable from a planning perspective
- Avoids subdivision risk, approval timeline, and construction complexity
- Value-add ceiling = best renovated comparable in the suburb
- Present as a lower-risk alternative with comparable or better returns

**Character-sympathetic extension (TBCO properties):**
- Permitted under TBCO subject to design compliance
- Key rules: matching materials, roof pitch, setbacks, maximum addition size
- Engages an architect experienced in character design — $15–30k design cost
- Can add 1–2 bedrooms and a second living area without triggering demolition rules

**Knockdown-rebuild (if no TBCO):**
- Best end value = prestige new build in same suburb (use KDR comp)
- Build cost: $700k–$1.1m for quality 4-bed in Brisbane/Melbourne
- KDR margin = KDR end value - land floor - build cost - holding

---

## STEP 7 — Build the Report (format from STEP 0)

Content and section structure are identical in every format. Build rules
per format come from `report-export`:

- **PDF:** read the pdf skill. Use ReportLab, A4, 18mm margins. Render pages
  and check them before sending.
- **Word:** read the docx skill. Arial; tables with PRIMARY headers; page
  breaks between sections; convert to PDF and render to check.
- **Canva:** call `generate-design` (report), then rebuild the content page by
  page with `edit-design`. Draw the verdict panel, compliance table colours
  and any GDV/margin charts with native shapes. Confirm with the user before
  committing.

File / design name: `[StreetNo]_[StreetName]_[Suburb]_[Subdivision|KDR|Renovate]_Feasibility`
(.pdf / .docx / Canva title).

### Cover block
1. Title bar (ALT background): "[SUBDIVISION | KDR | RENOVATION] FEASIBILITY REPORT" | address | date
2. Verdict panel: coloured border matching verdict (GREEN=feasible, AMBER=marginal, RED=not feasible)
   Verdict label + 1-sentence summary of blockers or confirmation of feasibility
3. Agency logo (or placeholder) + "Prepared by [Agent name]" when a non-Stash brand is used

### Colour palette — brand tokens

The brand chosen in STEP 0 supplies PRIMARY / ACCENT / TINT / ALT / TEXT
(see `report-export`). Stash default:

- PRIMARY = #32374A (headings, table headers, rules)
- ACCENT = #3555FF (links, highlight rules, key figures)
- TINT = #EEF1FF (highlighted total rows)
- ALT = #F4F5F8 (zebra rows, cover bar)
- TEXT = #333333, GREY_MID = #666666

Verdict and risk colours are semantic and never change with brand:

- HIGH_BG = #FFF0EE, HIGH_TX = #A82020
- MED_BG = #FFF8E6, MED_TX = #C87000
- LOW_BG = TINT, LOW_TX = PRIMARY
- NONE_BG = #F0FAF8, NONE_TX = #1B7A3E

If ACCENT is light (e.g. yellow), use it only as a fill behind PRIMARY text.

### Report sections

**Section 1 — Property Profile**
Table: all key attributes including land area, frontage, zone, TBCO, all hazard
scores, last sale, QVAS site value, AVM range. Highlight hazard rows in matching
risk colour. Highlight TBCO = true in amber. Highlight all-clear profile in green.

**Section 2 — Planning Rules Compliance**
Table: Rule | Requirement | Subject | Result (PASS / FAIL / CONDITIONAL)
Cover all applicable zone rules: per-lot min, average min (VIC), frontage, height,
TBCO, flood, BPA. Colour result column: PASS=green, FAIL=red, CONDITIONAL=amber.

**Section 3 — Blocker Detail** (if any blockers exist)
One paragraph per blocker explaining:
- The exact rule that is breached
- Why it cannot be overcome without intervention
- What evidence would be needed to revisit

**Section 4 — Indicative Lot Geometry** (if feasible/marginal)
Table: Lot # | Description | Area (est.) | Frontage | Street | Notes
Include corner lot premium note. Mark as indicative — licensed surveyor required.

**Section 5 — Comparable Land Sales** (if feasibility run)
Table: Address | Date | Sale Price | Land | $/m2 | Notes
Show adopted blended rate in highlighted total row.

**Section 6 — Financial Feasibility** (if feasible/marginal)
Table: Item | Low | Mid | High | Assumptions
Rows: GDV by lot group, then total GDV, then each cost category, then grand total,
then net profit, then margin on cost.
Include NOTE row if construction of new dwellings is not included in the model.

**Section 7 — Risk Register**
Table: Risk | Rating | Detail
Cover: planning approval risk, purchase price uncertainty, market absorption,
timeline, asbestos/contamination, any positive factors.

**Section 8 — Alternative Strategies** (always include)
Table: Option | Feasibility | Notes
Cover: secondary dwelling, renovation, boundary realignment, KDR.
Colour rows: POSSIBLE=green, UNLIKELY=amber, NOT RECOMMENDED=red.

**Section 9 — Recommended Next Steps**
Table: # | Action | Who | Priority
Priority colour: IMMEDIATE=red, BEFORE OFFER=amber, PRE-SETTLEMENT=green.
Always include: solicitor title search, town planner pre-app meeting, independent
valuation, licensed surveyor, asbestos assessment if pre-1987.

**Disclaimer**
Standard preliminary analysis disclaimer. Confirm planning rules with town planner.
Confirm flood data with council. Note that planning schemes are subject to amendment.

---

## STEP 8 — Excel Model (when requested)

When the user asks for a "feaso spreadsheet", "Excel model", "feasibility model",
or similar:

Read /mnt/skills/public/xlsx/SKILL.md before writing any code.

Use openpyxl. Run recalc.py after generating. Fix all errors before presenting.
Output to /mnt/user-data/outputs/[StreetNo]_[StreetName]_[Suburb]_DevFeaso.xlsx

Header and section fills use the brand's PRIMARY (or ACCENT for section
bands) from STEP 0; Stash default otherwise.

### Colour coding (industry standard)
- Blue text (0,0,255): hardcoded inputs — cells users will change for scenarios
- Black text (0,0,0): all formulas and calculations
- Green text (0,128,0): links pulling from other sheets in same workbook

### Sheet structure (6 sheets)

**Sheet 1 — Summary**
- Title block (PRIMARY header)
- Key metrics panel: Purchase Price | GDV | Total Costs | Net Profit |
  Margin on Cost | Margin on GDV | Return on Equity | Implied IRR
  All formula-linked to other sheets. TINT highlight on profit and margin rows.
- Scenario comparison table: LOW | MID | HIGH | STRETCH
  Rows: Purchase Price | Land Rate/m2 | GDV | Total Costs | Net Profit | Margin on Cost
- Subject property profile (static reference data)
- Note row: blue = inputs, black = formulas

**Sheet 2 — Assumptions**
All inputs in one place. Three columns: Input | Value | Source/Note
Section headers in ACCENT (or PRIMARY if ACCENT is light) with contrasting text.
Sections: ACQUISITION | SITE | LAND RATE ASSUMPTIONS | CONSTRUCTION/DEVELOPMENT |
FINANCE & HOLDING | SALES & MARKETING
Blue text for all hardcoded input values.
Black text for any calculated inputs (e.g. average lot size = total area / lot count).

**Sheet 3 — GDV**
Per-lot valuation table: Lot | Area (m2) | Land Rate ($/m2) | Gross Value | Premium | Notes
Land rate cells formula-linked to Assumptions sheet mid/low/high rate cells.
Corner lots get premium formula linked to Assumptions corner premium %.
GDV summary table: MID | LOW | HIGH | STRETCH
Rows: Total GDV | Average $/m2 | Average lot value
Land comparable sales benchmark table below (hardcoded reference data, black text).

**Sheet 4 — Costs**
Cost waterfall: Item | MID | LOW | HIGH | Note
Section subtotals after each category.
Grand total row (TINT highlight) formula = sum of all subtotals.
All cost formulas linked to Assumptions sheet where possible.
LOW/HIGH columns are +/- % adjustments from MID.

**Sheet 5 — Sensitivity**
Two sensitivity tables:
1. Net Profit ($) — rows = purchase prices, columns = land rates
2. Margin on Cost (%) — same axes
Both formula-driven from Assumptions inputs.
Column widths set to display all values clearly.
Notes row explaining assumptions used (hold period, finance rate, stamp duty rate).

**Sheet 6 — Lot Schedule & Milestones**
Lot schedule: Lot # | Description | Area (m2) | Land Rate | List Price | Sale Price | Settled? | Notes
Sale Price column = blue input (user fills in as lots sell).
Total row at bottom formula-summing area, list price, sale price.
Project milestone table below: # | Milestone | Target Date | Responsible | Status
Pre-populated with standard subdivision milestones:
  title search -> pre-app meeting -> valuation -> surveyor -> exchange ->
  settlement -> asbestos -> demo -> ROL lodgement -> approval ->
  survey plan -> titles -> marketing -> all settled

### Formula rules
- Use Excel formulas for ALL calculations — never hardcode a calculated value
- All cost formulas reference Assumptions sheet cells, not hardcoded numbers
- All GDV formulas reference Assumptions land rate cells
- Sensitivity table formulas must be self-contained (no cross-sheet dependencies
  that create circular references)
- Run recalc.py and fix all errors before presenting the file

---

## Critical rules

- Always ask feasibility type (and export format + brand, in the same card)
  before pulling any data
- Never produce a feasibility conversationally — always produce a report in the
  chosen format (PDF, Word or Canva)
- When verdict is NOT FEASIBLE: still complete the full report including
  alternative strategies and next steps — the client needs to know what to do instead
- VIC R1Z: the 400m2 average test is the primary blocker — always calculate it
  explicitly. Many blocks that pass the 300m2 per-lot test still fail this test.
- BPA in VIC: always quantify the BAL cost range in the financial model — it is
  a material cost item, not a footnote
- TBCO: if true and building is pre-1947, this is a HARD BLOCKER for demolition-
  dependent strategies. Do not soften this finding.
- Flood risk >= 4: must be quantified in the cost model (DFL compliance, elevated
  construction) — not just noted in the risk table
- Each feasibility is fully self-contained — never reference data from a previous
  property or conversation; pull all data fresh (except the cma hand-off context)
- Always use current property lat/lon for get_market_activity — never use cached
  coordinates from a previous session
- The Excel model is optional — only produce it when the user explicitly asks
  for a spreadsheet, model, or feaso Excel file
- Never reproduce another company's logo — use the user's own brand kit logo or
  an "Agency logo" placeholder
- After presenting files or the Canva link, confirm in chat:
  - Format and brand used
  - Feasibility verdict (FEASIBLE / MARGINAL / NOT FEASIBLE)
  - Primary blockers (if any) or primary opportunity
  - Proposed lot count and indicative GDV range (if feasible)
  - Key next step the client should take
