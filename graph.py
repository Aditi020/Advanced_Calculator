"""
graph.py
--------
This file handles the Interactive Graph page.
It embeds Matplotlib (a popular charting library) directly into the Tkinter window.

Libraries used:
- matplotlib.pyplot: The core plotting library.
- matplotlib.backends.backend_tkagg.FigureCanvasTkAgg: Allows us to embed a Matplotlib graph inside a Tkinter widget.
- numpy: Used for generating arrays of numbers for the graphs.
"""
import customtkinter as ctk
import theme
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
import calculations as calc

class GraphFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG1)
        self.app = app
        
        self.stat_x = []
        self.stat_y = []
        self.is_stats_mode = False
        self.plot_type = "Linear Reg"
        
        # Variables to track mouse dragging for panning the graph
        self._drag_start = None
        self._xlim_start = None
        self._ylim_start = None

        # --- 1. Top Toolbar ---
        self.toolbar = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        self.toolbar.pack(fill="x", padx=14, pady=(0, 6))
        
        # Back Button
        self.back_btn = ctk.CTkButton(self.toolbar, text="←", width=35, fg_color=theme.BTN_OP, text_color=theme.TEXT, font=("Segoe UI", 16, "bold"), command=self.app._close_graph_view)
        self.back_btn.pack(side="left", padx=5, pady=5)

        # Dropdown Menu for Graph Types
        graph_types = ["Linear Reg", "Histogram", "Normal Curve", "Poisson Dist"]
        self.type_menu = ctk.CTkOptionMenu(
            self.toolbar, values=graph_types, 
            fg_color=theme.BTN_SCI, text_color=theme.TEXT, button_color=theme.BTN_OP, font=theme.FONT_KEY,
            command=self.change_plot_type, width=130
        )
        self.type_menu.pack(side="left", padx=10, pady=5)

        # Zoom / Reset Controls
        self.reset_btn = ctk.CTkButton(self.toolbar, text="↺", width=30, fg_color=theme.BTN_CLEAR, text_color=theme.TEXT, font=("Segoe UI", 16, "bold"), command=self.reset_view)
        self.reset_btn.pack(side="right", padx=5, pady=5)
        self.zoom_out_btn = ctk.CTkButton(self.toolbar, text="−", width=30, fg_color=theme.BTN_SCI, text_color=theme.TEXT, font=("Segoe UI", 16, "bold"), command=self.zoom_out)
        self.zoom_out_btn.pack(side="right", padx=2, pady=5)
        self.zoom_in_btn = ctk.CTkButton(self.toolbar, text="+", width=30, fg_color=theme.BTN_SCI, text_color=theme.TEXT, font=("Segoe UI", 16, "bold"), command=self.zoom_in)
        self.zoom_in_btn.pack(side="right", padx=2, pady=5)

        # --- 2. Graph Canvas Area ---
        self.canvas_frame = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        self.canvas_frame.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        # FigureCanvasTkAgg bridges Matplotlib and Tkinter
        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        self.fig.patch.set_facecolor(theme.GRAPH_BG) # Set background color
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # --- 3. Bottom Summary Area ---
        self.summary_frame = ctk.CTkScrollableFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS, height=180)
        self.summary_frame.pack(fill="x", padx=14, pady=(0, 10))
        
        ctk.CTkLabel(self.summary_frame, text="📈 Summary", font=theme.FONT_KEY, text_color=theme.TEXT).pack(pady=(5, 5), anchor="w", padx=5)
        self.summary_container = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        self.summary_container.pack(fill="x", expand=True)

        self.setup_axes()
        self._connect_mouse_events()

    def _connect_mouse_events(self):
        # Connects mouse scroll, click, and movement to our custom functions.
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.canvas.mpl_connect('button_press_event', self._on_press)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)

    def setup_axes(self):
        # Clears the graph and applies modern styling (removes top/right borders).
        self.ax.clear()
        self.ax.set_facecolor(theme.GRAPH_BG)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(theme.TEXT_MUTED)
        self.ax.spines['bottom'].set_color(theme.TEXT_MUTED)
        self.ax.grid(True, color=theme.GRAPH_GRID, linestyle="--", linewidth=0.7, alpha=0.7)
        self.ax.axhline(0, color=theme.TEXT, linewidth=1.2, alpha=0.5)
        self.ax.axvline(0, color=theme.TEXT, linewidth=1.2, alpha=0.5)
        self.ax.tick_params(colors=theme.TEXT_MUTED, labelsize=9)
        # MaxNLocator ensures we don't get an ugly crowded axis
        self.ax.xaxis.set_major_locator(MaxNLocator(nbins=7, prune='both'))
        self.ax.yaxis.set_major_locator(MaxNLocator(nbins=7, prune='both'))

    def load_statistics(self, x, y):
        self.is_stats_mode = True
        self.stat_x = x
        self.stat_y = y
        self.type_menu.pack(side="left", padx=10, pady=5)
        self.type_menu.set("Linear Reg")
        self.plot_type = "Linear Reg"
        self.draw()

    def change_plot_type(self, choice):
        self.plot_type = choice
        self.draw()

    def draw(self):
        # Master function that redraws the graph based on the selected type.
        self.setup_axes()
        for w in self.summary_container.winfo_children():
            w.destroy()
            
        if self.is_stats_mode:
            self._draw_statistics()
        else:
            self._draw_function()
        self.canvas.draw() # Tells Matplotlib to actually render the changes

    def _auto_scale(self, x_data, y_data):
        # Automatically scales the graph so data fits perfectly on screen.
        if not len(x_data) or not len(y_data):
            self.ax.set_xlim(-10, 10)
            self.ax.set_ylim(-10, 10)
            return
        x_min, x_max = min(x_data), max(x_data)
        y_min, y_max = min(y_data), max(y_data)
        x_pad = (x_max - x_min) * 0.15 if x_max != x_min else 5
        y_pad = (y_max - y_min) * 0.15 if y_max != y_min else 5
        self.ax.set_xlim(x_min - x_pad, x_max + x_pad)
        self.ax.set_ylim(y_min - y_pad, y_max + y_pad)

    def _add_summary_row(self, label, value):
        # Helper to add a row to the summary panel.
        row = ctk.CTkFrame(self.summary_container, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED).pack(side="left", padx=10)
        ctk.CTkLabel(row, text=value, font=theme.FONT_KEY, text_color=theme.TEXT).pack(side="right", padx=10)

    def _show_error(self, msg):
        # Displays an error message in the center of the graph.
        self.ax.text(0.5, 0.5, msg, ha='center', va='center', color=theme.BTN_CLEAR, fontsize=12, transform=self.ax.transAxes)
        self._add_summary_row("Status", msg)

    def _draw_statistics(self):
        # Logic to draw Linear, Histogram, Normal, or Poisson distributions
        x_arr = np.array(self.stat_x) if self.stat_x else np.array([])
        y_arr = np.array(self.stat_y) if self.stat_y else np.array([])
        paired = len(x_arr) > 0 and len(x_arr) == len(y_arr)

        if self.plot_type == "Linear Reg":
            if not paired:
                self._show_error("Requires equal number of X and Y values.")
                return

            # Scatter plot points
            self.ax.scatter(x_arr, y_arr, color=theme.CURVE_1, s=40, zorder=3, edgecolor=theme.BG1, linewidth=1.5)
            
            reg = calc.get_regression_stats(self.stat_x, self.stat_y)
            if reg:
                m, b, r = reg["Slope (m)"], reg["Y-Int (b)"], reg["Corr (r)"]
                # Generate 100 points to draw the regression line
                x_line = np.linspace(min(x_arr), max(x_arr), 100)
                self.ax.plot(x_line, m * x_line + b, color=theme.BTN_EQ, linewidth=2.5)
                self._add_summary_row("Equation", f"y = {m:.2f}x + {b:.2f}")
                self._add_summary_row("Correlation (r)", f"{r:.4f}")
                self._add_summary_row("R-squared (R²)", f"{r**2:.4f}")
            
            self._auto_scale(x_arr, y_arr)

        elif self.plot_type in ["Histogram", "Normal Curve", "Poisson Dist"]:
            if len(x_arr) < 3:
                self._show_error("Requires at least 3 X values.")
                return
                
            stats = calc.get_descriptive_stats(self.stat_x)
            mean_x = stats['Mean']
            std_x = stats['Std (s)']

            if self.plot_type == "Histogram":
                # 'bins=auto' lets numpy figure out the best bucket size
                self.ax.hist(x_arr, bins='auto', color=theme.CURVE_2, edgecolor=theme.BG1, alpha=0.8)
                self._auto_scale(x_arr, [0, 1])
                self._add_summary_row("Sample Size (n)", str(len(x_arr)))
                self._add_summary_row("Mean", f"{mean_x:.4f}")
                self._add_summary_row("Std Dev (s)", f"{std_x:.4f}")

            elif self.plot_type == "Normal Curve":
                # The mathematical formula for a normal distribution curve (Bell Curve)
                x_curve = np.linspace(mean_x - 4*std_x, mean_x + 4*std_x, 200)
                y_curve = (1 / (std_x * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_curve - mean_x) / std_x)**2)
                self.ax.plot(x_curve, y_curve, color=theme.CURVE_3, linewidth=2.5)
                self.ax.fill_between(x_curve, y_curve, color=theme.CURVE_3, alpha=0.15)
                self._auto_scale(x_curve, y_curve)
                self._add_summary_row("Population Mean (μ)", f"{mean_x:.4f}")
                self._add_summary_row("Std Deviation (σ)", f"{std_x:.4f}")

            elif self.plot_type == "Poisson Dist":
                lam = mean_x
                max_k = int(max(x_arr)) + 2
                k_vals = np.arange(0, max_k)
                pmf_vals = [calc.get_poisson_pmf(k, lam) for k in k_vals]
                
                # Bar chart for Poisson
                self.ax.bar(k_vals, pmf_vals, color=theme.CURVE_4, edgecolor=theme.BG1, alpha=0.8)
                self._auto_scale(k_vals, pmf_vals)
                self._add_summary_row("Lambda (λ)", f"{lam:.4f}")
                self._add_summary_row("Model", "Poisson Distribution")

    def _draw_function(self):
        # Plots an equation typed by the user (e.g., y = sin(x))
        expr = self.func_entry.get().strip()
        if not expr: return
        if "=" in expr: expr = expr.split("=")[1].strip()
            
        # Generate 1000 X points to draw a smooth curve
        x_vals = np.linspace(-20, 20, 1000)
        y_vals = []
        for x in x_vals:
            try:
                val = calc.evaluate(expr, {"x": x}, self.app.angle_mode)
                if isinstance(val, (int, float, complex)):
                    y_vals.append(float(val.real) if isinstance(val, complex) else float(val))
                else:
                    y_vals.append(np.nan) # np.nan represents "Not a Number" (handles asymptotes)
            except Exception:
                y_vals.append(np.nan)
        
        y_arr = np.array(y_vals)
        self.ax.plot(x_vals, y_arr, color=theme.CURVE_1, linewidth=2.5)
        
        self._add_summary_row("Equation", f"f(x) = {expr}")
        self._add_summary_row("Angle Mode", self.app.angle_mode)
        
        # Limit Y axis to prevent massive asymptotes (like tan(x)) from ruining the view
        finite_y = y_arr[np.isfinite(y_arr)]
        if len(finite_y) > 0:
            y_med = np.median(finite_y)
            y_range = max(finite_y) - min(finite_y)
            self.ax.set_ylim(y_med - y_range*0.8, y_med + y_range*0.8)
        self.ax.set_xlim(-10, 10)

    # --- Interactions ---
    def zoom_in(self): self._apply_zoom(0.8)
    def zoom_out(self): self._apply_zoom(1.25)

    def reset_view(self):
        if self.is_stats_mode: self.draw()
        else:
            self.ax.set_xlim(-10, 10)
            self.ax.set_ylim(-10, 10)
            self.canvas.draw()

    def _apply_zoom(self, factor):
        # Calculates new X and Y limits based on zoom factor
        xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
        xc, yc = (xlim[0] + xlim[1]) / 2, (ylim[0] + ylim[1]) / 2
        self.ax.set_xlim(xc + (xlim[0] - xc) * factor, xc + (xlim[1] - xc) * factor)
        self.ax.set_ylim(yc + (ylim[0] - yc) * factor, yc + (ylim[1] - yc) * factor)
        self.canvas.draw()

    def _on_scroll(self, event):
        # Mouse wheel zoom
        if event.inaxes != self.ax: return
        self._apply_zoom(0.8 if event.button == 'up' else 1.25)

    def _on_press(self, event):
        # Start mouse drag
        if event.inaxes != self.ax: return
        self._drag_start = (event.xdata, event.ydata)
        self._xlim_start = self.ax.get_xlim()
        self._ylim_start = self.ax.get_ylim()

    def _on_motion(self, event):
        # Mouse drag panning
        if self._drag_start is None or event.inaxes != self.ax: return
        dx, dy = event.xdata - self._drag_start[0], event.ydata - self._drag_start[1]
        self.ax.set_xlim(self._xlim_start[0] - dx, self._xlim_start[1] - dx)
        self.ax.set_ylim(self._ylim_start[0] - dy, self._ylim_start[1] - dy)
        self.canvas.draw()

    def _on_release(self, event):
        # End mouse drag
        self._drag_start = None