import customtkinter as ctk
import theme
import calculations as calc

class StatisticsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=theme.BG1)
        self.app = app
        self.data_x = []
        self.data_y = []
        
        # --- 1. Data Entry Area ---
        entry_frame = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        entry_frame.pack(fill="x", padx=14, pady=(0, 6))
        
        # X Entry
        row_x = ctk.CTkFrame(entry_frame, fg_color="transparent")
        row_x.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(row_x, text="Data (X):", font=theme.FONT_KEY, text_color=theme.TEXT).pack(side="left")
        self.entry_x = ctk.CTkEntry(row_x, font=theme.FONT_KEY, fg_color=theme.BG1, text_color=theme.TEXT)
        self.entry_x.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_x.bind("<Return>", lambda e: self.add_x())
        ctk.CTkButton(row_x, text="Add", width=50, fg_color=theme.BTN_OP, text_color=theme.TEXT, command=self.add_x).pack(side="right")
        
        # X Viewer
        self.view_x = ctk.CTkTextbox(entry_frame, height=30, font=theme.FONT_HISTORY, fg_color=theme.BG1, text_color=theme.TEXT_MUTED, wrap="word")
        self.view_x.pack(fill="x", padx=10, pady=(0, 10))
        self.view_x.insert("end", "No X data entered yet.")
        self.view_x.configure(state="disabled")
        
        # Y Entry (Optional)
        row_y = ctk.CTkFrame(entry_frame, fg_color="transparent")
        row_y.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkLabel(row_y, text="Data (Y):", font=theme.FONT_KEY, text_color=theme.TEXT).pack(side="left")
        self.entry_y = ctk.CTkEntry(row_y, font=theme.FONT_KEY, fg_color=theme.BG1, text_color=theme.TEXT)
        self.entry_y.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_y.bind("<Return>", lambda e: self.add_y())
        ctk.CTkButton(row_y, text="Add", width=50, fg_color=theme.BTN_OP, text_color=theme.TEXT, command=self.add_y).pack(side="right")

        # Y Viewer
        self.view_y = ctk.CTkTextbox(entry_frame, height=30, font=theme.FONT_HISTORY, fg_color=theme.BG1, text_color=theme.TEXT_MUTED, wrap="word")
        self.view_y.pack(fill="x", padx=10, pady=(0, 10))
        self.view_y.insert("end", "No Y data entered yet (Optional).")
        self.view_y.configure(state="disabled")

        # --- 2. Function Buttons ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=6)
        
        buttons = [
            ("Q1", self.show_q1), ("Q3", self.show_q3), ("IQR", self.show_iqr), ("Mode", self.show_mode),
            ("Samp Var", self.show_vars), ("Pop Var", self.show_varp), ("Std (σ)", self.show_stdp), ("Clear All", self.clear_all),
            ("Corr (r)", self.show_r), ("Slope (m)", self.show_m), ("Y-Int (b)", self.show_b)
        ]
        
        for i, (label, cmd) in enumerate(buttons):
            r, c = divmod(i, 4)
            btn_frame.grid_columnconfigure(c, weight=1)
            fg = theme.BTN_CLEAR if label == "Clear All" else theme.BTN_SCI
            ctk.CTkButton(btn_frame, text=label, font=theme.FONT_KEY, fg_color=fg, text_color=theme.TEXT, 
                          hover_color=theme.BTN_HOVER, corner_radius=theme.RADIUS, command=cmd).grid(row=r, column=c, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(btn_frame, text="📈 View Graph", font=theme.FONT_KEY, fg_color=theme.BTN_EQ, text_color=theme.TEXT_LIGHT, 
                      hover_color=theme.BTN_HOVER, corner_radius=theme.RADIUS, command=self.show_graph).grid(row=3, column=0, columnspan=4, padx=3, pady=(6, 3), sticky="ew")

        # --- 3. Live Summary ---
        self.summary_frame = ctk.CTkScrollableFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        self.summary_frame.pack(fill="both", expand=True, padx=14, pady=(6, 10))
        
        self.update_summary()

    def parse_input(self, text):
        text = text.replace(",", " ")
        return [float(x) for x in text.split() if x.strip()]

    def add_x(self):
        try:
            vals = self.parse_input(self.entry_x.get())
            if vals:
                self.data_x.extend(vals)
                self.entry_x.delete(0, "end")
                self.update_summary()
        except ValueError:
            self.app._update_result("Error: Invalid X input")

    def add_y(self):
        try:
            vals = self.parse_input(self.entry_y.get())
            if vals:
                self.data_y.extend(vals)
                self.entry_y.delete(0, "end")
                self.update_summary()
        except ValueError:
            self.app._update_result("Error: Invalid Y input")

    def clear_all(self):
        self.data_x = []
        self.data_y = []
        self.update_summary()

    def update_summary(self):
        # Update Data Viewers
        self.view_x.configure(state="normal")
        self.view_x.delete("1.0", "end")
        self.view_x.insert("end", ", ".join(f"{v:g}" for v in self.data_x) if self.data_x else "No X data entered yet.")
        self.view_x.configure(state="disabled")

        self.view_y.configure(state="normal")
        self.view_y.delete("1.0", "end")
        self.view_y.insert("end", ", ".join(f"{v:g}" for v in self.data_y) if self.data_y else "No Y data entered yet (Optional).")
        self.view_y.configure(state="disabled")

        # Clear old summary
        for w in self.summary_frame.winfo_children():
            w.destroy()

        has_x = len(self.data_x) > 0
        has_y = len(self.data_y) > 0
        
        if not has_x and not has_y:
            ctk.CTkLabel(self.summary_frame, text="Enter data to see results.", font=theme.FONT_KEY, text_color=theme.TEXT_MUTED).pack(pady=20)
            return

        # 1. Data X Summary
        if has_x:
            x_stats = calc.get_descriptive_stats(self.data_x)
            core_x_keys = ["n (Count)", "Mean", "Median", "Std (s)"]
            core_x = {k: x_stats[k] for k in core_x_keys if k in x_stats}
            self._build_summary_card("📊 Data X Overview", core_x)
            
        # 2. Data Y Summary
        if has_y:
            ctk.CTkFrame(self.summary_frame, height=10, fg_color="transparent").pack()
            y_stats = calc.get_descriptive_stats(self.data_y)
            core_y_keys = ["n (Count)", "Mean", "Median", "Std (s)"]
            core_y = {k: y_stats[k] for k in core_y_keys if k in y_stats}
            self._build_summary_card("📊 Data Y Overview", core_y)

    def _build_summary_card(self, title, stats_dict):
        ctk.CTkLabel(self.summary_frame, text=title, font=theme.FONT_KEY, text_color=theme.TEXT, anchor="w").pack(fill="x", pady=(5, 2))
        for key, val in stats_dict.items():
            val_str = f"{val:.4f}" if isinstance(val, float) else str(val)
            row = ctk.CTkFrame(self.summary_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=key, font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=val_str, font=theme.FONT_KEY, text_color=theme.TEXT, anchor="e").pack(side="right", padx=10)

    def _get_stat(self, key, is_reg=False):
        if is_reg:
            data = calc.get_regression_stats(self.data_x, self.data_y)
        else:
            data = calc.get_descriptive_stats(self.data_x)
            
        val = data.get(key)
        if val is not None:
            # Instead of a local label, send it straight to the History box on the main screen
            self.app._update_result(f"{key} = {val:.4f}")
            self.app._record(f"{key}", val)
        else:
            self.app._update_result(f"Cannot compute: Need more data.")

    def show_q1(self): self._get_stat("Q1")
    def show_q3(self): self._get_stat("Q3")
    def show_iqr(self): self._get_stat("IQR")
    def show_mode(self): self._get_stat("Mode")
    def show_vars(self): self._get_stat("Var (s²)")
    def show_varp(self): self._get_stat("Var (σ²)")
    def show_stdp(self): self._get_stat("Std (σ)")
    
    def show_r(self): self._get_stat("Corr (r)", is_reg=True)
    def show_m(self): self._get_stat("Slope (m)", is_reg=True)
    def show_b(self): self._get_stat("Y-Int (b)", is_reg=True)
    
    def show_graph(self):
        self.app._open_graph_view(self.data_x, self.data_y)