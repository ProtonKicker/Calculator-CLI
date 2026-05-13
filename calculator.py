import cmath
import math
import re
import sys
from fractions import Fraction

_imag_unit = "j"
_show_imag_roots = True
_deg_mode = False
_DEG = math.pi / 180
_RAD = 180 / math.pi


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


def _is_simple(s: str) -> bool:
    """Check if a string is a simple value that doesn't need parentheses."""
    return bool(re.fullmatch(r'[a-zA-Z0-9πτ.√∛∜]+', s))


def _latex_to_display_inner(expr: str) -> str:
    """Recursively convert LaTeX math syntax to display-friendly Unicode string."""

    # \frac{num}{den} -> num/den
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
                        num = _latex_to_display_inner(expr[num_start+1:num_end])
                        den = _latex_to_display_inner(expr[den_start+1:den_end])
                        pre_func = None
                        j = i - 1
                        while j >= 0 and expr[j].isalpha():
                            j -= 1
                        if j >= 0 and expr[j] == '\\' and j + 1 < i:
                            pre_func = expr[j+1:i]
                        num_str = num if _is_simple(num) else f"({num})"
                        den_str = den if _is_simple(den) else f"({den})"
                        replacement = f"{num_str}/{den_str}"
                        if pre_func:
                            replacement = f"{pre_func}({replacement})"
                            expr = expr[:j] + replacement + expr[den_end+1:]
                        else:
                            expr = expr[:i] + replacement + expr[den_end+1:]
                        return _latex_to_display_inner(expr)
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
                    rad = _latex_to_display_inner(expr[rad_start+1:rad_end])
                    rad_str = rad if _is_simple(rad) else f"({rad})"
                    root_map = {"2": "√", "3": "∛", "4": "∜"}
                    symbol = root_map.get(idx)
                    if symbol:
                        replacement = f"{symbol}{rad_str}"
                    else:
                        replacement = f"{rad_str}^(1/{idx})"
                    expr = expr[:i] + replacement + expr[rad_end+1:]
                    return _latex_to_display_inner(expr)
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
                    arg = _latex_to_display_inner(expr[cmd_end+1:arg_end])
                    expr = expr[:i] + f"{cmd_name}({arg})" + expr[arg_end+1:]
                    return _latex_to_display_inner(expr)
        i += 1

    # Strip \left and \right
    expr = re.sub(r'\\left\b', '', expr)
    expr = re.sub(r'\\right\b', '', expr)

    # Greek letter aliases
    greek_map = {
        r'\pi': 'π', r'\tau': 'τ', r'\alpha': 'α', r'\beta': 'β',
        r'\gamma': 'γ', r'\delta': 'δ', r'\theta': 'θ', r'\lambda': 'λ',
        r'\mu': 'μ', r'\phi': 'φ', r'\omega': 'ω', r'\epsilon': 'ε',
        r'\varepsilon': 'ε', r'\rho': 'ρ', r'\sigma': 'σ', r'\xi': 'ξ',
        r'\zeta': 'ζ', r'\eta': 'η', r'\iota': 'ι', r'\kappa': 'κ',
        r'\upsilon': 'υ', r'\chi': 'χ', r'\psi': 'ψ',
    }
    for cmd, char in greek_map.items():
        expr = expr.replace(cmd, char)

    # LaTeX operator aliases
    expr = expr.replace(r'\cdot', '*')
    expr = expr.replace(r'\times', '*')
    expr = expr.replace(r'\div', '/')
    expr = expr.replace(r'\pm', '+')

    # Convert LaTeX subscripts to normal text
    expr = re.sub(r'_\{(\d+)\}', r'_\1', expr)
    expr = re.sub(r'_(\d+)', r'\1', expr)

    # Remaining braces -> parentheses
    expr = expr.replace('{', '(').replace('}', ')')

    # Strip backslash from remaining alphabetic commands
    expr = re.sub(r'\\([a-zA-Z]+)', r'\1', expr)

    # Remove any stray backslashes
    expr = expr.replace('\\', '')

    return expr


def _replace_sqrt(s: str) -> str:
    """Replace sqrt(...) with √(...) handling nested parentheses."""
    result = []
    i = 0
    while i < len(s):
        if s[i:i+5] == 'sqrt(':
            depth = 1
            j = i + 5
            while j < len(s) and depth > 0:
                if s[j] == '(':
                    depth += 1
                elif s[j] == ')':
                    depth -= 1
                j += 1
            inner = _replace_sqrt(s[i+5:j-1])
            rad_str = inner if _is_simple(inner) else f'({inner})'
            result.append('√' + rad_str)
            i = j
        else:
            result.append(s[i])
            i += 1
    return ''.join(result)


