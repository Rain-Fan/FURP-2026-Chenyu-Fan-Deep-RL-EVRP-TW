#!/usr/bin/env python3
"""Generate dependency-free SVG research visualizations from experiment outputs."""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent
WEEK2_JSON = ROOT / "src" / "experiments" / "week2" / "results" / "week2_results.json"
WEEK3_JSON = ROOT / "src" / "experiments" / "week3" / "results" / "week3_results.json"
WEEK4_JSON = ROOT / "src" / "experiments" / "week4" / "results" / "week4_results.json"
WEEK5_JSON = ROOT / "src" / "experiments" / "week5" / "results" / "week5_results.json"
WEEK6_JSON = ROOT / "src" / "experiments" / "week6" / "results" / "week6_results.json"
WEEK7_JSON = ROOT / "src" / "experiments" / "week7" / "results" / "week7_results.json"

PALETTE = {
    "tested": "#dc2626",
    "baseline": "#2563eb",
    "green": "#059669",
    "amber": "#d97706",
    "purple": "#7c3aed",
    "slate": "#334155",
    "muted": "#64748b",
    "grid": "#e2e8f0",
    "panel": "#f8fafc",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_svg(path: Path, body: str, width: int = 1100, height: int = 700) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
  <rect width="100%" height="100%" fill="white"/>
{body}
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def text(x: float, y: float, label: object, size: int = 14, weight: str = "400", fill: str = "#0f172a", anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
        f"{escape(str(label))}</text>"
    )


def rect(x: float, y: float, w: float, h: float, fill: str, stroke: str = "none", rx: int = 0) -> str:
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'


def line(x1: float, y1: float, x2: float, y2: float, stroke: str = "#0f172a", width: float = 1.0, dash: str = "") -> str:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width:.1f}"{dash_attr}/>'


def circle(x: float, y: float, r: float, fill: str, stroke: str = "white", width: float = 1.0) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{width:.1f}"/>'


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 1.5, opacity: float = 0.55) -> str:
    coords = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width:.1f}" opacity="{opacity:.2f}"/>'


def panel(x: int, y: int, w: int, h: int, title: str, subtitle: str = "") -> str:
    parts = [rect(x, y, w, h, PALETTE["panel"], "#cbd5e1", 6), text(x + 18, y + 30, title, 18, "700")]
    if subtitle:
        parts.append(text(x + 18, y + 52, subtitle, 12, "400", PALETTE["muted"]))
    return "\n".join(parts)


def scale_y(value: float, min_value: float, max_value: float, top: float, bottom: float) -> float:
    if max_value == min_value:
        return bottom
    return bottom - (value - min_value) / (max_value - min_value) * (bottom - top)


def draw_axes(x: int, y: int, w: int, h: int, max_value: float, ticks: int = 4, suffix: str = "") -> str:
    parts = [line(x, y + h, x + w, y + h, "#94a3b8", 1.2), line(x, y, x, y + h, "#94a3b8", 1.2)]
    for i in range(ticks + 1):
        value = max_value * i / ticks
        yy = y + h - h * i / ticks
        parts.append(line(x, yy, x + w, yy, PALETTE["grid"], 0.8))
        label = f"{value:.0f}{suffix}" if max_value > 10 else f"{value:.2f}{suffix}"
        parts.append(text(x - 8, yy + 4, label, 10, "400", PALETTE["muted"], "end"))
    return "\n".join(parts)


def draw_grouped_bars(
    rows: list[dict[str, object]],
    x: int,
    y: int,
    w: int,
    h: int,
    groups: list[int],
    series: list[str],
    value_key: str,
    colors: dict[str, str],
    y_suffix: str = "",
) -> str:
    values = [float(row[value_key] or 0) for row in rows]
    max_value = max(values) * 1.15 if values else 1.0
    parts = [draw_axes(x, y, w, h, max_value, suffix=y_suffix)]
    group_w = w / len(groups)
    bar_gap = 5
    bar_w = min(42, (group_w - 28) / max(1, len(series)) - bar_gap)
    row_map = {(int(row["scale"]), str(row["method"])): row for row in rows}
    for gi, group in enumerate(groups):
        gx = x + group_w * gi + group_w / 2
        for si, name in enumerate(series):
            row = row_map.get((group, name))
            value = float(row[value_key] or 0) if row else 0.0
            bx = gx - (len(series) * (bar_w + bar_gap) - bar_gap) / 2 + si * (bar_w + bar_gap)
            bh = 0 if max_value == 0 else value / max_value * h
            parts.append(rect(bx, y + h - bh, bar_w, bh, colors[name], rx=2))
        parts.append(text(gx, y + h + 24, group, 12, "600", PALETTE["slate"], "middle"))
    return "\n".join(parts)


def legend(items: list[tuple[str, str]], x: int, y: int) -> str:
    parts = []
    offset = 0
    for label, color in items:
        parts.append(rect(x + offset, y - 10, 12, 12, color, rx=2))
        parts.append(text(x + offset + 18, y, label, 12, "500", PALETTE["slate"]))
        offset += 18 + len(label) * 7 + 26
    return "\n".join(parts)


def short_method(name: str) -> str:
    mapping = {
        "POMO-style multi-start masked greedy": "POMO-style",
        "GA permutation + EV/TW repair": "GA repair",
        "OR-Tools CVRPTW + charging repair": "OR-Tools repair",
        "A_due_time_priority": "A: due-time",
        "B_nearest_customer": "B: nearest",
        "C_composite_score": "C: composite+2opt",
        "D_composite_inter_route": "D: +inter-route",
        "E_fixed_portfolio": "E-fixed: portfolio",
        "E_adaptive_portfolio": "E-adaptive: UCB1",
        "F_dqn_portfolio": "F: Double DQN",
    }
    return mapping.get(name, name)


