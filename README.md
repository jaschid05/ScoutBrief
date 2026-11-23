# ScoutBrief

**Turn a college basketball prospect's name into a one-page scouting brief in minutes, not hours.**

> Status: in progress. The data layer is built. The interface, the brief and PDF export are next.

## The problem

I interviewed 5+ basketball scouts about how they evaluate prospects. Gathering the data was the step every one of them found most painful: pulling bios, season stats, game logs and splits from several sources took about 3 hours per player before any real evaluation started. ScoutBrief automates that step so scouts can spend their time on judgment instead of copy-pasting.

Scope: men's NCAA Division I.

## How it will work

1. Enter a prospect's name and school.
2. ScoutBrief pulls the player's data from the [cbbdata API](https://www.cbbdata.com/) (Barttorvik).
3. A one-page brief shows bio, per-game and advanced stats across seasons, recent game-log highlights, splits (home/away, opponent quality, month, result), and a short AI-written summary based only on the fetched data.
4. Export the brief as a PDF.

## Roadmap

- [x] **1. Data layer:** API client, local caching and player lookup, tested against the complete 2026 season
- [ ] **2. Normalize** raw data into a clean player profile
- [ ] **3. Streamlit UI:** search and brief layout
- [ ] **4. AI scouting summary**, based only on the fetched data, saying "data not available" instead of guessing
- [ ] **5. PDF export**

## Design decisions

- **Data access in one module.** All API calls go through `data/cbbdata_client.py`, so data sources can be swapped or added without touching the rest of the app.
- **Local caching.** Non-empty API responses are cached to disk under a key that excludes the API key, so repeat lookups are instant and don't hit the API again.
- **Forgiving player search.** Typed names are fuzzy-matched against the team roster, so small typos or capitalization differences still find the right player.
- **Plain error messages.** Missing players and failed requests show a clear message, never a stack trace.
- **Key safety.** The API key lives only in `.env`, is never printed or logged, and is removed from any URL or error message.
- **No scraping.** It uses only the official API, which respects the data provider's terms.

## Run it

Requires Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then add your cbbdata credentials (see below)

# One-time: put CBD_USER and CBD_PW in .env, then fetch and save your API key
python -m scripts.get_api_key

# Fetch and print a player's raw data
python -m scripts.fetch_player --player "<Player Name>" --team "<Team>" --year 2026
```

## Project structure

```
data/
  cbbdata_client.py   API client: season stats, game logs, splits
  cache.py            on-disk cache for raw responses
scripts/
  get_api_key.py      one-time login helper that saves the key to .env
  fetch_player.py     command-line script: look up a player and print their data
```

---

Built by Jason Christopher · [LinkedIn](https://www.linkedin.com/in/jason-chid-christopher)
