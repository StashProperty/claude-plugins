---
name: cma
description: "Two-stage property valuation: quickval in chat, then a buyer CMA, a 6-page seller appraisal (price at the end) or a full vendor CMA, exported as PDF, Word or Canva in your brand; feaso hand-off for development."
---

# CMA Skill — Two-Stage Property Valuation

**Stages:**

- **Stage 1** is the fast quickval, in chat.
- **Stage 2** is the full CMA report, only triggered if the user asks for it.

**Triggers:** any property valuation request, e.g.

- "what's it worth", "quick val", "ballpark", "price guide", "appraisal"
- "CMA", "comps", "comparable sales", "estimate", "market value"
- "what should I pay", "what should I offer", "what can I sell for", "help me price"
- "run a CMA", "do a market analysis", "property report"
- any address paired with buying, selling, pricing, development, subdivision, KDR or feasibility language

Ask the role question (buying / selling / development) only at the moment of
escalation, never before.

**Stage 2 output:** PDF, Word (.docx) or a Canva design, in the user's
branding. Format and brand are chosen once, via the `report-export` skill.
If the user says "put it in a PDF", "do it in Canva" or "make it a Word doc"
at any point, re-render in that format from the data in context.

The same property data is fetched once at Stage 1 and reused at Stage 2.
Never re-fetch what's already in conversation context.

---

## STAGE 1 — Quickval (always runs first)

Fast conversational valuation. Maximum 4 Stash calls. No document. No scoring.
No adjustments. Respond directly in chat.

### Workflow

#### Call 1 — Resolve property
```
suggest_entity(query="[full address]", type="property")
-> capture propertyId, lat, lon, land area
```

#### Call 2 — Profile + AVM (run together)
```
get_property_profile(propertyId, include={salesHistory:true, valuations:true})
-> bed, bath, car, land, year built, last sale date + price

get_property_avm(propertyId)
-> low, mid, high, confidence
```

#### Call 3 — Wide comp fetch (used by both stages)
```
get_market_activity(
  where={ lat:[lat], lon:[lon], radius:1000 },
  category="sold", days=180, limit=15,
  minBed=[subject_bed - 1], propertyType=["House"]
)
```

CRITICAL: Use lat/lon from the current property's suggest_entity result.
Never reuse coordinates from a previous property in the same session.

**Fallback rule:** If fewer than 8 comps return at 1km, run ONE additional
call at radius:1500. Do not widen further. Do not extend days beyond 180
unless the second call also returns < 8.

### Quickval response format

Respond in chat — no headers, no tables, keep it tight. Display only the
TOP 5 closest comps even though you fetched 15 (the rest sit in context for
Stage 2). Include the propertyId-based Stash link on the closest comp.

```
**[Address]** — [bed/bath/car, land, year]
Last sold [date] at $[price] ([X]-year hold)

**Price guide: $X.XXm – $X.XXm**
AVM mid: $X.XXm ([confidence] confidence)

**Nearby sales (last 6 months):**
- [[Address]](https://stashproperty.com.au/app/properties/{propertyId}) — [date], $[price], [bed]b[bath]ba, [land]m2
- [Address] — [date], $[price], [bed]b[bath]ba, [land]m2
- [Address] — [date], $[price], [bed]b[bath]ba, [land]m2
- [Address] — [date], $[price], [bed]b[bath]ba, [land]m2
- [Address] — [date], $[price], [bed]b[bath]ba, [land]m2

**Quick take:** 1–2 sentences. Anchor comp + key risk + AVM reliability.
If last sale < 3 years, note it. If VIC BPA 5/5, flag BAL assessment.
```

### Quickval rules

- No document — chat only, always
- No adjustments — report sale prices as-is
- No scoring — list comps as context, not ranked evidence
- 4 calls maximum (3 if fallback not triggered)
- Each property is independent — never reference previous queries
- If AVM confidence is VeryLow or Low, flag it explicitly
- Format prices as $X.XXm throughout

### Stage 1 → Stage 2 handoff

End the quickval with:

> **Want me to write this up as a full report?** Let me know if this is for
> buying, selling, or development and I'll take it from there.

