---
name: "listing-update"
description: "Vendor-facing Listing Update / campaign review (\"Day 20\") with real Stash listing photos, showing why a listed property's guide needs to meet the market. Exports to PDF, Word or Canva, in your brand. Has a sample/demo mode."
---

# Listing Update: Campaign Review Skill

Produces a vendor-facing **Listing Update** for a property that is on the market but not selling. It gives the agent visual, evidence-based support to condition the vendor on price. The report is framed around the campaign day ("Campaign review · Day 20") and compares the vendor's guide with:

- competing listings
- recent campaigns that started too high
- the CMA market range
- current market conditions

Triggers: "listing update", "campaign review", "vendor update", "day 20 report", "price conditioning", "vendor isn't meeting the market", "why the price needs to move", or a request to show a vendor evidence for a guide adjustment.

---

## Language rules (non-negotiable)

The report goes to the vendor. Tone is calm, factual and supportive.

- NEVER write "price reduction", "drop the price", "cut", "overpriced" or "reduce".
- Use instead: "align the guide to the market", "refresh the campaign", "meet the market", "where buyers are transacting", "market range", "reach the largest group of active buyers".
- Lead every section with a one-line takeaway in plain English, then the evidence.
- Never fabricate figures. Anything the agent must supply (enquiries, inspections, offers) is shown as `[agent to add]`.
- If the campaign facts are illustrative (no real listing date or guide given), label the report as an example on the cover.

---

## Sample / demo mode

Use when the user wants a demo or sample report ("sample report", "demo", "show what people can get", "fake the address").

- Build from real Stash market data for a real suburb, but give the subject a **fictional address**. Check it with `suggest_entity(type="property")`: it must return no results.
- No "SAMPLE REPORT" pill on the cover by default. Start the disclaimer with "The property address is fictional." Add a pill only if the user asks for one.
- Buyer activity may be filled with realistic illustrative numbers, but the panel heading must say "(sample figures)". Outside sample mode, never invent them: use `[agent to add]`.
- Images: use photoreal AI images (see `report-export` → "Sample mode"), and caption every page that has them "Images are AI-generated for illustration". Stash photos of real nearby homes may go on the comp cards. Never claim a photo is the subject. Never use another real address as the subject.
- Fill "Prepared by" and the contact line with the brand name and website instead of `[Agent name]` placeholders.

---

## STEP 0: Ask first (one prompt, before any data calls)

Ask these together in a single question card (AskUserQuestion, or ask_user_input_v0 on claude.ai). Skip any that the user already answered.

1. **Export format:** PDF / Word (.docx) / Canva design
2. **Campaign facts**, if not given: listing date or days on market, current guide (e.g. "Offers over $2.95m"), and method (private treaty / auction / EOI / best-offers date)
3. **Branding:** Stash (default) / my saved brand / paste a brand URL (website, Canva brand kit name or hex codes) / unbranded

Resolve the brand into tokens (PRIMARY, ACCENT, TINT, ALT, TEXT) with the `report-export` skill: it checks Canva brand kits, extracts colours from a pasted URL, and offers to save the brand as the default.

Optional, accepted if offered but never blocking: portal views, enquiries, inspections, second inspections, offers, and buyer price feedback. If not supplied, show `[agent to add]`.

Compute **Day N** = report date − listing date (calendar days). Use it in the cover subtitle ("Campaign review · Day N · <date>") and the snapshot headline ("Day N: your guide sits $X above the market").

---

## STEP 1: Market range (reuse the CMA)

If a CMA for this property exists in the conversation, reuse its:

- weighted CMA
- listing range
- adjusted comps
- AVM
- planning flags

Otherwise run the `cma` skill's Stage 1 and Stage 2 calculations silently (no CMA document). These are the steps:

