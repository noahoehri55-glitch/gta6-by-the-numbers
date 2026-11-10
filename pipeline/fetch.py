"""Pull the raw public data into data/raw/. Runs on GitHub Actions (the dev sandbox can't reach these hosts).
Sources: BLS (CPI-U, average hourly earnings), Wikimedia pageviews, Stooq (TTWO share price, optional)."""
import csv, io, json, os, sys, datetime as dt
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = f"{ROOT}/data/raw"
os.makedirs(RAW, exist_ok=True)
UA = {"User-Agent": "gta6-by-the-numbers/1.0 (data channel; github.com/noahoehri55-glitch)"}
today = dt.date.today()


def bls():
    """CPI-U NSA + avg hourly earnings (production & nonsupervisory). v1 API: no key, 10 years per call."""
    series = {"CUUR0000SA0": "cpi", "CES0500000008": "wage"}
    out = {v: {} for v in series.values()}
    for start in range(1997, today.year + 1, 10):
        body = {"seriesid": list(series), "startyear": str(start), "endyear": str(min(start + 9, today.year))}
        r = requests.post("https://api.bls.gov/publicAPI/v1/timeseries/data/", json=body, headers=UA, timeout=60)
        r.raise_for_status()
        j = r.json()
        if j.get("status") != "REQUEST_SUCCEEDED":
            sys.exit(f"BLS error: {j.get('message')}")
        for s in j["Results"]["series"]:
            for p in s["data"]:
                if p["period"].startswith("M") and p["period"] != "M13" and p["value"] not in ("-", ""):
                    out[series[s["seriesID"]]][f"{p['year']}-{p['period'][1:]}"] = float(p["value"])
    json.dump({k: dict(sorted(v.items())) for k, v in out.items()}, open(f"{RAW}/bls.json", "w"), indent=0)
    print("bls", {k: (min(v), max(v), len(v)) for k, v in out.items()})


def wiki():
    end = (today - dt.timedelta(days=1)).strftime("%Y%m%d")
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
           f"Grand_Theft_Auto_VI/daily/20220201/{end}")
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    rows = [(i["timestamp"][:4] + "-" + i["timestamp"][4:6] + "-" + i["timestamp"][6:8], i["views"]) for i in r.json()["items"]]
    with open(f"{RAW}/wiki.csv", "w") as f:
        csv.writer(f).writerows([("day", "views")] + rows)
    print("wiki", rows[0], rows[-1], len(rows))


def ttwo():
    try:
        r = requests.get("https://stooq.com/q/d/l/?s=ttwo.us&i=d", headers=UA, timeout=60)
        r.raise_for_status()
        rows = list(csv.DictReader(io.StringIO(r.text)))
        assert rows and "Close" in rows[0], r.text[:200]
        with open(f"{RAW}/ttwo.csv", "w") as f:
            csv.writer(f).writerows([("day", "close")] + [(x["Date"], x["Close"]) for x in rows if x["Date"] >= "2022-01-01"])
        print("ttwo", rows[-1])
    except Exception as e:  # optional source
        print("ttwo skipped:", e)


if __name__ == "__main__":
    bls()
    wiki()
    ttwo()