def latex_to_display(expr: str) -> str:
    """Convert LaTeX math syntax to a display-friendly Unicode string."""
    if '\\' in expr:
        expr = expr.replace(r'\(', '(').replace(r'\)', ')')
        expr = expr.replace(r'\[', '(').replace(r'\]', ')')
        expr = _latex_to_display_inner(expr)
    return _replace_sqrt(expr)


_ROOT_RE = re.compile(r'\(?([a-zA-Z_]\w*|\d+(?:\.\d+)?)\)?\*\*\(1/(\d+)\)')
_ROOT_HALF_RE = re.compile(r'\(?([a-zA-Z_]\w*|\d+(?:\.\d+)?)\)?\*\*0\.5(?!\d)')


def detect_root(cleaned: str) -> str | None:
    m = _ROOT_RE.search(cleaned)
    if m:
        base = m.group(1)
        n = int(m.group(2))
        if n == 2:
            return f"√{base}"
        elif n == 3:
            return f"∛{base}"
        elif n == 4:
            return f"∜{base}"
        else:
            return f"{base}^(1/{n})"
    m = _ROOT_HALF_RE.search(cleaned)
    if m:
        return f"√{m.group(1)}"
    return None


def to_fraction(x: float) -> str | None:
    if abs(x - round(x)) < 1e-12:
        return None
    f = Fraction(x).limit_denominator(10000)
    if f.denominator != 1 and abs(float(f) - x) < 1e-10:
        return f"{f.numerator}/{f.denominator}"
    return None


# ── Multi-Integral Solver ─────────────────────────────────────────────────────

_INTEGRAL_SEG = re.compile(
    r'\\(?:i+|I+)nt\s*'
    r'(?:'
    r'_\s*\{?([^\s}{^_]+)\}?(?:\s*\^\s*\{?([^\s}{^_]+)\}?)?'    # _lower ^upper?
    r'|'
    r'\^\s*\{?([^\s}{^_]+)\}?(?:\s*_\s*\{?([^\s}{^_]+)\}?)?'    # ^upper _lower?
    r')?'
)


def _parse_multi_integral(expr):
    r"""Parse any number of nested \int_{lower}^{upper} ... d{var} expressions.
    Returns (outer_to_inner_list, integrand_text) or None."""
    expr = expr.strip()
    if not re.match(r'\\i+nt', expr):
        return None
    int_matches = list(_INTEGRAL_SEG.finditer(expr))
    if not int_matches:
        return None
    dvar_matches = list(re.finditer(r'd\s*\{?([a-zA-Z])\}?', expr))
    if len(int_matches) != len(dvar_matches):
        return None
    last_int_end = int_matches[-1].end()
    first_dvar_start = dvar_matches[0].start()
    integrand = expr[last_int_end:first_dvar_start].strip()
    ints = []
    for m in int_matches:
        if m.group(1) is not None:
            ints.append((m.group(1), m.group(2)))
        else:
            ints.append((m.group(4), m.group(3)))
    dvars = [m.group(1) for m in dvar_matches]
    paired = [
        (lower, upper, dvar)
        for (lower, upper), dvar in zip(ints, reversed(dvars))
    ]
    return paired, integrand


def _numerical_integrate(f, a, b, depth=0):
    """Integrate f from a to b using composite Simpson's rule."""
    if a == b:
        return 0.0
    if a > b:
        return -_numerical_integrate(f, b, a, depth)
    n = max(8, 150 // (depth + 1))
    if n % 2:
        n += 1
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n, 2):
        s += 4 * f(a + i * h)
    for i in range(2, n - 1, 2):
        s += 2 * f(a + i * h)
    return s * h / 3


def _preprocess_light(expr):
    """Preprocess without converting standalone i to imaginary unit."""
    expr = latex_to_python(expr)
    expr = expr.replace('{', '(').replace('}', ')').replace('[', '(').replace(']', ')')
    cleaned = expr.replace(" ", "")
    for old, new in [("mod", "%"), ("MOD", "%"), ("Mod", "%"),
                     ("^", "**"),
                     ("π", "3.14159265358979"),
                     ("PI", "3.14159265358979"),
                     ("pi", "3.14159265358979")]:
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r'(\d)([a-zA-Z(])', r'\1*\2', cleaned)
    cleaned = re.sub(r'\)(\d)', r')*\1', cleaned)
    return cleaned