def generate_week2_visualization() -> Path:
    data = load_json(WEEK2_JSON)
    scales = sorted({int(row["scale"]) for row in data})
    methods = sorted({str(row["method"]) for row in data})
    colors = {
        "POMO-style multi-start masked greedy": PALETTE["green"],
        "GA permutation + EV/TW repair": PALETTE["amber"],
        "OR-Tools CVRPTW + charging repair": PALETTE["purple"],
    }
    body = [
        text(40, 42, "Week 2 EVRP-TW baseline comparison", 26, "800"),
        text(40, 68, "Objective distance and runtime across generated instance scales", 14, "400", PALETTE["muted"]),
        panel(40, 95, 500, 520, "Objective distance", "Lower is better; compare feasible rows only"),
        panel(560, 95, 500, 520, "Runtime", "Wall-clock seconds recorded by each method"),
        draw_grouped_bars(data, 105, 180, 390, 330, scales, methods, "objective", colors),
        draw_grouped_bars(data, 625, 180, 390, 330, scales, methods, "runtime_sec", colors),
        text(300, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(820, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        legend([(short_method(m), colors[m]) for m in methods], 70, 650),
    ]
    path = OUT_DIR / "week2_baseline_comparison.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def generate_week3_performance_visualization() -> Path:
    data = load_json(WEEK3_JSON)["aggregate"]
    scales = sorted({int(row["scale"]) for row in data})
    methods = ["A_due_time_priority", "B_nearest_customer"]
    colors = {"A_due_time_priority": PALETTE["tested"], "B_nearest_customer": PALETTE["baseline"]}
    body = [
        text(40, 42, "Week 3 controlled evaluation: performance", 26, "800"),
        text(40, 68, "Due-time-priority greedy versus nearest-customer baseline on the same EVRP-TW instances", 14, "400", PALETTE["muted"]),
        panel(40, 95, 500, 520, "Feasibility rate", "Fraction of instances satisfying all EVRP-TW checks"),
        panel(560, 95, 500, 520, "Mean feasible objective", "Total route distance for feasible solutions"),
        draw_grouped_bars(data, 105, 180, 390, 330, scales, methods, "feasibility_rate", colors),
        draw_grouped_bars(data, 625, 180, 390, 330, scales, methods, "mean_objective_feasible", colors),
        text(300, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(820, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        legend([(short_method(m), colors[m]) for m in methods], 340, 650),
    ]
    path = OUT_DIR / "week3_performance_summary.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def generate_week3_diagnostics_visualization() -> Path:
    data = load_json(WEEK3_JSON)["aggregate"]
    scales = sorted({int(row["scale"]) for row in data})
    methods = ["A_due_time_priority", "B_nearest_customer"]
    colors = {"A_due_time_priority": PALETTE["tested"], "B_nearest_customer": PALETTE["baseline"]}
    body = [
        text(40, 42, "Week 3 controlled evaluation: diagnostics", 26, "800"),
        text(40, 68, "Resource use and coverage failures explain why due-time-only priority is weaker", 14, "400", PALETTE["muted"]),
        panel(40, 95, 325, 520, "Vehicles used", "Mean vehicles per instance"),
        panel(387, 95, 325, 520, "Charging visits", "Mean station visits per instance"),
        panel(735, 95, 325, 520, "Coverage violations", "Unserved-customer failures"),
        draw_grouped_bars(data, 92, 180, 230, 330, scales, methods, "mean_vehicles_used", colors),
        draw_grouped_bars(data, 439, 180, 230, 330, scales, methods, "mean_charge_count", colors),
        draw_grouped_bars(data, 787, 180, 230, 330, scales, methods, "coverage_violations", colors),
        text(207, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(554, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(902, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        legend([(short_method(m), colors[m]) for m in methods], 340, 650),
    ]
    path = OUT_DIR / "week3_diagnostic_summary.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def load_week3_instance(scale: int = 50):
    sys.path.insert(0, str(ROOT / "src" / "experiments" / "week3"))
    from compare_week3_baselines import generate_instance

    data = load_json(WEEK3_JSON)["instances"]
    selected_seed = min(int(row["seed"]) for row in data if int(row["scale"]) == scale)
    instance = generate_instance(scale, selected_seed)
    rows = [row for row in data if int(row["scale"]) == scale and int(row["seed"]) == selected_seed]
    return instance, rows


def transform_points(nodes, x: int, y: int, w: int, h: int):
    xs = [node.x for node in nodes]
    ys = [node.y for node in nodes]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    def project(node):
        px = x + (node.x - min_x) / (max_x - min_x) * w
        py = y + h - (node.y - min_y) / (max_y - min_y) * h
        return px, py

    return project


def draw_route_panel(instance, result: dict[str, object], x: int, y: int, w: int, h: int, color: str, *, compact: bool = False) -> str:
    nodes = instance.nodes
    project = transform_points(nodes, x + 22, y + 70, w - 44, h - 105)
    subtitle = (
        f"seed={result['seed']}, obj={float(result['objective_distance']):.1f}"
        if compact
        else f"seed={result['seed']}, objective={float(result['objective_distance']):.1f}, feasible={result['feasible']}"
    )
    parts = [panel(x, y, w, h, short_method(str(result["method"])), subtitle)]
    for route in result["routes"]:
        points = [project(instance.node(int(idx))) for idx in route]
        parts.append(polyline(points, color, 1.3, 0.45))
    for node in instance.customers:
        px, py = project(node)
        parts.append(circle(px, py, 3.0, "#94a3b8", "white", 0.7))
    for node in instance.stations:
        px, py = project(node)
        parts.append(rect(px - 4, py - 4, 8, 8, PALETTE["amber"], "white", 1))
    dx, dy = project(instance.depot)
    parts.append(circle(dx, dy, 7, PALETTE["green"], "white", 1.5))
    footer = "depot / stations / customers" if compact else "green depot, amber charging stations, gray customers"
    parts.append(text(x + 18, y + h - 18, footer, 11, "400", PALETTE["muted"]))
    return "\n".join(parts)


def generate_week3_route_visualization() -> Path:
    instance, rows = load_week3_instance(scale=50)
    by_method = {str(row["method"]): row for row in rows}
    body = [
        text(40, 42, "Week 3 representative route footprint", 26, "800"),
        text(40, 68, "Same 50-customer instance; route geometry shows the spatial cost of due-time-only priority", 14, "400", PALETTE["muted"]),
        draw_route_panel(instance, by_method["A_due_time_priority"], 40, 95, 500, 520, PALETTE["tested"]),
        draw_route_panel(instance, by_method["B_nearest_customer"], 560, 95, 500, 520, PALETTE["baseline"]),
    ]
    path = OUT_DIR / "week3_representative_routes.svg"
    write_svg(path, "\n".join(body), 1100, 660)
    return path


# ---------------------------------------------------------------------------
# Week 4: method-improvement visualizations
# ---------------------------------------------------------------------------

def generate_week4_performance_visualization() -> Path:
    """Feasibility rate and mean feasible objective for C vs A vs B, baseline profile only."""
    data = load_json(WEEK4_JSON)["aggregate"]
    baseline = [row for row in data if row["profile"] == "baseline"]
    scales = sorted({int(row["scale"]) for row in baseline})
    methods = ["C_composite_score", "A_due_time_priority", "B_nearest_customer"]
    colors = {
        "C_composite_score": PALETTE["tested"],
        "A_due_time_priority": PALETTE["amber"],
        "B_nearest_customer": PALETTE["baseline"],
    }
    body = [
        text(40, 42, "Week 4 method improvement: performance (baseline profile)", 26, "800"),
        text(40, 68, "Composite-score greedy + 2-opt (C) vs due-time greedy (A) vs nearest-customer (B)", 14, "400", PALETTE["muted"]),
        panel(40, 95, 500, 520, "Feasibility rate", "Fraction of instances satisfying all EVRP-TW constraints"),
        panel(560, 95, 500, 520, "Mean feasible objective", "Total route distance — lower is better"),
        draw_grouped_bars(baseline, 105, 180, 390, 330, scales, methods, "feasibility_rate", colors),
        draw_grouped_bars(baseline, 625, 180, 390, 330, scales, methods, "mean_objective_feasible", colors),
        text(300, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(820, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        legend([(short_method(m), colors[m]) for m in methods], 180, 650),
    ]
    path = OUT_DIR / "week4_performance_summary.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def generate_week4_profiles_visualization() -> Path:
    """Feasibility rate for Method C across all three stress profiles."""
    data = load_json(WEEK4_JSON)["aggregate"]
    profiles = ["baseline", "tight_tw", "small_battery"]
    profile_labels = {
        "baseline": "Baseline",
        "tight_tw": "Tight TW (60%)",
        "small_battery": "Small battery (75%)",
    }
    scales = sorted({int(row["scale"]) for row in data})
    colors = {
        "baseline": PALETTE["green"],
        "tight_tw": PALETTE["purple"],
        "small_battery": PALETTE["amber"],
    }

    # draw_grouped_bars groups by scale and series-by-method; here we remap the
    # stress profile onto the "method" key so each profile becomes one bar.
    c_rows: list[dict[str, object]] = []
    a_rows: list[dict[str, object]] = []
    for profile in profiles:
        for scale in scales:
            for src, dst in (("C_composite_score", c_rows), ("A_due_time_priority", a_rows)):
                row = next(
                    (r for r in data if r["profile"] == profile
                     and int(r["scale"]) == scale and r["method"] == src),
                    None,
                )
                if row:
                    dst.append({
                        "scale": scale,
                        "method": profile,
                        "feasibility_rate": row["feasibility_rate"],
                        "mean_two_opt_gain": row.get("mean_two_opt_gain", 0.0),
                    })

    body = [
        text(40, 42, "Week 4 method improvement: stress-profile sensitivity", 26, "800"),
        text(40, 68, "How feasibility rate changes under tighter time windows and smaller battery", 14, "400", PALETTE["muted"]),
        panel(40, 95, 325, 520, "Method C feasibility rate", "Composite + 2-opt under each stress profile"),
        panel(387, 95, 325, 520, "Method A feasibility rate", "Due-time greedy — reference from Week 3"),
        panel(735, 95, 325, 520, "2-opt gain (Method C)", "Mean distance removed by local search"),
        draw_grouped_bars(c_rows, 92, 180, 230, 330, scales, profiles, "feasibility_rate", colors),
        draw_grouped_bars(a_rows, 439, 180, 230, 330, scales, profiles, "feasibility_rate", colors),
        draw_grouped_bars(c_rows, 787, 180, 230, 330, scales, profiles, "mean_two_opt_gain", colors),
        text(207, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(554, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(902, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        legend([(profile_labels[p], colors[p]) for p in profiles], 250, 650),
    ]
    path = OUT_DIR / "week4_profile_sensitivity.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def load_week4_instance(scale: int = 50):
    """Load one Week 4 instance and its per-method result rows."""
    sys.path.insert(0, str(ROOT / "src" / "experiments" / "week4"))
    from compare_week4_methods import DEFAULT_SEED, apply_profile, generate_instance  # noqa: E402

    data = load_json(WEEK4_JSON)["instances"]
    # Pick the first baseline seed for this scale
    baseline_rows = [
        r for r in data
        if int(r["scale"]) == scale and r["profile"] == "baseline"
    ]
    selected_seed = min(int(r["seed"]) for r in baseline_rows)
    instance = apply_profile(generate_instance(scale, selected_seed), "baseline")
    rows = [r for r in baseline_rows if int(r["seed"]) == selected_seed]
    return instance, rows


def generate_week4_route_visualization() -> Path:
    """Three-panel route footprint: Method B, A, and C on the same instance."""
    instance, rows = load_week4_instance(scale=50)
    by_method = {str(row["method"]): row for row in rows}
    colors = {
        "A_due_time_priority": PALETTE["amber"],
        "B_nearest_customer": PALETTE["baseline"],
        "C_composite_score": PALETTE["tested"],
    }
    panels = []
    panel_w, panel_h = 330, 520
    for i, method in enumerate(["A_due_time_priority", "B_nearest_customer", "C_composite_score"]):
        px = 40 + i * (panel_w + 20)
        row = by_method.get(method, {})
        panels.append(draw_route_panel(instance, row, px, 95, panel_w, panel_h, colors[method]))
    body = [
        text(40, 42, "Week 4 representative route footprint (3 methods)", 26, "800"),
        text(40, 68, "Same 50-customer instance: A is vehicle-heavy, C is most compact", 14, "400", PALETTE["muted"]),
        *panels,
    ]
    path = OUT_DIR / "week4_representative_routes.svg"
    write_svg(path, "\n".join(body), 1060, 660)
    return path


# ---------------------------------------------------------------------------
# Week 5: inter-route local-search visualizations
# ---------------------------------------------------------------------------

def generate_week5_performance_visualization() -> Path:
    """Mean feasible objective for D vs C vs B across scales (baseline profile)."""
    data = load_json(WEEK5_JSON)["aggregate"]
    baseline = [row for row in data if row["profile"] == "baseline"]
    scales = sorted({int(row["scale"]) for row in baseline})
    methods = ["D_composite_inter_route", "C_composite_score", "B_nearest_customer"]
    colors = {
        "D_composite_inter_route": PALETTE["tested"],
        "C_composite_score": PALETTE["amber"],
        "B_nearest_customer": PALETTE["baseline"],
    }
    body = [
        text(40, 42, "Week 5 inter-route local search: performance (baseline profile)", 24, "800"),
        text(40, 68, "Composite + 2-opt + inter-route LS (D) vs composite + 2-opt (C) vs nearest-customer (B)", 14, "400", PALETTE["muted"]),
        panel(40, 95, 500, 520, "Mean feasible objective", "Total route distance — lower is better"),
        panel(560, 95, 500, 520, "Mean vehicles used", "Fewer vehicles usually means tighter routing"),
        draw_grouped_bars(baseline, 105, 180, 390, 330, scales, methods, "mean_objective_feasible", colors),
        draw_grouped_bars(baseline, 625, 180, 390, 330, scales, methods, "mean_vehicles_used", colors),
        text(300, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(820, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        legend([(short_method(m), colors[m]) for m in methods], 180, 650),
    ]
    path = OUT_DIR / "week5_performance_summary.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def load_week5_instance(scale: int = 50):
    """Load one Week 5 instance and its per-method result rows (baseline profile)."""
    sys.path.insert(0, str(ROOT / "src" / "experiments" / "week3"))
    sys.path.insert(0, str(ROOT / "src" / "experiments" / "week4"))
    sys.path.insert(0, str(ROOT / "src" / "experiments" / "week5"))
    from compare_week3_baselines import generate_instance  # noqa: E402
    from compare_week4_methods import apply_profile  # noqa: E402

    data = load_json(WEEK5_JSON)["instances"]
    baseline_rows = [
        r for r in data
        if int(r["scale"]) == scale and r["profile"] == "baseline"
    ]
    selected_seed = min(int(r["seed"]) for r in baseline_rows)
    instance = apply_profile(generate_instance(scale, selected_seed), "baseline")
    rows = [r for r in baseline_rows if int(r["seed"]) == selected_seed]
    return instance, rows


def generate_week5_route_visualization() -> Path:
    """Three-panel route footprint: Method B, C, and D on the same instance."""
    instance, rows = load_week5_instance(scale=50)
    by_method = {str(row["method"]): row for row in rows}
    colors = {
        "B_nearest_customer": PALETTE["baseline"],
        "C_composite_score": PALETTE["amber"],
        "D_composite_inter_route": PALETTE["tested"],
    }
    panels = []
    panel_w, panel_h = 330, 520
    for i, method in enumerate(["B_nearest_customer", "C_composite_score", "D_composite_inter_route"]):
        px = 40 + i * (panel_w + 20)
        row = by_method.get(method, {})
        panels.append(draw_route_panel(instance, row, px, 95, panel_w, panel_h, colors[method]))
    body = [
        text(40, 42, "Week 5 representative route footprint (3 methods)", 26, "800"),
        text(40, 68, "Same 50-customer instance: inter-route moves (D) remove crossings C left behind", 14, "400", PALETTE["muted"]),
        *panels,
    ]
    path = OUT_DIR / "week5_representative_routes.svg"
    write_svg(path, "\n".join(body), 1060, 660)
    return path


# ---------------------------------------------------------------------------
# Week 6: portfolio + adaptive operator-selection visualizations
# ---------------------------------------------------------------------------

def draw_annotated_grouped_bars(
    rows: list[dict[str, object]],
    x: int,
    y: int,
    w: int,
    h: int,
    groups: list[int],
    series: list[str],
    value_key: str,
    colors: dict[str, str],
    decimals: int,
) -> str:
    """Draw grouped bars and print the measured value above each bar."""
    parts = [draw_grouped_bars(rows, x, y, w, h, groups, series, value_key, colors)]
    values = [float(row[value_key] or 0) for row in rows]
    max_value = max(values) * 1.15 if values else 1.0
    group_w = w / len(groups)
    bar_gap = 5
    bar_w = min(42, (group_w - 28) / max(1, len(series)) - bar_gap)
    row_map = {(int(row["scale"]), str(row["method"])): row for row in rows}
    for group_index, group in enumerate(groups):
        group_x = x + group_w * group_index + group_w / 2
        for series_index, name in enumerate(series):
            row = row_map.get((group, name))
            if not row:
                continue
            value = float(row[value_key] or 0)
            bar_x = group_x - (len(series) * (bar_w + bar_gap) - bar_gap) / 2 + series_index * (bar_w + bar_gap)
            bar_height = 0 if max_value == 0 else value / max_value * h
            label_y = y + h - bar_height - 7 - (series_index % 2) * 12
            parts.append(text(bar_x + bar_w / 2, label_y, f"{value:.{decimals}f}", 8, "600", PALETTE["slate"], "middle"))
    return "\n".join(parts)


def generate_week6_performance_visualization() -> Path:
    """Portfolio quality/runtime trade-off on the baseline profile."""
    data = load_json(WEEK6_JSON)["aggregate"]
    baseline = [row for row in data if row["profile"] == "baseline"]
    scales = sorted({int(row["scale"]) for row in baseline})
    methods = [
        "B_nearest_customer",
        "D_composite_inter_route",
        "E_fixed_portfolio",
        "E_adaptive_portfolio",
    ]
    colors = {
        "B_nearest_customer": PALETTE["baseline"],
        "D_composite_inter_route": PALETTE["amber"],
        "E_fixed_portfolio": PALETTE["purple"],
        "E_adaptive_portfolio": PALETTE["tested"],
    }
    body = [
        text(40, 42, "Week 6 portfolio + UCB1: measured performance (baseline profile)", 24, "800"),
        text(40, 68, "Means over 12 locally generated instances per scale; labels are read from week6_results.json", 14, "400", PALETTE["muted"]),
        panel(40, 95, 500, 520, "Mean feasible objective", "Total route distance — lower is better"),
        panel(560, 95, 500, 520, "Mean runtime", "Wall-clock seconds — lower is faster"),
        draw_annotated_grouped_bars(baseline, 105, 180, 390, 330, scales, methods, "mean_objective_feasible", colors, 2),
        draw_annotated_grouped_bars(baseline, 625, 180, 390, 330, scales, methods, "mean_runtime_sec", colors, 3),
        text(300, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(820, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        legend([(short_method(method), colors[method]) for method in methods], 80, 650),
    ]
    path = OUT_DIR / "week6_performance_summary.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def generate_week6_operator_visualization() -> Path:
    """Summarize actual UCB1 operator selections and rewards from all trace rows."""
    trace = load_json(WEEK6_JSON)["adaptive_trace"]
    actions = ["two_opt", "relocate", "swap"]
    colors = {
        "two_opt": PALETTE["green"],
        "relocate": PALETTE["tested"],
        "swap": PALETTE["purple"],
    }
    rows = []
    for action in actions:
        selected = [row for row in trace if row["action"] == action]
        rows.append(
            {
                "action": action,
                "selections": len(selected),
                "accepted": sum(bool(row["accepted"]) for row in selected),
                "mean_reward": mean(float(row["reward"]) for row in selected),
            }
        )
    best_reward_row = max(rows, key=lambda row: float(row["mean_reward"]))

    def action_bars(value_key: str, x: int, y: int, w: int, h: int, decimals: int) -> str:
        values = [float(row[value_key]) for row in rows]
        max_value = max(values) * 1.18
        parts = [draw_axes(x, y, w, h, max_value)]
        group_w = w / len(rows)
        bar_w = 62
        for index, row in enumerate(rows):
            value = float(row[value_key])
            center_x = x + group_w * index + group_w / 2
            bar_height = value / max_value * h
            parts.append(rect(center_x - bar_w / 2, y + h - bar_height, bar_w, bar_height, colors[str(row["action"])], rx=3))
            parts.append(text(center_x, y + h - bar_height - 9, f"{value:.{decimals}f}", 12, "700", PALETTE["slate"], "middle"))
            parts.append(text(center_x, y + h + 24, row["action"], 12, "600", PALETTE["slate"], "middle"))
        return "\n".join(parts)

    body = [
        text(40, 42, "Week 6 adaptive operator selection: observed UCB1 behavior", 25, "800"),
        text(40, 68, f"All {len(trace)} trace rows from the local 3-profile × 3-scale experiment", 14, "400", PALETTE["muted"]),
        panel(40, 95, 500, 520, "Operator selections", "How often UCB1 selected each action"),
        panel(560, 95, 500, 520, "Mean normalized reward", "Accepted relative improvement, averaged over all selections"),
        action_bars("selections", 105, 180, 390, 330, 0),
        action_bars("mean_reward", 625, 180, 390, 330, 5),
        text(300, 560, "Operator", 13, "700", PALETTE["slate"], "middle"),
        text(820, 560, "Operator", 13, "700", PALETTE["slate"], "middle"),
        text(
            550,
            650,
            f"{best_reward_row['action']} was selected {best_reward_row['selections']} times and achieved "
            f"the highest mean reward ({float(best_reward_row['mean_reward']):.5f})",
            13,
            "600",
            PALETTE["slate"],
            "middle",
        ),
    ]
    path = OUT_DIR / "week6_adaptive_operator_summary.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def load_week6_instance(scale: int = 50):
    """Rebuild one Week 6 instance and load its measured per-method routes."""
    sys.path.insert(0, str(ROOT / "src" / "experiments" / "week3"))
    sys.path.insert(0, str(ROOT / "src" / "experiments" / "week4"))
    from compare_week3_baselines import generate_instance  # noqa: E402
    from compare_week4_methods import apply_profile  # noqa: E402

    data = load_json(WEEK6_JSON)["instances"]
    baseline_rows = [
        row for row in data
        if int(row["scale"]) == scale and row["profile"] == "baseline"
    ]
    selected_seed = min(int(row["seed"]) for row in baseline_rows)
    instance = apply_profile(generate_instance(scale, selected_seed), "baseline")
    rows = [row for row in baseline_rows if int(row["seed"]) == selected_seed]
    return instance, rows


def generate_week6_route_visualization() -> Path:
    """Route footprints for Week 5 D, fixed portfolio, and adaptive portfolio."""
    instance, rows = load_week6_instance(scale=50)
    by_method = {str(row["method"]): row for row in rows}
    methods = ["D_composite_inter_route", "E_fixed_portfolio", "E_adaptive_portfolio"]
    colors = {
        "D_composite_inter_route": PALETTE["amber"],
        "E_fixed_portfolio": PALETTE["purple"],
        "E_adaptive_portfolio": PALETTE["tested"],
    }
    panels = []
    panel_w, panel_h = 330, 520
    for index, method in enumerate(methods):
        panel_x = 40 + index * (panel_w + 20)
        row = dict(by_method[method])
        row["objective_distance"] = row["objective"]
        panels.append(draw_route_panel(instance, row, panel_x, 95, panel_w, panel_h, colors[method]))
    body = [
        text(40, 42, "Week 6 representative route footprint (same local instance)", 25, "800"),
        text(40, 68, "Week 5 D → fixed portfolio → UCB1 adaptive portfolio on the same 50-customer seed", 14, "400", PALETTE["muted"]),
        *panels,
    ]
    path = OUT_DIR / "week6_representative_routes.svg"
    write_svg(path, "\n".join(body), 1060, 660)
    return path


# ---------------------------------------------------------------------------
# Week 7: trainable Double-DQN extension visualizations
# ---------------------------------------------------------------------------

def generate_week7_performance_visualization() -> Path:
    """Held-out quality/runtime comparison for D, E-fixed, UCB1, and DQN."""
    data = load_json(WEEK7_JSON)["aggregate"]
    baseline = [row for row in data if row["profile"] == "baseline"]
    scales = sorted({int(row["scale"]) for row in baseline})
    methods = ["D_composite_inter_route", "E_fixed_portfolio", "E_adaptive_portfolio", "F_dqn_portfolio"]
    colors = {
        "D_composite_inter_route": PALETTE["amber"],
        "E_fixed_portfolio": PALETTE["purple"],
        "E_adaptive_portfolio": PALETTE["baseline"],
        "F_dqn_portfolio": PALETTE["tested"],
    }
    body = [
        text(40, 42, "Week 7 Double DQN: held-out EVRP-TW performance", 25, "800"),
        text(40, 68, "Six unseen seeds per scale; all objective labels come from independently validated feasible routes", 14, "400", PALETTE["muted"]),
        panel(40, 95, 500, 520, "Mean feasible objective", "Baseline profile — lower is better"),
        panel(560, 95, 500, 520, "Mean runtime", "Real wall-clock seconds — lower is faster"),
        draw_annotated_grouped_bars(baseline, 105, 180, 390, 330, scales, methods, "mean_objective_feasible", colors, 2),
        draw_annotated_grouped_bars(baseline, 625, 180, 390, 330, scales, methods, "mean_runtime_sec", colors, 3),
        text(300, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        text(820, 560, "Customers", 13, "700", PALETTE["slate"], "middle"),
        legend([(short_method(method), colors[method]) for method in methods], 95, 650),
    ]
    path = OUT_DIR / "week7_heldout_performance.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def generate_week7_training_visualization() -> Path:
    """Epoch-level return and distance-improvement summaries from real training."""
    payload = load_json(WEEK7_JSON)
    history = payload["training_history"]
    epochs = sorted({int(row["epoch"]) for row in history})
    returns = [mean(float(row["return"]) for row in history if int(row["epoch"]) == epoch) for epoch in epochs]
    gains = [mean(float(row["improvement_pct"]) for row in history if int(row["epoch"]) == epoch) for epoch in epochs]

    def line_chart(values: list[float], x: int, y: int, w: int, h: int, color: str, digits: int) -> str:
        min_value = min(0.0, min(values))
        max_value = max(values) * 1.18 if max(values) > 0 else 1.0
        parts = [draw_axes(x, y, w, h, max_value)]
        points = []
        for index, value in enumerate(values):
            px = x + (index + 0.5) * w / len(values)
            py = scale_y(value, min_value, max_value, y, y + h)
            points.append((px, py))
            parts.append(circle(px, py, 5, color))
            parts.append(text(px, py - 12, f"{value:.{digits}f}", 11, "700", PALETTE["slate"], "middle"))
            parts.append(text(px, y + h + 24, f"epoch {epochs[index] + 1}", 11, "600", PALETTE["slate"], "middle"))
        parts.append(polyline(points, color, 2.8, 0.9))
        return "\n".join(parts)

    model_hash = str(payload["metadata"]["model_parameter_hash"])
    body = [
        text(40, 42, "Week 7 Double-DQN training summary", 26, "800"),
        text(40, 68, f"{len(history)} real training episodes; model hash {model_hash[:12]}", 14, "400", PALETTE["muted"]),
        panel(40, 95, 500, 520, "Mean episode return", "Average across profiles, scales, seeds, and construction sources"),
        panel(560, 95, 500, 520, "Mean distance improvement", "Improvement from the feasible 2-opt warm start (%)"),
        line_chart(returns, 105, 180, 390, 330, PALETTE["baseline"], 4),
        line_chart(gains, 625, 180, 390, 330, PALETTE["green"], 2),
        text(300, 560, "Training epoch", 13, "700", PALETTE["slate"], "middle"),
        text(820, 560, "Training epoch", 13, "700", PALETTE["slate"], "middle"),
        text(550, 650, "Training and held-out evaluation use disjoint seed sets (overlap = 0)", 13, "600", PALETTE["slate"], "middle"),
    ]
    path = OUT_DIR / "week7_training_summary.svg"
    write_svg(path, "\n".join(body), 1100, 700)
    return path


def load_week7_instance(scale: int = 50):
    sys.path.insert(0, str(ROOT / "src" / "experiments" / "week3"))
    sys.path.insert(0, str(ROOT / "src" / "experiments" / "week4"))
    from compare_week3_baselines import generate_instance  # noqa: E402
    from compare_week4_methods import apply_profile  # noqa: E402

    rows = [row for row in load_json(WEEK7_JSON)["instances"] if row["profile"] == "baseline" and int(row["scale"]) == scale]
    seed = min(int(row["seed"]) for row in rows)
    instance = apply_profile(generate_instance(scale, seed), "baseline")
    return instance, [row for row in rows if int(row["seed"]) == seed]


def generate_week7_route_visualization() -> Path:
    instance, rows = load_week7_instance(50)
    by_method = {str(row["method"]): row for row in rows}
    methods = ["D_composite_inter_route", "E_fixed_portfolio", "E_adaptive_portfolio", "F_dqn_portfolio"]
    colors = {
        "D_composite_inter_route": PALETTE["amber"],
        "E_fixed_portfolio": PALETTE["purple"],
        "E_adaptive_portfolio": PALETTE["baseline"],
        "F_dqn_portfolio": PALETTE["tested"],
    }
    panels = []
    panel_w, panel_h = 250, 500
    for index, method in enumerate(methods):
        row = dict(by_method[method])
        row["objective_distance"] = row["objective"]
        panels.append(draw_route_panel(instance, row, 25 + index * 270, 95, panel_w, panel_h, colors[method], compact=True))
    body = [
        text(25, 42, "Week 7 held-out route footprint (same unseen instance)", 25, "800"),
        text(25, 68, "Fixed search, UCB1, and Double DQN share construction sources, operators, budget, and validator", 14, "400", PALETTE["muted"]),
        *panels,
    ]
    path = OUT_DIR / "week7_representative_routes.svg"
    write_svg(path, "\n".join(body), 1100, 640)
    return path


def generate_index(paths: list[Path]) -> Path:
    week3 = load_json(WEEK3_JSON)
    comparison = week3["comparison"]
    lines = [
        "# Research Visualization Index",
        "",
        "Generated from the existing Week 2–Week 7 experiment result files.",
        "",
        "## Figures",
        "",
    ]
    for path in paths:
        lines.append(f"- [{path.name}]({path.name})")
    lines.extend(
        [
            "",
            "## Week 3 headline deltas",
            "",
            "| Customers | Feasibility delta A-B | Feasible objective delta A-B | Coverage violation delta A-B |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in comparison:
        lines.append(
            f"| {row['scale']} | {row['feasibility_rate_delta']:.3f} | "
            f"{row['mean_feasible_objective_delta']:.3f} | {row['coverage_violation_delta']} |"
        )
    lines.extend(
        [
            "",
            "A is `A_due_time_priority`; B is `B_nearest_customer`. Negative feasibility",
            "delta means A solved fewer instances. Positive objective delta means A used",
            "longer feasible routes.",
            "",
        ]
    )

    week4 = load_json(WEEK4_JSON)
    week4_cmp = week4["comparison"]
    lines.extend(
        [
            "## Week 4 headline deltas (Method C vs references, baseline profile)",
            "",
            "| Customers | Reference | Feasibility delta C-ref | Feasible objective delta C-ref |",
            "|---:|---|---:|---:|",
        ]
    )
    for row in week4_cmp:
        if row["profile"] != "baseline":
            continue
        obj_delta = row["mean_feasible_objective_delta"]
        obj_text = f"{obj_delta:.3f}" if obj_delta is not None else "NA"
        lines.append(
            f"| {row['scale']} | {short_method(row['reference'])} | "
            f"{row['feasibility_rate_delta']:.3f} | {obj_text} |"
        )
    lines.extend(
        [
            "",
            "C is `C_composite_score` (composite-score greedy + feasibility-aware 2-opt).",
            "Positive feasibility delta means C solved more instances than the reference.",
            "Negative objective delta means C found shorter feasible routes.",
            "",
        ]
    )

    week5 = load_json(WEEK5_JSON)
    week5_cmp = week5["comparison"]
    lines.extend(
        [
            "## Week 5 headline deltas (Method D vs references, baseline profile)",
            "",
            "| Customers | Reference | Feasibility delta D-ref | Objective delta D-ref (%) |",
            "|---:|---|---:|---:|",
        ]
    )
    for row in week5_cmp:
        if row["profile"] != "baseline":
            continue
        pct = row["mean_feasible_objective_pct"]
        pct_text = f"{pct:.2f}" if pct is not None else "NA"
        lines.append(
            f"| {row['scale']} | {short_method(row['reference'])} | "
            f"{row['feasibility_rate_delta']:.3f} | {pct_text} |"
        )
    lines.extend(
        [
            "",
            "D is `D_composite_inter_route` (Method C plus inter-route or-opt + swap).",
            "Negative objective percent means D found shorter feasible routes; at n=50 and",
            "n=100 D is now below the baseline, closing the Week 4 medium-scale gap.",
            "",
        ]
    )

    week6 = load_json(WEEK6_JSON)
    week6_cmp = [
        row for row in week6["comparisons"]
        if row["tested_method"] == "E_adaptive_portfolio"
        and row["reference_method"] == "D_composite_inter_route"
    ]
    profile_order = {"baseline": 0, "tight_tw": 1, "small_battery": 2}
    profile_labels = {"baseline": "baseline", "tight_tw": "tight TW", "small_battery": "small battery"}
    lines.extend(
        [
            "## Week 6 headline deltas (E-adaptive vs Week 5 D)",
            "",
            "Negative objective percentage means E-adaptive finds shorter feasible routes.",
            "Feasibility delta is zero in every cell.",
            "",
            "| Profile | Customers | Objective delta (%) | Runtime delta (s) | W/T/L |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(week6_cmp, key=lambda item: (profile_order[str(item["profile"])], int(item["scale"]))):
        lines.append(
            f"| {profile_labels[str(row['profile'])]} | {row['scale']} | "
            f"{row['mean_feasible_objective_pct']:+.2f} | {row['mean_runtime_delta_sec']:+.3f} | "
            f"{row['wins']}/{row['ties']}/{row['losses']} |"
        )
    lines.extend(
        [
            "",
            "The integrated portfolio improves mean route quality in all nine cells. The",
            "adaptive method does not win every instance, so the figures and full table also",
            "show its losses and runtime trade-off rather than only aggregate gains.",
            "",
            "## Detailed Week 6 PNG figures",
            "",
            "- [Week 6 workflow](../experiments/week6/results/week6_workflow.png)",
            "- [Week 6 objective and feasibility](../experiments/week6/results/week6_objective_feasibility.png)",
            "- [Week 6 quality/runtime trade-off](../experiments/week6/results/week6_quality_runtime.png)",
            "- [Week 6 operator heatmap](../experiments/week6/results/week6_operator_heatmap.png)",
            "- [Week 6 adaptive convergence](../experiments/week6/results/week6_convergence.png)",
            "- [Week 6 improvement distribution](../experiments/week6/results/week6_improvement_distribution.png)",
            "",
        ]
    )
    week7 = load_json(WEEK7_JSON)
    week7_cmp = [row for row in week7["comparisons"] if row["reference_method"] == "E_adaptive_portfolio"]
    lines.extend([
        "## Week 7 headline deltas (Double DQN vs Week 6 UCB1)", "",
        "Negative objective percentage means Double DQN is shorter on held-out seeds.",
        "All feasibility deltas are zero; mixed quality results are retained.", "",
        "| Profile | Customers | Objective delta (%) | Runtime delta (s) | W/T/L |",
        "|---|---:|---:|---:|---:|",
    ])
    profile_order = {"baseline": 0, "tight_tw": 1, "small_battery": 2}
    labels = {"baseline": "baseline", "tight_tw": "tight TW", "small_battery": "small battery"}
    for row in sorted(week7_cmp, key=lambda item: (profile_order[str(item["profile"])], int(item["scale"]))):
        lines.append(
            f"| {labels[str(row['profile'])]} | {row['scale']} | {row['mean_feasible_objective_pct']:+.2f} | "
            f"{row['mean_runtime_delta_sec']:+.3f} | {row['wins']}/{row['ties']}/{row['losses']} |"
        )
    lines.extend([
        "", "Double DQN is shorter in five of nine cells, tied in one, and worse in three.",
        "The clearest negative case is baseline n=100 (+3.65% distance), so the prototype",
        "does not support a claim that learned selection universally beats UCB1.", "",
        "## Detailed Week 7 PNG figures", "",
        "- [Training curve](../experiments/week7/results/week7_training_curve.png)",
        "- [Held-out objective and feasibility](../experiments/week7/results/week7_objective_feasibility.png)",
        "- [Quality/runtime trade-off](../experiments/week7/results/week7_quality_runtime.png)",
        "- [Action selection](../experiments/week7/results/week7_action_selection.png)",
        "- [Policy-state heatmap](../experiments/week7/results/week7_policy_state_heatmap.png)",
        "- [Representative routes](../experiments/week7/results/week7_representative_routes.png)", "",
    ])
    path = OUT_DIR / "research_visualizations.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    paths = [
        generate_week2_visualization(),
        generate_week3_performance_visualization(),
        generate_week3_diagnostics_visualization(),
        generate_week3_route_visualization(),
        generate_week4_performance_visualization(),
        generate_week4_profiles_visualization(),
        generate_week4_route_visualization(),
        generate_week5_performance_visualization(),
        generate_week5_route_visualization(),
        generate_week6_performance_visualization(),
        generate_week6_operator_visualization(),
        generate_week6_route_visualization(),
        generate_week7_performance_visualization(),
        generate_week7_training_visualization(),
        generate_week7_route_visualization(),
    ]
    index = generate_index(paths)
    for path in [*paths, index]:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
