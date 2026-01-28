import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import load_portfolio_from_db

# --- STYLING CONSTANTS ---
BG_COLOR = "#2b2b2b"
FG_COLOR = "#ffffff"
ROW_EVEN_BG = "#333333"
ROW_ODD_BG = "#2b2b2b"

class BaseDashboardFrame(ttk.Frame):
    """Helper class for common dashboard functions"""
    def create_treeview(self, parent, columns):
        container = tk.Frame(parent, bg=BG_COLOR)
        container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree = ttk.Treeview(
            container, 
            columns=columns, 
            show='headings', 
            yscrollcommand=scrollbar.set,
            style="Dark.Treeview"
        )
        
        scrollbar.config(command=tree.yview)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Tags for striping
        tree.tag_configure('odd', background=ROW_ODD_BG, foreground=FG_COLOR)
        tree.tag_configure('even', background=ROW_EVEN_BG, foreground=FG_COLOR)
        
        return tree

    def create_figure(self, parent):
        fig, ax = plt.subplots(figsize=(5, 4))
        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return fig, ax, canvas

    def populate_tree(self, tree, data):
        # Clear old
        for item in tree.get_children():
            tree.delete(item)
            
        for i, c in enumerate(data):
            tag = 'even' if i % 2 == 0 else 'odd'
            tree.insert("", tk.END, values=(
                c.get('ticker', ''),
                c.get('sector', ''),
                f"{c.get('price', 0.0):.2f}",
                f"{c.get('change_pct', 0.0):+.2f}%",
                f"{c.get('share', 0.0):.2f}%"
            ), tags=(tag,))

# --- HELPER: Shared Colors ---
def get_sector_colors(sectors_list):
    """
    Returns a dictionary {sector_name: hex_color} using tab20.
    sectors_list should be sorted by size/importance.
    """
    cmap = plt.get_cmap("tab20")
    colors = {}
    for i, sector in enumerate(sectors_list):
        # Cycle through 20 colors
        colors[sector] = cmap(i % 20)
    return colors

# --- TAB 1: Index Composition (Chart Left + Table Right) ---
class IndexTab(BaseDashboardFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)

        # Split: Left (Chart), Right (Table)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left: Chart
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        self.fig, self.ax, self.canvas = self.create_figure(left_frame)

        # Right: Table
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        img_label = ttk.Label(right_frame, text="Tabela Spółek", background=BG_COLOR, foreground="white", font=('Helvetica', 12, 'bold'))
        img_label.pack(pady=5)
        
        cols = ("Ticker", "Sector", "Price", "Change %", "Share %")
        self.tree = self.create_treeview(right_frame, cols)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80)
        self.tree.column("Sector", width=120)
        
        self.update_view()

    def update_view(self):
        data = load_portfolio_from_db()
        if not data: return
        
        # 1. Tree: Sorted by Share Desc
        data_sorted = sorted(data, key=lambda x: x.get('share', 0), reverse=True)
        self.populate_tree(self.tree, data_sorted)
        
        # 2. Chart: Top 10 Companies (Colored by SECTOR)
        self.ax.clear()
        
        # Identify Sectors and Colors first to be consistent
        # We need the full sector list to generate the "canonical" colors
        all_sectors = {}
        for c in data:
            sec = c.get('sector', 'Inne')
            all_sectors[sec] = all_sectors.get(sec, 0) + c.get('share', 0)
        
        sorted_sector_names = [x[0] for x in sorted(all_sectors.items(), key=lambda x: x[1], reverse=True)]
        sector_colors = get_sector_colors(sorted_sector_names)
        
        top_n = 10
        top_comps = data_sorted[:top_n]
        rest_comps = data_sorted[top_n:]
        
        labels = []
        sizes = []
        
        for c in top_comps:
            labels.append(c['ticker'])
            sizes.append(c.get('share', 0))
            
        # Unique colors for every company (User request: "każda spółka inny kolor")
        cmap = plt.get_cmap("tab20")
        colors = [cmap(i) for i in range(len(sizes))]
        
        rest_share = sum(c.get('share', 0) for c in rest_comps)
        if rest_share > 0:
            labels.append("Inne")
            sizes.append(rest_share)
            colors.append("#a0a0a0") # Lighter/Brighter Grey
            
        self.ax.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            startangle=140,
            textprops=dict(color="white", fontsize=8),
            pctdistance=0.85,
            colors=colors
        )
        self.ax.set_title("Top 10 Spółek", color='white', fontweight='bold')
        self.ax.add_artist(plt.Circle((0,0),0.70,fc=BG_COLOR))
        self.canvas.draw()


# --- TAB 2: Sectors (Sector Chart + Table) ---
class SectorsTab(BaseDashboardFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        
        # Split: Left (Pie), Right (Table)
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left: Chart
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        self.fig, self.ax, self.canvas = self.create_figure(left_frame)

        # Right: Table
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        lbl = ttk.Label(right_frame, text="Spółki wg Sektorów", background=BG_COLOR, foreground="white", font=('Helvetica', 12, 'bold'))
        lbl.pack(pady=5)
        
        cols = ("Ticker", "Sector", "Price", "Change %", "Share %")
        self.tree = self.create_treeview(right_frame, cols)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80)
        self.tree.column("Sector", width=120)

        self.update_view()

    def update_view(self):
        data = load_portfolio_from_db()
        if not data: return
        
        # 1. Chart: Sectors
        self.ax.clear()
        sectors = {}
        for c in data:
            sec = c.get('sector', 'Inne')
            sectors[sec] = sectors.get(sec, 0) + c.get('share', 0)
        
        sorted_sectors_items = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
        sorted_sector_names = [x[0] for x in sorted_sectors_items]
        
        sector_colors = get_sector_colors(sorted_sector_names)
        
        labels = sorted_sector_names
        sizes = [x[1] for x in sorted_sectors_items]
        colors = [sector_colors.get(x, "#a0a0a0") for x in labels]
        
        self.ax.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            startangle=140,
            textprops=dict(color="white", fontsize=8),
            pctdistance=0.85,
            colors=colors
        )
        self.ax.set_title("Struktura Sektorowa", color='white', fontweight='bold')
        self.ax.add_artist(plt.Circle((0,0),0.70,fc=BG_COLOR))
        self.canvas.draw()
        
        # 2. Tree: Sorted by Sector, then Share
        # Sort key tuple: (Sector Name, Share Descending)
        # Note: to sort share desc inside sector, we negate share
        data_sorted = sorted(data, key=lambda x: (x.get('sector', 'ZZZ'), -x.get('share', 0)))
        self.populate_tree(self.tree, data_sorted)
