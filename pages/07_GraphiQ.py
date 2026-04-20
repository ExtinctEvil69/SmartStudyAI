"""GraphiQ — advanced interactive equation graphing and AI visualization support."""

import json

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from core import gemma_engine
from core.math_graph_engine import (
    build_cartesian_curve,
    build_derivative_curve,
    build_implicit_curve,
    build_integral_region,
    build_parametric_curve,
    build_surface_data,
    build_tangent_line_curve,
    curve_to_desmos_expression,
    curve_to_dict,
    detect_cartesian_parameters,
    detect_implicit_parameters,
    detect_parametric_parameters,
    detect_surface_parameters,
    is_implicit_equation,
)
from core.obsidian_export import export_study_guide
from core.page_state import ensure_state, set_result
from core.sidebar import render_sidebar
from core.ui_components import inject_global_css, page_header


PHYSICS_TEMPLATES = {
    "Simple Harmonic Motion": {
        "context": "Comparing phase shifts and amplitude changes in simple harmonic motion.",
        "mode": "Cartesian",
        "equation": "y = A*sin(omega*x + phi)",
        "label": "SHM",
        "x_range": (0.0, 12.0),
        "y_range": (-3.0, 3.0),
        "params": {"A": 1.0, "omega": 1.0, "phi": 0.0},
    },
    "Damped Oscillation": {
        "context": "Useful for advanced mechanics and signal damping comparisons.",
        "mode": "Cartesian",
        "equation": "y = A*exp(-beta*x)*cos(omega*x)",
        "label": "Damped Oscillation",
        "x_range": (0.0, 20.0),
        "y_range": (-2.5, 2.5),
        "params": {"A": 2.0, "beta": 0.15, "omega": 2.0},
    },
    "Projectile Trajectory": {
        "context": "Compare trajectories under different initial velocities or launch angles.",
        "mode": "Cartesian",
        "equation": "y = y0 + x*tan(theta) - g*x^2/(2*v0^2*cos(theta)^2)",
        "label": "Projectile",
        "x_range": (0.0, 80.0),
        "y_range": (0.0, 40.0),
        "params": {"y0": 0.0, "theta": 0.785, "g": 9.81, "v0": 25.0},
    },
    "Wave Interference": {
        "context": "Compare constructive and destructive interference patterns in wave physics.",
        "mode": "Cartesian",
        "equation": "y = A*sin(k1*x) + B*sin(k2*x)",
        "label": "Wave Interference",
        "x_range": (0.0, 20.0),
        "y_range": (-4.0, 4.0),
        "params": {"A": 1.0, "B": 1.0, "k1": 1.0, "k2": 1.4},
    },
    "Unit Circle": {
        "context": "Parametric comparison for trigonometry and rotational motion.",
        "mode": "Parametric",
        "x_expression": "a*cos(t)",
        "y_expression": "b*sin(t)",
        "label": "Ellipse / Circle",
        "x_range": (0.0, 6.283),
        "y_range": (-3.0, 3.0),
        "params": {"a": 1.0, "b": 1.0},
    },
    "3D Wave Surface": {
        "context": "Surface view for advanced physics, PDE intuition, and wave motion.",
        "surface": "z = A*sin(kx*x)*cos(ky*y)",
        "label": "Wave Surface",
        "surface_x": (-6.0, 6.0),
        "surface_y": (-6.0, 6.0),
        "params": {"A": 1.0, "kx": 1.0, "ky": 1.0},
    },
}


def _render_parameter_sliders(param_names: list[str], prefix: str) -> dict[str, float]:
    values: dict[str, float] = {}
    if not param_names:
        return values
    slider_cols = st.columns(min(3, len(param_names)))
    for index, name in enumerate(param_names):
        with slider_cols[index % len(slider_cols)]:
            key = f"{prefix}_{name}_value"
            if key not in st.session_state:
                st.session_state[key] = 1.0
            values[name] = st.slider(name, -20.0, 20.0, float(st.session_state[key]), 0.1, key=key)
    return values


