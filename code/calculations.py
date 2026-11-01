"""
Math engine for the calculator. No GUI here, just logic.
I used AST to parse strings safely because using eval() directly is a huge security risk.
Libraries: ast, math, re, random, statistics, numpy, sympy
"""

import ast, math, re, random, statistics
from fractions import Fraction
import numpy as np

# Try to import sympy for algebra. If it fails, skip equation solving.
try:
    import sympy as sp
    from sympy.parsing.sympy_parser import parse_expr as _sym_parse
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

# Regex for finding factorials and variable assignments
_FACT_RE = re.compile(r"(\d+(?:\.\d+)?)!") 
_ASSIGN_RE  = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+)$") 

# These are the only things allowed in a math expression.
# If someone tries to slip in "__import__('os')", it will get blocked here.
_ALLOWED = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Name, ast.Load, ast.Call,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd,
)

def safe_fact(n):
    """
    The standard math.factorial doesn't have a limit. 
    fact(100000) will freeze the app and crash Python.
    We cap it at 1000 to keep the UI responsive.
    """
    if n > 1000:
        raise ValueError("Factorial too large (max 1000)")
    if n < 0:
        raise ValueError("Factorial of negative number")
    return math.factorial(n)

def safe_pow(base, exp):
    """
    Python crashes if you do 9**9**9 because the number is insanely huge.
    This checks the size before doing the calculation so the app doesn't freeze.
    """
    if abs(exp) > 10000:
        raise ValueError("Exponent too large")
    if abs(base) > 1e100 and abs(exp) > 100:
        raise ValueError("Number too large")
    try:
        return base ** exp
    except OverflowError:
        raise ValueError("Number too large")

class PowTransformer(ast.NodeTransformer):
    """
    Hooks into the AST tree and swaps the default ** operator 
    with our safe_pow function before Python tries to execute it.
    """
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Pow):
            return ast.Call(func=ast.Name(id='safe_pow', ctx=ast.Load()),
                            args=[node.left, node.right], keywords=[])
        return node

def safe_tan(x, mode="DEG"):
    """
    Python's math.tan(90) returns a massive number instead of erroring.
    This works to manually check if the angle is 90 or 270 and throws an error.
    """
    if mode == "DEG":
        if abs((x % 180) - 90) < 1e-9:
            raise ValueError("Undefined") 
        return math.tan(math.radians(x))
    else:
        if abs((x % math.pi) - (math.pi / 2)) < 1e-9:
            raise ValueError("Undefined")
        return math.tan(x)

def _fix_zeros(m):
    # Strips leading zeros (009 -> 9) but keeps the zero in decimals (0.5 -> 0.5)
    num = m.group(0)
    stripped = num.lstrip("0")
    if not stripped:
        return "0"
    if stripped.startswith("."):
        return "0" + stripped
    return stripped
    
def _preprocess(s):
    """
    Swaps the × and ÷ symbols for python symbols and then handles percentages.
    """
    #Resolves 009 to 9
    s = re.sub(r'\b\d+(?:\.\d+)?\b', _fix_zeros, s)
    # Replace visual symbols
    s = s.replace("×", "*").replace("÷", "/").replace("−", "-").replace("^", "**")
    
    # Converts 5! to safe_fact(5)
    while _FACT_RE.search(s):
        s = _FACT_RE.sub(r"safe_fact(\1)", s, count=1)

    # Percentage math: 200 + 10% becomes 200 + (200 * 10 / 100)
    s = re.sub(r'(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)%', r'(\1 + \1 * \2 / 100)', s)
    s = re.sub(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)%', r'(\1 - \1 * \2 / 100)', s)
    s = re.sub(r'(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)%', r'(\1 * \2 / 100)', s)
    s = re.sub(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)%', r'(\1 / (\2 / 100))', s)
    
    return s