When the user responds, route based on their answer:

- **Buying** → Stage 2 buyer CMA (this skill, buyer mode)
- **Selling** → Stage 2 seller CMA (this skill, seller mode)
- **Development** → ask sub-type next, then hand off to the `feaso` skill

If their answer is ambiguous ("yes" / "go ahead" / "do it"), ask the
buying / selling / development question explicitly. Do not assume.

**Sub-type question (development branch only):**

If they pick development, ask ONE follow-up question, single-select:

> **What kind of development?**
> - Subdivide as-is (split land, no demolition)
> - Knockdown rebuild (single new dwelling)
> - Demolish + multi-dwelling (townhouses, duplex, small-lot subdivision)
> - Buy + renovate (cosmetic / structural reno, no demolition)

Use `ask_user_input_v0` (or AskUserQuestion) with one question, single_select,
four options.

Do NOT ask hold strategy, build standard, equity mix, or target margin at
this stage. Defaults are inferred by the feaso skill (sell-on-completion,
mid-spec build, 70% LVR, 20% target margin on cost). If the user wants to
override these later, feaso handles it.

After the sub-type answer, hand off to the `feaso` skill with the
following context:

- Resolved propertyId, lat, lon (from quickval Call 1)
- Subject profile data (from quickval Call 2)
- AVM range + confidence (from quickval Call 2) — used as the buy-in cost
- Selected dev sub-type (from the question above)
- Export format and brand, if already chosen in this conversation

The feaso skill is responsible for everything beyond this point —
planning rules, build costs, GDV modelling, sensitivity, and the report /
Excel output.

Do not run the buyer/seller CMA Stage 2 if development was selected. Do
not produce a CMA report as a "bonus" — the user asked for a feasibility,
they get a feasibility.

**Critical:** the data Stage 1 fetched is mostly NOT what feaso needs.
Feaso needs zoning, character overlay, flood, slope, build cost per m²,
and dwelling-type sale values per suburb. The reuse here is narrow: the
propertyId (skips address resolution) and the AVM (used as buy-in cost).
Feaso will pull its own planning, risks, and dev-comp data.

---

## STAGE 2 — Full CMA (only on explicit escalation)

### STEP 0 — Confirm role, then export format + brand

1. **Role.** If the user already stated buying or selling at the handoff, skip
   this. Only ask the role question if it's still ambiguous. Never mix buyer
   and seller framings in one document.
2. **Export + brand.** As a separate, second ask, load the `report-export`
   skill and ask its one card:
   - How would you like to export it? PDF / Word (.docx) / Canva design
   - Branding: Stash (default) / my saved brand / paste a brand URL / unbranded

   Skip whichever the user has already answered ("do it as a PDF", a brand
   used earlier in the chat). Resolve the brand into tokens (PRIMARY, ACCENT,
   TINT, ALT, TEXT) per `report-export` before building.
3. **Seller document style** (SELLING only, ask in the same card):
   - **Seller appraisal (6 pages, price at the end)**: the default whenever the
     user says "appraisal", "for the owner", "for the seller" or "to give the
     vendor". See "SELLING MODE — Seller appraisal" below.
   - **Full vendor CMA (8 sections)**: the detailed technical version.

An agent's own preparation before the listing appointment ("pre-appraisal",
"brief me") is a different document. Hand it to the `pre-appraisal` skill.

If the user picked development at handoff, you should NOT be in this
section — the workflow forks to the `feaso` skill before STEP 0. If you
find yourself here for a development request, that's a bug — re-route.

### STEP 1 — Reuse Stage 1 data

The following are already in conversation context — DO NOT re-fetch:
- Property profile + sales history + valuations (from quickval Call 2)
- AVM low/mid/high + confidence (from quickval Call 2)
- 15-comp market_activity result (from quickval Call 3)

### STEP 2 — Pull planning + risks (new call)

```
get_planning_and_risks(propertyId, include_nearby_das=true,
                      nearby_radius_m=2000, nearby_days=730)
```

This is the only new Stash call required for the full CMA.