- `suggest_entity` resolves the address.
- `get_property_profile` with salesHistory + valuations.
- `get_property_avm`.
- `get_market_activity` for sold houses within a 1km radius over 180 days, `minBed` = bed−1, limit 15.
- Score the comps and apply the CMA adjustments (land, bathrooms, car, pool, and floor area where recorded).

**Market range** = weighted × 0.97 to weighted × 1.05.
**Gap** = guide ÷ top of range − 1, and guide ÷ midpoint − 1.

If the vendor has advised changes since the last sale (pool, renovation), apply them to the subject before adjusting.

---

## STEP 2: Stash evidence pulls

Large result sets get saved to file. Parse them with `jq` (address, propertyId, bed, bath, land, builtYear, firstListedDate, daysOnTheMarket, firstAskingPrice, price, saleDetails, distance, mainImage.url).

**A. Competing listings**

```
get_market_activity(where={lat,lon,radius:1500}, category="for_sale",
  propertyType=["House"], minBed=subject_bed, limit=25)
```

Keep listings within about ±25% of the subject guide, plus any same-street or larger homes asking at or below the subject guide. For the 8–12 most relevant, call `get_property_profile(include={listingHistory:true})` and read `listings[].auditLog` and `firstSeen` for:

- passed offers deadlines or auctions ("Best offers by 30 Sep" and still listed)
- advertised price changes (e.g. Offers over $2.90m to $2.60m)
- prior withdrawn campaigns

**B. Recent campaigns that started too high**

```
get_market_activity(where={lat,lon,radius:1500}, category="sold",
  propertyType=["House"], minBed=subject_bed, days=270, limit=40)
```

Shortlist sales with daysOnTheMarket > 60 or a numeric first asking price above the sale price. Pull `listingHistory` and `salesHistory` for each to capture:

- withdrawn campaigns
- the first advertised price
- total days across all campaigns

Compute the change from first asking price to sale price. Do not trust `listingInsights.discount`; its sign and base are inconsistent. Always calculate the change yourself from the advertised figures.

**C. Priced-right contrast**

From the CMA comp set, take 2–3 comparable sales that sold in 30 days or less. Show their days to sell and sale price.

**D. Resale check (going-down evidence)**

Look for comps or competing listings with a prior sale in the last 3 years. Show the prior sale against the current sale or asking price.

- Prefer resales that went **down or flat**: under the suburb's growth for the same period, or a passed deadline at roughly the last sale price.
- If none are down, use the closest flat or below-trend resale (e.g. sold $2.61m, now asking $2.69m 14 months later, +3%), and lean on evidence B instead.
- Never invent a loss.

**E. Listing photos (Stash)**

Every `get_market_activity` row has `mainImage.url`, a public JPEG on `property-images-ap-southeast-2.proptechdata.io`. Capture it with the address when parsing A, B and C.

- **Subject:** use its current listing photo if Stash has one. Otherwise ask the agent for a hero photo. In sample mode, use a similar nearby home's photo.
- **Competition:** the photos of the 4 most comparable listings (same bed count, nearest guide).
- **Priced-right sales:** the photos of the 2–3 fast sales from C.

The sandbox cannot download these images (the proxy blocks the host). Canva can: `upload-asset-from-url` with the `mainImage.url` returns an asset id to place with `insert_fill` or `update_fill`.

**F. Suburb context**

`get_suburb_context(slug, statistics:true)`. Use:

- house median DOM
- 12-month growth by bedroom count (e.g. 4-bed +2.3% against 5-bed +13.8%)
- auction clearance
- stock on market

---

## STEP 3: Market conditions (Stash first)

**Source order (strict):** Stash MCP first. Only where Stash has no figure, use domain.com.au or realestate.com.au. Do not use or cite Cotality, CoreLogic, SQM or other data vendors. The RBA is fine for the cash rate.

**From Stash (always):**

