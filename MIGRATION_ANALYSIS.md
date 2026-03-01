# Migration Analysis: OQI-UC002-DWave → UC002-Food-Production-Optimization

> **Date**: 2026-02-27  
> **Reference**: `@todo/report/content_report.tex` (Phase 3 & 4 Report)  
> **Goal**: Identify all files needed to reproduce the three studies in the report, migrate them to a clean repo.

---

## Studies to Reproduce

| Study | Description | Problem Variant | Key Outputs |
|-------|------------|-----------------|-------------|
| **Study 1** | Hybrid Solver Benchmarking | Variant A (Binary Crop Allocation, 27 crops) | Tables 5–10, Figure 1 |
| **Study 2** | Pure QPU Decomposition Methods | Variant A (8 decomposition strategies) | Tables 11–14, Figures 2–4 |
| **Study 3** | Quantum Advantage on Rotation | Variant B (Multi-Period Rotation, 6 crop families) | Tables 15–19, Figures 5–8 |
| **Appendix** | Crop Benefit Sensitivity Analysis | N/A | Figures 9–17, Table 20 |

---

## FILE-BY-FILE ANALYSIS

### Legend
- ✅ **ESSENTIAL** — Required to reproduce results
- ⚠️ **SUPPORTING** — Useful but not strictly required (tests, legacy alternatives)
- ❌ **NOT NEEDED** — Debug scripts, one-off investigations, scratch files

---

### 1. CONFIGURATION / ENVIRONMENT

| File | Verdict | Claim |
|------|---------|-------|
| `requirements.yml` | ✅ ESSENTIAL | Defines conda environment. Missing D-Wave/Gurobi deps — needs cleanup but is the canonical env file. |
| `requirements_conda_fix.yml` | ✅ ESSENTIAL | Practical variant of requirements. Also missing D-Wave/Gurobi. |
| `.gitignore` | ✅ ESSENTIAL | Defines repo ignore patterns (Constraints/, CQM_Models/, DWave_Results/, PuLP_Results/, .pickle, .cqm). |
| `.gitmodules` | ❌ NOT NEEDED | References `external/Benchmark_Naeimeh` which is set to `ignore = all`. Not used by any study. |
| `formulations.tex` | ✅ ESSENTIAL | Canonical mathematical formulation document. Referenced by code and report. |

---

### 2. CORE SOURCE CODE — `src/`

| File | Verdict | Study | Claim |
|------|---------|-------|-------|
| `src/__init__.py` | ✅ ESSENTIAL | All | Package init, required for imports. |
| `src/data_models.py` | ✅ ESSENTIAL | All | Defines `OptimizationObjective` enum and `OptimizationResult` dataclass used throughout. |
| `src/scenarios.py` | ✅ ESSENTIAL | All | **Master scenario loader** (~2768 lines). `load_food_data()` dispatches to 30+ scenario generators. Generates farm data, food attributes, constraints for all studies. |
| `src/synergy_optimizer_pure.py` | ✅ ESSENTIAL | 1 | Pure-Python synergy pair precomputation. Used by LQ formulation in Study 1. |
| `src/synergy_optimizer.pyx` | ⚠️ SUPPORTING | 1 | Cython compiled version of synergy optimizer. Optional — pure Python fallback exists. |
| `src/fast_rotation_bqm.pyx` | ⚠️ SUPPORTING | 3 | Cython extension for fast BQM building. Optional — Python fallback exists. |
| `src/qbsolv_runner.py` | ❌ NOT NEEDED | — | Legacy wrapper for external qbsolv binary. Not used by any study. |
| `src/setup.py` | ⚠️ SUPPORTING | — | Build script for optional Cython extensions. |
| `src/setup_fast_rotation.py` | ⚠️ SUPPORTING | — | Build script for optional fast_rotation_bqm Cython extension. |
| `src/utils/plotting.py` | ❌ NOT NEEDED | — | Stub with mostly `pass` implementations. |

---

### 3. D-WAVE INTEGRATION — `my_functions/`

