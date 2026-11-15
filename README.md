# FINN — Financial Investment Agent

FINN is a mobile-first prototype for three investor workflows: a windowed portfolio signal feed (**Push**), company research (**Pull**), and synthetic network discovery (**The Network**). The reliable default is offline/demo mode. Optional Yahoo Finance access can provide market history and best-effort annual statement fields; filings, contact profiles, and the eight-module research analysis remain synthetic. Nothing here is investment advice.

## Run locally

Requirements: Python 3.11+ and Node.js 20.9+.

```bash
# Terminal 1 — backend
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The API is at [http://localhost:8000/docs](http://localhost:8000/docs); `/health` is the readiness endpoint. SQLite initializes automatically in `backend/storage/finn.db`. To deploy frontend and API on separate origins, set `NEXT_PUBLIC_API_BASE_URL` to the backend origin and configure `CORS_ORIGINS` for the frontend origin.

To opt into Yahoo Finance market history, copy `.env.example` to `.env`, set `ENABLE_LIVE_DATA=true`, then restart the backend. The portfolio and alert endpoints fetch latest daily bars; company research also attempts Yahoo annual income statement, balance sheet, and cash-flow line items when available. INR statement values use Yahoo's financial-currency metadata and display as readable ₹ crore/lakh-crore amounts; other currencies use compact formatting, and an unknown currency is explicitly labeled. Daily SMA-20/50/200, RSI-14, MACD, Bollinger bands, and ATR-14 are calculated locally from OHLCV history. Requests are cached for `YFINANCE_CACHE_TTL_SECONDS`; missing or blocked data falls back to visibly labeled demo seed data. Yahoo Finance through yfinance is unofficial and may be delayed or incomplete; it is not an authoritative exchange or audited-statement source.

## Free demo deployment

The repository includes a Render Blueprint for the FastAPI backend. To deploy:

1. Import the GitHub repository into Vercel and set the project root to `frontend`.
2. After Vercel creates the site, create a Render Blueprint from the repository root. When prompted, set `CORS_ORIGINS` to a JSON list containing the Vercel origin, for example `["https://your-app.vercel.app"]`.
3. In Vercel, set `NEXT_PUBLIC_API_BASE_URL` to the Render service origin (no trailing slash), then redeploy the frontend.
4. Confirm the backend is healthy at `<render-origin>/health`.

The demo keeps live Yahoo fetching disabled by default. Render's free service sleeps when idle and has ephemeral storage, so SQLite cache data is reset after restarts; the demo seed is loaded on startup.

API responses and live Yahoo snapshots are persisted in the local SQLite database (`backend/storage/finn.db`) and served until their TTL expires. Defaults are configurable in `.env`: Yahoo quote/history 1 hour; Yahoo annual statements 30 days; portfolio, alerts, and research responses 5 minutes; digests 15 minutes; narrative audits and network results 24 hours; Copilot responses 5 minutes. Expired entries are removed on access and refreshed from their source. The symbol catalog is a local data file refreshed separately with `python scripts/update_symbols.py`.

The Research module-status cards link directly to the relevant Yahoo statement pages when applicable and to NSE's corporate-filings search for primary-source verification. Yahoo statement data is still secondary-source data and is labeled accordingly.

Research search suggestions use the locally saved exchange-symbol catalog in `backend/data/exchange_symbols.json`. Refresh the NSE list from its public CSV with `python scripts/update_symbols.py`. To merge a BSE equity-list CSV that you are authorized to download, run `python scripts/update_symbols.py --bse-csv /path/to/bse-equities.csv`, then restart the backend. The BSE listing endpoint tested for this prototype returned HTTP 403, so the updater does not attempt to bypass its access controls; the current local catalog contains NSE listings only.

## Features

- **Push:** 24-hour/7-day digest, material/routine separation, threshold alert examples, ticker filtering, and synthetic network context.
- **Pull:** 20-stock selector and arbitrary NSE-symbol lookup; optional yfinance quote/technical data, a 1-year price chart with 1M/3M/6M/1Y ranges, available annual statement extracts, and explicit unavailable states for unsupported research modules.
- **Network:** 50 generated fictional profiles, expertise keyword matching, graph snapshot, relationship paths, and contact dossiers.
- **Ask FINN:** context-aware demo endpoint that explains limitations and can surface synthetic network matches.
- Responsive mobile-first PWA metadata, with a centered phone-width canvas on desktop.

## Verification

```bash
python3 -m pytest backend/tests -q
python3 scripts/verify_pipeline.py
cd frontend && npm run lint && npm run build
```

## Submission package

Run `python3 scripts/package_submission.py` from the project root to create `FINN_submission_2026-11-15.zip`. The packager bundles files present in the local working tree and excludes `.env`, databases, dependency directories, generated builds, and the challenge PDF. Review the generated archive before sharing.

## Data and safety notes

With live mode disabled (the reliable default), all prices, alerts, events, research metrics, and network records are synthetic demo content. With live mode enabled, only successfully retrieved Yahoo quotes, technical indicators, and statement line items are sourced from Yahoo; filings, management guidance, company analysis modules, and people remain synthetic. [NSEPython's documentation](https://unofficed.com/nse-python/documentation/) describes an unofficial wrapper and notes NSE's anti-bot restrictions, so FINN does not use it to bypass those controls. Prefer authorized feeds or official, permitted downloads for exchange filings. Do not rely on FINN's current output for investment or diligence decisions. Primary-source parsing/citations, verified transcript integration, LLM synthesis, and production authentication remain future integrations.
