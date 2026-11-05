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

HERE = os.path.dirname(os.path.abspath(__file__))
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
    "heading_font": None,      # optional path to a .ttf; default is the bundled Outfit
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
    head = brand.get("heading_font") or os.path.join(HERE, "fonts", "Outfit-Regular.ttf")
    headb = os.path.join(HERE, "fonts", "Outfit-Bold.ttf")
    try:
        pdfmetrics.registerFont(TTFont("Head", head))
        pdfmetrics.registerFont(TTFont("HeadBold", headb if not brand.get("heading_font") else head))
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
