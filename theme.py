"""
theme.py
--------
This file acts as the "CSS" for our application. 
Instead of hardcoding colors and fonts in every file, we define them here once. 
If we want to change the app from Vanilla & Apricot to Dark Mode, we only change this file.
"""

# --- Palette (Vanilla & Apricot Theme) ---
# These are Hexadecimal color codes.
BG1        = "#F5EBDD"   # Main background color (Vanilla Cream)
BG2        = "#FFFCF5"   # Secondary background / Display screen (Warm Ivory)
BTN_SCI    = "#F8E9BE"   # Scientific buttons (Butter Yellow)
BTN_OP     = "#E8C5A1"   # Operators & Mode buttons (Soft Caramel)
BTN_CLEAR  = "#DDA078"   # Clear & Backspace buttons (Apricot)
BTN_EQ     = "#B96940"   # Equals & Primary actions (Toasted Orange)
BTN_HOVER  = "#EFE0CC"   # Color when mouse hovers over a button
TEXT       = "#554337"   # Main text color (Espresso Brown)
TEXT_LIGHT = "#FFFCF5"   # Text on dark backgrounds
TEXT_MUTED = "#8A766A"   # Secondary, smaller text

# --- Graph Colors ---
GRAPH_BG, GRAPH_GRID = "#FFFAF0", "#E8DCCB"
CURVE_1, CURVE_2, CURVE_3, CURVE_4 = "#829DB0", "#A58AA0", "#B96940", "#7BA05B"

# --- Fonts ---
# The format is ("Font Name", Size, "Style")
FONT_TITLE    = ("Segoe UI", 20, "bold")
FONT_SUBTITLE = ("Segoe UI", 10)
FONT_DISPLAY  = ("Consolas", 18, "bold")  # Consolas is a monospace font (like code)
FONT_RESULT   = ("Consolas", 28, "bold")
FONT_KEY      = ("Segoe UI", 13)
FONT_HISTORY  = ("Consolas", 11)

# --- Shape / size ---
RADIUS, PAD = 10, 6         # Corner radius for buttons and padding size
WIN_W, WIN_H = 440, 760     # Default window width and height