def solve_multi_integral(expr):
    parsed = _parse_multi_integral(expr)
    if not parsed:
        return None
    integrals, integrand = parsed
    integrand_cleaned = _preprocess_light(integrand)

    def eval_depth(depth, var_bindings):
        if depth >= len(integrals):
            sd = _build_safe_dict()
            sd.update(var_bindings)
            try:
                return eval(integrand_cleaned, {"__builtins__": {}}, sd)
            except Exception:
                return float('nan')

        lower_str, upper_str, var = integrals[depth]
        lower_cleaned, _ = preprocess(lower_str)
        upper_cleaned, _ = preprocess(upper_str)
        try:
            lo = float(eval(lower_cleaned, {"__builtins__": {}}, _build_safe_dict()))
            hi = float(eval(upper_cleaned, {"__builtins__": {}}, _build_safe_dict()))
        except Exception:
            return float('nan')

        def f(val):
            nb = var_bindings.copy()
            nb[var] = val
            return eval_depth(depth + 1, nb)

        return _numerical_integrate(f, lo, hi, depth)

    result = eval_depth(0, {})
    if isinstance(result, complex) or (math.isnan(result) if isinstance(result, (int, float)) else False):
        return None
    if isinstance(result, (int, float)) and math.isinf(result):
        return None
    if isinstance(result, (int, float)) and abs(result - round(result)) < 5e-7:
        return round(result)
    return result


# ── Multi-Sum Solver ──────────────────────────────────────────────────────────

_SUM_SEG = re.compile(
    r'\\sum\s*_\s*\{?([a-zA-Z])\s*=\s*([^}]+)\}?\s*\^\s*\{?([^\s}]+)\}?'
)


def _parse_multi_sum(expr):
    r"""Parse any number of nested \sum_{var=start}^{end} expressions.
    Returns (outer_to_inner_list, summand_text) or None."""
    expr = expr.strip()
    if not expr.startswith(r'\sum'):
        return None
    sum_matches = list(_SUM_SEG.finditer(expr))
    if not sum_matches:
        return None
    last_end = sum_matches[-1].end()
    summand = expr[last_end:].strip()
    sums = [(m.group(1), m.group(2), m.group(3)) for m in sum_matches]
    return sums, summand


def solve_multi_sum(expr):
    parsed = _parse_multi_sum(expr)
    if not parsed:
        return None
    sums, summand = parsed
    summand_cleaned = _preprocess_light(summand)

    def eval_depth(depth, var_bindings):
        if depth >= len(sums):
            sd = _build_safe_dict()
            sd.update(var_bindings)
            try:
                return eval(summand_cleaned, {"__builtins__": {}}, sd)
            except Exception:
                return float('nan')

        var, start_str, end_str = sums[depth]
        start_cleaned, _ = preprocess(start_str)
        end_cleaned, _ = preprocess(end_str)
        try:
            lo = int(eval(start_cleaned, {"__builtins__": {}}, _build_safe_dict()))
            hi = int(eval(end_cleaned, {"__builtins__": {}}, _build_safe_dict()))
        except Exception:
            return float('nan')

        total = 0.0
        for i in range(lo, hi + 1):
            nb = var_bindings.copy()
            nb[var] = i
            total += eval_depth(depth + 1, nb)
        return total

    result = eval_depth(0, {})
    if isinstance(result, complex) or (math.isnan(result) if isinstance(result, (int, float)) else False):
        return None
    if isinstance(result, (int, float)) and math.isinf(result):
        return None
    if isinstance(result, (int, float)) and abs(result - round(result)) < 5e-7:
        return round(result)
    return result


# ── Derivative Solver ─────────────────────────────────────────────────────────

_DERIV_RE = re.compile(r'd(?:\^?(\d+))?/d([a-zA-Z])(?:\^?(\d+))?\s*(?:_\{?([^\s}]+)\}?)?\s*(.+)$')


