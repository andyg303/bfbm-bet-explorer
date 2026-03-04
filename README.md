# BFBM Bet Explorer

A comprehensive betting strategy analysis tool with PostgreSQL database, FastAPI backend, and Vue.js frontend.

## Features

- **Data Ingestion**: Import CSV bet data with automatic sanitization
- **Strategy Analysis**: View performance metrics for each betting strategy
- **Advanced Filtering**: Multi-select filters for strategies, bet types, markets, countries, and more
- **Staking Calculator**: Recalculate P/L with different staking strategies:
  - Level Stake
  - Level Win (Back bets)
  - Level Win (Lay bets)
  - Level Liability (Lay bets)
- **Visualizations**: Interactive charts showing P/L over time
- **Detailed Bet View**: Paginated table with all bet details

## Setup

### Option 1 — Docker (recommended)

The easiest way to run everything. Only requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

**1. Configure environment**

```bash
cp .env.example .env
```

The defaults in `.env` work out of the box with Docker. Edit only if you want to change the database password.

**2. Start all services**

```bash
docker compose up --build
```

This starts three containers — PostgreSQL, FastAPI backend, and the Vue frontend served by nginx — in the correct dependency order with health checks.

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3080 |
| Backend API | http://localhost:8000 |

**3. Import your CSV data** (first run only)

Place your Betfair/BetMaker CSV export files in the `data/` folder in the project root — they are automatically mounted into the Docker container.

**Option A — Upload via the UI (easiest):**  
Open http://localhost:3080, click **"Ingest Bet Data"** in the top-right corner, select your CSV file, and click **Ingest**. The database updates immediately and the dashboard refreshes automatically.

**Option B — Bulk import via CLI** (for ingesting all files in `data/` at once):

```bash
docker compose exec backend python scripts/ingest_bets.py
```

> Duplicate bets are detected by Bet ID and updated rather than re-inserted, so it's safe to re-run with the same file.

**Subsequent starts** (images already built):

```bash
docker compose up
```

**Stop everything:**

```bash
docker compose down
```

**Stop and wipe the database volume:**

```bash
docker compose down -v
```

---

### Option 2 — Local development

Requires Python 3.8+, Node.js 16+, and a local PostgreSQL 12+ instance.

**1. Configure environment**

```bash
cp .env.example .env
```

Edit `.env` with your local Postgres credentials:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bfbm_bets
DB_USER=<your_postgres_user>
DB_PASSWORD=<your_postgres_password>
```

**2. Create the database**

```bash
cd backend
python scripts/create_database.py
```

**3. Install dependencies & import data**

Place your CSV files in the `data/` folder in the project root, then:

```bash
# Backend
cd backend
pip install -r requirements.txt
python scripts/ingest_bets.py

# Frontend
cd frontend
npm install
```

**4. Start both servers**

```bash
# From the repo root — starts backend + frontend in parallel
./start.sh
```

Or manually:

```bash
# Backend (http://localhost:8000)
cd backend && python api/main.py

# Frontend (http://localhost:5173)
cd frontend && npm run dev
```

## Usage

1. Open your browser to http://localhost:3080 (Docker) or http://localhost:5173 (local dev)
2. Use the filter panel to select strategies and apply filters
3. View strategy performance in the stats table
4. Analyze P/L trends in the charts
5. Use the staking calculator to simulate different staking approaches
6. Browse individual bets in the bet table

## Data Structure

The application handles bet data with the following key fields:

- **Bet Type**: BACK or LAY
- **Stake**: For BACK bets, this is the amount wagered. For LAY bets, this is the amount won if the selection loses
- **Lay Liability**: Calculated as (odds - 1) × stake for LAY bets
- **P/L**: Profit or loss for each bet
- **Strategy**: The betting strategy used
- **Market Type**: WIN, MATCH_ODDS, PLACE, etc.

## API Endpoints

- `GET /filter-options` - Get all available filter values
- `POST /strategy-stats` - Get aggregated statistics by strategy
- `POST /bets` - Get paginated bet list with filters
- `POST /pl-over-time` - Get P/L time series data
- `POST /recalculate-staking` - Recalculate P/L with different staking
- `GET /summary-stats` - Get overall summary statistics

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Vue.js 3, TypeScript, Pinia, TailwindCSS
- **Charts**: Chart.js, vue-chartjs
- **Data Processing**: Pandas