| File | Verdict | Study | Claim |
|------|---------|-------|-------|
| `my_functions/__init__.py` | ✅ ESSENTIAL | All | Package init. |
| `my_functions/qubo_converter.py` | ✅ ESSENTIAL | 1, 2 | QUBO converter: CQM→BQM conversion, variable encoding, constraint penalties. 843 lines. |
| `my_functions/dwave_qpu_adapter.py` | ✅ ESSENTIAL | All | Core D-Wave QPU interface: BQM/CQM building, QPU/hybrid/SA solver, embedding, chain strength. 1613 lines. |

---

### 4. UNIFIED BENCHMARK FRAMEWORK — `unified_benchmark/`

| File | Verdict | Study | Claim |
|------|---------|-------|-------|
| `unified_benchmark/__init__.py` | ✅ ESSENTIAL | 3 | Package exports for Study 3 framework. |
| `unified_benchmark/core.py` | ✅ ESSENTIAL | 3 | JSON schema, RunEntry/TimingInfo/DecompositionInfo/ConstraintViolations dataclasses, MIQP default params (γ_rot=0.2, γ_spat=0.1, λ_oh=3.0). |
| `unified_benchmark/scenarios.py` | ✅ ESSENTIAL | 3 | Scenario loading for Study 3: wraps `src/scenarios.py`, defines 6-family + 27-food scenarios, builds rotation matrices and spatial neighbors. |
| `unified_benchmark/miqp_scorer.py` | ✅ ESSENTIAL | 3 | **True MIQP objective recomputation** matching formulations.tex: benefit + temporal synergy + spatial synergy − one-hot penalty + diversity bonus. Also `check_constraints()`. |
| `unified_benchmark/gurobi_solver.py` | ✅ ESSENTIAL | 3 | Gurobi ground truth solver: full MIQP with rotation/spatial synergies. Classical baseline for Study 3. |
| `unified_benchmark/quantum_solvers.py` | ✅ ESSENTIAL | 3 | Three quantum/SA solvers: `qpu-native-6-family`, `qpu-hierarchical-aggregated`, `qpu-hybrid-27-food`. 1283 lines. |

---

### 5. UTILITY MODULES — `Utils/`

| File | Verdict | Study | Claim |
|------|---------|-------|-------|
| `Utils/__init__.py` | ✅ ESSENTIAL | All | Package init exporting samplers, cache, validators. |
| `Utils/farm_sampler.py` | ✅ ESSENTIAL | 1 | Generates realistic farm size distributions (Indonesian class-based model). |
| `Utils/patch_sampler.py` | ✅ ESSENTIAL | 1, 2 | Generates patch-level land distributions. |
| `Utils/crop_aggregation.py` | ✅ ESSENTIAL | 3 | **Canonical 27→6 family mapping**: `CROP_TO_FAMILY_MAPPING`, benefit aggregation, reverse mapping. |
| `Utils/rotation_matrix.py` | ✅ ESSENTIAL | 1, 3 | Builds crop×crop rotation synergy matrix R from embedded nutritional data. |
| `Utils/benchmark_cache.py` | ✅ ESSENTIAL | 1 | Cache manager for benchmark results. |
| `Utils/constraint_validator.py` | ✅ ESSENTIAL | 1, 2 | Validates BQM_PATCH solutions: at-most-one, linking, food group constraints. |
| `Utils/Grid_Refinement.py` | ✅ ESSENTIAL | Appendix | Referenced by report appendix (Grid Refinement Analysis). |
| `Utils/farm_sampler.py` | ✅ ESSENTIAL | 1 | Farm size distribution sampling. |
| `Utils/verifier.py` | ⚠️ SUPPORTING | 1 | Professional verification of solutions. Not strictly needed for reproduction. |
| `Utils/validate_cqm_vs_pulp.py` | ⚠️ SUPPORTING | 1 | Pre-submission validation. |
| `Utils/enhanced_dwave_solver.py` | ⚠️ SUPPORTING | 1, 2 | Enhanced BQM solver with repair. |
| `Utils/piecewise_approximation.py` | ⚠️ SUPPORTING | 1 (NLN) | SOS2 approximation for power functions. Only needed for NLN formulation variant. |
| `Utils/save_dwave_sampleset.py` | ⚠️ SUPPORTING | 1, 2 | Saves D-Wave results to CSV. |
| All `analyze_*.py`, `diagnose_*.py`, `check_*.py` in Utils/ | ❌ NOT NEEDED | — | One-off diagnostic/analysis scripts. |