def _load_template(template_name: str) -> None:
    template = PHYSICS_TEMPLATES[template_name]
    if "mode" in template:
        st.session_state.graphiq_mode = template["mode"]
        st.session_state.graphiq_context = template["context"]
        st.session_state.graphiq_2d_label = template["label"]
        st.session_state.graphiq_x_min, st.session_state.graphiq_x_max = template["x_range"]
        st.session_state.graphiq_y_min, st.session_state.graphiq_y_max = template["y_range"]
        if template["mode"] == "Cartesian":
            st.session_state.graphiq_equation = template["equation"]
        else:
            st.session_state.graphiq_x_expression = template["x_expression"]
            st.session_state.graphiq_y_expression = template["y_expression"]
        for name, value in template["params"].items():
            st.session_state[f"graphiq_2d_{name}_value"] = float(value)
    else:
        st.session_state.graphiq_context = template["context"]
        st.session_state.graphiq_surface_expression = template["surface"]
        st.session_state.graphiq_surface_label = template["label"]
        st.session_state.graphiq_surface_x_min, st.session_state.graphiq_surface_x_max = template["surface_x"]
        st.session_state.graphiq_surface_y_min, st.session_state.graphiq_surface_y_max = template["surface_y"]
        for name, value in template["params"].items():
            st.session_state[f"graphiq_3d_{name}_value"] = float(value)


def _build_desmos_html(curves: list[dict], x_bounds: tuple[float, float], y_bounds: tuple[float, float]) -> str:
    expressions = []
    for index, curve in enumerate(curves, start=1):
        try:
            # curve_to_desmos_expression works for explicit curves with desmos_latex
            expressions.append(curve_to_desmos_expression(curve, f"curve{index}"))
        except Exception:
            # For implicit curves, the metadata has desmos_latex set directly
            desmos_latex = curve.get("metadata", {}).get("desmos_latex")
            if desmos_latex:
                expressions.append({
                    "id": f"curve{index}",
                    "latex": desmos_latex,
                    "label": curve.get("label", f"curve{index}"),
                    "showLabel": True,
                })
            continue

    expressions_json = json.dumps(expressions)
    left, right = x_bounds
    bottom, top = y_bounds
    return f"""
    <div id="desmos-calculator" style="width:100%;height:520px;"></div>
    <script src="https://www.desmos.com/api/v1.11/calculator.js?apiKey=desmos"></script>
    <script>
      const elt = document.getElementById('desmos-calculator');
      const calculator = Desmos.GraphingCalculator(elt, {{expressionsCollapsed:false, settingsMenu:false}});
      calculator.setMathBounds({{left:{left}, right:{right}, bottom:{bottom}, top:{top}}});
      const expressions = {expressions_json};
      expressions.forEach(expr => calculator.setExpression(expr));
    </script>
    """


st.set_page_config(page_title="GraphiQ", page_icon="📊", layout="wide")
inject_global_css()
model_config = render_sidebar("graphiq")

page_header("📊", "GraphiQ — Advanced Graphing + AI Visualization", "Use Desmos-powered interactive 2D math graphs, Plotly-powered 3D surfaces, and persistent graph memory for advanced comparison workflows.", badge="Graphing")

ensure_state(
    graphiq_curves=[],
    graphiq_implicit_curves=[],
    graphiq_regions=[],
    graphiq_surfaces=[],
    graphiq_context="",
    graphiq_plot_title="Advanced Graph Comparison",
    graphiq_x_label="x",
    graphiq_y_label="y",
    graphiq_x_min=-10.0,
    graphiq_x_max=10.0,
    graphiq_y_min=-10.0,
    graphiq_y_max=10.0,
    graphiq_mode="Cartesian",
    graphiq_equation="y = sin(x)",
    graphiq_implicit_equation="(x^2 + y^2 - 1)^3 - x^2 * y^3 = 0",
    graphiq_2d_label="",
    graphiq_x_expression="cos(t)",
    graphiq_y_expression="sin(t)",
    graphiq_surface_expression="z = sin(x) * cos(y)",
    graphiq_surface_label="Surface 1",
    graphiq_surface_x_min=-5.0,
    graphiq_surface_x_max=5.0,
    graphiq_surface_y_min=-5.0,
    graphiq_surface_y_max=5.0,
    graphiq_result="",
    graphiq_code="",
    graphiq_request="",
)

