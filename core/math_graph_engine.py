"""Equation parsing and plotting helpers for GraphiQ."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

import numpy as np
from sympy import (
    Abs,
    E,
    Symbol,
    acos,
    acosh,
    asin,
    asinh,
    atan,
    atanh,
    cos,
    cosh,
    diff,
    exp,
    latex,
    lambdify,
    log,
    pi,
    simplify,
    sin,
    sinh,
    sqrt,
    tan,
    tanh,
)
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)
SAFE_GLOBALS = {
    "x": Symbol("x"),
    "y": Symbol("y"),
    "z": Symbol("z"),
    "t": Symbol("t"),
    "pi": pi,
    "e": E,
    "E": E,
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "asin": asin,
    "acos": acos,
    "atan": atan,
    "sinh": sinh,
    "cosh": cosh,
    "tanh": tanh,
    "asinh": asinh,
    "acosh": acosh,
    "atanh": atanh,
    "exp": exp,
    "log": log,
    "ln": log,
    "sqrt": sqrt,
    "abs": Abs,
    "Abs": Abs,
}
PLOT_RESERVED = {
    "cartesian": {"x"},
    "implicit": {"x", "y"},
    "parametric": {"t"},
    "surface": {"x", "y"},
}


@dataclass
class CurveData:
    label: str
    kind: str
    x_values: list[float | None]
    y_values: list[float | None]
    expression: str
    parameters: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)


def _normalize_expression(value: str) -> str:
    return value.strip().replace("^", "**")


def _build_local_dict(raw: str) -> dict[str, Any]:
    local_dict = dict(SAFE_GLOBALS)
    for token in set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", raw)):
        if token not in local_dict:
            local_dict[token] = Symbol(token)
    return local_dict


def _parse_sympy_expression(raw: str):
    normalized = _normalize_expression(raw)
    return parse_expr(normalized, transformations=TRANSFORMATIONS, local_dict=_build_local_dict(normalized))


def _numeric_integral(x_values: list[float], y_values: list[float]) -> float:
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y_values, x_values))
    return float(np.trapz(y_values, x_values))


def parse_parameters(raw: str) -> dict[str, float]:
    params: dict[str, float] = {}
    if not raw.strip():
        return params
    for item in raw.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(f"Invalid parameter assignment: {item}")
        name, value = item.split("=", 1)
        normalized_value = _normalize_expression(value)
        parsed_value = parse_expr(normalized_value, transformations=TRANSFORMATIONS, local_dict=_build_local_dict(normalized_value))
        params[name.strip()] = float(parsed_value)
    return params


def _extract_free_symbol_names(expr, mode: str) -> list[str]:
    reserved = PLOT_RESERVED[mode]
    return sorted(symbol.name for symbol in expr.free_symbols if symbol.name not in reserved)


def detect_cartesian_parameters(equation: str) -> list[str]:
    expr, _ = parse_cartesian_expression(equation)
    return _extract_free_symbol_names(expr, "cartesian")


def detect_parametric_parameters(x_expression: str, y_expression: str) -> list[str]:
    x_expr = _parse_sympy_expression(x_expression)
    y_expr = _parse_sympy_expression(y_expression)
    return sorted(set(_extract_free_symbol_names(x_expr, "parametric") + _extract_free_symbol_names(y_expr, "parametric")))


def detect_surface_parameters(expression: str) -> list[str]:
    expr, _ = parse_surface_expression(expression)
    return _extract_free_symbol_names(expr, "surface")


def parse_cartesian_expression(equation: str):
    if not equation.strip():
        raise ValueError("Enter an equation first.")
    normalized = equation.strip()
    if "=" in normalized:
        left, right = [side.strip() for side in normalized.split("=", 1)]
        if left.lower() in ("y", "f(x)", "f( x )", "g(x)", "h(x)"):
            expr = _parse_sympy_expression(right)
        elif right.lower() in ("y", "f(x)", "f( x )", "g(x)", "h(x)"):
            expr = _parse_sympy_expression(left)
        else:
            # Treat the right-hand side as the expression to plot
            expr = _parse_sympy_expression(right)
    else:
        expr = _parse_sympy_expression(normalized)
    return expr, normalized


def parse_surface_expression(expression: str):
    if not expression.strip():
        raise ValueError("Enter a surface equation first.")
    normalized = expression.strip()
    if "=" in normalized:
        left, right = [side.strip() for side in normalized.split("=", 1)]
        if left.lower() in ("z", "f(x,y)", "f(x, y)"):
            expr = _parse_sympy_expression(right)
        elif right.lower() in ("z", "f(x,y)", "f(x, y)"):
            expr = _parse_sympy_expression(left)
        else:
            expr = _parse_sympy_expression(right)
    else:
        expr = _parse_sympy_expression(normalized)
    return expr, normalized


def is_implicit_equation(equation: str) -> bool:
    """Return True if the equation has both x and y as free variables
    and cannot be reduced to an explicit ``y = f(x)`` form."""
    if not equation.strip():
        return False
    normalized = equation.strip()
    if "=" in normalized:
        left, right = [s.strip() for s in normalized.split("=", 1)]
        if left.lower() in ("y", "f(x)", "g(x)", "h(x)"):
            return False
        if right.lower() in ("y", "f(x)", "g(x)", "h(x)"):
            return False
    else:
        return False  # no = sign → treat as explicit f(x)
    # Check if both x and y appear
    try:
        left_expr = _parse_sympy_expression(left)
        right_expr = _parse_sympy_expression(right)
        combined = left_expr - right_expr
        names = {s.name for s in combined.free_symbols}
        return "x" in names and "y" in names
    except Exception:
        return False


def parse_implicit_expression(equation: str):
    """Parse ``LHS = RHS`` into ``LHS - RHS`` (implicit form F(x,y) = 0)."""
    if not equation.strip():
        raise ValueError("Enter an equation first.")
    normalized = equation.strip()
    if "=" not in normalized:
        raise ValueError("Implicit equations must contain '=', e.g. x^2 + y^2 = 1")
    left, right = [s.strip() for s in normalized.split("=", 1)]
    left_expr = _parse_sympy_expression(left)
    right_expr = _parse_sympy_expression(right)
    return left_expr - right_expr, normalized


def detect_implicit_parameters(equation: str) -> list[str]:
    expr, _ = parse_implicit_expression(equation)
    return _extract_free_symbol_names(expr, "implicit")


def build_implicit_curve(
    equation: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    parameters: dict[str, float] | None = None,
    label: str | None = None,
    samples: int = 400,
) -> dict[str, Any]:
    """Build contour data for an implicit equation F(x,y) = 0.

    Returns a dict with grid data suitable for Plotly ``go.Contour``
    and a ``desmos_latex`` field for Desmos rendering.
    """
    expr, normalized = parse_implicit_expression(equation)
    substituted, parameter_values = _substitute_parameters(expr, parameters, "implicit")

    x_sym = Symbol("x")
    y_sym = Symbol("y")
    func = lambdify((x_sym, y_sym), substituted, modules=["numpy"])

    xs = np.linspace(x_min, x_max, samples)
    ys = np.linspace(y_min, y_max, samples)
    grid_x, grid_y = np.meshgrid(xs, ys)
    try:
        grid_z = np.asarray(func(grid_x, grid_y), dtype=float)
    except Exception as exc:
        raise ValueError(f"Could not evaluate the implicit equation: {exc}") from exc

    if grid_z.shape == ():
        grid_z = np.full_like(grid_x, float(grid_z))
    grid_z = np.where(np.isfinite(grid_z), grid_z, np.nan)

    # Build Desmos-compatible latex: LHS = RHS kept as-is
    left_str, right_str = [s.strip() for s in normalized.split("=", 1)]
    desmos_latex = f"{latex(_parse_sympy_expression(left_str))}={latex(_parse_sympy_expression(right_str))}"

    return {
        "label": label or normalized,
        "kind": "implicit",
        "expression": normalized,
        "parameters": parameter_values,
        "x_grid": grid_x.tolist(),
        "y_grid": grid_y.tolist(),
        "z_grid": grid_z.tolist(),
        "metadata": {
            "desmos_latex": desmos_latex,
        },
    }


def _substitute_parameters(expr, parameters: dict[str, float] | None, mode: str):
    parameter_values = parameters or {}
    unresolved = [name for name in _extract_free_symbol_names(expr, mode) if name not in parameter_values]
    if unresolved:
        raise ValueError(f"Missing parameter values for: {', '.join(unresolved)}")
    return expr.subs(parameter_values), parameter_values


def _clean_line_data(x_values, y_values):
    cleaned_x: list[float | None] = []
    cleaned_y: list[float | None] = []
    for x_val, y_val in zip(x_values.tolist(), y_values.tolist()):
        if np.isfinite(x_val) and np.isfinite(y_val):
            cleaned_x.append(float(x_val))
            cleaned_y.append(float(y_val))
        else:
            cleaned_x.append(None)
            cleaned_y.append(None)
    return cleaned_x, cleaned_y


def build_cartesian_curve(
    equation: str,
    x_min: float,
    x_max: float,
    parameters: dict[str, float] | None = None,
    label: str | None = None,
    samples: int = 800,
    role: str = "base",
) -> CurveData:
    expr, normalized = parse_cartesian_expression(equation)
    substituted, parameter_values = _substitute_parameters(expr, parameters, "cartesian")

    x_symbol = Symbol("x")
    function = lambdify(x_symbol, substituted, modules=["numpy"])
    x_values = np.linspace(x_min, x_max, samples)
    try:
        y_values = np.asarray(function(x_values), dtype=float)
    except Exception as exc:
        raise ValueError(f"Could not evaluate the equation: {exc}") from exc

    if y_values.shape == ():
        y_values = np.full_like(x_values, float(y_values))

    cleaned_x, cleaned_y = _clean_line_data(x_values, y_values)
    return CurveData(
        label=label or normalized,
        kind="cartesian",
        x_values=cleaned_x,
        y_values=cleaned_y,
        expression=normalized,
        parameters=parameter_values,
        metadata={
            "expr": str(simplify(substituted)),
            "raw_equation": normalized,
            "role": role,
            "desmos_latex": f"y={latex(simplify(substituted))}",
        },
    )


def build_parametric_curve(
    x_expression: str,
    y_expression: str,
    t_min: float,
    t_max: float,
    parameters: dict[str, float] | None = None,
    label: str | None = None,
    samples: int = 800,
) -> CurveData:
    if not x_expression.strip() or not y_expression.strip():
        raise ValueError("Enter both x(t) and y(t) expressions.")

    x_expr = _parse_sympy_expression(x_expression)
    y_expr = _parse_sympy_expression(y_expression)
    x_sub, parameter_values = _substitute_parameters(x_expr, parameters, "parametric")
    y_sub, _ = _substitute_parameters(y_expr, parameter_values, "parametric")

    t_symbol = Symbol("t")
    x_func = lambdify(t_symbol, x_sub, modules=["numpy"])
    y_func = lambdify(t_symbol, y_sub, modules=["numpy"])
    t_values = np.linspace(t_min, t_max, samples)
    try:
        x_values = np.asarray(x_func(t_values), dtype=float)
        y_values = np.asarray(y_func(t_values), dtype=float)
    except Exception as exc:
        raise ValueError(f"Could not evaluate the parametric curve: {exc}") from exc

    if x_values.shape == ():
        x_values = np.full_like(t_values, float(x_values))
    if y_values.shape == ():
        y_values = np.full_like(t_values, float(y_values))

    cleaned_x, cleaned_y = _clean_line_data(x_values, y_values)
    expression = f"x(t) = {x_expression}; y(t) = {y_expression}"
    return CurveData(
        label=label or expression,
        kind="parametric",
        x_values=cleaned_x,
        y_values=cleaned_y,
        expression=expression,
        parameters=parameter_values,
        metadata={
            "x_expr": str(simplify(x_sub)),
            "y_expr": str(simplify(y_sub)),
            "desmos_latex": f"({latex(simplify(x_sub))},{latex(simplify(y_sub))})",
        },
    )


def build_derivative_curve(
    equation: str,
    x_min: float,
    x_max: float,
    parameters: dict[str, float] | None = None,
    label: str | None = None,
    samples: int = 800,
) -> CurveData:
    expr, normalized = parse_cartesian_expression(equation)
    derivative_expr = diff(expr, Symbol("x"))
    return build_cartesian_curve(
        equation=f"y = {str(simplify(derivative_expr))}",
        x_min=x_min,
        x_max=x_max,
        parameters=parameters,
        label=label or f"d/dx {normalized}",
        samples=samples,
        role="derivative",
    )


def build_tangent_line_curve(
    equation: str,
    x0: float,
    x_min: float,
    x_max: float,
    parameters: dict[str, float] | None = None,
    label: str | None = None,
    samples: int = 800,
) -> tuple[CurveData, dict[str, float]]:
    expr, normalized = parse_cartesian_expression(equation)
    substituted, parameter_values = _substitute_parameters(expr, parameters, "cartesian")
    x_symbol = Symbol("x")
    derivative_expr = diff(substituted, x_symbol)
    y0 = float(substituted.subs({x_symbol: x0}))
    slope = float(derivative_expr.subs({x_symbol: x0}))
    tangent_expr = simplify(slope * (x_symbol - x0) + y0)
    curve = build_cartesian_curve(
        equation=f"y = {str(tangent_expr)}",
        x_min=x_min,
        x_max=x_max,
        parameters={},
        label=label or f"Tangent at x={x0:g}",
        samples=samples,
        role="tangent",
    )
    curve.metadata.update({"point_x": x0, "point_y": y0, "slope": slope, "base_equation": normalized})
    return curve, {"x": x0, "y": y0, "slope": slope}


def build_integral_region(
    equation: str,
    x_start: float,
    x_end: float,
    parameters: dict[str, float] | None = None,
    samples: int = 400,
) -> dict[str, Any]:
    expr, normalized = parse_cartesian_expression(equation)
    substituted, parameter_values = _substitute_parameters(expr, parameters, "cartesian")
    x_symbol = Symbol("x")
    function = lambdify(x_symbol, substituted, modules=["numpy"])
    x_values = np.linspace(x_start, x_end, samples)
    try:
        y_values = np.asarray(function(x_values), dtype=float)
    except Exception as exc:
        raise ValueError(f"Could not evaluate the integral region: {exc}") from exc

    finite_mask = np.isfinite(y_values)
    x_clean = x_values[finite_mask]
    y_clean = y_values[finite_mask]
    if len(x_clean) < 2:
        raise ValueError("Not enough valid points to shade the selected interval.")

    area = _numeric_integral(x_clean.tolist(), y_clean.tolist())
    return {
        "label": f"Area under {normalized} from {x_start:g} to {x_end:g}",
        "equation": normalized,
        "x_fill": list(x_clean) + list(x_clean[::-1]),
        "y_fill": list(y_clean) + [0.0 for _ in range(len(y_clean))],
        "area": area,
        "x_start": x_start,
        "x_end": x_end,
        "parameters": parameter_values,
    }


def build_surface_data(
    expression: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    parameters: dict[str, float] | None = None,
    label: str | None = None,
    samples: int = 60,
) -> dict[str, Any]:
    expr, normalized = parse_surface_expression(expression)
    substituted, parameter_values = _substitute_parameters(expr, parameters, "surface")

    x_symbol = Symbol("x")
    y_symbol = Symbol("y")
    function = lambdify((x_symbol, y_symbol), substituted, modules=["numpy"])

    x_values = np.linspace(x_min, x_max, samples)
    y_values = np.linspace(y_min, y_max, samples)
    grid_x, grid_y = np.meshgrid(x_values, y_values)
    try:
        grid_z = np.asarray(function(grid_x, grid_y), dtype=float)
    except Exception as exc:
        raise ValueError(f"Could not evaluate the surface: {exc}") from exc

    if grid_z.shape == ():
        grid_z = np.full_like(grid_x, float(grid_z))
    grid_z = np.where(np.isfinite(grid_z), grid_z, np.nan)

    return {
        "label": label or normalized,
        "expression": normalized,
        "parameters": parameter_values,
        "x_grid": grid_x.tolist(),
        "y_grid": grid_y.tolist(),
        "z_grid": grid_z.tolist(),
    }


def curve_to_dict(curve: CurveData) -> dict[str, Any]:
    return {
        "label": curve.label,
        "kind": curve.kind,
        "x_values": curve.x_values,
        "y_values": curve.y_values,
        "expression": curve.expression,
        "parameters": curve.parameters,
        "metadata": curve.metadata,
    }


def curve_to_desmos_expression(curve: dict[str, Any], expression_id: str) -> dict[str, str]:
    latex_expr = curve.get("metadata", {}).get("desmos_latex")
    if not latex_expr:
        raise ValueError("Curve does not contain a Desmos-compatible expression.")
    return {
        "id": expression_id,
        "latex": latex_expr,
        "label": curve.get("label", expression_id),
        "showLabel": True,
    }