---

### 6. @todo/ — KEY ALGORITHM IMPLEMENTATIONS (Studies 2 & 3)

| File | Verdict | Study | Claim |
|------|---------|-------|-------|
| `@todo/food_grouping.py` | ✅ ESSENTIAL | 3 | Food→family mapping module: `FOOD_TO_FAMILY`, `FAMILY_ORDER`, `aggregate_foods_to_families()`, `create_family_rotation_matrix()`. Imported by unified_benchmark. |
| `@todo/hierarchical_quantum_solver.py` | ✅ ESSENTIAL | 3 | **Hierarchical 3-level solver**: crop aggregation + spatial decomposition + QPU/SA subproblems + post-processing. Core of Study 3 QPU results. |
| `@todo/hybrid_formulation.py` | ✅ ESSENTIAL | 3 | Hybrid formulation with 27-food variables and 6-family synergy matrices. DWaveCliqueSampler with spatial decomposition. |
| `@todo/qpu_benchmark.py` | ✅ ESSENTIAL | 2 | **QPU-only benchmark v2.0**: Direct QPU + 8 decomposition strategies (PlotBased, Multilevel, Louvain, Spectral, CQM-First, Coordinated, HybridGrid). 5639 lines. |
| `@todo/decomposition_strategies.py` | ✅ ESSENTIAL | 2 | Unified decomposition strategy interface (factory pattern). |
| `@todo/formulation_builders.py` | ✅ ESSENTIAL | 1, 2 | Unified CQM/BQM builders for Farm, Patch, Direct BQM, Ultra-Sparse formulations. |
| `@todo/gurobi_scaling_benchmark.py` | ✅ ESSENTIAL | 1 | Gurobi scaling benchmark: MIP vs BP formulation comparison. Produces Table 6 (Gurobi QUBO degradation). |
| `@todo/data_loader_utils.py` | ⚠️ SUPPORTING | 3 | Data loading utilities. May be imported by other essential files. |
| `@todo/hard_scenarios.py` | ⚠️ SUPPORTING | 3 | Hard scenario generation. |
| All `test_*.py`, `debug_*.py`, `analyze_*.py`, `investigate_*.py`, `verify_*.py` in @todo/ | ❌ NOT NEEDED | — | ~200+ one-off debugging/investigation/validation scripts. |
| All `*.md` reports in @todo/ (~50+ files) | ❌ NOT NEEDED | — | Investigation notes, analysis reports, session summaries. |
| All `*.json` benchmark results in @todo/ (~150+ files) | ❌ NOT NEEDED | — | Cached benchmark runs. Regenerable from scripts. |
| All `*.tex`, `*.pdf`, `*.log`, `*.aux` in @todo/ (non-report) | ❌ NOT NEEDED | — | Intermediate LaTeX artifacts. |

---

### 7. BENCHMARK SCRIPTS — `Benchmark Scripts/`

