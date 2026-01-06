from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    bet_id = Column(String, unique=True, index=True)
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

    __table_args__ = (
        Index('idx_strategy_date', 'strategy', 'settled_date'),
        Index('idx_bet_type_status', 'bet_type', 'status'),
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
