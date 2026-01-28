import time
import sys
import tkinter as tk
from tkinter import ttk
import threading

# Modules
# Modules
from database import init_db, save_portfolio_snapshot, load_portfolio_from_db, get_last_portfolio_date, bulk_upsert_sectors
# from scheduler import should_update_portfolio # scheduler.py deleted
from sectors import enrich_data_with_sectors
# from fetch_gpw_debug import fetch_gpw_shares # fetch_gpw_debug.py deleted
from market_data import MarketDataFetcher
from visualizer import HeatMapVisualizer # Now a Tkinter Frame

def main():
    print("--- Start Systemu WIG Scalper (Tkinter + Threading) ---")
    
    # 1. Init DB
    init_db()
    
    # 2. Logic (Check Updates) 
    # Legacy scheduler/fetch logic removed as files were cleaned up.
    # The application now relies on existing DB data or Manual triggers (future).
    # If DB is empty, user might need to run a seed script or we can re-implement
    # a basic fetcher here if critical. For now, assuming data exists or thread will handle price updates.
    
    # Check data integrity
    if not load_portfolio_from_db():
        print("!!! [CRITICAL] No data in DB.")
        sys.exit(1)

    # 3. Start Data Thread (Producer)
    print(">>> [THREAD] Starting MarketDataFetcher...")
    
    # --- RESTORE CONSOLE OUTPUT ---
    # User wants to see the loaded data
    loaded_data = load_portfolio_from_db()
    if loaded_data:
        print(f"\n{'='*60}")
        print(f"{'TICKER':<15} | {'SECTOR':<30} | {'SHARE':<10}")
        print(f"{'-'*60}")
        # Sort by share desc
        sorted_data = sorted(loaded_data, key=lambda x: x.get('share', 0), reverse=True)
        for row in sorted_data:
            t = row.get('ticker', '')
            s = row.get('sector', 'N/A')
            sh = row.get('share', 0.0)
            print(f"{t:<15} | {s:<30} | {sh:<10.2f}%")
        print(f"{'='*60}\n")
        print(f">>> Loaded {len(loaded_data)} companies.")
    # ------------------------------

    fetcher = MarketDataFetcher(interval=30)
    fetcher.start()

    # 4. Start GUI (Consumer)
    root = tk.Tk()
    root.title("WIG Scalper - System Handlowy")
    root.geometry("1400x900")
    root.configure(bg="#2b2b2b")

    # --- LOGO & HEADER ---
    try:
        from PIL import Image, ImageTk
        import os
        
        logo_path = "LOGO.png"
        if os.path.exists(logo_path):
            # 1. Load Image
            pil_img = Image.open(logo_path)
            
            # 2. Set Window Icon (Taskbar)
            icon_photo = ImageTk.PhotoImage(pil_img)
            root.iconphoto(True, icon_photo)
            
            # 3. Create Header Frame
            header_frame = tk.Frame(root, bg="#2b2b2b")
            header_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=10)
            
            # 4. Resize for Header UI (Keep Aspect Ratio)
            ui_img = pil_img.copy()
            ui_img.thumbnail((56, 56), Image.Resampling.LANCZOS) # Slightly smaller to fit frame
            ui_photo = ImageTk.PhotoImage(ui_img)
            
            # Styled "Icon Frame" to make it look like a badge
            icon_frame = tk.Frame(header_frame, bg="#2b2b2b", highlightbackground="#444", highlightthickness=2, highlightcolor="#444")
            icon_frame.pack(side=tk.LEFT, padx=(0, 15))
            
            logo_label = tk.Label(icon_frame, image=ui_photo, bg="#2b2b2b")
            logo_label.image = ui_photo # keep ref
            logo_label.pack(padx=2, pady=2)
            
            # 5. Application Title next to Logo
            app_title = tk.Label(header_frame, text="sWIG80tr", font=('Helvetica', 22, 'bold'), fg="white", bg="#2b2b2b")
            app_title.pack(side=tk.LEFT, padx=(0, 20))
            
            # --- HEADER STATS (Left Side, next to title) ---
            stats_frame = tk.Frame(header_frame, bg="#2b2b2b")
            stats_frame.pack(side=tk.LEFT)
            
            # Labels for stats (Horizontal Layout)
            # "Cena:" Label on White
            lbl_price_title = tk.Label(stats_frame, text="Cena:", font=('Helvetica', 14), fg="white", bg="#2b2b2b")
            lbl_price_title.pack(side=tk.LEFT, padx=(0, 5))

            lbl_index_price = tk.Label(stats_frame, text="...", font=('Helvetica', 22, 'bold'), fg="#ddd", bg="#2b2b2b")
            lbl_index_price.pack(side=tk.LEFT, padx=(0, 15))
            
            lbl_index_change = tk.Label(stats_frame, text="...", font=('Helvetica', 16, 'bold'), fg="white", bg="#2b2b2b")
            lbl_index_change.pack(side=tk.LEFT, padx=(0, 20))
            
            # Additional Details: Open, Prev Close, Avg
            lbl_index_extended = tk.Label(stats_frame, text="...", font=('Helvetica', 11), fg="#aaa", bg="#2b2b2b")
            lbl_index_extended.pack(side=tk.LEFT, padx=(0, 20))
            
            # --- TURNOVER (Obrót) ---
            # "Obrót:" Label on White
            lbl_turnover = tk.Label(stats_frame, text="Obrót: ...", font=('Helvetica', 14, 'bold'), fg="white", bg="#2b2b2b") 
            lbl_turnover.pack(side=tk.LEFT, padx=(0, 0))
            
            print(">>> [GUI] Logo loaded successfully.")

            # Function to update header stats
            def update_idx_stats():
                try:
                    # 1. Update Index/ETF Stats
                    import yfinance as yf
                    ticker = "ETFBS80TR.WA"
                    # Fetch 5d to ensure we have previous close
                    data = yf.Ticker(ticker).history(period="5d")
                    
                    if not data.empty:
                        last = data.iloc[-1]
                        price = last['Close']
                        open_p = last['Open']
                        high_p = last['High']
                        low_p = last['Low']
                        
                        # Average (Typical Price)
                        avg_p = (high_p + low_p + price) / 3.0
                        
                        # Previous Close (if available)
                        prev_close = open_p # Default fallback
                        if len(data) >= 2:
                            prev_close = data.iloc[-2]['Close']
                        
                        # Calculate change vs Previous Close (Standard)
                        change_pct = 0.0
                        if prev_close > 0:
                            change_pct = ((price - prev_close) / prev_close) * 100.0
                        
                        # Color
                        color = "#00ff00" if change_pct >= 0 else "#ff4444"
                        sign = "+" if change_pct >= 0 else ""
                        
                        # Formatting
                        formatted_price = f"{price:,.2f}".replace(",", " ")
                        lbl_index_price.config(text=f"{formatted_price} PLN")
                        lbl_index_change.config(text=f"{sign}{change_pct:.2f}%", fg=color)
                        
                        # Extended info
                        lbl_index_extended.config(
                            text=f"Otw: {open_p:.2f}  |  Zam: {prev_close:.2f}  |  Śr: {avg_p:.2f}"
                        )
                        
                    # 2. Update Total Turnover (Sum of all companies)
                    # We read directly from DB as it is updated by MarketDataFetcher thread
                    from database import load_portfolio_from_db
                    portfolio = load_portfolio_from_db()
                    total_turnover = sum(c.get('turnover', 0.0) for c in portfolio)
                    
                    # Format to mln PLN
                    turnover_mln = total_turnover / 1_000_000.0
                    lbl_turnover.config(text=f"Obrót: {turnover_mln:.1f} mln PLN")
                    
                except Exception as e:
                    print(f"Index Stats Error: {e}")
                
                # Update every 60s
                root.after(60000, update_idx_stats)
            
            # Start updating
            root.after(1000, update_idx_stats)

        else:
            print(f">>> [GUI] Logo file not found: {logo_path}")
            
    except Exception as e:
        print(f"Error checking requirements or loading logo: {e}")
    
    # --- STYLING ---
    style = ttk.Style()
    style.theme_use('clam') # 'clam' allows better custom coloring than 'vista'
    
    # Configure Notebook (Tabs)
    style.configure("TNotebook", background="#2b2b2b", borderwidth=0)
    style.configure("TNotebook.Tab", background="#3e3e3e", foreground="white", padding=[15, 5], font=('Helvetica', 10, 'bold'))
    style.map("TNotebook.Tab", background=[("selected", "#1a9641")], foreground=[("selected", "white")])
    
    # Configure Treeview
    style.configure("Dark.Treeview", 
                    background="#2b2b2b", 
                    foreground="white", 
                    fieldbackground="#2b2b2b", 
                    rowheight=25, 
                    borderwidth=0)
    style.configure("Dark.Treeview.Heading", 
                    background="#1e1e1e", 
                    foreground="white", 
                    font=('Helvetica', 10, 'bold'),
                    relief="flat")
    style.map("Dark.Treeview.Heading", background=[("active", "#333333")])
    
    # --- TABS LAYOUT ---
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Imports
    from visualizer import HeatMapVisualizer
    from dashboard import IndexTab, SectorsTab
    
    # Tab 1: Skład Indeksu
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text="Skład Indeksu")
    index_frame = IndexTab(tab1)
    
    # Tab 2: Sektory
    tab2 = ttk.Frame(notebook)
    notebook.add(tab2, text="Sektory")
    sectors_frame = SectorsTab(tab2)
    
    # Tab 3: Heatmapa
    tab3 = ttk.Frame(notebook)
    notebook.add(tab3, text="Heatmapa")
    viz_frame = HeatMapVisualizer(tab3)
    
    # Periodic GUI Update Loop
    def update_gui_loop():
        # Update current tab content
        current_tab = notebook.index(notebook.select())
        
        try:
            if current_tab == 0:
                index_frame.update_view()
            elif current_tab == 1:
                sectors_frame.update_view()
            elif current_tab == 2:
                viz_frame.update_plot()
        except Exception as e:
            print(f"GUI Error: {e}")
        
        root.after(5000, update_gui_loop)

    # Start the loop
    root.after(1000, update_gui_loop)

    # Handle Close
    def on_closing():
        print(">>> Closing App...")
        fetcher.stop()
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    print(">>> [GUI] GUI Starting...")
    root.mainloop()

if __name__ == "__main__":
    main()
