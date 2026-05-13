I'm a student. One day I thought: Why bother carrying the old fashioned TI-84 around if I have my laptop? Kalker is definitely close but I haven't found any calculator that I really liked, so here I'm building myself one👇

# Calculator CLI 

A terminal-based scientific calculator supporting basic math, scientific functions, imaginary numbers, and LaTeX syntax input.


## Built-in Constants

| Constant | Value | Description | Field |
|----------|-------|-------------|-------|
| `pi` | 3.14159265358979 | π |
| `e` | 2.718281828459045 | Euler's number |
| `tau` | 6.283185307179586 | τ = 2π |
| `g` | 9.80665 | Standard gravity (m/s²) | Physics |
| `c` | 299792458 | Speed of light (m/s) | Physics |
| `G` | 6.67430×10⁻¹¹ | Gravitational constant (m³/kg·s²) | Physics |
| `h` | 6.62607015×10⁻³⁴ | Planck constant (J·s) | Physics |
| `k` | 1.380649×10⁻²³ | Boltzmann constant (J/K) | Physics |
| `mu0` | 1.25663706212×10⁻⁶ | Vacuum permeability (N/A²) | Physics |
| `eps0` | 8.8541878128×10⁻¹² | Vacuum permittivity (F/m) | Physics |
| `NA` | 6.02214076×10²³ | Avogadro constant (mol⁻¹) | Chemistry |
| `R` | 8.31446261815324 | Ideal gas constant (J/mol·K) | Chemistry |
| `F` | 96485.33212331001 | Faraday constant (C/mol) | Chemistry |
| `atm` | 101325 | Standard atmosphere (Pa) | Chemistry |
| `Vm` | 22.413969545014137 | Molar volume @ STP (L/mol) | Chemistry |

LaTeX subscript form: `\mu_0`, `\epsilon_0`, `\varepsilon_0` are also accepted.

## Commands

| Command | Description |
|---------|-------------|
| `help` / `h` / `^h` | Show help message |
| `quit` / `q` / `^q` | Exit the calculator |
| `yes_i` / `yes_j` | Switches between `i` and `j` fo display of imaginary unit as (input accepts both `i` and `j`) |
| `i_root` | Toggle display of imaginary/complex roots in equation solving |
| `radian` / `degree` | Toggle angle input mode for trigonometric functions |

- **Imaginary unit display**: By default, imaginary units are displayed as `j`. Typing `yes_i` changes the output to use `i`, and `yes_j` reverts to `j`. Both `j` and `i` are always accepted as input.
- **Imaginary roots**: When equation solving (`x^2 + 1 = 0`), toggling `i_root` off filters results to show only real roots.
- **Angle mode**: In degree mode, `sin(90)` = 1 and `asin(1)` = 90. Default is radian mode.

## LaTeX Input

The calculator supports LaTeX-style syntax for many operations:

| Input | Display | Example |
|-------|---------|---------|
| `\frac{num}{den}` | num/den | `\frac{1}{2}` → 0.5 |
| `\sqrt{rad}` | √rad | `\sqrt{144}` → 12 |
| `\sqrt[n]{rad}` | ∛rad, ∜rad, rad^(1/n) | `\sqrt[3]{8}` → 2 |
| `\sin{arg}` | sin(arg) | `\sin{0}` → 0 |
| `\pi`, `\tau`, etc. | π, τ | `\pi` → 3.141593 |
| `\mu_0`, `\epsilon_0` | constants | Permittivity, permeability |

## Definite Integrals (Numerical)

Numerical integration using adaptive Simpson's rule:

```
\int_0^1 2x dx              → 1
\int_0^{pi} sin(x) dx       → 2
\int_0^1 \int_0^2 x*y dy dx → 1
```

Supports any nesting depth. Bounds can be braced `{0}` or unbraced `0`. Use `d{var}` to specify the integration variable. Also supports `\iint` (∬) and `\iiint` (∭) notation.

## Summations

```
\sum_{n=0}^{5} n^2                            → 55
\sum_{i=1}^{3} \sum_{j=1}^{2} i*j            → 18
\sum^{3}_{i=1} 3i                            → 18  (reversed bounds also work)
```

Supports any nesting depth. Both `_lower^upper` and `^upper_lower` orderings are accepted.

## Numerical Derivatives

Evaluate derivatives at a point using central finite differences:

```
d/dx_3 x^2          → 6        (first derivative at x=3)
d^2/dx^2_3 x^3     → 18       (second derivative at x=3)
d/dx_0 sin(x)       → 1        (d/dx sin(x) at x=0)
```

Supports higher-order derivatives via `d^n/dx^n` or `dn/dxn` notation.

## Notes

- In integrals, sums, and derivatives, `i` is treated as a variable name (not the imaginary unit). Use `j` explicitly for the imaginary unit in these expressions.
- Numerical integration uses adaptive Simpson's rule with a tolerance of 1e-8.
- Derivatives use central finite differences with adaptive step sizes.
- For sums, only the `{var=start}` braced subscript form is supported.
