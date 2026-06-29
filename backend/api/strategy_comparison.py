from collections import defaultdict
from datetime import datetime
from typing import Any

from database import Bet, User
from api.commission import calculate_restaked_commission_map, net_profit_loss_for_bet
from api.staking_utils import calculate_stake_or_liability, deduplicate_bets


def _empty_stats(strategy: str) -> dict[str, Any]:
    return {
        "strategy": strategy,
        "num_bets": 0,
        "total_pl": 0,
        "roi": 0,
        "yield_pct": 0,
        "total_staked": 0,
        "avg_odds": 0,
        "win_rate": 0,
        "num_back": 0,
        "num_lay": 0,
        "bsp_fill_pct": 0,
        "avg_bsp_abs": 0,
        "avg_bsp_pct": 0,
        "avg_bsp_prob": 0,
    }


def _empty_monthly() -> dict[str, Any]:
    return {
        "grid": [],
        "years": [],
        "key_stats": {
            "total_profit": 0,
            "monthly_average": 0,
            "monthly_low": 0,
            "monthly_high": 0,
            "winning_months": 0,
            "months_of_data": 0,
            "winning_months_pct": 0,
            "max_absolute_drawdown": 0,
            "max_peak_trough_drawdown": 0,
        },
    }


def _monthly_response(monthly: dict[str, float], daily: dict[str, float]) -> dict[str, Any]:
    if not monthly:
        return _empty_monthly()

    years_sorted = sorted({int(k[:4]) for k in monthly})
    grid = []
    for year in years_sorted:
        row: dict[str, Any] = {"year": year}
        for month in range(1, 13):
            key = f"{year}-{month:02d}"
            row[str(month)] = round(monthly[key], 2) if key in monthly else None
        grid.append(row)

    month_values = list(monthly.values())
    total_profit = sum(month_values)
    months_of_data = len(month_values)
    monthly_average = total_profit / months_of_data if months_of_data else 0
    monthly_low = min(month_values) if month_values else 0
    monthly_high = max(month_values) if month_values else 0
    winning_months = sum(1 for value in month_values if value > 0)
    winning_months_pct = (winning_months / months_of_data * 100) if months_of_data else 0

    daily_values = [daily[key] for key in sorted(daily.keys())]
    cumulative = 0.0
    max_abs_dd = 0.0
    for value in daily_values:
        cumulative += value
        if cumulative < max_abs_dd:
            max_abs_dd = cumulative

    cumulative = 0.0
    peak = 0.0
    max_pt_dd = 0.0
    for value in daily_values:
        cumulative += value
        if cumulative > peak:
            peak = cumulative
        drawdown = cumulative - peak
        if drawdown < max_pt_dd:
            max_pt_dd = drawdown

    return {
        "grid": grid,
        "years": years_sorted,
        "key_stats": {
            "total_profit": round(total_profit, 2),
            "monthly_average": round(monthly_average, 2),
            "monthly_low": round(monthly_low, 2),
            "monthly_high": round(monthly_high, 2),
            "winning_months": winning_months,
            "months_of_data": months_of_data,
            "winning_months_pct": round(winning_months_pct, 1),
            "max_absolute_drawdown": round(max_abs_dd, 2),
            "max_peak_trough_drawdown": round(max_pt_dd, 2),
        },
    }


def _pl_over_time(daily: dict[str, float]) -> list[dict[str, Any]]:
    cumulative = 0.0
    rows = []
    for date in sorted(daily.keys()):
        daily_pl = daily[date]
        cumulative += daily_pl
        rows.append({
            "date": date,
            "daily_pl": round(daily_pl, 2),
            "cumulative_pl": round(cumulative, 2),
        })
    return rows


def _sort_key(bet: Bet):
    return bet.start_time or bet.placed_date or bet.matched_date or bet.settled_date or datetime.max