### STEP 3 — Land-led check (conditional, rarely runs)

Only run this step if ALL conditions are met:
1. Subject land area >= zone minimum lot size for subdivision
2. No flood risk >= 4/5
3. No heritage listing
4. Land genuinely interesting (>= 500m² inner, >= 600m² middle suburbs)

If all pass:
```
get_market_activity(
  where={ lat, lon, radius:2000 },
  category="sold", days=730, limit=50,
  propertyType=["Land"]
)
```

Filter to same/adjacent suburb. Calculate $/m² → land floor.
- Land floor > house CMA → land-led valuation, update cover/offer/reserve
- Land floor <= house CMA → house CMA leads; include as Section 2b context

VIC R1Z note: 400m² average test means many blocks > 300m² min are still
not subdivisible. Run the average test before concluding land value applies.

### STEP 4 — Score & adjust comparables

Use the 15 comps already in context. Score each:

- **HIGH:** bed match, land ±20%, era ±15 years, ≤18 months, ≤800m
- **MEDIUM:** 1–2 attributes differ, ≤36 months, ≤1km
- **LOW:** 2+ attributes differ, dev/investment sale, edge of radius

Adjustments to subject (applied to indexed price):

| Factor | Rate (Brisbane) | Notes |
|---|---|---|
| Land size | $800/m² | Per m² above/below subject (adjust for other markets) |
| Bathrooms | $40,000 | Per bath above/below |
| Car spaces | $20,000 | Per space above/below |
| Pool | $50–80k | Discount comp if subject has no pool; add to comp if subject has one and comp doesn't |
| Road type | Qualitative | Arterial = discount vs quiet street |
| Condition | Qualitative | Tenanted/investor = floor, not guide |
| Flood-free | Qualitative | Premium when comp is flood-free, subject isn't |

Indexing applies only to Tier 4–5 (>18 months). For comps within 6 months,
multiplier = 1.000.

If the user advises a change since the last sale (e.g. a pool added),
apply it to the subject before adjusting and note it as vendor-advised.

### STEP 5 — Weighted estimate

```
avg_high   = mean of HIGH adjusted values
avg_medium = mean of MEDIUM adjusted values
weighted   = (0.60 × avg_high) + (0.30 × avg_medium) + (0.10 × AVM_mid)

// Buying mode
opening_offer = weighted × 0.93     (~7% below — risk/condition discount)
max_bid       = weighted × 1.05     (~5% above — hard ceiling)

// Selling mode
listing_low   = weighted × 0.97
listing_high  = weighted × 1.05
price_guide   = listing_low × 0.97  (quoted as "Offers over $X.XXm")
reserve       = weighted × 0.985    (at or just below CMA midpoint)
```

If HIGH count is sparse (n=1), widen to n=2 by promoting the closest
MEDIUM. If still sparse, fall back to (0.85 × avg_medium) + (0.15 × AVM_mid)
and flag confidence as Medium in the report.

### STEP 6 — Configuration caveat (deterministic, no web search)

If last sale was within 5 years AND no renovation evidence in the comp
listing descriptions or sales history, add the standard caveat to the
Valuation Summary:

- Buying: "⚠ Configuration unverified since [date]. Request inspection
  records before making an offer."
- Selling: "⚠ Configuration unverified since [date]. Physical inspection
  recommended before listing."

Do NOT run a web_search to check for renovations or DAs. The caveat fires
on hold-period logic alone. Web searches at this step rarely return
useful data and burn ~5k tokens for no quality gain.

---

## STEP 7 — Build the report (format from STEP 0)

Content and section structure are identical in every format. Build rules
per format come from `report-export`:

- **Word:** read the docx skill.
- **PDF:** read the pdf skill. Use ReportLab and build directly from the data
  in context; never convert the Word file.
- **Canva:** copy the last design of the same report if one exists;
  otherwise generate the design and rebuild the content page by page with
  native shapes for any charts. Use `report-export` → "Report layout kit".
  Confirm with the user before committing.
- **Photos in PDF/Word:** use the thumbnail method in `report-export`.

### BUYING MODE — 6-section report

