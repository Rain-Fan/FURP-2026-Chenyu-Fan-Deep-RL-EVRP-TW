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


def draw_route_panel(instance, result: dict[str, object], x: int, y: int, w: int, h: int, color: str) -> str:
    nodes = instance.nodes
    project = transform_points(nodes, x + 22, y + 70, w - 44, h - 105)
    parts = [panel(x, y, w, h, short_method(str(result["method"])), f"seed={result['seed']}, objective={float(result['objective_distance']):.1f}, feasible={result['feasible']}")]
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
    parts.append(text(x + 18, y + h - 18, "green depot, amber charging stations, gray customers", 11, "400", PALETTE["muted"]))
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


def generate_index(paths: list[Path]) -> Path:
    week3 = load_json(WEEK3_JSON)
    comparison = week3["comparison"]
    lines = [
        "# Research Visualization Index",
        "",
        "Generated from the existing Week 2, Week 3, Week 4, and Week 5 experiment result files.",
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
    ]
    index = generate_index(paths)
    for path in [*paths, index]:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
