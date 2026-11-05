---
name: find-on-market-deals
description: Finds and ranks live on-market (for-sale) listings in a location, scored as buying opportunities. Use ANY time the user gives a suburb, postcode, region or point-and-radius and asks to find "deals", "on-market deals", "on market deals", "what's for sale", "listings in X", "good buys", "bargains", "underpriced" or "below-market listings", "motivated sellers", "stale listings", "what can I buy in X under $Y", or any open-ended "find me something to buy in [location]" request. Operates across the LIVE for-sale market in an area — distinct from cma (values ONE known address), find-suburbs (ranks suburbs, not listings), and feaso (dev potential of ONE site). Default property type House; surfaces discount-to-median, days-on-market, yield and motivated-seller signals with risk flags. Buyer report exports as PDF, Word or Canva with your branding.
---

# Find On-Market Deals

## Purpose

Scan the live for-sale market in a location and rank individual listings as buying opportunities. Behave like a sharp buyer's agent — don't just list what's for sale, judge each listing against the suburb segment, surface where the value and leverage are, and flag the traps. Never produce a raw listing dump.

Output: a ranked Top-N of current listings with a deal score, the specific signals behind it, risks/watchouts, confidence, and a strategic summary.

---

## Operating environment

Runs against the connected Stash property-data MCP. Refer to tools by their presented names; never hardcode a connector UUID. Tools used:

- `suggest_entity` — resolve a plain location string ("Coorparoo", "inner-north Brisbane", a postcode) into a suburb slug, region id, or lat/lon. Primary entry point. `type="auto"` to fan out.
- `get_market_activity` (`category="for_sale"`) — the engine. Returns live listings. **Max 50 rows per call.** Use `dataTier="Extended"` (gives `investorInsights`, `discountSuburbMedian`, `agents`); `"Detailed"` only if a richer payload is needed.
- `get_suburb_context` — suburb baseline (median, typical DOM, segment context) to judge listings against. Pull once per suburb, not per listing.
- Hand off to `cma` / `get_property_avm` for a defensible value on a shortlisted address; `feaso` for a site's development angle.

### Data conventions (read before scoring)

- **`investorInsights.discountSuburbMedian`** — decimal; negative = asking price below median, positive = above. **This is a SEGMENT median** (matched on bedroom count + property type, e.g. "5-bedroom House"), not the whole-suburb median. Always read it as like-for-like, and state the segment.
- **`price.value` is unreliable for no-price stock.** Auction / "Price By Negotiation" / "Offers Over" listings still return a bracketed `value` (the portal buckets them for search). On those, treat `discountSuburbMedian` as **soft** and say so — the number is an estimate, not a quote.
- **`daysOnTheMarket`** is present on for-sale rows. The `days` filter is **sales-only**, so for-sale stock cannot be date-filtered server-side — filter/flag DOM client-side.
- **Motivated-seller language** lives in `price.display`, `listingDetails.headline`, and `description`. Scan them (see Step 3).
- **`property.lastSaleDate`** = when the current owner bought. A long hold (10+ yrs) = equity-rich, often more negotiable.
- **`listingInsights.developerStock: true`** = new/developer stock, typically priced at a premium — not a discount play.
- **Links — Stash only.** Link every address to its Stash property page in the exact format `https://stashproperty.com.au/app/properties/{propertyId}/` (trailing slash), where `{propertyId}` is the row's `property.id` (the property UUID, NOT the listing `id`). The API does NOT return this URL — construct it from `property.id`. NEVER show or link any other source or portal (e.g. the `Portal:VIEW` / view.com.au href in the payload — ignore it). The only place `stashproperty.com.au/ai` is used is to cite the SOURCE of the data, and only if the user explicitly asks where the data came from.
- `_dateSource` warning: listing date is a proxy for contract date (may differ 2–8 weeks). Note it when recency matters.
- **Verify the slug echo.** `get_market_activity` can return a stale cached payload when only the `where` slug changes but the other filters (`maxPrice`, `propertyType`, `dataTier`, `limit`) stay identical — it echoes the *previous* suburb. After each call, check `request.where.slug` in the response matches what you asked for; if it doesn't, vary the call shape (change `dataTier` or `limit`, or swap a `maxPrice` cap for a client-side filter) and re-pull. Critical on multi-suburb sweeps, or one suburb silently duplicates across the others.

