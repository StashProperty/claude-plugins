---
name: report-export
description: "Shared export, branding and layout kit for Stash report skills (cma, pre-appraisal, listing-update, feaso, commercial-cma, reno-case-studies, find-suburbs, deals): PDF, Word or Canva in your brand, with photos; Stash data first."
---

# Report Export & Branding (shared)

Use this skill whenever any Stash report skill is about to produce a client-facing document. That includes:

- `cma`
- `commercial-cma`
- `feaso`
- `listing-update`
- `pre-appraisal`
- `reno-case-studies`
- `find-suburbs`
- `find-on-market-deals`

It decides two things once per report: **the export format** and **the brand**. It then gives build rules for each format. The calling skill still owns the content: sections, data, wording and calculations.

If a calling skill hard-codes a format (e.g. "produce a .docx") or the Stash palette, this skill overrides that. The user's choice here wins.

---

## STEP A: Ask (one card, two questions)

Ask at the moment the report is about to be built, not at the start of a quick chat answer.

Use AskUserQuestion (or ask_user_input_v0 on claude.ai). Skip any question the user has already answered in the conversation, e.g. "give me a PDF", "do it in Canva", or a brand already used earlier.

1. **How would you like to export it?**
   - PDF
   - Word (.docx)
   - Canva design
2. **Branding**
   - Stash Property (default)
   - My saved brand (show this option only if a saved brand exists; see STEP B)
   - Paste a brand URL: the user types a website URL, Canva brand kit name or hex codes in the free-text "Other" field
   - Unbranded (neutral charcoal)

For an Excel deliverable (e.g. the feaso model), the format question doesn't apply. Still apply the brand colours to the header fills.

---

## STEP B: Resolve the brand

### Saved brand

Before asking, check memory for `/topics/report-branding.md`. If it exists, offer it as "My saved brand (<name>)".

After a new brand is extracted, ask once: "Save this as your default brand for reports?" If yes, write or update `/topics/report-branding.md` with:

- name
- source URL
- the hex tokens below
- font notes
- logo rule

### From a pasted URL

1. **Check Canva first.** Call `list-brand-kits`. If a kit matches the brand name, use it: pass `brand_kit_id` for Canva, and read its colours for PDF/Word.
2. **Otherwise extract from the site.**
   - Open the URL in the user's browser (Claude in Chrome, or the built-in browser) and run JavaScript that reads `getComputedStyle` on body, h1/h2, buttons, links, the header and the footer. Collect the most-used non-neutral colours and the font families.
   - WebFetch only returns text, so it rarely shows colours. Use it just for the name and tagline.
   - If no browser is available, ask the user for 2–3 hex codes.
3. **Map to tokens:**

| Token | Use | Stash default |
|---|---|---|
| PRIMARY | Headings, table headers, dark panels, body emphasis | #32374A |
| ACCENT | Highlights, key figures, cover panel, "your property" in charts | #3555FF |
| TINT | Soft highlight rows, market-range bands | #EEF1FF |
| ALT | Zebra rows, cover bar background | #F4F5F8 |
| ACCENT_DARK | Accent used as text on white (eyebrows, status lines) | #3555FF |
| ACCENT_ON_DARK | Accent on PRIMARY panels; must contrast with PRIMARY | #9AABFF |
| TEXT | Body text | #333333 |
| ON_ACCENT | Text placed on ACCENT | white or PRIMARY, whichever has the higher contrast |

   Example: Ray White-style gives PRIMARY #2B2B2B, ACCENT #FFE512, TINT #FFF6B3, ALT #F4F4F4, ON_ACCENT #2B2B2B.

4. **Contrast check.** If ACCENT is light (e.g. yellow), never use it for text on white. Use it as a fill behind PRIMARY text, or on dark PRIMARY panels.
5. **Risk colours stay semantic** whatever the brand: HIGH red, MED amber, LOW soft tint, NONE green.

### Logos and names