| File | Verdict | Study | Claim |
|------|---------|-------|-------|
| `Benchmark Scripts/solver_runner.py` | ✅ ESSENTIAL | 1 | Original CQM solver runner: scenario → CQM → PuLP/D-Wave hybrid. |
| `Benchmark Scripts/solver_runner_BINARY.py` | ✅ ESSENTIAL | 1 | Binary-only formulation (plot-level): CQM→BQM conversion + HybridBQM. |
| `Benchmark Scripts/solver_runner_BQUBO.py` | ✅ ESSENTIAL | 1 | Binary QUBO variant. |
| `Benchmark Scripts/solver_runner_LQ.py` | ✅ ESSENTIAL | 1 | Linear-Quadratic objective with synergy bonus. |
| `Benchmark Scripts/solver_runner_NLD.py` | ⚠️ SUPPORTING | 1 | Non-Linear Density (MINLP). Not featured prominently in final report. |
| `Benchmark Scripts/solver_runner_NLN.py` | ⚠️ SUPPORTING | 1 | Non-Linear Nutrient objective. Not featured prominently in final report. |
| `Benchmark Scripts/solver_runner_PATCH.py` | ✅ ESSENTIAL | 1 | Patch-level binary formulation — this is the main Study 1 formulation. |
| `Benchmark Scripts/solver_runner_ROTATION.py` | ✅ ESSENTIAL | 1, 3 | 3-period crop rotation solver. 2904 lines. |
| `Benchmark Scripts/benchmarks.py` | ✅ ESSENTIAL | 1 | Scalability benchmark driver: 40 configs from 5 to 1535 farms. |
| `Benchmark Scripts/rotation_benchmark.py` | ✅ ESSENTIAL | 1 | 3-period rotation benchmark across multiple configs. |
| `Benchmark Scripts/comprehensive_benchmark.py` | ✅ ESSENTIAL | 1 | Comprehensive Farm+Patch comparison: 6 solver configs × 8 scaling points. |
| `Benchmark Scripts/benchmark_scalability_LQ.py` | ⚠️ SUPPORTING | 1 | LQ-specific scalability. |
| `Benchmark Scripts/benchmark_scalability_*.py` (BQUBO, NLN, NLD, PATCH) | ⚠️ SUPPORTING | 1 | Scalability benchmarks for non-primary formulations. |
| `Benchmark Scripts/benchmark_gurobi_qubo_only.py` | ⚠️ SUPPORTING | 1 | Gurobi-on-QUBO benchmark. |
| `Benchmark Scripts/solver_runner_BQUBO.py` | ⚠️ SUPPORTING | 1 | Duplicate entry — already listed. |
| `Benchmark Scripts/debug_pyomo_values.py` | ❌ NOT NEEDED | — | Debug script. |
| `Benchmark Scripts/test_caching_improvements.py` | ❌ NOT NEEDED | — | Test script. |
| Subdirectories: `Constraints_LQ/`, `CQM_Models_LQ/`, `DWave_Results_LQ/`, `PuLP_Results_LQ/` | ❌ NOT NEEDED | — | Cached intermediate results. Regenerable. |

---

### 8. ROOT-LEVEL ENTRY POINTS

| File | Verdict | Study | Claim |
|------|---------|-------|-------|
| `unified_benchmark.py` | ✅ ESSENTIAL | 3 | **Master CLI for Study 3**: runs all 4 modes across all scenarios, outputs JSON. |
| `run_qpu_benchmarks_all_scenarios.py` | ✅ ESSENTIAL | 3 | Batch runner: all 3 QPU modes × 20 scenarios. |
| `postprocessing_repair.py` | ✅ ESSENTIAL | 3 | Classical post-processing repair for QPU one-hot violations. |
| `plot_config.py` | ✅ ESSENTIAL | All | Unified publication-quality plot config: 20-color palette, method colors, `setup_publication_style()`. |
| `crop_benefit_weight_analysis.py` | ✅ ESSENTIAL | Appendix | Generates Appendix A figures (sensitivity analysis, 10,000 random weight configs). |
| `generate_all_report_plots.py` | ✅ ESSENTIAL | All | **Master plotting script** (3625 lines). Generates all report figures. |
| `generate_study_plots.py` | ✅ ESSENTIAL | All | Study-specific plots. |
| `generate_paper_plots.py` | ✅ ESSENTIAL | 3 | Publication-quality QPU vs Gurobi plots. |
| `fast_bqm_wrapper.py` | ⚠️ SUPPORTING | 3 | Wrapper for Cython fast BQM; falls back to Python. |
| `setup_synergy.py` | ⚠️ SUPPORTING | 1 | Compiles optional Cython extension. |
| `benchmark_synergy_speed.py` | ❌ NOT NEEDED | — | Speed benchmark for synergy optimizer. |
| All other root `analyze_*.py`, `compare_*.py`, `debug_*.py`, `check_*.py`, `inspect_*.py` (~30+ files) | ❌ NOT NEEDED | — | One-off investigation scripts. |
| All `benchmark_*.json` in root (~5 files) | ❌ NOT NEEDED | — | Cached benchmark results. |
| All `*.md` in root (~20+ files) | ❌ NOT NEEDED | — | Investigation reports, analysis notes. |
| `main.tex`, `results_section.tex` | ❌ NOT NEEDED | — | Superseded by `@todo/report/content_report.tex`. |

