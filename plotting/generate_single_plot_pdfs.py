#!/usr/bin/env python3
"""
Single-Plot PDF Generator for UC002-Food-Production-Optimization Report.

Generates individual PDF files for plots not covered by generate_all_report_plots.py:
  - study1_hybrid_performance  (Study 1: Hybrid Solver benchmarking)
  - scaling_objectives_by_vars / scaling_objectives_by_farms
  - scaling_qpu_breakdown_by_vars / scaling_qpu_breakdown_by_farms
  - crop_benefit_heatmap

Ported from OQI-UC002-DWave/generate_single_plot_pdfs.py with paths adapted
to the UC002-Food-Production-Optimization repository layout.
"""

from __future__ import annotations

import itertools
import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import rcParams

warnings.filterwarnings("ignore")

# =============================================================================
# IMPORT DATA LOADING AND COLOR DEFINITIONS FROM ORIGINAL SCRIPT
# =============================================================================

from generate_all_report_plots import (
    QUALITATIVE_COLORS,
    SOLVER_COLORS,
    FORMULATION_COLORS,
    METHOD_COLORS,
    MARKERS,
    load_qpu_hierarchical,
    load_gurobi_60s,
    DEFAULT_QPU_HIER_PATH,
    DEFAULT_GUROBI_60S_PATH,
    DEFAULT_OUTPUT_DIR,
    PROJECT_ROOT,
)

# =============================================================================
# PATHS
# =============================================================================

REPO_ROOT = PROJECT_ROOT.parent
SINGLE_PLOT_OUTPUT_DIR = PROJECT_ROOT / "phase3_results_plots"

# Study 1 benchmark data
STUDY1_BENCHMARK_DIR = REPO_ROOT / "data" / "benchmark_results" / "study1"

# Food data
FOOD_DATA_EXCEL = REPO_ROOT / "data" / "inputs" / "Combined_Food_Data.xlsx"

# QPU benchmark files (for Gurobi ground_truth consistency)
QPU_BENCHMARK_DIR = REPO_ROOT / "data" / "benchmark_results" / "study2"


# =============================================================================
# LARGE FONT STYLE CONFIGURATION
# =============================================================================


def setup_large_font_style() -> None:
    """Configure matplotlib for single plots with LARGE fonts."""
    rcParams.update(
        {
            "text.usetex": False,
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman", "Times New Roman", "DejaVu Serif"],
            "font.size": 18,
            "axes.labelsize": 22,
            "axes.titlesize": 26,
            "axes.labelweight": "bold",
            "axes.titleweight": "bold",
            "legend.fontsize": 18,
            "xtick.labelsize": 18,
            "ytick.labelsize": 18,
            "figure.dpi": 150,
            "figure.constrained_layout.use": True,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.15,
            "savefig.transparent": False,
            "axes.grid": True,
            "axes.grid.which": "major",
            "axes.grid.axis": "both",
            "grid.alpha": 0.4,
            "grid.linestyle": "--",
            "grid.linewidth": 1.0,
            "axes.axisbelow": True,
            "axes.linewidth": 1.8,
            "axes.labelpad": 12,
            "axes.titlepad": 18,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 8,
            "ytick.major.size": 8,
            "xtick.major.width": 1.8,
            "ytick.major.width": 1.8,
            "xtick.minor.size": 4,
            "ytick.minor.size": 4,
            "xtick.minor.width": 1.2,
            "ytick.minor.width": 1.2,
            "xtick.minor.visible": True,
            "ytick.minor.visible": True,
            "lines.linewidth": 2.5,
            "lines.markersize": 10,
            "lines.markeredgewidth": 1.5,
            "patch.linewidth": 1.0,
            "legend.frameon": True,
            "legend.framealpha": 0.95,
            "legend.fancybox": False,
            "legend.edgecolor": "black",
            "legend.shadow": False,
            "errorbar.capsize": 4,
        }
    )