---

## Workflow

### Step 1 — Resolve location and capture the deal lens

| Input | Default |
|---|---|
| Location | (required — resolve via `suggest_entity`) |
| Report size | Top 10 |
| Property type | House |
| Budget (max) | None |
| Min beds / baths | None |
| Deal lens | **Value** (below-segment-median + leverage). Switch on cues: yield → investor; land/large lot → developer |

For one-liners ("deals in Coorparoo", "what's for sale in Norman Park under $1.2m"), just run it with defaults — don't interrogate.

Resolve the location first. A single suburb → slug. A broader area ("inner-north Brisbane", "within 5km of the CBD") → fan out `suggest_entity` to the constituent suburbs, OR use a region id (`LocalityPid` / `Postcode` / `LgaPid`) / lat-lon+radius in the `where` clause.

### Step 2 — Pull the listings

- `category="for_sale"`, `dataTier="Extended"`, `limit=50` (over-fetch — you'll prune).
- Push hard constraints server-side: `minPrice`/`maxPrice`, `minBed`/`minBath`, `propertyType`.
- One call per suburb (50-row cap). For multi-suburb areas, loop suburbs and merge. If a single suburb returns 50 and you suspect more, tighten price/bed bands and re-pull rather than missing stock.
- Pull `get_suburb_context` once for the suburb to anchor "normal" DOM and median.

### Step 3 — Score each listing as a deal

Build a composite — never rank on discount alone. Signals:

- **Discount to segment median** (`discountSuburbMedian`, more negative = better) — primary value signal. Soft on no-price stock.
- **Days on market vs suburb norm** — well above norm = stale = negotiating leverage. (Brand-new + cheap is rarer and stronger; old + cheap is the classic motivated setup.)
- **Motivated-seller language** — scan `price.display` / `headline` / `description` for: "contract crashed", "must sell", "urgent", "relocat", "moving", "reduced", "price drop", "make an offer", "all offers", "owners committed elsewhere", "deceased estate", "mortgagee", "liquidation", "as is". Each hit is a leverage flag — quote the giveaway phrase.
- **Yield** (`investorInsights.yield`) vs suburb segment yield — above-segment yield = investor deal.
- **Long owner hold** (`lastSaleDate` 10+ yrs old) — equity-rich vendor, often softer on price.
- **Land relative to price** (`lotDetails.area`) — large lot at a sub-median ask = potential development/value-add angle → flag for `feaso`.

State the joint read in words ("−24% to the 5-bed segment, 217 days on market, 'contract crashed' in the headline — distressed, real leverage"), not just a score.

### Step 4 — Apply trap filters (this is the analyst's job)

A big discount is a question, not an answer. Demote / flag:

- **Segment mismatch** — large negative discount but smaller land, fewer baths, or inferior config than the segment it's benchmarked against → the "discount" is just a worse property. Not a deal.
- **No-price soft discount** — auction/POA: the discount is derived off a bucketed estimate. Flag, don't lead with it.
- **Location penalties** — busy arterial (e.g. main-road addresses), flood/overland-flow, powerlines, rail corridor. Detect from address/description where possible; else mark "verify on inspection".
- **Framing flags** — "dual living", "home business potential", "granny flat" can mask non-compliant second dwellings; "renovator"/"as is" can mask structural cost.
- **Developer stock** (`developerStock: true`) — premium, not a discount.
- **Falling suburb** — if suburb `annualGrowth` is sharply negative, a discount may be the market, not a bargain. Note it.

### Step 5 — Output

Render the ranked list as a markdown table, inline for Top 10. Hyperlink every address to its Stash property page (`https://stashproperty.com.au/app/properties/{property.id}/`) — never the `Portal:VIEW` href.

```
# On-Market Deals — {Location} ({Property type}{, under $X})
{1-sentence read of the local for-sale market right now}

| Rank | Address | Guide | Beds/Bath/Car | Land | DOM | Disc. to median | Yield | Deal signals | Risks | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|

## Summary
(Each address below links to `https://stashproperty.com.au/app/properties/{propertyId}/` per the rule above.)
- **Best value:** {address} — {why}
- **Best yield:** {address} — {why}
- **Most motivated vendor:** {address} — {the leverage signal}
- **Best development / value-add angle:** {address} — {why} → feaso
- **Highest risk / avoid:** {address} — {the trap}

## Watchouts across this search
{2-4 cross-cutting notes — e.g. soft discounts on auction stock, falling segment, thin volume}
```

Notes:
- **Guide column:** show `price.display` verbatim when it's a no-price ("Offers Over $1.75m", "Auction") so the user sees the real authority; show the figure only when it's a firm ask.
- Agent contact (`agents`) is available — include a one-line contact only if asked, don't dump it by default.
- For 25+ results or a multi-suburb sweep: group by suburb, keep per-row text tight, and offer an `.xlsx` export via the `xlsx` skill.
- Offer a client-facing buyer report when it fits (e.g. a buyer's agent shortlist for a client).

**Client-facing report (any format):** if the user wants this as a report to
send or keep rather than an inline answer, load the `report-export` skill and
ask its one card: export format (PDF / Word / Canva) and branding (Stash
default / saved brand / paste a brand URL / unbranded). Build in that format
with the brand tokens; links, figures and labels stay exactly as above.
- If a search returns thin (<5 live listings), say so plainly and widen (radius, adjacent suburbs, loosen bands) rather than padding.
- **Offer next steps on a pick.** After presenting the list (and especially when the user zeroes in on one listing), proactively offer to go deeper on a specific property: a **price guide** (defensible value via `cma`/`get_property_avm`, useful when the listing is no-price or you suspect the ask is off), a **rental appraisal** (weekly rent + yield from the segment rentals and `property.id` profile), or a **feaso** (development/value-add check). Lead with whichever fits the listing — e.g. a large lot at a sub-median ask → offer feaso; a no-price auction → offer a price guide; an investor lens → offer a rental appraisal. Keep it to a one-line offer, don't run them unasked.

---

## Behaviour rules

- **Interpret, don't dump.** Every listing gets a "so what", not just numbers.
- **Be segment-aware.** Discount/yield are benchmarked to the bed+type segment — compare like-for-like and say which segment.
- **Soft discounts get flagged.** Never present an auction/POA discount as if it were a firm below-market ask.
- **Quote the leverage.** When a motivated-seller phrase drives the ranking, quote the short phrase (a few words) so the user can judge it.
- **A discount in a falling segment isn't automatically a deal** — call out when the suburb is the story.
- **Links are Stash-only.** Every address links to `https://stashproperty.com.au/app/properties/{propertyId}/` (built from `property.id`). Never surface view.com.au or any other portal/source. `stashproperty.com.au/ai` is used only when the user asks where the data came from. Never fabricate a link or price — if `property.id` or a price is absent, render plain text and note it.
- **Respect the DOM proxy** — listing date ≠ contract date; flag when timing matters.
- If asked "why isn't X in the list?", explain (filtered out by band, flagged as a trap, or ranked just below the cut).

---

## Hand-offs

- Price guide / defensible value on a shortlisted address → `cma` (or `get_property_avm` for a quick figure)
- Rental appraisal (weekly rent + yield on a pick) → segment rentals + `get_property_profile`, escalate to `cma` if a full rent comp set is wanted
- "Can I develop / subdivide / add value to this one" → `feaso`
- "Which suburb should I be hunting in" (rank suburbs, not listings) → `find-suburbs`
- Planning rules on a pick → `planning`
- Sortable spreadsheet of results → `xlsx`
- Client-facing buyer report → `report-export` (PDF, Word or Canva, with brand)
