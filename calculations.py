"""
calculations.py
---------------
This is the mathematical "Engine" of the calculator. 
It contains NO GUI code. It can be tested independently of the app.

Libraries used:
- ast: Safely parses mathematical strings into Python syntax without executing malicious code.
- math: Provides mathematical functions (sqrt, log, factorial).
- sympy (sp): A symbolic math library used for solving algebra equations.
- statistics: Standard Python library for calculating mean, median, variance, etc.
- numpy (np): Used for polynomial fitting and complex array operations.
- fractions (Fraction): Used to convert decimals into neat fractions (e.g., 0.5 to 1/2).
"""
import ast, math, re, random, statistics
from fractions import Fraction
import numpy as np

# We try to import SymPy. If the user hasn't installed it, we set a flag so the app doesn't crash.
try:
    import sympy as sp
    from sympy.parsing.sympy_parser import parse_expr as _sym_parse
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

# Regex (Regular Expression) patterns used to identify specific math patterns in text.
_FACT_RE   = re.compile(r"(\d+(?:\.\d+)?)!") # Finds factorials like "5!"
_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+)$") # Finds variable assignments like "a = 5"

# A strict allow-list of Python AST (Abstract Syntax Tree) nodes. 
# This prevents users from running malicious code like "__import__('os')" inside the calculator.
_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Name, ast.Load, ast.Call,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd,
)

def _preprocess(expr: str) -> str:
    """
    Converts calculator visual symbols into valid Python math symbols.
    Example: "5 × 3" becomes "5 * 3", and "2^4" becomes "2**4".
    Also converts factorials: "5!" becomes "fact(5)".
    """
    expr = expr.replace("×", "*").replace("÷", "/")
    expr = expr.replace("−", "-").replace("^", "**")
    
    # Converts "5!" into "fact(5)" so Python can process it.
    while _FACT_RE.search(expr):
        expr = _FACT_RE.sub(r"fact(\1)", expr, count=1)

    # --- NEW: Percentage Logic ---
    # This regex finds any number directly followed by a '%' (e.g., "10%")
    # and replaces it with "(10/100)".
    
    expr = re.sub(r'(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)%',r'(\1 + \1 * \2 / 100)',expr)      
    
    
    return expr

def _build_namespace(variables: dict, angle_mode: str) -> dict:
    """
    Creates a dictionary of allowed math functions the calculator can use.
    It dynamically switches sin/cos/tan formulas based on Degree or Radian mode.
    """
    ns = {
        "abs": abs, "fact": math.factorial,
        "sqrt": math.sqrt, 
        # Custom log function: math.log10 by default, or math.log(x, base)
        "log": lambda x, b=10: math.log10(x) if b == 10 else math.log(x, b), 
        "ln": math.log, "log2": math.log2,
        "log10": math.log10,
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "floor": math.floor, "ceil": math.ceil, "exp": math.exp,
        "comb": math.comb, "perm": math.perm, "rand": random.random,
        "pi": math.pi, "e": math.e, "mod": lambda a, b: a % b
    }
    
    # Adjust sin/cos/tan based on Degree or Radian mode
    if angle_mode == "DEG":
        ns.update({
            "sin": lambda x: math.sin(math.radians(x)),
            "cos": lambda x: math.cos(math.radians(x)),
            "tan": lambda x: math.tan(math.radians(x)),
            "asin": lambda x: math.degrees(math.asin(x)),
            "acos": lambda x: math.degrees(math.acos(x)),
            "atan": lambda x: math.degrees(math.atan(x)),
        })
    else:
        ns.update({"sin": math.sin, "cos": math.cos, "tan": math.tan,
                   "asin": math.asin, "acos": math.acos, "atan": math.atan})
        
    # Add user-defined variables (a=5, b=10) to the allowed namespace
    ns.update(variables)
    return ns