def save_single_plot(fig: plt.Figure, filename: str, output_dir: Path | None = None) -> Path:
    """Save a single plot as PDF only."""
    if output_dir is None:
        output_dir = SINGLE_PLOT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{filename}.pdf"
    fig.savefig(output_path, format="pdf", bbox_inches="tight")
    print(f"   [OK] Saved: {output_path}")
    plt.close(fig)
    return output_path


# =============================================================================
# DATA PREPARATION
# =============================================================================


def prepare_scaling_data_60s() -> pd.DataFrame:
    """Prepare merged QPU + Gurobi 60s data for scaling plots."""
    qpu_df = load_qpu_hierarchical()
    gurobi_df = load_gurobi_60s()

    results = []
    for _, row in qpu_df.iterrows():
        sc = row["scenario_name"]
        gur = gurobi_df[gurobi_df["scenario_name"] == sc]
        if len(gur) == 0:
            continue
        gur = gur.iloc[0]

        results.append(
            {
                "scenario_name": sc,
                "n_vars": row["n_vars"],
                "n_farms": row["n_farms"],
                "n_foods": row["n_foods"],
                "formulation": row["formulation"],
                "qpu_objective": abs(row["objective_miqp"]),
                "gurobi_objective": gur["objective_miqp"],
                "qpu_total_time": row["total_wall_time"],
                "qpu_access_time": row["qpu_access_time"],
                "gurobi_time": gur["total_wall_time"],
                "gurobi_timeout": gur["hit_timeout"],
            }
        )

    return pd.DataFrame(results).sort_values("n_vars").reset_index(drop=True)


