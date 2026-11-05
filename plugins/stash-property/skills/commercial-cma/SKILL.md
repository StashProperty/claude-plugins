---
name: commercial-cma
description: "Use INSTEAD of cma when a valuation request (CMA, quick val, appraisal, price guide, comps, \"what's it worth\") is for a commercial or industrial property: warehouse, factory, office, retail, shop, medical, showroom, or any non-residential zone or property type. Full report exports as PDF, Word or Canva with your branding."
---

# Commercial CMA — Commercial & Industrial Property Valuation

Residential CMA logic (bed/bath matching, house comps, residential AVM) does
not work for commercial or industrial property. This skill values on land
rate, building rate and, where income is known, capitalised net rent, using
web-sourced commercial sales evidence.

Triggers: any request that would trigger `cma` ("CMA", "quick val",
"appraisal", "price guide", "comps", "comparable sales", "what's it worth",
"what should I pay / offer", "what can I sell for", "market analysis",
"property report") where the property is commercial or industrial.

---

## STEP 0 — Detect (when to switch to this skill)

Use this skill straight away if the user says the property is a warehouse,
factory, shed, office, shop, retail, medical, showroom or similar.

Otherwise detect after resolving the address. Switch from `cma` to this
skill if ANY of these is true in the Stash result:

- `propertyType` is Industrial, Commercial, Retail, Office or similar
- `propertyCategory` is `NonResidential`
- Zone is non-residential (QLD examples: LII Low Impact Industry, IN General
  Industry, MU Mixed Use, NC Neighbourhood Centre, DC District Centre, PC
  Principal Centre, SP Specialised Centre)
- Bedroom/bathroom attributes are implausible for the land and building
  size (e.g. 1 bed on 890 m² with a 556 m² building)
- A web search shows the address marketed as commercial for sale or lease

If a `cma` quickval already ran with house comps, keep the subject data and
discard the house comps as evidence. Say so plainly.

---

## STAGE 1 — Commercial quickval (always runs first, chat only)

### 1. Subject data (Stash, reuse if already in context)

```
suggest_entity(query="[full address]", type="property")
  -> propertyId, lat, lon, land area, alternative addresses

get_property_profile(propertyId,
  include={salesHistory:true, valuations:true, zones:true, marketStatus:true})
  -> zone, land area, building area, last sale, site value, tenure

get_planning_and_risks(propertyId)
  -> zone, minimum lot size, overlays, flood / bushfire / heritage
```

- Building area (GFA/NLA) is the key attribute. Ignore bed/bath.
- Note every alternative address (corner sites often list under two streets)
  and search the web under each.
- Record site cover = building area / land area.
- Do NOT call `get_property_avm` as evidence. If an AVM is already in
  context, report it as unreliable (it is a residential model, normally
  VeryLow confidence here) and give it zero weight.
- Do NOT fetch house comps. Stash `get_market_activity` and PropRadar
  sold tools do not cover commercial or industrial sales.

### 2. Subject web research

Search the subject address (and alternative address) for:

- Current or past lease listings: tenancy sizes, asking rent, uses, agent
- Past sale campaigns: sale method, price, description
- Tenants, fit-out, parking, exposure, roller doors, clearance heights

### 3. Sales evidence (web)

Go to the web. Target 4-8 priced sales. Search order:

1. Same zone, same suburb
2. Same zone, adjoining suburbs / same inner-ring precinct
3. Other commercial zones on the same road or centre
4. Wider precinct, last resort

Useful sources: commercialrealestate.com.au sold pages by suburb and
category, realcommercial.com.au sold pages, commercial agency sold pages
(Ray White Commercial, Colliers, CBRE, Cushman & Wakefield, Knight Frank,
JLL, Savills, Elders Commercial, Chase Commercial, McGees), portal street
records for undisclosed prices, and news (urban.com.au, Australian Property
Journal, AFR).

For each comp capture: address, sale date, price, land area, building area,
zone, vacant or tenanted (net income and yield if tenanted), property type,
source of the price.

Rules:

- Time window: prefer 24 months. Extend to 36 months if fewer than 4 priced
  comps. Commercial markets are thin, so older evidence is acceptable if
  flagged.
