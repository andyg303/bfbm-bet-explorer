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

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+

### Database Setup

1. Create a PostgreSQL database:
```sql
CREATE DATABASE bfbm_bets;
```

2. Copy `.env.example` to `.env` and update with your database credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bfbm_bets
DB_USER=postgres
DB_PASSWORD=your_password
```

### Backend Setup

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Import CSV data:
```bash
python ingest_bets.py
```

3. Start the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. Start the backend API server
2. Start the frontend development server
3. Open your browser to `http://localhost:5173`
4. Use the filter panel to select strategies and apply filters
5. View strategy performance in the stats table
6. Analyze P/L trends in the charts
7. Use the staking calculator to simulate different staking approaches
8. Browse individual bets in the bet table

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
