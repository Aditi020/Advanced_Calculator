"""
keypads.py
----------
This file stores the layout of the calculator buttons for Scientific and Advanced modes.
We use a list of lists (a grid). 

Each button is a tuple: (Label, What_it_inserts, Style_Color)
- Label: Text shown on the screen.
- Insert: The text injected into the calculator display. If None, it triggers a special function.
- Style: Maps to theme.py (num=BG2, op=BTN_OP, sci=BTN_SCI, eq=BTN_EQ, clear=BTN_CLEAR)
"""

SCIENTIFIC_KEYS = [
    [("sin","sin(","sci"), ("cos","cos(","sci"), ("tan","tan(","sci"), ("log",None,"sci"), ("ln","ln(","sci")],
    [("√","sqrt(","sci"),  ("x²","**2","sci"),  ("xʸ","**","sci"),   ("π","pi","sci"),   ("e","e","sci")],
    [("(","(","num"),      (")",")","num"),     ("1/x","1/","sci"),  ("n!","!","sci"),   ("%","%","op")],
    [("7","7","num"),      ("8","8","num"),     ("9","9","num"),     ("÷","/","op"),     ("⌫",None,"clear")],
    [("4","4","num"),      ("5","5","num"),     ("6","6","num"),     ("×","*","op"),     ("C",None,"clear")],
    [("1","1","num"),      ("2","2","num"),     ("3","3","num"),     ("−","-","op"),     ("AC",None,"clear")],
    [("0","0","num"),      (".",".","num"),     ("<",None,"op"),     (">",None,"op"),    ("=",None,"eq")],
]

ADVANCED_KEYS = [
    [("sin⁻¹","asin(","sci"), ("cos⁻¹","acos(","sci"), ("tan⁻¹","atan(","sci"), ("sinh","sinh(","sci"), ("cosh","cosh(","sci")],
    [("tanh","tanh(","sci"),  ("abs","abs(","sci"),   ("floor","floor(","sci"),("ceil","ceil(","sci"),("EQN",None,"sci")],
    [("(","(","num"),         (")",")","num"),        ("nCr",None,"sci"),      ("nPr",None,"sci"),   ("log",None,"sci")],
    [("7","7","num"),         ("8","8","num"),        ("9","9","num"),         ("÷","/","op"),       ("⌫",None,"clear")],
    [("4","4","num"),         ("5","5","num"),        ("6","6","num"),         ("×","*","op"),       ("C",None,"clear")],
    [("1","1","num"),         ("2","2","num"),        ("3","3","num"),         ("−","-","op"),       ("AC",None,"clear")],
    [("0","0","num"),         (".",".","num"),        ("<",None,"op"),         (">",None,"op"),      ("=",None,"eq")],
]