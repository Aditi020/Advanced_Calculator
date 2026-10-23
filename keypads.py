"""
keypads.py
----------
This file stores the layout of the calculator buttons for Scientific and Advanced modes.

Each button is a tuple: (Label, Insert_Text, Style_Color, Cursor_Offset)
- Label: The text shown on the button.
- Insert_Text: The text injected into the calculator display. If None, it triggers a special function.
- Style_Color: Maps to theme.py (num, op, sci, eq, clear).
- Cursor_Offset: (Optional) How many spaces to move the cursor backwards after typing.
                 Used for functions like sin(, cos(, sqrt( so the cursor lands INSIDE the bracket.
"""
# The format is now: (Label, Insert_Text, Style_Color, Cursor_Offset)
# The brackets are fully closed "()", and the offset moves the cursor back inside.

SCIENTIFIC_KEYS = [
    [("sin", "sin()", "sci", 1), ("cos", "cos()", "sci", 1), ("tan", "tan()", "sci", 1), ("log", None, "sci"), ("ln", "ln()", "sci", 1)],
    [("√", "sqrt()", "sci", 1), ("x²", "**2", "sci"), ("xʸ", "**", "sci"), ("π", "pi", "sci"), ("e", "e", "sci")],
    [("1/x", "1/", "sci"), ("n!", "!", "sci"), ("DEG", None, "sci"), ("RAD", None, "sci"), ("%", "%", "op")],
    [("7", "7", "num"), ("8", "8", "num"), ("9", "9", "num"), ("÷", "/", "op"), ("⌫", None, "clear")],
    [("4", "4", "num"), ("5", "5", "num"), ("6", "6", "num"), ("×", "*", "op"), ("C", None, "clear")],
    [("1", "1", "num"), ("2", "2", "num"), ("3", "3", "num"), ("−", "-", "op"), ("AC", None, "clear")],
    [("0", "0", "num"), (".", ".", "num"), ("(", "(", "num"), (")", ")", "num"), ("=", None, "eq")],
]

ADVANCED_KEYS = [
    [("sin⁻¹", "asin()", "sci", 1), ("cos⁻¹", "acos()", "sci", 1), ("tan⁻¹", "atan()", "sci", 1), ("sinh", "sinh()", "sci", 1), ("cosh", "cosh()", "sci", 1)],
    [("tanh", "tanh()", "sci", 1), ("abs", "abs()", "sci", 1), ("floor", "floor()", "sci", 1), ("ceil", "ceil()", "sci", 1), ("EQN", None, "sci")],
    [("DEG", None, "sci"), ("RAD", None, "sci"), ("nCr", None, "sci"), ("nPr", None, "sci"), ("mod", " % ", "sci")],
    [("7", "7", "num"), ("8", "8", "num"), ("9", "9", "num"), ("÷", "/", "op"), ("⌫", None, "clear")],
    [("4", "4", "num"), ("5", "5", "num"), ("6", "6", "num"), ("×", "*", "op"), ("C", None, "clear")],
    [("1", "1", "num"), ("2", "2", "num"), ("3", "3", "num"), ("−", "-", "op"), ("AC", None, "clear")],
    [("0", "0", "num"), (".", ".", "num"), ("(", "(", "num"), (")", ")", "num"), ("=", None, "eq")],
]