**Cover page**
- Soft ALT background bar, PRIMARY rule lines
- Badge: "BUYERS AGENT" in ACCENT above title (one accent only)
- Title: "COMPARATIVE MARKET ANALYSIS"
- Sub-label: "Prepared for Buyer — Confidential · Do not distribute"
- Property address + config line below
- Value label: "ESTIMATED FAIR VALUE / MAXIMUM BID"
- Price: fair value range
- Sub-label: "Weighted CMA: $X.XXm · N comps · Xkm / X months"
- Agency logo (or placeholder) + "Prepared by [Agent name]" when a non-Stash brand is used

**Running header** (PDF/Word): `BUYERS AGENT CMA — [address] | Prepared for Buyer — Confidential`

**Section 1 — Subject Property**
Table rows: Address, Type, Config, Land, Building Area, Year Built, Last Sale
(flag vendor hold period in amber if < 5 years), Gov. Valuation, AVM Range.
Opening paragraph: flag hold period and unverified condition as buyer levers.

**Section 2 — Comparable Sales — Xkm Radius, Last X Months**
Opening line states the tier (e.g. "Tier 1 — N sales within 1km, no indexing").
Table columns: Address (hyperlinked) | Sold | Sale $ | Adj. $ | Bd | Ba | Cr | Land | Built | Pool | Relev.
- Format all prices as `$X.XXm`
- Relev. column: GREEN=HIGH, AMBER=MEDIUM, RED=LOW with colour fills
- Link each address to `https://stashproperty.com.au/app/properties/{propertyId}`
- Footer note: adjustment rates used

**Section 3 — Comparable Sales Commentary**
Buyer intelligence, not neutral analysis. For each key comp:
- Anchor (strongest comp near subject)
- Floor (lowest sale, explain the discount)
- Pool premium not in subject — name and quantify
- Frame everything as "what this means for your offer"

**Section 4 — Valuation Summary**
Table: HIGH avg | MEDIUM avg | AVM mid | Weighted CMA (TINT highlight)
Caveats below table in amber italic.

**Section 5 — Risk & Planning — Buyer Due Diligence**
8-row condensed table (must fit on one page):
Zone & Overlay | Development | Flood Overall | Flood River | Flood Local |
Storm Tide | Bushfire/Heritage/Biodiversity | Nearby DAs

Risk shading: NONE=green, LOW=soft tint, MED=amber, HIGH=red
If floodingRisk >= 4: bold the finding, name as negotiating lever.
Close with bullet action list: flood report, building inspection, DA check.

**Section 6 — Negotiation Strategy**
Table rows: Fair Value | AVM Range | Opening Offer | Max Bid (red) | Flood |
Hold Period | Character Overlay | DOM | Condition | Confidence

Closing paragraph: direct buyer advice. Opening offer rationale, primary
levers by priority, hard ceiling with reason.

### SELLING MODE — 8-section report

**Cover page**
- Same styling as buyer mode, no buyer badge
- Title: "COMPARATIVE MARKET ANALYSIS"
- Sub-label: "Prepared for Vendor — Confidential · [date]"
- Value label: "RECOMMENDED LISTING RANGE"
- Price: recommended listing range

**Running header** (PDF/Word): `COMPARATIVE MARKET ANALYSIS — [address] | Prepared for Vendor — Confidential`

**Section 1 — Subject Property** — neutral vendor presentation, no leverage framing.
Planning/hazards row coloured: green if all clear (selling point), amber/red if risk.

**Section 2 — Suburb Growth Context**
If Tier 1–2: state "All comps within 6 months — no indexing required."
Compact table: Metric | Suburb | Corridor | Note
Rows: Median price, 12-mo growth %, median DOM, buyer competition, indexing required?

**Section 3 — Prior Sale Histories**
Repeat sales table for key comps: Property | Prior Sale | Recent Sale | Hold | Gain | Note
Demonstrates capital growth narrative. Highlight subject's own gain.

**Section 4 — Comparable Sales** — same format as buyer mode.
If Tier 3+: add "Indexed $" column.

