# Report build scripts

The fixed PDF layouts for report-export, kept as Markdown so the plugin ships
text only. Don't run anything from this file directly: extract the four files
with the command in SKILL.md (PDF, step 3), then run them. Don't edit the code
when building a report; put any new component in `kit.py`.

### kit.py

```python
"""Stash report layout kit: fixed-layout A4 PDF pages that match the Canva designs.

All coordinates are Canva pixels on a 794 x 1123 page, measured from the TOP-LEFT,
exactly as in the Canva designs. The kit converts to PDF points (x 0.75) and
flips the y axis. Font sizes are also Canva px.

Used by build_appraisal.py, build_briefing.py and build_campaign_review.py.
Only needs reportlab and Pillow (pip install reportlab pillow).
"""
import os, tempfile
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

S = 0.75                     # px -> pt
PW, PH = 794, 1123           # page in px
M, CW = 80, 634              # margin and content width in px

DEFAULT_BRAND = {
    "name": "Stash Property",
    "website": "stashproperty.com.au",
    "primary": "#32374A",      # headings, table headers, dark panels
    "accent": "#3555FF",       # highlight on dark panels, key figures
    "accent_dark": "#3555FF",  # accent used as text on white
    "accent_on_dark": "#9AABFF",  # accent used on PRIMARY panels (must contrast with primary)
    "tint": "#EEF1FF",         # soft bands, highlight rows
    "text": "#333333",
    "muted": "#5E6B7C",
    "on_dark_label": "#BDBDBD",
    "logo": None,              # path to a PNG (own brand only), else the name is set in type
    "heading_font": None,      # optional path to a .ttf; default is Helvetica
}


def load_brand(path=None):
    import json
    b = dict(DEFAULT_BRAND)
    if path:
        with open(path) as f:
            b.update({k: v for k, v in json.load(f).items() if v is not None})
        base = os.path.dirname(os.path.abspath(path))
        if b.get("logo") and not os.path.isabs(b["logo"]):
            b["logo"] = os.path.join(base, b["logo"])
        if "accent_on_dark" not in json.load(open(path)):
            b["accent_on_dark"] = b["accent"]
        if b.get("heading_font") and not os.path.isabs(b["heading_font"]):
            b["heading_font"] = os.path.join(base, b["heading_font"])
    return b


def _register_fonts(brand):
    head = brand.get("heading_font")
    if not head:
        return "Helvetica", "Helvetica-Bold"
    try:
        pdfmetrics.registerFont(TTFont("Head", head))
        pdfmetrics.registerFont(TTFont("HeadBold", head))
        return "Head", "HeadBold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def m(v):
    """1.234 -> $1.23m"""
    return f"${v:.2f}m"


class Report:
    def __init__(self, path, brand, title="Report", author=""):
        self.b = brand
        self.c = rl_canvas.Canvas(path, pagesize=(PW * S, PH * S))
        self.c.setTitle(title)
        self.c.setAuthor(author or brand.get("name", ""))
        self.head, self.headb = _register_fonts(brand)
        self.page_no = 0
        self._tmp = tempfile.mkdtemp()
        self._started = False

    # ------------------------------------------------------------ basics
    def col(self, key_or_hex):
        v = self.b.get(key_or_hex, key_or_hex)
        return HexColor(v)

    def new_page(self):
        if self._started:
            self.c.showPage()
        self._started = True
        self.page_no += 1

    def save(self):
        self.c.showPage()
        self.c.save()

    def rect(self, x, y, w, h, fill, r=0, stroke=None, sw=1):
        c = self.c
        c.setFillColor(self.col(fill))
        if stroke:
            c.setStrokeColor(self.col(stroke)); c.setLineWidth(sw * S)
        if r:
            c.roundRect(x * S, (PH - y - h) * S, w * S, h * S, r * S, fill=1, stroke=1 if stroke else 0)
        else:
            c.rect(x * S, (PH - y - h) * S, w * S, h * S, fill=1, stroke=1 if stroke else 0)

    def line(self, x1, y1, x2, y2, color, w=1, dash=None):
        c = self.c
        c.setStrokeColor(self.col(color)); c.setLineWidth(w * S)
        c.setDash(*(dash or []))
        c.line(x1 * S, (PH - y1) * S, x2 * S, (PH - y2) * S)
        c.setDash()

    def circle(self, cx, cy, r, fill):
        self.c.setFillColor(self.col(fill))
        self.c.circle(cx * S, (PH - cy) * S, r * S, fill=1, stroke=0)

    def _font(self, bold, italic, face):
        if face == "head":
            return self.headb if bold else self.head
        if bold and italic:
            return "Helvetica-BoldOblique"
        if bold:
            return "Helvetica-Bold"
        if italic:
            return "Helvetica-Oblique"
        return "Helvetica"

    def text(self, x, y, w, s, size=14, color="text", bold=False, italic=False, face="body",
             align="left", lh=1.4, fit=False):
        """Draw wrapped text with its box top at y. Returns the bottom y (px)."""
        c = self.c
        font = self._font(bold, italic, face)
        fs = size
        if fit:  # shrink single-line text until it fits the width
            while fs > 7 and pdfmetrics.stringWidth(s, font, fs * S) > w * S:
                fs -= 0.5
        lines = []
        for para in str(s).split("\n"):
            lines += simpleSplit(para, font, fs * S, w * S) or [""]
        lead = fs * lh
        c.setFillColor(self.col(color))
        c.setFont(font, fs * S)
        yb = y + (lead - fs) / 2 + fs * 0.82
        for ln in lines:
            px = (PH - yb) * S
            if align == "right":
                c.drawRightString((x + w) * S, px, ln)
            elif align == "center":
                c.drawCentredString((x + w / 2) * S, px, ln)
            else:
                c.drawString(x * S, px, ln)
            yb += lead
        return y + lead * len(lines)

    def bullets(self, x, y, w, items, size=13, color="text", lh=1.6, dot="accent_dark", gap=0):
        for it in items:
            self.circle(x + 4, y + size * lh / 2, 2.6, dot)
            y = self.text(x + 16, y, w - 16, it, size=size, color=color, lh=lh) + gap
        return y

    def image(self, path, x, y, w, h, r=0, label="Photo"):
        """Cover-crop an image into the box. Missing file -> neutral placeholder."""
        if not path or not os.path.exists(path):
            self.rect(x, y, w, h, "#D9DDE3", r=r)
            self.text(x, y + h / 2 - 8, w, label, size=12, color="#7A8494", align="center")
            return
        from PIL import Image
        im = Image.open(path).convert("RGB")
        tr = w / h
        iw, ih = im.size
        if iw / ih > tr:
            nw = int(ih * tr); l = (iw - nw) // 2; im = im.crop((l, 0, l + nw, ih))
        else:
            nh = int(iw / tr); t = (ih - nh) // 2; im = im.crop((0, t, iw, t + nh))
        out = os.path.join(self._tmp, f"img{abs(hash((path, w, h)))}.jpg")
        im.save(out, quality=90)
        c = self.c
        if r:
            c.saveState()
            p = c.beginPath(); p.roundRect(x * S, (PH - y - h) * S, w * S, h * S, r * S)
            c.clipPath(p, stroke=0, fill=0)
        c.drawImage(out, x * S, (PH - y - h) * S, w * S, h * S)
        if r:
            c.restoreState()

    # ------------------------------------------------------------ components
    def logo(self, x, y, w=130, h=27, color="primary"):
        lg = self.b.get("logo")
        if lg and os.path.exists(lg):
            from PIL import Image
            iw, ih = Image.open(lg).size
            hh = min(h, w * ih / iw); ww = hh * iw / ih
            self.c.drawImage(lg, x * S, (PH - y - hh) * S, ww * S, hh * S, mask="auto")
        else:
            self.text(x, y, 300, self.b.get("name", ""), size=20, color=color, bold=True, face="head", lh=1.2)

    def footer(self, label=None, band="tint", text_color="text"):
        self.rect(-21, 1043, 838, 108, band)
        self.logo(80, 1066, color="primary" if band != "primary" else "#FFFFFF")
        self.text(511, 1072, 244, label or f"Page {self.page_no}", size=17, color=text_color, align="right")

    def title(self, s, y=79, size=44):
        return self.text(M, y, CW, s, size=size, color="primary", face="head", lh=1.15)

    def eyebrow(self, s, y, x=M, w=CW, color="accent_dark"):
        return self.text(x, y, w, s.upper(), size=12, color=color, bold=True, lh=1.2)

    def table(self, y, cols, header, rows, fs=12, x0=0, highlight=(), bold_cols=(0,), colors=None,
              bar="primary", hl_color="tint"):
        """cols: list of (left_px, width_px[, align]). One row per 21.6px (12px @ 1.8).
        colors: optional dict {(row, col): color}. Returns bottom y."""
        rowh = fs * 1.8
        self.rect(M, y, CW, 26, bar)
        for (cx, cw, *al), h in zip(cols, header):
            self.text(cx + x0, y + 6, cw, h, size=11, color="#FFFFFF", bold=True, lh=1.2,
                      align=(al[0] if al else "left"))
        yy = y + 32
        for ri, row in enumerate(rows):
            if ri in highlight:
                self.rect(M, yy - 3, CW, rowh, hl_color)
            for ci, ((cx, cw, *al), val) in enumerate(zip(cols, row)):
                colr = (colors or {}).get((ri, ci)) or ("primary" if ci in bold_cols else "text")
                self.text(cx + x0, yy, cw, str(val), size=fs, color=colr,
                          bold=(ci in bold_cols or ri in highlight), lh=1.4, fit=True,
                          align=(al[0] if al else "left"))
            yy += rowh
        return yy

    def stat_row(self, y, label, value, sub, x=80, w=314):
        """Label (caps), sub text left, big value right: the 'Your home' tiles."""
        self.text(x, y, w, label.upper(), size=18, color="accent_dark", bold=True, lh=1.2)
        self.text(x, y + 44, 205, sub, size=15, color="text", lh=1.3)
        self.text(x + w - 160, y + 40, 160, value, size=22, color="primary", bold=True, align="right", lh=1.2)

    def big_figure(self, x, y, w, value, caption, vsize=30, vcolor="accent_dark", csize=13):
        self.text(x, y, w, value, size=vsize, color=vcolor, bold=True, lh=1.2, fit=True)
        return self.text(x, y + vsize * 1.35, w, caption, size=csize, color="text", lh=1.4)

    def photo_card(self, x, y, w, h, img, name, spec, status, status_color="accent_dark"):
        self.image(img, x, y, w, h)
        self.text(x, y + h + 10, w, name, size=15, color="primary", bold=True, lh=1.2, fit=True)
        self.text(x, y + h + 32, w, spec, size=12, color="text", lh=1.2, fit=True)
        self.text(x, y + h + 51, w, status, size=12, color=status_color, bold=True, lh=1.2, fit=True)

    def cover(self, hero, title, eyebrow, address, specs, stats, prepared_by, date):
        """stats: [(label, value, value_color), (label, value, value_color)]"""
        self.image(hero, -35, -26, 865, 670)
        self.rect(31, 596, 857, 601, "#FFFFFF", r=68)
        self.text(80, 627, 560, title, size=76, color="primary", face="head", lh=1.05)
        self.text(82, 832, 600, eyebrow.upper(), size=14, color="accent_dark", bold=True, lh=1.2)
        self.text(82, 858, 620, address, size=26, color="primary", bold=True, lh=1.2, fit=True)
        self.text(82, 896, 620, specs, size=16, color="text", lh=1.2, fit=True)
        self.rect(80, 940, 634, 104, "primary", r=14)
        for i, (lab, val, vc) in enumerate(stats[:2]):
            x = 104 if i == 0 else 392
            self.text(x, 956, 280, lab.upper(), size=12, bold=True,
                      color="on_dark_label" if i == 0 else "accent_on_dark", lh=1.2, fit=True)
            self.text(x, 978, 268, val, size=38, bold=True, color=vc, lh=1.2, fit=True)
        self.logo(80, 1062, w=160, h=33)
        self.text(262, 1072, 230, f"Prepared by {prepared_by}", size=17, color="text", align="right")
        self.text(511, 1072, 244, date, size=17, color="text", align="right")

    def dark_side_panel(self, heading, body, y0=0, h=803):
        self.rect(449, y0, 345, h, "primary")
        self.text(480, y0 + 80, 285, heading, size=24, color="accent_on_dark", bold=True, lh=1.2)
        return self.text(480, y0 + 170, 285, body, size=15, color="#FFFFFF", lh=1.55)

    def price_panel(self, y, eyebrow, big, sub, tiles):
        """tiles: [(label, value, color)] x3"""
        self.rect(80, y, 634, 250, "primary", r=14)
        self.text(112, y + 28, 570, eyebrow.upper(), size=13, color="accent_on_dark", bold=True, lh=1.2)
        self.text(112, y + 52, 570, big, size=56, color="#FFFFFF", bold=True, lh=1.1, fit=True)
        self.text(112, y + 128, 570, sub, size=14, color="#FFFFFF", lh=1.3)
        self.rect(112, y + 162, 570, 1, "#3A5A7E")
        for (lab, val, colr), x, w in zip(tiles, (112, 310, 540), (190, 225, 150)):
            self.text(x, y + 180, w, lab.upper(), size=11, color="on_dark_label", bold=True, lh=1.2, fit=True)
            self.text(x, y + 200, w, val, size=24, color=colr, bold=True, lh=1.2, fit=True)
        return y + 250
```