---

### 9. DATA FILES

| File | Verdict | Study | Claim |
|------|---------|-------|-------|
| `Inputs/Combined_Food_Data.xlsx` | ✅ ESSENTIAL | All | Master food attribute data: 27 foods, 5 food groups, nutrition/env/afford/sustain scores. |
| `Inputs/NVS_12Apr2024.xlsx` | ✅ ESSENTIAL | All | Nutritional Value Scores. |
| `Inputs/PricePer100NVS_Indonesia_3Sept2024_CHF.xlsx` | ✅ ESSENTIAL | All | Price data per 100g NVS for Indonesia. |
| `Inputs/LCA results per kg & NVS.xlsx` | ✅ ESSENTIAL | All | Life Cycle Assessment results. |
| `rotation_data/rotation_crop_matrix.csv` | ✅ ESSENTIAL | 1, 3 | 27×27 crop rotation synergy matrix. |
| `rotation_data/rotation_group_matrix.csv` | ✅ ESSENTIAL | 3 | 5×5 food group rotation synergy matrix. |
| `rotation_data/group_env_means.csv` | ✅ ESSENTIAL | 3 | Group-level environmental impact means. |
| `Inputs/AffordabilityTargetFoods_FinalReport_3May2024_clean.docx` | ⚠️ SUPPORTING | — | Reference document, not parsed by code. |
| `Inputs/Nutrition Value Score_Clean_21Mar2024 (1).docx` | ⚠️ SUPPORTING | — | Reference document. |
| `Inputs/D3_5a_SMILING_FCT_Indonesia_070813_protected.xlsx` | ⚠️ SUPPORTING | — | Indonesia food composition table. May be used indirectly. |

---

### 10. REPORT / DOCUMENTATION

| File | Verdict | Study | Claim |
|------|---------|-------|-------|
| `@todo/report/content_report.tex` | ✅ ESSENTIAL | All | **Main report**. The canonical reference document. |
| `@todo/report/content_report.pdf` | ✅ ESSENTIAL | All | Compiled PDF of the report. |
| `formulations.tex` | ✅ ESSENTIAL | All | Mathematical formulations referenced by code. |

---

### 11. CACHED RESULTS — `Benchmarks/`

| Directory | Verdict | Claim |
|-----------|---------|-------|
| `Benchmarks/COMPREHENSIVE/` | ⚠️ SUPPORTING | Farm+Patch hybrid results for Study 1. Regenerable but saves D-Wave QPU budget. |
| `Benchmarks/ALL_STRATEGIES/` | ⚠️ SUPPORTING | QPU decomposition results for Study 2. Regenerable but expensive (QPU minutes). |
| `Benchmarks/ROTATION/` | ⚠️ SUPPORTING | Rotation benchmark results. |
| `Benchmarks/LQ/`, `BQUBO/`, `NLD/`, `NLN/`, `PATCH/` | ❌ NOT NEEDED | Results for non-primary formulations. |
| `Benchmarks/CUSTOM_HYBRID/`, `DECOMPOSED/` | ❌ NOT NEEDED | Results for non-study methods. |

---

### 12. DIRECTORIES FULLY EXCLUDED

