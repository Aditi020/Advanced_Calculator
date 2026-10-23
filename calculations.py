"""
calculations.py
---------------
"""
import ast, math, re, random, statistics
from fractions import Fraction
import numpy as np

try:
    import sympy as sp
    from sympy.parsing.sympy_parser import parse_expr as _sym_parse
    HAS_SYMPY = True
except ImportError:
    HAS_SYMPY = False

_FACT_RE   = re.compile(r"(\d+(?:\.\d+)?)!")
_ASSIGN_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+)$")

_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Name, ast.Load, ast.Call,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd,
)

def safe_pow(base, exp):
    """
    NEW: Prevents the app from freezing when calculating massive powers.
    Example: 9**9**9 crashes Python because the exponent becomes 387,420,489.
    This function checks the size of the exponent before calculating.
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
    NEW: Finds the '**' operator in the math expression and replaces it 
    with our safe_pow() function.
    """
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Pow):
            return ast.Call(func=ast.Name(id='safe_pow', ctx=ast.Load()),
                            args=[node.left, node.right], keywords=[])
        return node

def safe_tan(x, mode="DEG"):
    if mode == "DEG":
        if abs((x % 180) - 90) < 1e-9:
            raise ValueError("Undefined") # <-- Changed to "Undefined"
        return math.tan(math.radians(x))
    else:
        if abs((x % math.pi) - (math.pi / 2)) < 1e-9:
            raise ValueError("Undefined") # <-- Changed to "Undefined"
        return math.tan(x)

def _preprocess(expr: str) -> str:
    expr = expr.replace("×", "*").replace("÷", "/")
    expr = expr.replace("−", "-").replace("^", "**")
    
    while _FACT_RE.search(expr):
        expr = _FACT_RE.sub(r"fact(\1)", expr, count=1)

    # Percentage logic
    expr = re.sub(r'(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)%', r'(\1 + \1 * \2 / 100)', expr)
    expr = re.sub(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)%', r'(\1 - \1 * \2 / 100)', expr)
    expr = re.sub(r'(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)%', r'(\1 * \2 / 100)', expr)
    expr = re.sub(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)%', r'(\1 / (\2 / 100))', expr)
    
    return expr

def _build_namespace(variables: dict, angle_mode: str) -> dict:
    ns = {
        "abs": abs, "fact": math.factorial,
        "sqrt": math.sqrt, 
        "log": lambda x, b=10: math.log10(x) if b == 10 else math.log(x, b), 
        "ln": math.log, "log2": math.log2, "log10": math.log10,
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "floor": math.floor, "ceil": math.ceil, "exp": math.exp,
        "comb": math.comb, "perm": math.perm, "rand": random.random,
        "pi": math.pi, "e": math.e, "mod": lambda a, b: a % b,
        "safe_pow": safe_pow # Add our safe power function
    }
    
    if angle_mode == "DEG":
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
        
    ns.update(variables)
    return ns

def _safe_eval(expr: str, namespace: dict) -> float:
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
                
    # Apply the safe power transformer
    tree = PowTransformer().visit(tree)
    ast.fix_missing_locations(tree)
                
    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, namespace)

def evaluate(expr: str, variables: dict | None = None, angle_mode: str = "DEG") -> float:
    if not expr.strip():
        raise ValueError("Empty expression")
        
    src = _preprocess(expr)
    ns  = _build_namespace(variables or {}, angle_mode)
    
    try:
        result = _safe_eval(src, ns)
        return result
    except ZeroDivisionError:
        raise ValueError("Division by zero")
    except OverflowError:
        raise ValueError("Number too large")

def try_assignment(expr: str, variables: dict, angle_mode: str = "DEG"):
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
    if is_fraction_mode:
        try:
            frac = Fraction(value).limit_denominator(10000)
            if frac.denominator == 1:
                return str(frac.numerator)
            return f"{frac.numerator}/{frac.denominator}"
        except Exception:
            pass
    return f"{value:.10g}"

# --- Equation Solvers ---
def solve_equation(equation_str: str, variable: str = "x"):
    if not HAS_SYMPY: raise ValueError("SymPy missing")
    if "=" not in equation_str: raise ValueError("Equation must contain '='")
    lhs, rhs = equation_str.split("=", 1)
    sym = sp.Symbol(variable)
    try:
        eq = sp.Eq(_sym_parse(lhs, local_dict={variable: sym}),
                   _sym_parse(rhs, local_dict={variable: sym}))
        solutions = sp.solve(eq, sym)
    except Exception as e:
        raise ValueError(f"Cannot solve: {e}")
    if not solutions:
        raise ValueError("No solutions found")
    return solutions

def _format_sympy_val(s):
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
    if not HAS_SYMPY: raise ValueError("SymPy missing")
    x = sp.Symbol('x')
    try:
        expr = sum(c * x**i for i, c in enumerate(reversed(coeffs)))
        sols = sp.solve(expr, x)
        if not sols: return "No real solutions"
        res = [f"x{i+1} = {_format_sympy_val(s)}" for i, s in enumerate(sols)]
        return " | ".join(res)
    except Exception as err:
        return f"Error: {err}"

# --- Statistics ---
def get_descriptive_stats(data):
    if not data: return {}
    n = len(data)
    res = {
        "n (Count)": n, "Sum": sum(data), "Mean": statistics.mean(data),
        "Min": min(data), "Max": max(data),
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

def get_regression_stats(x, y):
    if len(x) != len(y) or len(x) < 2: return {}
    n = len(x)
    mean_x, mean_y = statistics.mean(x), statistics.mean(y)
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / (n - 1)
    try: r = statistics.correlation(x, y)
    except Exception: r = 0.0
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den = sum((x[i] - mean_x)**2 for i in range(n))
    m = (num / den) if den != 0 else 0
    b = mean_y - m * mean_x
    return {"Corr (r)": r, "Slope (m)": m, "Y-Int (b)": b, "Covariance": cov}

def get_poisson_pmf(k, lam):
    return (lam**k * np.exp(-lam)) / math.factorial(k)