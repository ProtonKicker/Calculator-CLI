import math
import re
import sys


def _sqrt(x: float) -> float | complex:
    """Square root supporting negative inputs (returns complex)."""
    r = x ** 0.5
    if isinstance(r, complex) and abs(r.imag) < 1e-15:
        return r.real
    return r



def _find_matching_brace(s: str, start: int) -> int:
    """Find matching closing brace from start position (must be '{')."""
    if start >= len(s) or s[start] != '{':
        return -1
    depth = 1
    i = start + 1
    while i < len(s) and depth > 0:
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
        i += 1
    return i - 1 if depth == 0 else -1


def _latex_to_python_inner(expr: str) -> str:
    """Recursively convert LaTeX math syntax to Python syntax."""

    # \frac{num}{den} → (num)/(den)
    i = 0
    while i < len(expr):
        if expr[i:i+6] == r"\frac{" and i + 6 <= len(expr):
            num_start = i + 5
            num_end = _find_matching_brace(expr, num_start)
            if num_end != -1:
                den_start = num_end + 1
                if den_start < len(expr) and expr[den_start] == '{':
                    den_end = _find_matching_brace(expr, den_start)
                    if den_end != -1:
                        num = _latex_to_python_inner(expr[num_start+1:num_end])
                        den = _latex_to_python_inner(expr[den_start+1:den_end])
                        replacement = f"({num})/({den})"
                        # Check for preceding function command: \func\frac{...}{...}
                        pre_func = None
                        j = i - 1
                        while j >= 0 and expr[j].isalpha():
                            j -= 1
                        if j >= 0 and expr[j] == '\\' and j + 1 < i:
                            pre_func = expr[j+1:i]
                        if pre_func:
                            replacement = f"{pre_func}({replacement})"
                            expr = expr[:j] + replacement + expr[den_end+1:]
                        else:
                            expr = expr[:i] + replacement + expr[den_end+1:]
                        return _latex_to_python_inner(expr)
        i += 1

    # \sqrt[index]{rad} and \sqrt{rad}
    i = 0
    while i < len(expr):
        if expr[i:i+5] == r"\sqrt" and i + 5 <= len(expr):
            idx = "2"
            rad_start = i + 5
            if rad_start < len(expr) and expr[rad_start] == '[':
                bracket_end = expr.find(']', rad_start + 1)
                if bracket_end != -1:
                    idx = expr[rad_start+1:bracket_end]
                    rad_start = bracket_end + 1
            if rad_start < len(expr) and expr[rad_start] == '{':
                rad_end = _find_matching_brace(expr, rad_start)
                if rad_end != -1:
                    rad = _latex_to_python_inner(expr[rad_start+1:rad_end])
                    if idx == "2":
                        expr = expr[:i] + f"sqrt({rad})" + expr[rad_end+1:]
                    else:
                        expr = expr[:i] + f"({rad})**(1/{idx})" + expr[rad_end+1:]
                    return _latex_to_python_inner(expr)
        i += 1

    # \cmd{arg} for any alphabetic LaTeX command
    i = 0
    while i < len(expr):
        if expr[i] == '\\' and i + 1 < len(expr) and expr[i+1].isalpha():
            cmd_end = i + 1
            while cmd_end < len(expr) and expr[cmd_end].isalpha():
                cmd_end += 1
            cmd_name = expr[i+1:cmd_end]
            if cmd_end < len(expr) and expr[cmd_end] == '{':
                arg_end = _find_matching_brace(expr, cmd_end)
                if arg_end != -1:
                    arg = _latex_to_python_inner(expr[cmd_end+1:arg_end])
                    expr = expr[:i] + f"{cmd_name}({arg})" + expr[arg_end+1:]
                    return _latex_to_python_inner(expr)
        i += 1

    # Strip \left and \right
    expr = re.sub(r'\\left\b', '', expr)
    expr = re.sub(r'\\right\b', '', expr)

    # Greek letter aliases (most common)
    expr = expr.replace(r'\pi', 'pi')
    expr = expr.replace(r'\tau', 'tau')
    expr = expr.replace(r'\alpha', 'alpha')
    expr = expr.replace(r'\beta', 'beta')
    expr = expr.replace(r'\gamma', 'gamma')
    expr = expr.replace(r'\delta', 'delta')
    expr = expr.replace(r'\theta', 'theta')
    expr = expr.replace(r'\lambda', 'lambda')
    expr = expr.replace(r'\mu', 'mu')
    expr = expr.replace(r'\phi', 'phi')
    expr = expr.replace(r'\omega', 'omega')
    expr = expr.replace(r'\epsilon', 'epsilon')
    expr = expr.replace(r'\varepsilon', 'varepsilon')
    expr = expr.replace(r'\rho', 'rho')
    expr = expr.replace(r'\sigma', 'sigma')
    expr = expr.replace(r'\xi', 'xi')
    expr = expr.replace(r'\zeta', 'zeta')
    expr = expr.replace(r'\eta', 'eta')
    expr = expr.replace(r'\iota', 'iota')
    expr = expr.replace(r'\kappa', 'kappa')
    expr = expr.replace(r'\upsilon', 'upsilon')
    expr = expr.replace(r'\chi', 'chi')
    expr = expr.replace(r'\psi', 'psi')

    # Convert LaTeX subscripts to normal text (before brace → paren conversion)
    expr = re.sub(r'_\{(\d+)\}', r'\1', expr)
    expr = re.sub(r'_(\d+)', r'\1', expr)

    # Remaining braces → parentheses
    expr = expr.replace('{', '(').replace('}', ')')

    # LaTeX operator aliases
    expr = expr.replace(r'\cdot', '*')
    expr = expr.replace(r'\times', '*')
    expr = expr.replace(r'\div', '/')
    expr = expr.replace(r'\pm', '+')

    # Strip backslash from remaining alphabetic commands
    expr = re.sub(r'\\([a-zA-Z]+)', r'\1', expr)

    # Remove any stray backslashes
    expr = expr.replace('\\', '')

    return expr


