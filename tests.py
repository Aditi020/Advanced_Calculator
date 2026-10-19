"""Run: python tests.py — no GUI involved, pure maths."""
import sys
import calculations as calc


def check(name, got, expected, tol=1e-9):
    ok = abs(got - expected) < tol if isinstance(expected, float) else got == expected
    print(f"{'OK  ' if ok else 'FAIL'}  {name}: got {got!r}, expected {expected!r}")
    return ok


def main():
    results = [
        check("5+10",     calc.evaluate("5+10"),       15),
        check("25*4",     calc.evaluate("25*4"),       100),
        check("2+3*4",    calc.evaluate("2+3*4"),      14),
        check("(2+3)*4",  calc.evaluate("(2+3)*4"),    20),
        check("2**10",    calc.evaluate("2**10"),      1024),
        check("sqrt(81)", calc.evaluate("sqrt(81)"),   9),
        check("sin 30°",  calc.evaluate("sin(30)"),    0.5),
        check("cos 60°",  calc.evaluate("cos(60)"),    0.5),
        check("sin π/2",  calc.evaluate("sin(pi/2)", angle_mode="RAD"), 1.0),
        check("5!",       calc.evaluate("5!"),         120),
        check("log 1000", calc.evaluate("log(1000)"),  3),
        check("ln e",     calc.evaluate("ln(e)"),      1),
        check("2^3^2",    calc.evaluate("2**3**2"),    512),
    ]

    vars = {}
    calc.try_assignment("a = 5", vars)
    calc.try_assignment("b = 10", vars)
    results.append(check("a+b", calc.evaluate("a+b", vars), 15))

    for expr in ["5/0", "foo(5)", "__import__('os')", "sqrt("]:
        try:
            calc.evaluate(expr)
            print(f"FAIL  should have errored: {expr}")
            results.append(False)
        except Exception as e:
            print(f"OK    rejected {expr!r}: {e}")
            results.append(True)

    try:
        sols = calc.solve_equation("x**2 - 4 = 0")
        ok = {float(s) for s in sols} == {-2.0, 2.0}
        print(f"{'OK  ' if ok else 'FAIL'}  x**2-4=0 → {sols}")
        results.append(ok)
    except Exception as e:
        print(f"FAIL  solve error: {e}")
        results.append(False)

    print(f"\n{sum(results)}/{len(results)} passed")
    return all(results)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)