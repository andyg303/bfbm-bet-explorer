from typing import Optional

def calculate_new_stake(
    bet_type: str,
    original_stake: float,
    avg_price_matched: float,
    staking_type: str,
    base_stake: float
) -> float:
    """Calculate new stake based on staking strategy"""
    if staking_type == "default":
        return original_stake
    
    elif staking_type == "level_stake":
        return base_stake
    
    elif staking_type == "level_win":
        # For LAY bets, stake to win a level amount
        # For BACK bets, use base stake
        if bet_type == "LAY":
            return base_stake / (avg_price_matched - 1)
        else:
            return base_stake
    
    return original_stake

def calculate_new_pl(
    original_stake: float,
    original_pl: float,
    new_stake: float
) -> float:
    """Calculate new P/L based on new stake"""
    if original_stake == 0:
        return 0
    pl_ratio = original_pl / original_stake
    return new_stake * pl_ratio

def calculate_stake_or_liability(
    bet_type: str,
    new_stake: float,
    avg_price_matched: float
) -> float:
    """Calculate stake or liability for totals"""
    if bet_type == "LAY":
        return (avg_price_matched - 1) * new_stake
    else:
        return new_stake


def deduplicate_bets(bets: list) -> tuple:
    """
    Deduplicate bets so the same market position is only counted once,
    even when multiple strategies triggered the same bet.

    Dedup key (must match ALL parts to be considered the same bet):
      Primary:   (selection, market_id, start_time)
      Fallback:  (selection, description, start_time)

    start_time is included to guard against market-id reuse across
    different race meetings / fixtures.

    Returns:
        (deduped_bets, strategy_counts, strategies_map)
        - deduped_bets: list of Bet objects (one per unique market position)
        - strategy_counts: dict  bet.id → number of unique strategies
        - strategies_map:  dict  bet.id → list of strategy names
    """
    from collections import defaultdict
    from datetime import datetime as _dt

    groups = defaultdict(list)
    for bet in bets:
        selection_part = (bet.selection or '').lower().strip()

        # Time component — normalise to minute precision
        st = bet.start_time or bet.settled_date
        time_part = st.strftime('%Y-%m-%d %H:%M') if st else ''

        if bet.market_id and bet.market_id.strip():
            market_part = bet.market_id.strip()
        else:
            market_part = (bet.description or '').lower().strip()

        key = (selection_part, market_part, time_part)
        groups[key].append(bet)

    deduped = []
    strategy_counts = {}
    strategies_map = {}

    for key, group_bets in groups.items():
        # Sort by placed_date (earliest first); fall back to matched then settled
        group_bets.sort(
            key=lambda b: (
                b.placed_date or b.matched_date or b.settled_date or _dt.min
            )
        )
        first_bet = group_bets[0]
        deduped.append(first_bet)
        unique_strats = list(set(b.strategy for b in group_bets if b.strategy))
        strategy_counts[first_bet.id] = len(unique_strats) if unique_strats else 1
        strategies_map[first_bet.id] = unique_strats

    return deduped, strategy_counts, strategies_map
