"""Turn data/raw + data/static into data/frozen/facts.json, cut off at episode.json's data_end.
Narration and graphics both read this one file, so spoken and shown numbers can't drift apart."""
import csv, json, os, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EP = json.load(open(f"{ROOT}/episode.json"))
END = EP["data_end"]
G = json.load(open(f"{ROOT}/data/static/games.json"))
bls = json.load(open(f"{ROOT}/data/raw/bls.json"))
cpi = {k: v for k, v in bls["cpi"].items() if k <= END[:7]}
wage = {k: v for k, v in bls["wage"].items() if k <= END[:7]}
cpi_m, wage_m = max(cpi), max(wage)
CPI, WAGE = cpi[cpi_m], wage[wage_m]

F = {"data_end": END, "cpi_month": cpi_m, "wage_month": wage_m, "cpi_now": CPI, "wage_now": WAGE, "games": []}
for g in G["games"]:
    m = cpi_m if g["month"] == "latest" else g["month"]
    wm = wage_m if g["month"] == "latest" else g["month"]
    c, w = cpi[m], wage[wm]
    F["games"].append({**g, "cpi_month_used": m, "cpi": c, "wage": w,
                       "adj": round(g["price"] * CPI / c, 2),
                       "hours": round(g["price"] / w, 2),
                       "combo": round(g["price"] + g["console_price"], 2),
                       "combo_adj": round((g["price"] + g["console_price"]) * CPI / c, 2)})
gs = F["games"]
six = gs[-1]
old = gs[:-1]
F["cheaper_than_all"] = all(x["adj"] > six["adj"] for x in old)
F["closest"] = min(old, key=lambda x: x["adj"])["id"]
F["priciest"] = max(old, key=lambda x: x["adj"])["id"]
F["combo_record"] = all(x["combo_adj"] < six["combo_adj"] for x in old)
rank = sorted(gs, key=lambda x: -x["combo_adj"])
F["combo_rank"] = [x["id"] for x in rank]
F["combo_top"] = rank[0]["id"]
F["gta6_combo_place"] = F["combo_rank"].index("gta6") + 1
F["ultimate"] = G["gta6_ultimate"]
F["ultimate_beats"] = [x["id"] for x in old if x["adj"] < G["gta6_ultimate"]]
F["hours_fewest"] = min(gs, key=lambda x: x["hours"])["id"]

# Wikipedia attention
rows = [(d, int(v)) for d, v in list(csv.reader(open(f"{ROOT}/data/raw/wiki.csv")))[1:] if d <= END]
F["wiki_total"] = sum(v for _, v in rows)
F["wiki_last"] = rows[-1]
last7 = rows[-7:]
F["wiki_last7_avg"] = round(sum(v for _, v in last7) / len(last7))
ser = [(d, v) for d, v in rows if d >= "2023-11-01"]
F["wiki_series"] = ser
F["wiki_median"] = sorted(v for _, v in ser)[len(ser) // 2]
# biggest spikes, at least 45 days apart, labelled from the event list when one is within 2 days
spikes = []
for d, v in sorted(ser, key=lambda r: -r[1]):
    if all(abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(s["day"])).days) > 45 for s in spikes):
        lab = next((e["label"] for e in G["events"]
                    if abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(e["date"])).days) <= 2), None)
        spikes.append({"day": d, "views": v, "label": lab})
    if len(spikes) == 4:
        break
F["wiki_spikes"] = spikes
F["wiki_peak"] = spikes[0]

if os.path.exists(f"{ROOT}/data/raw/ttwo.csv"):
    t = [(d, float(c)) for d, c in list(csv.reader(open(f"{ROOT}/data/raw/ttwo.csv")))[1:] if d <= END]
    if t:
        base = next(c for d, c in t if d >= "2023-12-01")
        F["ttwo_last"] = t[-1]
        F["ttwo_since_trailer1"] = round((t[-1][1] / base - 1) * 100, 1)

os.makedirs(f"{ROOT}/data/frozen", exist_ok=True)
json.dump(F, open(f"{ROOT}/data/frozen/facts.json", "w"), indent=1)
summary = {k: v for k, v in F.items() if k != "wiki_series"}
summary["games"] = [(x["name"], x["price"], x["adj"], x["hours"], x["combo_adj"]) for x in gs]
print(json.dumps(summary, indent=1))
