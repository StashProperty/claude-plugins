---
name: find-suburbs
description: Ranks Australian suburbs against a user's strategy (growth, yield, development, renovation, family, balanced, or house-vs-unit catch-up). Use ANY time the user asks to rank, shortlist or find "top/best suburbs" (any count), "where to buy/invest", a "hotspot list", "underrated suburbs", "growth corridors", "best yield/growth/family suburbs", a "house vs unit comparison", "where units haven't caught up", "house-unit ratio", "catch-up suburbs", "where the gap widened", or any open-ended suburb-discovery question. Distinct from cma (one address) and feaso (one site's dev potential). Operates across MANY suburbs and produces ranked shortlists with reasoning and risk flags. Default-excludes mining towns unless user opts in. Client-facing report exports as PDF, Word or Canva with your branding.
---

# Find Suburbs

## Purpose

Identify and rank Australian suburbs against the user's stated strategy. Behave like a senior property analyst — interpret metrics in context, weigh opportunity against risk, and explain reasoning. Do not produce a raw spreadsheet dump.

Outputs: Top 10, Top 50 or Top 100 suburb reports with rankings, key strengths, risks, confidence indicators and a strategic summary.

---

## Operating environment

This skill runs against the connected Stash property-data MCP. Refer to its tools by their presented names (e.g. `get_hotspots`, `get_suburb_context`) — bind to whatever the runtime exposes; never hardcode a connector UUID, as it varies per install. Two tools matter most:

- `get_hotspots` — filter and sort suburbs by aggregate metrics. Primary engine.
- `get_suburb_context` — deeper context on shortlisted suburbs (top of the list only).

Data conventions:

- Rates/ratios (`Yield`, `VacancyRate`, `MedianGrowth`, `SocialHousingRatio`) are **decimals** — 6% is `0.06`. Always pass decimals in filters.
- `miningTown` flag is unreliable. Well-known mining LGAs (Karratha, Port Hedland, Kalgoorlie-Boulder, Mount Isa, Moranbah, Roxby Downs, Tom Price, Newman, Paraburdoo, Coober Pedy, Leinster, Dysart, Blackwater, Emerald) often slip through as false. Apply secondary LGA/locality filter when excluding mining.
- Large unfiltered queries exceed the response budget. Apply tight filters before sorting. If a response is large and you need to re-query repeatedly, write the payload to a temp file first (e.g. `/tmp/hotspots.json`), then derive/filter with `jq` against that file instead of re-calling the tool.

### Growth signals

Use sustained-growth fields, not short-horizon composites:

- `medianGrowth` — 12-month. Confirmation only, never primary rank.
- `salePriceMedianCAGR5Year` — annualised last 5Y. Heavily COVID-affected.
- `salePriceMedianCAGR10Year` — annualised last 10Y. Blends pre- and post-COVID.
- `salePriceMedianGrowth10Year`, `salePriceMedianGrowth5Year` — total growth, needed to derive pre-COVID CAGR.

### Derive pre-COVID 5Y CAGR (years -10 to -5)

Growth rate over the **first** 5 years of the 10-year window — before the 2020-22 COVID boom. Strong both windows = real long-term compounder. Weak pre-COVID, strong post-COVID = WFH/rate beneficiary; may not persist.

```
preCovid5YGrowth = (1 + salePriceMedianGrowth10Year) / (1 + salePriceMedianGrowth5Year) - 1
preCovid5YCagr   = (1 + preCovid5YGrowth) ^ (1/5) - 1
```

jq: `. + { preCovid5YCagr: (pow((1 + .salePriceMedianGrowth10Year) / (1 + .salePriceMedianGrowth5Year); 1/5) - 1) }`

### Reading 10Y CAGR and pre-COVID 5Y CAGR together

**Both required. Don't lean on either alone.**

- `salePriceMedianCAGR10Year` = full-decade compounding (what holders generated).
- `preCovid5YCagr` (derived) = organic baseline (pre-WFH/COVID).

| 10Y ↓ \ pre-COVID 5Y → | High (≥5%) | Moderate (3-5%) | Weak (1-3%) | Negative |
|---|---|---|---|---|
| **High (≥8%)** | Consistent compounder — highest conviction | Reliable compounder — high conviction | COVID-amplified — medium | Cyclical recovery — low |
| **Moderate (5-8%)** | Mature — solid, lower runway | Workhorse — solid | Recent-driver — verify catalyst | Weak — skip unless cheap |
| **Low (<5%)** | Decade-stall recovery — investigate | Marginal — skip unless yield | Skip | Avoid |

When 10Y and pre-COVID move together → real track record. When they diverge (high 10Y, weak pre-COVID) → COVID-carried; 10Y is a poor predictor of next decade.

Caveat: today's 5Y window starts mid-2021, so "prior 5Y" includes ~12 months of early COVID boom. `preCovid5YCagr` is a *conservative* estimate of true pre-pandemic growth.

---

## Workflow

### Step 1 — Capture strategy and constraints

