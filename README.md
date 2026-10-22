# Calc — Scientific & Analytical Calculator

A modern, desktop-based scientific calculator built with Python. Originally assigned as a basic calculator project, this application has been extended into a comprehensive analytical tool designed for students, data analysts, and data scientists. 

It features a custom, warm UI ("Vanilla & Apricot" theme), advanced algebraic equation solving, statistical data analysis, and an interactive graphing module.

## ✨ Features

### 1. Scientific & Advanced Modes
- **Basic Math:** Safe evaluation of complex expressions, parentheses, powers, roots, and factorials.
- **Trigonometry & Logs:** Sine, cosine, tangent, hyperbolic functions, and logarithms with custom base support. Supports both DEG and RAD modes.
- **Variable Memory:** Type `a = 5` and press `=` to store variables, then use `a * 2` in your next calculation.
- **Equation Solver:** Dedicated popup window to solve 2-variable linear systems, quadratics, and cubics using SymPy.
- **Combinatorics:** Calculate Combinations (nCr) and Permutations (nPr).
- **Fraction Mode:** Toggle the "S⇔D" button to convert decimals into exact fractions.

### 2. Statistics Workspace
- **Dataset Input:** Easily enter paired X and Y data one by one.
- **Live Summary:** A dynamically updating dashboard shows the core metrics (Count, Mean, Median, Standard Deviation) instantly.
- **Advanced Metrics:** Dedicated buttons to calculate Quartiles (Q1, Q3), IQR, Variance, and Regression stats.
- **Linear Regression:** Automatically calculates Correlation (r), Slope (m), and Y-Intercept (b).

### 3. Interactive Graphing (Matplotlib)
- **Embedded Canvas:** The graph is not a separate window; it lives inside the app.
- **Pan & Zoom:** Click and drag to move around the graph, and use your mouse wheel to zoom in and out.
- **Graph Types:**
  - **Linear Regression:** Scatter plot with the line of best fit.
  - **Histogram:** Distribution of the X dataset.
  - **Normal Curve:** Bell curve fit for the X dataset.
  - **Poisson Distribution:** Probability mass function for count data.
- **Summary Panel:** A scrollable panel below the graph shows the exact equation, R² value, and statistical parameters for the active graph.

## 🛠️ Tech Stack & Architecture

This project uses a modular architecture to separate the UI from the math engine:

- **`customtkinter`**: Modern, rounded UI widgets with a custom color palette.
- **`sympy`**: Symbolic mathematics for exact equation solving.
- **`matplotlib` & `numpy`**: For plotting interactive graphs and handling arrays.
- **`ast` & `math`**: Built-in Python libraries for safe parsing and basic math.

### File Structure
```text
Calculator/
├── main.py                # Entry point to run the app
├── theme.py               # Colors, fonts, and styling constants
├── calculations.py        # The pure math engine (no GUI code)
├── interface.py           # Main window, keyboard bindings, and controller
├── keypads.py             # Layouts for Scientific and Advanced buttons
├── statistics_mode.py     # UI and logic for the Statistics workspace
├── graph.py               # Matplotlib embedding and interactive controls
├── requirements.txt       # Python dependencies
└── README.md              # You are here!