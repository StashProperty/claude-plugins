---
name: pre-appraisal
description: "Agent-facing pre-appraisal briefing for a property before the listing appointment: comps, adjustments, competition, suburb market and planning, evidence only with no price decided. PDF, Word or Canva."
---

# Pre-Appraisal Briefing (agent-facing)

Gives the agent everything known about a property **before** they walk in for the appraisal, so nothing in the room surprises them. It covers:

- the property
- its sales history
- comparable sales with adjustments
- sales the owner may raise
- the competition
- the suburb market
- planning and flood
- what to confirm on site

Triggers: "pre-appraisal", "pre appraisal report", "appraisal prep", "brief me before the appraisal", "what should I know before I see this property", "agent briefing", "listing appointment prep".

This is **not** the seller document. When the agent wants something to hand the owner, use the `cma` skill in SELLING mode (the 6-page seller appraisal).

---

## Framing rules (non-negotiable)

The agent hasn't seen the property yet. The briefing must not read as if they've made up their mind.

- **Evidence only.** No recommended listing price, price guide, reserve, sale method or campaign.
- **No objection handling, scripts or "fluff".** Keep it to data and short neutral notes.
- **No loaded labels.** Not "anchor", "ceiling", "floor", "weak comp" or "the vendor will say…". Use neutral headings such as "Nearby sales that aren't like-for-like".
- **The value is indicative.** Show the weighted value and the indicative range (weighted × 0.97 to × 1.05) as "subject to inspection". Show the Stash AVM with its confidence and range.
- **Close with "To confirm at the appraisal".** List what could move the value: condition and finish, work done since the last sale, floor area and layout against the record, pool approval and safety certificate, the council flood report, and the owners' plans and timing.
- Never fabricate figures. Missing data shows as "not recorded".

---

## STEP 0: Ask (one card)

Load `report-export` and ask its card:

- **Format:** PDF / Word / Canva
- **Branding:** Stash / saved brand / paste a brand URL / unbranded

Skip anything already answered. Sample mode follows `report-export` → "Sample mode": a fictional address and AI-generated images, both labelled.

---

## STEP 1: Data (Stash first)

Reuse anything already in the conversation. Otherwise:

1. `suggest_entity` to resolve the address.
2. `get_property_profile` with salesHistory, listingHistory, valuations, zones and hazards.
3. `get_property_avm` for the value, range and confidence.
4. **Comps:** run the `cma` Stage 1 comp fetch and the STEP 4–5 scoring, adjustments and weighting. The adjustment rates and weights come from `cma`.
5. **Prior sales for each comp:** `get_property_profile(include={salesHistory:true})` gives each comp's previous sale and how its price changed. Check the build year and listing history, and note when a comp was rebuilt or extended in between.
6. `get_planning_and_risks(propertyId, include_nearby_das=true)` for zone, overlays, flood bands, bushfire, heritage and nearby DAs.
7. **Competition:** `get_market_activity(category="for_sale")` within 1.5km for same and larger bed counts. Pull listingHistory for the most relevant 6 to find passed deadlines and price changes. The method is the same as `listing-update` STEP 2A.
8. **Suburb:** `get_suburb_context(slug, statistics:true, demographics:true)` for:
   - median and its trend
   - growth by bed count
   - days on market for 12 months and the latest quarter
   - stock, clearance and vacancy
   - rent
   - 10-year growth and CAGR
9. **Outliers:** nearby sales the owner may quote that aren't comparable, such as riverfront homes, large sites, luxury new builds or a different property type. Write one neutral line on why each one differs.

---

## STEP 2: Structure (5 pages, A4 portrait)

The page kit and coordinates are in `report-export` → "Report layout kit".

1. **Cover**
   - Hero photo, then the title "Pre-Appraisal Briefing" and the eyebrow "AGENT USE ONLY · <date>".
   - Address and specs.
   - Dark panel with "STASH AVM $X.XXm" and "INDICATIVE RANGE (SUBJECT TO INSPECTION) $X.XXm–$X.XXm".
   - Footer: logo, "Prepared by", date.
2. **The property**
   - Four stat rows:
     - weighted value (N sales within 1km, adjusted)
     - Stash AVM (confidence and range)
     - owner hold (years, bought $X)
     - rental estimate (and gross yield)
   - Dark side panel "Property profile": type, beds/baths/cars/pool, land and floor area, year built, zone and overlays, flood band, other overlays, and what's nearby.
   - Tint band "Sales history": up to 3 figures (e.g. land purchase, bought new, today est. +X%).
3. **Comparable sales** (photo page)
   - A 2×2 grid of photo cards. Each card shows: name · distance, a specs line, and "$X.XXm Mon ’YY · adjusted $X.XXm".
   - A row of 3 on-market tiles: asking price and status.
   - Caption naming the photo source.
4. **Where the evidence points**
   - Intro with the adjustment rates.
   - Adjustment table with columns Sale | Sold | Land | Bath | Car | Pool | Floor | Adjusted | Rating.
   - Summary rows: HIGH average, MED average, Stash AVM, weighted value, with the weights. Highlight the weighted row in TINT.
   - Footnote: promotion rules if no comp met every HIGH test, any comp missing floor area, and the indicative range.
   - Tint section "Nearby sales that aren't like-for-like": 4 blocks, each "address · $X.XXm" plus one neutral line.
5. **Competition and market**
   - Competition table with columns Listing | Home | Asking | Days | Campaign so far, and a takeaway line.
   - Market table with columns Measure | Now | Context.
   - "To confirm at the appraisal".
   - Disclaimer: "Agent use only", data from Stash Property as at <date>, not a formal valuation.

---

## STEP 3: Build and export

Follow `report-export` STEP C for the chosen format, using the layout kit.

- **Canva:** start from the Pre-Appraisal Briefing template link in `report-export` → "Canva templates". If none is listed, `copy-design` a previous briefing; otherwise generate and rebuild to the layout kit.
- **PDF:** fill `report-export/examples/briefing_example.json` with this property's data and run `report-export/scripts/build_briefing.py data.json out.pdf [brand.json]`. Don't write new layout code. Get photos with the thumbnail method in `report-export`.
- **Name:** `Pre-Appraisal_<Street>_<Suburb>`. In Canva: "Pre-Appraisal Briefing – <address>".

## Finish

Give the link or file and the indicative range with its basis (weighted value and number of comps). Name the 2–3 things to check on site, and any data gaps.