- Use a logo only if it is the user's own brand (their agency or Stash) and they confirm it, or it comes from their Canva brand kit.
- Otherwise leave an "Agency logo" placeholder.
- Never recreate another company's logo or wordmark.
- Put the agent name and contact as `[Agent name] · [Mobile] · [Email]` unless supplied.

---

## STEP C: Build in the chosen format

All formats share these rules:

- Same sections, data and wording as the calling skill.
- Prices in $X.XXm format.
- Stash property links on addresses wherever the format supports links.
- Disclaimer from the calling skill.
- File and design names: `<ReportType>_<StreetName>_<Suburb>[_<Mode>]`.

### PDF

**For the three designed reports, always use the fixed build scripts.** Don't
write new layout code. The scripts are in this skill's `scripts/` folder:

| Report | Script | Example data |
|---|---|---|
| Property Appraisal (seller) | `build_appraisal.py` | `examples/appraisal_example.json` |
| Pre-Appraisal Briefing | `build_briefing.py` | `examples/briefing_example.json` |
| Campaign Review | `build_campaign_review.py` | `examples/campaign_review_example.json` |

1. Copy the matching example JSON and replace every value with this
   report's data. Keep the same keys and list lengths (4 photo cards, 3
   on-market tiles, 4 value-change blocks, and so on). Image paths are
   relative to the JSON file.
2. Write the brand JSON: name, primary, accent, accent_dark,
   accent_on_dark, tint, text, muted, logo. `examples/brand_example.json`
   shows the format. Leave it out for the Stash default.
3. Find the skill folder (the folder holding this SKILL.md). If you're unsure where it is, run
   `find / -path '*report-export/scripts/kit.py' 2>/dev/null | head -1`.
   Then run `python3 <skill>/scripts/build_<report>.py data.json out.pdf
   [brand.json]`. It needs only reportlab and Pillow; install them with
   `pip install reportlab pillow` if missing.
4. Render with `pdftoppm -r 50` and look at every page. Long text shrinks
   to fit one line, but check for wrapping in the body text and shorten
   the wording if needed.
5. Compare against the layout you get by building the matching file in
   `examples/` (e.g. `appraisal_example.json`) with the same script.

For any other report (buyer CMA, feaso, case studies, and so on), use
ReportLab with these rules:

- A4, 18mm margins, a running header in PRIMARY, and a footer with the
  disclaimer and page number.
- Build charts in matplotlib using the brand tokens.
- Avoid glyphs Helvetica lacks (→ ≤ − ☐ ²): write "to", "<=", "-", "sqm".
- Render the pages with `pdftoppm` and look at them before sending.

### Word (.docx)

- Read the docx skill.
- Arial throughout. Table headers in PRIMARY with white text, highlight rows in TINT, cover bar in ALT with an ACCENT rule.
- Embed charts as PNGs.
- Convert to PDF and render it to check the layout before sending.

### Canva

**Start from the template when one is listed.** If the user, their
organisation or this bundle has published a Canva template for this report
(see "Canva templates" below):

1. `resolve-shortlink` or open the template link to get its design id.
2. `copy-design` it. Fill it with `replace_text`, `update_fill` for photos,
   and `format_text`, following the same page structure as the PDF script.
3. If the copy fails (no access), ask the user to click the template link
   once to make their own copy, then find it with `search-designs`.

**Otherwise:**

1. If the user has an earlier design of the same report in their Canva
   account, `copy-design` it.
2. If there is no earlier design, call `generate-design` (design_type
   `report`) with a detailed page-by-page query containing ALL figures,
   tables and wording. Then call `create-design-from-candidate`.
3. Rebuild it to the page grid in the layout kit below. Use the example
   JSON for the content and the reference PNGs for the look.

**In every case:**

- Generate the operation JSON with a short Python script so the
  coordinates line up.
- After each page, check the returned thumbnail for overflow, wrapping or
  overlap and fix it before moving on.
