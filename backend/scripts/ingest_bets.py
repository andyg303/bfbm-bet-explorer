import pandas as pd
import re
from sqlalchemy.orm import Session
from datetime import datetime
import os
import glob
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, init_db, Bet
from scripts.bsp_utils import calculate_bsp_metrics


# ═══════════════════════════════════════════════════════════════════════════════
# Column name mapping — maps every known BFBM CSV column header (lowercased)
# to our internal DB field name.  None = recognised but not stored.
# ═══════════════════════════════════════════════════════════════════════════════

COLUMN_MAP = {
    # ── Profit / Loss ──────────────────────────────────────────────────────
    'p/l':                        'profit_loss',
    'profitloss':                 'profit_loss',
    'profit/loss':                'profit_loss',
    'profit_loss':                'profit_loss',
    'profit loss':                'profit_loss',

    # ── Monetary amounts ───────────────────────────────────────────────────
    'matched amount':             'matched_amount',
    'matched':                    'matched_amount',
    'loss rec. amount':           'loss_rec_amount',
    'total matched on runner':    'total_matched_on_runner',
    'total matched on market':    'total_matched_on_market',

    # ── Prices / Odds ─────────────────────────────────────────────────────
    'avg. price matched':         'avg_price_matched',
    'avgprice':                   'avg_price_matched',
    'average price':              'avg_price_matched',
    'average price matched':      'avg_price_matched',
    'price requested':            'price_requested',
    'bsp':                        'bsp',
    'sp':                         'bsp',
    'sp price':                   'bsp',

    # ── Identifiers ───────────────────────────────────────────────────────
    'bet id':                     'bet_id',
    'betid':                      'bet_id',

    # ── Core descriptors ──────────────────────────────────────────────────
    'status':                     'status',
    'strategy':                   'strategy',
    'strategyname':               'strategy',
    'selection':                  'selection',
    'selectionname':              'selection',
    'description':                'description',
    'name':                       'description',        # bet_data "Name" column
    'bet type':                   'bet_type',

    # ── Event / Sport ─────────────────────────────────────────────────────
    'event':                      'event',
    'eventtypename':              'event',
    'sport':                      'event',

    # ── Dates ─────────────────────────────────────────────────────────────
    'placed date':                'placed_date',
    'placeddate':                 'placed_date',
    'matched date':               'matched_date',
    'settled date':               'settled_date',
    'starttime':                  'start_time',
    'market start time':          'start_time',

    # ── Categorical / metadata ────────────────────────────────────────────
    'country code':               'country_code',
    'competition':                'competition',
    'favorite position':          'favorite_position',
    'market type':                'market_type',
    'marketname':                 'market_name',
    'market':                     'market_name',        # BFBM "Market" column
    'detailed market name':       'market_name',        # BFBM optional column
    'number of selections':       'number_of_selections',
    'short description':          'short_description',
    'tipster':                    'tipster',
    'marketid':                   'market_id',
    'market id':                  'market_id',

    # ── Known optional columns from BFBM Customization dialog ─────────────
    # These are all recognised so they don't trigger "unrecognised" warnings.
    # Columns mapped to None are silently ignored during ingestion.

    # -- IDs --
    'unmatched':                  None,
    'setid':                      None,
    'journey':                    None,
    'runner id':                  None,
    'runnerid':                   None,
    'selectionid':                None,
    'selection id':               None,
    'competition id':             None,
    'event type id':              None,
    'eventtypeid':                None,
    'strategy id':                None,
    'strategyid':                 None,
    'strategy selection id':      None,
    'strategyselectionid':        None,

    # -- Bet status / result --
    'settle as win':              None,
    'settle as loss':             None,
    'void bet':                   None,
    'win/lose':                   None,
    'betresult':                  None,
    'simulated bet?':             None,
    'simulated bet':              None,
    'simulatedbet':               None,

    # -- Sizing / amounts --
    'unmatched amount':           None,
    'size canceled':              None,
    'size cancelled':             None,
    'sizecanceled':               None,
    'sizecancelled':              None,
    'size lapsed':                None,
    'sizelapsed':                 None,
    'size settled':               None,
    'sizesettled':                None,

    # -- Banking / percentage --
    '% of betting bank':          None,
    'betting bank':               None,
    'bettingbank':                None,
    'p/l as % of betting bank':   None,

    # -- Market metadata --
    'market type variant':        None,
    'markettypevariant':          None,
    'order type':                 None,
    'ordertype':                  None,
    'currency':                   None,

    # -- Price / trading --
    'persistence':                None,
    'persistence type':           None,
    'price reduced.':             None,
    'price reduced':              None,
    'pricereduced':               None,

    # -- Runner / position --
    'runner position':            None,
    'runnerposition':             None,

    # -- Handicap --
    'handicap':                   None,

    # -- In-play / live --
    'in play':                    None,
    'inplay':                     None,
    'betplacedlive':              None,
    'bet placed live':            None,

    # -- Commission / regulation --
    'commission':                 None,
    'commission rate':            None,
    'regulator code':             None,
    'regulator name':             None,
    'rule 4 deduction':           None,
    'rule4deduction':             None,

    # -- Other / legacy --
    'eventname':                  None,
    'event name':                 None,
    'net profit':                 None,
    'settle date':                None,
    'betplaceddate':              None,
    'marketstarttime':            None,
    'start time':                 'start_time',
}

