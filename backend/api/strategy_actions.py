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