- `get_suburb_context(slug, statistics:true)`: median price and 12-month change, median DOM, auction clearance, stock on market, growth by bedroom count.
- `get_market_activity(category="for_sale")` over the suburb: count of current listings, and how many were first listed in the last 30 days (new listings).
- `get_market_activity(category="sold", days=90)` vs `days=365`: median days on market and sales count now vs the year, computed from the rows.
- Repeat `get_suburb_context` for the city/region slug if available, for a wider read.

**Web, only for gaps** (current month and year, `allowed_domains=["domain.com.au","realestate.com.au"]`):

- "<city> auction clearance rate <month year>"
- "<city> house prices <month year>"

Extract only dated, sourced figures. Label each KPI tile with its source ("Stash Property", "Domain", "realestate.com.au"). If the market is rising, say so honestly and frame the section around competition and buyer choice instead of falling values.

---

## STEP 4: Report structure (9 pages, A4 portrait)

1. **Cover:** full-bleed hero photo on top, then the title "Campaign Review", the eyebrow "LISTING UPDATE · <date>", address and specs. No Day N badge on the cover; Day N goes in the snapshot headline. Two stat panels: Current guide (charcoal) and Where the market is trading (accent colour). Agency logo or placeholder, "Prepared by [Agent name]", and the date.
2. **Campaign snapshot:** the headline "Day N: your guide sits $X above the market". Facts grid:
   - Listed
   - Days on market (vs suburb median)
   - Current guide
   - Method
   - Comparable sales range
   - Gap to the market

   Below it, the buyer activity panel. Then a callout on the first 2–3 weeks and portal price filters (state the bracket the guide falls into, e.g. "a guide above $2.75m hides your home from buyers searching up to $2.75m").
3. **The market has shifted** (Stash data first, Domain/realestate.com.au for gaps): 4 KPI tiles, a supporting panel headed "What it means for your campaign", and a sources line.
4. **Your competition:** a days-on-market bar chart (subject highlighted in the accent colour, a dashed line at the suburb median, bars shaded darker for >60 days) and a campaign history table:
   - Address
   - Bd/Ba
   - Land
   - Days
   - Campaign so far
   - Guide now

   Takeaway line: how many listings passed a deadline or auction unsold. Note larger homes asking the same money.
5. **Homes buyers are comparing** (photo page):
   - Top: a 2×2 grid of the most comparable competing listings. Each card has the photo (307×180), address (bold), specs line, and a status line in ACCENT, e.g. "55 days · was $2.90m, now $2.60m".
   - Bottom: "Priced right from day one", three photos of the fast sales with a big "11 days" figure and "address · sold $X.XXm".
   - Caption: "Listing photos from Stash Property. Days on market as at <date>."
6. **What recent campaigns tell us:** a dumbbell chart (first advertised price in grey, result in charcoal, with the % change) and a "Time is a cost too" line. Then a priced-right contrast panel with big "11 days / 24 days / 28 days" figures.
7. **Where your price sits:** a stat stack (range bottom / range top / your guide with the % gap). A ranked dot chart combines adjusted sales (black) and competing guides (grey), with the shaded market band and a guide line. Then the resale check card (big "+3% in 14 months" or similar) and the 4-bed vs 5-bed growth note.
8. **Options from here:**
   - A · Hold the guide (likely outcome)
   - B · Align to the market (offers over the bottom of the range)
   - C · Set a date (best offers within 14–21 days at the range)
   - No recommendation in the report. The intro says the decision is the vendor's and that their agent will talk them through how each option fits their timing and goals. The agent makes the recommendation in conversation.
9. **Next steps:** a tall Stash listing photo on the left, then the "This week" action list, opening "Once you've chosen a direction, we can refresh the campaign within 48 hours…" (agree the guide and date, new lead photo and portal relaunch, call every past enquirer, weekly update), the agent contact line, and the disclaimer: market evidence from Stash Property as at <date> (name Domain or realestate.com.au only if used); an indicative market review, not a formal valuation.

---

## STEP 5: Export (format chosen in STEP 0)

