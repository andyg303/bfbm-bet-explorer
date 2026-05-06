"""Commission calculation helpers for BFBM bet data."""

from collections import defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from database import Bet, User
from api.staking_utils import calculate_new_stake, calculate_new_pl, calculate_stake_or_liability


def is_aus_nz_bet(bet: Bet) -> bool:
    """Return True if this bet belongs to an AUS/NZ market."""
    if bet.country_code and bet.country_code.upper() in ('AU', 'AUS', 'NZ', 'NZL'):
        return True
    if bet.competition:
        comp_lower = bet.competition.lower()
        if 'australia' in comp_lower or 'new zealand' in comp_lower:
            return True
    for field in (bet.description, bet.event, bet.market_name):
        if field and ('(AUS)' in field or '(NZL)' in field or '(NZ)' in field):
            return True
    return False


def get_market_key(description: str | None) -> str:
    """Extract the market identifier from a bet description.

    BFBM description format: "HH:MM EventName\\MarketType\\Selection".
    The trailing selection is stripped so all bets in the same market group together.
    """
    if not description:
        return ''
    parts = description.rsplit('\\', 1)
    return parts[0].strip() if len(parts) > 1 else description.strip()


def apply_commission_for_user(db: Session, user: User) -> int:
    """Persist commission-adjusted P/L for a user's active bets.

    This is used both by the settings-page "Recalculate all bets" action and
    automatically after CSV ingestion, so imports immediately reflect the user's
    saved commission settings.
    """
    global_rate = (user.commission_rate if user.commission_rate is not None else 2.0) / 100.0
    aus_nz_rate = (user.commission_rate_aus_nz if user.commission_rate_aus_nz is not None else 5.0) / 100.0

    all_bets = (
        db.query(Bet)
        .filter(Bet.user_id == user.id, Bet.is_deleted == False)  # noqa: E712
        .all()
    )

    for bet in all_bets:
        if bet.commission_paid and bet.commission_paid != 0 and bet.profit_loss is not None:
            bet.profit_loss = round(bet.profit_loss + bet.commission_paid, 6)
        bet.commission_paid = 0.0

    active_bets = [bet for bet in all_bets if not bet.is_archived]

    groups: dict[tuple, list[Bet]] = defaultdict(list)
    for bet in active_bets:
        if bet.profit_loss is None:
            continue
        groups[(get_market_key(bet.description), bet.strategy or '')].append(bet)

    for group_bets in groups.values():
        net_pl = sum(bet.profit_loss for bet in group_bets if bet.profit_loss is not None)
        if net_pl <= 0:
            continue

        rate = aus_nz_rate if any(is_aus_nz_bet(bet) for bet in group_bets) else global_rate
        total_commission = round(net_pl * rate, 6)

        positive_bets = sorted(
            [bet for bet in group_bets if bet.profit_loss and bet.profit_loss > 0],
            key=lambda bet: (bet.placed_date or bet.start_time or datetime.min),
        )
        if not positive_bets:
            continue

        target_bet = positive_bets[0]
        target_bet.commission_paid = round(total_commission, 4)
        target_bet.profit_loss = round(target_bet.profit_loss - total_commission, 6)

    db.commit()
    return len(active_bets)


def calculate_restaked_commission_map(bets: list[Bet], filters: Any, user: User) -> dict[int, dict]:
    """Calculate custom-staking P/L with commission applied per market+strategy group.

    Stored Bet.profit_loss already includes any persisted commission deduction.
    For modelling level-stake / level-win, this restores each bet's gross P/L
    by adding back commission_paid, scales that gross P/L to the custom stake,
    then applies commission once to the positive net market result for each strategy.
    """
    global_rate = (user.commission_rate if user.commission_rate is not None else 2.0) / 100.0
    aus_nz_rate = (user.commission_rate_aus_nz if user.commission_rate_aus_nz is not None else 5.0) / 100.0

    recalculated: dict[int, dict] = {}
    groups: dict[tuple, list[Bet]] = defaultdict(list)

    for bet in bets:
        if bet.profit_loss is None or not bet.matched_amount or not bet.avg_price_matched:
            continue

        gross_pl = (bet.profit_loss or 0) + (bet.commission_paid or 0)
        new_stake = calculate_new_stake(
            bet.bet_type,
            bet.matched_amount,
            bet.avg_price_matched,
            filters.staking_type,
            filters.base_stake,
        )
        gross_recalculated_pl = calculate_new_pl(bet.matched_amount, gross_pl, new_stake)
        recalculated[bet.id] = {
            "stake": new_stake,
            "liability": calculate_stake_or_liability(bet.bet_type, new_stake, bet.avg_price_matched),
            "gross_pl": gross_recalculated_pl,
            "pl": gross_recalculated_pl,
            "commission_paid": 0.0,
        }

        groups[(get_market_key(bet.description), bet.strategy or '')].append(bet)

    for group_bets in groups.values():
        net_gross_pl = sum(recalculated[bet.id]["gross_pl"] for bet in group_bets if bet.id in recalculated)
        if net_gross_pl <= 0:
            continue

        rate = aus_nz_rate if any(is_aus_nz_bet(bet) for bet in group_bets) else global_rate
        commission = net_gross_pl * rate
        positive_bets = sorted(
            [bet for bet in group_bets if bet.id in recalculated and recalculated[bet.id]["gross_pl"] > 0],
            key=lambda bet: (bet.placed_date or bet.start_time or datetime.min),
        )
        if not positive_bets:
            continue

        target_bet = positive_bets[0]
        recalculated[target_bet.id]["commission_paid"] = commission
        recalculated[target_bet.id]["pl"] = recalculated[target_bet.id]["gross_pl"] - commission

    return recalculated
