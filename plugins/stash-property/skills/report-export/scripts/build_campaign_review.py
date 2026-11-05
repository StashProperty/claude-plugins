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