**Section 5 — Risk & Planning — Vendor Disclosure**
Same 8-row structure, column heading "Vendor Action / Note":
- Flood NONE: "Include council flood report — flood-free is a premium asset"
- Flood HIGH: "Obtain council report, supply proactively in marketing pack"
- TBCO NONE: "Highlight full renovation flexibility in campaign copy"
- Subdivision potential: "Include STCA note to broaden buyer pool"
Close with vendor disclosure checklist.

**Section 6 — Valuation Summary**
Table: HIGH avg | MEDIUM avg | AVM mid | Weighted CMA (TINT) |
Recommended Listing Range | Pre-auction Price Guide | Suggested Vendor Reserve

**Section 7 — Campaign Strategy** (selling-only)
Recommended method (auction / private treaty / EOI), campaign duration,
inspection schedule, photography/staging notes.

**Section 8 — Vendor Disclosure Checklist** (selling-only)
Bullet list: flood report, pre-sale building report, pool safety cert,
known defects disclosure.

### SELLING MODE — Seller appraisal (6 pages, price at the end)

This is the owner-facing appraisal. It tells the story in order: your home,
then your market, the sales, how they compare, and finally our price. **No
value appears before page 6**: not on the cover, the home page or the sales
cards. Page geometry is in `report-export` → "Report layout kit". Copy the
last seller appraisal design in Canva if one exists.

**Extra data for this layout** (on top of STEPS 1–5):

- `get_suburb_context(slug, statistics:true, demographics:true)`:
  - median and the annual medians for the last 2–3 years
  - 12-month growth by bed count
  - days on market over 12 months and the latest quarter
  - houses for sale and new in the last 30 days
  - sales over 12 months
  - clearance, stock on market and vacancy
  - rent
  - 3- and 10-year CAGR and 10-year growth
  - population growth, household income, owner-occupier share
  - IRSAD/IEO percentile, school ICSEA, distance to the CBD
- **Prior sales for each comp** from `get_property_profile(include={salesHistory:true, listingHistory:true})`. Compute prior to recent and the % change. Label what changed:
  - **rebuilt** when the build year is later than the prior sale; show "rebuilt", not a %.
  - **extended (3 to 4 bed)** when the bed count rose between listings.
  - otherwise **largely unchanged**: same home, market growth.
  - Also add any current listing that sold in the last 2 years: sold $X, now asking $Y (+Z%).
- **Competition:** the same pull as `listing-update` STEP 2A, up to 6 listings with campaign status.

**Pages**

1. **Cover**
   - Hero photo of the subject: its listing photo, one supplied by the agent, or in sample mode an AI image.
   - Title "Property Appraisal" and the eyebrow "PREPARED FOR THE OWNERS · <MONTH YEAR>".
   - Address and specs.
   - A dark panel with two suburb stats: "<SUBURB> HOUSE MEDIAN $X.XXm" and "<SUBURB> HOUSES · 10-YEAR GROWTH +X%".
   - Footer: logo, "Prepared by <agency>", date.
2. **Your home**
   - Four stat rows: land, floor area, built (age, cars, pool), rental estimate.
   - Dark side panel "What buyers will see": 5–6 short, honest points (condition or era, a rare feature, pool, planning freedom, location, flood band with the council report as the fix).
   - Tint band "Your home's history": up to 3 figures from salesHistory, plus "+X%, <suburb> houses, 10 yrs".
3. **Your market**
   - Competition table: Listing | Home | Asking | Days | Campaign so far.
   - A takeaway line, factual and not alarmist.
   - Suburb table with columns Measure | Now | Context, 9 rows:
     - median price
     - 2-year trend
     - 12-month growth (by bed)
     - days on market (12 months vs latest quarter)
     - houses for sale (new in 30 days, over 60 days)
     - sales over 12 months
     - auction clearance
     - stock · vacancy
     - long-run growth
   - "What supports value in <suburb>": 5–6 bullets from demographics and nearby projects.
   - Include only figures Stash returns.
