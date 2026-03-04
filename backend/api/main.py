from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uvicorn
import sys
import os
import tempfile
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, Bet, init_db
from scripts.ingest_bets import ingest_csv_file
from api.staking_utils import calculate_new_stake, calculate_new_pl, calculate_stake_or_liability

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

app = FastAPI(title="BFBM Bet Explorer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FilterParams(BaseModel):
    strategies: Optional[List[str]] = []
    bet_types: Optional[List[str]] = []
    statuses: Optional[List[str]] = []
    market_types: Optional[List[str]] = []
    country_codes: Optional[List[str]] = []
    events: Optional[List[str]] = []
    min_odds: Optional[float] = None
    max_odds: Optional[float] = None
    min_stake: Optional[float] = None
    max_stake: Optional[float] = None
    min_pl: Optional[float] = None
    max_pl: Optional[float] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    selection_search: Optional[str] = None
    description_search: Optional[str] = None
    staking_type: Optional[str] = 'default'
    base_stake: Optional[float] = 10

class StakingParams(BaseModel):
    staking_type: str
    base_stake: float

class RecalculateStakingParams(FilterParams, StakingParams):
    pass

def apply_filters(query, filters: FilterParams):
    """Apply filters to a query"""
    if filters.strategies:
        query = query.filter(Bet.strategy.in_(filters.strategies))
    if filters.bet_types:
        query = query.filter(Bet.bet_type.in_(filters.bet_types))
    if filters.statuses:
        query = query.filter(Bet.status.in_(filters.statuses))
    if filters.market_types:
        query = query.filter(Bet.market_type.in_(filters.market_types))
    if filters.country_codes:
        query = query.filter(Bet.country_code.in_(filters.country_codes))
    if filters.events:
        query = query.filter(Bet.event.in_(filters.events))
    if filters.min_odds is not None:
        query = query.filter(Bet.avg_price_matched >= filters.min_odds)
    if filters.max_odds is not None:
        query = query.filter(Bet.avg_price_matched <= filters.max_odds)
    if filters.min_stake is not None:
        query = query.filter(Bet.matched_amount >= filters.min_stake)
    if filters.max_stake is not None:
        query = query.filter(Bet.matched_amount <= filters.max_stake)
    if filters.min_pl is not None:
        query = query.filter(Bet.profit_loss >= filters.min_pl)
    if filters.max_pl is not None:
        query = query.filter(Bet.profit_loss <= filters.max_pl)
    if filters.date_from:
        query = query.filter(Bet.settled_date >= datetime.fromisoformat(filters.date_from))
    if filters.date_to:
        query = query.filter(Bet.settled_date <= datetime.fromisoformat(filters.date_to))
    if filters.selection_search:
        query = query.filter(Bet.selection.ilike(f"%{filters.selection_search}%"))
    if filters.description_search:
        query = query.filter(Bet.description.ilike(f"%{filters.description_search}%"))
    
    return query

@app.get("/")
def read_root():
    return {"message": "BFBM Bet Explorer API"}

@app.get("/filter-options")
def get_filter_options(db: Session = Depends(get_db)):
    """Get all available filter options"""
    strategies = db.query(Bet.strategy).distinct().filter(Bet.strategy.isnot(None)).all()
    bet_types = db.query(Bet.bet_type).distinct().filter(Bet.bet_type.isnot(None)).all()
    statuses = db.query(Bet.status).distinct().filter(Bet.status.isnot(None)).all()
    market_types = db.query(Bet.market_type).distinct().filter(Bet.market_type.isnot(None)).all()
    country_codes = db.query(Bet.country_code).distinct().filter(Bet.country_code.isnot(None)).all()
    events = db.query(Bet.event).distinct().filter(Bet.event.isnot(None)).all()
    
    return {
        "strategies": sorted([s[0] for s in strategies if s[0]]),
        "bet_types": sorted([b[0] for b in bet_types if b[0]]),
        "statuses": sorted([s[0] for s in statuses if s[0]]),
        "market_types": sorted([m[0] for m in market_types if m[0]]),
        "country_codes": sorted([c[0] for c in country_codes if c[0]]),
        "events": sorted([e[0] for e in events if e[0]])
    }

@app.post("/strategy-stats")
def get_strategy_stats(filters: FilterParams, db: Session = Depends(get_db)):
    """Get statistics grouped by strategy"""
    # If using custom staking, recalculate per-bet
    if filters.staking_type and filters.staking_type != 'default':
        query = db.query(Bet).filter(Bet.strategy.isnot(None))
        query = apply_filters(query, filters)
        bets = query.all()
        
        # Group by strategy
        strategy_data = {}
        for bet in bets:
            if not bet.strategy or not bet.avg_price_matched or bet.profit_loss is None:
                continue
                
            if bet.strategy not in strategy_data:
                strategy_data[bet.strategy] = {
                    'bets': [],
                    'num_back': 0,
                    'num_lay': 0,
                    'num_wins': 0,
                    'num_bets_with_bsp': 0,
                    'bsp_abs_sum': 0,
                    'bsp_pct_sum': 0,
                    'bsp_prob_sum': 0,
                    'odds_sum': 0
                }
            
            strategy_data[bet.strategy]['bets'].append(bet)
            if bet.bet_type == 'BACK':
                strategy_data[bet.strategy]['num_back'] += 1
            else:
                strategy_data[bet.strategy]['num_lay'] += 1
            
            if bet.profit_loss > 0:
                strategy_data[bet.strategy]['num_wins'] += 1
            
            if bet.bsp and bet.bsp > 0:
                strategy_data[bet.strategy]['num_bets_with_bsp'] += 1
                if bet.bsp_diff_absolute:
                    strategy_data[bet.strategy]['bsp_abs_sum'] += bet.bsp_diff_absolute
                if bet.bsp_diff_percentage:
                    strategy_data[bet.strategy]['bsp_pct_sum'] += bet.bsp_diff_percentage
                if bet.bsp_diff_probability:
                    strategy_data[bet.strategy]['bsp_prob_sum'] += bet.bsp_diff_probability
            
            strategy_data[bet.strategy]['odds_sum'] += bet.avg_price_matched
        
        # Calculate stats for each strategy
        stats = []
        for strategy, data in strategy_data.items():
            total_pl = 0
            total_staked = 0
            total_stake_only = 0
            
            for bet in data['bets']:
                original_stake = bet.matched_amount if bet.matched_amount else 0
                if original_stake == 0:
                    continue
                
                new_stake = calculate_new_stake(
                    bet.bet_type,
                    original_stake,
                    bet.avg_price_matched,
                    filters.staking_type,
                    filters.base_stake
                )
                
                new_pl = calculate_new_pl(original_stake, bet.profit_loss, new_stake)
                new_stake_or_liability = calculate_stake_or_liability(
                    bet.bet_type,
                    new_stake,
                    bet.avg_price_matched
                )
                
                total_pl += new_pl
                total_staked += new_stake_or_liability
                total_stake_only += new_stake
            
            num_bets = len(data['bets'])
            roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
            yield_pct = (total_pl / total_stake_only * 100) if total_stake_only > 0 else 0
            win_rate = (data['num_wins'] / num_bets * 100) if num_bets > 0 else 0
            bsp_fill_pct = (data['num_bets_with_bsp'] / num_bets * 100) if num_bets > 0 else 0
            avg_odds = data['odds_sum'] / num_bets if num_bets > 0 else 0
            
            stats.append({
                "strategy": strategy,
                "num_bets": num_bets,
                "total_pl": round(total_pl, 2),
                "roi": round(roi, 2),
                "yield_pct": round(yield_pct, 2),
                "total_staked": round(total_staked, 2),
                "avg_odds": round(avg_odds, 2),
                "win_rate": round(win_rate, 2),
                "num_back": data['num_back'],
                "num_lay": data['num_lay'],
                "bsp_fill_pct": round(bsp_fill_pct, 1),
                "avg_bsp_abs": round(data['bsp_abs_sum'] / data['num_bets_with_bsp'], 3) if data['num_bets_with_bsp'] > 0 else 0,
                "avg_bsp_pct": round(data['bsp_pct_sum'] / data['num_bets_with_bsp'], 2) if data['num_bets_with_bsp'] > 0 else 0,
                "avg_bsp_prob": round(data['bsp_prob_sum'] / data['num_bets_with_bsp'], 2) if data['num_bets_with_bsp'] > 0 else 0
            })
        
        return sorted(stats, key=lambda x: x['total_pl'], reverse=True)
    
    # Default staking - use aggregation
    query = db.query(
        Bet.strategy,
        func.count(Bet.id).label('num_bets'),
        func.sum(Bet.profit_loss).label('total_pl'),
        func.sum(case((Bet.bet_type == 'LAY', Bet.lay_liability), else_=Bet.matched_amount)).label('total_staked'),
        func.sum(Bet.matched_amount).label('total_stake_only'),
        func.avg(Bet.avg_price_matched).label('avg_odds'),
        func.sum(case((Bet.status == 'WON', 1), else_=0)).label('num_won'),
        func.sum(case((Bet.bet_type == 'BACK', 1), else_=0)).label('num_back'),
        func.sum(case((Bet.bet_type == 'LAY', 1), else_=0)).label('num_lay'),
        func.sum(case((Bet.bsp.isnot(None), 1), else_=0)).label('num_with_bsp'),
        func.avg(Bet.bsp_diff_absolute).label('avg_bsp_abs'),
        func.avg(Bet.bsp_diff_percentage).label('avg_bsp_pct'),
        func.avg(Bet.bsp_diff_probability).label('avg_bsp_prob')
    ).filter(Bet.strategy.isnot(None))
    
    query = apply_filters(query, filters)
    query = query.group_by(Bet.strategy)
    
    results = query.all()
    
    stats = []
    for row in results:
        total_staked = float(row.total_staked or 0)
        total_stake_only = float(row.total_stake_only or 0)
        total_pl = float(row.total_pl or 0)
        num_bets = row.num_bets
        num_won = row.num_won
        num_with_bsp = row.num_with_bsp
        
        roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
        yield_pct = (total_pl / total_stake_only * 100) if total_stake_only > 0 else 0
        win_rate = (num_won / num_bets * 100) if num_bets > 0 else 0
        bsp_fill_pct = (num_with_bsp / num_bets * 100) if num_bets > 0 else 0
        
        stats.append({
            "strategy": row.strategy,
            "num_bets": num_bets,
            "total_pl": round(total_pl, 2),
            "roi": round(roi, 2),
            "yield_pct": round(yield_pct, 2),
            "total_staked": round(total_staked, 2),
            "avg_odds": round(float(row.avg_odds or 0), 2),
            "win_rate": round(win_rate, 2),
            "num_back": row.num_back,
            "num_lay": row.num_lay,
            "bsp_fill_pct": round(bsp_fill_pct, 2),
            "avg_bsp_abs": round(float(row.avg_bsp_abs or 0), 4),
            "avg_bsp_pct": round(float(row.avg_bsp_pct or 0), 4),
            "avg_bsp_prob": round(float(row.avg_bsp_prob or 0), 4)
        })
    
    return stats

@app.post("/bets")
def get_bets(filters: FilterParams, skip: int = Query(0), limit: int = Query(100), db: Session = Depends(get_db)):
    """Get filtered bets with pagination"""
    query = db.query(Bet)
    query = apply_filters(query, filters)
    query = query.order_by(Bet.settled_date.desc())
    
    total = query.count()
    bets = query.offset(skip).limit(limit).all()
    
    # If using custom staking, add recalculated values
    if filters.staking_type and filters.staking_type != 'default':
        bet_list = []
        for bet in bets:
            bet_dict = {
                "id": bet.id,
                "bet_id": bet.bet_id,
                "description": bet.description,
                "selection": bet.selection,
                "bet_type": bet.bet_type,
                "matched_amount": bet.matched_amount,
                "avg_price_matched": bet.avg_price_matched,
                "bsp": bet.bsp,
                "bsp_diff_absolute": bet.bsp_diff_absolute,
                "bsp_diff_percentage": bet.bsp_diff_percentage,
                "bsp_diff_probability": bet.bsp_diff_probability,
                "status": bet.status,
                "profit_loss": bet.profit_loss,
                "strategy": bet.strategy,
                "settled_date": bet.settled_date,
                "placed_date": bet.placed_date,
                "matched_date": bet.matched_date,
                "market_type": bet.market_type,
                "lay_liability": bet.lay_liability,
                "country_code": bet.country_code,
                "event": bet.event,
                "competition": bet.competition,
                "price_requested": bet.price_requested
            }
            
            # Calculate recalculated values
            if bet.avg_price_matched and bet.profit_loss is not None and bet.matched_amount:
                new_stake = calculate_new_stake(
                    bet.bet_type,
                    bet.matched_amount,
                    bet.avg_price_matched,
                    filters.staking_type,
                    filters.base_stake
                )
                new_pl = calculate_new_pl(bet.matched_amount, bet.profit_loss, new_stake)
                new_liability = calculate_stake_or_liability(
                    bet.bet_type,
                    new_stake,
                    bet.avg_price_matched
                )
                
                bet_dict["recalculated_stake"] = round(new_stake, 2)
                bet_dict["recalculated_pl"] = round(new_pl, 2)
                bet_dict["recalculated_liability"] = round(new_liability, 2)
            
            bet_list.append(bet_dict)
        
        return {
            "total": total,
            "bets": bet_list
        }
    
    return {
        "total": total,
        "bets": bets
    }

@app.post("/pl-over-time")
def get_pl_over_time(filters: FilterParams, db: Session = Depends(get_db)):
    """Get P/L over time data"""
    # If using custom staking, recalculate per-bet
    if filters.staking_type and filters.staking_type != 'default':
        query = db.query(Bet).filter(Bet.settled_date.isnot(None))
        query = apply_filters(query, filters)
        query = query.order_by(Bet.settled_date)
        bets = query.all()
        
        # Group by date
        daily_data = {}
        for bet in bets:
            if not bet.avg_price_matched or bet.profit_loss is None or not bet.matched_amount:
                continue
            
            date_key = str(bet.settled_date.date())
            if date_key not in daily_data:
                daily_data[date_key] = 0
            
            new_stake = calculate_new_stake(
                bet.bet_type,
                bet.matched_amount,
                bet.avg_price_matched,
                filters.staking_type,
                filters.base_stake
            )
            new_pl = calculate_new_pl(bet.matched_amount, bet.profit_loss, new_stake)
            daily_data[date_key] += new_pl
        
        # Build cumulative data
        cumulative_pl = 0
        data = []
        for date in sorted(daily_data.keys()):
            daily_pl = daily_data[date]
            cumulative_pl += daily_pl
            data.append({
                "date": date,
                "daily_pl": round(daily_pl, 2),
                "cumulative_pl": round(cumulative_pl, 2)
            })
        
        return data
    
    # Default staking - use aggregation
    query = db.query(
        func.date(Bet.settled_date).label('date'),
        func.sum(Bet.profit_loss).label('daily_pl')
    ).filter(Bet.settled_date.isnot(None))
    
    query = apply_filters(query, filters)
    query = query.group_by(func.date(Bet.settled_date)).order_by(func.date(Bet.settled_date))
    
    results = query.all()
    
    cumulative_pl = 0
    data = []
    for row in results:
        daily_pl = float(row.daily_pl or 0)
        cumulative_pl += daily_pl
        data.append({
            "date": row.date.isoformat() if row.date else None,
            "daily_pl": round(daily_pl, 2),
            "cumulative_pl": round(cumulative_pl, 2)
        })
    
    return data

@app.post("/summary-stats")
def get_summary_stats(filters: FilterParams, db: Session = Depends(get_db)):
    """Get summary statistics"""
    query = db.query(Bet)
    query = apply_filters(query, filters)
    
    total_bets = query.count()
    num_strategies = query.with_entities(func.count(func.distinct(Bet.strategy))).scalar()
    
    # If using custom staking, recalculate
    if filters.staking_type and filters.staking_type != 'default':
        bets = query.all()
        total_pl = 0
        total_staked = 0
        total_stake_only = 0
        
        for bet in bets:
            if not bet.avg_price_matched or bet.profit_loss is None or not bet.matched_amount:
                continue
            
            new_stake = calculate_new_stake(
                bet.bet_type,
                bet.matched_amount,
                bet.avg_price_matched,
                filters.staking_type,
                filters.base_stake
            )
            new_pl = calculate_new_pl(bet.matched_amount, bet.profit_loss, new_stake)
            new_stake_or_liability = calculate_stake_or_liability(
                bet.bet_type,
                new_stake,
                bet.avg_price_matched
            )
            
            total_pl += new_pl
            total_staked += new_stake_or_liability
            total_stake_only += new_stake
        
        roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
        yield_pct = (total_pl / total_stake_only * 100) if total_stake_only > 0 else 0
        
        return {
            "num_bets": total_bets,
            "total_pl": round(total_pl, 2),
            "total_staked": round(total_staked, 2),
            "roi": round(roi, 2),
            "yield_pct": round(yield_pct, 2),
            "num_strategies": num_strategies
        }
    
    # Default staking - use aggregation
    total_pl = query.with_entities(func.sum(Bet.profit_loss)).scalar()
    total_staked = query.with_entities(
        func.sum(case((Bet.bet_type == 'BACK', Bet.matched_amount), else_=Bet.lay_liability))
    ).scalar()
    total_stake_only = query.with_entities(func.sum(Bet.matched_amount)).scalar()
    
    roi = (float(total_pl) / float(total_staked) * 100) if total_staked and total_pl else 0
    yield_pct = (float(total_pl) / float(total_stake_only) * 100) if total_stake_only and total_pl else 0
    
    return {
        "num_bets": total_bets,
        "total_pl": round(float(total_pl), 2) if total_pl else 0,
        "total_staked": round(float(total_staked), 2) if total_staked else 0,
        "roi": round(roi, 2),
        "yield_pct": round(yield_pct, 2),
        "num_strategies": num_strategies
    }

@app.post("/recalculate-staking")
def recalculate_staking(filters: FilterParams, db: Session = Depends(get_db)):
    """Recalculate bets with new staking strategy"""
    query = db.query(Bet)
    query = apply_filters(query, filters)
    bets = query.all()
    
    recalculated_bets = []
    total_pl = 0
    total_staked = 0
    
    for bet in bets:
        original_stake = bet.matched_amount or 0
        avg_price = bet.avg_price_matched or 0
        
        if original_stake == 0 or avg_price == 0:
            continue
        
        new_stake = calculate_new_stake(
            bet.bet_type,
            original_stake,
            avg_price,
            filters.staking_type,
            filters.base_stake
        )
        
        new_pl = calculate_new_pl(original_stake, bet.profit_loss or 0, new_stake)
        stake_or_liability = calculate_stake_or_liability(bet.bet_type, new_stake, avg_price)
        
        total_pl += new_pl
        total_staked += stake_or_liability
        
        recalculated_bets.append({
            "bet_id": bet.bet_id,
            "original_stake": round(original_stake, 2),
            "new_stake": round(new_stake, 2),
            "original_pl": round(bet.profit_loss or 0, 2),
            "new_pl": round(new_pl, 2)
        })
    
    roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
    
    return {
        "summary": {
            "total_pl": round(total_pl, 2),
            "total_staked": round(total_staked, 2),
            "roi": round(roi, 2),
            "num_bets": len(recalculated_bets)
        },
        "sample_bets": recalculated_bets[:10]
    }

@app.post("/odds-bands-profit")
def get_odds_bands_profit(filters: FilterParams, db: Session = Depends(get_db)):
    """Get profit by odds bands"""
    query = db.query(Bet)
    query = apply_filters(query, filters)
    bets = query.all()
    
    bands = {
        "1.01-2.00": {"min": 1.01, "max": 2.00, "bets": [], "total_pl": 0, "total_staked": 0},
        "2.01-3.00": {"min": 2.01, "max": 3.00, "bets": [], "total_pl": 0, "total_staked": 0},
        "3.01-5.00": {"min": 3.01, "max": 5.00, "bets": [], "total_pl": 0, "total_staked": 0},
        "5.01-10.00": {"min": 5.01, "max": 10.00, "bets": [], "total_pl": 0, "total_staked": 0},
        "10.01+": {"min": 10.01, "max": float('inf'), "bets": [], "total_pl": 0, "total_staked": 0}
    }
    
    # If using custom staking, recalculate
    if filters.staking_type and filters.staking_type != 'default':
        for bet in bets:
            if not bet.avg_price_matched or bet.profit_loss is None or not bet.matched_amount:
                continue
            
            odds = bet.avg_price_matched
            
            new_stake = calculate_new_stake(
                bet.bet_type,
                bet.matched_amount,
                bet.avg_price_matched,
                filters.staking_type,
                filters.base_stake
            )
            new_pl = calculate_new_pl(bet.matched_amount, bet.profit_loss, new_stake)
            stake_or_liability = calculate_stake_or_liability(bet.bet_type, new_stake, bet.avg_price_matched)
            
            for band_name, band_data in bands.items():
                if band_data["min"] <= odds <= band_data["max"]:
                    band_data["bets"].append(bet)
                    band_data["total_pl"] += new_pl
                    band_data["total_staked"] += stake_or_liability
                    break
    else:
        # Default staking
        for bet in bets:
            odds = bet.avg_price_matched or 0
            pl = bet.profit_loss or 0
            stake = bet.lay_liability if bet.bet_type == 'LAY' else (bet.matched_amount or 0)
            
            for band_name, band_data in bands.items():
                if band_data["min"] <= odds <= band_data["max"]:
                    band_data["bets"].append(bet)
                    band_data["total_pl"] += pl
                    band_data["total_staked"] += stake
                    break
    
    result = []
    for band_name, band_data in bands.items():
        num_bets = len(band_data["bets"])
        total_pl = band_data["total_pl"]
        total_staked = band_data["total_staked"]
        roi = (total_pl / total_staked * 100) if total_staked > 0 else 0
        
        result.append({
            "band": band_name,
            "num_bets": num_bets,
            "total_pl": round(total_pl, 2),
            "total_staked": round(total_staked, 2),
            "roi": round(roi, 2)
        })
    
    return result

@app.post("/ingest")
async def ingest_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CSV bet export file and ingest it into the database"""
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    # Write upload to a temp file then ingest
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = ingest_csv_file(tmp_path, db)
        total_bets = db.query(Bet).count()
        return {
            "filename": file.filename,
            "inserted": result['inserted'],
            "updated": result['updated'],
            "skipped": result['skipped'],
            "total_bets_in_db": total_bets,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
