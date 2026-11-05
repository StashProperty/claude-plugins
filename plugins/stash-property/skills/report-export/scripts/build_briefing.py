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