| Directory | Claim |
|-----------|-------|
| `DWave_Results/` | Legacy D-Wave result pickles. Not used by current report. |
| `DWaveNotebooks/` | Tutorial Jupyter notebooks for D-Wave. |
| `Examples/` | Example scripts unrelated to studies. |
| `Legacy/` | Older implementations. |
| `KSAT/` | K-SAT experiments. Separate problem domain. |
| `Mimir/` | Submodule — separate project (nornicdb/vscode-extension). |
| `external/` | External submodule (Benchmark_Naeimeh). Not used. |
| `Phase3Report/` | Older Phase 3 report with scripts/data/plots. Superseded by `@todo/report/`. |
| `Constraints/` | Cached constraint JSON files. Regenerable. |
| `Plot Scripts/` | 30+ individual plot scripts. Superseded by `generate_all_report_plots.py`. |
| `Plots/` | ~150 generated PNG plots. Regenerable from plot scripts. |
| `Tests/` | Test scripts. Useful for CI but not for reproducing results. |
| `Latex/` | Standalone LaTeX documents (superseded by report). |
| `@todo/report/` (non-essential files) | Older report versions, presentation slides, compilation artifacts. |

---

## SUMMARY: ESSENTIAL FILE LIST

### Core Source Code (17 files)
```
src/__init__.py
src/data_models.py
src/scenarios.py
src/synergy_optimizer_pure.py
my_functions/__init__.py
my_functions/qubo_converter.py
my_functions/dwave_qpu_adapter.py
unified_benchmark/__init__.py
unified_benchmark/core.py
unified_benchmark/scenarios.py
unified_benchmark/miqp_scorer.py
unified_benchmark/gurobi_solver.py
unified_benchmark/quantum_solvers.py
Utils/__init__.py
Utils/farm_sampler.py
Utils/patch_sampler.py
Utils/crop_aggregation.py
Utils/rotation_matrix.py
Utils/benchmark_cache.py
Utils/constraint_validator.py
Utils/Grid_Refinement.py
```

### Study-Specific Algorithms (6 files)
```
@todo/food_grouping.py
@todo/hierarchical_quantum_solver.py
@todo/hybrid_formulation.py
@todo/qpu_benchmark.py
@todo/decomposition_strategies.py
@todo/formulation_builders.py
```

### Benchmark Scripts / Entry Points (14 files)
```
Benchmark Scripts/solver_runner.py
Benchmark Scripts/solver_runner_BINARY.py
Benchmark Scripts/solver_runner_BQUBO.py
Benchmark Scripts/solver_runner_LQ.py
Benchmark Scripts/solver_runner_PATCH.py
Benchmark Scripts/solver_runner_ROTATION.py
Benchmark Scripts/benchmarks.py
Benchmark Scripts/rotation_benchmark.py
Benchmark Scripts/comprehensive_benchmark.py
unified_benchmark.py
run_qpu_benchmarks_all_scenarios.py
postprocessing_repair.py
@todo/gurobi_scaling_benchmark.py
```

### Plot Generation (4 files)
```
plot_config.py
generate_all_report_plots.py
generate_study_plots.py
generate_paper_plots.py
crop_benefit_weight_analysis.py
```

### Data (7 files)
```
Inputs/Combined_Food_Data.xlsx
Inputs/NVS_12Apr2024.xlsx
Inputs/PricePer100NVS_Indonesia_3Sept2024_CHF.xlsx
Inputs/LCA results per kg & NVS.xlsx
rotation_data/rotation_crop_matrix.csv
rotation_data/rotation_group_matrix.csv
rotation_data/group_env_means.csv
```

### Config / Documentation (4 files)
```
requirements.yml
requirements_conda_fix.yml
.gitignore
formulations.tex
```

### Report (2 files)
```
@todo/report/content_report.tex
@todo/report/content_report.pdf
```

---

## TOTAL: ~52 essential files + ~7 data files = ~59 files

**vs. original repo**: Hundreds of files across dozens of directories, including ~200+ one-off scripts, ~150+ cached JSON results, ~150+ generated plots, ~50+ markdown investigation reports.

---

