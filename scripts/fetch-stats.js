/**
 * fetch-stats.js
 * 
 * Fetches La Liga player statistics from API-Football (free tier).
 * Runs nightly via GitHub Actions and writes data/laliga-stats.json
 * 
 * FREE API: api-football.com — 100 requests/day on free plan
 * Sign up at: https://dashboard.api-football.com/register
 * Then add your key as a GitHub Secret named: FOOTBALL_API_KEY
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

const API_KEY = process.env.API_KEY;
const SEASON = new Date().getFullYear(); // auto-detect current season year
const LEAGUE_ID = 140; // La Liga

// Scoring rules — mirrors the frontend
function calculatePoints(p, pos) {
  let pts = 0;
  switch (pos) {
    case 'Goalkeeper':
      pts += (p.games.cleansheets || 0) * 4;
      pts += Math.floor((p.goals.saves || 0) / 3);
      pts += (p.penalty.saved || 0) * 5;
      pts += -Math.floor((p.goals.conceded || 0) / 2);
      break;
    case 'Defender':
      pts += (p.goals.total || 0) * 6;
      pts += (p.goals.assists || 0) * 3;
      pts += (p.games.cleansheets || 0) * 4;
      pts += (p.tackles.total || 0) * 1;
      pts += (p.tackles.interceptions || 0) * 1;
      break;
    case 'Midfielder':
      pts += (p.goals.total || 0) * 5;
      pts += (p.goals.assists || 0) * 3;
      pts += (p.games.cleansheets || 0) * 1;
      pts += (p.passes.key || 0) * 1;
      pts += (p.shots.on || 0) * 1;
      pts += (p.dribbles.past || 0) * 0.5; // bonus for dribbles
      break;
    case 'Attacker':
      pts += (p.goals.total || 0) * 4;
      pts += (p.goals.assists || 0) * 3;
      pts += (p.shots.on || 0) * 1;
      break;
  }
  pts += (p.cards.yellow || 0) * -1;
  pts += (p.cards.red || 0) * -3;
  pts += (p.penalty.missed || 0) * -2;
  return pts;
}

async function fetchPlayers() {
  if (!API_KEY) {
    console.log('No API key found — writing placeholder data');
    writePlaceholder();
    return;
  }

  const headers = {
    'x-rapidapi-host': 'api-football-v1.p.rapidapi.com',
    'x-rapidapi-key': API_KEY,
  };

  const allPlayers = [];
  let page = 1;

  try {
    while (true) {
      console.log(`Fetching page ${page}...`);
      const res = await axios.get(
        `https://api-football-v1.p.rapidapi.com/v3/players`,
        {
          headers,
          params: { league: LEAGUE_ID, season: SEASON, page },
        }
      );

      const { response, paging } = res.data;
      
      response.forEach(({ player, statistics }) => {
        const stat = statistics[0]; // primary team stats
        if (!stat) return;

        const posRaw = stat.games.position || 'Midfielder';
        const posMap = {
          'Goalkeeper': 'GK',
          'Defender': 'DEF',
          'Midfielder': 'MID',
          'Attacker': 'FWD',
        };
        const pos = posMap[posRaw] || 'MID';

        allPlayers.push({
          id: player.id,
          name: player.name,
          club: stat.team.name,
          pos,
          goals: stat.goals.total || 0,
          assists: stat.goals.assists || 0,
          cleanSheets: stat.games.cleansheets || 0,
          saves: stat.goals.saves || 0,
          penaltySaves: stat.penalty.saved || 0,
          goalsConceded: stat.goals.conceded || 0,
          yellowCards: stat.cards.yellow || 0,
          redCards: stat.cards.red || 0,
          ownGoals: 0,
          penaltiesMissed: stat.penalty.missed || 0,
          tacklesWon: stat.tackles.total || 0,
          interceptions: stat.tackles.interceptions || 0,
          keyPasses: stat.passes.key || 0,
          shotsOnTarget: stat.shots.on || 0,
          bigChancesCreated: 0,
          motm: 0,
          points: calculatePoints(stat, posRaw),
        });
      });

      if (page >= paging.total) break;
      page++;

      // Rate limit: 10 req/min on free plan
      await new Promise(r => setTimeout(r, 6500));
    }

    console.log(`Fetched ${allPlayers.length} players`);
    writeData(allPlayers);

  } catch (err) {
    console.error('API error:', err.message);
    console.log('Writing placeholder to avoid breaking site...');
    writePlaceholder();
  }
}

function writeData(players) {
  const output = {
    updatedAt: new Date().toISOString(),
    season: SEASON,
    league: 'La Liga',
    players,
  };
  fs.writeFileSync(
    path.join(__dirname, '../data/laliga-stats.json'),
    JSON.stringify(output, null, 2)
  );
  console.log('✅ data/laliga-stats.json written');
}

function writePlaceholder() {
  const output = {
    updatedAt: new Date().toISOString(),
    season: SEASON,
    league: 'La Liga',
    note: 'No API key configured. Add FOOTBALL_API_KEY to GitHub Secrets.',
    players: [],
  };
  fs.writeFileSync(
    path.join(__dirname, '../data/laliga-stats.json'),
    JSON.stringify(output, null, 2)
  );
}

fetchPlayers();
