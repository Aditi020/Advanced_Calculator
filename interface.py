"""
interface.py
------------
"""
import customtkinter as ctk
import tkinter as tk
import theme
import calculations as calc
import math
import time
import json
import os
from keypads import SCIENTIFIC_KEYS, ADVANCED_KEYS
from statistics_mode import StatisticsFrame
from graph import GraphFrame

MENU_FONT = ("Segoe UI", 16)
HISTORY_FILE = "history.json"

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

        self.wizard = {
            "active": False,
            "type": None,
            "step": 0,
            "data": [],
            "prompts": []
        }

        self._load_history()
        self._build_header()
        self._build_mode_bar()
        self._build_display()
        self._build_keypad()
        self._build_history()
        self._bind_keys()
        
        self._start_history_cleanup()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        import matplotlib.pyplot as plt
        plt.close('all')
        self.quit()
        self.destroy()

    def _start_wizard(self, wizard_type, prompts):
        self.wizard = {
            "active": True,
            "type": wizard_type,
            "step": 0,
            "data": [],
            "prompts": prompts
        }
        self.expression = ""
        self.cursor_pos = 0
        self._update_result("")
        self._refresh_display()

    def _wizard_capture(self):
        try:
            val = calc.evaluate(self.expression, self.variables, self.angle_mode)
        except Exception:
            self._update_result("Error: Enter a valid number")
            self.expression = ""
            self._refresh_display()
            return

        self.wizard["data"].append(val)
        self.wizard["step"] += 1
        self.expression = ""
        
        if self.wizard["step"] >= len(self.wizard["prompts"]):
            self.wizard["active"] = False
            w_type = self.wizard["type"]
            w_data = self.wizard["data"]
            
            if w_type == "eqn_2var":
                res = calc.solve_linear_system(*w_data)
            elif w_type in ["eqn_quad", "eqn_cubic"]:
                res = calc.solve_polynomial(w_data)
            elif w_type == "ncr":
                res = str(math.comb(int(w_data[0]), int(w_data[1])))
            elif w_type == "npr":
                res = str(math.perm(int(w_data[0]), int(w_data[1])))
            else:
                res = "Error"
                
            self._update_result(res)
            self._record(f"{w_type}({', '.join(map(str,w_data))})", res)
        
        self._refresh_display()

    def _load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    saved_history = json.load(f)
                current_time = time.time()
                self.history = [item for item in saved_history if current_time - item[2] < 3600]
            except Exception:
                self.history = []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump(self.history, f)
        except Exception:
            pass

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
            for c, key_data in enumerate(row):
                self.keypad_frame.grid_columnconfigure(c, weight=1)
                
                label, insert, style = key_data[:3]
                offset = key_data[3] if len(key_data) > 3 else 0
                
                # --- NEW: Highlight DEG/RAD if active ---
                if label == "DEG" and self.angle_mode == "DEG":
                    bg = theme.BTN_EQ
                    fg = theme.TEXT_LIGHT
                elif label == "RAD" and self.angle_mode == "RAD":
                    bg = theme.BTN_EQ
                    fg = theme.TEXT_LIGHT
                else:
                    bg = {"num": theme.BTN_NUM, "op": theme.BTN_OP, "sci": theme.BTN_SCI, "eq": theme.BTN_EQ, "clear": theme.BTN_CLEAR}[style]
                    fg = theme.TEXT_LIGHT if style == "eq" else theme.TEXT
                
                ctk.CTkButton(self.keypad_frame, text=label, font=theme.FONT_KEY, fg_color=bg, hover_color=theme.BTN_HOVER, text_color=fg,
                              corner_radius=theme.RADIUS, command=lambda l=label, i=insert, o=offset: self._press(l, i, o)
                              ).grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

    def _build_history(self):
        self.history_frame = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        self.history_frame.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(self.history_frame, text="History", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=10, pady=(6, 0))
        
        self.history_box = ctk.CTkTextbox(self.history_frame, height=90, font=theme.FONT_HISTORY, fg_color=theme.BG2, text_color=theme.TEXT)
        self.history_box.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        
        for item in self.history:
            expr, val = item[0], item[1]
            if isinstance(val, str):
                self.history_box.insert("end", f"{expr} -> {val}\n")
            else:
                self.history_box.insert("end", f"{expr} = {val:.6g}\n")
        self.history_box.see("end")

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
        if self.wizard["active"]:
            prompt = self.wizard["prompts"][self.wizard["step"]]
            text = f"{prompt}: {self.expression}|"
            self.expr_label.configure(text=text)
            return

        text = self.expression or " "
        if 0 <= self.cursor_pos <= len(self.expression):
            text = text[:self.cursor_pos] + "|" + text[self.cursor_pos:]
        self.expr_label.configure(text=text)

    def _toggle_frac(self):
        self.is_fraction = not self.is_fraction
        self.frac_label.configure(text_color=theme.BTN_EQ if self.is_fraction else theme.TEXT_MUTED)
        current_val = self.result_box.get("1.0", "end").strip()
        if current_val and current_val != "0" and "Error" not in current_val:
            try:
                val = float(current_val)
                self._update_result(calc.format_result(val, self.is_fraction))
            except ValueError:
                pass

    def _show_log_menu(self):
        # Removed 'ln' from here since it's a dedicated button on the keypad.
        menu = tk.Menu(self, tearoff=0, bg=theme.BG2, fg=theme.TEXT, font=MENU_FONT, activebackground=theme.BTN_OP, activeforeground=theme.TEXT)
        menu.add_command(label="log₁₀", command=lambda: self._press("log10", "log10()", 1))
        menu.add_command(label="logₙ (custom)", command=lambda: self._press("log", "log(, )", 2))
        try:
            x, y = self.winfo_pointerx(), self.winfo_pointery()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _show_eqn_menu(self):
        menu = tk.Menu(self, tearoff=0, bg=theme.BG2, fg=theme.TEXT, font=MENU_FONT, activebackground=theme.BTN_OP, activeforeground=theme.TEXT)
        menu.add_command(label="2-Variable System", command=lambda: self._start_wizard("eqn_2var", ["Enter a", "Enter b", "Enter c", "Enter d", "Enter e", "Enter f"]))
        menu.add_command(label="Quadratic", command=lambda: self._start_wizard("eqn_quad", ["Enter a", "Enter b", "Enter c"]))
        menu.add_command(label="Cubic", command=lambda: self._start_wizard("eqn_cubic", ["Enter a", "Enter b", "Enter c", "Enter d"]))
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

    def _press(self, label, insert, offset=0):
        if "Error" in self.result_box.get("1.0", "end"):
            self._update_result("")

        if label == "AC":
            self.wizard["active"] = False
            self.expression, self.last_result, self.cursor_pos = "", None, 0
            self.history_box.delete("1.0", "end")
            self.history = []
            self._save_history()
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
            
        # --- NEW: Redraw keys when DEG/RAD is pressed so color updates ---
        if label == "DEG":
            self.angle_mode = "DEG"
            self._refresh_display()
            self._render_keys() 
            return
        if label == "RAD":
            self.angle_mode = "RAD"
            self._refresh_display()
            self._render_keys()
            return
            
        if label == "+/-":
            self.expression = f"-({self.expression})"
            self.cursor_pos = len(self.expression)
            self._refresh_display(); return
        
        if label == "log":
            self._show_log_menu(); return
        if label == "EQN":
            self._show_eqn_menu(); return
        if label == "nCr":
            self._start_wizard("ncr", ["Enter n", "Enter r"]); return
        if label == "nPr":
            self._start_wizard("npr", ["Enter n", "Enter r"]); return
        if label == "=":
            self._calculate(); return

        if insert is not None:
            self._insert_text(insert)
            if offset > 0:
                self.cursor_pos -= offset
                self._refresh_display()

    def _calculate(self):
        if self.wizard["active"]:
            self._wizard_capture()
            return

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
        self.history.append((expr, value, time.time()))
        self._save_history()
        
        if isinstance(value, str):
            self.history_box.insert("end", f"{expr} -> {value}\n")
        else:
            self.history_box.insert("end", f"{expr} = {value:.6g}\n")
        self.history_box.see("end")

    def _start_history_cleanup(self):
        current_time = time.time()
        new_history = []
        for item in self.history:
            if len(item) == 3:
                if current_time - item[2] < 3600:
                    new_history.append(item)
            else:
                new_history.append((item[0], item[1], current_time))
        
        if len(new_history) < len(self.history):
            self.history = new_history
            self._save_history()
            
            self.history_box.delete("1.0", "end")
            for expr, val, _ in self.history:
                if isinstance(val, str):
                    self.history_box.insert("end", f"{expr} -> {val}\n")
                else:
                    self.history_box.insert("end", f"{expr} = {val:.6g}\n")
        
        self.after(60000, self._start_history_cleanup)

    def _is_typing(self):
        focused = self.focus_get()
        return isinstance(focused, (ctk.CTkEntry, tk.Entry))

    def _bind_keys(self):
        self.bind("<Return>",    lambda e: self._press("=", None) if not self._is_typing() else None)
        self.bind("<BackSpace>", lambda e: self._press("⌫", None) if not self._is_typing() else None)
        self.bind("<Escape>",    lambda e: self._press("AC", None) if not self._is_typing() else None)
        self.bind("<Left>",      lambda e: self._press("<", None) if not self._is_typing() else None)
        self.bind("<Right>",     lambda e: self._press(">", None) if not self._is_typing() else None)
        
        for ch in "0123456789.+-*/()%=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_": 
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