You are absolutely right. I overshot. A README should be **documentation**, not a diary entry. You want the professional tone of your original README, just with the "AI polish" removed so it reads like a real developer wrote it.

Here is the updated `README.md`. I kept your structure and vocabulary, removed the marketing fluff, and made the setup instructions actually functional.

### `README.md`

```markdown
# Calc — Scientific & Analytical Calculator

A desktop scientific calculator built with Python. Originally assigned as a basic calculator project, this application was extended into an analytical tool designed for students and data analysts.

It features a custom dark-themed UI, algebraic equation solving, statistical data analysis, and an interactive graphing module.

## Features

### 1. Scientific & Advanced Modes
- **Basic Math:** Safe evaluation of expressions, parentheses, powers, roots, and factorials.
- **Trigonometry & Logs:** Sine, cosine, tangent, hyperbolic functions, and logarithms with custom base support. Supports both DEG and RAD modes.
- **Variable Memory:** Type `a = 5` and press `=` to store variables, then use `a * 2` in your next calculation.
- **Equation Solver:** An inline step-by-step menu. Press EQN, choose 1 (2-variable), 2 (quadratic), or 3 (cubic), and enter coefficients one by one directly on the main screen.
- **Combinatorics:** Calculate Combinations (nCr) and Permutations (nPr).
- **Fraction Mode:** Toggle the "S⇔D" button to convert decimals into exact fractions.

### 2. Statistics Workspace
- **Dataset Input:** Enter paired X and Y data one by one or comma-separated.
- **Live Summary:** A dynamically updating dashboard shows Count, Mean, Median, and Standard Deviation instantly.
- **Advanced Metrics:** Dedicated buttons for Quartiles (Q1, Q3), IQR, MAD, Variance, and Regression stats.
- **Linear Regression:** Automatically calculates Correlation (r), Slope (m), and Y-Intercept (b) when X and Y lengths match.

### 3. Interactive Graphing (Matplotlib)
- **Embedded Canvas:** The graph lives inside the app, not in a separate window.
- **Pan & Zoom:** Click and drag to pan; use the mouse wheel to zoom in and out.
- **Graph Types:**
  - **Linear Regression:** Scatter plot with a line of best fit.
  - **Histogram:** Distribution of the X dataset.
  - **Normal Curve:** Bell curve fit for the X dataset.
  - **Poisson Distribution:** Probability mass function for count data.
- **Summary Panel:** A panel below the graph shows the equation, R² value, and statistical parameters.

## Tech Stack & Architecture

The project uses a modular architecture to separate the UI from the math engine:

- **`customtkinter`**: Modern, rounded UI widgets with a custom dark color palette.
- **`sympy`**: Symbolic mathematics for exact equation solving.
- **`matplotlib` & `numpy`**: For plotting interactive graphs and handling arrays.
- **`ast` & `math`**: Built-in Python libraries for safe parsing and basic math.

### File Structure

```text
Calculator/
├── main.py                # Entry point to run the app
├── theme.py               # Colors, fonts, and styling constants
├── calculations.py        # The math engine (no GUI code)
├── interface.py           # Main window, keyboard bindings, and controller
├── keypads.py             # Layouts for Scientific and Advanced buttons
├── statistics_mode.py     # UI and logic for the Statistics workspace
├── graph.py               # Matplotlib embedding and interactive controls
├── requirements.txt       # Python dependencies
└── README.md              # You are here
```

## How to Run

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Aditi020/Advanced_Calculator.git
   cd Advanced_Calculator
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Technical Notes

- **Security:** The calculator does not use `eval()` directly. It uses Python's `ast` library to whitelist only math operations, preventing code injection.
- **Undefined Results:** `math.tan(90)` in Python returns a huge number instead of erroring. The `safe_tan` wrapper intercepts this and raises "Undefined".
- **Large Powers:** An AST transformer (`PowTransformer`) intercepts the `**` operator and limits the exponent size to prevent the app from freezing on inputs like `9**9**9`.
- **History:** Calculations are saved to a local `history.json` file. Entries automatically expire after 1 hour. This file is gitignored.

## Author

Aditi Kumar
NextHikes IT Solutions — Project 2
```