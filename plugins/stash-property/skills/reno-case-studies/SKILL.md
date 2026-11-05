---
name: reno-case-studies
description: Finds real-world repeat-sale case studies in a location — properties that were bought and then sold AGAIN within the last 5 years — and labels each as a Flip, Reno, KDRB, or New Build, with a before/after profit table. Use ANY time the user asks for "reno case studies", "renovation case studies", "before and after sales", "flips", "who's been flipping in X", "flip margins/profits", "renovation gains", "value-add examples", "repeat sales", "resales", "bought and resold", "double sales", "knockdown rebuild examples", "KDRB examples", "land to house builds", "what reno uplift can I get in X", or "show me what renovators made in [suburb / near this address]". Operates across the SOLD market and pairs the same property's two sales — distinct from cma (values ONE address), find-on-market-deals (LIVE listings, not resales), find-suburbs (ranks suburbs), and feaso (dev potential of ONE site). Works for a whole suburb OR a radius (default 5km) around a single address. Exports to PDF, Word or Canva.
---

# Reno Case Studies

## Purpose

Surface real evidence of value-add in an area: properties that **sold, then sold again** within the window, so the purchase and the later sale can be paired into a before/after. For each pair, show purchase price → sold price, hold period, dollar and percentage uplift, and a **label** explaining the uplift — was it the market doing the work (Flip), a renovation beating the market (Reno), a knock-down-rebuild (KDRB), or a land-to-dwelling new build?

Behave like an analyst building a comp file of renovator/developer outcomes — not a raw resale dump. The label and the "so what" are the product. Sort by **% increase, descending**.

Output: a before/after table of paired sales with labels, ranked by % uplift, plus a short read of what the renovator/flipper money has been doing in this market.

---

## Operating environment

Runs against the connected Stash property-data MCP. Refer to tools by their presented names; never hardcode a connector UUID. Tools used:

- `suggest_entity` — resolve a location string ("Coorparoo", a postcode) into a suburb slug, OR resolve a single address into a property so you can read its lat/lon for radius mode. Primary entry point.
- `get_property_profile` — when the input is ONE address (radius mode), pull it to get the centre lat/lon.
- `get_market_activity` (`category="sold"`) — the engine. **This is the only source of the paired sales.**
- `get_suburb_context` — pull once to anchor the segment median and the suburb's annualised growth, which is the benchmark that separates a Flip from a Reno.

### How the sold data actually works (read before building)

Each row returned by `get_market_activity` is **one sale event**, not a property. The fields that matter:

- `property.id` — the **persistent property UUID**. The same property selling twice in the window appears as **two rows with the same `property.id`**. This is the primary key for pairing. (It is also the link key — see below.)
- `saleDetails.date` and `saleDetails.price.value` — the event's contract date and price. **Days held and uplift come from comparing the two events' `saleDetails`, NOT from `daysOnTheMarket`** (that is the resale listing's marketing days, a different number).
- `location.address.streetLocation.pid` (e.g. `GAQLD156494296`) — the **physical address point**. Use as a SECONDARY key: a knock-down-rebuild or a strata/title change can issue a NEW `property.id` for the same dirt, so pairs that share an address pid but differ on `property.id` are exactly the KDRB / re-titled candidates.
- `property.builtYear` — a built year that postdates the purchase = new construction between the two sales (KDRB or new build signal).
- `propertyType` — a `Land` → dwelling change between events = a new build.
- `attributes.bedrooms/bathrooms/parkingSpaces`, `lotDetails.area` — config; a bed/bath jump between events supports KDRB/major-reno.
- `listingInsights.developerStock`, `listingDetails.headline`, `listingDetails.description` — context for the label (developer stock, "renovated", "fully renovated", "as new", "brand new", "DA approved", "rebuilt").

There is **no embedded sale history and no offset/cursor**. You cannot ask the API "give me the prior sale" or page past row 50. Both events of a pair must be caught in the sweep, which is why coverage comes from **partitioned over-fetching** (Step 2), not a single call.

### Data conventions

- **Window:** 5 years = `days=1825` (max the API allows is `3650` = 10y). The `days` filter applies to sales.
- **Row cap:** `limit` max **50 per call**, no pagination. A call that returns exactly 50 is almost certainly truncated — subdivide that slice and re-pull.
- **Tier:** sweep on `dataTier="Basic"` — it already carries `property.id`, `builtYear`, `saleDetails`, address pid, type, attributes, `lotDetails`, `developerStock`, headline/description. Reserve `Extended`/`Detailed` for the shortlisted pairs only (adds planning, nearby, agents).
- **Radius:** `where: {lat, lon, radius}` — radius is metres, **max 5000 (5km)**. Default to 5000 when the user says "around" an address without a number.
- **Links — Stash only.** Link every address to `https://stashproperty.com.au/app/properties/{property.id}/` (trailing slash), built from the row's `property.id`. NEVER surface `Portal:VIEW` / view.com.au or any other portal. `stashproperty.com.au/ai` is only for citing the data source if explicitly asked.
- **Cache / slug-echo check.** `get_market_activity` can return a stale cached payload when only the location changes but the other filters stay identical (the cache key omits `where`). After each call, confirm `request.where` echoes what you asked for, and watch for a band returning the **same first `id`** as the previous band — if so, vary the call shape (change `dataTier` or `limit`, or move a `maxPrice` cap to a client-side filter) and re-pull. Critical on multi-band sweeps and radius runs.
- `_dateSource: contract` means the date is the contract date (good); `listed`/`unknown` are proxies — note when a pair's hold period leans on a proxy date.

---

## Workflow

### Step 1 — Resolve the location and the mode

| Input | Default |
|---|---|
| Target | (required) |
| Mode | **Suburb** if a suburb/postcode is given; **Radius** if a single street address is given |
| Radius (radius mode) | 5000 m (5 km) |
| Window | 5 years (`days=1825`) |
| Property type | All (House + Unit + Townhouse + Land) unless the user names one |
| Report size | Top 15 pairs (or all that clear the bar, if fewer) |

- **Suburb mode:** `suggest_entity` → suburb slug (e.g. `coorparoo-qld-4151`).
- **Radius mode:** resolve the centre address via `suggest_entity` / `get_property_profile`, read its lat/lon, then use `where: {lat, lon, radius:5000}`.

Run one-liners ("reno case studies in Coorparoo", "flips within 5km of 14 Frank St Norman Park") on defaults — don't interrogate.

### Step 2 — Sweep the sold market for full coverage (partitioned over-fetch)

The goal is to capture **as many sale events as possible** so both halves of each pair are present. Because of the 50-row cap and no pagination, partition the search space and union the results.

1. Pull `get_suburb_context` once to get the rough segment median (anchors the price bands AND the growth benchmark in Step 4).
2. Build ~6–10 **price bands** spanning roughly 0.3× to 3× the median, plus an open-ended top band. Example around a $900k median: `<500k, 500–700k, 700–900k, 900–1.1m, 1.1–1.3m, 1.3–1.6m, 1.6–2m, 2m+`.
3. For each band, call `get_market_activity` with `category="sold"`, `days=1825`, `dataTier="Basic"`, `limit=50`, the band's `minPrice`/`maxPrice`, and the `where` clause (slug or lat/lon+radius). Sweep **every band** — a property's purchase and its resale fall in *different* bands, but sweeping all bands captures both.
4. If a band returns exactly 50 rows it's truncated → split it (narrower price sub-band, or add a `propertyType` / `exactBed` partition) and re-pull the slice.
5. **Dump every payload to `/tmp`** as you go (e.g. `/tmp/reno_<band>.json`), then merge and **dedupe by row `id`** with `jq`/python. Re-call the tool as little as possible after that — derive from the files.

Note the call budget honestly: this is a heavier skill than a single CMA. A thorough suburb sweep is ~8–16 calls; radius is similar. If the user wants it fast, narrow first (one property type, or a tighter price band) and say coverage is partial.

### Step 3 — Pair the repeat sales

From the merged, deduped event set:

1. **Primary pairing — same `property.id`.** Group events by `property.id`; keep groups with **≥2 events**. Sort each group by `saleDetails.date`. The earliest = **purchase (before)**, the latest = **sale (after)**. For chains of 3+, default to first→last but note interim sales; if an interim short-hold/big-uplift episode looks like a discrete reno, surface that pair too.
2. **Secondary pairing — same address, different `property.id`.** Index remaining single-event properties by `streetLocation.pid` (fall back to normalised `streetAddress`). Where two events share an address pid but have different `property.id`, pair them — these are the **KDRB / re-titled** cases the primary key misses. Flag them as cross-id pairs (lower-confidence join; verify on the address).
3. **Drop non-arms-length / junk pairs:** nominal or implausible prices (<~$10k, or buy/sell within ~1–2% — likely a transfer, related-party, or duplicate record), and same-day double records. Flag, don't rank them.

For each surviving pair compute:
- `gainAbs = sell − buy`
- `gainPct = sell/buy − 1`
- `daysHeld = sell.date − buy.date`; `yearsHeld = daysHeld/365.25`

### Step 4 — Label each pair

Benchmark first: get the segment's **annualised growth** (`get_suburb_context` CAGR for the matching type, e.g. unit vs house). Fallback if unavailable (or in radius mode): the **internal repeat-sales median** — the median annualised gain across all *same-id, same-builtYear, same-type* pairs in your set approximates pure market movement. Then per pair:

```
mktExpectedPct = (1 + segmentCAGR) ^ yearsHeld - 1     # what the market alone would have delivered over the hold
excessPct      = gainPct - mktExpectedPct               # the uplift ABOVE the market = the value-add "alpha"
bedDelta / bathDelta = sell - buy attributes
builtYearJump  = sell.builtYear present AND > buy.date.year
typeChange     = buy.propertyType vs sell.propertyType
```

Apply in order — first match wins:

1. **New Build (land→dwelling)** — buy `propertyType == "Land"` (or no dwelling) and sell is a dwelling; or `builtYearJump` with a land/vacant purchase. *Land bought, house built, sold.*
2. **KDRB (knock-down-rebuild)** — cross-id pair on the same address; OR `builtYearJump` (built year postdates purchase) on a dwelling; OR dwelling-type unchanged but `bedDelta ≥ +1`/`bathDelta ≥ +1` with very large `excessPct`. These carry the **biggest uplifts** and may not share `property.id`.
3. **Reno (above and beyond)** — same `property.id`, no built-year jump, and `excessPct` materially positive — roughly **≥ +15pp**, or `gainPct ≥ ~1.5 × mktExpectedPct` — typically on a hold under ~4 years. The increase beats what time-in-market explains; headline keywords ("renovated", "as new") corroborate. Note *how far* above market.
4. **Flip / market timing** — same `property.id`, `excessPct` within roughly ±15pp of market: the uplift is explained by **time in market**, not work. Short hold + thin margin → "Flip"; long hold tracking the market → sub-label "Hold (market)".
5. **Inconclusive** — thin/missing prices, proxy dates on a short hold, or signals that conflict. Keep with a low-confidence flag; don't let it lead.

Thresholds are heuristics, not gospel — reason on edge cases. A 14-month hold with +40% on a unit in a flat segment is a Reno even if the description is silent; a +90% over 5 years in a segment that itself ran +80% is market, not magic. State the joint read in words.

### Step 5 — Output

Render the before/after table inline, **sorted by % increase descending**. Each address links to its Stash page.

```
# Reno Case Studies — {Suburb | within {R}km of {address}} ({window}, {types})
{1-sentence read of what the renovator/flipper money has been doing here}

| # | Address | Type | Before (buy) | After (sold) | Held | $ Uplift | % Uplift | Label | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [addr](stash url) | House 3→4bd | $810k (Mar 22) | $1.46m (Aug 24) | 2.4 yrs | +$650k | +80% | KDRB | High |
| 2 | ... | Unit | $... | $... | ... | ... | ... | Reno | Med |

## Read
- **Biggest value-add:** {address} — {what the numbers say} ({label})
- **Cleanest reno play:** {address} — {uplift vs market over the hold}
- **Pure market / flip:** {address} — {gain ≈ market, no work evident}
- **KDRB / new build evidence:** {address(es)} — {built-year jump or land→house}

## Coverage & caveats
{How many sale events swept, how many pairs found, segment CAGR benchmark used, and where coverage is partial (50-cap truncation, proxy dates, cross-id joins to verify).}
```

Notes:
- Show buy/sell as price + month-year so the hold reads at a glance.
- Quote the corroborating headline phrase (a few words) when it drives a Reno/KDRB label.
- For 25+ pairs or a multi-type sweep: offer an `.xlsx` export (`xlsx` skill) with full columns and the raw event list.
- When the user wants something client-facing, offer a case-study pack and follow `report-export` (PDF / Word / Canva + brand URL). Suggested pages: cover, the before/after table, one card per top 3–5 pair (buy → sell, hold, uplift vs market, label), the Read, and Coverage & caveats. In Canva, draw a before/after bar pair per case natively.

**Client-facing report (any format):** if the user wants this as a report to
send or keep rather than an inline answer, load the `report-export` skill and
ask its one card: export format (PDF / Word / Canva) and branding (Stash
default / saved brand / paste a brand URL / unbranded). Build in that format
with the brand tokens; links, figures and labels stay exactly as above.
- If the sweep finds few pairs (<5), say so plainly and widen (bigger radius, longer window up to 10y, add property types) rather than padding.

---

## Behaviour rules

- **Pair on `property.id` first, address pid second.** The cross-id/same-address join is what catches KDRBs — don't skip it, but mark those pairs as needing address verification.
- **Days held and uplift come from the two `saleDetails`, never from `daysOnTheMarket`.**
- **The label is the deliverable.** Every pair gets a Flip / Reno / KDRB / New Build call with the reasoning, benchmarked against the segment's own growth over that specific hold — not a raw resale list.
- **Separate the market from the work.** A big gain in a segment that itself boomed is market timing, not a reno. Always state the benchmark and the excess.
- **Flag non-arms-length pairs** (nominal prices, near-identical buy/sell, duplicates) and keep them out of the ranking.
- **Be honest about coverage.** The 50-row cap with no pagination means the sweep is thorough but not guaranteed exhaustive — say how much was swept and where it's partial.
- **Links are Stash-only**, built from `property.id`: `https://stashproperty.com.au/app/properties/{property.id}/`. Never surface view.com.au or another portal. Never fabricate a link or price — if absent, render plain text and note it.
- **Run the slug-echo / cache check** after each call; vary the call shape if a band echoes the previous payload.
- If asked "why isn't X here?", explain (only sold once in the window, filtered as non-arms-length, truncated out of a 50-capped band, or ranked below the cut).

---

## Hand-offs

- Defensible value on one of the resold addresses → `cma` (or `get_property_avm` for a quick figure)
- "Could I do the same KDRB/subdivision on a site" → `feaso`
- Planning rules behind a KDRB/rebuild → `planning`
- "Which suburb has the best reno upside" (rank suburbs, not pairs) → `find-suburbs`
- Live listings to actually buy a reno project → `find-on-market-deals`
- Sortable spreadsheet of all pairs + raw events → `xlsx`
- Client-facing case-study pack → `report-export` (PDF, Word or Canva, with brand)