### build_appraisal.py

```python
"""Property Appraisal (seller, 6 pages, price on the last page): fixed-layout PDF.

    python build_appraisal.py data.json out.pdf [brand.json]

data.json follows examples/appraisal_example.json. Image paths are relative to data.json.
The layout matches the Canva seller appraisal page for page.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Report, load_brand, M, CW


def build(data_path, out, brand_path=None):
    d = json.load(open(data_path))
    base = os.path.dirname(os.path.abspath(data_path))
    img = lambda p: os.path.join(base, p) if p else None
    b = load_brand(brand_path)
    r = Report(out, b, title=f"Property Appraisal – {d['subject']['address']}")
    who = d.get("prepared_by", b["name"])

    # 1 cover --------------------------------------------------------------
    r.new_page()
    cs = d["cover_stats"]
    r.cover(img(d["subject"].get("hero")), "Property Appraisal",
            f"Prepared for the owners · {d['month_year']}", d["subject"]["address"], d["subject"]["specs"],
            [(cs[0]["label"], cs[0]["value"], "#FFFFFF"), (cs[1]["label"], cs[1]["value"], "accent_on_dark")],
            who, d["report_date"])

    # 2 your home ------------------------------------------------------------
    h = d["home"]
    r.new_page()
    r.rect(-21, 803, 838, 240, "tint")
    r.title("Your home", y=79)
    for i, s in enumerate(h["stats"][:4]):
        r.stat_row(210 + 108 * i, s["label"], s["value"], s["sub"])
    r.dark_side_panel(h.get("panel_heading", "What buyers will see"), "\n\n".join(h["buyers_see"]))
    r.text(80, 846, 600, h.get("history_heading", "Your home's history"), size=38, color="primary", face="head", lh=1.15)
    for i, f in enumerate(h["history"][:3]):
        x = 79 + 219 * i
        r.text(x, 927, 200, f["value"], size=30, color="primary", face="head", lh=1.2, fit=True)
        r.text(x, 967, 200, f["label"], size=17, color="text", lh=1.3)
    r.text(80, 1010, 634, h.get("source", ""), size=10, color="muted", italic=True)
    r.footer()

    # 3 your market ------------------------------------------------------------
    mk = d["market"]
    r.new_page()
    r.title("Your market")
    r.eyebrow(mk.get("competition_label", "Your competition · homes for sale nearby"), 168)
    rows = [[c["listing"], c["home"], c["asking"], c["days"], c["status"]] for c in mk["competition"][:6]]
    y = r.table(192, [(88, 168), (258, 104), (364, 112), (478, 36), (518, 196)],
                ["Listing", "Home", "Asking", "Days", "Campaign so far"], rows, bold_cols=(0, 3))
    y = r.text(M, y + 10, CW, mk["competition_takeaway"], size=13, color="primary", bold=True)
    r.eyebrow(mk.get("suburb_label", "Suburb house market · Stash Property"), y + 30)
    y = r.table(y + 52, [(88, 150), (244, 170), (420, 294)], ["Measure", "Now", "Context"], mk["suburb_rows"][:9])
    y = r.text(M, y + 32, CW, mk.get("supports_heading", "What supports value"), size=22, color="primary", lh=1.2)
    r.bullets(M, y + 12, CW, mk["supports"][:6], size=13, lh=1.6)
    r.rect(-21, 1043, 838, 108, "primary")
    r.text(80, 1062, 400, mk.get("footnote", ""), size=9, color="on_dark_label", lh=1.4)
    r.text(511, 1072, 244, f"Page {r.page_no}", size=17, color="#FFFFFF", align="right")

    # 4 recent sales ------------------------------------------------------------
    s = d["sales"]
    r.new_page()
    r.title("Recent sales near you", size=40)
    r.text(M, 140, CW, s["intro"], size=15, lh=1.45)
    r.eyebrow(s.get("label", "Comparable sales"), 208)
    for i, cd in enumerate(s["cards"][:4]):
        x, y = (80 if i % 2 == 0 else 407), (232 if i < 2 else 494)
        r.photo_card(x, y, 307, 180, img(cd.get("image")), cd["name"], cd["spec"], cd["status"])
    r.eyebrow(s.get("on_market_label", "Your closest competition"), 758)
    for i, t in enumerate(s["on_market"][:3]):
        x = 80 + 218 * i
        r.image(img(t.get("image")), x, 782, 198, 120)
        r.text(x, 910, 198, t["value"], size=24, color="accent_dark", bold=True, lh=1.2, fit=True)
        r.text(x, 944, 198, t["caption"], size=12, lh=1.2, fit=True)
    r.text(M, 985, CW, s.get("caption", ""), size=10, color="muted", italic=True)
    r.footer()

    # 5 compared with your home --------------------------------------------------
    c = d["compare"]
    r.new_page()
    r.rect(-32, 622, 861, 421, "tint")
    r.title("Compared with your home", size=40)
    r.text(M, 150, CW, c["intro"], size=14, lh=1.45)
    cols = [(88, 118), (208, 56), (266, 54), (322, 50), (374, 46), (422, 50), (474, 60), (536, 70), (612, 100)]
    colors = {(i, 8): "accent_dark" for i in range(len(c["rows"]))}
    colors.update({(i, 7): "primary" for i in range(len(c["rows"]))})
    y = r.table(222, cols, ["Sale", "Sold", "Land", "Bath", "Car", "Pool", "Floor", "Adjusted", "Rating"],
                c["rows"][:6], bold_cols=(0, 7, 8), colors=colors)
    r.text(M, y + 12, CW, c["footnote"], size=11, color="muted", italic=True)
    r.text(M, 452, CW, c.get("context_heading", "Your home in context"), size=24, color="primary", lh=1.1)
    for i, f in enumerate(c["context"][:3]):
        r.big_figure(80 + 217 * i, 496, 200, f["value"], f["caption"])
    r.text(83, 660, CW, c.get("changes_heading", "How these homes have changed in value"), size=24, color="primary", lh=1.1)
    for i, blk in enumerate(c["changes"][:4]):
        x, y = (83 if i % 2 == 0 else 415), (712 if i < 2 else 842)
        r.text(x, y, 300, blk["title"], size=16, color="primary", bold=True, lh=1.2, fit=True)
        r.text(x, y + 28, 300, blk["body"], size=14, lh=1.4)
    r.text(83, 965, CW, c.get("changes_note", ""), size=11, color="muted", italic=True)
    r.footer()

    # 6 our appraisal ------------------------------------------------------------
    p = d["price"]
    r.new_page()
    r.title("Our appraisal")
    r.text(M, 145, CW, p["intro"], size=15, lh=1.45)
    r.eyebrow("How we weight the evidence", 205)
    n = len(p["weights"])
    y = r.table(228, [(88, 330), (420, 110), (560, 150)], ["Evidence", "Value", "Weight"], p["weights"],
                bold_cols=(0, 1), highlight=(n - 1,))
    y = r.text(M, y + 14, CW, p["weights_note"], size=11, color="muted", italic=True)
    t = p["tiles"]
    y = r.price_panel(max(430, y + 30), "Our appraisal · likely selling range", p["range"], p["range_sub"],
                      [(x["label"], x["value"], "accent_on_dark" if x.get("highlight") else "#FFFFFF") for x in t])
    if p.get("why"):
        y = r.text(M, y + 34, CW, p.get("why_heading", "Why the guide sits where it does"), size=22, color="primary", lh=1.1)
        r.text(M, y + 10, CW, p["why"], size=14, lh=1.5)
    r.text(M, 975, CW, p["disclaimer"], size=10, color="muted", italic=True)
    r.footer()
    r.save()
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    print(build(a[0], a[1], a[2] if len(a) > 2 else None))
```