def _numerical_derivative(f, x, order=1):
    """Compute the nth derivative of f at x using central differences."""
    if order == 0:
        return f(x)
    if order == 1:
        h = 1e-5 * max(1.0, abs(x))
        return (f(x + h) - f(x - h)) / (2 * h)
    if order == 2:
        h = 1e-4 * max(1.0, abs(x))
        return (f(x + h) - 2 * f(x) + f(x - h)) / (h * h)
    if order == 3:
        h = 1e-4 * max(1.0, abs(x))
        h2 = 2 * h
        return (f(x + h2) - 2 * f(x + h) + 2 * f(x - h) - f(x - h2)) / (2 * h ** 3)
    if order == 4:
        h = 1e-4 * max(1.0, abs(x))
        h2 = 2 * h
        return (f(x + h2) - 4 * f(x + h) + 6 * f(x) - 4 * f(x - h) + f(x - h2)) / (h ** 4)
    f_prev = lambda val: _numerical_derivative(f, val, order - 1)
    h = 1e-4 * max(1.0, abs(x))
    return (f_prev(x + h) - f_prev(x - h)) / (2 * h)


def solve_derivative(expr):
    m = _DERIV_RE.match(expr.strip())
    if not m:
        return None
    var = m.group(2)
    order = int(m.group(1) or m.group(3) or '1')
    point_str = m.group(4)
    ex = m.group(5).strip()
    if point_str is None:
        return None
    try:
        point_cleaned, _ = preprocess(point_str)
    except Exception:
        return None
    ex_cleaned = _preprocess_light(ex)
    try:
        x0 = float(eval(point_cleaned, {"__builtins__": {}}, _build_safe_dict()))
    except Exception:
        return None
    if isinstance(x0, str):
        return None

    def f(val):
        sd = _build_safe_dict(var, val)
        try:
            return eval(ex_cleaned, {"__builtins__": {}}, sd)
        except Exception:
            return float('nan')

    try:
        deriv = _numerical_derivative(f, x0, order)
        if abs(deriv) < 1e-12:
            deriv = 0.0
        if isinstance(deriv, (int, float)) and abs(deriv - round(deriv)) < 5e-7:
            deriv = round(deriv)
        if math.isnan(deriv) or math.isinf(deriv):
            return None
        return deriv
    except Exception:
        return None


# ── Display formatter ─────────────────────────────────────────────────────────

def _format_calc_display(expr):
    expr = expr.replace(r'\iiiint', '∬∬').replace(r'\iiint', '∭').replace(r'\iint', '∬')
    expr = expr.replace(r'\int', '∫')
    return expr.replace(r'\sum', '∑')


# ─────────────────────────────────────────────────────────────────────────────


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
    try:
        result = eval(expr, {"__builtins__": {}}, _build_safe_dict())
        return result
    except Exception as e:
        return f"Error: {e}"


def _format_float(x: float | int) -> str:
    """Format a number, using scientific notation for extreme values."""
    s = f"{x:.10g}"
    return "0" if s == "-0" else s


_CONSTANT_NAMES = {
    "e", "g", "c", "h", "k", "j",
    "pi", "tau",
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sqrt", "log", "log2", "log10", "exp", "ln", "lg",
    "abs", "ceil", "floor", "factorial", "pow",
}

def _find_variable(expr: str) -> str | None:
    names = set(re.findall(r'[a-z]\w*', expr))
    names -= _CONSTANT_NAMES
    names = {n for n in names if n.islower()}
    return names.pop() if len(names) == 1 else None


def _finite(x):
    if isinstance(x, complex):
        return math.isfinite(x.real) and math.isfinite(x.imag)
    return isinstance(x, (int, float)) and math.isfinite(x)


def _secant_from(f, guess):
    x0, x1 = guess, guess + 0.1 if guess == 0 else guess * 1.1
    for _ in range(500):
        f0, f1 = f(x0), f(x1)
        if not (_finite(f0) and _finite(f1)):
            break
        if abs(f1) < 1e-13:
            return x1
        if abs(f1 - f0) < 1e-15:
            break
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        if abs(x2 - x1) < 1e-12:
            if abs(f1) < 1e-8:
                return x2
            break
        x0, x1 = x1, x2
    return None


def _find_roots(f):
    real_guesses = [0, 1, -1, 2, -2, 5, -5, 10, -10, 100, -100]
    complex_guesses = [
        1j, -1j,
        0.5+0.866j, -0.5+0.866j, -0.5-0.866j, 0.5-0.866j,
    ]
    roots = []
    for g in real_guesses + complex_guesses:
        r = _secant_from(f, g)
        if r is None:
            continue
        if not any(abs(r - e) < 1e-6 for e in roots):
            roots.append(r)
    roots.sort(key=lambda r: (r.real if isinstance(r, complex) else r,
                               abs(r.imag) if isinstance(r, complex) else 0))
    return roots