def load_study1_hybrid_data() -> dict | None:
    """
    Load Study 1: Comprehensive benchmark data (CQM/BQM vs Gurobi).

    Returns a dictionary with aggregated data by problem scale (n_patches).
    """
    candidates = list(STUDY1_BENCHMARK_DIR.glob("comprehensive_benchmark_configs_dwave_*.json"))
    if not candidates:
        print("  [WARN] No comprehensive benchmark files found for Study 1")
        return None

    best_file = max(candidates, key=lambda p: p.stat().st_size)
    try:
        with open(best_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [WARN] Error loading Study 1 data: {e}")
        return None

    # Load Gurobi ground_truth from QPU benchmark files (for consistency)
    gurobi_ground_truth: dict[int, dict] = {}
    for qpu_file in sorted(QPU_BENCHMARK_DIR.glob("qpu_benchmark_*.json")):
        try:
            with open(qpu_file, "r", encoding="utf-8") as f:
                qpu_data = json.load(f)
            for result in qpu_data.get("results", []):
                n_farms = result.get("n_farms", 0)
                gt = result.get("ground_truth", {})
                if gt and n_farms > 0:
                    gurobi_ground_truth[n_farms] = {
                        "time": gt.get("solve_time", 0),
                        "obj": gt.get("objective", 0),
                    }
        except Exception:
            pass

    patch_results = data.get("patch_results", [])
    if not patch_results:
        return None

    data_by_size: dict[int, dict] = {}
    for r in patch_results:
        n_units = r.get("n_units", 0)
        if n_units not in data_by_size:
            data_by_size[n_units] = {
                "gurobi_time": [], "gurobi_obj": [],
                "dwave_cqm_time": [], "dwave_cqm_obj": [],
                "dwave_cqm_qpu": [], "dwave_cqm_total": [],
                "gurobi_qubo_time": [], "gurobi_qubo_obj": [],
                "dwave_bqm_time": [], "dwave_bqm_obj": [],
                "dwave_bqm_qpu": [], "dwave_bqm_total": [],
            }

        solvers = r.get("solvers", {})

        if n_units in gurobi_ground_truth:
            gt = gurobi_ground_truth[n_units]
            if gt["time"] > 0:
                data_by_size[n_units]["gurobi_time"].append(gt["time"])
                data_by_size[n_units]["gurobi_obj"].append(gt["obj"])

        if "dwave_cqm" in solvers:
            total_time = solvers["dwave_cqm"].get("hybrid_time", 0)
            qpu_time = solvers["dwave_cqm"].get("qpu_time", 0)
            obj = solvers["dwave_cqm"].get("objective_value", 0)
            if total_time > 0:
                data_by_size[n_units]["dwave_cqm_time"].append(total_time)
                data_by_size[n_units]["dwave_cqm_obj"].append(obj)
                data_by_size[n_units]["dwave_cqm_qpu"].append(qpu_time)
                data_by_size[n_units]["dwave_cqm_total"].append(total_time)

        if "gurobi_qubo" in solvers and solvers["gurobi_qubo"].get("success"):
            data_by_size[n_units]["gurobi_qubo_time"].append(
                solvers["gurobi_qubo"].get("solve_time", 0)
            )
            data_by_size[n_units]["gurobi_qubo_obj"].append(
                solvers["gurobi_qubo"].get("objective_value", 0)
            )

        if "dwave_bqm" in solvers:
            total_time = solvers["dwave_bqm"].get("hybrid_time", 0)
            qpu_time = solvers["dwave_bqm"].get("qpu_time", 0)
            obj = solvers["dwave_bqm"].get("objective_value", 0)
            if total_time > 0:
                data_by_size[n_units]["dwave_bqm_time"].append(total_time)
                data_by_size[n_units]["dwave_bqm_obj"].append(obj)
                data_by_size[n_units]["dwave_bqm_qpu"].append(qpu_time)
                data_by_size[n_units]["dwave_bqm_total"].append(total_time)

    # Include all scales that have any data (not just those with Gurobi ground truth)
    n_patches = sorted(data_by_size.keys())
    if not n_patches:
        return None

    result = {
        "n_patches": n_patches,
        "gurobi_cqm_time": [
            np.mean(data_by_size[n]["gurobi_time"]) if data_by_size[n]["gurobi_time"] else np.nan
            for n in n_patches
        ],
        "gurobi_cqm_obj": [
            np.mean(data_by_size[n]["gurobi_obj"]) if data_by_size[n]["gurobi_obj"] else np.nan
            for n in n_patches
        ],
        "dwave_cqm_time": [
            np.mean(data_by_size[n]["dwave_cqm_time"]) if data_by_size[n]["dwave_cqm_time"] else np.nan
            for n in n_patches
        ],
        "dwave_cqm_obj": [
            np.mean(data_by_size[n]["dwave_cqm_obj"]) if data_by_size[n]["dwave_cqm_obj"] else np.nan
            for n in n_patches
        ],
        "gurobi_qubo_time": [
            np.mean(data_by_size[n]["gurobi_qubo_time"]) if data_by_size[n]["gurobi_qubo_time"] else np.nan
            for n in n_patches
        ],
        "gurobi_qubo_obj": [
            np.mean(data_by_size[n]["gurobi_qubo_obj"]) if data_by_size[n]["gurobi_qubo_obj"] else np.nan
            for n in n_patches
        ],
        "dwave_bqm_time": [
            np.mean(data_by_size[n]["dwave_bqm_time"]) if data_by_size[n]["dwave_bqm_time"] else np.nan
            for n in n_patches
        ],
        "dwave_bqm_obj": [
            np.mean(data_by_size[n]["dwave_bqm_obj"]) if data_by_size[n]["dwave_bqm_obj"] else np.nan
            for n in n_patches
        ],
        "dwave_cqm_qpu_pct": [
            100 * np.mean(data_by_size[n]["dwave_cqm_qpu"]) / np.mean(data_by_size[n]["dwave_cqm_total"])
            if data_by_size[n]["dwave_cqm_total"] and np.mean(data_by_size[n]["dwave_cqm_total"]) > 0
            else np.nan
            for n in n_patches
        ],
        "dwave_bqm_qpu_pct": [
            100 * np.mean(data_by_size[n]["dwave_bqm_qpu"]) / np.mean(data_by_size[n]["dwave_bqm_total"])
            if data_by_size[n]["dwave_bqm_total"] and np.mean(data_by_size[n]["dwave_bqm_total"]) > 0
            else np.nan
            for n in n_patches
        ],
    }

    return result


# =============================================================================
# SCALING PLOTS (5 plots)
# =============================================================================


def plot_scaling_objectives_by_vars(df: pd.DataFrame, output_dir: Path | None = None) -> Path:
    """Objectives comparison by number of variables."""
    fig, ax = plt.subplots(figsize=(10, 7))
    for formulation in ["6-Food", "27-Food (Agg.)"]:
        form_df = df[df["formulation"] == formulation].sort_values("n_vars")
        if len(form_df) > 0:
            color = FORMULATION_COLORS.get(formulation, "gray")
            ax.plot(form_df["n_vars"], form_df["qpu_objective"],
                    marker=MARKERS.get(formulation, "o"), color=color,
                    label=f"{formulation} (QPU)", linewidth=3, markersize=12, alpha=0.8)
            ax.plot(form_df["n_vars"], form_df["gurobi_objective"],
                    marker=MARKERS.get(formulation, "o"), color=SOLVER_COLORS["gurobi"],
                    label=f"{formulation} (Gurobi)", linewidth=3, markersize=10, alpha=0.8, linestyle=":")
    ax.set_xlabel("Number of Variables")
    ax.set_ylabel("Objective Value (|abs|)")
    ax.set_title("Solution Quality: Classical vs Quantum")
    ax.legend(loc="upper left", fontsize=14)
    ax.grid(True, alpha=0.3)
    return save_single_plot(fig, "scaling_objectives_by_vars", output_dir)


def plot_scaling_objectives_by_farms(df: pd.DataFrame, output_dir: Path | None = None) -> Path:
    """Objectives comparison by number of farms."""
    fig, ax = plt.subplots(figsize=(10, 7))
    for formulation in ["6-Food", "27-Food (Agg.)"]:
        form_df = df[df["formulation"] == formulation].sort_values("n_farms")
        if len(form_df) > 0:
            color = FORMULATION_COLORS.get(formulation, "gray")
            ax.plot(form_df["n_farms"], form_df["qpu_objective"],
                    marker=MARKERS.get(formulation, "o"), color=color,
                    label=f"{formulation} (QPU)", linewidth=3, markersize=12, alpha=0.8)
            ax.plot(form_df["n_farms"], form_df["gurobi_objective"],
                    marker=MARKERS.get(formulation, "o"), color=SOLVER_COLORS["gurobi"],
                    label=f"{formulation} (Gurobi)", linewidth=3, markersize=10, alpha=0.8, linestyle=":")
    ax.set_xlabel("Number of Farms")
    ax.set_ylabel("Objective Value (|abs|)")
    ax.set_title("Solution Quality: Classical vs Quantum (by Farms)")
    ax.legend(loc="upper left", fontsize=14)
    ax.grid(True, alpha=0.3)
    return save_single_plot(fig, "scaling_objectives_by_farms", output_dir)


def plot_scaling_qpu_breakdown_by_vars(df: pd.DataFrame, output_dir: Path | None = None) -> Path:
    """QPU Time breakdown by number of variables."""
    fig, ax = plt.subplots(figsize=(10, 7))
    for formulation in ["6-Food", "27-Food (Agg.)"]:
        form_df = df[df["formulation"] == formulation].sort_values("n_vars")
        if len(form_df) > 0:
            color = FORMULATION_COLORS.get(formulation, "gray")
            ax.plot(form_df["n_vars"], form_df["qpu_total_time"],
                    marker=MARKERS.get(formulation, "o"), color=color,
                    label=f"{formulation} (Total)", linewidth=3, markersize=12, alpha=0.8)
            ax.plot(form_df["n_vars"], form_df["qpu_access_time"],
                    marker=MARKERS.get(formulation, "o"), color=color,
                    label=f"{formulation} (Pure QPU)", linewidth=3, markersize=10,
                    alpha=0.6, linestyle="--")
            ax.plot(form_df["n_vars"], form_df["gurobi_time"],
                    marker=MARKERS.get(formulation, "o"), color=SOLVER_COLORS["gurobi"],
                    label=f"{formulation} (Gurobi)", linewidth=3, markersize=10,
                    alpha=0.8, linestyle=":")
    ax.set_xlabel("Number of Variables")
    ax.set_ylabel("Time (seconds)")
    ax.set_title("QPU Time Breakdown: Total vs Pure Quantum")
    ax.legend(loc="upper left", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.set_yscale("log")
    ylim = ax.get_ylim()
    ax.set_ylim(ylim[0], ylim[1] * 10)
    return save_single_plot(fig, "scaling_qpu_breakdown_by_vars", output_dir)


def plot_scaling_qpu_breakdown_by_farms(df: pd.DataFrame, output_dir: Path | None = None) -> Path:
    """QPU Time breakdown by number of farms."""
    fig, ax = plt.subplots(figsize=(10, 7))
    for formulation in ["6-Food", "27-Food (Agg.)"]:
        form_df = df[df["formulation"] == formulation].sort_values("n_farms")
        if len(form_df) > 0:
            color = FORMULATION_COLORS.get(formulation, "gray")
            ax.plot(form_df["n_farms"], form_df["qpu_total_time"],
                    marker=MARKERS.get(formulation, "o"), color=color,
                    label=f"{formulation} (Total)", linewidth=3, markersize=12, alpha=0.8)
            ax.plot(form_df["n_farms"], form_df["qpu_access_time"],
                    marker=MARKERS.get(formulation, "o"), color=color,
                    label=f"{formulation} (Pure QPU)", linewidth=3, markersize=10,
                    alpha=0.6, linestyle="--")
            ax.plot(form_df["n_farms"], form_df["gurobi_time"],
                    marker=MARKERS.get(formulation, "o"), color=SOLVER_COLORS["gurobi"],
                    label=f"{formulation} (Gurobi)", linewidth=3, markersize=10,
                    alpha=0.8, linestyle=":")
    ax.set_xlabel("Number of Farms")
    ax.set_ylabel("Time (seconds)")
    ax.set_title("Solve Time Breakdown (by Farms)")
    ax.legend(loc="upper left", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.set_yscale("log")
    ylim = ax.get_ylim()
    ax.set_ylim(ylim[0], ylim[1] * 5)
    return save_single_plot(fig, "scaling_qpu_breakdown_by_farms", output_dir)


# =============================================================================
# STUDY 1: HYBRID PERFORMANCE (combined 2-panel figure)
# =============================================================================


def plot_study1_hybrid_performance(hybrid_data: dict | None, output_dir: Path | None = None) -> Path:
    """Create Study 1: Hybrid Solver Performance (2-panel figure)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    if hybrid_data is None:
        ax1.text(0.5, 0.5, "Data not available", ha="center", va="center",
                 transform=ax1.transAxes, fontsize=18)
        ax2.text(0.5, 0.5, "Data not available", ha="center", va="center",
                 transform=ax2.transAxes, fontsize=18)
        fig.suptitle("Study 1: Hybrid Solver Performance", fontsize=20, fontweight="bold")
        return save_single_plot(fig, "study1_hybrid_performance", output_dir)

    n_patches = hybrid_data["n_patches"]

    # Panel A: Solve time comparison (log-log)
    ax1.loglog(n_patches, hybrid_data["gurobi_cqm_time"],
               "o-", color=SOLVER_COLORS["gurobi"], linewidth=2.5, markersize=10,
               label="Gurobi (CQM)", markeredgecolor="white", markeredgewidth=0.5)
    ax1.loglog(n_patches, hybrid_data["dwave_cqm_time"],
               "s-", color=SOLVER_COLORS.get("cqm", "#3498db"), linewidth=2.5, markersize=10,
               label="D-Wave CQM", markeredgecolor="white", markeredgewidth=0.5)
    ax1.loglog(n_patches, hybrid_data["gurobi_qubo_time"],
               "^-", color="#27ae60", linewidth=2.5, markersize=10,
               label="Gurobi (QUBO)", markeredgecolor="white", markeredgewidth=0.5)
    ax1.loglog(n_patches, hybrid_data["dwave_bqm_time"],
               "v-", color=SOLVER_COLORS.get("bqm", "#e74c3c"), linewidth=2.5, markersize=10,
               label="D-Wave BQM", markeredgecolor="white", markeredgewidth=0.5)
    ax1.axhline(y=300, color="gray", linestyle="--", linewidth=1, alpha=0.7, label="Timeout (300s)")
    ax1.set_xlabel("Number of Patches", fontweight="bold")
    ax1.set_ylabel("Solve Time (s)", fontweight="bold")
    ax1.set_title("(a) Solver Performance Scaling", fontweight="bold")
    ax1.legend(loc="upper left", frameon=True, framealpha=0.95, fontsize=14)
    ax1.grid(True, which="both", alpha=0.3, linestyle="-", linewidth=0.5)

    # Panel B: QPU % of total time
    x = np.arange(len(n_patches))
    width = 0.35
    ax2.bar(x - width / 2, hybrid_data["dwave_cqm_qpu_pct"], width,
            color=SOLVER_COLORS.get("cqm", "#3498db"), label="D-Wave CQM",
            alpha=0.8, edgecolor="white", linewidth=0.5)
    ax2.bar(x + width / 2, hybrid_data["dwave_bqm_qpu_pct"], width,
            color=SOLVER_COLORS.get("bqm", "#e74c3c"), label="D-Wave BQM",
            alpha=0.8, edgecolor="white", linewidth=0.5)
    ax2.set_xlabel("Number of Patches", fontweight="bold")
    ax2.set_ylabel("QPU Time (% of Total)", fontweight="bold")
    ax2.set_title("(b) QPU Utilization", fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(n) for n in n_patches])
    ax2.legend(loc="upper right", frameon=True, framealpha=0.95, fontsize=14)
    ax2.grid(True, axis="y", alpha=0.3, linestyle="-", linewidth=0.5)

    fig.suptitle("Study 1: Hybrid Solver Performance", fontsize=22, fontweight="bold", y=1.02)
    plt.tight_layout()
    return save_single_plot(fig, "study1_hybrid_performance", output_dir)


# =============================================================================
# CROP BENEFIT HEATMAP
# =============================================================================


def load_food_data_for_heatmap(excel_path: Path | None = None) -> pd.DataFrame:
    """Load food data from Excel file for benefit heatmap."""
    if excel_path is None:
        excel_path = FOOD_DATA_EXCEL
    return pd.read_excel(excel_path)


def generate_weight_combinations_for_heatmap(
    step: float = 0.1, n_weights: int = 5
) -> list[tuple]:
    """Generate all weight combinations that sum to 1."""
    values = np.arange(0, 1 + step / 2, step)
    values = np.round(values, 2)
    valid_combinations = []
    for combo in itertools.product(values, repeat=n_weights):
        if abs(sum(combo) - 1.0) < 1e-9:
            valid_combinations.append(combo)
    return valid_combinations


def calculate_benefit_for_heatmap(food_data: dict, weights: dict) -> float:
    """Calculate composite benefit score for a food."""
    return (
        weights["nutritional_value"] * food_data["nutritional_value"]
        + weights["nutrient_density"] * food_data["nutrient_density"]
        - weights["environmental_impact"] * food_data["environmental_impact"]
        + weights["affordability"] * food_data["affordability"]
        + weights["sustainability"] * food_data["sustainability"]
    )


def analyze_crop_benefits_for_heatmap(
    df: pd.DataFrame, step: float = 0.1
) -> tuple[pd.DataFrame, list[str]]:
    """Analyze crop benefits for all weight combinations."""
    weight_names = [
        "nutritional_value",
        "nutrient_density",
        "environmental_impact",
        "affordability",
        "sustainability",
    ]
    combinations = generate_weight_combinations_for_heatmap(step=step)

    foods = {}
    for _, row in df.iterrows():
        foods[row["Food_Name"]] = {
            "nutritional_value": row["nutritional_value"],
            "nutrient_density": row["nutrient_density"],
            "environmental_impact": row["environmental_impact"],
            "affordability": row["affordability"],
            "sustainability": row["sustainability"],
        }

    foods_list = list(foods.keys())
    results = []
    for combo in combinations:
        weights = dict(zip(weight_names, combo))
        benefits = {}
        for food_name, food_data in foods.items():
            benefits[food_name] = calculate_benefit_for_heatmap(food_data, weights)
        results.append({"weights": combo, "benefits": benefits})

    return pd.DataFrame(results), foods_list


def plot_benefit_heatmap(output_dir: Path | None = None) -> Path:
    """Generate heatmap showing crop benefits across weight combinations."""
    food_df = load_food_data_for_heatmap()
    results_df, foods_list = analyze_crop_benefits_for_heatmap(food_df, step=0.1)

    n_samples = 100
    sample_indices = np.linspace(0, len(results_df) - 1, n_samples, dtype=int)
    sampled = results_df.iloc[sample_indices]

    benefit_matrix = np.zeros((len(foods_list), n_samples))
    for j, (_, row) in enumerate(sampled.iterrows()):
        for i, food in enumerate(foods_list):
            benefit_matrix[i, j] = row["benefits"][food]

    fig, ax = plt.subplots(figsize=(16, 10), constrained_layout=False)
    im = ax.imshow(benefit_matrix, aspect="auto", cmap="RdBu_r", interpolation="nearest")
    ax.set_yticks(range(len(foods_list)))
    ax.set_yticklabels(foods_list, fontsize=14)
    ax.set_xlabel("Weight Combination Index (sampled)")
    ax.set_ylabel("Crop")
    ax.set_title("Crop Benefits Across Weight Combinations")
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Benefit Score")
    cbar.ax.tick_params(labelsize=16)
    fig.tight_layout()
    return save_single_plot(fig, "crop_benefit_heatmap", output_dir)


# =============================================================================
# MAIN
# =============================================================================


def generate_all_single_plots() -> dict[str, bool]:
    """Generate all individual PDF plots."""
    setup_large_font_style()

    results: dict[str, bool] = {}
    output_dir = SINGLE_PLOT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("GENERATING SINGLE-PLOT PDFs")
    print("=" * 80)
    print(f"Output directory: {output_dir}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load shared data
    print("Loading shared data...")
    df_60s = None
    try:
        df_60s = prepare_scaling_data_60s()
        print(f"  [OK] 60s scaling data: {len(df_60s)} scenarios")
    except Exception as e:
        print(f"  [FAIL] Failed to load 60s data: {e}")

    hybrid_data = None
    try:
        hybrid_data = load_study1_hybrid_data()
        if hybrid_data:
            print(f"  [OK] Study 1 hybrid data: {len(hybrid_data['n_patches'])} scales")
        else:
            print("  [WARN] Study 1 hybrid data not available")
    except Exception as e:
        print(f"  [FAIL] Failed to load Study 1 hybrid data: {e}")

    print()

    plot_functions = [
        ("scaling_objectives_by_vars", lambda: plot_scaling_objectives_by_vars(df_60s, output_dir)),
        ("scaling_objectives_by_farms", lambda: plot_scaling_objectives_by_farms(df_60s, output_dir)),
        ("scaling_qpu_breakdown_by_vars", lambda: plot_scaling_qpu_breakdown_by_vars(df_60s, output_dir)),
        ("scaling_qpu_breakdown_by_farms", lambda: plot_scaling_qpu_breakdown_by_farms(df_60s, output_dir)),
        ("study1_hybrid_performance", lambda: plot_study1_hybrid_performance(hybrid_data, output_dir)),
        ("crop_benefit_heatmap", lambda: plot_benefit_heatmap(output_dir)),
    ]

    for name, func in plot_functions:
        print(f"Generating: {name}...")
        try:
            func()
            results[name] = True
        except Exception as e:
            results[name] = False
            print(f"  [FAIL] {name}: {e}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    successful = sum(results.values())
    total = len(results)
    print(f"Completed: {successful}/{total} plots generated successfully")

    failed = [name for name, success in results.items() if not success]
    if failed:
        print("Failed plots:")
        for name in failed:
            print(f"  - {name}")

    print(f"\nOutput directory: {output_dir}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    return results


def main() -> None:
    """Entry point."""
    generate_all_single_plots()


if __name__ == "__main__":
    main()
