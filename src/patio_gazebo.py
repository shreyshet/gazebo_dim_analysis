import tkinter as tk
from tkinter import messagebox, filedialog
from math import floor

# --- PDF export deps ---
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors

# Default zoom: 1 inch = 4 pixels (updated via Fit to Window / slider)
SCALE = 4


class DragDropApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Patio & Gazebo Fit Tool (Inches)")

        # Fixed window size (adjust as needed)
        self.WINDOW_W = 1000
        self.WINDOW_H = 720
        self.root.geometry(f"{self.WINDOW_W}x{self.WINDOW_H}")

        # State
        self.scale = SCALE            # current scale (px per inch)
        self.pad = 30                 # margin around patio (px)
        self.pan_start = None         # for middle-button panning

        # Options: grid & snapping
        self.snap_enabled = tk.BooleanVar(value=True)
        self.grid_enabled = tk.BooleanVar(value=True)
        self.grid_in_var = tk.DoubleVar(value=12.0)   # grid every 12 inches by default

        # ===== TOP BAR: Inputs + actions =====
        top = tk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        # Inputs
        tk.Label(top, text="Patio W (in):").grid(row=0, column=0, sticky="e")
        tk.Label(top, text="Patio H (in):").grid(row=0, column=2, sticky="e")
        tk.Label(top, text="Gazebo W (in):").grid(row=0, column=4, sticky="e")
        tk.Label(top, text="Gazebo H (in):").grid(row=0, column=6, sticky="e")

        self.patio_w_entry = tk.Entry(top, width=7)
        self.patio_h_entry = tk.Entry(top, width=7)
        self.gazebo_w_entry = tk.Entry(top, width=7)
        self.gazebo_h_entry = tk.Entry(top, width=7)

        self.patio_w_entry.grid(row=0, column=1, padx=(4, 12))
        self.patio_h_entry.grid(row=0, column=3, padx=(4, 12))
        self.gazebo_w_entry.grid(row=0, column=5, padx=(4, 12))
        self.gazebo_h_entry.grid(row=0, column=7, padx=(4, 12))

        # Defaults
        self.patio_w_entry.insert(0, "180")   # 15 ft
        self.patio_h_entry.insert(0, "144")   # 12 ft
        self.gazebo_w_entry.insert(0, "120")
        self.gazebo_h_entry.insert(0, "120")

        # Actions
        tk.Button(top, text="Update", command=self.update_dimensions).grid(row=0, column=8, padx=(6, 6))
        tk.Button(top, text="Fit to Window", command=self.fit_to_window).grid(row=0, column=9, padx=(6, 6))
        tk.Button(top, text="Center Gazebo", command=self.center_gazebo).grid(row=0, column=10, padx=(6, 6))
        tk.Button(top, text="Save PDF", command=self.save_pdf).grid(row=0, column=11, padx=(10, 0))

        # Zoom slider (affects SCALE live)
        tk.Label(top, text="Zoom (px/in):").grid(row=0, column=12, padx=(12, 4))
        self.zoom_var = tk.IntVar(value=self.scale)
        zoom = tk.Scale(top, from_=1, to=30, orient=tk.HORIZONTAL, variable=self.zoom_var,
                        command=self.on_zoom_change, length=180)
        zoom.grid(row=0, column=13)

        # ===== GRID / SNAP PANEL =====
        gridbar = tk.Frame(root)
        gridbar.pack(side=tk.TOP, fill=tk.X, padx=8)

        tk.Checkbutton(gridbar, text="Show Grid", variable=self.grid_enabled, command=self.redraw_grid).pack(side=tk.LEFT)
        tk.Checkbutton(gridbar, text="Snap to Grid", variable=self.snap_enabled).pack(side=tk.LEFT, padx=(10,0))

        tk.Label(gridbar, text="Grid (in):").pack(side=tk.LEFT, padx=(16,4))
        self.grid_entry = tk.Entry(gridbar, width=5, textvariable=self.grid_in_var)
        self.grid_entry.pack(side=tk.LEFT)
        tk.Button(gridbar, text="Apply Grid", command=self.apply_grid_from_entry).pack(side=tk.LEFT, padx=6)

        # ===== DISTANCE PANEL =====
        dist = tk.Frame(root)
        dist.pack(side=tk.TOP, pady=(4, 4))
        self.left_lbl = tk.Label(dist, text="Left: -- in")
        self.right_lbl = tk.Label(dist, text="Right: -- in")
        self.top_lbl = tk.Label(dist, text="Top: -- in")
        self.bottom_lbl = tk.Label(dist, text="Bottom: -- in")
        self.left_lbl.grid(row=0, column=0, padx=12)
        self.right_lbl.grid(row=0, column=1, padx=12)
        self.top_lbl.grid(row=0, column=2, padx=12)
        self.bottom_lbl.grid(row=0, column=3, padx=12)

        # ===== NUDGE CONTROL PANEL =====
        nudge = tk.LabelFrame(root, text="Nudge Gazebo (0.5 in per click)")
        nudge.pack(side=tk.TOP, pady=(0, 6))

        btn_cfg = dict(width=3, height=1)
        tk.Button(nudge, text="↖", command=lambda: self.move_gazebo(-0.5, -0.5), **btn_cfg).grid(row=0, column=0, padx=2, pady=2)
        tk.Button(nudge, text="↑", command=lambda: self.move_gazebo(0, -0.5), **btn_cfg).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(nudge, text="↗", command=lambda: self.move_gazebo(0.5, -0.5), **btn_cfg).grid(row=0, column=2, padx=2, pady=2)
        tk.Button(nudge, text="←", command=lambda: self.move_gazebo(-0.5, 0), **btn_cfg).grid(row=1, column=0, padx=2, pady=2)
        tk.Label(nudge, text="•").grid(row=1, column=1, padx=2, pady=2)
        tk.Button(nudge, text="→", command=lambda: self.move_gazebo(0.5, 0), **btn_cfg).grid(row=1, column=2, padx=2, pady=2)
        tk.Button(nudge, text="↙", command=lambda: self.move_gazebo(-0.5, 0.5), **btn_cfg).grid(row=2, column=0, padx=2, pady=2)
        tk.Button(nudge, text="↓", command=lambda: self.move_gazebo(0, 0.5), **btn_cfg).grid(row=2, column=1, padx=2, pady=2)
        tk.Button(nudge, text="↘", command=lambda: self.move_gazebo(0.5, 0.5), **btn_cfg).grid(row=2, column=2, padx=2, pady=2)

        # ===== CANVAS + SCROLLBARS =====
        canvas_frame = tk.Frame(root)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.hbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.vbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="lightgray",
            xscrollcommand=self.hbar.set,
            yscrollcommand=self.vbar.set
        )
        self.hbar.config(command=self.canvas.xview)
        self.vbar.config(command=self.canvas.yview)

        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bindings for panning and wheel scrolling
        self.canvas.bind("<ButtonPress-2>", self.pan_start_event)  # Middle mouse press to pan
        self.canvas.bind("<B2-Motion>", self.pan_move_event)

        # Windows / Linux wheel
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)         # vertical
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_wheel)  # horizontal

        # macOS wheel bindings (older Tk may use these)
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(+1, "units"))

        # Keyboard arrow keys for nudging (0.5 in)
        self.root.bind("<Up>",    lambda e: self.move_gazebo(0, -0.5))
        self.root.bind("<Down>",  lambda e: self.move_gazebo(0, 0.5))
        self.root.bind("<Left>",  lambda e: self.move_gazebo(-0.5, 0))
        self.root.bind("<Right>", lambda e: self.move_gazebo(0.5, 0))

        # IDs for shapes
        self.patio = None
        self.gazebo = None

        # Dragging
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Initial draw
        self.update_dimensions()

    # ----------------- Helpers to get numeric inputs -----------------
    def get_inputs(self):
        try:
            patio_w_in = float(self.patio_w_entry.get())
            patio_h_in = float(self.patio_h_entry.get())
            gazebo_w_in = float(self.gazebo_w_entry.get())
            gazebo_h_in = float(self.gazebo_h_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for dimensions (inches).")
            return None
        return patio_w_in, patio_h_in, gazebo_w_in, gazebo_h_in

    # ----------------- Drawing / update -----------------
    def update_dimensions(self):
        vals = self.get_inputs()
        if not vals:
            return
        patio_w_in, patio_h_in, gazebo_w_in, gazebo_h_in = vals

        # Clear canvas
        self.canvas.delete("all")

        # Convert to pixels
        patio_w_px = patio_w_in * self.scale
        patio_h_px = patio_h_in * self.scale
        gazebo_w_px = gazebo_w_in * self.scale
        gazebo_h_px = gazebo_h_in * self.scale

        # Create patio (fixed) — keep fill transparent so grid is visible
        self.patio = self.canvas.create_rectangle(
            self.pad, self.pad, self.pad + patio_w_px, self.pad + patio_h_px,
            outline="green", width=3, fill=""
        )

        # Draw grid (under shapes)
        self.redraw_grid()

        # Create gazebo (draggable)
        self.gazebo = self.canvas.create_rectangle(
            self.pad + 10, self.pad + 10, self.pad + 10 + gazebo_w_px, self.pad + 10 + gazebo_h_px,
            fill="lightblue", outline="blue", width=2
        )

        # Drag bindings for gazebo
        self.canvas.tag_bind(self.gazebo, "<Button-1>", self.start_drag)
        self.canvas.tag_bind(self.gazebo, "<B1-Motion>", self.drag_move)
        self.canvas.tag_bind(self.gazebo, "<ButtonRelease-1>", self.drag_end)

        # Update scrollregion to cover entire drawing + margin
        self.canvas.configure(scrollregion=(0, 0, self.pad + patio_w_px + self.pad, self.pad + patio_h_px + self.pad))

        # Refresh distances
        self.update_distances()

    # ----------------- Grid handling -----------------
    def apply_grid_from_entry(self):
        try:
            g = float(self.grid_in_var.get())
            if g <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid grid", "Please enter a positive number for grid size (inches).")
            self.grid_in_var.set(12.0)
            return
        self.redraw_grid()

    def redraw_grid(self):
        self.canvas.delete("grid")
        if not self.grid_enabled.get() or not self.patio:
            return

        px1, py1, px2, py2 = self.canvas.coords(self.patio)
        grid_in = self.grid_in_var.get()
        try:
            grid_in = float(grid_in)
            if grid_in <= 0:
                grid_in = 12.0
        except Exception:
            grid_in = 12.0
            self.grid_in_var.set(grid_in)

        grid_px = grid_in * self.scale

        # Make the grid visible at most zooms
        grid_color = "#888888"                       # darker than #d0d0d0
        line_w = max(1, int(round(self.scale / 6)))  # thicken when zooming in

        # Vertical lines
        if grid_px >= 1:
            x = px1
            count = 0
            while x <= px2 + 0.5 and count < 5000:
                self.canvas.create_line(x, py1, x, py2, fill=grid_color, width=line_w, tags="grid")
                x += grid_px
                count += 1

        # Horizontal lines
        if grid_px >= 1:
            y = py1
            count = 0
            while y <= py2 + 0.5 and count < 5000:
                self.canvas.create_line(px1, y, px2, y, fill=grid_color, width=line_w, tags="grid")
                y += grid_px
                count += 1

        # Keep patio & gazebo outlines above the grid
        self.canvas.tag_raise(self.patio)
        if self.gazebo:
            self.canvas.tag_raise(self.gazebo)

    # ----------------- Fit patio to current window -----------------
    def fit_to_window(self):
        vals = self.get_inputs()
        if not vals:
            return
        patio_w_in, patio_h_in, *_ = vals

        # Available canvas area inside the window (approx)
        avail_w = max(100, self.WINDOW_W - 80)   # px
        avail_h = max(100, self.WINDOW_H - 260)  # px (leave space for bars/panels)

        if patio_w_in <= 0 or patio_h_in <= 0:
            messagebox.showerror("Invalid Input", "Patio dimensions must be > 0.")
            return

        # Compute scale to fit patio within available area (keep aspect)
        scale_w = (avail_w - 2*self.pad) / patio_w_in
        scale_h = (avail_h - 2*self.pad) / patio_h_in
        new_scale = floor(min(scale_w, scale_h))
        new_scale = max(1, min(new_scale, 30))  # clamp within slider range

        self.scale = new_scale
        self.zoom_var.set(new_scale)
        self.update_dimensions()
        self.redraw_grid()

    # ----------------- Zoom slider callback -----------------
    def on_zoom_change(self, value):
        try:
            self.scale = int(value)
        except Exception:
            return
        self.update_dimensions()
        self.redraw_grid()

    # ----------------- Drag handlers -----------------
    def start_drag(self, event):
        self.dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag_move(self, event):
        if not self.gazebo:
            return
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y

        gx1, gy1, gx2, gy2 = self.canvas.coords(self.gazebo)
        new_x1 = gx1 + dx
        new_y1 = gy1 + dy

        new_x1, new_y1 = self.clamp_top_left_within(new_x1, new_y1, gx2 - gx1, gy2 - gy1)

        self.canvas.move(self.gazebo, new_x1 - gx1, new_y1 - gy1)

        self.drag_start_x = event.x
        self.drag_start_y = event.y

        self.update_distances()

    def drag_end(self, event):
        if self.snap_enabled.get():
            self.snap_gazebo_to_grid()
        self.clamp_gazebo_within()
        self.update_distances()
        self.dragging = False

    # ----------------- Panning (middle mouse) -----------------
    def pan_start_event(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.pan_start = (event.x, event.y)

    def pan_move_event(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    # ----------------- Mouse wheel scroll -----------------
    def on_mousewheel(self, event):
        if event.delta:
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def on_shift_wheel(self, event):
        if event.delta:
            self.canvas.xview_scroll(int(-event.delta / 120), "units")

    # ----------------- Distance calculation -----------------
    def update_distances(self):
        if not (self.patio and self.gazebo):
            return

        px1, py1, px2, py2 = self.canvas.coords(self.patio)
        gx1, gy1, gx2, gy2 = self.canvas.coords(self.gazebo)

        left_gap   = (gx1 - px1) / self.scale
        right_gap  = (px2 - gx2) / self.scale
        top_gap    = (gy1 - py1) / self.scale
        bottom_gap = (py2 - gy2) / self.scale

        def color_for(gap):
            return "red" if gap <= 1e-6 else "black"

        self.left_lbl.config(text=f"Left: {left_gap:.1f} in",   fg=color_for(left_gap))
        self.right_lbl.config(text=f"Right: {right_gap:.1f} in", fg=color_for(right_gap))
        self.top_lbl.config(text=f"Top: {top_gap:.1f} in",       fg=color_for(top_gap))
        self.bottom_lbl.config(text=f"Bottom: {bottom_gap:.1f} in", fg=color_for(bottom_gap))

    # ----------------- Geometry helpers -----------------
    def clamp_top_left_within(self, x1, y1, gw, gh):
        px1, py1, px2, py2 = self.canvas.coords(self.patio)

        min_x1 = px1
        min_y1 = py1
        max_x1 = px2 - gw
        max_y1 = py2 - gh

        if max_x1 < min_x1:
            x1 = min_x1
        else:
            x1 = min(max(x1, min_x1), max_x1)

        if max_y1 < min_y1:
            y1 = min_y1
        else:
            y1 = min(max(y1, min_y1), max_y1)

        return x1, y1

    def clamp_gazebo_within(self):
        if not self.gazebo:
            return
        gx1, gy1, gx2, gy2 = self.canvas.coords(self.gazebo)
        gw, gh = gx2 - gx1, gy2 - gy1
        nx1, ny1 = self.clamp_top_left_within(gx1, gy1, gw, gh)
        self.canvas.move(self.gazebo, nx1 - gx1, ny1 - gy1)

    def snap_gazebo_to_grid(self):
        if not (self.gazebo and self.patio and self.grid_enabled.get()):
            return

        grid_in = self.grid_in_var.get()
        if grid_in <= 0:
            return
        grid_px = grid_in * self.scale

        px1, py1, px2, py2 = self.canvas.coords(self.patio)
        gx1, gy1, gx2, gy2 = self.canvas.coords(self.gazebo)
        gw, gh = gx2 - gx1, gy2 - gy1

        offset_x = round((gx1 - px1) / grid_px) * grid_px
        offset_y = round((gy1 - py1) / grid_px) * grid_px
        nx1 = px1 + offset_x
        ny1 = py1 + offset_y

        nx1, ny1 = self.clamp_top_left_within(nx1, ny1, gw, gh)

        self.canvas.move(self.gazebo, nx1 - gx1, ny1 - gy1)

    # ----------------- High-level actions -----------------
    def move_gazebo(self, dx_in, dy_in):
        if not self.gazebo:
            return
        dx_px = dx_in * self.scale
        dy_px = dy_in * self.scale

        gx1, gy1, gx2, gy2 = self.canvas.coords(self.gazebo)
        gw, gh = gx2 - gx1, gy2 - gy1

        nx1 = gx1 + dx_px
        ny1 = gy1 + dy_px

        nx1, ny1 = self.clamp_top_left_within(nx1, ny1, gw, gh)
        self.canvas.move(self.gazebo, nx1 - gx1, ny1 - gy1)

        if self.snap_enabled.get():
            self.snap_gazebo_to_grid()

        self.update_distances()

    def center_gazebo(self):
        if not (self.patio and self.gazebo):
            return
        px1, py1, px2, py2 = self.canvas.coords(self.patio)
        gx1, gy1, gx2, gy2 = self.canvas.coords(self.gazebo)
        pw, ph = px2 - px1, py2 - py1
        gw, gh = gx2 - gx1, gy2 - gy1

        nx1 = px1 + (pw - gw) / 2
        ny1 = py1 + (ph - gh) / 2
        nx1, ny1 = self.clamp_top_left_within(nx1, ny1, gw, gh)

        self.canvas.move(self.gazebo, nx1 - gx1, ny1 - gy1)

        if self.snap_enabled.get():
            self.snap_gazebo_to_grid()

        self.update_distances()

    # ----------------- PDF Export -----------------
    def save_pdf(self):
        """Save a to-scale PDF of the current layout (inches -> PDF points)."""
        vals = self.get_inputs()
        if not vals:
            return
        patio_w_in, patio_h_in, gazebo_w_in, gazebo_h_in = vals

        if not (self.patio and self.gazebo):
            messagebox.showerror("Nothing to save", "Draw the patio and gazebo first.")
            return

        # Ask user where to save
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save PDF"
        )
        if not path:
            return

        # Current gazebo offsets from patio (inches)
        px1, py1, px2, py2 = self.canvas.coords(self.patio)
        gx1, gy1, gx2, gy2 = self.canvas.coords(self.gazebo)
        gazebo_left_in = (gx1 - px1) / self.scale
        gazebo_top_in  = (gy1 - py1) / self.scale

        # Page orientation: landscape if patio wider
        page_w, page_h = letter
        if patio_w_in >= patio_h_in:
            page_w, page_h = landscape(letter)

        c = pdfcanvas.Canvas(path, pagesize=(page_w, page_h))
        pt_per_in = 72.0

        # Margins & usable area
        margin_in = 0.5
        margin_pt = margin_in * pt_per_in
        usable_w_pt = page_w - 2 * margin_pt
        usable_h_pt = page_h - 2 * margin_pt

        # Scale (in -> pt) so the patio fits inside usable area
        scale_pt = min(usable_w_pt / patio_w_in, usable_h_pt / patio_h_in)

        # Center patio on page
        patio_w_pt = patio_w_in * scale_pt
        patio_h_pt = patio_h_in * scale_pt
        origin_x = (page_w - patio_w_pt) / 2.0
        origin_y = (page_h - patio_h_pt) / 2.0

        # Title
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(page_w / 2, page_h - margin_pt + 8, "Gazebo on Patio Layout")

        # Patio outline
        c.setStrokeColor(colors.green)
        c.setLineWidth(2)
        c.rect(origin_x, origin_y, patio_w_pt, patio_h_pt, fill=0)

        # Grid (optional)
        if self.grid_enabled.get():
            grid_in = self.grid_in_var.get()
            try:
                grid_in = float(grid_in)
            except Exception:
                grid_in = 12.0
            if grid_in > 0:
                grid_pt = grid_in * scale_pt
                c.setStrokeColor(colors.HexColor("#888888"))
                c.setLineWidth(0.4)
                # Vertical lines
                x = 0.0
                while x <= patio_w_in + 1e-6:
                    cx = origin_x + x * scale_pt
                    c.line(cx, origin_y, cx, origin_y + patio_h_pt)
                    x += grid_in
                # Horizontal lines
                y = 0.0
                while y <= patio_h_in + 1e-6:
                    cy = origin_y + y * scale_pt
                    c.line(origin_x, cy, origin_x + patio_w_pt, cy)
                    y += grid_in

        # Gazebo rectangle
        c.setFillColor(colors.lightblue)
        c.setStrokeColor(colors.blue)
        c.setLineWidth(1)
        gz_x = origin_x + gazebo_left_in * scale_pt
        gz_y = origin_y + gazebo_top_in * scale_pt
        gz_w = gazebo_w_in * scale_pt
        gz_h = gazebo_h_in * scale_pt
        c.rect(gz_x, gz_y, gz_w, gz_h, fill=1)

        # Clearances (inches)
        left_gap   = gazebo_left_in
        right_gap  = patio_w_in - gazebo_left_in - gazebo_w_in
        top_gap    = gazebo_top_in
        bottom_gap = patio_h_in - gazebo_top_in - gazebo_h_in

        c.setFont("Helvetica", 10)
        info_top_y = page_h - margin_pt - 14
        c.setFillColor(colors.black)
        c.drawString(margin_pt, info_top_y,
                     f"Patio: {patio_w_in:.1f} in × {patio_h_in:.1f} in   "
                     f"Gazebo: {gazebo_w_in:.1f} in × {gazebo_h_in:.1f} in")
        c.drawString(margin_pt, info_top_y - 14,
                     f"Clearances – Left: {left_gap:.1f} in, Right: {right_gap:.1f} in, "
                     f"Top: {top_gap:.1f} in, Bottom: {bottom_gap:.1f} in")

        # Scale bar
        desired_in = 24
        bar_len_pt = desired_in * scale_pt
        max_bar_pt = usable_w_pt * 0.5
        if bar_len_pt > max_bar_pt:
            steps = max(1, int((max_bar_pt / scale_pt) // 6))
            desired_in = steps * 6
            bar_len_pt = desired_in * scale_pt

        bar_x = origin_x
        bar_y = origin_y - 20
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.line(bar_x, bar_y, bar_x + bar_len_pt, bar_y)
        c.setLineWidth(1)
        c.line(bar_x, bar_y - 3, bar_x, bar_y + 3)
        c.line(bar_x + bar_len_pt, bar_y - 3, bar_x + bar_len_pt, bar_y + 3)
        c.setFont("Helvetica", 9)
        c.drawString(bar_x, bar_y - 12, f"Scale bar: {desired_in} in")

        # Footer
        c.setFont("Helvetica", 8)
        c.drawRightString(page_w - margin_pt, margin_pt - 10, "Generated by Patio & Gazebo Fit Tool")

        c.showPage()
        c.save()
        messagebox.showinfo("Saved", f"PDF saved to:\n{path}")


def main():
    root = tk.Tk()
    app = DragDropApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()