def _build_safe_dict(var_name: str | None = None, var_val: float | complex | None = None) -> dict:
    use_cmath = isinstance(var_val, complex)
    d = {
        "abs": abs, "pow": pow,
        "e": math.e, "tau": math.tau,
        "g": 9.80665, "c": 299792458, "G": 6.67430e-11,
        "h": 6.62607015e-34, "k": 1.380649e-23,
        "NA": 6.02214076e23, "R": 8.31446261815324, "F": 96485.33212331001,
        "atm": 101325, "Vm": 22.413969545014137,
        "mu0": 1.25663706212e-6, "eps0": 8.8541878128e-12,
        "epsilon0": 8.8541878128e-12, "varepsilon0": 8.8541878128e-12,
        "j": 1j,
    }
    if use_cmath:
        d.update({
            "sin": cmath.sin, "cos": cmath.cos, "tan": cmath.tan,
            "asin": cmath.asin, "acos": cmath.acos, "atan": cmath.atan,
            "sqrt": cmath.sqrt,
            "log": cmath.log, "log2": lambda z: cmath.log(z, 2),
            "log10": lambda z: cmath.log(z, 10),
            "exp": cmath.exp, "ln": cmath.log, "lg": lambda z: cmath.log(z, 10),
        })
    else:
        d.update({
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "asin": math.asin, "acos": math.acos, "atan": math.atan,
            "sqrt": _sqrt,
            "log": math.log, "log2": math.log2, "log10": math.log10,
            "exp": math.exp, "ln": math.log, "lg": math.log10,
            "ceil": math.ceil, "floor": math.floor, "factorial": math.factorial,
        })
    if _deg_mode:
        m = cmath if use_cmath else math
        d.update({
            "sin": lambda x: m.sin(x * _DEG),
            "cos": lambda x: m.cos(x * _DEG),
            "tan": lambda x: m.tan(x * _DEG),
            "asin": lambda x: m.asin(x) * _RAD,
            "acos": lambda x: m.acos(x) * _RAD,
            "atan": lambda x: m.atan(x) * _RAD,
        })
    if var_name is not None and var_val is not None:
        d[var_name] = var_val
    return d


def _format_root(r: float | complex) -> str:
    if isinstance(r, complex):
        if abs(r.imag) < 1e-12:
            val = r.real
            rnd = round(val)
            return str(rnd) if abs(val - rnd) < 1e-6 else _format_float(val)
        real, imag = r.real, r.imag
        if abs(real) < 1e-12:
            real = 0.0
        if abs(imag) < 1e-12:
            imag = 0.0
        if real == 0:
            return f"{_format_float(imag)}{_imag_unit}"
        r_str = _format_float(real)
        i_str = _format_float(abs(imag))
        return f"{r_str}+{i_str}{_imag_unit}" if imag > 0 else f"{r_str}-{i_str}{_imag_unit}"
    rnd = round(r)
    return str(rnd) if abs(r - rnd) < 1e-6 else _format_float(r)


def solve_equation(expr: str) -> str:
    parts = expr.split("=")
    if len(parts) != 2:
        return "Error: Equation must have exactly one '='"

    lhs_raw, rhs_raw = parts[0].strip(), parts[1].strip()

    var = _find_variable(lhs_raw + " " + rhs_raw)
    if var is None:
        return "Error: Could not identify a single variable to solve for"

    lhs, _ = preprocess(lhs_raw)
    rhs, _ = preprocess(rhs_raw)

    def f(val):
        sd = _build_safe_dict(var, val)
        try:
            return eval(lhs, {"__builtins__": {}}, sd) - eval(rhs, {"__builtins__": {}}, sd)
        except Exception:
            return float("nan")

    roots = _find_roots(f)
    roots = [r for r in roots if abs(r) < 1000]
    if not _show_imag_roots:
        roots = [r for r in roots if not (isinstance(r, complex) and abs(r.imag) > 1e-12)]
    if not roots:
        return f"Error: No solution found for '{var}'"

    parts = []
    for r in roots[:5]:
        parts.append(_format_root(r))
    j = " or ".join(parts)
    if len(roots) > 5:
        j += f" … and {len(roots) - 5} more"
    return f"{var} = {j}"


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
            return f"{_format_float(i)}{_imag_unit}"
        r_str = _format_float(r)
        i_str = _format_float(abs(i))
        return f"{r_str}+{i_str}{_imag_unit}" if i > 0 else f"{r_str}-{i_str}{_imag_unit}"
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
    print("Integrals (numerical):")
    print(r"  \int_0^1 2x dx                 -> 1")
    print(r"  \int_0^1 \int_0^2 x*y dy dx    -> 1")
    print()
    print("Sums:")
    print(r"  \sum_{n=0}^{5} n^2             -> 55")
    print(r"  \sum_{i=1}^{3} \sum_{j=1}^{2} i*j -> 18")
    print()
    print("Derivatives (numerical):")
    print(r"  d/dx_3 x^2                     -> 6")
    print(r"  d^2/dx^2_3 x^3                -> 18")
    print()
    print("Examples:")
    print("  7 mod 5       -> 2")
    print("  sqrt(144)     -> 12")
    print("  sin(0)        -> 0")
    print("  2^10          -> 1024")
    print("  2sin(30)      -> uses radians")
    print("  x^2 = 4       -> solves equation")
    print()
    print("  ^h / help     -> this message")
    print("  ^q / quit     -> exit")
    print("  yes_i / yes_j -> set imaginary unit display")
    print("  i_root        -> toggle imaginary root display")
    print("  radian/degree -> toggle angle input mode")
    print()