# Minimum fields the CSV must contain for a meaningful import
REQUIRED_FIELDS = ['profit_loss', 'status', 'bet_id']

# We warn (but don't block) if these are absent
RECOMMENDED_FIELDS = {
    'placed_date':  'Placed Date',
    'strategy':     'Strategy',
    'selection':    'Selection',
}

# Monetary columns that may contain currency symbols (£, ?, ï¿½ etc.)
CURRENCY_FIELDS = {
    'matched_amount', 'loss_rec_amount', 'profit_loss',
    'total_matched_on_runner', 'total_matched_on_market',
}

# Date/time columns
DATE_FIELDS = {'placed_date', 'matched_date', 'settled_date', 'start_time'}


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def sanitize_currency(value):
    """Remove currency symbols and convert to float.
    Handles any encoding artefacts (£ rendered as ï¿½ etc.) by stripping
    everything that isn't a digit, decimal point, or leading minus sign."""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    value_str = str(value).strip()
    negative = value_str.startswith('-')
    # Keep only digits and decimal point — encoding-agnostic
    cleaned = re.sub(r'[^\d.]', '', value_str)

    if not cleaned:
        return None
    try:
        result = float(cleaned)
        return -result if negative else result
    except ValueError:
        return None

def sanitize_strategy_name(name):
    """Clean strategy names by replacing encoding artefacts and non-ASCII
    characters (e.g. £ rendered as \\ufffd or ï¿½) with their best ASCII
    equivalents.  The £ sign is kept as the actual £ character so
    that it displays correctly across all platforms."""
    if pd.isna(name) or not name:
        return None
    s = str(name).strip()
    # Replace common mojibake / replacement-character sequences
    s = s.replace('\ufffd', '£')       # U+FFFD replacement character -> £
    s = s.replace('ï¿½', '£')           # UTF-8 mojibake of replacement char
    s = s.replace('Â£', '£')            # Double-encoded UTF-8 £
    s = s.replace('Ã‚Â£', '£')          # Triple-encoded UTF-8 £
    # Question-mark artefact from encoding loss (e.g. ?100 → £100)
    s = re.sub(r'\?(\d)', r'£\1', s)
    # Remove any remaining non-printable / control characters
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', s)
    # Collapse multiple spaces
    s = re.sub(r'\s{2,}', ' ', s)
    return s

def normalize_event_name(event_name):
    """Convert event name to kebab-case format and standardize names"""
    if pd.isna(event_name) or not event_name:
        return None
    
    # Convert to lowercase and replace spaces with hyphens
    normalized = str(event_name).lower().strip()
    normalized = normalized.replace(' ', '-')
    
    # Standardize soccer to football
    if normalized == 'soccer':
        normalized = 'football'
    
    return normalized

def apply_commission(profit_loss):
    """Apply 2% commission on winning bets"""
    if profit_loss is None:
        return None
    
    # Only apply commission on positive returns (winning bets)
    if profit_loss > 0:
        return profit_loss * 0.98  # Deduct 2% commission
    
    return profit_loss