def build_strategy_comparison(
    bets: list[Bet],
    strategies: list[str],
    filters: Any,
    user: User,
) -> dict[str, Any]:
    selected = [strategy for strategy in strategies if strategy]
    selected_set = set(selected)
    use_per_bet = bool(
        (getattr(filters, "staking_type", "default") and getattr(filters, "staking_type", "default") != "default")
        or getattr(filters, "deduplicate", False)
    )

    comparison_bets = [bet for bet in bets if bet.strategy in selected_set]
    comparison_bets.sort(key=_sort_key)

    if getattr(filters, "deduplicate", False):
        comparison_bets, _, _ = deduplicate_bets(comparison_bets)

    restaked = calculate_restaked_commission_map(comparison_bets, filters, user) if use_per_bet else {}

    buckets: dict[str, dict[str, Any]] = {}
    for strategy in selected:
        buckets[strategy] = {
            "stats": _empty_stats(strategy),
            "total_reverse_risk": 0.0,
            "num_wins": 0,
            "num_bets_with_bsp": 0,
            "bsp_abs_sum": 0.0,
            "bsp_pct_sum": 0.0,
            "bsp_prob_sum": 0.0,
            "odds_sum": 0.0,
            "daily": defaultdict(float),
            "monthly": defaultdict(float),
        }

    for bet in comparison_bets:
        if not bet.strategy or bet.strategy not in buckets:
            continue

        recalc = restaked.get(bet.id) if use_per_bet else None
        if use_per_bet and not recalc:
            continue

        if recalc:
            pl = float(recalc["pl"])
            actual_risk = float(recalc["liability"])
            stake = float(recalc["stake"])
        else:
            if bet.profit_loss is None:
                continue
            pl = float(net_profit_loss_for_bet(bet) or 0)
            stake = float(bet.matched_amount or 0)
            if bet.bet_type == "LAY":
                actual_risk = float(
                    bet.lay_liability
                    if bet.lay_liability is not None
                    else calculate_stake_or_liability(bet.bet_type, stake, bet.avg_price_matched or 0)
                )
            else:
                actual_risk = stake

        odds = float(bet.avg_price_matched or 0)
        reverse_risk = (odds - 1) * stake if bet.bet_type == "BACK" else stake

        bucket = buckets[bet.strategy]
        stats = bucket["stats"]
        stats["num_bets"] += 1
        stats["total_pl"] += pl
        stats["total_staked"] += actual_risk
        stats["num_back"] += 1 if bet.bet_type == "BACK" else 0
        stats["num_lay"] += 1 if bet.bet_type == "LAY" else 0
        bucket["total_reverse_risk"] += reverse_risk
        bucket["odds_sum"] += odds
        if pl > 0:
            bucket["num_wins"] += 1

        if bet.bsp and bet.bsp > 0:
            bucket["num_bets_with_bsp"] += 1
            bucket["bsp_abs_sum"] += float(bet.bsp_diff_absolute or 0)
            bucket["bsp_pct_sum"] += float(bet.bsp_diff_percentage or 0)
            bucket["bsp_prob_sum"] += float(bet.bsp_diff_probability or 0)

        if bet.start_time:
            date_key = str(bet.start_time.date())
            month_key = bet.start_time.strftime("%Y-%m")
            bucket["daily"][date_key] += pl
            bucket["monthly"][month_key] += pl

    response = []
    for strategy in selected:
        bucket = buckets[strategy]
        stats = bucket["stats"]
        num_bets = stats["num_bets"]
        num_bets_with_bsp = bucket["num_bets_with_bsp"]
        total_pl = stats["total_pl"]
        total_staked = stats["total_staked"]
        total_reverse_risk = bucket["total_reverse_risk"]

        stats["total_pl"] = round(total_pl, 2)
        stats["total_staked"] = round(total_staked, 2)
        stats["roi"] = round((total_pl / total_staked * 100) if total_staked > 0 else 0, 2)
        stats["yield_pct"] = round((total_pl / total_reverse_risk * 100) if total_reverse_risk > 0 else 0, 2)
        stats["avg_odds"] = round((bucket["odds_sum"] / num_bets) if num_bets > 0 else 0, 2)
        stats["win_rate"] = round((bucket["num_wins"] / num_bets * 100) if num_bets > 0 else 0, 2)
        stats["bsp_fill_pct"] = round((num_bets_with_bsp / num_bets * 100) if num_bets > 0 else 0, 2)
        stats["avg_bsp_abs"] = round((bucket["bsp_abs_sum"] / num_bets_with_bsp) if num_bets_with_bsp > 0 else 0, 4)
        stats["avg_bsp_pct"] = round((bucket["bsp_pct_sum"] / num_bets_with_bsp) if num_bets_with_bsp > 0 else 0, 4)
        stats["avg_bsp_prob"] = round((bucket["bsp_prob_sum"] / num_bets_with_bsp) if num_bets_with_bsp > 0 else 0, 4)

        response.append({
            "strategy": strategy,
            "stats": stats,
            "pl_over_time": _pl_over_time(bucket["daily"]),
            "monthly_pl": _monthly_response(bucket["monthly"], bucket["daily"]),
        })

    return {"strategies": response}
