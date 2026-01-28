from fetch_gpw_debug import fetch_gpw_data
from sectors import enrich_data_with_sectors
from database import init_db, save_portfolio_snapshot, load_portfolio_from_db, get_last_portfolio_date
from scheduler import should_update_portfolio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

# Upewniamy się, że baza jest gotowa
init_db()

# ... create_gui and other view functions remain the same but need to be retained ...
# To modify imports and main while keeping other functions, I should use multi_replace or careful replace. 
# But since I have to replace lines 1-8 and 202-217, it's easier to use replace_file_content on the whole file 
# OR use multi_replace. However, instructions say "Retry with simpler edit".
# Let's replace ONLY main() first, assuming imports are handled. No, imports need to be there.
# I will just replace the top block and the bottom block using multi_replace.

# Oops, I can't switch tool in thought. I must use the tool.
# I will use multi_replace_file_content this time as it's cleaner for non-contiguous edits.
# Wait, I am running `replace_file_content`. I will use it to replace the whole file content since I have it all from view_file.
# Actually, I will just replace the imports and main() using multi_replace.


def create_gui(data):
    """
    Tworzy okno GUI z zakładkami (Spółki / Sektory).
    """
    root = tk.Tk()
    root.title("Analiza Portfela sWIG80 (Live AI Sector Analysis)")
    root.geometry("1400x900")
    
    # --- DARK THEME CONFIG ---
    bg_color = "#2b2b2b"
    fg_color = "#ffffff"
    accent_color = "#3c3f41"
    
    root.configure(bg=bg_color)
    plt.style.use('dark_background') # Matplotlib Dark Mode
    
    style = ttk.Style()
    style.theme_use('clam')
    
    # Konfiguracja stylów widgetów
    style.configure("TFrame", background=bg_color)
    style.configure("TLabel", background=bg_color, foreground=fg_color)
    style.configure("TNotebook", background=bg_color, borderwidth=0)
    style.configure("TNotebook.Tab", background=accent_color, foreground="lightgray", padding=[10, 5])
    style.map("TNotebook.Tab", background=[("selected", bg_color)], foreground=[("selected", "white")])
    
    style.configure("Treeview", 
                    background=bg_color, 
                    foreground=fg_color, 
                    fieldbackground=bg_color,
                    borderwidth=0)
    style.configure("Treeview.Heading", 
                    background=accent_color, 
                    foreground="white", 
                    relief="flat")
    style.map("Treeview", background=[('selected', '#4a6984')])
    
    # Notebook (Zakładki)
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # === ZAKŁADKA 1: SPÓŁKI ===
    tab_companies = ttk.Frame(notebook)
    notebook.add(tab_companies, text="Analiza Wg Spółek")
    create_company_view(tab_companies, data, bg_color)
    
    # === ZAKŁADKA 2: SEKTORY ===
    tab_sectors = ttk.Frame(notebook)
    notebook.add(tab_sectors, text="Analiza Wg Sektorów")
    create_sector_view(tab_sectors, data, bg_color)
    
    print("Okno GUI otwarte.")
    root.mainloop()

def create_company_view(parent_frame, data, bg_color):
    # Podział na lewo (wykres) i prawo (tabela)
    left_frame = ttk.Frame(parent_frame)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    right_frame = ttk.Frame(parent_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # --- DANE ---
    data_sorted = sorted(data, key=lambda x: x.get('share', 0), reverse=True)
    TOP_N = 12
    labels = []
    sizes = []
    
    for company in data_sorted[:TOP_N]:
        labels.append(company.get('ticker', 'N/A'))
        sizes.append(company.get('share', 0.0))
        
    remaining = data_sorted[TOP_N:]
    if remaining:
        remaining_share = sum(c.get('share', 0) for c in remaining)
        labels.append(f"Pozostałe ({len(remaining)})")
        sizes.append(remaining_share)

    # --- WYKRES ---
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor(bg_color) # Tło figury
    
    colors = plt.cm.tab20c.colors
    slice_colors = list(colors[:len(sizes)])
    if "Pozostałe" in str(labels[-1]):
        slice_colors[-1] = (0.5, 0.5, 0.5, 1.0) # Szary dla pozostałych
    
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%', startangle=140, pctdistance=0.85,
        colors=slice_colors, wedgeprops=dict(width=0.4, edgecolor=bg_color)
    )
    plt.setp(texts, size=9, color="white")
    plt.setp(autotexts, size=8, weight="bold", color="black") # Czarne na kolorowym tle
        
    ax.set_title(f'Top Spółki (Wg Udziału)', fontsize=12, fontweight='bold', color='white')
    
    canvas = FigureCanvasTkAgg(fig, master=left_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # --- TABELA ---
    lbl = ttk.Label(right_frame, text="Lista Spółek", font=("Arial", 12, "bold"))
    lbl.pack(pady=5)
    
    columns = ("lp", "ticker", "sector", "share")
    tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=30)
    tree.heading("lp", text="Lp.")
    tree.heading("ticker", text="Ticker")
    tree.heading("sector", text="Sektor (Pobrany)") 
    tree.heading("share", text="Udział %")
    
    tree.column("lp", width=40, anchor="center")
    tree.column("ticker", width=80, anchor="center")
    tree.column("sector", width=150, anchor="center")
    tree.column("share", width=70, anchor="center")
    
    scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    for idx, company in enumerate(data_sorted, 1):
        tick = company.get('ticker')
        # Sektor już powinien być w słowniku dzięki enrich_data_with_sectors
        sec = company.get('sector', 'Analiza...')
        tree.insert("", tk.END, values=(idx, tick, sec, f"{company.get('share')}%"))

