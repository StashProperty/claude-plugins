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
