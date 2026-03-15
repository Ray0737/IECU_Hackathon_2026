import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import math

# --- Constants & Dimensions ---
# Total Storage Dimensions (from layout)
WH_LENGTH = 5000  # cm
WH_WIDTH = 5000  # Corrected to 5000 to match component sum (200+500+3600+500+200)
WH_HEIGHT = 700  # cm
WH_AREA_M2 = (WH_LENGTH / 100) * (WH_WIDTH / 100)  # 2000 m2

# Specific Area Dimensions
DOCK_WIDTH = 200 # cm
STAGING_WIDTH = 500 # cm
WEST_STAGING_X = DOCK_WIDTH
EAST_STAGING_X = WH_WIDTH - STAGING_WIDTH
STORAGE_AREA_WIDTH = 3600 # cm
STORAGE_AREA_X = WEST_STAGING_X + STAGING_WIDTH

# Rack Data
NUM_RACKS = 25
RACK_WIDTH = 100  # cm
RACK_LENGTH = 3600 # cm
FORKLIFT_TRACK_WIDTH = 100 # cm

# SKUs (Data is pre-set based on user's input/image)
SKUS = {
    'A': {'length': 100, 'width': 100, 'height': 200},
    'B': {'length': 100, 'width': 100, 'height': 50},
    'C': {'length': 100, 'width': 80, 'height': 150},
    'D': {'length': 100, 'width': 100, 'height': 200},
    'E': {'length': 100, 'width': 80, 'height': 150},
    'F': {'length': 100, 'width': 80, 'height': 150},
    'G': {'length': 100, 'width': 100, 'height': 50},
    'H': {'length': 100, 'width': 80, 'height': 200},
}

# --- Advanced Data Management ---
# Custom Rack Assignments (based on user request)
RACK_CONFIGS = {
    'H': {'racks': list(range(1, 15)), 'skus': ['H'], 'target': 1890, 'max': 1890, 'per_lvl': 45, 'lvls': 3},
    'AD': {'racks': list(range(15, 17)), 'skus': ['A', 'D'], 'target': 205, 'max': 216, 'per_lvl': 36, 'lvls': 3},
    'CEF': {'racks': list(range(17, 23)), 'skus': ['C', 'E', 'F'], 'target': 980, 'max': 1080, 'per_lvl': 45, 'lvls': 4},
    'BG': {'racks': list(range(23, 26)), 'skus': ['B', 'G'], 'target': 835, 'max': 972, 'per_lvl': 36, 'lvls': 9}
}

# User-specified Flow-In (Florin) Quantities
FLOW_IN_QUANTS = {
    'A': 20, 'B': 10, 'C': 45, 'D': 15, 'E': 30, 'F': 10, 'G': 35, 'H': 90
}

# --- Logistics Logic Engine Data ---
VEHICLE_SPECS = {
    '53FT_HC': {'length': 1600, 'width': 250, 'height': 270, 'name': '53ft High Cube'},
    '26FT_BOX': {'length': 790, 'width': 240, 'height': 240, 'name': '26ft Box Truck'}
}

# Daily Flow (Requirement for Booking Calculator)
DAILY_FLOW = FLOW_IN_QUANTS # Reusing the florin counts as daily flow

# Real-time inventory tracking (SKU -> Quantity)
sku_inventory = {s: 0 for s in SKUS.keys()}

# Docks initialization (needed by GUI logic)
docks = {f'East Dock {i+1}': {'vehicle': None, 'type': 'Input', 'items': None} for i in range(25)}
docks.update({f'West Dock {i+1}': {'vehicle': None, 'type': 'Output', 'items': None} for i in range(25)} )

# Track active operations
transaction_log = []
active_loadings = {} # {Group: {'type': 'IN'/'OUT', 'qty_remaining': int, 'sku': str, 'docks': [names]}}
rack_inventory = {i + 1: 0 for i in range(NUM_RACKS)} # Total items per rack
rack_sku_counts = {i + 1: {} for i in range(NUM_RACKS)} # Specific SKU counts per rack

class WarehouseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("A-H Warehouse Cross-Docking & Stock WMS")
        self.root.geometry("1400x900")

        # --- Initialize Attributes ---
        self.booking_sku_var = tk.StringVar(value='H')
        self.booking_veh_var = tk.StringVar(value='26FT_BOX')
        self.manual_sku_var = tk.StringVar()
        self.manual_qty_var = tk.StringVar()
        self.calc_sku_var = tk.StringVar()
        
        self.canvas = None
        self.v_scroll = None
        self.h_scroll = None
        self.dock_rects = {} # ID -> name
        self.canvas_docks = {} # name -> ID
        
        self.dashboard_tree = ttk.Treeview(self.root)
        self.group_tree = ttk.Treeview(self.root)
        self.booking_result_lbl = ttk.Label(self.root)
        self.calc_output_area = tk.Text(self.root)
        self.transaction_listbox = tk.Listbox(self.root)
        self.heat_grid_frame = ttk.Frame(self.root)
        self.left_frame = ttk.Frame(self.root)
        self.right_frame = ttk.Frame(self.root)
        self.stock_left_frame = ttk.Frame(self.root)
        self.stock_right_frame = ttk.Frame(self.root)
        self.stock_left_legend = ttk.LabelFrame(self.root)
        self.canvas_frame = ttk.Frame(self.root)
        self.stats_panel = ttk.LabelFrame(self.root)
        self.canvas = tk.Canvas(self.root)
        self.wh_scale = 0.3

        # Define Notebook/Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True, fill="both")

        # --- Window 01: Layout & Transport ---
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="01 - Layout & Transport")
        self.create_layout_tab()

        # --- Window 02: Stock Management ---
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="02 - Stock Management")
        self.create_stock_tab()

    # =========================================================================
    # ======================== TAB 01: LAYOUT & TRANSPORT ======================
    # =========================================================================

    def create_layout_tab(self):
        # PanedWindow for split layout
        pane = tk.PanedWindow(self.tab1, orient=tk.HORIZONTAL)
        pane.pack(expand=True, fill="both")

        # --- Left Panel: Vehicle Input ---
        self.left_frame = ttk.Frame(pane, padding=10)
        pane.add(self.left_frame)

        # --- Booking Calculator (Logistics Logic Engine) ---
        calc_group = ttk.LabelFrame(self.left_frame, text="Logistics Logic Engine (Booking)", padding=10)
        calc_group.pack(fill='x', pady=10)

        ttk.Label(calc_group, text="Select SKU:").grid(row=0, column=0, sticky='w')
        self.booking_sku_combo = ttk.Combobox(calc_group, textvariable=self.booking_sku_var, values=list(SKUS.keys()), width=10)
        self.booking_sku_combo.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(calc_group, text="Vehicle:").grid(row=1, column=0, sticky='w')
        self.booking_veh_combo = ttk.Combobox(calc_group, textvariable=self.booking_veh_var, values=list(VEHICLE_SPECS.keys()), width=15)
        self.booking_veh_combo.grid(row=1, column=1, padx=5, pady=2)

        ttk.Button(calc_group, text="Calculate Booking", command=self.calculate_vehicle_booking).grid(row=2, column=0, pady=10)
        ttk.Button(calc_group, text="Execute Booking", command=self.execute_booking).grid(row=2, column=1, pady=10)

        self.booking_result_lbl = ttk.Label(calc_group, text="Result: --", font=('Helvetica', 10, 'bold'), foreground='blue')
        self.booking_result_lbl.grid(row=3, column=0, columnspan=2, sticky='w')

        # --- Group Summary (Simulation Context) ---
        summary_group = ttk.LabelFrame(self.left_frame, text="Rack Group Summaries", padding=10)
        summary_group.pack(fill='x', pady=10)
        
        summary_text = (
            "H Rack: 135 | x14 rack\n"
            "D 108\n"
            "D 57 + A40\n"
            "C180 x4 rack\n"
            "E180 | F80\n"
            "G201 | G324 | B324"
        )
        ttk.Label(summary_group, text=summary_text, justify=tk.LEFT, font=('Arial', 9)).pack(anchor='w')

        # Log Display
        ttk.Label(self.left_frame, text="Today's Transaction Log", font=('Helvetica', 10, 'bold')).pack(anchor='nw', pady=(20, 0))
        self.transaction_listbox = tk.Listbox(self.left_frame, height=25)
        self.transaction_listbox.pack(fill='both', expand=True, pady=5)

        # --- Right Panel: Interactive Dock Layout & Legend ---
        self.right_frame = ttk.Frame(pane, padding=10)
        pane.add(self.right_frame)

        # Setup Canvas
        self.canvas_frame = ttk.Frame(self.right_frame)
        self.canvas_frame.pack(side=tk.TOP, fill='both', expand=True)

        self.wh_scale = 0.3 # Adjusted for a more compact yet readable view
        
        # Add Scrollbars
        self.v_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self.canvas_frame, width=800, height=600, bg="white", 
                                yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.canvas.pack(side=tk.LEFT, expand=True, fill="both")
        
        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.draw_warehouse_structure()

        # Legend/Stats Panel
        self.stats_panel = ttk.LabelFrame(self.right_frame, text="Legend & Active Docks", padding=10)
        self.stats_panel.pack(side=tk.BOTTOM, fill='x', pady=10)
        
        self.draw_legend()

    # ======================== TAB 01 Drawing =================================

    def draw_warehouse_structure(self):
        self.canvas.delete("all")
        s = self.wh_scale
        margin = 50 # Fixed margin for scrollable area

        # 1. Main WH Outline
        wh_x1, wh_y1 = margin, margin
        wh_x2, wh_y2 = margin + WH_WIDTH * s, margin + WH_LENGTH * s
        
        self.canvas.create_rectangle(wh_x1, wh_y1, wh_x2, wh_y2, fill="lightgrey", outline="black", width=2)

        # 2. Area Outlines (No Labels)
        def rel_outline(x, y, w, h, fill, outline):
            coords = (margin + x * s, margin + y * s, margin + (x + w) * s, margin + (y + h) * s)
            self.canvas.create_rectangle(coords, fill=fill, outline=outline, width=1)

        # Base Areas
        rel_outline(WH_WIDTH - DOCK_WIDTH, 0, DOCK_WIDTH, WH_LENGTH, "lightgrey", "black")
        rel_outline(WH_WIDTH - DOCK_WIDTH - STAGING_WIDTH, 0, STAGING_WIDTH, WH_LENGTH, "khaki", "black")
        rel_outline(0, 0, DOCK_WIDTH, WH_LENGTH, "lightgrey", "black")
        rel_outline(DOCK_WIDTH, 0, STAGING_WIDTH, WH_LENGTH, "khaki", "black")
        rel_outline(STORAGE_AREA_X, 0, STORAGE_AREA_WIDTH, WH_LENGTH, "white", "black")

        # 3. Interactive Docks, 4. Staging Squares & 5. Racks (Aligned Symmetry)
        rack_y_start = 100 # cm from top
        forklift_gap_cm = 100 # cm

        for i in range(NUM_RACKS):
            rack_num = i + 1
            y_top_cm = rack_y_start + i * (RACK_WIDTH + forklift_gap_cm)
            
            y1 = margin + y_top_cm * s
            y2 = y1 + RACK_WIDTH * s
            
            # --- East Side: Dock -> Staging ---
            # Dock Square - Wider to hold text better
            xe_dock1, xe_dock2 = margin + (WH_WIDTH - DOCK_WIDTH + 20) * s, margin + (WH_WIDTH - 20) * s
            rect_e = self.canvas.create_rectangle(xe_dock1, y1, xe_dock2, y2, fill="white", outline="black", width=2, tags=("dock", f"East Dock {rack_num}"))
            self.canvas_docks[f'East Dock {rack_num}'] = rect_e
            self.dock_rects[rect_e] = f'East Dock {rack_num}'
            self.canvas.create_text((xe_dock1 + xe_dock2) / 2, (y1 + y2) / 2, text=f"E{rack_num}", font=('Arial', 9, 'bold'))
            
            # Staging Square (East)
            xe_stag1, xe_stag2 = margin + (WH_WIDTH - DOCK_WIDTH - STAGING_WIDTH + 100) * s, margin + (WH_WIDTH - DOCK_WIDTH - 100) * s
            self.canvas.create_rectangle(xe_stag1, y1, xe_stag2, y2, fill="yellow", outline="black")

            # --- West Side: Dock -> Staging ---
            # Dock Square - Wider to hold text better
            xw_dock1, xw_dock2 = margin + 20 * s, margin + (DOCK_WIDTH - 20) * s
            rect_w = self.canvas.create_rectangle(xw_dock1, y1, xw_dock2, y2, fill="white", outline="black", width=2, tags=("dock", f"West Dock {rack_num}"))
            self.canvas_docks[f'West Dock {rack_num}'] = rect_w
            self.dock_rects[rect_w] = f'West Dock {rack_num}'
            self.canvas.create_text((xw_dock1 + xw_dock2) / 2, (y1 + y2) / 2, text=f"W{rack_num}", font=('Arial', 9, 'bold'))
            
            # Staging Square (West)
            xw_stag1, xw_stag2 = margin + (DOCK_WIDTH + 100) * s, margin + (DOCK_WIDTH + STAGING_WIDTH - 100) * s
            self.canvas.create_rectangle(xw_stag1, y1, xw_stag2, y2, fill="yellow", outline="black")

            # --- Center: Racks ---
            xr1, xr2 = margin + STORAGE_AREA_X * s, margin + (STORAGE_AREA_X + STORAGE_AREA_WIDTH) * s
            rect_r = self.canvas.create_rectangle(xr1, y1, xr2, y2, fill="darkgreen", outline="darkgrey")
            self.canvas.itemconfigure(rect_r, tags=(f"rack_{rack_num}",))
            
            # --- Uniform Rack Labels [R#-Class-Qty] ---
            txt_center = (xr1 + xr2) / 2
            txt_y = (y1 + y2) / 2
            label_font = ('Arial', 9, 'bold')
            label_color = "white"

            # Determine loading suffix
            loading_suffix = ""
            for g_name, l_data in active_loadings.items():
                if rack_num in RACK_CONFIGS[g_name]['racks']:
                    loading_suffix = f"\n[LOADING {l_data['type']}]"
                    break

            # Determine group class
            group_class = "RACK"
            for g, config in RACK_CONFIGS.items():
                if rack_num in config['racks']:
                    group_class = g
                    break
            
            # Get status from rack_sku_counts
            sku_counts = rack_sku_counts.get(rack_num, {})
            # Format as "A20 + D15" or just "35"
            sku_parts = [f"{s}{q}" for s, q in sku_counts.items() if q > 0]
            sku_display = " + ".join(sku_parts) if sku_parts else "0"
            
            rack_label = f"[R{rack_num}-{group_class}-{sku_display}]{loading_suffix}"
            self.canvas.create_text(txt_center, txt_y, text=rack_label, font=label_font, fill=label_color)

        # Update scrollregion
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Canvas Click Binding (for docks)
        self.canvas.tag_bind("dock", "<Button-1>", self.on_dock_click)

    def draw_legend(self):
        ttk.Label(self.stats_panel, text="Vehicle Status Legend", font=('Helvetica', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        
        legend_colors = [("Empty/Waiting", "white"), ("Loading/Unloading", "skyblue"), ("Full/Assigned", "tomato")]
        for text, color in legend_colors:
            f = ttk.Frame(self.stats_panel)
            f.pack(side=tk.LEFT, padx=10)
            tk.Label(f, bg=color, width=3, height=1, borderwidth=1, relief="solid").pack(side=tk.LEFT)
            ttk.Label(f, text=f" = {text}").pack(side=tk.LEFT, padx=(5, 0))

    # ======================== TAB 01 Functionality ============================

    def on_dock_click(self, event):
        # Find which visual element was clicked
        item_id = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item_id)
        
        dock_name = next((t for t in tags if "Dock" in t), None)
        
        if not dock_name: return

        dock_data = docks[dock_name]
        v_assigned = dock_data['vehicle'] if dock_data['vehicle'] else "Empty"
        item_assigned = dock_data['items'] if dock_data['items'] else "None"
        
        msg = f"Dock: {dock_name}\nType: {dock_data['type']}\n\nAssigned Vehicle: {v_assigned}\nItems: {item_assigned}"
        
        if dock_data['vehicle']:
            msg += "\n\nClear Dock?"
            if messagebox.askyesno("Dock Activity", msg):
                docks[dock_name]['vehicle'] = None
                docks[dock_name]['items'] = None
                self.update_dock_visuals()
                self.add_transaction_log(f"{dock_name} cleared of {v_assigned}")
        else:
            messagebox.showinfo("Dock Info", msg)

    def update_dock_visuals(self):
        for dock_name, dock_data in docks.items():
            if dock_name in self.canvas_docks:
                visual_id = self.canvas_docks[dock_name]
                
                new_color = "white"
                if dock_data['vehicle']:
                    if dock_data['vehicle'] == 'LOADING':
                        new_color = "skyblue"
                    else:
                        new_color = "tomato" # Occupied/Assigned
                
                self.canvas.itemconfigure(visual_id, fill=new_color)

    def add_transaction_log(self, text):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.transaction_listbox.insert(tk.END, f"[{now}] {text}")
        self.transaction_listbox.see(tk.END) # Scroll to bottom

    # =========================================================================
    # ======================== TAB 02: STOCK MANAGEMENT ========================
    # =========================================================================

    def create_stock_tab(self):
        # 1. Main PanedWindow for split layout
        stock_pane = tk.PanedWindow(self.tab2, orient=tk.HORIZONTAL)
        stock_pane.pack(expand=True, fill="both")

        # --- Left Frame: Rack Statistics Dashboard (Heatmap) ---
        self.stock_left_frame = ttk.Frame(stock_pane, padding=10)
        stock_pane.add(self.stock_left_frame)

        ttk.Label(self.stock_left_frame, text="Warehouse Rack Capacity Monitor (Heatmap)", font=('Helvetica', 14, 'bold')).pack(anchor='nw', pady=(0, 15))
        
        # Grid of labels for the racks (represented by color/percent)
        self.heat_grid_frame = ttk.Frame(self.stock_left_frame)
        self.heat_grid_frame.pack(side=tk.LEFT, fill='both', expand=True, pady=10)
        
        self.draw_rack_heatmap()

        # Legend Panel
        self.stock_left_legend = ttk.LabelFrame(self.stock_left_frame, text="Capacity Legend", padding=10)
        self.stock_left_legend.pack(side=tk.BOTTOM, fill='x', pady=10)
        
        heatmap_colors = [("0-25%", "lightgrey"), ("26-50%", "lightskyblue"), ("51-75%", "gold"), ("76-100%", "lightcoral")]
        for text, color in heatmap_colors:
            f = ttk.Frame(self.stock_left_legend)
            f.pack(side=tk.LEFT, padx=15)
            tk.Label(f, bg=color, width=4, height=1, borderwidth=1, relief="solid").pack(side=tk.LEFT)
            ttk.Label(f, text=f" = {text}").pack(side=tk.LEFT, padx=(5, 0))

        # --- Right Frame: Stock Analysis Calculator ---
        self.stock_right_frame = ttk.Frame(stock_pane, padding=10)
        stock_pane.add(self.stock_right_frame)

        # 2. SKU Status Dashboard (Advanced Tracking)
        self.dashboard_frame = ttk.LabelFrame(self.stock_right_frame, text="2. SKU Detail Dashboard (Fixed Flow Value)", padding=10)
        self.dashboard_frame.pack(fill='both', expand=True, pady=5)
        
        self.dashboard_tree = ttk.Treeview(self.dashboard_frame, columns=("SKU", "Current", "Flows", "Target", "Max"), show='headings', height=8)
        self.dashboard_tree.heading("SKU", text="SKU")
        self.dashboard_tree.heading("Current", text="Stock")
        self.dashboard_tree.heading("Flows", text="Flows In")
        self.dashboard_tree.heading("Target", text="Target")
        self.dashboard_tree.heading("Max", text="Max Cap")
        for col in ("SKU", "Current", "Flows", "Target", "Max"):
            self.dashboard_tree.column(col, width=55, anchor='center')
        self.dashboard_tree.pack(fill='both', expand=True)
        
        # 3. Rack Group Dashboard (Summary)
        self.group_dashboard_frame = ttk.LabelFrame(self.stock_right_frame, text="3. Rack Groups Status Summary", padding=10)
        self.group_dashboard_frame.pack(fill='x', pady=5)

        self.group_tree = ttk.Treeview(self.group_dashboard_frame, columns=("Group", "Items", "Target", "Fullness"), show='headings', height=4)
        self.group_tree.heading("Group", text="Rack Group")
        self.group_tree.heading("Items", text="Actual Items")
        self.group_tree.heading("Target", text="Target")
        self.group_tree.heading("Fullness", text="Fullness %")
        for col in ("Group", "Items", "Target", "Fullness"):
            self.group_tree.column(col, width=70, anchor='center')
        self.group_tree.pack(fill='x')

        self.update_inventory_display()

        # 4. Flow Management Controls (Add/Delete Florin)
        flow_frame = ttk.LabelFrame(self.stock_right_frame, text="4. Flow Management (+ /- Florin Value)", padding=10)
        flow_frame.pack(fill='x', pady=5)
        
        sku_grid = ttk.Frame(flow_frame)
        sku_grid.pack(fill='x')
        for i, sku in enumerate(sorted(SKUS.keys())):
            s_frame = ttk.Frame(sku_grid)
            s_frame.grid(row=i//2, column=i%2, sticky="ew", padx=5, pady=2)
            
            ttk.Label(s_frame, text=f"SKU-{sku}:", width=8).pack(side=tk.LEFT)
            ttk.Button(s_frame, text="+", width=3, command=lambda s=sku: self.add_sku_flow(s)).pack(side=tk.LEFT, padx=2)
            ttk.Button(s_frame, text="-", width=3, command=lambda s=sku: self.remove_sku_flow(s)).pack(side=tk.LEFT, padx=2)
            
        sku_grid.columnconfigure(0, weight=1)
        sku_grid.columnconfigure(1, weight=1)

        # 5. Manual Keyboard Entry (New Request)
        manual_frame = ttk.LabelFrame(self.stock_right_frame, text="5. Manual Transaction (Keyboard Qty)", padding=10)
        manual_frame.pack(fill='x', pady=5)

        ttk.Label(manual_frame, text="Qty:").pack(side=tk.LEFT, padx=2)
        self.manual_qty_entry = ttk.Entry(manual_frame, textvariable=self.manual_qty_var, width=8)
        self.manual_qty_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(manual_frame, text="SKU:").pack(side=tk.LEFT, padx=2)
        manual_cb = ttk.Combobox(manual_frame, textvariable=self.manual_sku_var, values=sorted(SKUS.keys()), width=4)
        manual_cb.pack(side=tk.LEFT, padx=2)

        ttk.Button(manual_frame, text="Key-In", command=self.add_manual_qty).pack(side=tk.LEFT, padx=5)
        ttk.Button(manual_frame, text="Erase", command=self.erase_manual).pack(side=tk.LEFT, padx=2)

        # Output Text Area (Further reduced height)
        self.calc_output_area = tk.Text(self.stock_right_frame, wrap=tk.WORD, height=8, width=40)
        self.calc_output_area.pack(pady=10, fill='both', expand=True)
        self.calc_output_area.tag_configure("bold", font=('Helvetica', 10, 'bold'))
        self.calc_output_area.tag_configure("red", foreground="red", font=('Helvetica', 11, 'bold'))

    # ======================== TAB 02 Functionality ============================

    def draw_rack_heatmap(self):
        # Clear previous heat grid frame contents
        for widget in self.heat_grid_frame.winfo_children():
            widget.destroy()

        # Group Colors for visibility
        group_colors = {'AD': '#e1f5fe', 'H': '#f3e5f5', 'CEF': '#e8f5e9', 'BG': '#fff3e0'}

        for row in range(5):
            self.heat_grid_frame.grid_rowconfigure(row, weight=1)
            for col in range(5):
                rack_idx = (row * 5) + col
                rack_num = rack_idx + 1
                
                # Determine which group this rack belongs to
                assigned_group = None
                for g_name, conf in RACK_CONFIGS.items():
                    if rack_num in conf['racks']:
                        assigned_group = g_name
                        break
                
                # Calculate usage % for that group
                if assigned_group:
                    conf = RACK_CONFIGS[assigned_group]
                    total_group_stock = sum(sku_inventory[s] for s in conf['skus'])
                    usage_percent = min(100, int((total_group_stock / conf['max']) * 100))
                    base_bg = group_colors[assigned_group]
                else:
                    usage_percent = 0
                    base_bg = "white"

                # Heatmap Intensity (redder if fuller)
                if usage_percent < 26: heat_color = base_bg
                elif usage_percent < 51: heat_color = "lightskyblue"
                elif usage_percent < 76: heat_color = "gold"
                else: heat_color = "lightcoral"

                f = tk.Frame(self.heat_grid_frame, bg=heat_color, borderwidth=1, relief="groove")
                f.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
                
                label_text = f"R#{rack_num}\n({assigned_group or 'FREE'})\n{usage_percent}%"
                tk.Label(f, text=label_text, font=('Helvetica', 8, 'bold'), 
                         bg=heat_color).pack(expand=True)

    def add_manual_qty(self):
        sku = self.manual_sku_var.get()
        qty_str = self.manual_qty_var.get()
        if not sku or not qty_str.isdigit():
            messagebox.showwarning("Input Error", "Please select a SKU and enter a valid quantity.")
            return
        
        qty = int(qty_str)
        # Capacity check
        assigned_group = None
        for g_name, conf in RACK_CONFIGS.items():
            if sku in conf['skus']:
                assigned_group = g_name
                break
        
        if assigned_group:
            curr_total = sum(sku_inventory[s] for s in RACK_CONFIGS[assigned_group]['skus'])
            if curr_total + qty > RACK_CONFIGS[assigned_group]['max']:
                if not messagebox.askyesno("Capacity Warning", f"Adding {qty} units exceeds {assigned_group} Max. Proceed?"):
                    return

            # Distribute items to racks
            remaining = qty
            config = RACK_CONFIGS[assigned_group]
            max_per_rack = config['per_lvl'] * config['lvls']
            for r_num in config['racks']:
                if remaining <= 0: break
                space = max_per_rack - rack_inventory[r_num]
                to_add = min(remaining, space)
                if to_add > 0:
                    rack_inventory[r_num] += to_add
                    rack_sku_counts[r_num][sku] = rack_sku_counts[r_num].get(sku, 0) + to_add
                    remaining -= to_add

            sku_inventory[sku] += qty
            self.update_inventory_display()
            self.add_transaction_log(f"Manual Key-In: +{qty} to SKU-{sku}")

    def erase_manual(self):
        sku = self.manual_sku_var.get()
        qty_str = self.manual_qty_var.get()
        if not sku or not qty_str.isdigit():
            messagebox.showwarning("Input Error", "Please select a SKU and enter a valid quantity.")
            return
        
        qty = int(qty_str)
        if sku_inventory[sku] - qty < 0:
            messagebox.showwarning("Inventory Error", f"Cannot erase {qty} units. Stock would become negative.")
            return

        # Find which group this SKU belongs to
        assigned_group = None
        for g_name, conf in RACK_CONFIGS.items():
            if sku in conf['skus']:
                assigned_group = g_name
                break
        
        if assigned_group:
            # Remove items from racks
            remaining = qty
            config = RACK_CONFIGS[assigned_group]
            for r_num in reversed(list(config['racks'])):
                if remaining <= 0: break
                available = rack_sku_counts[r_num].get(sku, 0)
                to_remove = min(remaining, available)
                if to_remove > 0:
                    rack_sku_counts[r_num][sku] -= to_remove
                    rack_inventory[r_num] -= to_remove
                    remaining -= to_remove

            sku_inventory[sku] -= qty
            self.update_inventory_display()
            self.add_transaction_log(f"Manual Erase: -{qty} from SKU-{sku}")

    def add_sku_flow(self, sku):
        # Find which group this SKU belongs to
        assigned_group = None
        for g_name, conf in RACK_CONFIGS.items():
            if sku in conf['skus']:
                assigned_group = g_name
                conf = RACK_CONFIGS[g_name]
                break
        
        if not assigned_group:
            messagebox.showerror("Error", f"SKU {sku} has no assigned rack group.")
            return

        # Use user-specified flow-in quantities (florin)
        flow_qty = FLOW_IN_QUANTS.get(sku, 0)
        
        # Check if addition exceeds group max
        current_group_total = sum(sku_inventory[s] for s in conf['skus'])
        if current_group_total + flow_qty > conf['max']:
            if not messagebox.askyesno("Capacity Warning", 
                f"Adding {flow_qty} units to {sku} exceeds Group {assigned_group} Max Capacity ({conf['max']}). Proceed with overflow?"):
                return

        # Distribute items to racks
        remaining = flow_qty
        max_per_rack = conf['per_lvl'] * conf['lvls']
        for r_num in conf['racks']:
            if remaining <= 0: break
            space = max_per_rack - rack_inventory[r_num]
            to_add = min(remaining, space)
            if to_add > 0:
                rack_inventory[r_num] += to_add
                rack_sku_counts[r_num][sku] = rack_sku_counts[r_num].get(sku, 0) + to_add
                remaining -= to_add

        sku_inventory[sku] += flow_qty
        self.update_inventory_display()
        self.add_transaction_log(f"Added Flow (+{flow_qty}) to SKU-{sku} (Group {assigned_group})")

    def remove_sku_flow(self, sku):
        # Find which group this SKU belongs to
        assigned_group = None
        for g_name, conf in RACK_CONFIGS.items():
            if sku in conf['skus']:
                assigned_group = g_name
                break
        
        if not assigned_group: return

        # Use user-specified flow-in quantities (florin)
        flow_qty = FLOW_IN_QUANTS.get(sku, 0)
        
        if sku_inventory[sku] - flow_qty < 0:
            messagebox.showwarning("Inventory Note", f"Cannot remove {flow_qty} units from SKU-{sku}. Stock would be negative.")
            return

        # Remove items from racks
        remaining = flow_qty
        config = RACK_CONFIGS[assigned_group]
        for r_num in reversed(list(config['racks'])):
            if remaining <= 0: break
            available = rack_sku_counts[r_num].get(sku, 0)
            to_remove = min(remaining, available)
            if to_remove > 0:
                rack_sku_counts[r_num][sku] -= to_remove
                rack_inventory[r_num] -= to_remove
                remaining -= to_remove

        sku_inventory[sku] -= flow_qty
        self.update_inventory_display()
        self.add_transaction_log(f"Deleted Flow (-{flow_qty}) from SKU-{sku} (Group {assigned_group})")

    def calculate_vehicle_booking(self):
        sku_code = self.booking_sku_var.get()
        veh_code = self.booking_veh_var.get()
        if not sku_code or not veh_code: return

        sku_dim = SKUS[sku_code]
        veh_dim = VEHICLE_SPECS[veh_code]
        daily_qty = DAILY_FLOW[sku_code]

        # 1. Stacking Rule
        # If item height <= 1.0m (100cm) -> Classes B, G. Others are non-stackable.
        is_stackable = sku_dim['height'] <= 100
        stack_factor = int(veh_dim['height'] / sku_dim['height']) if is_stackable else 1

        # 2. Capacity per Vehicle (Floor footprint)
        # Orientation 1: SKU Length along Veh Length, SKU Width along Veh Width
        fit1_l = int(veh_dim['length'] / sku_dim['length'])
        fit1_w = int(veh_dim['width'] / sku_dim['width'])
        cap1 = fit1_l * fit1_w

        # Orientation 2: SKU Width along Veh Length, SKU Length along Veh Width
        fit2_l = int(veh_dim['length'] / sku_dim['width'])
        fit2_w = int(veh_dim['width'] / sku_dim['length'])
        cap2 = fit2_l * fit2_w

        floor_cap = max(cap1, cap2)
        total_cap_per_veh = floor_cap * stack_factor

        # 3. Reservation Requirement (Ceil)
        req_vehicles = math.ceil(daily_qty / total_cap_per_veh) if total_cap_per_veh > 0 else 0

        # 4. Efficiency (Floor space utilization)
        sku_floor_area = sku_dim['length'] * sku_dim['width']
        veh_floor_area = veh_dim['length'] * veh_dim['width']
        efficiency = (floor_cap * sku_floor_area / veh_floor_area) * 100

        stack_text = "Stackable" if is_stackable else "Non-Stackable"
        res_text = (
            f"SKU: {sku_code} ({stack_text})\n"
            f"Vehicle: {veh_dim['name']}\n"
            f"Max Load per Truck: {total_cap_per_veh} units\n"
            f"Daily Flow: {daily_qty} units\n"
            f"RESULT: Reserve {req_vehicles} Units (Slots)\n"
            f"Efficiency: {efficiency:.1f}%"
        )
        self.booking_result_lbl.config(text=res_text)

    def execute_booking(self):
        sku_code = self.booking_sku_var.get()
        veh_code = self.booking_veh_var.get()
        if not sku_code or not veh_code: return

        # 1. Calculation
        sku_dim = SKUS[sku_code]
        veh_dim = VEHICLE_SPECS[veh_code]
        daily_qty = DAILY_FLOW[sku_code]
        is_stackable = sku_dim['height'] <= 100
        stack_factor = int(veh_dim['height'] / sku_dim['height']) if is_stackable else 1
        floor_cap = max(int(veh_dim['length'] / sku_dim['length']) * int(veh_dim['width'] / sku_dim['width']),
                        int(veh_dim['length'] / sku_dim['width']) * int(veh_dim['width'] / sku_dim['length']))
        total_veh_cap = floor_cap * stack_factor
        import math
        req_vehicles = math.ceil(daily_qty / total_veh_cap) if total_veh_cap > 0 else 0

        # 2. Dock/Type Assignment
        assigned_group = None
        for group, config in RACK_CONFIGS.items():
            if sku_code in config['skus']:
                assigned_group = group
                break
        if not assigned_group: return
        
        # Decide IN or OUT based on current group stock vs target
        target = RACK_CONFIGS[assigned_group]['target']
        current = sum(sku_inventory[s] for s in RACK_CONFIGS[assigned_group]['skus'])
        op_type = 'IN' if current < target else 'OUT'
        dock_type = 'Input' if op_type == 'IN' else 'Output'

        # Find empty docks
        assigned_docks = []
        for d_name, d_data in docks.items():
            if len(assigned_docks) < req_vehicles and d_data['type'] == dock_type and d_data['vehicle'] is None:
                docks[d_name]['vehicle'] = veh_dim['name']
                docks[d_name]['items'] = f"BOOKED: SKU-{sku_code} ({op_type})"
                assigned_docks.append(d_name)
        
        if not assigned_docks:
            messagebox.showwarning("No Docks", f"All {dock_type} docks are currently full!")
            return

        # 3. Start Sequential Simulation (one by one)
        # Total to transfer = daily_qty
        active_loadings[assigned_group] = {
            'type': op_type, 
            'qty_remaining': daily_qty, 
            'sku': sku_code, 
            'docks': assigned_docks
        }
        self.add_transaction_log(f"SIMULATION STARTED: {op_type} for SKU-{sku_code} ({daily_qty} units)")
        self.run_loading_simulation(assigned_group)

    def run_loading_simulation(self, group):
        if group not in active_loadings: return
        
        data = active_loadings[group]
        if data['qty_remaining'] <= 0:
            # Simulation Finished
            self.add_transaction_log(f"SIMULATION FINISHED: Group {group} processing complete.")
            # Clear docks
            for d_name in data['docks']:
                docks[d_name]['vehicle'] = None
                docks[d_name]['items'] = None
            active_loadings.pop(group)
            self.draw_warehouse_structure()
            self.update_dock_visuals()
            self.update_inventory_display()
            return

        # Perform 1 unit transfer (One-by-One)
        sku = data['sku']
        op = data['type']
        config = RACK_CONFIGS[group]
        max_per_rack = config['per_lvl'] * config['lvls']

        success = False
        if op == 'IN':
            # Find first rack in group that has space
            for r_num in config['racks']:
                if rack_inventory[r_num] < max_per_rack:
                    rack_inventory[r_num] += 1
                    sku_inventory[sku] += 1
                    # Update per-rack SKU counts
                    rack_sku_counts[r_num][sku] = rack_sku_counts[r_num].get(sku, 0) + 1
                    success = True
                    break
        else: # OUT
            # Find first rack in group that has items
            for r_num in config['racks']:
                if rack_sku_counts[r_num].get(sku, 0) > 0:
                    rack_sku_counts[r_num][sku] -= 1
                    rack_inventory[r_num] -= 1
                    sku_inventory[sku] = max(0, sku_inventory[sku] - 1)
                    success = True
                    break
        
        if success:
            data['qty_remaining'] -= 1
        else:
            # Group is full or empty
            data['qty_remaining'] = 0 
        
        # Update visuals during sim
        self.update_inventory_display()
        self.update_dock_visuals()
        self.root.update_idletasks() # Force UI refresh

        # Schedule next unit (simulate 5s total for the whole flow? or 5s per unit? 
        # User said "add timer like maybe for sim 5 sec for each process". 
        # For 90 units, 5s each is too slow. I'll make it 5s per vehicle load or a fast per-unit speed.
        # Actually 5s "for each process" likely means the whole vehicle load. 
        # Let's do a fast sequential update (100ms per unit) to visually see it fill up over a few seconds.
        self.root.after(50, lambda: self.run_loading_simulation(group))

    def update_inventory_display(self):
        # 1. Update SKU Treeview (Details)
        if self.dashboard_tree:
            for item in self.dashboard_tree.get_children():
                self.dashboard_tree.delete(item)
            
            for sku in sorted(SKUS.keys()):
                target, max_cap = 0, 0
                for conf in RACK_CONFIGS.values():
                    if sku in conf['skus']:
                        target, max_cap = conf['target'], conf['max']
                        break
                
                # Calculate Flow Count
                flow_val = FLOW_IN_QUANTS.get(sku, 1)
                curr_stock = sku_inventory.get(sku, 0)
                flow_count = round(curr_stock / flow_val, 1) if flow_val > 0 else 0
                
                self.dashboard_tree.insert("", tk.END, values=(sku, curr_stock, flow_count, target, max_cap))

        # 2. Update Group Treeview (Summary)
        if self.group_tree:
            for item in self.group_tree.get_children():
                self.group_tree.delete(item)
            
            for g_name, conf in RACK_CONFIGS.items():
                actual_items = sum(sku_inventory.get(s, 0) for s in conf['skus'])
                full_val = conf['max']
                fullness = int((actual_items / full_val) * 100) if full_val > 0 else 0
                
                self.group_tree.insert("", tk.END, values=(g_name, actual_items, conf['target'], f"{fullness}%"))

        # 3. Refresh Layout Tab (Labels/Heatmap)
        self.draw_warehouse_structure()
        self.draw_rack_heatmap()

    def calculate_sku_maxout(self):
        sku_to_calc = self.calc_sku_var.get()
        if not sku_to_calc: return

        sku_dim = SKUS[sku_to_calc]
        
        self.calc_output_area.delete('1.0', tk.END)
        self.calc_output_area.insert(tk.END, f"--- Analyzing Max Capacity for SKU: {sku_to_calc} ---\n", "bold")
        self.calc_output_area.insert(tk.END, f"Dimensions (HxWxL): {sku_dim['height']}x{sku_dim['width']}x{sku_dim['length']} cm\n\n")

        # 1. Stacking Calculation (Max out Height)
        # Safety clearance: assume items can stack almost to 7m, leaving 20cm clearance.
        safe_stacking_height = 680 # cm
        max_levels = int(safe_stacking_height / sku_dim['height'])
        
        # 2. Optimized Capacity Calculation (Auto-Rotation)
        # Orientation A: SKU Length along Rack Length, SKU Width along Rack Width
        fit_a_len = int(RACK_LENGTH / sku_dim['length'])
        fit_a_wid = int(RACK_WIDTH / sku_dim['width'])
        total_a = fit_a_len * fit_a_wid

        # Orientation B: SKU Width along Rack Length, SKU Length along Rack Width
        fit_b_len = int(RACK_LENGTH / sku_dim['width'])
        fit_b_wid = int(RACK_WIDTH / sku_dim['length'])
        total_b = fit_b_len * fit_b_wid

        if total_a >= total_b:
            max_items_along_length = fit_a_len
            max_items_along_width = fit_a_wid
            orient_text = f"Primary (Side {sku_dim['length']}cm along length)"
        else:
            max_items_along_length = fit_b_len
            max_items_along_width = fit_b_wid
            orient_text = f"Rotated (Side {sku_dim['width']}cm along length)"

        self.calc_output_area.insert(tk.END, f"Optimal Orientation:\n", "bold")
        self.calc_output_area.insert(tk.END, f" - {orient_text}\n\n")

        self.calc_output_area.insert(tk.END, f"Single Rack (Floor Level) Max Out:\n", "bold")
        self.calc_output_area.insert(tk.END, f" - Items along rack length (3600cm): {max_items_along_length} units\n")
        self.calc_output_area.insert(tk.END, f" - Items across rack width (100cm): {max_items_along_width} unit(s)\n")

        # 4. Total Units per single Rack
        total_per_rack = max_items_along_length * max_items_along_width * max_levels
        
        self.calc_output_area.insert(tk.END, f"\nTOTAL Max Units for ONE 36m Rack:\n", "bold")
        self.calc_output_area.insert(tk.END, f" - Capacity: ")
        self.calc_output_area.insert(tk.END, f"{total_per_rack} units", "red")
        self.calc_output_area.insert(tk.END, f" of SKU-{sku_to_calc}\n")

        # 5. Whole Warehouse
        wh_capacity = total_per_rack * NUM_RACKS
        self.calc_output_area.insert(tk.END, f"TOTAL Max Units in Warehouse (all 25 Racks):\n", "bold")
        self.calc_output_area.insert(tk.END, f" - Total Capacity: ")
        self.calc_output_area.insert(tk.END, f"{wh_capacity} units", "red")
        self.calc_output_area.insert(tk.END, f"\n")

        # Heatmap Refresh (illustrative usage)
        self.draw_rack_heatmap()

if __name__ == "__main__":
    root = tk.Tk()
    app = WarehouseGUI(root)
    root.mainloop()