| Input | Default |
|---|---|
| Report size | Top 10 |
| Geography | National |
| Strategy | Balanced (unless prompt cues yield/growth/family/dev) |
| Budget | None |
| Property type | House |
| Metro vs regional | No preference |
| Exclude mining towns | YES |
| Min sale volume | 20+ |
| Min suburb population | 1,500 |

Use prompt cues to set strategy directly. For one-liners like "top suburbs for yield", just run it.

### Step 2 — Build the query

#### Yield / Cashflow
- Sort: `Yield` desc
- Filters: `Yield > 0.055`, `VacancyRate < 0.03`, `SaleCount > 20`, `SuburbPopulation > 1500`
- Post-filter: exclude mining LGAs

#### Investment Growth
Sustained compounders, not momentum suburbs at end of run.
- Sort: `MedianGrowth` desc (trawl only — real ranking in code)
- Filters: `MedianGrowth > 0.05`, `VacancyRate < 0.025`, `SaleCount > 30`, `OwnershipRatio > 0.55`, `SocialHousingRatio < 0.08`
- **Re-rank locally** with four-horizon composite (10Y and pre-COVID equal-class primary):
  - 30% × `preCovid5YCagr` (derived; organic long-term)
  - 30% × `salePriceMedianCAGR10Year` (total decade)
  - 25% × `salePriceMedianCAGR5Year` (recent, COVID-inclusive)
  - 15% × `medianGrowth` (12m, confirmation)
- **Demote any suburb where `medianGrowth` > 2× `salePriceMedianCAGR5Year`** — momentum trap. Flag as "late-cycle, entry-timing risk".
- **Always show BOTH `preCovid5YCagr` AND `salePriceMedianCAGR10Year` columns** in output.
- Apply the matrix to each suburb; state joint read explicitly ("high 10Y + high pre-COVID → consistent compounder"). This is the analytical core.
- Highest conviction: pre-COVID 5Y ≥ 3% AND 10Y ≥ 7% AND recent 5Y within ~3pp of pre-COVID. Mark explicitly.

#### Development
- Sort: `BuildingApprovalsRatio` desc OR `MarketAbsorptionRate` desc
- Filters: `SaleCount > 30`, `MedianGrowth > 0.03`, `Yield > 0.04`
- WATCH: high `BuildingApprovalsRatio` (>0.04) is supply-risk, not positive.

#### Renovation / Value-add
- Sort: `MedianGrowth` desc
- Filters: `SaleCount > 30`, `OwnershipRatio > 0.6`
- Prefer `salepriceIqrRatio` 0.30-0.60. Reject <0.20 (cookie-cutter) and >0.70 (bifurcated).

#### Family / Owner-occupier
- Sort: `SchoolScore` desc (fallback: local re-rank by `salePriceMedianCAGR5Year`)
- Filters: `OwnershipRatio > 0.65`, `SocialHousingRatio < 0.05`, `RenterRatio < 0.30`, `VacancyRate < 0.025`

#### Balanced
- Sort: `MedianGrowth` desc (trawl)
- Filters: `Yield > 0.04`, `MedianGrowth > 0.04`, `VacancyRate < 0.025`, `SaleCount > 30`
- Re-rank locally on composite of normalised `yieldMedian`, `salePriceMedianCAGR5Year`, inverse `vacancyRate`.

#### House vs Unit Comparison (catch-up arbitrage)

Trigger: "where have units not caught up", "biggest gap between houses and units", "house-vs-unit", "catch-up suburbs".

**Key insight:** in most capital cities the unit catch-up trade has been substantially playing out since 2022. The real question is no longer "where is the ratio low?" — it's **"where is the ratio still falling?"**

Workflow:

1. **Pull two matched datasets** — same geography, `House` and `Unit`. Sort by `SuburbPopulation` desc. Filters: `SaleCount > 30` units, `> 50` houses, `SocialHousingRatio < 0.10`. Limit 50 each.
2. **Match by `suburbSlug`** (strip `-house`/`-unit` suffix). Only suburbs in both sets are usable.
3. **Derive per suburb:**
   ```
   ratio_now      = unit_now / house_now
   house_5yago    = house_now / (1 + house_5Y_total_growth)
   unit_5yago     = unit_now  / (1 + unit_5Y_total_growth)
   ratio_5yago    = unit_5yago / house_5yago
   ratio_change   = ratio_now - ratio_5yago   // negative = gap widening
   growth_gap_pp  = house_5Y_growth - unit_5Y_growth
   ```
   Plus `unit_preCovid5YCagr` as trap-detector.

4. **Classify:**

| `ratio_change` over 5Y | `unit_preCovid5YCagr` | Read |
|---|---|---|
| < -3pp | > 1% | Catch-up still running. High conviction. |
| < -3pp | -2% to 1% | Gap widening but weak unit base. Medium. |
| < -3pp | < -2% | Unit market structurally broken. **Avoid.** |
| -3 to +3pp | any | Stable gap. Use other lenses. |
| > +3pp | any | **Catch-up played out.** Watch for reversion. |

