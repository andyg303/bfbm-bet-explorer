# BFBM Bet Explorer - Task List

## Phase 1: Database Setup
- [x] Create database schema for PostgreSQL
- [x] Build Python ingestion script with data sanitization
- [ ] Test data import with all CSV files (requires user to set up .env)

## Phase 2: Backend API
- [x] Set up FastAPI backend structure
- [x] Create database models and ORM (SQLAlchemy)
- [x] Build API endpoints for bet queries
- [x] Implement filtering logic
- [x] Add staking calculation endpoints
- [x] Create aggregation endpoints for statistics

## Phase 3: Frontend Setup
- [x] Initialize Vue.js project with Vite
- [x] Set up TailwindCSS and component library
- [x] Create base layout and routing

## Phase 4: Core Features
- [x] Strategy selector/viewer component
- [x] Headline statistics dashboard
- [x] Filter panel with multi-select, range sliders, and text search
- [x] Bet table with pagination
- [x] Staking strategy selector and recalculation

## Phase 5: Visualizations
- [x] P/L over time chart
- [x] Cumulative P/L chart
- [ ] Additional charts (optional enhancements)

## Phase 6: Testing & Polish
- [ ] Test all filters and combinations (requires running servers)
- [ ] Performance optimization (after testing)
- [x] Responsive design (TailwindCSS responsive classes used)
- [x] Documentation (README.md created)

## Next Steps for User
1. Copy `.env.example` to `.env` and add PostgreSQL credentials
2. Install Python dependencies: `cd backend && pip install -r requirements.txt`
3. Run data ingestion: `python backend/ingest_bets.py`
4. Start backend: `python backend/main.py`
5. Start frontend: `cd frontend && npm run dev`