def latex_to_python(expr: str) -> str:
    """Convert LaTeX math syntax to a Python expression."""
    if '\\' not in expr:
        return expr
    expr = expr.replace(r'\(', '(').replace(r'\)', ')')
    expr = expr.replace(r'\[', '(').replace(r'\]', ')')
    return _latex_to_python_inner(expr)


def preprocess(expr: str) -> tuple[str, list[str]]:
    """Clean the expression and return (processed_expr, steps)."""
    steps = []

    # Convert LaTeX syntax before other processing
    expr = latex_to_python(expr)

    # Convert braces/brackets to parentheses (grouping)
    expr = expr.replace('{', '(').replace('}', ')').replace('[', '(').replace(']', ')')

    # Remove all spaces
    cleaned = expr.replace(" ", "")
    steps.append(f"Raw input: '{expr}'")
    steps.append(f"Cleaned: '{cleaned}'")

    # Convert text operators to Python operators
    replacements = [
        ("mod", "%"),
        ("MOD", "%"),
        ("Mod", "%"),
        ("^", "**"),
        ("π", "3.14159265358979"),
        ("PI", "3.14159265358979"),
        ("pi", "3.14159265358979"),
    ]
    for old, new in replacements:
        cleaned = cleaned.replace(old, new)
    steps.append(f"Operators converted")

    # Implicit multiplication: 2sin(30) -> 2*sin(30), 3(4+5) -> 3*(4+5)
    # Number followed by function name or parenthesis
    cleaned = re.sub(r'(\d)([a-zA-Z(])', r'\1*\2', cleaned)
    # Parenthesis followed by number: )( -> )*
    cleaned = re.sub(r'\)(\d)', r')*\1', cleaned)
    steps.append(f"Implicit multiplication added")

    # Imaginary unit: convert math 'i' to Python 'j'
    cleaned = re.sub(r'(\d)i\b', r'\1j', cleaned)
    cleaned = re.sub(r'\)i\b', r')*1j', cleaned)
    cleaned = re.sub(r'\bi\b', '1j', cleaned)
    steps.append(f"Imaginary unit converted")

    steps.append(f"Ready to evaluate: '{cleaned}'")

    return cleaned, steps


