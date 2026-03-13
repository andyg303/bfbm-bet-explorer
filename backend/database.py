from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv
from datetime import datetime, timezone
import os

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    password_reset_token = Column(String, nullable=True, index=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # Subscription / Stripe
    subscription_status = Column(String, default="inactive", nullable=False)  # inactive | active | cancelled | expired
    subscription_plan = Column(String, nullable=True)  # 6month | 12month
    subscription_start = Column(DateTime, nullable=True)
    subscription_expires = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String, nullable=True, unique=True, index=True)
    stripe_checkout_session_id = Column(String, nullable=True)

    bets = relationship("Bet", back_populates="owner", lazy="dynamic")


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
    lay_liability = Column(Float)
    bsp_diff_absolute = Column(Float)
    bsp_diff_percentage = Column(Float)
    bsp_diff_probability = Column(Float)
    is_deleted = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False, index=True)

    owner = relationship("User", back_populates="bets")

    __table_args__ = (
        Index('idx_strategy_date', 'strategy', 'settled_date'),
        Index('idx_bet_type_status', 'bet_type', 'status'),
        Index('idx_user_bet_id', 'user_id', 'bet_id', unique=True),
        Index('idx_user_strategy', 'user_id', 'strategy'),
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
