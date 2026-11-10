"""Append one snapshot of live Twitch viewers for GTA VI and GTA V to data/twitch.csv.
Runs every 30 minutes on Actions (twitch.yml) and is committed to the 'data' branch, so we build
our own viewer history; Twitch's API only shows what is live right now."""
import csv, os, sys, datetime as dt
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CID, SEC = os.environ.get("TWITCH_CLIENT_ID"), os.environ.get("TWITCH_CLIENT_SECRET")
if not (CID and SEC):
    sys.exit("TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET not set")
tok = requests.post("https://id.twitch.tv/oauth2/token",
                    params={"client_id": CID, "client_secret": SEC, "grant_type": "client_credentials"}, timeout=30)
tok.raise_for_status()
H = {"Client-Id": CID, "Authorization": "Bearer " + tok.json()["access_token"]}
API = "https://api.twitch.tv/helix"
NAMES = {"gta6": "Grand Theft Auto VI", "gta5": "Grand Theft Auto V"}
r = requests.get(f"{API}/games", headers=H, params=[("name", n) for n in NAMES.values()], timeout=30)
r.raise_for_status()
ids = {g["name"]: g["id"] for g in r.json()["data"]}


def viewers(gid):
    total = streams = top = 0
    cur = None
    for _ in range(100):  # up to 10,000 streams
        p = {"game_id": gid, "first": 100, "type": "live"}
        if cur:
            p["after"] = cur
        j = requests.get(f"{API}/streams", headers=H, params=p, timeout=30).json()
        for s in j.get("data", []):
            total += s["viewer_count"]
            streams += 1
            top = max(top, s["viewer_count"])
        cur = (j.get("pagination") or {}).get("cursor")
        if not cur or not j.get("data"):
            break
    return total, streams, top


now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
row = [now]
for k, n in NAMES.items():
    row += list(viewers(ids[n])) if n in ids else ["", "", ""]
path = f"{ROOT}/data/twitch.csv"
new = not os.path.exists(path)
with open(path, "a", newline="") as f:
    w = csv.writer(f)
    if new:
        w.writerow(["utc", "gta6_viewers", "gta6_streams", "gta6_top", "gta5_viewers", "gta5_streams", "gta5_top"])
    w.writerow(row)
print(row, "ids:", ids)