4. **Recent sales near you**
   - A 2×2 grid of photo cards. Each shows: name · distance, a specs line, and "Sold $X.XXm · Mon ’YY · N days on market". No adjusted figures here.
   - Below: 3 "your closest competition" photo tiles showing asking price and status.
5. **Compared with your home**
   - Adjustment table: Sale | Sold | Land | Bath | Car | Pool | Floor | Adjusted | Rating.
   - A plain-English footnote: "Adjusted = what each sale would likely have fetched if it were your home". Explain HIGH and MED, and flag missing data.
   - "Your home in context": 3 big figures (what you paid, 10-year CAGR, last 12 months).
   - Tint section "How these homes have changed in value": 4 blocks, each "address · +X%" plus "$prior Mon ’YY to $recent Mon ’YY. <what changed>". End with a footnote for any relisted resale.
6. **Our appraisal**
   - Weighting table: closest matches (HIGH), wider group (MED), Stash AVM, and weighted value, with their weights.
   - A note on why the AVM differs.
   - A dark price panel:
     - "OUR APPRAISAL · LIKELY SELLING RANGE"
     - the big range (weighted × 0.97 to × 1.05)
     - three tiles: weighted value, suggested price guide, Stash AVM
   - A short "Why the guide sits where it does" paragraph. It must say the reserve and method are the owner's call.
   - Disclaimer: an opinion of likely selling price, not a formal valuation; Stash data as at <date>.
   - Drop the guide tile and paragraph if the user wants the agent to cover the guide in person.

**Language:** written to the owner ("your home") in a warm, factual tone.
Never use "overpriced" or "reduce". Leave out leverage framing and objection
scripts.

**Naming:** `Appraisal_<Street>_<Suburb>`. In Canva: "Property Appraisal –
<address>".

**Build:**

- **PDF:** fill `report-export/examples/appraisal_example.json` with this
  report's data and run `report-export/scripts/build_appraisal.py`. The
  layout is fixed, so every user's PDF matches the reference.
- **Canva:** start from the Property Appraisal template link in
  `report-export` → "Canva templates" if one is listed. Otherwise follow
  the "Otherwise" route there.
- **Photos:** use the thumbnail method in `report-export`.

### Formatting rules (all formats)

- All prices in tables: `$X.XXm` (two decimals — never three, never raw `$1,520,000`)
- Dates in comp tables: short month + 2-digit year with typographic right-quote, e.g. `Nov ’25`, `Mar ’26` (use `’` not straight apostrophe)
- Relevance labels in comp table: `HIGH`, `MED`, `LOW` (never the full word "MEDIUM")
- Word: apply `noWrap: true` to every numeric / categorical cell in the comp table (Sold, Sale $, Adj. $, Bd, Ba, Cr, Land, Built, Pool, Relev.). The address column is the only one allowed to wrap.
- Font: Arial (Word), Helvetica (PDF), brand kit font or a clean sans (Canva)
- Page breaks before every major section
- Risk & Planning section must fit on one page
- PDF: avoid glyphs Helvetica lacks (→ ≤ − ☐ ²) — write "to", "<=", "-", "sqm"

### Colour palette — brand tokens

The brand chosen in STEP 0 supplies the tokens. When the brand is Stash
(default) or unspecified, use:

| Token | Stash hex | Use |
|---|---|---|
| PRIMARY | `#32374A` | Section titles, table headers, rules, running header — dominant colour |
| ACCENT | `#3555FF` | Links, weighted-row label, cover price-panel top border, buyer badge — small high-signal accents only |
| TINT | `#EEF1FF` | Weighted-row / highlight background |
| ALT | `#F4F5F8` | Zebra rows, cover bar background |
| TEXT | `#333333` | Body text |

With a custom brand: map the brand's dominant dark colour to PRIMARY and its
signature colour to ACCENT (see `report-export`). If ACCENT is light (e.g.
yellow), use it as a fill behind PRIMARY text, never as text on white.

Risk colours are semantic and never change with brand:

| Risk | Background | Text |
|---|---|---|
| HIGH | `#FFF0EE` | `#A82020` |
| MED | `#FFF8E6` | `#C87000` |
| LOW | TINT | PRIMARY |
| NONE | `#F0FAF8` | `#1B7A3E` |

