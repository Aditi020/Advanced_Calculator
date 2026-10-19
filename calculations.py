import ast, math, re, random
from fractions import Fraction

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

def _preprocess(expr: str) -> str:
    expr = expr.replace("×", "*").replace("÷", "/")
    expr = expr.replace("−", "-").replace("^", "**")
    while _FACT_RE.search(expr):
        expr = _FACT_RE.sub(r"fact(\1)", expr, count=1)
    return expr

def _build_namespace(variables: dict, angle_mode: str) -> dict:
    ns = {
        "abs": abs, "fact": math.factorial,
        "sqrt": math.sqrt, 
        "log": lambda x, b=10: math.log10(x) if b == 10 else math.log(x, b), 
        "ln": math.log, "log2": math.log2,
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "floor": math.floor, "ceil": math.ceil, "exp": math.exp,
        "comb": math.comb, "perm": math.perm, "rand": random.random,
        "pi": math.pi, "e": math.e, "mod": lambda a, b: a % b
    }
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
    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, namespace)

def evaluate(expr: str, variables: dict | None = None, angle_mode: str = "DEG") -> float:
    if not expr.strip():
        raise ValueError("Empty expression")
    src = _preprocess(expr)
    ns  = _build_namespace(variables or {}, angle_mode)
    try:
        result = _safe_eval(src, ns)
        if isinstance(result, float) and abs(result - round(result)) < 1e-10:
            return float(round(result))
        return result
    except ZeroDivisionError:
        raise ValueError("Division by zero")

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

def format_result(value: float, is_fraction: bool) -> str:
    if is_fraction:
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
    """Helper to format SymPy numbers to 4 decimals and clean up complex 'I'"""
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
    """Solves ax + by + c = 0 and dx + ey + f = 0"""
    if not HAS_SYMPY: raise ValueError("SymPy missing")
    x, y = sp.symbols('x y')
    try:
        # We explicitly construct the equations to avoid any parser ambiguity
        eq1 = sp.Eq(a*x + b*y + c, 0)
        eq2 = sp.Eq(d*x + e*y + f, 0)
        sol = sp.solve([eq1, eq2], (x, y))
        
        if not sol: return "No unique solution"
        
        # Format to 4 decimal places
        x_val = _format_sympy_val(sol[x])
        y_val = _format_sympy_val(sol[y])
        return f"x = {x_val}, y = {y_val}"
    except Exception as err:
        return f"Error: {err}"

def solve_polynomial(coeffs):
    """Solves ax^2+bx+c=0 or ax^3+bx^2+cx+d=0"""
    if not HAS_SYMPY: raise ValueError("SymPy missing")
    x = sp.Symbol('x')
    try:
        expr = sum(c * x**i for i, c in enumerate(reversed(coeffs)))
        sols = sp.solve(expr, x)
        if not sols: return "No real solutions"
        res = []
        for i, s in enumerate(sols):
            res.append(f"x{i+1} = {_format_sympy_val(s)}")
        return " | ".join(res)
    except Exception as err:
        return f"Error: {err}"