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