def parse_datetime(value):
    """Parse datetime strings in multiple formats (ISO, DD/MM/YYYY, etc.).
    Rejects sentinel dates like 0001-01-01 used for unsettled bets."""
    if pd.isna(value) or value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        # dayfirst=True handles DD/MM/YYYY (UK/Betfair standard)
        # ISO format (YYYY-MM-DD) is unambiguous and still parsed correctly
        dt = pd.to_datetime(s, dayfirst=True)
        if pd.isna(dt):
            return None
        # Reject sentinel dates (e.g. 0001-01-01 for unsettled bets)
        if dt.year < 1900:
            return None
        return dt
    except Exception:
        return None

def read_csv(filepath: str) -> 'pd.DataFrame':
    """Try multiple encodings so both UTF-8 and latin-1 exports work."""
    for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
        try:
            return pd.read_csv(filepath, encoding=encoding)
        except UnicodeDecodeError:
            continue
    # Last resort: replace undecodable bytes
    return pd.read_csv(filepath, encoding='latin-1', errors='replace')


def clean_column_name(col: str) -> str:
    """Strip BOM markers, replacement characters, and surrounding quotes
    from a raw CSV column header."""
    s = str(col).strip()
    # BOM bytes that leak through when read with latin-1 / cp1252
    s = s.replace('\ufeff', '').replace('\ufffd', '').replace('ï¿½', '')
    s = s.lstrip('\xef\xbb\xbf')
    # UTF-16 LE BOM byte that can appear as ÿ (0xFF) in latin-1
    s = s.lstrip('\xff\xfe')
    # Surrounding quotes
    s = s.strip('"').strip("'").strip()
    return s


def normalize_columns(df: 'pd.DataFrame'):
    """Map CSV column headers to internal field names.

    Returns (renamed_df, warnings_list).
    Raises ValueError if required columns are missing.
    """
    warnings: list[str] = []

    # 1) Clean raw headers
    cleaned_map = {col: clean_column_name(col) for col in df.columns}
    df = df.rename(columns=cleaned_map)

    # 2) Build rename dict: cleaned header → internal name
    rename_map: dict[str, str] = {}
    used_internals: dict[str, str] = {}  # internal_name → first csv header
    unmapped: list[str] = []

    for col in df.columns:
        key = col.lower().strip()
        if key in COLUMN_MAP:
            internal = COLUMN_MAP[key]
            if internal is None:
                continue  # recognised but intentionally ignored
            if internal in used_internals:
                # Another column already maps here – skip duplicate
                warnings.append(
                    f"Column '{col}' also maps to '{internal}' (already mapped from "
                    f"'{used_internals[internal]}'). Skipping duplicate."
                )
                continue
            rename_map[col] = internal
            used_internals[internal] = col
        else:
            unmapped.append(col)

    if unmapped:
        warnings.append(f"Unrecognised columns (ignored): {', '.join(unmapped)}")

    df = df.rename(columns=rename_map)

    # 3) Validate required fields
    missing = [f for f in REQUIRED_FIELDS if f not in df.columns]
    if missing:
        labels = {
            'profit_loss': 'Profit/Loss (P/L or ProfitLoss)',
            'status':       'Status',
            'bet_id':       'Bet ID (Bet Id or BetId)',
        }
        pretty = [labels.get(f, f) for f in missing]
        raise ValueError(
            f"CSV is missing required columns: {', '.join(pretty)}. "
            f"Please ensure these fields are included in your BFBM export."
        )

    # 4) Warn about missing recommended fields
    missing_rec = {k: v for k, v in RECOMMENDED_FIELDS.items() if k not in df.columns}
    if missing_rec:
        names = ', '.join(missing_rec.values())
        warnings.append(f"Missing recommended columns: {names}. Some features may be limited.")

    return df, warnings


def safe_get(row, field, default=None):
    """Return the value of *field* from a pandas row, or *default* if the
    column doesn't exist or the value is NaN."""
    if field in row.index and pd.notna(row[field]):
        return row[field]
    return default


def safe_float(value):
    """Convert a value to float, stripping commas. Returns None on failure."""
    if value is None:
        return None
    try:
        return float(str(value).replace(',', ''))
    except (ValueError, TypeError):
        return None


def safe_int(value):
    """Convert a value to int (via float to handle '3.0'). Returns None on failure."""
    if value is None:
        return None
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Main ingestion
# ═══════════════════════════════════════════════════════════════════════════════

