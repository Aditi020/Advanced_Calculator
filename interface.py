"""
This is the main Controller of the application. It builds the window, handles switching 
between modes (Scientific, Advanced, Stats, Graph), manages the inline "Solver" prompts, 
and binds physical keyboard inputs.

Key Libraries Used:
- customtkinter (ctk): For the modern, dark-themed UI widgets.
- tkinter (tk): Underlying Tkinter used for specific popups (Menus) and window management.
- json & os: To save and load the calculation history to a local file so it persists across restarts.
- time: To calculate timestamps for the 1-hour history expiration.
- matplotlib.pyplot: Imported locally in `on_closing` to cleanly shut down graph memory.
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
    """
    The main application window. 
    Inherits from CTk (CustomTkinter's main window class).
    """
    def __init__(self):
        super().__init__()
        self.title("Calculator")
        self.geometry(f"{theme.WIN_W}x{theme.WIN_H}")
        self.minsize(380, 640)
        self.configure(fg_color=theme.BG1)

        # --- Application State ---
        self.mode        = "sci"          # Current mode: "sci", "adv", or "stat"
        self.expression  = ""             # The math string currently being typed
        self.cursor_pos  = 0              # Where the blinking "|" cursor is placed
        self.angle_mode  = "DEG"          # "DEG" or "RAD"
        self.is_fraction = False          # False = Decimal (1.25), True = Fraction (5/4)
        
        self.variables   = {}             # Stores variables (e.g., {"a": 5, "b": 10})
        self.history     = []             # List of tuples: (expression, result, timestamp)
        self.last_result = None           # Stores the previous answer
        self.previous_view = "sci"        # Remembers where to return after closing the Graph

        # --- Solver State (For Inline Prompts like nCr, EQN) ---
        # Instead of opening a clunky popup window, the calculator goes into a "Solver" mode.
        # The display will ask "Enter a:", the user types a number and presses "=".
        self.solver = {
            "active": False,              # Is the sequence currently running?
            "type": None,                 # "ncr", "eqn_quad", etc.
            "step": 0,                    # Which prompt are we currently on?
            "data": [],                   # Stores the numbers the user has entered so far
            "prompts": [],                # e.g., ["Enter a", "Enter b", "Enter c"]
            "skeleton": ""                # The equation text shown at the top (e.g., "ax² + bx + c = 0")
        }

        # --- Build the UI ---
        self._load_history()              # Load saved history from JSON file
        self._build_header()
        self._build_mode_bar()
        self._build_display()
        self._build_keypad()
        self._build_history()
        self._bind_keys()                 # Bind physical keyboard events
        
        # --- Background Tasks & Close Handling ---
        self._start_history_cleanup()     # Start the 1-hour expiration timer
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle the "X" button

    def on_closing(self):
        """Safely closes Matplotlib plots to prevent terminal spam and memory leaks, then closes the app."""
        import matplotlib.pyplot as plt
        plt.close('all')
        self.quit()
        self.destroy()

    # ==========================================
    # SOLVER LOGIC (Inline Prompts)
    # ==========================================
    def _start_sequence(self, solver_type, prompts, skeleton=""):
        """
        Initializes the solver mode. 
        :param solver_type: The type of operation (e.g., "eqn_menu", "eqn_quad")
        :param prompts: List of prompts to show the user (e.g., ["a", "b", "c"])
        :param skeleton: The equation template shown at the top (e.g., "ax² + bx + c = 0")
        """
        self.solver = {
            "active": True,
            "type": solver_type,
            "step": 0,
            "data": [],
            "prompts": prompts,
            "skeleton": skeleton
        }
        self.expression = ""
        self.cursor_pos = 0
        self._refresh_display()
        self.update_idletasks()

    def _capture_sequence_input(self):
        """
        Triggered when the user presses '=' while a solver is active. 
        Captures the number, saves it, and either moves to the next prompt or calculates the final answer.
        """
        # --- SPECIAL CASE: The EQN Menu ---
        # When the user clicks EQN, we show a menu on screen. 
        # If they type '1' and press '=', it routes them to the 2-variable solver.
        if self.solver["type"] == "eqn_menu":
            try:
                choice = int(self.expression)
            except ValueError:
                self._update_result("Error: Enter 1, 2, or 3", scroll="end")
                self.expression = ""
                self._refresh_display()
                return
            
            self.expression = ""
            if choice == 1:
                self._start_sequence("eqn_2var", ["a", "b", "c", "d", "e", "f"], skeleton="ax + by + c = 0\ndx + ey + f = 0")
            elif choice == 2:
                self._start_sequence("eqn_quad", ["a", "b", "c"], skeleton="ax² + bx + c = 0")
            elif choice == 3:
                self._start_sequence("eqn_cubic", ["a", "b", "c", "d"], skeleton="ax³ + bx² + cx + d = 0")
            else:
                self._update_result("Error: Invalid choice (1-3)", scroll="end")
                self.expression = ""
                self._refresh_display()
            return

        # --- STANDARD INPUT CAPTURE ---
        # Now the user is typing a coefficient for a variable (like a=5)
        try:
            val = calc.evaluate(self.expression, self.variables, self.angle_mode)
        except Exception:
            self._update_result("Error: Enter a valid number", scroll="end")
            self.expression = ""
            return # Do not refresh display so error stays visible

        # Convert floats to integers if they are whole numbers (e.g., 1.0 -> 1)
        if isinstance(val, float) and val.is_integer():
            self.solver["data"].append(int(val))
        else:
            self.solver["data"].append(val)
            
        self.solver["step"] += 1
        self.expression = ""
        self.cursor_pos = 0 # Reset cursor when moving to the next variable
        
        # Check if we have collected ALL required numbers
        if self.solver["step"] >= len(self.solver["prompts"]):
            self.solver["active"] = False
            w_type = self.solver["type"]
            w_data = self.solver["data"]
            
            # Solve the equation based on the collected data
            try:
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
            except Exception as e:
                res = f"Error: {e}"
                
            # Display the final answer and save to history
            self._update_result(res, scroll="end")
            self._record(f"{w_type}({', '.join(map(str,w_data))})", res)
        
        self._refresh_display()

    # ==========================================
    # HISTORY MANAGEMENT (JSON Persistence)
    # ==========================================
    def _load_history(self):
        """Reads history.json on startup, keeping only entries younger than 1 hour (3600s)."""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    saved_history = json.load(f)
                current_time = time.time()
                self.history = [item for item in saved_history if current_time - item[2] < 3600]
            except Exception:
                self.history = []

    def _save_history(self):
        """Writes the current history list to history.json."""
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump(self.history, f)
        except Exception:
            pass

    def _start_history_cleanup(self):
        """Runs every 60 seconds to automatically delete history entries older than 1 hour."""
        current_time = time.time()
        new_history = []
        
        # Filter out old items
        for item in self.history:
            if len(item) == 3:
                if current_time - item[2] < 3600:
                    new_history.append(item)
            else:
                new_history.append((item[0], item[1], current_time))
        
        # If items were removed, update the file and redraw the visual history box
        if len(new_history) < len(self.history):
            self.history = new_history
            self._save_history()
            
            self.history_box.delete("1.0", "end")
            for expr, val, _ in self.history:
                if isinstance(val, str):
                    self.history_box.insert("end", f"{expr} -> {val}\n")
                else:
                    self.history_box.insert("end", f"{expr} = {val:.6g}\n")
        
        # Schedule the next cleanup in 60,000 milliseconds (60 seconds)
        self.after(60000, self._start_history_cleanup)

    # ==========================================
    # UI BUILDING METHODS
    # ==========================================
    def _build_header(self):
        h = ctk.CTkFrame(self, fg_color=theme.BG1)
        h.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(h, text="Calculator", font=theme.FONT_TITLE, text_color=theme.TEXT).pack(side="left")
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
        
        # Fixed height to prevent the UI from jumping when the skeleton loads
        self.expr_label = ctk.CTkLabel(self.display_frame, text=" ", font=theme.FONT_DISPLAY, text_color=theme.TEXT_MUTED, anchor="e", height=45)
        self.expr_label.pack(fill="x", padx=12)
        
        self.result_box = ctk.CTkTextbox(self.display_frame, height=60, font=theme.FONT_RESULT, fg_color=theme.BG2, text_color=theme.TEXT, wrap="word")
        self.result_box.pack(fill="x", padx=12, pady=(0, 10))
        self.result_box.insert("end", "0")
        self.result_box.configure(state="disabled")
        
        # FIX: Prevent the textbox from stealing focus when clicked, otherwise backspace breaks
        self.result_box.bind("<Button-1>", lambda e: "break")
        self.result_box._textbox.configure(takefocus=0)

    def _update_result(self, text, scroll="end"):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", text)
        self.result_box.configure(state="disabled")
        self.result_box.see(scroll)
        self.focus_set() # Force focus back to the main window so keyboard shortcuts work

    def _build_keypad(self):
        self.keypad_frame = ctk.CTkFrame(self, fg_color=theme.BG1)
        self.stats_frame = StatisticsFrame(self, self)
        self.graph_frame = GraphFrame(self, self)
        
        self.keypad_frame.pack(fill="both", expand=True, padx=14, pady=6)
        self._render_keys()

    def _build_history(self):
        self.history_frame = ctk.CTkFrame(self, fg_color=theme.BG2, corner_radius=theme.RADIUS)
        self.history_frame.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(self.history_frame, text="History", font=theme.FONT_SUBTITLE, text_color=theme.TEXT_MUTED, anchor="w").pack(fill="x", padx=10, pady=(6, 0))
        
        self.history_box = ctk.CTkTextbox(self.history_frame, height=90, font=theme.FONT_HISTORY, fg_color=theme.BG2, text_color=theme.TEXT)
        self.history_box.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.history_box.bind("<Button-1>", lambda e: "break")
        self.history_box._textbox.configure(takefocus=0)
        
        for item in self.history:
            expr, val = item[0], item[1]
            if isinstance(val, str):
                self.history_box.insert("end", f"{expr} -> {val}\n")
            else:
                self.history_box.insert("end", f"{expr} = {val:.6g}\n")
        self.history_box.see("end")

    # ==========================================
    # MODE & STATE MANAGEMENT
    # ==========================================
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
        for k, b in self._mode_btns.items(): 
            b.configure(fg_color=theme.BTN_OP if k == self.mode else theme.BG2)

    def _render_keys(self):
        """Dynamically draws the keypad from keypads.py, highlighting active DEG/RAD."""
        for w in self.keypad_frame.winfo_children(): w.destroy()
        keys = SCIENTIFIC_KEYS if self.mode == "sci" else ADVANCED_KEYS
        
        for r, row in enumerate(keys):
            self.keypad_frame.grid_rowconfigure(r, weight=1)
            for c, key_data in enumerate(row):
                self.keypad_frame.grid_columnconfigure(c, weight=1)
                
                label, insert, style = key_data[:3]
                offset = key_data[3] if len(key_data) > 3 else 0
                
                # Highlight DEG or RAD if active
                if label == "DEG" and self.angle_mode == "DEG":
                    bg, fg = theme.BTN_EQ, theme.TEXT_LIGHT
                elif label == "RAD" and self.angle_mode == "RAD":
                    bg, fg = theme.BTN_EQ, theme.TEXT_LIGHT
                else:
                    bg = {"num": theme.BTN_NUM, "op": theme.BTN_OP, "sci": theme.BTN_SCI, "eq": theme.BTN_EQ, "clear": theme.BTN_CLEAR}[style]
                    fg = theme.TEXT_LIGHT if style == "eq" else theme.TEXT
                
                ctk.CTkButton(self.keypad_frame, text=label, font=theme.FONT_KEY, fg_color=bg, hover_color=theme.BTN_HOVER, text_color=fg,
                              corner_radius=theme.RADIUS, command=lambda l=label, i=insert, o=offset: self._press(l, i, o)
                              ).grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

    def _refresh_display(self):
        """
        Updates the expression label and result box.
        If a Solver is active, it shows the equation skeleton at the top and the prompt at the bottom.
        """
        if self.solver["active"]:
            self.expr_label.configure(text=self.solver.get("skeleton", ""))
            
            if self.solver["type"] == "eqn_menu":
                # Shrink font for the menu so it fits without scrolling
                self.result_box.configure(font=("Consolas", 14, "bold"))
                menu_text = "1. 2-Variable (x, y)\n2. Quadratic (x)\n3. Cubic (x)"
                # Scroll to top when nothing is typed. Scroll to bottom when typing.
                if self.expression == "":
                    self._update_result(f"{menu_text}\n\n> {self.expression}|", scroll="1.0")
                else:
                    self._update_result(f"{menu_text}\n\n> {self.expression}|", scroll="end")
            else:
                # Font for variable prompts (a = 5)
                self.result_box.configure(font=("Consolas", 20, "bold"))
                prompt = self.solver["prompts"][self.solver["step"]]
                self._update_result(f"{prompt} = {self.expression}|", scroll="end")
            return

        # Normal calculator display logic
        self.result_box.configure(font=theme.FONT_RESULT)
        text = self.expression or " "
        if 0 <= self.cursor_pos <= len(self.expression):
            text = text[:self.cursor_pos] + "|" + text[self.cursor_pos:]
        self.expr_label.configure(text=text)

    def _toggle_frac(self):
        # 1. Flip the mode
        self.is_fraction = not self.is_fraction
        self.frac_label.configure(text_color=theme.BTN_EQ if self.is_fraction else theme.TEXT_MUTED)
        
        # 2. Grab what is currently on the screen
        current_val = self.result_box.get("1.0", "end").strip()
        
        # 3. If there's a valid number, reformat it
        if current_val and current_val != "0" and "Error" not in current_val:
            try:
                # If the screen shows a fraction (like "1/2"), we use our math engine to calculate it to 0.5 first.
                if "/" in current_val:
                    val = calc.evaluate(current_val)
                else:
                    # Otherwise, just convert the string to a float
                    val = float(current_val)
                    
                # 4. Display the newly formatted result
                self._update_result(calc.format_result(val, self.is_fraction), scroll="end")
            except Exception:
                # If it's a complex equation result (like "x = 2"), ignore the toggle
                pass

    # ==========================================
    # INPUT HANDLING & EVALUATION
    # ==========================================
    def _show_log_menu(self):
        menu = tk.Menu(self, tearoff=0, bg=theme.BG2, fg=theme.TEXT, font=MENU_FONT, activebackground=theme.BTN_OP, activeforeground=theme.TEXT)
        menu.add_command(label="log₁₀", command=lambda: self._press("log10", "log10()", 1))
        menu.add_command(label="logₙ (custom)", command=lambda: self._press("log", "log(, )", 2))
        try:
            x, y = self.winfo_pointerx(), self.winfo_pointery()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _insert_text(self, insert):
        # Simply insert the text at the cursor position. 
        # No smart chaining anymore.
        self.expression = self.expression[:self.cursor_pos] + insert + self.expression[self.cursor_pos:]
        self.cursor_pos += len(insert)
        self._refresh_display()

    def _press(self, label, insert, offset=0):
        if "Error" in self.result_box.get("1.0", "end"):
            self._update_result("", scroll="end")

        if label == "AC":
            self.solver["active"] = False
            self.result_box.configure(font=theme.FONT_RESULT)
            self.expr_label.configure(text=" ")
            self.expression, self.last_result, self.cursor_pos = "", None, 0
            self.history_box.delete("1.0", "end")
            self.history = []
            self._save_history()
            self._update_result("0", scroll="end")
            self._refresh_display(); return
        if label == "C":
            self.expression, self.cursor_pos = "", 0
            self._update_result("0", scroll="end")
            self._refresh_display(); return
        if label == "⌫":
            # Clamp the cursor to the string length to prevent out-of-bounds slicing
            if self.cursor_pos > len(self.expression):
                self.cursor_pos = len(self.expression)
                
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
            self.angle_mode = "DEG"
            self._refresh_display(); self._render_keys(); return
        if label == "RAD":
            self.angle_mode = "RAD"
            self._refresh_display(); self._render_keys(); return
            
        if label == "+/-":
            self.expression = f"-({self.expression})"
            self.cursor_pos = len(self.expression)
            self._refresh_display(); return
        
        if label == "log":
            self._show_log_menu(); return
            
        if label == "EQN":
            # Starts the inline equation menu (1. 2-Variable, 2. Quadratic, 3. Cubic)
            self._start_sequence("eqn_menu", ["choice"], skeleton="Select Equation Type")
            return
            
        if label == "nCr":
            self._start_sequence("ncr", ["n", "r"], skeleton="nCr Combinations")
            return
        if label == "nPr":
            self._start_sequence("npr", ["n", "r"], skeleton="nPr Permutations")
            return
        if label == "=":
            self._calculate(); return

        if insert is not None:
            self._insert_text(insert)
            if offset > 0:
                self.cursor_pos -= offset
                self._refresh_display()

    def _calculate(self):
        if self.solver["active"]:
            self._capture_sequence_input()
            return

        expr = self.expression.strip()
        if not expr: return
        
        # Try variable assignment first (e.g., "a = 5")
        try:
            assigned = calc.try_assignment(expr, self.variables, self.angle_mode)
            if assigned is not None:
                self._update_result(calc.format_result(assigned, self.is_fraction), scroll="end")
                self._record(expr, assigned)
                self.expression, self.cursor_pos = "", 0
                self._refresh_display()
                return
        except Exception:
            pass

        # Standard math evaluation
        try:
            value = calc.evaluate(expr, self.variables, self.angle_mode)
        except Exception as e:
            self._update_result(f"Error: {e}", scroll="end")
            return
            
        # Store Answer. We don't use smart chaining on operators anymore, 
        # but we keep this so the user can literally type "Ans" on the keyboard to fetch the last result.
        self.variables["Ans"] = value
        self.last_result = value
        self._update_result(calc.format_result(value, self.is_fraction), scroll="end")
        self._record(expr, value)
        self.expression, self.cursor_pos = "", 0
        self._refresh_display()

    def _record(self, expr, value):
        """Saves a calculation to history and updates the visual History box."""
        self.history.append((expr, value, time.time()))
        self._save_history()
        
        if isinstance(value, str):
            self.history_box.insert("end", f"{expr} -> {value}\n")
        else:
            self.history_box.insert("end", f"{expr} = {value:.6g}\n")
        self.history_box.see("end")

    # ==========================================
    # KEYBOARD BINDINGS
    # ==========================================
    def _is_typing(self):
        """Checks if the user is currently typing inside a text entry box."""
        focused = self.focus_get()
        return isinstance(focused, (ctk.CTkEntry, tk.Entry))

    def _bind_keys(self):
        # bind_all ensures the root window catches the event EVEN IF a widget has focus.
        self.bind_all("<Return>", self._on_return)
        self.bind_all("<BackSpace>", self._on_backspace)
        self.bind_all("<Escape>", self._on_escape)
        self.bind_all("<Left>", self._on_left)
        self.bind_all("<Right>", self._on_right)
        self.bind_all("<Key>", self._on_key)
        
        # Bind directly to the internal Tkinter text widgets to override their default behavior
        self.result_box._textbox.bind("<BackSpace>", self._on_backspace)
        self.result_box._textbox.bind("<Return>", self._on_return)
        self.history_box._textbox.bind("<BackSpace>", self._on_backspace)
        self.history_box._textbox.bind("<Return>", self._on_return)

    def _on_return(self, event):
        if not self._is_typing():
            self._press("=", None)
            return "break" # Stops the event from propagating to text boxes

    def _on_backspace(self, event):
        if not self._is_typing():
            self.focus_set()
            self._press("⌫", None)
            return "break"

    def _on_escape(self, event):
        if not self._is_typing():
            self._press("AC", None)
            return "break"

    def _on_left(self, event):
        if not self._is_typing():
            self._press("<", None)
            return "break"

    def _on_right(self, event):
        if not self._is_typing():
            self._press(">", None)
            return "break"

    def _on_key(self, event):
        if not self._is_typing():
            char = event.char
            if char in "0123456789.+-*/()%=!abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_":
                self._insert_text(char)
                return "break"
            elif char == "^":
                self._insert_text("**")
                return "break"

    # ==========================================
    # GRAPH MODE ROUTING
    # ==========================================
    def _open_graph_view(self, x_data=None, y_data=None):
        self.previous_view = self.mode
        self.display_frame.pack_forget()
        self.keypad_frame.pack_forget()
        self.history_frame.pack_forget()
        self.stats_frame.pack_forget()
        
        self.graph_frame.load_statistics(x_data, y_data)
        self.graph_frame.pack(fill="both", expand=True, padx=14, pady=6)

    def _close_graph_view(self):
        self.graph_frame.pack_forget()
        self._set_mode(self.previous_view)