def evaluate(expr: str) -> float | str:
    """Evaluate a math expression safely."""
    # Create a safe namespace with math functions
    safe_dict = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "sqrt": _sqrt,
        "log": math.log,
        "log2": math.log2,
        "log10": math.log10,
        "exp": math.exp,
        "ln": math.log,
        "lg": math.log10,
        "abs": abs,
        "ceil": math.ceil,
        "floor": math.floor,
        "factorial": math.factorial,
        "pow": pow,
        "e": math.e,
        "tau": math.tau,
        # Physics & Chemistry constants (exact 2019 SI / CODATA 2018)
        "g": 9.80665,
        "c": 299792458,
        "G": 6.67430e-11,
        "h": 6.62607015e-34,
        "k": 1.380649e-23,
        "NA": 6.02214076e23,
        "R": 8.31446261815324,
        "F": 96485.33212331001,
        "atm": 101325,
        "Vm": 22.413969545014137,
        "mu0": 1.25663706212e-6,
        "eps0": 8.8541878128e-12,
        "epsilon0": 8.8541878128e-12,
        "varepsilon0": 8.8541878128e-12,
        # Imaginary unit
        "j": 1j,
    }

    try:
        result = eval(expr, {"__builtins__": {}}, safe_dict)
        return result
    except Exception as e:
        return f"Error: {e}"


def _format_float(x: float | int) -> str:
    """Format a number, using scientific notation for extreme values."""
    s = f"{x:.10g}"
    return "0" if s == "-0" else s


def format_result(result: float | complex | str) -> str:
    """Format the result nicely."""
    if isinstance(result, str):
        return result
    if isinstance(result, complex):
        r, i = result.real, result.imag
        if abs(r) < 1e-12:
            r = 0.0
        if abs(i) < 1e-12:
            i = 0.0
        if i == 0:
            return _format_float(r)
        if r == 0:
            return f"{_format_float(i)}j"
        r_str = _format_float(r)
        i_str = _format_float(abs(i))
        return f"{r_str}+{i_str}j" if i > 0 else f"{r_str}-{i_str}j"
    return _format_float(result)


def print_help():
    """Print help message."""
    print("\n📖 Scientific Calculator CLI")
    print("=" * 35)
    print("Basic Math: +  -  *  /  %  ^")
    print("Functions:  sin  cos  tan  sqrt  log  ln  lg  log2  log10")
    print("            abs  ceil  floor  exp")
    print("Constants:  pi  e  tau  j (imaginary unit)")
    print("           Physics:  g  c  G  h  k  mu0  eps0")
    print("           Chem:     NA  R  F  atm  Vm")
    print()
    print("LaTeX input is supported:")
    print(r"  \frac{1}{2}         -> 0.5")
    print(r"  \sqrt{144}          -> 12")
    print(r"  \sin{0}             -> 0")
    print(r"  \pi                 -> 3.141593")
    print(r"  \sin\frac{\pi}{2}   -> 1")
    print(r"  \mu_0  \epsilon_0   -> constants")
    print()
    print("Examples:")
    print("  7 mod 5       -> 2")
    print("  sqrt(144)     -> 12")
    print("  sin(0)        -> 0")
    print("  2^10          -> 1024")
    print("  2sin(30)      -> uses radians")
    print()
    print("  ^h or help    -> this message")
    print("  ^q or quit    -> exit")
    print()


def main():
    print("🔢 Scientific Calculator CLI")
    print("Type ^h for help. Type ^q to quit.\n")

    while True:
        try:
            expr = input("calc > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!\n")
            break

        if not expr:
            continue

        if expr in ("^q", "quit", "exit", "q"):
            print("👋 Goodbye!\n")
            break

        if expr in ("^h", "help", "h"):
            print_help()
            continue

        # Process and evaluate
        cleaned, _ = preprocess(expr)

        result = evaluate(cleaned)
        formatted = format_result(result)

        # Show result
        print(f"⇒ {formatted}\n") #→↪↳⇒▶►


if __name__ == "__main__":
    main()
