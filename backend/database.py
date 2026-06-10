from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Index, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv
from datetime import datetime, timezone
from urllib.parse import quote_plus
import os

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD', ''))}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # test connections before use, auto-reconnect stale ones
    pool_recycle=300,          # recycle connections every 5 minutes
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    password_reset_token = Column(String, nullable=True, index=True)
    password_reset_token_id = Column(String, nullable=True, index=True)  # plaintext prefix for O(1) lookup
    password_reset_expires = Column(DateTime, nullable=True)
    token_version = Column(Integer, default=0, nullable=False)  # increment to invalidate all JWTs
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)

    # Commission settings
    commission_rate = Column(Float, default=2.0, nullable=False, server_default='2.0')
    commission_rate_aus_nz = Column(Float, default=5.0, nullable=False, server_default='5.0')

    # Subscription / Stripe
    subscription_status = Column(String, default="inactive", nullable=False)  # inactive | active | cancelled | expired
    subscription_plan = Column(String, nullable=True)  # 6month | 12month
    subscription_start = Column(DateTime, nullable=True)
    subscription_expires = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String, nullable=True, unique=True, index=True)
    stripe_checkout_session_id = Column(String, nullable=True)

    # Referrals
    referral_code = Column(String, nullable=True, unique=True, index=True)
    referred_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    referral_rewarded_at = Column(DateTime, nullable=True)
    referral_credit_balance = Column(Integer, default=0, nullable=False, server_default='0')
    referral_credits_awarded = Column(Integer, default=0, nullable=False, server_default='0')
    referral_credits_redeemed = Column(Integer, default=0, nullable=False, server_default='0')
    referral_pending_checkout_session_id = Column(String, nullable=True)
    referral_last_redeemed_session_id = Column(String, nullable=True)

    bets = relationship("Bet", back_populates="owner", lazy="dynamic")
    automation_tokens = relationship("AutomationToken", back_populates="user", lazy="dynamic")


class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    bet_id = Column(String, index=True)  # unique per user, not globally
    event = Column(String, index=True)
    country_code = Column(String, index=True)
    competition = Column(String, index=True)
    favorite_position = Column(Integer)
    description = Column(String)
    selection = Column(String, index=True)
    bet_type = Column(String, index=True)
    matched_amount = Column(Float)
    loss_rec_amount = Column(Float)
    avg_price_matched = Column(Float)
    price_requested = Column(Float)
    status = Column(String, index=True)
    profit_loss = Column(Float, index=True)
    strategy = Column(String, index=True)
    strategy_id = Column(String, nullable=True, index=True)
    bsp = Column(Float)
    total_matched_on_runner = Column(Float)
    total_matched_on_market = Column(Float)
    short_description = Column(String)
    tipster = Column(String)
    placed_date = Column(DateTime, index=True)
    matched_date = Column(DateTime, index=True)
    settled_date = Column(DateTime, index=True)
    number_of_selections = Column(Integer)
    market_type = Column(String, index=True)
    market_name = Column(String)         # e.g. "Over/Under 1.5 Goals" (bet_data export)
    market_id = Column(String)           # Betfair market ID (bet_data export)
    start_time = Column(DateTime)        # Event start time (bet_data export)
    lay_liability = Column(Float)
    bsp_diff_absolute = Column(Float)
    bsp_diff_percentage = Column(Float)
    bsp_diff_probability = Column(Float)
    commission_paid = Column(Float, default=0.0, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False, index=True)

    owner = relationship("User", back_populates="bets")

    __table_args__ = (
        Index('idx_strategy_date', 'strategy', 'settled_date'),
        Index('idx_bet_type_status', 'bet_type', 'status'),
        Index('idx_user_bet_id', 'user_id', 'bet_id', unique=True),
        Index('idx_user_strategy', 'user_id', 'strategy'),
        # Partial composite indexes targeting the hot dashboard query pattern
        # (user_id = ? AND is_deleted = false AND is_archived = false).
        # Created in production by scripts/add_performance_indexes.py — listed
        # here so fresh installs via init_db() pick them up too.
        Index(
            'idx_bets_user_active', 'user_id',
            postgresql_where=text('is_deleted = false AND is_archived = false'),
        ),
        Index(
            'idx_bets_user_starttime', 'user_id', 'start_time',
            postgresql_where=text('is_deleted = false AND is_archived = false'),
        ),
    )


class IngestionLog(Base):
    """Tracks every CSV upload — successes, warnings, and errors."""
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)  # success | partial | error
    rows_total = Column(Integer, default=0)
    rows_inserted = Column(Integer, default=0)
    rows_updated = Column(Integer, default=0)
    rows_skipped = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    warnings = Column(String, nullable=True)  # JSON array of warning strings
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User")


class AutomationToken(Base):
    """Revocable API tokens for VPS/desktop upload helpers."""
    __tablename__ = "automation_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    token_prefix = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True, index=True)

    user = relationship("User", back_populates="automation_tokens")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