### build_briefing.py

```python
"""Pre-Appraisal Briefing (agent-facing, 5 pages, evidence only): fixed-layout PDF.

    python build_briefing.py data.json out.pdf [brand.json]

data.json follows examples/briefing_example.json. Image paths are relative to data.json.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Report, load_brand, M, CW


def build(data_path, out, brand_path=None):
    d = json.load(open(data_path))
    base = os.path.dirname(os.path.abspath(data_path))
    img = lambda p: os.path.join(base, p) if p else None
    b = load_brand(brand_path)
    r = Report(out, b, title=f"Pre-Appraisal Briefing – {d['subject']['address']}")
    who = d.get("prepared_by", b["name"])

    # 1 cover
    r.new_page()
    r.cover(img(d["subject"].get("hero")), "Pre-Appraisal Briefing",
            "Agent use only · evidence to take into the appraisal", d["subject"]["address"], d["subject"]["specs"],
            [("Stash AVM", d["avm"], "#FFFFFF"), ("Indicative range · subject to inspection", d["indicative_range"], "accent_on_dark")],
            who, d["report_date"])

    # 2 the property
    p = d["property"]
    r.new_page()
    r.rect(-21, 803, 838, 240, "tint")
    r.title("The property")
    for i, s in enumerate(p["stats"][:4]):
        r.stat_row(210 + 108 * i, s["label"], s["value"], s["sub"])
    r.dark_side_panel("Property profile", "\n".join(p["profile"]))
    r.text(80, 846, 600, "Sales history", size=38, color="primary", face="head", lh=1.15)
    for i, f in enumerate(p["history"][:3]):
        x = 79 + 219 * i
        r.text(x, 927, 200, f["value"], size=30, color="primary", face="head", lh=1.2, fit=True)
        r.text(x, 967, 200, f["label"], size=17, lh=1.3)
    r.text(80, 1010, 634, p.get("source", ""), size=10, color="muted", italic=True)
    r.footer()

    # 3 comparable sales (photos)
    s = d["sales"]
    r.new_page()
    r.title("Comparable sales", size=40)
    r.text(M, 140, CW, s["intro"], size=15, lh=1.45)
    r.eyebrow(s.get("label", "Recent comparable sales · within 1km"), 208)
    for i, cd in enumerate(s["cards"][:4]):
        x, y = (80 if i % 2 == 0 else 407), (232 if i < 2 else 494)
        r.photo_card(x, y, 307, 180, img(cd.get("image")), cd["name"], cd["spec"], cd["status"])
    r.eyebrow(s.get("on_market_label", "Currently on the market"), 758)
    for i, t in enumerate(s["on_market"][:3]):
        x = 80 + 218 * i
        r.image(img(t.get("image")), x, 782, 198, 120)
        r.text(x, 910, 198, t["value"], size=24, color="accent_dark", bold=True, lh=1.2, fit=True)
        r.text(x, 944, 198, t["caption"], size=12, lh=1.2, fit=True)
    r.text(M, 985, CW, s.get("caption", ""), size=10, color="muted", italic=True)
    r.footer()

    # 4 where the evidence points
    e = d["evidence"]
    r.new_page()
    r.rect(-32, 622, 861, 421, "tint")
    r.title("Where the evidence points", size=40)
    r.text(M, 150, CW, e["intro"], size=14, lh=1.45)
    cols = [(88, 118), (208, 56), (266, 54), (322, 50), (374, 46), (422, 50), (474, 60), (536, 70), (612, 100)]
    colors = {(i, 8): "accent_dark" for i in range(len(e["rows"]))}
    y = r.table(222, cols, ["Sale", "Sold", "Land", "Bath", "Car", "Pool", "Floor", "Adjusted", "Rating"],
                e["rows"][:6], bold_cols=(0, 7, 8), colors=colors)
    y += 6
    r.rect(M, y + 3 * 21.6 - 3, CW, 21.6, "tint")
    for i, (lab, val, wt) in enumerate(e["summary"]):
        yy = y + 21.6 * i
        r.text(88, yy, 300, lab, size=12, color="primary", bold=True)
        r.text(536, yy, 70, val, size=12, color="primary", bold=True)
        r.text(612, yy, 100, wt, size=12)
    y = r.text(M, y + 21.6 * len(e["summary"]) + 10, CW, e["footnote"], size=11, color="muted", italic=True)
    r.text(83, 660, CW, e.get("outliers_heading", "Nearby sales that aren't like-for-like"), size=24, color="primary", lh=1.1)
    for i, blk in enumerate(e["outliers"][:4]):
        x, yy = (83 if i % 2 == 0 else 415), (712 if i < 2 else 842)
        r.text(x, yy, 300, blk["title"], size=16, color="primary", bold=True, lh=1.2, fit=True)
        r.text(x, yy + 28, 300, blk["body"], size=14, lh=1.4)
    r.text(83, 965, CW, e.get("note", ""), size=11, color="muted", italic=True)
    r.footer()

    # 5 competition and market
    mk = d["market"]
    r.new_page()
    r.title("Competition and market")
    r.eyebrow(mk.get("competition_label", "On the market now"), 168)
    rows = [[c["listing"], c["home"], c["asking"], c["days"], c["status"]] for c in mk["competition"][:6]]
    y = r.table(192, [(88, 168), (258, 104), (364, 112), (478, 36), (518, 196)],
                ["Listing", "Home", "Asking", "Days", "Campaign so far"], rows, bold_cols=(0, 3))
    y = r.text(M, y + 10, CW, mk["competition_takeaway"], size=13, color="primary", bold=True)
    r.eyebrow(mk.get("suburb_label", "Suburb houses · Stash Property"), y + 30)
    y = r.table(y + 52, [(88, 150), (244, 170), (420, 294)], ["Measure", "Now", "Context"], mk["suburb_rows"][:9])
    y = r.text(M, y + 32, CW, "To confirm at the appraisal", size=22, color="primary", lh=1.2)
    r.bullets(M, y + 12, CW, mk["to_confirm"], size=13, lh=1.6)
    r.rect(-21, 1043, 838, 108, "primary")
    r.text(80, 1062, 400, mk.get("disclaimer", ""), size=9, color="on_dark_label", lh=1.4)
    r.text(511, 1072, 244, f"Page {r.page_no}", size=17, color="#FFFFFF", align="right")
    r.save()
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    print(build(a[0], a[1], a[2] if len(a) > 2 else None))
```