- Replace template placeholders ("hello@reallygreatsite.com", phone
  numbers) with the agent's details or `[Agent name]` fields.
- Call `update_title` with the report name.
- Ask the user to approve, then `commit`. Share the edit link, and offer
  `export-design` as a PDF.

### Canva templates

When the report owner shares a Canva template link ("Share → Template
link" in Canva), record it here so every user starts from the same design:

| Report | Template link |
|---|---|
| Property Appraisal (seller) | `[paste template link]` |
| Pre-Appraisal Briefing | `[paste template link]` |
| Campaign Review | `[paste template link]` |

If a row still says `[paste template link]`, use the "Otherwise" route
above.

---

## Report layout kit (Canva and PDF look the same)

Use this kit so a report built in Canva and the same report built as a PDF
match page for page. The three designed reports are:

| Report | Skill | Pages | Reader |
|---|---|---|---|
| Campaign Review (Listing Update) | `listing-update` | 9 | vendor, on the market |
| Property Appraisal (seller) | `cma`, SELLING, seller appraisal | 6, price last | owner, before listing |
| Pre-Appraisal Briefing | `pre-appraisal` | 5, evidence only | agent, before the appointment |

### Page grid

- **Page:** A4 at 794 × 1123 px in Canva.
- **Margins and columns:** 80 px side margins give a content width of 634 px. Two-column cards are 307 px wide with a 20 px gap. Three tiles are 198 px wide with a 20 px gap.
- **Footer:** a full-width TINT band from y=1043. Logo at (80, 1066), 130 × 27. "Page N" right-aligned at (511, 1072), w=244.
- **Cover:**
  - Hero photo from the top to about y=640.
  - A white rounded panel (radius about 68) overlapping it from y=596.
  - Title 76 px at y=627, eyebrow 14 px bold ACCENT-dark at y=832, address 26 px bold at y=858, specs 16 px at y=896.
  - A dark rounded stat panel at (80, 940), 634 × 104, holding two label/value pairs: label 12 px bold, value 38 px bold.
- **Page title:** 40–44 px PRIMARY at (80, 79). Intro 14–15 px at y=145–150.
- **Section eyebrow:** 12 px bold ACCENT-dark caps.
- **Tables:**
  - Header bar: a 26 px PRIMARY rect, with 11 px bold white labels at bar top + 6.
  - Rows: one multi-line text element per column, 12 px with line height 1.8 (about 21.6 px per row), starting at bar top + 32. First column bold PRIMARY.
  - Highlight row: a 24 px TINT rect behind it.
- **Photo cards:** photo 307 × 180, then name 15 px bold, specs 12 px, status 12 px bold ACCENT-dark.
- **Big-number tiles:** value 24–30 px bold, caption 12–13 px.
- **Price panel:** a PRIMARY rounded rect 634 × 250. Eyebrow 13 px bold ACCENT, range 56 px bold white, then a 1 px divider and three tiles.
- **Dark side panel:** a PRIMARY rect at x=449, width 345, full height to y=803. Heading 24 px bold ACCENT_ON_DARK, body 15 px white with line height 1.55.
- **ACCENT_ON_DARK:** the accent used on PRIMARY panels. It must stand out against PRIMARY: e.g. Stash blue #3555FF on #32374A is too dark, so use #9AABFF.

### Canva build notes (lessons learned)

- **Fastest path:** `copy-design` the last design of the same report and replace the content. Otherwise use `generate-design` + `create-design-from-candidate`, then rebuild.
- **Large reads:** `read-design` results for large designs are saved to a file. Parse the file with Python to get locator ids, positions and text.
- **New text:** `add_text` creates 16 px black text. Style it with `format_text` in a second call, using the locator ids returned. `font_size` must be an integer.
- **Apostrophes:** `find_and_replace_text` fails on curly apostrophes. Use `replace_text` on the element instead.
- **Shapes:** `insert_shape` with path `M0 0H{w}V{h}H0Z`, `view_box` = w,h, `color`, and optional `corner_rounding`.
- **Images:** `insert_fill` with `asset_id` places an image. Use `update_fill` to swap one.
- **New pages:** `add_page` (794×1123), then `read-design` with `page_indices` to get the new page id. `reorder_page` moves pages. Renumber the footers after.
- **Checking:** check every returned thumbnail for wrapping, overlap or empty gaps before moving on.
- **Finishing:** commit only after the user approves. Export with `export-design` as pdf, a4, pro. The link is the user's and lasts about a day; the sandbox can't download it.

### PDF build notes

- The scripts draw on the ReportLab canvas in Canva pixel coordinates.
  `kit.py` converts them (pt = px × 0.75, y flipped). Put any new
  component in `kit.py` so all three reports share it.
- **Fonts:** headings use the bundled Outfit font (`scripts/fonts`, OFL)
  and body text uses Helvetica. A brand JSON may set `heading_font` to
  another .ttf.
- **Missing images:** a missing image file draws a grey "Photo"
  placeholder, so the PDF still builds.

### Photos for PDF/Word (Canva thumbnail method, tested)

The sandbox can't download Stash photo URLs (proxy 403) or Canva exports.
Canva can fetch them, and the page thumbnails Canva returns are saved
locally.

1. **Get each image into Canva:**
   - **Stash photo:** `upload-asset-from-url` with `mainImage.url`.
     Check the returned `smart_tags`. If they show an interior
     ("livingroom", "couch", "furniture" without "exterior"), the
     main image isn't the house front: pick another comp, or use another
     image from `images[]`.
   - **AI image (sample mode):** `generate-image`, then
     `get-generate-image-job`.
2. **Render them on a scratch design.** Open any scratch design in a
   transaction and `add_page` at 1200 × 800 (one per photo). Put one
   photo full-page with `insert_fill` (top 0, left 0, 1200 × 800). Small
   tiles can share a page, e.g. three 400 × 400 squares.
3. **Collect the thumbnails.** Each `edit-design` call returns a ~600 ×
   400 thumbnail, saved as `tool-results/mcp-Canva-blob-*.png`. Copy each
   one to `images/` next to the data JSON, cropping with PIL where several
   photos share a page.
4. **Discard the scratch pages.** `edit-design` with `finalize: cancel`.
   Nothing needs saving: the thumbnails come from the draft.
5. **Sharp cover hero:** render the left and right halves on two 800 × 900
   pages and stitch them together (about 1066 × 600).

### Sample mode (demo reports for sharing)

Use sample mode when the user wants a demo, a sample, or a fake address:

- **Data:** real Stash data for a real suburb.
- **Address:** a fictional address. Check it with `suggest_entity`: it must return nothing.
- **Images:** photoreal AI images from Canva `generate-image`, e.g. "photorealistic two-storey <style> home in <city>, street view, daylight, no people, no text". Caption them "Images are AI-generated for illustration".
- **Labelling:** no "sample report" pill unless the user asks for one. The disclaimer says the address is fictional and the images are AI-generated.
- **AVM:** a fictional address has no Stash AVM. Weight HIGH 70% / MED 30%, and say so in the weighting note. Replace the AVM tile with a suburb figure, e.g. the 4-bed median.
- **Never** present a real neighbour's photo or address as the subject. Comparable-sale cards may use their real Stash listing photos.

---

## Data sources (all report skills)

- Use Stash MCP data wherever it exists: comps, listings, photos, suburb stats, growth, DOM, clearance, stock.
- Only where Stash has no figure, use domain.com.au or realestate.com.au (WebSearch with `allowed_domains`). Do not use or cite Cotality, CoreLogic, SQM or other data vendors. The RBA is fine for the cash rate.
- Label figures with their source and date, Stash first.

---

## Finish

Tell the user:

- the format
- the brand used, and whether it's saved as default
- the file or link
- any placeholders left for the agent

The calling skill's own summary items follow.