General build rules for each format live in `report-export`. The listing-update specifics are below. "Charcoal" and "accent colour" in STEP 4 mean the PRIMARY and ACCENT brand tokens.

### PDF

Fill `report-export/examples/campaign_review_example.json` with this
campaign's data. Prices that drive charts are numbers in $m. Then run:

    python3 report-export/scripts/build_campaign_review.py data.json out.pdf [brand.json]

The script draws the DOM bars, the dumbbell and the ranked dot chart
natively, in the brand colours. Don't write new layout code. Render with
`pdftoppm` and check every page against
`report-export/examples/reference/Campaign_Review_example_Dwellicious.pdf`.

### Word (.docx)

- Read the docx skill.
- Use the same section order. Embed the matplotlib PNG charts. Use tables for the competition and campaign data, an accent-colour heading rule, and page breaks between sections.
- Convert to PDF and render it to check the layout before sending.

### PDF / Word with photos

The sandbox can't download Stash photos directly. Use the thumbnail method in `report-export` → "Report layout kit" → "Photos for PDF/Word". Canva fetches the photo (or generates it in sample mode), and the page thumbnail it returns is saved locally, cropped, and placed in ReportLab or docx. Only if that fails, build without photos and say why.

### Canva

0. **Fastest path:** start from the Campaign Review template link in `report-export` → "Canva templates" if one is listed. Otherwise, if a previous Campaign Review design exists in the user's Canva, `copy-design` it and restyle it rather than generating again.
   - Use `recolor_element` on shapes and `format_text` on text to apply the brand tokens. Generate the per-element operations with a Python script from the `read-design` JSON; large reads are saved to a file you can parse.
   - Swap the photos with `update_fill`, replace the address everywhere, and add the photo page with `add_page`, then `reorder_page` and renumber the page footers.
   - Put the brand logo in each footer band, but only when it is the user's own brand.
1. Use the brand resolved in STEP 0: pass `brand_kit_id` if it came from a Canva brand kit, otherwise style with the extracted tokens (e.g. a Ray White-style palette: yellow #FFE512, charcoal #2B2B2B, white).
   - Never reproduce another company's logo or wordmark. Leave an "Agency logo" placeholder for the agent to drop in from their own brand kit.
2. `generate-design` (design_type "report") with a detailed page-by-page query containing ALL the data. Then `create-design-from-candidate`.
3. Canva's generator summarises and drops the evidence. Expect to rebuild the content:
   - `read-design` with `open_transaction`, then `edit-design` page by page: replace_text, delete off-message stock images (e.g. rising-arrow graphs), add_text, format_text.
   - Draw charts natively with `insert_shape`: rectangles for bars, 14px circles (`M7 0A7 7 0 1 1 7 14A7 7 0 1 1 7 0Z`) for dots, thin rectangles for lines and bands.
   - Generate the operation JSON with a short Python script so the coordinates line up.
   - Image uploads from the sandbox are usually blocked by the proxy, so don't rely on uploading matplotlib PNGs. Public URLs work: use `upload-asset-from-url` for Stash listing photos and the brand logo.
   - `update_fill` center-crops. If a photo frames badly, try `crop_media` or pick a different photo; check the thumbnail.
   - New text defaults to 16pt black; always follow with format_text. Use `layer_element` to bring text above added panels.
   - Check each page's returned thumbnail and fix overlaps or wrapping before moving on.
4. Rename the design to "Campaign Review – <street>, <suburb> (Day N)".
5. Ask the user to approve, then commit. Give them the edit link.
6. If they want a file, `export-design` as PDF (A4). The download link is for the user; the sandbox can't fetch it.

---

## Finish

Reply briefly:

- the file or link
- Day N, the guide against the range, and the gap %
- the 2–3 strongest pieces of evidence
- which items are placeholders for the agent (or, in sample mode, which items are illustrative)
- sources: Stash first, then any Domain / realestate.com.au pages used, and Stash property links where useful

Do not recap the steps.
