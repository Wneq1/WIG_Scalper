
import sqlite3
import datetime
import os

DB_FILE = r"C:\Users\WneQ\Desktop\wig\wig_data.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()
    # Tabela sektorów (Baza Wiedzy)
    c.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            ticker TEXT PRIMARY KEY,
            sector TEXT,
            updated_at TIMESTAMP
        )
    ''')
    
    # Tabela składu portfela (Cache Portfela)
    c.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            ticker TEXT PRIMARY KEY,
            share REAL,
            price REAL,
            change_pct REAL,
            updated_at TIMESTAMP
        )
    ''')
    
    # Check if new columns exist (migration for existing DB)
    try:
        c.execute('ALTER TABLE portfolio ADD COLUMN price REAL')
    except sqlite3.OperationalError:
        pass # Columns already exist
        
    try:
        c.execute('ALTER TABLE portfolio ADD COLUMN change_pct REAL')
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def get_sector_from_db(ticker):
    """Retrieves the sector for a given ticker from the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT sector FROM companies WHERE ticker = ?', (ticker,))
    row = c.fetchone()
    conn.close()
    if row:
        return row['sector']
    return None

def save_sector_to_db(ticker, sector):
    """Saves or updates the sector for a given ticker."""
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now()
    c.execute('''
        INSERT INTO companies (ticker, sector, updated_at) 
        VALUES (?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET
            sector=excluded.sector,
            updated_at=excluded.updated_at
    ''', (ticker, sector, now))
    conn.commit()
    conn.close()

def bulk_upsert_sectors(data_dict):
    """
    Updates multiple sectors at once.
    data_dict: {ticker: sector}
    """
    if not data_dict:
        return
        
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now()
    
    # Prepare list of tuples for executemany
    params = [(ticker, sector, now) for ticker, sector in data_dict.items()]
    
    c.executemany('''
        INSERT INTO companies (ticker, sector, updated_at) 
        VALUES (?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET
            sector=excluded.sector,
            updated_at=excluded.updated_at
    ''', params)
    
    conn.commit()
    conn.close()

# --- PORTFOLIO FUNCTIONS ---

def save_portfolio_snapshot(data_list):
    """
    Saves the full portfolio list to DB.
    Replaces existing cache (we assume we want the current state).
    data_list: list of dicts {'ticker': ..., 'share': ..., 'price': ..., 'change_pct': ...}
    """
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now()
    
    # Clear old portfolio cache - we only want current state
    c.execute('DELETE FROM portfolio')
    
    params = []
    for item in data_list:
        params.append((
            item['ticker'], 
            item.get('share', 0.0), 
            item.get('price', 0.0), 
            item.get('change_pct', 0.0), 
            now
        ))
        
    c.executemany('''
        INSERT INTO portfolio (ticker, share, price, change_pct, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', params)
    
    conn.commit()
    conn.close()

def load_portfolio_from_db():
    """
    Loads portfolio from DB and joins with sectors.
    Returns list of dicts: {'ticker', 'share', 'sector', 'price', 'change_pct'}
    """
    conn = get_connection()
    c = conn.cursor()
    
    # Left join to get sectors if available
    c.execute('''
        SELECT p.ticker, p.share, p.price, p.change_pct, c.sector 
        FROM portfolio p
        LEFT JOIN companies c ON p.ticker = c.ticker
    ''')
    rows = c.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            'ticker': r['ticker'],
            'share': r['share'],
            'price': r['price'] if r['price'] else 0.0,
            'change_pct': r['change_pct'] if r['change_pct'] else 0.0,
            'sector': r['sector'] if r['sector'] else 'Inne / Nieznany'
        })
    return result

def get_last_portfolio_date():
    """Returns the datetime of the last portfolio update or None."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT MAX(updated_at) as last_date FROM portfolio')
    row = c.fetchone()
    conn.close()
    
    if row and row['last_date']:
        try:
            return datetime.datetime.strptime(row['last_date'], "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            # Try alternative format if microsecond assumes diff
            try:
                return datetime.datetime.strptime(row['last_date'], "%Y-%m-%d %H:%M:%S")
            except:
                return None
    return None