## MIGRATION PLAN

### New Repository Structure
```
UC002-Food-Production-Optimization/
├── src/
│   ├── __init__.py
│   ├── data_models.py
│   ├── scenarios.py
│   └── synergy_optimizer_pure.py
├── dwave_interface/                 # was: my_functions/
│   ├── __init__.py
│   ├── qubo_converter.py
│   └── dwave_qpu_adapter.py
├── unified_benchmark/
│   ├── __init__.py
│   ├── core.py
│   ├── scenarios.py
│   ├── miqp_scorer.py
│   ├── gurobi_solver.py
│   └── quantum_solvers.py
├── utils/                           # was: Utils/
│   ├── __init__.py
│   ├── farm_sampler.py
│   ├── patch_sampler.py
│   ├── crop_aggregation.py
│   ├── rotation_matrix.py
│   ├── benchmark_cache.py
│   ├── constraint_validator.py
│   └── grid_refinement.py
├── algorithms/                      # was: scattered across @todo/
│   ├── food_grouping.py
│   ├── hierarchical_quantum_solver.py
│   ├── hybrid_formulation.py
│   ├── qpu_benchmark.py
│   ├── decomposition_strategies.py
│   └── formulation_builders.py
├── benchmarks/                      # was: Benchmark Scripts/
│   ├── solver_runner.py
│   ├── solver_runner_BINARY.py
│   ├── solver_runner_BQUBO.py
│   ├── solver_runner_LQ.py
│   ├── solver_runner_PATCH.py
│   ├── solver_runner_ROTATION.py
│   ├── benchmarks.py
│   ├── rotation_benchmark.py
│   ├── comprehensive_benchmark.py
│   ├── gurobi_scaling_benchmark.py
│   ├── unified_benchmark_cli.py     # was: unified_benchmark.py (root)
│   └── run_qpu_all_scenarios.py
├── postprocessing/
│   └── repair.py                    # was: postprocessing_repair.py
├── plotting/
│   ├── plot_config.py
│   ├── generate_all_report_plots.py
│   ├── generate_study_plots.py
│   ├── generate_paper_plots.py
│   └── crop_benefit_weight_analysis.py
├── data/
│   ├── inputs/                      # was: Inputs/
│   │   ├── Combined_Food_Data.xlsx
│   │   ├── NVS_12Apr2024.xlsx
│   │   ├── PricePer100NVS_Indonesia_3Sept2024_CHF.xlsx
│   │   └── LCA results per kg & NVS.xlsx
│   └── rotation/                    # was: rotation_data/
│       ├── rotation_crop_matrix.csv
│       ├── rotation_group_matrix.csv
│       └── group_env_means.csv
├── docs/
│   ├── formulations.tex
│   └── report/
│       ├── content_report.tex
│       └── content_report.pdf
├── requirements.yml
├── requirements_conda_fix.yml
├── .gitignore
└── README.md
```

### Key Decisions
1. **Rename `my_functions/` → `dwave_interface/`** — clearer naming
2. **Merge `@todo/` algorithm files → `algorithms/`** — single location for study code
3. **Rename `Benchmark Scripts/` → `benchmarks/`** — no spaces in dir names
4. **Move plot scripts → `plotting/`** — separated from core logic
5. **Flatten data hierarchy** — `Inputs/` + `rotation_data/` → `data/inputs/` + `data/rotation/`
6. **Import paths will need updating** — this is expected; a follow-up task

### What's NOT Migrated (and why)
- **~200+ debug/investigate/analyze scripts** — one-off work, not reproducibility-relevant
- **~150+ cached JSON benchmark results** — regenerable (though costs QPU budget)
- **~50+ markdown investigation reports** — working notes, not deliverables
- **~150+ generated plot PNGs** — regenerable from plot scripts
- **Cython extensions (.pyx)** — optional optimizations with Python fallbacks
- **Submodules (external/, Mimir/)** — unrelated to studies
- **Legacy/, Examples/, KSAT/, DWaveNotebooks/** — unrelated to report