def ingest_csv_file(filepath: str, db: Session, user_id: int = None):
    """Ingest a single CSV file into the database.

    Supports both BFBM *bet_history* and *bet_data* export formats,
    with any subset of optional columns and in any column order.

    Args:
        filepath: Path to CSV file.
        db: SQLAlchemy session.
        user_id: The authenticated user's ID. All bets will be tagged to this user.

    Returns:
        dict with keys: inserted, updated, skipped, warnings
    """
    print(f"Processing {filepath}...")

    df = read_csv(filepath)
    print(f"Found {len(df)} rows")

    # ── Column normalisation ──────────────────────────────────────────────
    df, warnings = normalize_columns(df)

    # ── Sanitise currency fields ──────────────────────────────────────────
    for field in CURRENCY_FIELDS:
        if field in df.columns:
            df[field] = df[field].apply(sanitize_currency)

    # ── Parse date fields ─────────────────────────────────────────────────
    for field in DATE_FIELDS:
        if field in df.columns:
            df[field] = df[field].apply(parse_datetime)

    # ── Row-by-row processing ─────────────────────────────────────────────
    inserted = 0
    updated = 0
    skipped = 0
    error_count = 0

    for idx, row in df.iterrows():
        try:
            # ── Status filter ─────────────────────────────────────────────
            status = safe_get(row, 'status')
            status = str(status).strip().upper() if status else None
            if status not in ('MATCHED', 'SETTLED'):
                skipped += 1
                continue

            # ── Bet ID (clean leading apostrophe from bet_data format) ────
            bet_id = safe_get(row, 'bet_id')
            if bet_id is None:
                skipped += 1
                continue
            bet_id = str(bet_id).strip()
            if bet_id.startswith("'"):
                bet_id = bet_id[1:]
            if not bet_id:
                skipped += 1
                continue

            # ── De-duplication lookup ─────────────────────────────────────
            if user_id is not None:
                existing = db.query(Bet).filter(
                    Bet.bet_id == bet_id, Bet.user_id == user_id
                ).first()
            else:
                existing = db.query(Bet).filter(Bet.bet_id == bet_id).first()

            # ── Typed field extraction ────────────────────────────────────
            bet_type = safe_get(row, 'bet_type')
            bet_type = str(bet_type).strip().upper() if bet_type else None

            matched_amount = safe_get(row, 'matched_amount')
            avg_price = safe_float(safe_get(row, 'avg_price_matched'))
            price_req = safe_float(safe_get(row, 'price_requested'))
            bsp_val = safe_float(safe_get(row, 'bsp'))
            fav_pos = safe_int(safe_get(row, 'favorite_position'))
            num_sel = safe_int(safe_get(row, 'number_of_selections'))

            total_runner = safe_get(row, 'total_matched_on_runner')
            total_market = safe_get(row, 'total_matched_on_market')

            # ── Lay liability ─────────────────────────────────────────────
            lay_liability = None
            if bet_type == 'LAY' and matched_amount and avg_price:
                lay_liability = (avg_price - 1) * matched_amount

            # ── BSP metrics ───────────────────────────────────────────────
            bsp_abs, bsp_pct, bsp_prob = calculate_bsp_metrics(
                bet_type, avg_price, bsp_val
            )

            # ── Commission on P/L ─────────────────────────────────────────
            raw_pl = safe_get(row, 'profit_loss')
            if raw_pl is not None and not isinstance(raw_pl, (int, float)):
                raw_pl = safe_float(raw_pl)
            profit_loss_with_commission = apply_commission(raw_pl)

            # ── String fields ─────────────────────────────────────────────
            event = safe_get(row, 'event')
            event = normalize_event_name(event) if event else None

            strategy = safe_get(row, 'strategy')
            strategy = sanitize_strategy_name(strategy) if strategy else None

            description     = str(safe_get(row, 'description'))   if safe_get(row, 'description') else None
            selection       = str(safe_get(row, 'selection'))     if safe_get(row, 'selection') else None
            country_code    = str(safe_get(row, 'country_code'))  if safe_get(row, 'country_code') else None
            competition     = str(safe_get(row, 'competition'))   if safe_get(row, 'competition') else None
            short_desc      = str(safe_get(row, 'short_description')) if safe_get(row, 'short_description') else None
            tipster         = str(safe_get(row, 'tipster'))       if safe_get(row, 'tipster') else None
            market_type     = str(safe_get(row, 'market_type'))   if safe_get(row, 'market_type') else None
            market_name     = str(safe_get(row, 'market_name'))   if safe_get(row, 'market_name') else None
            market_id       = str(safe_get(row, 'market_id'))     if safe_get(row, 'market_id') else None

            # ── Date fields ───────────────────────────────────────────────
            placed_date  = safe_get(row, 'placed_date')
            matched_date = safe_get(row, 'matched_date')
            settled_date = safe_get(row, 'settled_date')
            start_time   = safe_get(row, 'start_time')

            # ── Assemble bet record ───────────────────────────────────────
            bet_data = {
                'bet_id':                 bet_id,
                'event':                  event,
                'country_code':           country_code,
                'competition':            competition,
                'favorite_position':      fav_pos,
                'description':            description,
                'selection':              selection,
                'bet_type':               bet_type,
                'matched_amount':         matched_amount,
                'loss_rec_amount':        safe_get(row, 'loss_rec_amount'),
                'avg_price_matched':      avg_price,
                'price_requested':        price_req,
                'status':                 status,
                'profit_loss':            profit_loss_with_commission,
                'strategy':               strategy,
                'bsp':                    bsp_val,
                'total_matched_on_runner': total_runner,
                'total_matched_on_market': total_market,
                'short_description':      short_desc,
                'tipster':                tipster,
                'placed_date':            placed_date,
                'matched_date':           matched_date,
                'settled_date':           settled_date,
                'start_time':             start_time,
                'number_of_selections':   num_sel,
                'market_type':            market_type,
                'market_name':            market_name,
                'market_id':              market_id,
                'lay_liability':          lay_liability,
                'bsp_diff_absolute':      bsp_abs,
                'bsp_diff_percentage':    bsp_pct,
                'bsp_diff_probability':   bsp_prob,
            }

            if existing:
                # Update existing bet — NEVER overwrite is_deleted, is_archived, user_id
                for key, value in bet_data.items():
                    if key in ('bet_id', 'is_deleted', 'is_archived', 'user_id'):
                        continue
                    setattr(existing, key, value)
                updated += 1
            else:
                if user_id is not None:
                    bet_data['user_id'] = user_id
                bet = Bet(**bet_data)
                db.add(bet)
                inserted += 1

            # Commit in batches of 100
            if (inserted + updated) % 100 == 0:
                db.commit()
                print(f"  Processed {inserted + updated} rows...")

        except Exception as e:
            error_count += 1
            if error_count <= 5:
                warnings.append(f"Row {idx + 2}: {e}")  # +2 for 1-based + header
            elif error_count == 6:
                warnings.append("(Further row errors suppressed)")
            db.rollback()
            skipped += 1
            continue

    db.commit()  # Final commit for remaining rows

    print(f"Completed: {inserted} inserted, {updated} updated, {skipped} skipped")
    return {
        'inserted': inserted,
        'updated':  updated,
        'skipped':  skipped,
        'warnings': warnings,
    }


def main():
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # Resolve data directory: use DATA_DIR env var, or look for data/ relative to project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(script_dir)
        default_data_dir = os.path.join(backend_dir, 'data')
        data_dir = os.environ.get('DATA_DIR', default_data_dir)
        
        csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
        
        if not csv_files:
            print(f"No CSV files found in {data_dir}")
            print("Place your CSV bet export files in the 'data/' folder in the project root.")
            return
        
        print(f"Found {len(csv_files)} CSV files in {data_dir}")
        
        total_inserted = total_updated = total_skipped = 0
        all_warnings = []
        for csv_file in csv_files:
            result = ingest_csv_file(csv_file, db)
            total_inserted += result['inserted']
            total_updated += result['updated']
            total_skipped += result['skipped']
            all_warnings.extend(result['warnings'])
        
        total_bets = db.query(Bet).count()
        print(f"\nSummary: {total_inserted} inserted, {total_updated} updated, {total_skipped} skipped")
        print(f"Total bets in database: {total_bets}")
        if all_warnings:
            print(f"Warnings:")
            for w in all_warnings:
                print(f"  ⚠ {w}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
