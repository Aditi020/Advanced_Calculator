"""
Graph module. Embeds Matplotlib inside Tkinter.
Handles pan, zoom, and drawing the specific plot types.
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
        
        # Variables to track mouse dragging for panning
        self._drag_start = None
        self._xlim_start = None
        self._ylim_start = None

        # Toolbar area
        self.toolbar = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        self.toolbar.pack(fill="x", padx=14, pady=(0, 6))
        
        ctk.CTkButton(self.toolbar, text="←", width=35, fg_color=theme.BTN_OP, text_color=theme.TEXT, font=("Segoe UI", 16, "bold"), command=self.app._close_graph_view).pack(side="left", padx=5, pady=5)

        graph_types = ["Linear Reg", "Histogram", "Normal Curve", "Poisson Dist"]
        self.type_menu = ctk.CTkOptionMenu(
            self.toolbar, values=graph_types, 
            fg_color=theme.BTN_SCI, text_color=theme.TEXT, button_color=theme.BTN_OP, font=theme.FONT_KEY,
            command=self.change_plot_type, width=130
        )
        self.type_menu.pack(side="left", padx=10, pady=5)

        # Zoom / Reset controls
        ctk.CTkButton(self.toolbar, text="↺", width=30, fg_color=theme.BTN_CLEAR, text_color=theme.TEXT, font=("Segoe UI", 16, "bold"), command=self.reset_view).pack(side="right", padx=5, pady=5)
        ctk.CTkButton(self.toolbar, text="−", width=30, fg_color=theme.BTN_SCI, text_color=theme.TEXT, font=("Segoe UI", 16, "bold"), command=self.zoom_out).pack(side="right", padx=2, pady=5)
        ctk.CTkButton(self.toolbar, text="+", width=30, fg_color=theme.BTN_SCI, text_color=theme.TEXT, font=("Segoe UI", 16, "bold"), command=self.zoom_in).pack(side="right", padx=2, pady=5)

        # Canvas Area
        self.canvas_frame = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        self.canvas_frame.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        self.fig.patch.set_facecolor(theme.GRAPH_BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

        # Summary Area
        self.summary_frame = ctk.CTkScrollableFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS, height=180)
        self.summary_frame.pack(fill="x", padx=14, pady=(0, 10))
        
        ctk.CTkLabel(self.summary_frame, text="📈 Summary", font=theme.FONT_KEY, text_color=theme.TEXT).pack(pady=(5, 5), anchor="w", padx=5)
        self.summary_container = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
        self.summary_container.pack(fill="x", expand=True)

        self.setup_axes()
        self._connect_mouse_events()

    def _connect_mouse_events(self):
        self.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.canvas.mpl_connect('button_press_event', self._on_press)
        self.canvas.mpl_connect('button_release_event', self._on_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_motion)

    def setup_axes(self):
        """
        Matplotlib bugs out if you don't clear the axis properly. 
        This also sets the modern styling.
        """
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
        self.setup_axes()
        for w in self.summary_container.winfo_children():
            w.destroy()
            
        self._draw_statistics()
        self.canvas.draw()

    def _auto_scale(self, x_data, y_data):
        """
        Automatically scales the graph so the data fits on screen.
        """
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
        row = ctk.CTkFrame(self.summary_container, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=label, font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED).pack(side="left", padx=10)
        ctk.CTkLabel(row, text=value, font=theme.FONT_KEY, text_color=theme.TEXT).pack(side="right", padx=10)

    def _show_error(self, msg):
        self.ax.text(0.5, 0.5, msg, ha='center', va='center', color=theme.BTN_CLEAR, fontsize=12, transform=self.ax.transAxes)
        self._add_summary_row("Status", msg)

    def _draw_statistics(self):
        x = np.array(self.stat_x) if self.stat_x else np.array([])
        y = np.array(self.stat_y) if self.stat_y else np.array([])
        paired = len(x) > 0 and len(x) == len(y)

        if self.plot_type == "Linear Reg":
            if not paired:
                self._show_error("Requires equal number of X and Y values.")
                return

            self.ax.scatter(x, y, color=theme.CURVE_1, s=40, zorder=3, edgecolor=theme.BG1, linewidth=1.5)
            
            reg = calc.get_reg_stats(self.stat_x, self.stat_y)
            if reg:
                m, b, r = reg["Slope (m)"], reg["Y-Int (b)"], reg["Corr (r)"]
                x_line = np.linspace(min(x), max(x), 100)
                self.ax.plot(x_line, m * x_line + b, color=theme.BTN_EQ, linewidth=2.5)
                self._add_summary_row("Equation", f"y = {m:.2f}x + {b:.2f}")
                self._add_summary_row("Correlation (r)", f"{r:.4f}")
                self._add_summary_row("R-squared (R²)", f"{r**2:.4f}")
            
            self._auto_scale(x, y)

        elif self.plot_type in ["Histogram", "Normal Curve", "Poisson Dist"]:
            if len(x) < 3:
                self._show_error("Requires at least 3 X values.")
                return
                
            stats = calc.get_desc_stats(self.stat_x)
            mean_x = stats['Mean']
            std_x = stats['Std (s)']

            if self.plot_type == "Histogram":
                self.ax.hist(x, bins='auto', color=theme.CURVE_2, edgecolor=theme.BG1, alpha=0.8)
                self._auto_scale(x, [0, 1])
                self._add_summary_row("Sample Size (n)", str(len(x)))
                self._add_summary_row("Mean", f"{mean_x:.4f}")
                self._add_summary_row("Std Dev (s)", f"{std_x:.4f}")

            elif self.plot_type == "Normal Curve":
                xc = np.linspace(mean_x - 4*std_x, mean_x + 4*std_x, 200)
                yc = (1 / (std_x * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((xc - mean_x) / std_x)**2)
                self.ax.plot(xc, yc, color=theme.CURVE_3, linewidth=2.5)
                self.ax.fill_between(xc, yc, color=theme.CURVE_3, alpha=0.15)
                self._auto_scale(xc, yc)
                self._add_summary_row("Sample mean", f"{mean_x:.4f}")
                self._add_summary_row("Std Deviation (s)", f"{std_x:.4f}")

            elif self.plot_type == "Poisson Dist":
                if any(v < 0 for v in x) or any(not float(v).is_integer() for v in x):
                    self._show_error("Poisson requires non-negative integers.")
                    return
                    
                lam = mean_x
                if lam <= 0:
                    self._show_error("Lambda must be > 0.")
                    return
                    
                max_k = int(max(x)) + 2
                kv = np.arange(0, max_k)
                pmf = [calc.get_poisson(k, lam) for k in kv]
                
                self.ax.bar(kv, pmf, color=theme.CURVE_4, edgecolor=theme.BG1, alpha=0.8)
                self._auto_scale(kv, pmf)
                self._add_summary_row("Lambda (λ)", f"{lam:.4f}")
                self._add_summary_row("Model", "Poisson Distribution")

    # --- Interactions ---
    def zoom_in(self): self._apply_zoom(0.8)
    def zoom_out(self): self._apply_zoom(1.25)

    def reset_view(self):
        if self.is_stats_mode: self.draw()
        else:
            self.ax.set_xlim(-10, 10)
            self.ax.set_ylim(-10, 10)
            self.canvas.draw()

    def _apply_zoom(self, f):
        xl, yl = self.ax.get_xlim(), self.ax.get_ylim()
        xc, yc = (xl[0] + xl[1]) / 2, (yl[0] + yl[1]) / 2
        self.ax.set_xlim(xc + (xl[0] - xc) * f, xc + (xl[1] - xc) * f)
        self.ax.set_ylim(yc + (yl[0] - yc) * f, yc + (yl[1] - yc) * f)
        self.canvas.draw()

    def _on_scroll(self, event):
        if event.inaxes != self.ax: return
        self._apply_zoom(0.8 if event.button == 'up' else 1.25)

    def _on_press(self, event):
        if event.inaxes != self.ax: return
        self._drag_start = (event.xdata, event.ydata)
        self._xlim_start = self.ax.get_xlim()
        self._ylim_start = self.ax.get_ylim()

    def _on_motion(self, event):
        if self._drag_start is None or event.inaxes != self.ax: return
        dx, dy = event.xdata - self._drag_start[0], event.ydata - self._drag_start[1]
        self.ax.set_xlim(self._xlim_start[0] - dx, self._xlim_start[1] - dx)
        self.ax.set_ylim(self._ylim_start[0] - dy, self._ylim_start[1] - dy)
        self.canvas.draw()

    def _on_release(self, event):
        self._drag_start = None