### build_campaign_review.py

```python
"""Campaign Review / Listing Update (vendor-facing, 9 pages): fixed-layout PDF with native charts.

    python build_campaign_review.py data.json out.pdf [brand.json]

data.json follows examples/campaign_review_example.json. Image paths are relative to data.json.
Prices in the data are numbers in $m (2.95 = $2.95m) wherever a chart needs them.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import Report, load_brand, M, CW, m

GREY = "#B8BCC8"


def scale(lo, hi, x0, x1):
    return lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)


def build(data_path, out, brand_path=None):
    d = json.load(open(data_path))
    base = os.path.dirname(os.path.abspath(data_path))
    img = lambda p: os.path.join(base, p) if p else None
    b = load_brand(brand_path)
    sj, rng = d["subject"], d["market_range"]
    r = Report(out, b, title=f"Campaign Review – {sj['address']}")
    who = d.get("prepared_by", b["name"])
    gap = sj["guide"] - rng["high"]

    def head(title, takeaway=None, size=40):
        r.new_page()
        y = r.title(title, size=size)
        if takeaway:
            y = r.text(M, y + 12, CW, takeaway, size=16, color="accent_dark", bold=True, lh=1.4)
        return y + 18

    # 1 cover -------------------------------------------------------------
    r.new_page()
    r.cover(img(sj.get("hero")), "Campaign Review", f"Listing update · {d['report_date']}", sj["address"], sj["specs"],
            [("Current guide", sj["guide_text"], "#FFFFFF"),
             ("Where the market is trading", f"{m(rng['low'])} – {m(rng['high'])}", "accent_on_dark")],
            who, d["report_date"])

    # 2 snapshot ------------------------------------------------------------
    y = head("Campaign snapshot", f"Day {sj['day']}: your guide sits {m(gap)} above the top of the range where comparable homes are selling.")
    facts = [["Listed", sj["listed"]], ["Days on market", f"{sj['day']} ({d['suburb_name']} median: {d['suburb_dom']})"],
             ["Method", sj["method"]], ["Current guide", sj["guide_text"]],
             ["Comparable sales range", f"{m(rng['low'])} – {m(rng['high'])} (midpoint {m(rng['mid'])})"],
             ["Gap to the market", f"+{(sj['guide'] / rng['high'] - 1) * 100:.0f}% above the top of the range; "
                                   f"+{(sj['guide'] / rng['mid'] - 1) * 100:.0f}% above the midpoint"]]
    y = r.table(y, [(88, 200), (300, 410)], ["Campaign", ""], facts, highlight=(5,))
    r.eyebrow(d.get("activity_label", "Buyer activity so far"), y + 24)
    y = r.table(y + 46, [(88, 200), (300, 410)], ["Measure", "Result"], d["activity"], bold_cols=(0, 1))
    r.rect(M, y + 20, CW, 110, "tint", r=10)
    r.text(M + 24, y + 38, CW - 48, d["bracket_note"], size=14, color="primary", lh=1.5)
    r.footer()

    # 3 market -----------------------------------------------------------------
    mk = d["market"]
    y = head("The market has shifted", mk["takeaway"])
    for i, (val, lab) in enumerate(mk["kpis"][:4]):
        x = M + i * 163
        r.rect(x, y, 145, 120, "tint", r=10)
        r.rect(x, y, 145, 5, "accent")
        r.text(x + 14, y + 20, 120, val, size=28, color="primary", bold=True, lh=1.2, fit=True)
        r.text(x + 14, y + 62, 120, lab, size=11, lh=1.35)
    y = r.table(y + 150, [(88, 150), (244, 190), (440, 274)], ["Indicator", "Now", "Context"], mk["rows"])
    r.rect(M, y + 20, CW, 10, "primary")
    r.rect(M, y + 26, CW, 190, "primary", r=0)
    yy = r.text(M + 28, y + 46, CW - 56, "What it means for your campaign", size=20, color="accent_on_dark", bold=True, lh=1.2)
    r.text(M + 28, yy + 10, CW - 56, mk["meaning"], size=14, color="#FFFFFF", lh=1.5)
    r.text(M, 1005, CW, mk["source"], size=10, color="muted", italic=True)
    r.footer()

    # 4 competition (DOM bars + table) --------------------------------------------
    co = d["competition"]
    y = head("Your competition", co["takeaway"])
    ls = sorted(co["listings"], key=lambda a: -a["days"])[:10]
    rows = ls + [{"address": "Your home", "days": sj["day"], "_subject": True}]
    rows = sorted(rows, key=lambda a: -a["days"])
    mx = max(a["days"] for a in rows) * 1.08
    sx = scale(0, mx, 260, 700)
    for i, a in enumerate(rows):
        yy = y + 8 + i * 19
        r.text(M, yy, 175, a["address"], size=11, color="primary" if a.get("_subject") else "text",
               bold=bool(a.get("_subject")), lh=1.2, fit=True, align="right")
        colr = "accent" if a.get("_subject") else ("primary" if a["days"] > 60 else GREY)
        r.rect(260, yy + 1, sx(a["days"]) - 260, 13, colr)
        r.text(sx(a["days"]) + 4, yy, 40, str(a["days"]), size=10, color="text", lh=1.2)
    yb = y + 8 + len(rows) * 19
    xm = sx(d["suburb_dom"])
    r.line(xm, y, xm, yb, "accent_dark", w=1.5, dash=[3, 2])
    r.text(xm + 4, yb + 2, 220, f"{d['suburb_name']} median {d['suburb_dom']} days", size=10, color="accent_dark", bold=True)
    tr = [[a["address"], a["bdba"], a["land"], str(a["days"]), a["history"], a["guide"]] for a in ls]
    colors = {(i, 3): ("#A82020" if a["days"] >= 60 else "primary") for i, a in enumerate(ls)}
    y = r.table(yb + 30, [(88, 160), (250, 40), (292, 44), (338, 34), (374, 230), (606, 106)],
                ["Address", "Bd/Ba", "Land", "Days", "Campaign so far", "Guide now"], tr, fs=11,
                bold_cols=(0, 3), colors=colors)
    r.text(M, y + 10, CW, co["note"], size=13, lh=1.45)
    r.footer()

    # 5 homes buyers are comparing (photos) ------------------------------------------
    cp = d["comparing"]
    y = head("Homes buyers are comparing", cp.get("intro"))
    for i, cd in enumerate(cp["cards"][:4]):
        x, yy = (80 if i % 2 == 0 else 407), (y + (0 if i < 2 else 262))
        r.photo_card(x, yy, 307, 180, img(cd.get("image")), cd["name"], cd["spec"], cd["status"])
    yy = y + 530
    r.eyebrow("Priced right from day one", yy)
    for i, t in enumerate(cp["fast"][:3]):
        x = 80 + 218 * i
        r.image(img(t.get("image")), x, yy + 24, 198, 110)
        r.text(x, yy + 142, 198, t["value"], size=28, color="accent_dark", bold=True, lh=1.2, fit=True)
        r.text(x, yy + 180, 198, t["caption"], size=12, lh=1.2, fit=True)
    r.text(M, 1005, CW, cp.get("caption", ""), size=10, color="muted", italic=True)
    r.footer()

    # 6 what recent campaigns tell us (dumbbell) --------------------------------------
    ca = d["campaigns"]
    y = head("What recent campaigns tell us", ca["takeaway"])
    sl = ca["slow"]
    vals = [v for s in sl for v in (s.get("first"), s["sold"]) if v]
    sx = scale(min(vals) * 0.95, max(vals) * 1.03, 260, 640)
    for i, s in enumerate(sl):
        yy = y + 14 + i * 30
        r.text(M, yy, 170, s["address"], size=11, color="text", lh=1.2, fit=True, align="right")
        cy = yy + 8
        if s.get("first"):
            r.line(sx(s["first"]), cy, sx(s["sold"]), cy, GREY, w=3)
            r.circle(sx(s["first"]), cy, 6, GREY)
            pct = (s["sold"] / s["first"] - 1) * 100
            r.text(max(sx(s["first"]), sx(s["sold"])) + 12, yy, 80, f"{pct:+.0f}%", size=11, color="#A82020", bold=True, lh=1.2)
        r.circle(sx(s["sold"]), cy, 6, "primary")
    yy = y + 14 + len(sl) * 30
    r.circle(270, yy + 10, 5, GREY); r.text(280, yy + 2, 140, "First advertised price", size=10)
    r.circle(430, yy + 10, 5, "primary"); r.text(440, yy + 2, 140, "Sold price", size=10)
    tr = [[s["address"], s["bdba"], s["land"], s["story"], m(s["first"]) if s.get("first") else "–",
           f"{m(s['sold'])} {s['date']}", str(s["days"])] for s in sl]
    y = r.table(yy + 30, [(88, 150), (240, 36), (278, 40), (320, 212), (534, 56), (592, 86), (680, 34)],
                ["Address", "Bd/Ba", "Land", "Campaign", "First", "Result", "Days"], tr, fs=10,
                colors={(i, 6): "#A82020" for i in range(len(sl))}, bold_cols=(0, 6))
    r.rect(M, y + 20, CW, 150, "tint", r=10)
    r.text(M + 24, y + 36, CW - 48, ca.get("fast_heading", "By contrast: homes priced to the market at launch"),
           size=16, color="primary", bold=True, lh=1.2)
    for i, f in enumerate(ca["fast"][:3]):
        x = M + 24 + i * 200
        r.text(x, y + 70, 180, f"{f['days']} days", size=30, color="accent_dark", bold=True, lh=1.2)
        r.text(x, y + 112, 180, f"{f['address']} · sold {f['sold']}", size=11, lh=1.3)
    r.text(M, y + 190, CW, ca["note"], size=13, lh=1.45)
    r.footer()

    # 7 where your price sits (ranked dot chart) --------------------------------------
    po = d["position"]
    y = head("Where your price sits", po["takeaway"])
    for i, (lab, val, colr) in enumerate([("Range bottom", m(rng["low"]), "primary"), ("Range top", m(rng["high"]), "primary"),
                                          ("Your guide", f"{m(sj['guide'])}  (+{(sj['guide'] / rng['high'] - 1) * 100:.0f}%)", "#A82020")]):
        x = M + i * 215
        r.text(x, y, 200, lab.upper(), size=11, color="muted", bold=True, lh=1.2)
        r.text(x, y + 18, 210, val, size=24, color=colr, bold=True, lh=1.2, fit=True)
    items = [(n, v, "sale") for n, v in po["adjusted"]] + [(n, v, "listing") for n, v in po["guides"]]
    items.sort(key=lambda t: -t[1])
    allv = [t[1] for t in items] + [sj["guide"], rng["low"], rng["high"]]
    sx = scale(min(allv) * 0.95, max(allv) * 1.03, 250, 700)
    y0 = y + 72
    yb = y0 + len(items) * 20
    r.rect(sx(rng["low"]), y0 - 6, sx(rng["high"]) - sx(rng["low"]), yb - y0 + 10, "tint")
    r.line(sx(sj["guide"]), y0 - 10, sx(sj["guide"]), yb + 6, "#A82020", w=2)
    r.text(sx(sj["guide"]) + 4, yb + 6, 120, "Your guide", size=10, color="#A82020", bold=True)
    for i, (n, v, kind) in enumerate(items):
        yy = y0 + i * 20
        r.text(M, yy, 160, n, size=10, lh=1.2, fit=True, align="right")
        r.line(250, yy + 7, 700, yy + 7, "#E3E6EB", w=0.6)
        r.circle(sx(v), yy + 7, 5.5, "primary" if kind == "sale" else GREY)
    yy = yb + 28
    r.circle(260, yy + 6, 5, "primary"); r.text(270, yy, 160, "Adjusted comparable sale", size=10)
    r.circle(440, yy + 6, 5, GREY); r.text(450, yy, 160, "Competing listing guide", size=10)
    y = r.text(M, yy + 24, CW, po["note"], size=11, color="muted", italic=True)
    rs = po["resale"]
    r.rect(M, y + 18, CW, 150, "tint", r=10)
    r.text(M + 24, y + 34, 240, rs["value"], size=30, color="accent_dark", bold=True, lh=1.15, fit=True)
    r.text(M + 24, y + 80, 230, rs["title"], size=13, color="primary", bold=True, lh=1.3)
    r.text(M + 280, y + 34, CW - 304, rs["body"], size=12, lh=1.45)
    r.text(M, y + 190, CW, po["growth_note"], size=13, lh=1.45)
    r.footer()

    # 8 options ------------------------------------------------------------------------
    op = d["options"]
    y = head("Options from here", op["intro"])
    for i, it in enumerate(op["items"][:3]):
        yy = y + i * 200
        r.rect(M, yy, CW, 180, "tint", r=12)
        r.rect(M, yy, 8, 180, "accent")
        r.text(M + 28, yy + 20, CW - 56, it["title"], size=20, color="primary", bold=True, lh=1.2)
        r.text(M + 28, yy + 56, 120, "WHAT IT INVOLVES", size=10, color="accent_dark", bold=True, lh=1.2)
        r.text(M + 28, yy + 74, 250, it["involves"], size=13, lh=1.45)
        r.text(M + 320, yy + 56, 120, "LIKELY OUTCOME", size=10, color="accent_dark", bold=True, lh=1.2)
        r.text(M + 320, yy + 74, CW - 340, it["outcome"], size=13, lh=1.45)
    r.footer()

    # 9 next steps ------------------------------------------------------------------------
    nx = d["next"]
    r.new_page()
    r.image(img(nx.get("image")), 0, 0, 330, 1043)
    r.text(370, 79, 344, "Next steps", size=44, color="primary", face="head", lh=1.15)
    y = r.text(370, 150, 344, nx["intro"], size=15, lh=1.5)
    r.eyebrow("This week", y + 24, x=370, w=344)
    y = r.bullets(370, y + 50, 344, nx["steps"], size=14, lh=1.5, gap=8)
    r.rect(370, y + 24, 344, 1, "#D9DDE3")
    y = r.text(370, y + 40, 344, nx["contact"], size=15, color="primary", bold=True, lh=1.4)
    r.text(370, 930, 344, nx["disclaimer"], size=10, color="muted", italic=True)
    r.footer()
    r.save()
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    print(build(a[0], a[1], a[2] if len(a) > 2 else None))
```