def _build_ns(vars, angle):
    """
    Creates the dictionary of functions the evaluator can use.
    Changes trig functions depending on DEG or RAD mode.
    """
    ns = {
        "abs": abs, "fact": safe_fact, "safe_fact": safe_fact, "sqrt": math.sqrt, 
        "log": lambda x, b=10: math.log10(x) if b == 10 else math.log(x, b), 
        "ln": math.log, "log2": math.log2, "log10": math.log10,
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "floor": math.floor, "ceil": math.ceil, "exp": math.exp,
        "comb": math.comb, "perm": math.perm, "rand": random.random,
        "pi": math.pi, "e": math.e, "mod": lambda a, b: a % b,
        "safe_pow": safe_pow 
    }
    
    if angle == "DEG":
        ns.update({
            "sin": lambda x: math.sin(math.radians(x)),
            "cos": lambda x: math.cos(math.radians(x)),
            "tan": lambda x: safe_tan(x, "DEG"),
            "asin": lambda x: math.degrees(math.asin(x)),
            "acos": lambda x: math.degrees(math.acos(x)),
            "atan": lambda x: math.degrees(math.atan(x)),
        })
    else:
        ns.update({"sin": math.sin, "cos": math.cos, 
                   "tan": lambda x: safe_tan(x, "RAD"),
                   "asin": math.asin, "acos": math.acos, "atan": math.atan})
        
    ns.update(vars)
    return ns

