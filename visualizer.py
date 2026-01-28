import matplotlib.pyplot as plt
import matplotlib.patches as patches
import squarify
from matplotlib.colors import Normalize
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import time

# Import database functions to read buffer
from database import load_portfolio_from_db

class HeatMapVisualizer(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        
        # Create Figure
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#2b2b2b')
        
        # Adjust margins to maximize map size
        # title space at top=0.94, date space at bottom=0.02
        self.fig.subplots_adjust(left=0.00, right=1.00, top=0.94, bottom=0.00)
        
        # Embed in Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Initial draw
        self.update_plot()

    def get_color(self, value):
        """
        Returns hex color based on percentage change (Finviz style).
        """
        if value is None:
            return "#4b4b4b" 
        if value == 0:
            return "#4b4b4b"
            
        if value > 0:
            if value >= 3.0: return "#1a9641" # Bright Green
            elif value >= 2.0: return "#35b758"
            elif value >= 1.0: return "#397d49"
            else: return "#285233"
        else:
            if value <= -3.0: return "#d7191c" # Bright Red
            elif value <= -2.0: return "#bd3336"
            elif value <= -1.0: return "#962f32"
            else: return "#5e2628"

    def update_plot(self):
        """
        Reads data and draws a HIERARCHICAL Treemap (Sector -> Company).
        """
        data = load_portfolio_from_db()
        if not data:
            return

        # 1. Filter and Prepare
        data = [c for c in data if c.get('share', 0) > 0]
        
        # 2. Group by Sector
        sectors = {}
        for c in data:
            sec = c.get('sector', 'Inne')
            if sec not in sectors:
                sectors[sec] = []
            sectors[sec].append(c)
            
        # 3. Calculate Sector Totals and Sort
        sector_list = [] # List of tuples (name, total_share, companies_list)
        for sec_name, comps in sectors.items():
            total = sum(c.get('share', 0) for c in comps)
            # Sort companies within sector by share descending
            comps.sort(key=lambda x: x.get('share', 0), reverse=True)
            sector_list.append({'name': sec_name, 'total': total, 'companies': comps})
            
        # Sort sectors by total share descending
        sector_list.sort(key=lambda x: x['total'], reverse=True)
        
        # 4. Layout Calculation
        
        # Canvas dimensions (0..100, 0..100)
        X, Y, DX, DY = 0, 0, 100, 100
        
        # Calculate Level 1 (Sectors)
        sector_shares = [s['total'] for s in sector_list]
        # Normalize to cover full canvas
        normed_sectors = squarify.normalize_sizes(sector_shares, DX, DY)
        sector_rects = squarify.squarify(normed_sectors, X, Y, DX, DY)
        
        # 5. Drawing
        self.ax.clear()
        self.ax.set_facecolor('#2b2b2b')
        self.ax.axis('off')
        
        # Set limits manually since manual patches depend on it
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 100)
        
        for i, rect in enumerate(sector_rects):
            sec_data = sector_list[i]
            x, y, dx, dy = rect['x'], rect['y'], rect['dx'], rect['dy']
            
            # Draw Sector Border (optional, mainly just space for nested items)
            # We can draw a subtle border for the sector
            self.ax.add_patch(
                patches.Rectangle((x, y), dx, dy, linewidth=2, edgecolor='#1a1a1a', facecolor='none', zorder=10)
            )
            
            # --- Draw Sector Label (Top Left) ---
            # dynamic font size based on sector size
            # --- Draw Sector Label (Top Left) ---
            # dynamic font size based on sector size
            # Show label even if smaller, just scale font or clip
            if dx > 1 or dy > 1: # Practically always
                # Calculate reasonable font size
                lbl_size = min(12, int(dx/2)) 
                lbl_size = max(8, lbl_size)
                
                self.ax.text(x + 0.5, y + dy - 0.5, sec_data['name'], 
                             color='white', fontsize=lbl_size, fontweight='bold', ha='left', va='top', zorder=20,
                             bbox=dict(facecolor='black', alpha=0.4, edgecolor='none', pad=2))
            
            # Level 2 (Companies within Sector)
            comps = sec_data['companies']
            comp_shares = [c.get('share', 0) for c in comps]
            
            # Squarify inside the sector rectangle
            # Normalize for the sub-rectangle
            normed_comps = squarify.normalize_sizes(comp_shares, dx, dy)
            comp_rects = squarify.squarify(normed_comps, x, y, dx, dy)
            
            for j, crect in enumerate(comp_rects):
                comp = comps[j]
                cx, cy, cdx, cdy = crect['x'], crect['y'], crect['dx'], crect['dy']
                
                # Color
                pct = comp.get('change_pct', 0.0)
                color = self.get_color(pct)
                
                # Draw Box
                self.ax.add_patch(
                    patches.Rectangle((cx, cy), cdx, cdy, linewidth=1, edgecolor='#2b2b2b', facecolor=color)
                )
                
                # Label
                if cdx > 3 and cdy > 3:
                    fsize = 8 if cdx < 6 else 10
                    lbl = f"{comp['ticker']}\n{pct:+.1f}%"
                    self.ax.text(cx + cdx/2, cy + cdy/2, lbl, 
                                 color='white', fontsize=fsize, fontweight='bold', ha='center', va='center')

        # Static Title Top Center
        self.ax.set_title("sWIG80tr Map", fontsize=16, color='white', fontweight='bold', pad=10)
        
        # Dynamic Timestamp Bottom Right (using Axes coordinates 0..1)
        # 1.0, 0.0 is bottom right. We offset slightly up.
        last_update_str = time.strftime("%H:%M:%S")
        self.ax.text(0.99, 0.01, f"Aktualizacja: {last_update_str}", 
                     transform=self.ax.transAxes,
                     color='#aaaaaa', fontsize=10, ha='right', va='bottom',
                     bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', pad=2))

        self.canvas.draw()
