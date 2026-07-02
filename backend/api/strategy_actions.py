from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from database import Bet


def delete_archived_strategy_bets(db: Session, user_id: int, strategies: list[str]) -> int:
    if not strategies:
        return 0
    return (
        db.query(Bet)
        .filter(
            Bet.user_id == user_id,
            Bet.strategy.in_(strategies),
            Bet.is_archived == True,  # noqa: E712
            Bet.is_deleted == False,  # noqa: E712
        )
        .delete(synchronize_session=False)
    )


def _clean_text(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalized_text(value: str | None) -> str | None:
    cleaned = _clean_text(value)
    return cleaned.casefold() if cleaned else None


def _description_selection(description: str | None) -> str | None:
    cleaned = _clean_text(description)
    if not cleaned:
        return None
    return _clean_text(cleaned.rsplit("\\", 1)[-1])


def _description_market(description: str | None) -> str | None:
    cleaned = _clean_text(description)
    if not cleaned:
        return None
    parts = cleaned.rsplit("\\", 1)
    if len(parts) < 2:
        return None
    return _clean_text(parts[0])


def _duplicate_key(bet: Bet) -> tuple[str, str, str] | None:
    bet_name = _normalized_text(bet.selection) or _normalized_text(_description_selection(bet.description))
    market_id = _normalized_text(bet.market_id)
    market_name = _normalized_text(bet.market_name)
    market_description = _normalized_text(_description_market(bet.description))

    if market_id:
        market = ("market_id", market_id)
    elif market_name:
        market = ("market_name", market_name)
    elif market_description:
        market = ("description", market_description)
    else:
        return None

    if not bet_name:
        return None
    return bet_name, market[0], market[1]


def _bet_name(bet: Bet) -> str | None:
    return _clean_text(bet.selection) or _description_selection(bet.description)


def _market_display(bet: Bet) -> str | None:
    return _clean_text(bet.market_name) or _clean_text(bet.market_id) or _description_market(bet.description)


def _dedupe_sort_key(bet: Bet) -> tuple[datetime, int]:
    timestamp = bet.placed_date or bet.matched_date or bet.settled_date or bet.start_time or datetime.max
    return timestamp, bet.id or 0


def _duplicate_bet_dict(bet: Bet, original_strategy_by_id: dict[int, str] | None) -> dict:
    return {
        "id": bet.id,
        "bet_id": bet.bet_id,
        "bet_name": _bet_name(bet),
        "market": _market_display(bet),
        "event": bet.event,
        "strategy": bet.strategy,
        "original_strategy": (original_strategy_by_id or {}).get(bet.id, bet.strategy),
        "selection": bet.selection,
        "description": bet.description,
        "market_id": bet.market_id,
        "market_name": bet.market_name,
        "placed_date": bet.placed_date,
        "matched_date": bet.matched_date,
        "settled_date": bet.settled_date,
        "start_time": bet.start_time,
        "avg_price_matched": bet.avg_price_matched,
        "price_requested": bet.price_requested,
        "bet_type": bet.bet_type,
        "status": bet.status,
    }


def build_strategy_duplicate_groups(
    db: Session,
    user_id: int,
    strategy: str,
    original_strategy_by_id: dict[int, str] | None = None,
) -> list[dict]:
    bets = (
        db.query(Bet)
        .filter(
            Bet.user_id == user_id,
            Bet.strategy == strategy,
            Bet.is_archived == False,  # noqa: E712
            Bet.is_deleted == False,   # noqa: E712
        )
        .all()
    )

    groups: dict[tuple[str, str, str], list[Bet]] = defaultdict(list)
    for bet in bets:
        key = _duplicate_key(bet)
        if key:
            groups[key].append(bet)

    duplicate_groups = []
    for key, group_bets in groups.items():
        if len(group_bets) < 2:
            continue
        ordered_bets = sorted(group_bets, key=_dedupe_sort_key)
        keep_bet = ordered_bets[0]
        duplicate_groups.append({
            "key": "|".join(key),
            "bet_name": _bet_name(keep_bet),
            "market": _market_display(keep_bet),
            "market_kind": key[1],
            "market_value": key[2],
            "suggested_keep_bet_id": keep_bet.id,
            "suggested_delete_bet_ids": [bet.id for bet in ordered_bets[1:]],
            "bets": [_duplicate_bet_dict(bet, original_strategy_by_id) for bet in ordered_bets],
        })

    return sorted(duplicate_groups, key=lambda group: (group["market"] or "", group["bet_name"] or ""))


def delete_selected_duplicate_strategy_bets(
    db: Session,
    user_id: int,
    strategy: str,
    bet_ids: list[int],
) -> int:
    requested_ids = set(bet_ids)
    if not requested_ids:
        return 0

    groups = build_strategy_duplicate_groups(db, user_id, strategy)
    allowed_ids: set[int] = set()
    for group in groups:
        group_ids = {bet["id"] for bet in group["bets"]}
        selected_group_ids = group_ids.intersection(requested_ids)
        if selected_group_ids and selected_group_ids == group_ids:
            raise ValueError("Cannot delete every bet in a duplicate group")
        allowed_ids.update(group_ids)

    invalid_ids = requested_ids - allowed_ids
    if invalid_ids:
        raise ValueError("Selected bets are no longer duplicate candidates")

    bets = (
        db.query(Bet)
        .filter(
            Bet.user_id == user_id,
            Bet.strategy == strategy,
            Bet.id.in_(requested_ids),
            Bet.is_archived == False,  # noqa: E712
            Bet.is_deleted == False,   # noqa: E712
        )
        .all()
    )

    deleted = 0
    for bet in bets:
        db.delete(bet)
        deleted += 1

    return deleted
