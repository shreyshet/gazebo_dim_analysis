import tkinter as tk
from tkinter import messagebox

# Increase zoom: 1 inch = 4 pixels (adjust as needed)
SCALE = 4  


class DragDropApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Patio & Gazebo Fit Tool (Inches)")

        # ------------------------------
        # INPUT PANEL
        # ------------------------------
        input_frame = tk.Frame(root)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Patio Width (in):").grid(row=0, column=0)
        tk.Label(input_frame, text="Patio Height (in):").grid(row=1, column=0)
        tk.Label(input_frame, text="Gazebo Width (in):").grid(row=0, column=2)
        tk.Label(input_frame, text="Gazebo Height (in):").grid(row=1, column=2)

        self.patio_w_entry = tk.Entry(input_frame, width=8)
        self.patio_h_entry = tk.Entry(input_frame, width=8)
        self.gazebo_w_entry = tk.Entry(input_frame, width=8)
        self.gazebo_h_entry = tk.Entry(input_frame, width=8)

        self.patio_w_entry.grid(row=0, column=1, padx=8)
        self.patio_h_entry.grid(row=1, column=1, padx=8)
        self.gazebo_w_entry.grid(row=0, column=3, padx=8)
        self.gazebo_h_entry.grid(row=1, column=3, padx=8)

        # Default values
        self.patio_w_entry.insert(0, "180")   # 15 ft = 180 in
        self.patio_h_entry.insert(0, "144")   # 12 ft = 144 in
        self.gazebo_w_entry.insert(0, "120")
        self.gazebo_h_entry.insert(0, "120")

        update_btn = tk.Button(input_frame, text="Update", command=self.update_dimensions)
        update_btn.grid(row=2, column=0, columnspan=4, pady=12)

        # ------------------------------
        # DISTANCE DISPLAY PANEL
        # ------------------------------
        self.dist_frame = tk.Frame(root)
        self.dist_frame.pack(pady=10)

        self.left_lbl = tk.Label(self.dist_frame, text="Left: -- in")
        self.right_lbl = tk.Label(self.dist_frame, text="Right: -- in")
        self.top_lbl = tk.Label(self.dist_frame, text="Top: -- in")
        self.bottom_lbl = tk.Label(self.dist_frame, text="Bottom: -- in")

        self.left_lbl.grid(row=0, column=0, padx=15)
        self.right_lbl.grid(row=0, column=1, padx=15)
        self.top_lbl.grid(row=1, column=0, padx=15)
        self.bottom_lbl.grid(row=1, column=1, padx=15)

        # Canvas initialized later
        self.canvas = None
        self.patio = None
        self.gazebo = None

        self.start_x = 0
        self.start_y = 0

        self.update_dimensions()

    # -----------------------------------------
    # Update drawing from inputs
    # -----------------------------------------
    def update_dimensions(self):
        try:
            patio_w = float(self.patio_w_entry.get()) * SCALE
            patio_h = float(self.patio_h_entry.get()) * SCALE
            gazebo_w = float(self.gazebo_w_entry.get()) * SCALE
            gazebo_h = float(self.gazebo_h_entry.get()) * SCALE
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers.")
            return

        if self.canvas:
            self.canvas.destroy()

        self.canvas = tk.Canvas(self.root, width=patio_w + 60, height=patio_h + 60, bg="lightgray")
        self.canvas.pack()

        # Draw patio
        self.patio = self.canvas.create_rectangle(
            30, 30, 30 + patio_w, 30 + patio_h,
            outline="green", width=3
        )

        # Draw gazebo (draggable)
        self.gazebo = self.canvas.create_rectangle(
            40, 40, 40 + gazebo_w, 40 + gazebo_h,
            fill="lightblue", outline="blue", width=2
        )

        # Bind drag
        self.canvas.tag_bind(self.gazebo, "<Button-1>", self.start_drag)
        self.canvas.tag_bind(self.gazebo, "<B1-Motion>", self.drag)

        self.update_distances()

    # -----------------------------------------
    # Drag logic
    # -----------------------------------------
    def start_drag(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def drag(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.canvas.move(self.gazebo, dx, dy)
        self.start_x = event.x
        self.start_y = event.y
        self.update_distances()

    # -----------------------------------------
    # Distance calculation
    # -----------------------------------------
    def update_distances(self):
        px1, py1, px2, py2 = self.canvas.coords(self.patio)
        gx1, gy1, gx2, gy2 = self.canvas.coords(self.gazebo)

        left_gap = (gx1 - px1) / SCALE
        right_gap = (px2 - gx2) / SCALE
        top_gap = (gy1 - py1) / SCALE
        bottom_gap = (py2 - gy2) / SCALE

        self.left_lbl.config(text=f"Left: {left_gap:.1f} in")
        self.right_lbl.config(text=f"Right: {right_gap:.1f} in")
        self.top_lbl.config(text=f"Top: {top_gap:.1f} in")
        self.bottom_lbl.config(text=f"Bottom: {bottom_gap:.1f} in")



def main():
    root = tk.Tk()
    app = DragDropApp(root)
    root.mainloop()
