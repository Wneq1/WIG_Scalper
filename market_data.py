import threading
import time
import yfinance as yf
# Import existing logic - respecting user's "database.py" rule
from database import load_portfolio_from_db, save_portfolio_snapshot

# Manual mapping for sWIG80 companies where GPW Benchmark name != Yahoo Ticker
# Migrated from fetch_gpw_debug.py
TICKER_MAPPING = {
    'MLPGROUP': 'MLG',
    'SNIEZKA': 'SKA',
    'AGORA': 'AGO',
    'BLOOBER': 'BLO',
    'CREEPYJAR': 'CRJ',
    'COGNOR': 'COG',
    'AMBRA': 'AMB',
    'MERCATOR': 'MRC',
    'XTPL': 'XTP',
    'MABION': 'MAB',
    'MLSYSTEM': 'MLS',
    'COLUMBUS': 'CLC',
    'PEKABEX': 'PBX',
    'WITTCHEN': 'WTN',
    'ERBUD': 'ERB',
    'CIGAMES': 'CIG',
    'VOTUM': 'VOT',
    'VIGOPHOTN': 'VGO',
    'ASTARTA': 'AST',
    'WAWEL': 'WWL',
    'ECHO': 'ECH',
    'OPONEO.PL': 'OPN',
    'TOYA': 'TOA',
    'AMICA': 'AMC',
    'SYGNITY': 'SGN',
    'BIOTON': 'BIO',
    'ONDE': 'OND',
    'ACAUTOGAZ': 'ACG',
    'WIELTON': 'WLT',
    'ARCTIC': 'ATC',
    'SNTVERSE': 'SNT',
    'MOSTALZAB': 'MSZ',
    'MEDICALG': 'MDG',
    'STALEXP': 'STX',
    'UNIMOT': 'UNT',
    'QUERCUS': 'QRS',
    'KOGENERA': 'KGN',
    'COMP': 'CMP',
    'MENNICA': 'MNC',
    'SANOK': 'SNK',
    'BORYSZEW': 'BRS',
    'ELEKTROTI': 'ELT',
    'DADELO': 'DAD',
    'SELENAFM': 'SEL',
    'CAPTORTX': 'CTX',
    'ARLEN': 'ARA',
    'SCPFL': 'SCP',
    'PLAYWAY': 'PLW',
    'BIOCELTIX': 'BCX',
    'FORTE': 'FTE',
    'ZEPAK': 'ZEP',
    'TARCZYNSKI': 'TAR',
    'MCI': 'MCI',
    'APATOR': 'APT',
    'STALPROD': 'STP',
    'CLNPHARMA': 'CLN',
    'GREENX': 'GRX',
    'RYVU': 'RVU',
    'DECORA': 'DCR',
    'GRENEVIA': 'GEA',
    'ATAL': '1AT', 
    'ENTER': 'ENT',
    'FERRO': 'FRO',
    'SELVITA': 'SLV',
    'DATAWALK': 'DAT',
    'VRG': 'VRG',
    'ASSECOBS': 'ABS',
    'MURAPOL': 'APR', 
    'POLIMEXMS': 'PXM',
    'ARCHICOM': 'ARH',
    'SHOPER': 'SHO',
    'TORPOL': 'TOR',
    'RAINBOW': 'RBW',
    'PURE': 'PUR',
    'TIM': 'TIM',
    'VOXEL': 'VOX',
    'MANGATA': 'MGT',
    'GRODNO': 'GRN',
    
    # Corrections based on errors
    'CREOTECH': 'CRI',
    'AILLERON': 'ALL',
    'BOGDANKA': 'LWB',
    'PCCROKITA': 'PCR',
    'BUMECH': 'BMC',
    'UNIBEP': 'UNI',
    'MURAPOL': 'MUR',
}

class MarketDataFetcher(threading.Thread):
    def __init__(self, interval=30):
        super().__init__()
        self.interval = interval
        self.daemon = True # Ends when main program ends
        self.running = True
        self.lock = threading.Lock()

    def run(self):
        print("[MarketDataFetcher] Wątek startuje...")
        while self.running:
            try:
                self.update_market_data()
            except Exception as e:
                print(f"[MarketDataFetcher] Błąd: {e}")
            
            time.sleep(self.interval)

    def update_market_data(self):
        # 1. Load current portfolio from DB (buffer)
        # We need the tickers.
        current_data = load_portfolio_from_db()
        if not current_data:
            print("[MarketDataFetcher] Pusty portfel w bazie. Czekam...")
            return

        print(f"[MarketDataFetcher] Pobieranie cen dla {len(current_data)} spółek...")
        
        # 2. Prepare Tickers for YFinance
        # Use simple map logic or the advanced ONE from fetch_gpw_debug if accessible, 
        # but better to keep self-contained logic here for speed or reuse.
        # We will reuse the mapping we defined in fetch_gpw_debug.py by importing it.
        
        yf_tickers = []
        ticker_map = {} # "ABC.WA" -> list of company dicts

        for c in current_data:
            raw_ticker = c['ticker']
            
            if raw_ticker in TICKER_MAPPING:
                base = TICKER_MAPPING[raw_ticker]
            else:
                base = raw_ticker
            
            yf_ticker = f"{base}.WA"
            yf_tickers.append(yf_ticker)
            
            if yf_ticker not in ticker_map:
                ticker_map[yf_ticker] = []
            ticker_map[yf_ticker].append(c)

        # 3. Batch Download
        try:
            # interval='1d' is standard, maybe '1m' if user wants super live but '1d' gives correct Today Change % usually
            # '1d' is safer for change from open.
            data = yf.download(yf_tickers, period="1d", group_by='ticker', threads=True, progress=False)
            
            updated_count = 0
            
            for yf_tick, company_list in ticker_map.items():
                price = 0.0
                change_pct = 0.0
                
                try:
                    if len(yf_tickers) > 1:
                        df = data[yf_tick]
                    else:
                        df = data
                        
                    if not df.empty:
                        last_row = df.iloc[-1]
                        price = float(last_row['Close'])
                        open_price = float(last_row['Open'])
                        volume = float(last_row['Volume'])
                        
                        if open_price > 0:
                            change_pct = ((price - open_price) / open_price) * 100.0
                            updated_count += 1
                except Exception:
                    pass
                
                # Update in memory objects
                for c in company_list:
                    # Only update if we got a valid price, or keep old? 
                    # If fetch fails, better keep old than 0. 
                    if price > 0:
                        c['price'] = price
                        c['change_pct'] = change_pct
                        c['turnover'] = price * volume # Approximate daily turnover (Val * Vol)
            
            # 4. Save back to DB
            # We use save_portfolio_snapshot to dump the updated state
            save_portfolio_snapshot(current_data)
            print(f"[MarketDataFetcher] Zaktualizowano ceny dla {updated_count} spółek.")
            
        except Exception as e:
            print(f"[MarketDataFetcher] Błąd yfinance: {e}")

    def stop(self):
        self.running = False