def _safe_eval(s, ns):
    """
    Uses AST to parse the string safely. Walks through every node 
    to make sure there is no malicious code.
    """
    try:
        tree = ast.parse(s, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error: {e.msg}")
        
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            raise ValueError(f"Not allowed: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in ns:
            raise ValueError(f"Unknown name: {node.id}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls allowed")
            if node.func.id not in ns:
                raise ValueError(f"Unknown function: {node.func.id}")
                
    # Apply the safe power transformer
    tree = PowTransformer().visit(tree)
    ast.fix_missing_locations(tree)
                
    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, ns)

def evaluate(s, vars=None, angle="DEG"):
    """
    Main function. Takes a string, preprocesses it, checks safety, returns float.
    """
    if not s.strip():
        raise ValueError("Empty expression")
        
    src = _preprocess(s)
    ns  = _build_ns(vars or {}, angle)
    
    try:
        return _safe_eval(src, ns)
    except ZeroDivisionError:
        raise ValueError("Division by zero")
    except OverflowError:
        raise ValueError("Number too large")

def try_assign(s, vars, angle="DEG"):
    """
    Checks if the user typed something like "a = 5". If so, stores it.
    """
    m = _ASSIGN_RE.match(s)
    if not m:
        return None
    name, rhs = m.group(1), m.group(2)
    if name in _build_ns({}, angle):
        raise ValueError(f"Cannot use reserved name: {name}")
    val = evaluate(rhs, vars, angle)
    vars[name] = val
    return val

def fmt_res(val, is_frac):
    """
    Formats the output to fraction or decimal based on the S<->D toggle.
    """
    if is_frac:
        try:
            f = Fraction(val).limit_denominator(10000)
            if f.denominator == 1:
                return str(f.numerator)
            return f"{f.numerator}/{f.denominator}"
        except Exception:
            pass
    try:
        return f"{val:.10g}"
    except OverflowError:
        s = str(val)
        if len(s) > 10:
            return f"{s[0]}.{s[1:10]}e+{len(s)-1}"
        return s

# --- Sympy Equation Solvers ---
def _fmt_sympy(s):
    """
    Handles complex numbers like 3+2i when formatting Sympy outputs.
    """
    if s.is_real:
        return f"{float(s.evalf()):.4f}"
    else:
        re_p, im_p = s.as_real_imag()
        re_s = f"{float(re_p.evalf()):.4f}"
        im_s = f"{float(abs(im_p.evalf())):.4f}"
        sign = "+" if float(im_p.evalf()) >= 0 else "-"
        if float(re_p.evalf()) == 0:
            return f"{im_s}i" if sign == "+" else f"-{im_s}i"
        return f"{re_s} {sign} {im_s}i"

def solve_2var(a, b, c, d, e, f):
    """
    Solves 2 equations at once (ax + by + c = 0).
    Sympy returns a dict for unique solutions, a list for infinite solutions, 
    and an empty list for no solution.
    """
    if not HAS_SYMPY: raise ValueError("SymPy missing")
    x, y = sp.symbols('x y')
    try:
        eq1 = sp.Eq(a*x + b*y + c, 0)
        eq2 = sp.Eq(d*x + e*y + f, 0)
        sol = sp.solve([eq1, eq2], (x, y))
        
        # Check for no solution then Sympy returns an empty list if the equations have no solution.
        if not sol: 
            return "No solution"
            
        # Sympy sometimes returns a list of dictionaries. We grab the first one.
        if isinstance(sol, list):
            if len(sol) == 0:
                return "No solution"
            sol = sol[0]
            
        # If both x and y are solved, we have a unique solution.
        # If x is solved y like , x: -y, then it's dependent.
        if isinstance(sol, dict) and x in sol and y in sol:
            return f"x = {_fmt_sympy(sol[x])}, y = {_fmt_sympy(sol[y])}"
            
        return "Infinitely many solutions"
    except Exception as err:
        return f"Error: {err}"

def solve_poly(coeffs):
    """
    Solves quadratic or cubic equations based on a list of coefficients.
    """
    if not HAS_SYMPY: raise ValueError("SymPy missing")
    x = sp.Symbol('x')
    try:
        if all(c == 0 for c in coeffs):
            return "Infinite solutions"
            
        expr = sum(c * x**i for i, c in enumerate(reversed(coeffs)))
        sols = sp.solve(expr, x)
        
        if not sols: 
            return "No real solutions"
            
        res = [f"x{i+1} = {_fmt_sympy(s)}" for i, s in enumerate(sols)]
        return " | ".join(res)
    except Exception as err:
        return f"Error: {err}"

# --- Statistics ---
def get_desc_stats(data):
    """
    To Calculate mean, median, variance, std dev, MAD, and quartiles.
    """
    if not data: return {}
    n = len(data)
    mean = statistics.mean(data)
    
    # Mean Absolute Deviation (MAD): used to measure spread, how far values are from the mean.
    mad = sum(abs(x - mean) for x in data) / n
    
    res = {
        "n (Count)": n, "Sum": sum(data), "Mean": mean,
        "MAD": mad, "Min": min(data), "Max": max(data),
    }
    if n > 1:
        res["Median"] = statistics.median(data)
        res["Var (σ²)"] = statistics.pvariance(data)
        res["Var (s²)"] = statistics.variance(data)
        res["Std (σ)"] = statistics.pstdev(data)
        res["Std (s)"] = statistics.stdev(data)
        try:
            q = statistics.quantiles(data, n=4)
            res["Q1"] = q[0]; res["Q3"] = q[2]; res["IQR"] = q[2] - q[0]
        except Exception: pass
        try:
            modes = statistics.multimode(data)
            res["Mode"] = ", ".join(str(m) for m in modes)
        except Exception: pass
    return res

def get_reg_stats(x, y):
    """
    Calculates correlation, slope, intercept, and covariance.
    """
    if len(x) != len(y) or len(x) < 2: return {}
    n = len(x)
    mx, my = statistics.mean(x), statistics.mean(y)
    
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / (n - 1)
    try: r = statistics.correlation(x, y)
    except Exception: r = 0.0
        
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    den = sum((x[i] - mx)**2 for i in range(n))
    m = (num / den) if den != 0 else 0
    b = my - m * mx
    
    return {"Corr (r)": r, "Slope (m)": m, "Y-Int (b)": b, "Covariance": cov}

def get_poisson(k, lam):
    """
    Uses log-space computation (lgamma) to prevent overflow errors 
    when calculating massive factorials for the Poisson PMF.
    """
    if lam <= 0 or k < 0:
        return 0.0
    return math.exp(k * math.log(lam) - lam - math.lgamma(k + 1))
