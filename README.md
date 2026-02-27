# ⚽ FANTASTICO — La Liga Fantasy League

> 90s Miami Vice vibes. Snake draft. Neon glow. Pure fantasy football.

---

## 🚀 Quick Start

1. **Fork / clone** this repo to your GitHub account
2. Push to a new repo and enable **GitHub Pages** (Settings → Pages → Deploy from `main` branch root `/`)
3. Your site is live at: `https://yourusername.github.io/your-repo-name/`

---

## 📡 Live Stats (GitHub Actions Auto-Update)

The site fetches player stats from `data/laliga-stats.json`, which is updated nightly by a GitHub Action at **1:00 AM UTC**.

### Setup (takes 5 minutes):

1. **Get a free API key** from [API-Football](https://dashboard.api-football.com/register)
   - Free plan: 100 requests/day — enough for La Liga data
   
2. **Add as GitHub Secret:**
   - Go to your repo → **Settings → Secrets and Variables → Actions**
   - Click **New repository secret**
   - Name: `FOOTBALL_API_KEY`
   - Value: your API key

3. **Enable Actions:**
   - Go to your repo → **Actions** tab
   - Click "I understand my workflows, go ahead and enable them"
   - The workflow runs automatically at 1 AM UTC daily
   - Or click **Run workflow** to trigger manually

That's it! Stats update every night. The site reads the latest data on load.

---

## 🎮 How to Play

### Setup
- Open the site — a setup screen appears
- Enter all 3 manager names and team names
- Click **INITIALISE LEAGUE**

### Draft (Snake Format)
- Go to **Draft** page
- Order: Manager 1 → 2 → 3 → 3 → 2 → 1 → repeat
- Each manager picks 15 players total:
  - 2 GK, 5 DEF, 5 MID, 3 FWD
- Click **PICK** to select a player — you cannot pick players already owned

### Weekly Lineup
Starting XI each gameweek:
- 1 GK
- 4 DEF
- 4 MID
- 2 FWD
- 1 FLEX (any non-GK)

Set your **Captain** on the My Team page — their points are doubled (×2).

### Transfers
Each gameweek you can transfer players in/out of your squad:
- Transfer 1: **-2 pts**
- Transfer 2: **-4 pts**
- Transfer 3: **-6 pts**
- etc. (resets each gameweek)

Must transfer like-for-like positions.

### Advancing Gameweeks
Admin clicks **Next Gameweek** on the Dashboard to lock results and advance.

---

## 📊 Scoring System

| Action | GK | DEF | MID | FWD |
|--------|-----|-----|-----|-----|
| Goal | — | +6 | +5 | +4 |
| Assist | — | +3 | +3 | +3 |
| Clean Sheet | +4 | +4 | +1 | — |
| Save (per 3) | +1 | — | — | — |
| Penalty Save | +5 | — | — | — |
| Goal Conceded (per 2) | -1 | — | — | — |
| Tackle Won | — | +1 | — | — |
| Interception | — | +1 | — | — |
| Key Pass | — | — | +1 | — |
| Shot on Target | — | — | +1 | +1 |
| Big Chance Created | — | — | +1 | +1 |
| MOTM | +3 | +3 | +3 | +3 |
| Yellow Card | -1 | -1 | -1 | -1 |
| Red Card | -3 | -3 | -3 | -3 |
| Own Goal | -2 | -2 | -2 | -2 |
| Penalty Missed | -2 | -2 | -2 | -2 |

---

## 📁 File Structure

```
├── index.html              # Main app (single file, all JS/CSS inline)
├── data/
│   └── laliga-stats.json   # Auto-updated player stats
├── scripts/
│   └── fetch-stats.js      # Node script run by GitHub Actions
├── .github/
│   └── workflows/
│       └── fetch-stats.yml # Nightly cron job
└── README.md
```

---

## 🎨 Design

- **Font:** Orbitron (headers/numbers) + Rajdhani (body)
- **Colors:** Deep navy `#050d1a` · Neon teal `#00f5d4` · Hot pink `#ff4ecd` · Gold `#ffd700`
- **Effects:** Grid overlay · Glassmorphism cards · Neon glow · Neon border animations

---

## 💾 Data Storage

All league data (squads, lineups, scores, transfers) is stored in **browser localStorage**. This means:
- Data persists between sessions on the same browser
- Share the site URL — each person manages their own browser storage
- **Admin** (the host) manages gameweek advancement

For multi-user sync, future upgrade: replace localStorage with a free Supabase or Firebase backend.

---

## 🔧 Customisation

Edit `index.html`:
- `SEED_PLAYERS` array — add/remove players
- `calcPlayerPoints()` function — tweak scoring weights
- CSS variables at top — change colours/fonts