def _safe_eval(expr: str, namespace: dict) -> float:
    """
    Uses Python's 'ast' library to safely evaluate math strings.
    It walks through every part of the equation to ensure no forbidden commands are used.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error: {e.msg}")
        
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(f"Not allowed: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in namespace:
            raise ValueError(f"Unknown name: {node.id}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls allowed")
            if node.func.id not in namespace:
                raise ValueError(f"Unknown function: {node.func.id}")
                
    # Evaluate the string safely
    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, namespace)

def evaluate(expr: str, variables: dict | None = None, angle_mode: str = "DEG") -> float:
    """
    The main math function. Takes a string, preprocesses it, checks safety, and returns the final float value.
    """
    if not expr.strip():
        raise ValueError("Empty expression")
        
    src = _preprocess(expr)
    ns  = _build_namespace(variables or {}, angle_mode)
    
    try:
        result = _safe_eval(src, ns)
        # Float precision cleanup: math.log(1000, 10) might return 2.999999999999.
        # This ensures it returns exactly 3.0.
        if isinstance(result, float) and abs(result - round(result)) < 1e-10:
            return float(round(result))
        return result
    except ZeroDivisionError:
        raise ValueError("Division by zero")

def try_assignment(expr: str, variables: dict, angle_mode: str = "DEG"):
    """
    Checks if the user typed a variable assignment (like "x = 10").
    If so, evaluates the right side and stores it in the variables dictionary.
    """
    m = _ASSIGN_RE.match(expr)
    if not m:
        return None
        
    name, rhs = m.group(1), m.group(2)
    if name in _build_namespace({}, angle_mode):
        raise ValueError(f"Cannot use reserved name: {name}")
        
    value = evaluate(rhs, variables, angle_mode)
    variables[name] = value
    return value

def format_result(value: float, is_fraction_mode: bool) -> str:
    """
    Formats the output. 
    FIXED (Mentor Feedback 3): 
    If is_fraction_mode is TRUE -> Show Fraction (e.g., 6/5)
    If is_fraction_mode is FALSE -> Show Decimal (e.g., 1.2)
    """
    if is_fraction_mode:
        try:
            # 'Fraction' from the fractions library converts 1.2 to 6/5
            frac = Fraction(value).limit_denominator(10000)
            if frac.denominator == 1:
                return str(frac.numerator)
            return f"{frac.numerator}/{frac.denominator}"
        except Exception:
            pass
            
    # Default: Return Decimal formatted to 10 significant digits
    return f"{value:.10g}"


# --- Equation Solvers (Powered by SymPy) ---
def solve_equation(equation_str: str, variable: str = "x"):
    """
    Uses SymPy to solve a single string equation (like "x**2 - 4 = 0") and returns the roots.
    """
    if not HAS_SYMPY: raise ValueError("SymPy missing")
    if "=" not in equation_str: raise ValueError("Equation must contain '='")
    
    lhs, rhs = equation_str.split("=", 1)
    sym = sp.Symbol(variable)
    
    try:
        # sympy.Eq creates an equation object
        eq = sp.Eq(_sym_parse(lhs, local_dict={variable: sym}),
                   _sym_parse(rhs, local_dict={variable: sym}))
        # sp.solve finds the roots
        solutions = sp.solve(eq, sym)
    except Exception as e:
        raise ValueError(f"Cannot solve: {e}")
        
    if not solutions:
        raise ValueError("No solutions found")
    return solutions

def _format_sympy_val(s):
    """
    Formats SymPy math objects into neat 4-decimal strings and handles imaginary numbers (like 3 + 2i).
    """
    if s.is_real:
        return f"{float(s.evalf()):.4f}"
    else:
        re_part, im_part = s.as_real_imag()
        re_str = f"{float(re_part.evalf()):.4f}"
        im_str = f"{float(abs(im_part.evalf())):.4f}"
        sign = "+" if float(im_part.evalf()) >= 0 else "-"
        if float(re_part.evalf()) == 0:
            return f"{im_str}i" if sign == "+" else f"-{im_str}i"
        return f"{re_str} {sign} {im_str}i"

def solve_linear_system(a, b, c, d, e, f):
    """
    Uses SymPy to solve 2 equations at once (ax + by + c = 0).
    """
    if not HAS_SYMPY: raise ValueError("SymPy missing")
    x, y = sp.symbols('x y')
    try:
        eq1 = sp.Eq(a*x + b*y + c, 0)
        eq2 = sp.Eq(d*x + e*y + f, 0)
        sol = sp.solve([eq1, eq2], (x, y))
        if not sol: return "No unique solution"
        return f"x = {_format_sympy_val(sol[x])}, y = {_format_sympy_val(sol[y])}"
    except Exception as err:
        return f"Error: {err}"

def solve_polynomial(coeffs):
    """
    Uses SymPy to solve quadratic or cubic equations based on a list of coefficients.
    """
    if not HAS_SYMPY: raise ValueError("SymPy missing")
    x = sp.Symbol('x')
    try:
        # zip coefficients to powers of x
        expr = sum(c * x**i for i, c in enumerate(reversed(coeffs)))
        sols = sp.solve(expr, x)
        if not sols: return "No real solutions"
        res = [f"x{i+1} = {_format_sympy_val(s)}" for i, s in enumerate(sols)]
        return " | ".join(res)
    except Exception as err:
        return f"Error: {err}"


# --- Statistics (Powered by Python's `statistics` and `numpy` libraries) ---
def get_descriptive_stats(data):
    """
    Calculates mean, median, variance, std dev, and quartiles for a dataset.
    """
    if not data: return {}
    n = len(data)
    res = {
        "n (Count)": n,
        "Sum": sum(data),
        "Mean": statistics.mean(data), # statistics.mean calculates average
        "Min": min(data),
        "Max": max(data),
    }
    if n > 1:
        res["Median"] = statistics.median(data) # statistics.median finds middle value
        res["Var (σ²)"] = statistics.pvariance(data) # Population variance
        res["Var (s²)"] = statistics.variance(data)  # Sample variance
        res["Std (σ)"] = statistics.pstdev(data)     # Population std dev
        res["Std (s)"] = statistics.stdev(data)      # Sample std dev
        try:
            q = statistics.quantiles(data, n=4) # Splits data into 4 quarters
            res["Q1"] = q[0]
            res["Q3"] = q[2]
            res["IQR"] = q[2] - q[0] # Interquartile Range
        except Exception: pass
        try:
            modes = statistics.multimode(data) # Handles datasets with multiple modes
            res["Mode"] = ", ".join(str(m) for m in modes)
        except Exception: pass
    return res

def get_regression_stats(x, y):
    """
    Calculates correlation (r), slope (m), intercept (b), and covariance between two datasets.
    """
    if len(x) != len(y) or len(x) < 2: return {}
    n = len(x)
    mean_x, mean_y = statistics.mean(x), statistics.mean(y)
    
    # Covariance formula
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / (n - 1)
    
    try: 
        r = statistics.correlation(x, y) # Pearson correlation coefficient
    except Exception: 
        r = 0.0
        
    # Linear Regression formula: y = mx + b
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den = sum((x[i] - mean_x)**2 for i in range(n))
    m = (num / den) if den != 0 else 0
    b = mean_y - m * mean_x
    
    return {
        "Corr (r)": r,
        "Slope (m)": m,
        "Y-Int (b)": b,
        "Covariance": cov
    }

# --- Advanced Graph Math ---
def get_poisson_pmf(k, lam):
    """
    Poisson Probability Mass Function for a specific k and lambda.
    """
    return (lam**k * np.exp(-lam)) / math.factorial(k)