def main():
    global _imag_unit, _show_imag_roots, _deg_mode
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

        if expr == "yes_i":
            _imag_unit = "i"
            print("⇒ Imaginary unit set to i\n")
            continue

        if expr == "yes_j":
            _imag_unit = "j"
            print("⇒ Imaginary unit set to j\n")
            continue

        if expr == "i_root":
            _show_imag_roots = not _show_imag_roots
            msg = "displaying imaginary roots" if _show_imag_roots else "displaying only real roots"
            print(f"⇒ {msg}\n")
            continue

        if expr in ("radian", "degree"):
            _deg_mode = expr == "degree"
            mode = "Degree" if _deg_mode else "Radian"
            print(f"⇒ {mode} mode\n")
            continue

        # Integral solver
        if re.match(r'\\i+nt(?:_|\^|$|\s)', expr):
            result = solve_multi_integral(expr)
            if result is not None:
                display = _format_calc_display(expr)
                formatted = format_result(result)
                if isinstance(result, (int, float)) and abs(result - round(result)) >= 1e-12:
                    frac = to_fraction(result)
                    if frac:
                        formatted = frac
                print(f"⇒ {display} = {formatted}\n")
                continue
            print("⇒ Error: Invalid integral expression\n")
            continue

        # Sum solver
        if expr.startswith(r'\sum'):
            result = solve_multi_sum(expr)
            if result is not None:
                display = _format_calc_display(expr)
                formatted = format_result(result)
                if isinstance(result, (int, float)) and abs(result - round(result)) >= 1e-12:
                    frac = to_fraction(result)
                    if frac:
                        formatted = frac
                print(f"⇒ {display} = {formatted}\n")
                continue
            print("⇒ Error: Invalid sum expression\n")
            continue

        # Derivative solver
        m_d = re.match(r'd(?:\^?\d+)?/d[a-zA-Z]', expr)
        if m_d:
            result = solve_derivative(expr)
            if result is not None:
                formatted = format_result(result)
                if isinstance(result, (int, float)) and abs(result - round(result)) >= 1e-12:
                    frac = to_fraction(result)
                    if frac:
                        formatted = frac
                print(f"⇒ {expr} = {formatted}\n")
                continue
            # Fall through to normal processing

        # Equation solving if '=' is present
        if "=" in expr:
            formatted = solve_equation(expr)
            print(f"⇒ {formatted}\n")
            continue

        # Process and evaluate
        cleaned, _ = preprocess(expr)

        result = evaluate(cleaned)
        formatted = format_result(result)

        # Whole number -> just show number
        if isinstance(result, (int, float)) and abs(result - round(result)) < 1e-12:
            print(f"⇒ {formatted}\n")
            continue

        # Determine true value display
        true_val = None

        # 1. LaTeX display (for \sqrt, \frac, etc.)
        if '\\' in expr:
            true_val = latex_to_display(expr)

        # 2. Root pattern (for num^(1/n) notation)
        if true_val is None:
            true_val = detect_root(cleaned)

        # 3. Fraction conversion (for rational results)
        if true_val is None and isinstance(result, (int, float)):
            true_val = to_fraction(result)

        # 4. Fallback to latex_to_display (original or cleaned)
        if true_val is None:
            true_val = latex_to_display(expr)

        if true_val != formatted:
            print(f"⇒ {true_val} = {formatted}\n")
        else:
            print(f"⇒ {formatted}\n")


if __name__ == "__main__":
    main()
