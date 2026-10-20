import customtkinter as ctk
import tkinter as tk
import theme
import calculations as calc
import math
from keypads import SCIENTIFIC_KEYS, ADVANCED_KEYS
from statistics_mode import StatisticsFrame
from graph import GraphFrame

MENU_FONT = ("Segoe UI", 16)

class InputWindow(ctk.CTkToplevel):
    def __init__(self, parent, title_str, labels, calc_func):
        super().__init__(parent)
        self.title(title_str)
        self.title_str = title_str
        self.geometry("250x200")
        self.configure(fg_color=theme.BG1)
        self.attributes("-topmost", True)
        self.calc_func = calc_func
        self.parent_app = parent

        ctk.CTkLabel(self, text=title_str, font=theme.FONT_TITLE, text_color=theme.TEXT).pack(pady=10)
        self.entries = []
        for lbl in labels:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(row, text=f"{lbl}:", width=40, text_color=theme.TEXT).pack(side="left")
            e = ctk.CTkEntry(row, width=80)
            e.pack(side="right")
            self.entries.append(e)
        
        for i, e in enumerate(self.entries):
            if i < len(self.entries) - 1:
                e.bind("<Return>", lambda ev, nxt=self.entries[i+1]: nxt.focus_set())
            else:
                e.bind("<Return>", lambda ev: self._solve())

        ctk.CTkButton(self, text="Solve", fg_color=theme.BTN_EQ, command=self._solve).pack(pady=15)
        self.entries[0].focus_set()

    def _solve(self):
        try:
            vals = [float(e.get().strip()) for e in self.entries]
            res = self.calc_func(*vals)
            
            self.parent_app.expression = ""
            self.parent_app.cursor_pos = 0
            self.parent_app._refresh_display()
            
            self.parent_app._update_result(str(res))
            self.parent_app._record(f"{self.title_str}({', '.join(map(str, vals))})", res)
            self.destroy()
        except Exception as e:
            self.parent_app._update_result(f"Error: {e}")
            self.destroy()

