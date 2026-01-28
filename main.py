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
