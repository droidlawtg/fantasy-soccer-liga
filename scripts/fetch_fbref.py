"""
fetch_fbref.py
--------------
Scrapes La Liga player statistics from FBref.com — completely free, no API key needed.
Runs nightly via GitHub Actions and writes data/laliga-stats.json

FBref is run by Sports Reference and has the most complete football stats available.
We scrape 3 tables:
  - Standard stats (goals, assists, cards)
  - Goalkeeping stats (saves, clean sheets, goals conceded)
  - Defensive stats (tackles, interceptions, blocks)
  - Passing stats (key passes, progressive passes)
"""

import requests
import pandas as pd
import json
import os
import time
from datetime import datetime
from io import StringIO

# ── FBref La Liga table URLs ──────────────────────────────────────────────────
# These URLs point to the current season La Liga stats tables.
# FBref updates these automatically as the season progresses.

BASE = "https://fbref.com"

URLS = {
    "standard":   "https://fbref.com/en/comps/12/stats/La-Liga-Stats",
    "goalkeeping":"https://fbref.com/en/comps/12/keepers/La-Liga-Stats",
    "defensive":  "https://fbref.com/en/comps/12/defense/La-Liga-Stats",
    "passing":    "https://fbref.com/en/comps/12/passing/La-Liga-Stats",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Position mapping ──────────────────────────────────────────────────────────
POS_MAP = {
    "GK": "GK",
    "DF": "DEF", "DF,MF": "DEF", "DF,FW": "DEF",
    "MF": "MID", "MF,DF": "MID", "MF,FW": "MID",
    "FW": "FWD", "FW,MF": "FWD", "FW,DF": "FWD",
}

def safe_int(val):
    try:
        if val is None or val == "" or str(val).strip() in ("", "nan", "NaN"):
            return 0
        return int(float(str(val).strip()))
    except:
        return 0

def fetch_table(url, table_id=None):
    """Fetch an FBref stats table and return as DataFrame."""
    print(f"  Fetching: {url}")
    time.sleep(4)  # be polite to FBref — don't hammer them
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        
        # FBref wraps some tables in comments — pandas handles them
        tables = pd.read_html(StringIO(resp.text), header=1)
        
        if not tables:
            print(f"  ⚠ No tables found at {url}")
            return None
        
        # Take the biggest table (usually the player stats one)
        df = max(tables, key=lambda t: len(t))
        
        # Drop duplicate header rows FBref sometimes inserts
        df = df[df.iloc[:, 0] != df.columns[0]]
        
        # Drop rows where player name is NaN or "Player"
        if "Player" in df.columns:
            df = df[df["Player"].notna()]
            df = df[df["Player"] != "Player"]
        
        print(f"  ✓ Got {len(df)} rows")
        return df
    
    except Exception as e:
        print(f"  ✗ Error fetching {url}: {e}")
        return None


def normalise_name(name):
    """Strip accents and normalise for matching across tables."""
    import unicodedata
    if not isinstance(name, str):
        return ""
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").strip().lower()


def calculate_points(p):
    """Mirror the scoring system from index.html"""
    pts = 0
    pos = p.get("pos", "MID")

    if pos == "GK":
        pts += p.get("cleanSheets", 0) * 4
        pts += p.get("saves", 0) // 3
        pts += p.get("penaltySaves", 0) * 5
        pts -= p.get("goalsConceded", 0) // 2
    elif pos == "DEF":
        pts += p.get("goals", 0) * 6
        pts += p.get("assists", 0) * 3
        pts += p.get("cleanSheets", 0) * 4
        pts += p.get("tacklesWon", 0) * 1
        pts += p.get("interceptions", 0) * 1
    elif pos == "MID":
        pts += p.get("goals", 0) * 5
        pts += p.get("assists", 0) * 3
        pts += p.get("cleanSheets", 0) * 1
        pts += p.get("keyPasses", 0) * 1
        pts += p.get("shotsOnTarget", 0) * 1
        pts += p.get("bigChancesCreated", 0) * 1
    elif pos == "FWD":
        pts += p.get("goals", 0) * 4
        pts += p.get("assists", 0) * 3
        pts += p.get("shotsOnTarget", 0) * 1
        pts += p.get("bigChancesCreated", 0) * 1

    pts += p.get("yellowCards", 0) * -1
    pts += p.get("redCards", 0) * -3
    pts += p.get("ownGoals", 0) * -2
    pts += p.get("penaltiesMissed", 0) * -2

    return pts


def main():
    print("🔄 Fetching La Liga stats from FBref...")

    # ── 1. Standard stats ─────────────────────────────────────────────────────
    std = fetch_table(URLS["standard"])
    if std is None:
        print("✗ Failed to fetch standard stats — aborting")
        exit(1)

    players = {}

    for _, row in std.iterrows():
        name = str(row.get("Player", "")).strip()
        if not name or name == "Player":
            continue

        pos_raw = str(row.get("Pos", "MF")).split(",")[0].strip().upper()
        pos = POS_MAP.get(pos_raw, "MID")

        # Some FBref columns have multi-level headers flattened weirdly
        # Try multiple column name variants
        def get(keys, default=0):
            for k in keys if isinstance(keys, list) else [keys]:
                if k in row.index:
                    return safe_int(row[k])
            return default

        key = normalise_name(name)
        players[key] = {
            "id": abs(hash(name)) % 100000,
            "name": name,
            "club": str(row.get("Squad", "Unknown")).strip(),
            "pos": pos,
            "goals": get(["Gls", "Goals"]),
            "assists": get(["Ast", "Assists"]),
            "yellowCards": get(["CrdY"]),
            "redCards": get(["CrdR"]),
            "ownGoals": get(["OG"]),
            "penaltiesMissed": get(["PKmiss", "PKM"]),
            "shotsOnTarget": get(["SoT"]),
            "cleanSheets": 0,
            "saves": 0,
            "penaltySaves": 0,
            "goalsConceded": 0,
            "tacklesWon": 0,
            "interceptions": 0,
            "keyPasses": 0,
            "bigChancesCreated": 0,
            "motm": 0,
        }

    print(f"✓ Standard stats: {len(players)} players")

    # ── 2. Goalkeeping stats ──────────────────────────────────────────────────
    gk = fetch_table(URLS["goalkeeping"])
    if gk is not None:
        for _, row in gk.iterrows():
            name = str(row.get("Player", "")).strip()
            if not name or name == "Player":
                continue
            key = normalise_name(name)
            if key in players:
                players[key]["cleanSheets"] = safe_int(row.get("CS", 0))
                players[key]["saves"] = safe_int(row.get("Saves", 0))
                players[key]["penaltySaves"] = safe_int(row.get("PKsv", 0))
                players[key]["goalsConceded"] = safe_int(row.get("GA", 0))
        print(f"✓ GK stats merged")

    # ── 3. Defensive stats ────────────────────────────────────────────────────
    defn = fetch_table(URLS["defensive"])
    if defn is not None:
        for _, row in defn.iterrows():
            name = str(row.get("Player", "")).strip()
            if not name or name == "Player":
                continue
            key = normalise_name(name)
            if key in players:
                # TklW = tackles won; Int = interceptions
                players[key]["tacklesWon"] = safe_int(row.get("TklW", 0))
                players[key]["interceptions"] = safe_int(row.get("Int", 0))
        print(f"✓ Defensive stats merged")

    # ── 4. Passing stats ──────────────────────────────────────────────────────
    passing = fetch_table(URLS["passing"])
    if passing is not None:
        for _, row in passing.iterrows():
            name = str(row.get("Player", "")).strip()
            if not name or name == "Player":
                continue
            key = normalise_name(name)
            if key in players:
                # KP = key passes; xAG or PPA as proxy for big chances created
                players[key]["keyPasses"] = safe_int(row.get("KP", 0))
                players[key]["bigChancesCreated"] = safe_int(row.get("PPA", 0))
        print(f"✓ Passing stats merged")

    # ── 5. Calculate fantasy points ───────────────────────────────────────────
    player_list = list(players.values())
    for p in player_list:
        p["points"] = calculate_points(p)

    # Sort by points descending
    player_list.sort(key=lambda x: x["points"], reverse=True)

    print(f"\n✅ Total players: {len(player_list)}")
    print(f"   Top 5 by points:")
    for p in player_list[:5]:
        print(f"   {p['name']} ({p['club']}, {p['pos']}) — {p['points']} pts")

    # ── 6. Write output ───────────────────────────────────────────────────────
    output = {
        "updatedAt": datetime.utcnow().isoformat() + "Z",
        "season": "2024-25",
        "league": "La Liga",
        "source": "FBref.com",
        "players": player_list,
    }

    out_path = os.path.join(os.path.dirname(__file__), "../data/laliga-stats.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Written to data/laliga-stats.json")


if __name__ == "__main__":
    main()