- Many sold prices are undisclosed. Try the portal street record for the
  address. If still undisclosed, list the sale as unrated context, never
  estimate its price.
- Exclude strata units when the subject is freehold freestanding (and the
  reverse). Exclude development sites sold on approved yield.
- A price shown as $0 is undisclosed, not a sale price.
- Never invent a price, size, yield or growth index. If a number can't be
  sourced, say it is missing.

### 4. Analysis

For each priced comp compute:

```
land_rate     = price / land area        ($/m² land)
building_rate = price / building area    ($/m² building)
site_cover    = building area / land area
```

Apply to the subject:

```
land_method     = comp land rate range x subject land area
building_method = comp building rate range x subject building area
```

- If the two methods diverge, explain it by site cover. Low site cover on
  the subject means surplus hardstand / parking land that the building rate
  misses; the land method carries more weight.
- Small lots sell at a higher $/m² than large lots. Discount small-lot
  rates when applying to a larger subject.
- Qualitative adjustments only: zone match, main-road exposure, corner
  position, parking, building condition and age, vacant possession vs
  tenanted, distance to CBD.

Income method (only if net income is known or supplied):

```
value = net annual income / market yield
```

- Market yield must come from comp sales that disclosed income, or from a
  cited current research report. Never assume a yield.
- If income is unknown, state that the income method is missing and that
  it is the primary method for a tenanted asset. Ask for the tenancy
  schedule (tenant, area, rent, expiry, options, outgoings).

Cross-check: implied annual growth from the last sale price to the guide
midpoint. Flag anything implausible.

Confidence:

- Medium: 4+ priced comps, at least 2 same zone, at least 2 within 12
  months, income known
- Low-to-medium: 4+ priced comps but dated, or income unknown
- Low: fewer than 4 priced comps. Recommend a licensed commercial valuer.

### 5. Quickval response format (chat only)

Lead with the guide. Keep it tight.

```
**Price guide: $X.XXm – $X.XXm ([confidence] confidence)**

**[Address]** — [property type], [zone], [land] m² land, [building] m²
building, [site cover]% site cover
Last sold [date] at $X.XXm ([X]-year hold)

Subject findings: 2-3 bullets (leasing history, tenancy profile, planning
and hazards).

Sales evidence table:
Property | Sold | Price | Building / land | $/m² land | Read-across

Unrated context: undisclosed-price sales worth knowing about.

How the range was built: land method, building method, cross-check.

Gaps that matter: missing income, dated comps, unverified prices.
```

End with:

> **Want me to write this up as a full report?** Let me know if this is for
> buying, selling, or development and I'll take it from there.

If the tenancy schedule is missing, ask for it in the same message.

---

## STAGE 2 — Full Commercial CMA (only on explicit escalation)

Route on the answer:

- **Buying** -> buyer's commercial CMA
- **Selling** -> vendor's commercial CMA
- **Development** -> ask the sub-type, then hand off to the `feaso` skill
  with propertyId, lat/lon, zone, land area and the guide as buy-in cost.
  Do not produce a CMA document as well.

If the answer is ambiguous ("yes", "go ahead"), ask the buying / selling /
development question again. Never mix buyer and seller framing in one
document. Reuse everything from Stage 1; do not re-fetch.

### Export format + brand (second ask, after the role)

Load the `report-export` skill and ask its one card, skipping anything already
answered in the conversation:

- How would you like to export it? PDF / Word (.docx) / Canva design
- Branding: Stash (default) / my saved brand / paste a brand URL / unbranded

Resolve the brand into tokens (PRIMARY, ACCENT, TINT, ALT, TEXT) per
`report-export` before building.

### Valuation summary

```
fair_value = reconciled midpoint of land, building and (if available)
             income methods. State the weight given to each and why.

// Buying
opening_offer = fair_value x 0.93
max_bid       = fair_value x 1.05

// Selling
listing_low   = fair_value x 0.97
listing_high  = fair_value x 1.05
```

### Report sections

Content is identical in every format. Build rules per format come from
`report-export`:

- **Word:** read the docx skill.
- **PDF:** read the pdf skill; ReportLab, built directly from the data in context.
- **Canva:** generate the design, then rebuild the content page by page; draw
  any charts with native shapes. Confirm with the user before committing.

**Cover** — agency logo (or "Agency logo" placeholder) and "Prepared by [Agent name]" when a non-Stash brand is used; title "COMMERCIAL MARKET ANALYSIS"; buyer mode adds the
"BUYERS AGENT" badge and "Prepared for Buyer — Confidential"; seller mode
"Prepared for Vendor — Confidential". Value label: "ESTIMATED FAIR VALUE /
MAXIMUM BID" (buyer) or "RECOMMENDED LISTING RANGE" (seller).

1. **Subject Property** — address (and alternative address), property type,
   zone, land, building area, site cover, parking, last sale, site value,
   leasing history.
2. **Tenancy & Income** — tenancy schedule and net income if supplied;
   otherwise state it was not available and what is needed.
3. **Sales Evidence** — table: Address | Sold | Price | Land | Building |
   $/m² land | $/m² bldg | Zone | Vacant/Tenanted | Relev. (HIGH / MED /
   LOW). Unrated undisclosed sales listed below the table.
4. **Evidence Commentary** — anchor comp, floor comp, what each means for
   the offer (buyer) or the listing price (seller).
5. **Valuation Summary** — land method, building method, income method,
   reconciled fair value, cross-check against last sale, confidence.
6. **Planning & Risk** — zone and permitted uses, minimum lot size,
   overlays, flood, heritage, contamination risk for industrial uses,
   existing-use rights and approvals for current tenancies.
7. **Strategy** — buyer: opening offer, max bid, levers (income gaps,
   vacancy, lease expiries, dated evidence), due diligence list (lease
   documents, outgoings, building and environmental reports, GST / going
   concern treatment). Seller: listing range, sale method (EOI, auction,
   private treaty), campaign notes, disclosure checklist.

### Formatting

Use the document conventions from the `cma` skill, with colours from the
brand tokens chosen above (Stash default shown):

- Arial (Word) / Helvetica (PDF) / brand kit font (Canva)
- PRIMARY `#32374A` dominant; ACCENT `#3555FF` for small accents only;
  TINT highlight row `#EEF1FF`; ALT rows `#F4F5F8`. If a custom ACCENT is
  light (e.g. yellow), use it only as a fill behind PRIMARY text
- Relevance and risk fills: HIGH/NONE green `#F0FAF8` / `#1B7A3E`, MED
  amber `#FFF8E6` / `#C87000`, LOW/HIGH-risk red `#FFF0EE` / `#A82020`
- Prices as `$X.XXm`; rates as `$X,XXX/m²`; dates as `Nov ’25`
- Page break before each major section
- Relevance and risk colours are semantic and never change with brand
- Output: `CommercialCMA_[StreetName]_[Suburb]_[Buyer|Seller]` as .pdf or
  .docx (sent to the user) or a Canva design (edit link after commit). If the
  user later asks for another format, rebuild from the data in context.

---

## Links and sources

- Subject property link: always
  `https://stashproperty.com.au/app/properties/{propertyId}/` (trailing
  slash).
- Commercial comps have no Stash page. Leave comp addresses unlinked in
  tables.
- Web evidence must be verifiable: end the chat response and the document
  with a short Sources list of the pages the prices and sizes came from.
- Mark any price taken from a portal street record rather than an agent or
  title record as unverified.

---

## Critical rules

- Never value commercial or industrial property from house comps.
- Never rely on the residential AVM. Report it only to dismiss it.
- Never invent prices, yields, rents or growth rates.
- Always show both the land-rate and building-rate methods and explain any
  gap between them.
- Always state whether income evidence was available.
- Quickval always runs first; ask the buying / selling / development
  question only at escalation.
- Each commercial CMA is self-contained. Never reuse coordinates, comps or
  conclusions from another property.
- With fewer than 4 priced comps, or any unusual asset, recommend a
  licensed commercial valuer.
- Never reproduce another company's logo; use the user's own brand kit logo
  or an "Agency logo" placeholder.