def create_sector_view(parent_frame, data, bg_color):
    # Agregacja danych wg sektorów
    sectors_map = {}
    
    for company in data:
        share = company.get('share', 0.0)
        sec_name = company.get('sector', 'Nieznany')
        
        if sec_name not in sectors_map:
            sectors_map[sec_name] = 0.0
        sectors_map[sec_name] += share
        
    # Sortowanie sektorów
    sorted_sectors = sorted(sectors_map.items(), key=lambda x: x[1], reverse=True)
    
    # --- GUI Layout ---
    left_frame = ttk.Frame(parent_frame)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    right_frame = ttk.Frame(parent_frame)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # --- WYKRES SEKTOROWY ---
    labels = [s[0] for s in sorted_sectors]
    sizes = [s[1] for s in sorted_sectors]
    
    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor(bg_color)
    
    colors = plt.cm.Set3.colors 
    
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%', startangle=140, pctdistance=0.85,
        colors=colors, wedgeprops=dict(width=0.4, edgecolor=bg_color)
    )
    plt.setp(texts, size=9, color='white')
    plt.setp(autotexts, size=8, weight="bold", color="black")
    
    ax.set_title(f'Podział Wg Sektorów', fontsize=12, fontweight='bold', color='white')
    
    canvas = FigureCanvasTkAgg(fig, master=left_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    # --- TABELA SEKTORÓW ---
    lbl = ttk.Label(right_frame, text="Ranking Sektorów", font=("Arial", 12, "bold"))
    lbl.pack(pady=5)
    
    columns = ("lp", "sector", "total_share")
    tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=20)
    tree.heading("lp", text="Lp.")
    tree.heading("sector", text="Sektor")
    tree.heading("total_share", text="Łączny Udział %")
    
    tree.column("lp", width=50, anchor="center")
    tree.column("sector", width=200, anchor="w")
    tree.column("total_share", width=100, anchor="center")
    
    scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    for idx, (sec, share) in enumerate(sorted_sectors, 1):
        tree.insert("", tk.END, values=(idx, sec, f"{share:.2f}%"))

def main():
    print("--- Start Programu sWIG80 Analyzer ---")
    
    # 1. Sprawdzamy czy wymagana aktualizacja (Scheduler)
    # Daty rewizji: 3. piątek marca, czerwca, września, grudnia
    last_update = get_last_portfolio_date()
    needs_update = should_update_portfolio(last_update)
    
    data = []
    
    if needs_update:
        print(f">>> Wymagana aktualizacja danych (Ostatnia aktualizacja: {last_update}).")
        print(">>> Pobieranie aktualnej listy z GPW Benchmark...")
        
        # 1.1 Pobieranie z GPW (Live)
        # fetch_gpw_data() zwraca listę słowników {'ticker', 'share', 'name'}
        raw_data = fetch_gpw_data()
        
        if raw_data:
            print(f">>> Pobrano {len(raw_data)} spółek.")
            
            # 1.2 Wzbogacanie o sektory (AI / Cache / Static)
            data = enrich_data_with_sectors(raw_data)
            
            # 1.3 Zapis do bazy (Snapshot portfela)
            save_portfolio_snapshot(data)
            print(">>> Dane zaktualizowane i zapisane w bazie danych.")
            
        else:
            print("!!! Błąd pobierania danych. Próbuję wczytać ostatnie znane z bazy...")
            data = load_portfolio_from_db()
    else:
        print(f">>> Dane w bazie są aktualne (z dnia {last_update}). Wczytuję z SQLite (błyskawicznie).")
        data = load_portfolio_from_db()
    
    if data:
        create_gui(data)
    else:
        print("Brak danych do wyświetlenia. Uruchom program ponownie gdy dostępny będzie internet lub sprawdź błędy.")

if __name__ == "__main__":
    main()