**Implementation rules:**
- Cover title text: PRIMARY on ALT background
- Cover bottom rule: 12-size border in PRIMARY
- Cover price panel: white bg, top border 18-size in ACCENT (single accent line)
- Section title text: PRIMARY, bottom rule 12-size in PRIMARY
- Table headers: bg PRIMARY, text white, bold
- Running header text colour: PRIMARY, rule under header in PRIMARY
- Buyer-mode "BUYERS AGENT" badge: ACCENT on ALT cover bar
- Weighted-row in valuation summary: bg TINT, text PRIMARY bold
- Canva: cover hero photo + ACCENT panel; charts drawn natively; subject highlighted in ACCENT

### Output

- Word: `/mnt/user-data/outputs/CMA_[StreetName]_[Suburb]_[Buyer|Seller].docx`
- PDF: `/mnt/user-data/outputs/CMA_[StreetName]_[Suburb]_[Buyer|Seller].pdf`
- Canva: design titled `CMA – [Street], [Suburb] ([Buyer|Seller])`; share the edit link after the user approves the commit
- Send files with the file-sharing tool (SendUserFile / present_files)
- Confirm in chat:
  - Mode (buying / selling), format and brand
  - Weighted CMA + offer range or listing range
  - Flood risk rating + action
  - Comp tier and number used

### Re-rendering

If the user later asks for another format ("put it into a PDF", "now do it
in Canva"), rebuild from the data already in context in that format with
the same brand. Do not re-fetch and do not convert file-to-file.

---

## Key data sources

| Source | Tool | Use |
|---|---|---|
| Property profile | get_property_profile | Config, sales, gov val, planning, hazards |
| AVM | get_property_avm | Automated valuation range |
| Comparable sales | get_market_activity | Tiered radius search — pass current lat/lon |
| Planning & risks | get_planning_and_risks | Zone, overlays, hazards, nearby DAs |
| Indexing (Tier 4–5 only) | get_suburb_context (statistics) | Stash suburb growth rates; web (domain.com.au / realestate.com.au) only if Stash has none. Never Cotality/CoreLogic |
| Export + branding | report-export skill | Format question, brand tokens, Canva build |

---

## Critical rules

- **Quickval always runs first.** Even if the user explicitly asks for a CMA
  or a feasibility, the data fetch IS the quickval — display the chat summary,
  then ask the role question (buying / selling / development).
- **Three-way role question, asked once.** After quickval, the role question
  is buying / selling / development. Never assume the role from earlier
  context — ambiguous answers like "yes" / "go ahead" must be re-asked.
- **Export + brand asked once, after the role.** One card via `report-export`;
  skip anything already answered. Never ask format before the quickval.
- **Development branches off this skill.** If the user picks development,
  ask the sub-type question, then hand off to the `feaso` skill. Do NOT
  produce a CMA report when feasibility was requested.
- **One question at a time during escalation.** Role, then (if needed) dev
  sub-type or export/brand. Do not stack the role question with anything else.
- **Never re-fetch data already in context.** Property profile, AVM, and
  market_activity from Stage 1 carry forward to Stage 2 (CMA branch).
- **Buying and selling are entirely separate documents** — never mix framing.
  The buyer report's Section 3 (Comp Commentary) is the highest-value section.
- **Flood risk >= 4** must be explicitly named as a negotiating lever (buyer)
  or proactive disclosure (seller).
- **Flood-free status** must be named as a marketing asset in selling mode.
- **Pool comps** always adjust for pool difference (~$50–80k).
- **VIC R1Z** always run the 400m² average test before concluding subdivision.
- **No web_search for post-sale changes.** Use deterministic hold-period logic.
- **Each CMA is fully self-contained** — never reference previous properties.
- **Always pass current property lat/lon** to get_market_activity. Never reuse
  coordinates from a previous property in the same session.
- **Never reproduce another company's logo** — use the user's own brand kit
  logo or an "Agency logo" placeholder.
- **For low-confidence AVM or unusual properties**, recommend a licensed valuer.