5. **Secondary filters:** pop growth > 5%, unit vacancy < 2.5%, check affordability.

6. **Always report TWO tables**: gap-widened (still alive) AND gap-closed (catch-up done). The latter is the evidence the dynamic is real.

7. **Traps:**
   - **Hamilton trap** — very low ratio (<35%) + negative pre-COVID unit CAGR = structurally broken, not undervalued.
   - **Ratio-still-low trap** — low ratio with positive 5Y `ratio_change` means catch-up has been running. Late, not early.
   - **Premium-trophy trap** — inner-east land-value-dominated units (New Farm-type) won't catch up; buyer pools differ. "Compression by design".

### Step 3 — Pull, prune, contextualise

Over-fetch (2-3× rank size). Then:
1. Apply mining-town secondary filter if appropriate.
2. Drop `saleCount < 20`.
3. Dedupe by locality (keep larger by population).
4. Re-sort survivors by primary metric.
5. Trim to requested size.

For top 5 of final list, call `get_suburb_context` for richer writeup. Ranks 6-N: use hotspot payload only.

### Step 4 — Interpret, don't just rank

For each suburb derive:

- **Key strengths** — specific drivers ("yields 6.8% on $300k median, vacancy 0.4%"), not generic.
- **Risks / watchouts**:
  - High 5Y pop growth + weak 10Y → COVID-distortion
  - High `BuildingApprovalsRatio` (>0.04) → supply risk
  - IQR <0.20 → uniform stock, low reno upside
  - IQR >0.70 → bifurcated sub-markets; median misleading
  - Low `SchoolScore` + high `SocialHousingRatio` → OO ceiling
  - Yield > 8% with falling pop → cashflow trap
  - 1Y >> 5Y CAGR → momentum ending, not starting
- **Confidence** — High/Medium/Low based on `SaleCount`, recency, sustainability.

### Step 5 — Output format

Render the main ranking as a markdown table.

**Suburb hyperlinking — MANDATORY.** Every suburb name in every output (tables, summary bullets, inline references, traps) must hyperlink to Stash Property using the `localityPid` field from the payload:

```
https://stashproperty.com.au/app/suburb-profile/{localityPid}
```

So `Wynnum` becomes `[Wynnum](https://stashproperty.com.au/app/suburb-profile/QLD3197)` — using the actual `localityPid` returned. NEVER fabricate or guess. If absent, render plain text with a footnote.

Template:

```
# Top {N} Suburbs — {Strategy}
{1-sentence framing}

| Rank | Suburb | State | Score | Median | Yield | 12m | Best For | Key Strengths | Risks | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|

## Summary
(Each suburb below is hyperlinked per the localityPid rule above.)
- **Best overall:** {suburb} — {why}
- **Best value:** {suburb} — {why}
- **Best growth:** {suburb} — {why}
- **Best yield:** {suburb} — {why}
- **Best family:** {suburb} — {why}
- **Best development:** {suburb} — {why}
- **Highest risk:** {suburb} — {watch}
- **Most underrated:** {suburb} — {why overlooked}

## Key watchouts across this list
{2-4 cross-cutting risks}
```

For Top 50/100: group by state or tier, keep per-row text tight, offer .xlsx via `xlsx` skill. For Top 10: deliver inline.

**Client-facing report (any format):** if the user wants this as a report to
send or keep rather than an inline answer, load the `report-export` skill and
ask its one card: export format (PDF / Word / Canva) and branding (Stash
default / saved brand / paste a brand URL / unbranded). Build in that format
with the brand tokens; links, figures and labels stay exactly as above.

---

## Behaviour rules

- **Always hyperlink suburb names** to `https://stashproperty.com.au/app/suburb-profile/{localityPid}` using `localityPid` from the payload. Applies to ALL output types. Never fabricate.
- Interpret metrics in context — never present a number without a "so what".
- When a metric looks great but contradicts the longer-term trend, call it out.
- Don't recommend mining-economy towns under yield strategy unless user accepts volatility.
- Don't pad lists. If only 7 clear the bar for Top 10, deliver 7 and explain.
- Confidence ratings exist for a reason.
- If asked "why isn't X here?", explain (failed which filter, ranked where).
- **Offer to find live listings.** When the person already has a suburb in mind — they name one, ask to drill into a ranked suburb, or say "what about X" — offer to pull current on-market listings there via `find-on-market-deals` (e.g. "Want me to look up what's for sale in {suburb} right now?"). Don't just rank suburbs and stop; the natural next step from a suburb is the deals inside it.

---

## Hand-offs

- Live on-market listings in a suburb of interest → `find-on-market-deals`
- Valuation of specific address → `cma`
- "Can I subdivide / develop X" → `feaso`
- Planning rules → `planning`
- Sortable spreadsheet → `xlsx`
- Client-facing report → `report-export` (PDF, Word or Canva, with brand)