template_col, helper_col = st.columns([2, 3])
with template_col:
    template_name = st.selectbox("Physics / Math Template", ["None"] + list(PHYSICS_TEMPLATES.keys()))
with helper_col:
    if st.button("Load Template") and template_name != "None":
        _load_template(template_name)
        st.success(f"Loaded template: {template_name}")

with st.expander("Advanced Examples", expanded=False):
    st.markdown(
        "- `y = exp(-0.2*x)*cos(3*x)`\n"
        "- `y = log(x^2 + 1)`\n"
        "- `y = sqrt(abs(x)) * sin(2*x)`\n"
        "- `y = (x^3 - 3*x)/(x^2 + 1)`\n"
        "- Parametric: `x(t)=cos(3*t)`, `y(t)=sin(4*t)`\n"
        "- Surface: `z = sin(x^2 + y^2)/(x^2 + y^2 + 1)`"
    )

tab_2d, tab_3d, tab_ai = st.tabs(["2D Equation Lab", "3D Surface Lab", "AI Visualization Code"])

with tab_2d:
    st.subheader("2D Equation Lab")
    st.markdown("Add curves one by one. Graph memory stays alive until you reset it, so you can compare shifts, perturbations, derivatives, and tangent lines over time.")

    context = st.text_area("Context / notes", value=st.session_state.graphiq_context, height=100)
    if context != st.session_state.graphiq_context:
        set_result("graphiq_context", context)

    meta_col1, meta_col2, meta_col3 = st.columns(3)
    with meta_col1:
        plot_title = st.text_input("Plot title", value=st.session_state.graphiq_plot_title)
    with meta_col2:
        x_label = st.text_input("X axis label", value=st.session_state.graphiq_x_label)
    with meta_col3:
        y_label = st.text_input("Y axis label", value=st.session_state.graphiq_y_label)
    set_result("graphiq_plot_title", plot_title)
    set_result("graphiq_x_label", x_label)
    set_result("graphiq_y_label", y_label)

    _mode_options = ["Cartesian", "Implicit", "Parametric"]
    _mode_index = _mode_options.index(st.session_state.graphiq_mode) if st.session_state.graphiq_mode in _mode_options else 0
    setting_col1, setting_col2, setting_col3, setting_col4, setting_col5 = st.columns(5)
    with setting_col1:
        mode = st.radio("Mode", _mode_options, index=_mode_index)
    with setting_col2:
        x_min = st.number_input("X min", value=float(st.session_state.graphiq_x_min), step=1.0)
    with setting_col3:
        x_max = st.number_input("X max", value=float(st.session_state.graphiq_x_max), step=1.0)
    with setting_col4:
        y_min = st.number_input("Y min", value=float(st.session_state.graphiq_y_min), step=1.0)
    with setting_col5:
        y_max = st.number_input("Y max", value=float(st.session_state.graphiq_y_max), step=1.0)
    set_result("graphiq_mode", mode)
    set_result("graphiq_x_min", x_min)
    set_result("graphiq_x_max", x_max)
    set_result("graphiq_y_min", y_min)
    set_result("graphiq_y_max", y_max)

    samples = st.slider("2D resolution", 200, 2000, 800, step=100)
    curve_label = st.text_input("Curve label", value=st.session_state.graphiq_2d_label, placeholder="Optional custom label")
    set_result("graphiq_2d_label", curve_label)

    if mode == "Cartesian":
        equation = st.text_input("Equation", value=st.session_state.graphiq_equation, placeholder="e.g. y = exp(-0.2*x)*cos(2*x)")
        set_result("graphiq_equation", equation)

        # Auto-detect: if user typed an implicit equation in Cartesian mode, switch
        if equation.strip() and is_implicit_equation(equation):
            st.info("Detected implicit equation (both x and y). Switching to Implicit mode — click **Add Curve** to plot.")
            set_result("graphiq_mode", "Implicit")
            set_result("graphiq_implicit_equation", equation)
            mode = "Implicit"

        if mode == "Cartesian":
            param_names = detect_cartesian_parameters(equation) if equation.strip() else []
            parameters = _render_parameter_sliders(param_names, "graphiq_2d")

    if mode == "Implicit":
        if 'equation' not in dir() or not is_implicit_equation(equation if 'equation' in dir() else ""):
            equation = st.text_input(
                "Implicit equation",
                value=st.session_state.graphiq_implicit_equation,
                placeholder="e.g. (x^2 + y^2 - 1)^3 - x^2 * y^3 = 0",
            )
            set_result("graphiq_implicit_equation", equation)
        param_names = detect_implicit_parameters(equation) if equation.strip() else []
        parameters = _render_parameter_sliders(param_names, "graphiq_2d")

    elif mode == "Parametric":
        expr_col1, expr_col2 = st.columns(2)
        with expr_col1:
            x_expression = st.text_input("x(t)", value=st.session_state.graphiq_x_expression)
        with expr_col2:
            y_expression = st.text_input("y(t)", value=st.session_state.graphiq_y_expression)
        set_result("graphiq_x_expression", x_expression)
        set_result("graphiq_y_expression", y_expression)
        param_names = detect_parametric_parameters(x_expression, y_expression) if x_expression.strip() and y_expression.strip() else []
        parameters = _render_parameter_sliders(param_names, "graphiq_2d")

    action_col1, action_col2, action_col3 = st.columns(3)
    if action_col1.button("Add Curve", type="primary"):
        try:
            if mode == "Implicit":
                implicit_data = build_implicit_curve(
                    equation, x_min, x_max, y_min, y_max,
                    parameters=parameters, label=curve_label or None, samples=samples,
                )
                st.session_state.graphiq_implicit_curves.append(implicit_data)
                st.success(f"Added implicit curve: {implicit_data['label']}")
            elif mode == "Cartesian":
                curve = build_cartesian_curve(equation, x_min, x_max, parameters=parameters, label=curve_label or None, samples=samples)
                st.session_state.graphiq_curves.append(curve_to_dict(curve))
                st.success(f"Added curve: {curve.label}")
            else:
                curve = build_parametric_curve(
                    x_expression,
                    y_expression,
                    x_min,
                    x_max,
                    parameters=parameters,
                    label=curve_label or None,
                    samples=samples,
                )
                st.session_state.graphiq_curves.append(curve_to_dict(curve))
                st.success(f"Added curve: {curve.label}")
        except Exception as exc:
            st.error(str(exc))

    if action_col2.button("Remove Last Curve"):
        if st.session_state.graphiq_implicit_curves:
            removed = st.session_state.graphiq_implicit_curves.pop()
            st.info(f"Removed: {removed['label']}")
        elif st.session_state.graphiq_curves:
            removed = st.session_state.graphiq_curves.pop()
            st.info(f"Removed: {removed['label']}")
        elif st.session_state.graphiq_regions:
            removed = st.session_state.graphiq_regions.pop()
            st.info(f"Removed shaded region: {removed['label']}")

    if action_col3.button("Reset 2D Lab"):
        st.session_state.graphiq_curves = []
        st.session_state.graphiq_implicit_curves = []
        st.session_state.graphiq_regions = []
        st.success("Cleared all curves and shaded regions.")

    if st.session_state.graphiq_curves:
        cartesian_curves = [curve for curve in st.session_state.graphiq_curves if curve["kind"] == "cartesian"]
        if cartesian_curves:
            st.divider()
            st.subheader("Analysis Tools")
            selected_label = st.selectbox("Target curve", [curve["label"] for curve in cartesian_curves])
            selected_curve = next(curve for curve in cartesian_curves if curve["label"] == selected_label)

            analysis_col1, analysis_col2, analysis_col3 = st.columns(3)
            if analysis_col1.button("Add Derivative Curve"):
                derivative = build_derivative_curve(
                    selected_curve["metadata"]["raw_equation"],
                    x_min,
                    x_max,
                    parameters=selected_curve["parameters"],
                    label=f"Derivative of {selected_curve['label']}",
                    samples=samples,
                )
                st.session_state.graphiq_curves.append(curve_to_dict(derivative))
                st.success("Added derivative curve.")

            with analysis_col2:
                tangent_x = st.number_input("Tangent at x", value=0.0, step=0.5)
                if st.button("Add Tangent Line"):
                    tangent_curve, point = build_tangent_line_curve(
                        selected_curve["metadata"]["raw_equation"],
                        tangent_x,
                        x_min,
                        x_max,
                        parameters=selected_curve["parameters"],
                        label=f"Tangent to {selected_curve['label']}",
                        samples=samples,
                    )
                    st.session_state.graphiq_curves.append(curve_to_dict(tangent_curve))
                    st.success(f"Added tangent line at ({point['x']:.2f}, {point['y']:.2f}).")

            with analysis_col3:
                area_start = st.number_input("Integral start", value=-1.0, step=0.5)
                area_end = st.number_input("Integral end", value=1.0, step=0.5)
                if st.button("Shade Integral Area"):
                    region = build_integral_region(
                        selected_curve["metadata"]["raw_equation"],
                        area_start,
                        area_end,
                        parameters=selected_curve["parameters"],
                    )
                    st.session_state.graphiq_regions.append(region)
                    st.success(f"Added shaded region. Signed area = {region['area']:.4f}")

    fig = go.Figure()
    # Implicit curves rendered as zero-level contour lines
    for impl in st.session_state.graphiq_implicit_curves:
        fig.add_trace(
            go.Contour(
                x=impl["x_grid"][0],  # first row = x values
                y=[row[0] for row in impl["y_grid"]],  # first column = y values
                z=impl["z_grid"],
                contours=dict(start=0, end=0, size=1, coloring="none"),
                line=dict(width=3),
                showscale=False,
                name=impl["label"],
            )
        )
    # Explicit curves
    for curve in st.session_state.graphiq_curves:
        fig.add_trace(
            go.Scatter(
                x=curve["x_values"],
                y=curve["y_values"],
                mode="lines",
                name=curve["label"],
                hovertemplate="x=%{x}<br>y=%{y}<extra>%{fullData.name}</extra>",
            )
        )
        point_x = curve.get("metadata", {}).get("point_x")
        point_y = curve.get("metadata", {}).get("point_y")
        if point_x is not None and point_y is not None:
            fig.add_trace(
                go.Scatter(
                    x=[point_x],
                    y=[point_y],
                    mode="markers",
                    name=f"Point on {curve['label']}",
                    marker=dict(size=9),
                    showlegend=False,
                )
            )
    for region in st.session_state.graphiq_regions:
        fig.add_trace(
            go.Scatter(
                x=region["x_fill"],
                y=region["y_fill"],
                fill="toself",
                mode="lines",
                name=f"{region['label']} (area={region['area']:.3f})",
                line=dict(width=1),
                opacity=0.25,
            )
        )

    fig.update_layout(
        title=st.session_state.graphiq_plot_title,
        xaxis_title=st.session_state.graphiq_x_label,
        yaxis_title=st.session_state.graphiq_y_label,
        xaxis=dict(range=[x_min, x_max], zeroline=True, showgrid=True),
        yaxis=dict(range=[y_min, y_max], zeroline=True, showgrid=True),
        template="plotly_white",
        dragmode="pan",
        legend_title="Curves / Regions",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Plotly handles the numerical overlays, shaded integrals, 3D surfaces, and point inspection.")

    _all_curves = st.session_state.graphiq_curves + st.session_state.graphiq_implicit_curves
    if _all_curves:
        st.subheader("Desmos Interactive View")
        components.html(_build_desmos_html(_all_curves, (x_min, x_max), (y_min, y_max)), height=540, scrolling=False)
        st.caption("Desmos is the equation-native interactive layer for panning, zooming, and clean mathematical rendering.")

        with st.expander("Graph Memory", expanded=True):
            for index, curve in enumerate(_all_curves, start=1):
                st.markdown(f"**{index}. {curve['label']}**")
                st.caption(curve["expression"])
                if curve["parameters"]:
                    st.caption(f"Parameters: {curve['parameters']}")
            for region in st.session_state.graphiq_regions:
                st.markdown(f"**Region:** {region['label']}")
                st.caption(f"Signed area = {region['area']:.4f}")

        if st.button("Export 2D Graph Notes to Obsidian"):
            curve_lines = [f"- {curve['label']}: `{curve['expression']}`" for curve in _all_curves]
            region_lines = [f"- {region['label']}: signed area = {region['area']:.4f}" for region in st.session_state.graphiq_regions]
            notes = [
                "## Context",
                st.session_state.graphiq_context or "No context provided.",
                "",
                "## Curves",
                "\n".join(curve_lines) if curve_lines else "None",
                "",
                "## Regions",
                "\n".join(region_lines) if region_lines else "None",
                "",
                "## Axes",
                f"- x-axis: {st.session_state.graphiq_x_label} [{x_min}, {x_max}]",
                f"- y-axis: {st.session_state.graphiq_y_label} [{y_min}, {y_max}]",
            ]
            path = export_study_guide(
                f"GraphiQ - {st.session_state.graphiq_plot_title[:40]}",
                "\n".join(notes),
                tags=["graphiq", "equation-plotting"],
            )
            st.success(f"Exported to: {path}")

with tab_3d:
    st.subheader("3D Surface Lab")
    st.markdown("Use Plotly for 3D surfaces and advanced scientific graphing. Add multiple surfaces to compare how the geometry changes.")

    surface_expr = st.text_input("Surface equation", value=st.session_state.graphiq_surface_expression, placeholder="e.g. z = sin(x)*cos(y)")
    surface_label = st.text_input("Surface label", value=st.session_state.graphiq_surface_label)
    set_result("graphiq_surface_expression", surface_expr)
    set_result("graphiq_surface_label", surface_label)

    surface_col1, surface_col2, surface_col3, surface_col4 = st.columns(4)
    with surface_col1:
        sx_min = st.number_input("3D X min", value=float(st.session_state.graphiq_surface_x_min), step=1.0)
    with surface_col2:
        sx_max = st.number_input("3D X max", value=float(st.session_state.graphiq_surface_x_max), step=1.0)
    with surface_col3:
        sy_min = st.number_input("3D Y min", value=float(st.session_state.graphiq_surface_y_min), step=1.0)
    with surface_col4:
        sy_max = st.number_input("3D Y max", value=float(st.session_state.graphiq_surface_y_max), step=1.0)
    set_result("graphiq_surface_x_min", sx_min)
    set_result("graphiq_surface_x_max", sx_max)
    set_result("graphiq_surface_y_min", sy_min)
    set_result("graphiq_surface_y_max", sy_max)

    surface_samples = st.slider("3D resolution", 20, 120, 50, step=10)
    surface_param_names = detect_surface_parameters(surface_expr) if surface_expr.strip() else []
    surface_params = _render_parameter_sliders(surface_param_names, "graphiq_3d")

    surface_action1, surface_action2, surface_action3 = st.columns(3)
    if surface_action1.button("Add Surface", type="primary"):
        try:
            surface = build_surface_data(
                surface_expr,
                sx_min,
                sx_max,
                sy_min,
                sy_max,
                parameters=surface_params,
                label=surface_label or None,
                samples=surface_samples,
            )
            st.session_state.graphiq_surfaces.append(surface)
            st.success(f"Added surface: {surface['label']}")
        except Exception as exc:
            st.error(str(exc))

    if surface_action2.button("Remove Last Surface") and st.session_state.graphiq_surfaces:
        removed = st.session_state.graphiq_surfaces.pop()
        st.info(f"Removed surface: {removed['label']}")

    if surface_action3.button("Reset 3D Lab"):
        st.session_state.graphiq_surfaces = []
        st.success("Cleared all surfaces.")

    surface_fig = go.Figure()
    for index, surface in enumerate(st.session_state.graphiq_surfaces, start=1):
        surface_fig.add_trace(
            go.Surface(
                x=surface["x_grid"],
                y=surface["y_grid"],
                z=surface["z_grid"],
                name=surface["label"],
                opacity=max(0.35, 0.85 - (index - 1) * 0.15),
                showscale=index == 1,
            )
        )
    surface_fig.update_layout(
        title="3D Surface Comparison",
        scene=dict(xaxis_title="x", yaxis_title="y", zaxis_title="z"),
        margin=dict(l=10, r=10, t=50, b=10),
    )
    st.plotly_chart(surface_fig, use_container_width=True)

    if st.session_state.graphiq_surfaces:
        with st.expander("Surface Memory", expanded=True):
            for surface in st.session_state.graphiq_surfaces:
                st.markdown(f"**{surface['label']}**")
                st.caption(surface["expression"])
                if surface["parameters"]:
                    st.caption(f"Parameters: {surface['parameters']}")

with tab_ai:
    st.subheader("AI Visualization Code")
    st.caption("Use this when you want generated Python plotting code from a dataset description rather than direct equation plotting.")

    col1, col2 = st.columns([2, 1])
    with col1:
        data_description = st.text_area(
            "Describe your data and the visualization you want",
            height=150,
            placeholder="e.g. I have a CSV with columns: year, revenue, profit. Create a dual-axis line chart showing revenue and profit trends over time.",
        )
        sample_data = st.text_area(
            "Paste sample data (optional — CSV, JSON, or table)",
            height=120,
            placeholder="year,revenue,profit\n2020,100,20\n2021,150,35\n2022,200,50",
        )
    with col2:
        viz_library = st.selectbox("Library", ["matplotlib + seaborn", "plotly", "altair"])
        chart_type = st.selectbox("Chart type", [
            "Auto-detect", "Line chart", "Bar chart", "Scatter plot", "Histogram",
            "Box plot", "Heatmap", "Pie chart", "Area chart", "Violin plot",
        ])
        style = st.selectbox("Style", ["Publication-ready", "Minimal", "Dark theme", "Colorful"])

    if st.button("Generate Visualization Code", type="primary") and data_description.strip():
        lib_instructions = {
            "matplotlib + seaborn": "Use matplotlib and seaborn. Import both. Use seaborn's styling with sns.set_theme().",
            "plotly": "Use plotly.express or plotly.graph_objects. Make it interactive.",
            "altair": "Use the Altair library for declarative visualization.",
        }
        style_instructions = {
            "Publication-ready": "Use clean fonts, proper axis labels, title, legend, and gridlines. Suitable for academic papers.",
            "Minimal": "Minimalist design — remove unnecessary elements, use whitespace effectively.",
            "Dark theme": "Use a dark background theme with bright, contrasting colors.",
            "Colorful": "Use a vibrant, distinct color palette that's visually engaging.",
        }

        prompt = f"""Generate a complete, runnable Python visualization script.

**Data Description:** {data_description}
{f'**Sample Data:**{chr(10)}{sample_data}' if sample_data else ''}
{f'**Chart Type:** {chart_type}' if chart_type != 'Auto-detect' else ''}

**Requirements:**
- {lib_instructions[viz_library]}
- {style_instructions[style]}
- Include sample/dummy data if no real data is provided
- Add proper axis labels, title, and legend
- Include comments explaining each section
- The script should be copy-paste runnable
- Use plt.show() at the end (for matplotlib) or fig.show() (for plotly)

Output ONLY the Python code in a code block. No explanation before or after."""

        config = gemma_engine.GemmaConfig(model=model_config.model, temperature=0.3, max_tokens=4096)
        config.system_prompt = "You are an expert data visualization engineer. Generate clean, well-commented Python visualization code."
        placeholder = st.empty()
        with st.spinner("Generating visualization code..."):
            result = gemma_engine.generate(prompt, config, stream_callback=lambda t: placeholder.markdown(t))
        placeholder.markdown(result)

        import re

        code_match = re.search(r"```python\s*\n(.*?)```", result, re.DOTALL)
        code = code_match.group(1) if code_match else result
        set_result("graphiq_result", result)
        set_result("graphiq_code", code)
        set_result("graphiq_request", data_description)

    if st.session_state.graphiq_code:
        st.divider()
        st.subheader("Generated Code")
        st.code(st.session_state.graphiq_code, language="python")
        export_col, copy_col = st.columns(2)
        if copy_col.button("Copy Code"):
            st.code(st.session_state.graphiq_code, language="python")
            st.info("Code displayed above — use Ctrl+A, Ctrl+C to copy")
        if export_col.button("Export AI Visualization Notes"):
            path = export_study_guide(
                f"GraphiQ - {st.session_state.graphiq_request[:40]}",
                f"## Visualization Request\n{st.session_state.graphiq_request}\n\n## Generated Code\n```python\n{st.session_state.graphiq_code}\n```",
                tags=["graphiq", "visualization"],
            )
            st.success(f"Exported to: {path}")