class EquationSolverWindow(ctk.CTkToplevel):
    def __init__(self, parent, eq_type="2-Variable System"):
        super().__init__(parent)
        self.title("Equation Solver")
        self.geometry("340x450")
        self.configure(fg_color=theme.BG1)
        self.attributes("-topmost", True)
        self.parent_app = parent

        ctk.CTkLabel(self, text="Equation Solver", font=theme.FONT_TITLE, text_color=theme.TEXT).pack(pady=(15, 5))
        
        self.eq_type_var = tk.StringVar(value=eq_type)
        self.dropdown = ctk.CTkOptionMenu(
            self, variable=self.eq_type_var,
            values=["2-Variable System", "Quadratic", "Cubic"],
            width=220,
            fg_color=theme.BTN_OP, text_color=theme.TEXT,
            button_color=theme.BTN_SCI, button_hover_color=theme.BTN_HOVER,
            font=theme.FONT_KEY
        )
        self.dropdown.pack(pady=5)
        self.dropdown.configure(command=self.change_layout)

        self.ref_label = ctk.CTkLabel(self, text="", font=theme.FONT_KEY, text_color=theme.TEXT_MUTED)
        self.ref_label.pack(pady=(15, 5))

        self.inputs_frame = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=10)
        self.inputs_frame.pack(pady=15, padx=20, fill="x")
        
        self.result_box = ctk.CTkTextbox(self, height=60, font=theme.FONT_DISPLAY, fg_color=theme.BG1, text_color=theme.TEXT, wrap="word")
        self.result_box.pack(pady=(10, 15), padx=20, fill="both", expand=True)

        self.change_layout(self.eq_type_var.get())

    def change_layout(self, choice):
        for w in self.inputs_frame.winfo_children():
            w.destroy()
        
        self.entries = {}
        if choice == "2-Variable System":
            self.ref_label.configure(text="ax + by + c = 0\ndx + ey + f = 0")
            fields = ["a", "b", "c", "d", "e", "f"]
        elif choice == "Quadratic":
            self.ref_label.configure(text="ax² + bx + c = 0")
            fields = ["a", "b", "c"]
        elif choice == "Cubic":
            self.ref_label.configure(text="ax³ + bx² + cx + d = 0")
            fields = ["a", "b", "c", "d"]

        for i, f in enumerate(fields):
            r, c = divmod(i, 2)
            row_frame = ctk.CTkFrame(self.inputs_frame, fg_color="transparent")
            row_frame.grid(row=r, column=c, padx=10, pady=8, sticky="ew")
            
            ctk.CTkLabel(row_frame, text=f"{f}:", width=20, font=theme.FONT_KEY, text_color=theme.TEXT).pack(side="left")
            e = ctk.CTkEntry(row_frame, width=70, font=theme.FONT_KEY)
            e.pack(side="right")
            self.entries[f] = e

        self.inputs_frame.grid_columnconfigure(0, weight=1)
        self.inputs_frame.grid_columnconfigure(1, weight=1)

        entry_list = list(self.entries.values())
        for i, e in enumerate(entry_list):
            if i < len(entry_list) - 1:
                e.bind("<Return>", lambda ev, nxt=entry_list[i+1]: nxt.focus_set())
            else:
                e.bind("<Return>", lambda ev: self.solve(choice))
        
        btn_frame = ctk.CTkFrame(self.inputs_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        ctk.CTkButton(btn_frame, text="Clear", width=80, fg_color=theme.BTN_CLEAR, text_color=theme.TEXT, font=theme.FONT_KEY, command=self.clear_inputs).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Solve", width=80, fg_color=theme.BTN_EQ, text_color=theme.TEXT_LIGHT, font=theme.FONT_KEY, command=lambda: self.solve(choice)).pack(side="left", padx=5)

        if entry_list:
            entry_list[0].focus_set()

    def clear_inputs(self):
        for e in self.entries.values():
            e.delete(0, "end")
        self.result_box.delete("1.0", "end")
        if self.entries:
            list(self.entries.values())[0].focus_set()

    def solve(self, choice):
        try:
            vals = []
            for e in self.entries.values():
                val_str = e.get().strip()
                vals.append(float(val_str) if val_str else 0.0)
                
            if choice == "2-Variable System":
                res = calc.solve_linear_system(*vals)
            else:
                res = calc.solve_polynomial(vals)
            
            self.result_box.delete("1.0", "end")
            self.result_box.insert("end", res)
            
            self.parent_app.expression = ""
            self.parent_app.cursor_pos = 0
            self.parent_app._refresh_display()
            
            self.parent_app._update_result(res)
            self.parent_app._record(f"EQN: {choice}", res)
            
        except ValueError:
            self.result_box.delete("1.0", "end")
            self.result_box.insert("end", "Error: Enter valid numbers")
        except Exception as e:
            self.result_box.delete("1.0", "end")
            self.result_box.insert("end", f"Error: {e}")


class CalcApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Calc")
        self.geometry(f"{theme.WIN_W}x{theme.WIN_H}")
        self.minsize(380, 640)
        self.configure(fg_color=theme.BG1)

        self.mode        = "sci"
        self.expression  = ""
        self.cursor_pos  = 0
        self.angle_mode  = "DEG"
        self.is_fraction = False
        self.variables   = {}
        self.history     = []
        self.last_result = None
        self.previous_view = "sci"

        self._build_header()
        self._build_mode_bar()
        self._build_display()
        self._build_keypad()
        self._build_history()
        self._bind_keys()

    def _build_header(self):
        h = ctk.CTkFrame(self, fg_color=theme.BG1)
        h.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(h, text="Calc", font=theme.FONT_TITLE, text_color=theme.TEXT).pack(side="left")
        ctk.CTkLabel(h, text="SCIENTIFIC & ANALYTICAL", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED).pack(side="left", padx=10, pady=(8, 0))

    def _build_mode_bar(self):
        bar = ctk.CTkFrame(self, fg_color=theme.BG1)
        bar.pack(fill="x", padx=14, pady=(8, 4))
        self._mode_btns = {}
        modes = [("⌂", "sci"), ("Advanced", "adv"), ("Statistics", "stat")]
        for label, key in modes:
            b = ctk.CTkButton(bar, text=label, height=30,
                              font=theme.FONT_KEY if key=="sci" else theme.FONT_SUBTITLE,
                              corner_radius=theme.RADIUS, fg_color=theme.BG2, hover_color=theme.BTN_HOVER,
                              text_color=theme.TEXT, command=lambda k=key: self._set_mode(k))
            b.pack(side="left", expand=True, fill="x", padx=3)
            self._mode_btns[key] = b
        self._paint_mode_buttons()

    def _build_display(self):
        self.display_frame = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        self.display_frame.pack(fill="x", padx=14, pady=8)
        
        top_row = ctk.CTkFrame(self.display_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=12, pady=(6, 0))
        
        self.frac_label = ctk.CTkLabel(top_row, text="S⇔D", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED, cursor="hand2")
        self.frac_label.pack(side="left")
        self.frac_label.bind("<Button-1>", lambda e: self._toggle_frac())

        self.mode_label = ctk.CTkLabel(top_row, text="DEG", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED, cursor="hand2")
        self.mode_label.pack(side="right")
        self.mode_label.bind("<Button-1>", lambda e: self._press("DEG", None))
        
        self.expr_label = ctk.CTkLabel(self.display_frame, text=" ", font=theme.FONT_DISPLAY, text_color=theme.TEXT_MUTED, anchor="e")
        self.expr_label.pack(fill="x", padx=12)
        
        self.result_box = ctk.CTkTextbox(self.display_frame, height=45, font=theme.FONT_RESULT, fg_color=theme.BG2, text_color=theme.TEXT, wrap="word")
        self.result_box.pack(fill="x", padx=12, pady=(0, 10))
        self.result_box.insert("end", "0")
        self.result_box.configure(state="disabled")

    def _update_result(self, text):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", text)
        self.result_box.configure(state="disabled")
        self.result_box.see("end")

    def _build_keypad(self):
        self.keypad_frame = ctk.CTkFrame(self, fg_color=theme.BG1)
        self.stats_frame = StatisticsFrame(self, self)
        self.graph_frame = GraphFrame(self, self)
        
        self.keypad_frame.pack(fill="both", expand=True, padx=14, pady=6)
        self._render_keys()

    def _render_keys(self):
        for w in self.keypad_frame.winfo_children(): w.destroy()
        keys = SCIENTIFIC_KEYS if self.mode == "sci" else ADVANCED_KEYS
        for r, row in enumerate(keys):
            self.keypad_frame.grid_rowconfigure(r, weight=1)
            for c, (label, insert, style) in enumerate(row):
                self.keypad_frame.grid_columnconfigure(c, weight=1)
                bg = {"num": theme.BG2, "op": theme.BTN_OP, "sci": theme.BTN_SCI, "eq": theme.BTN_EQ, "clear": theme.BTN_CLEAR}[style]
                fg = theme.TEXT_LIGHT if style == "eq" else theme.TEXT
                
                ctk.CTkButton(self.keypad_frame, text=label, font=theme.FONT_KEY, fg_color=bg, hover_color=theme.BTN_HOVER, text_color=fg,
                              corner_radius=theme.RADIUS, command=lambda l=label, i=insert: self._press(l, i)
                              ).grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

    def _build_history(self):
        self.history_frame = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        self.history_frame.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(self.history_frame, text="History", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=10, pady=(6, 0))
        self.history_box = ctk.CTkTextbox(self.history_frame, height=70, font=theme.FONT_HISTORY, fg_color=theme.BG2, text_color=theme.TEXT)
        self.history_box.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    def _set_mode(self, key):
        self.mode = key
        self._paint_mode_buttons()
        
        self.display_frame.pack_forget()
        self.keypad_frame.pack_forget()
        self.history_frame.pack_forget()
        self.stats_frame.pack_forget()
        self.graph_frame.pack_forget()

        if key == "stat":
            self.stats_frame.pack(fill="both", expand=True, padx=14, pady=6)
        else:
            self.display_frame.pack(fill="x", padx=14, pady=8)
            self.keypad_frame.pack(fill="both", expand=True, padx=14, pady=6)
            self.history_frame.pack(fill="x", padx=14, pady=(0, 12))
            self._render_keys()

    def _paint_mode_buttons(self):
        for k, b in self._mode_btns.items(): b.configure(fg_color=theme.BTN_OP if k == self.mode else theme.BG2)

    def _refresh_display(self):
        text = self.expression or " "
        if 0 <= self.cursor_pos <= len(self.expression):
            text = text[:self.cursor_pos] + "|" + text[self.cursor_pos:]
        self.expr_label.configure(text=text)
        self.mode_label.configure(text=self.angle_mode)

    def _toggle_frac(self):
        self.is_fraction = not self.is_fraction
        self.frac_label.configure(text_color=theme.BTN_EQ if self.is_fraction else theme.TEXT_MUTED)

    def _show_log_menu(self):
        menu = tk.Menu(self, tearoff=0, bg=theme.BG2, fg=theme.TEXT, font=MENU_FONT, activebackground=theme.BTN_OP, activeforeground=theme.TEXT)
        menu.add_command(label="log₁₀", command=lambda: self._insert_text("log10("))
        menu.add_command(label="log₂", command=lambda: self._insert_text("log2("))
        menu.add_command(label="ln", command=lambda: self._insert_text("ln("))
        menu.add_command(label="custom base", command=lambda: InputWindow(self, "Log Base", ["x", "base"], calc_log_base))
        try:
            x, y = self.winfo_pointerx(), self.winfo_pointery()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _show_eqn_menu(self):
        menu = tk.Menu(self, tearoff=0, bg=theme.BG2, fg=theme.TEXT, font=MENU_FONT, activebackground=theme.BTN_OP, activeforeground=theme.TEXT)
        menu.add_command(label="2-Variable System", command=lambda: EquationSolverWindow(self, "2-Variable System"))
        menu.add_command(label="Quadratic", command=lambda: EquationSolverWindow(self, "Quadratic"))
        menu.add_command(label="Cubic", command=lambda: EquationSolverWindow(self, "Cubic"))
        try:
            x, y = self.winfo_pointerx(), self.winfo_pointery()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _insert_text(self, insert):
        if insert in ["+", "-", "*", "/", "%", "**", "mod("] and self.expression == "" and self.last_result is not None:
            self.expression = f"{self.last_result:.10g}"
            self.cursor_pos = len(self.expression)
        
        self.expression = self.expression[:self.cursor_pos] + insert + self.expression[self.cursor_pos:]
        self.cursor_pos += len(insert)
        self._refresh_display()

    def _press(self, label, insert):
        if "Error" in self.result_box.get("1.0", "end"):
            self._update_result("")

        if label == "AC":
            self.expression, self.last_result, self.cursor_pos = "", None, 0
            self.history_box.delete("1.0", "end")
            self.history = []
            self._update_result("0")
            self._refresh_display(); return
        if label == "C":
            self.expression, self.cursor_pos = "", 0
            self._update_result("0")
            self._refresh_display(); return
        if label == "⌫":
            if self.cursor_pos > 0:
                self.expression = self.expression[:self.cursor_pos-1] + self.expression[self.cursor_pos:]
                self.cursor_pos -= 1
            self._refresh_display(); return
        if label == "<":
            if self.cursor_pos > 0: self.cursor_pos -= 1
            self._refresh_display(); return
        if label == ">":
            if self.cursor_pos < len(self.expression): self.cursor_pos += 1
            self._refresh_display(); return
        if label == "DEG":
            self.angle_mode = "RAD" if self.angle_mode == "DEG" else "DEG"
            self._refresh_display(); return
        if label == "+/-":
            self.expression = f"-({self.expression})"
            self.cursor_pos = len(self.expression)
            self._refresh_display(); return
        
        if label == "log":
            self._show_log_menu(); return
        if label == "EQN":
            self._show_eqn_menu(); return
        if label == "nCr":
            InputWindow(self, "nCr", ["n", "r"], calc_comb); return
        if label == "nPr":
            InputWindow(self, "nPr", ["n", "r"], calc_perm); return
        if label == "=":
            self._calculate(); return

        if insert is not None:
            self._insert_text(insert)

    def _calculate(self):
        expr = self.expression.strip()
        if not expr: return
        
        try:
            assigned = calc.try_assignment(expr, self.variables, self.angle_mode)
            if assigned is not None:
                self._update_result(calc.format_result(assigned, self.is_fraction))
                self._record(expr, assigned)
                self.expression, self.cursor_pos = "", 0
                self._refresh_display(); return
        except Exception:
            pass

        try:
            value = calc.evaluate(expr, self.variables, self.angle_mode)
        except Exception as e:
            self._update_result(f"Error: {e}")
            return
            
        self.variables["Ans"] = value
        self.last_result = value
        self._update_result(calc.format_result(value, self.is_fraction))
        self._record(expr, value)
        self.expression, self.cursor_pos = "", 0
        self._refresh_display()

    def _record(self, expr, value):
        self.history.append((expr, value))
        if isinstance(value, str):
            self.history_box.insert("end", f"{expr} -> {value}\n")
        else:
            self.history_box.insert("end", f"{expr} = {value:.6g}\n")
        self.history_box.see("end")

    # --- THE FIX: Ignore keyboard shortcuts if typing in an Entry box ---
    def _is_typing(self):
        focused = self.focus_get()
        return isinstance(focused, (ctk.CTkEntry, tk.Entry))

    def _bind_keys(self):
        self.bind("<Return>",    lambda e: self._press("=", None) if not self._is_typing() else None)
        self.bind("<BackSpace>", lambda e: self._press("⌫", None) if not self._is_typing() else None)
        self.bind("<Escape>",    lambda e: self._press("AC", None) if not self._is_typing() else None)
        self.bind("<Left>",      lambda e: self._press("<", None) if not self._is_typing() else None)
        self.bind("<Right>",     lambda e: self._press(">", None) if not self._is_typing() else None)
        
        for ch in "0123456789.+-*/()%": 
            self.bind(ch, lambda e, c=ch: self._insert_text(c) if not self._is_typing() else None)
        self.bind("^", lambda e: self._insert_text("**") if not self._is_typing() else None)

    def _open_graph_view(self, x_data=None, y_data=None):
        self.previous_view = self.mode
        
        self.display_frame.pack_forget()
        self.keypad_frame.pack_forget()
        self.history_frame.pack_forget()
        self.stats_frame.pack_forget()
        
        if x_data is not None and y_data is not None:
            self.graph_frame.load_statistics(x_data, y_data)
        else:
            self.graph_frame.load_function_mode()

        self.graph_frame.pack(fill="both", expand=True, padx=14, pady=6)

    def _close_graph_view(self):
        self.graph_frame.pack_forget()
        self._set_mode(self.previous_view)

def calc_comb(n, r): return math.comb(int(n), int(r))
def calc_perm(n, r): return math.perm(int(n), int(r))
def calc_log_base(x, base):
    if base <= 0 or base == 1 or x <= 0:
        raise ValueError("Invalid log values")
    return f"{math.log(x, base):.4f}"