# Implementation Plan: Repo Migration & Import Rewriting

## Goal

Migrate all 60 essential files from `OQI-UC002-DWave` to `UC002-Food-Production-Optimization` with a clean directory structure and fully updated import paths, so that every script runs from the new repo root without referencing the old layout.

## Current State Analysis

Files have been **copied** to the new structure (Phase 1 complete — 60 files, verified). However, all internal imports and path strings still reference the old layout:

| Old Path | New Path | Files Affected |
|----------|----------|----------------|
| `from my_functions.X` | `from dwave_interface.X` | 2 files |
| `from Utils.X` / `from Utils import X` | `from utils.X` / `from utils import X` | 12 files |
| `from src.scenarios` | `from src.scenarios` | **No change** (kept `src/`) |
| `from food_grouping` | `from algorithms.food_grouping` | 4 files |
| `from solver_runner` / `import solver_runner_X` | `from benchmarks.solver_runner` / relative | 5 files |
| `from plot_config` | `from plotting.plot_config` | 1 file |
| `from scenarios import` (bare) | `from unified_benchmark.scenarios import` | 1 file |
| `"Inputs/Combined_Food_Data.xlsx"` | `"data/inputs/Combined_Food_Data.xlsx"` | 15+ occurrences in `scenarios.py` |
| `"rotation_data/..."` | `"data/rotation/..."` | 3 files |
| `"Benchmark Scripts/..."` | `"benchmarks/..."` | 1 file |
| `"@todo/..."` path strings | various | 3 files (plotting) |
| `sys.path.insert(0, ...)` hacks | Remove or update | 20+ files |
| `from decomposition_X import` (bare) | Not migrated — lazy imports in factory | 1 file (low priority) |
| `from my_functions.optimization` | Missing module — legacy | 1 file |
| `from .mean_field_base` | Missing module — not migrated | 1 file |

## What We're NOT Doing

- **Not refactoring code logic** — only import paths and file/directory references
- **Not fixing legacy dead imports** (`my_functions.optimization`, `mean_field_base`) — these already have try/except fallbacks
- **Not migrating** `decomposition_benders.py`, `decomposition_admm.py`, etc. — these are lazy-imported in `decomposition_strategies.py` and were never essential for reproducibility
- **Not converting** the codebase to a proper pip-installable package (no `pyproject.toml`) — out of scope
- **Not updating** `requirements.yml` to add D-Wave/Gurobi packages — separate task

## Prerequisites

- [x] Files already copied to new structure (60 files confirmed)
- [ ] No additional files need to be copied (verified in this plan)

---

## Phase 1: Fix `sys.path` Hacks to Use New Project Root

### Overview
Most files compute `project_root` by walking up from `__file__` and insert it into `sys.path`. Since files moved from root/`@todo`/`Benchmark Scripts` into subdirectories, this pattern now points one level too deep. Each file needs its `sys.path` hack updated to reference the new repo root.

### Changes Required

#### 1.1 `benchmarks/solver_runner.py` (line 27)

**File**: `benchmarks/solver_runner.py`

Old pattern:
```python
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
```
New pattern:
```python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
```
This ensures `project_root` points to `UC002-Food-Production-Optimization/` (one level up from `benchmarks/`).

**Same pattern applies to:**
- `benchmarks/solver_runner_BINARY.py` (line 22)
- `benchmarks/solver_runner_BQUBO.py` (line 22)
- `benchmarks/solver_runner_LQ.py` (line 28)
- `benchmarks/solver_runner_PATCH.py` (line 22)
- `benchmarks/solver_runner_ROTATION.py` (line 24)

#### 1.2 `benchmarks/benchmarks.py` (line 18)

Old:
```python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```
This already points one up — **correct** (now points to repo root). **No change needed.**

**Same for:** `benchmarks/comprehensive_benchmark.py` (line 33), `benchmarks/rotation_benchmark.py` (line 33).

#### 1.3 `benchmarks/unified_benchmark_cli.py` (lines 36-37)

Old:
```python
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "unified_benchmark"))
```
`project_root` is computed as `Path(__file__).resolve().parent` — was repo root when file was in root, now it's `benchmarks/`. Fix: `parent.parent`.

#### 1.4 `algorithms/formulation_builders.py` (line 21)

Old:
```python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```
Already goes one up from `algorithms/` → repo root. **Correct. No change needed.**

#### 1.5 `algorithms/hierarchical_quantum_solver.py` (line 31)

Old:
```python
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, project_root)
```
Was in `@todo/` → `.parent.parent` went to repo root. Now in `algorithms/` → `.parent.parent` goes one level above repo. Fix: use `.parent` only.

**Same for:** `algorithms/hybrid_formulation.py` (line 34), `algorithms/qpu_benchmark.py` (line 36).

#### 1.6 `dwave_interface/dwave_qpu_adapter.py` (line 86)

Old fallback:
```python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```
Was in `my_functions/` → goes to repo root. Now in `dwave_interface/` → still goes to repo root. **Correct. No change needed.**

#### 1.7 `postprocessing/repair.py` (line 34)

Old:
```python
project_root = str(Path(__file__).resolve().parent)
sys.path.insert(0, str(project_root))
```
Was root-level. Now in `postprocessing/`. Fix: `.parent.parent`.

#### 1.8 `src/scenarios.py` (multiple occurrences)

Each scenario function computes `_project_root` via:
```python
_project_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
```
Was in `src/` → `dirname(dirname(file))` = repo root. Still in `src/`. **Correct. No change needed.**

#### 1.9 `unified_benchmark/scenarios.py` (line 22)

Old:
```python
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, project_root)
```
Was in `unified_benchmark/` → `.parent.parent` = repo root. Still in `unified_benchmark/`. **Correct. No change needed.**

#### 1.10 `unified_benchmark/quantum_solvers.py` (line ~60)

Old:
```python
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, project_root)
```
Still in `unified_benchmark/`. **Correct. No change needed.**

#### 1.11 `utils/grid_refinement.py` (lines 21-24)

Old:
```python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'Benchmark Scripts'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```
Was in `Utils/`. Now in `utils/`. `dirname(dirname(file))` still = repo root. **First line correct.**
Second line references `'Benchmark Scripts'` → change to `'benchmarks'`.

### Success Criteria

**Automated**: `python -c "import sys; sys.path.insert(0, '.'); from src.scenarios import load_food_data"` works from repo root.
**Manual**: Each benchmark script can be executed with `python benchmarks/solver_runner.py --help` without ImportError.

---

## Phase 2: Update Module Import Paths

### Overview
Rewrite `from`/`import` statements that reference old module names.

### Changes Required

#### 2.1 `Utils` → `utils` (12 files, ~25 import lines)

| File | Line(s) | Old | New |
|------|---------|-----|-----|
| `algorithms/formulation_builders.py` | 25-26 | `from Utils.farm_sampler import ...` / `from Utils.patch_sampler import ...` | `from utils.farm_sampler import ...` / `from utils.patch_sampler import ...` |
| `algorithms/qpu_benchmark.py` | 89 | `from Utils import patch_sampler` | `from utils import patch_sampler` |
| `benchmarks/benchmarks.py` | 8 | `from Utils.farm_sampler import generate_farms` | `from utils.farm_sampler import generate_farms` |
| `benchmarks/comprehensive_benchmark.py` | 36-39 | `from Utils.farm_sampler ...`, `from Utils.patch_sampler ...`, `from Utils.save_dwave_sampleset ...`, `from Utils.validate_cqm_vs_pulp ...` | `from utils.farm_sampler ...`, `from utils.patch_sampler ...` + **remove** the `save_dwave_sampleset` and `validate_cqm_vs_pulp` imports (not migrated — wrap in try/except) |
| `benchmarks/rotation_benchmark.py` | 36 | `from Utils.patch_sampler import ...` | `from utils.patch_sampler import ...` |
| `benchmarks/solver_runner_BINARY.py` | 25-26 | `from Utils import patch_sampler` / `from Utils import farm_sampler` | `from utils import patch_sampler` / `from utils import farm_sampler` |
| `benchmarks/solver_runner_PATCH.py` | 25 | `from Utils.patch_sampler import ...` | `from utils.patch_sampler import ...` |
| `benchmarks/solver_runner_ROTATION.py` | 27-28 | `from Utils import patch_sampler` / `from Utils import farm_sampler` | `from utils import patch_sampler` / `from utils import farm_sampler` |
| `src/scenarios.py` | 108, 233, 360, 485, 603, 722, 837, 947, 1518, 2086, 2162, 2232, 2303, 2382, 2489, 2579, 2669 | `from Utils.farm_sampler import generate_farms` | `from utils.farm_sampler import generate_farms` |
| `utils/grid_refinement.py` | 101-102 | `from Utils import patch_sampler` / `from Utils.farm_sampler import ...` | `from utils import patch_sampler` / `from utils.farm_sampler import ...` |

#### 2.2 `my_functions` → `dwave_interface` (2 files, 4 import lines)

| File | Line(s) | Old | New |
|------|---------|-----|-----|
| `dwave_interface/dwave_qpu_adapter.py` | 88-89 (fallback) | `from my_functions.qubo_converter import ...` / `from my_functions.mean_field_base import ...` | `from dwave_interface.qubo_converter import ...` / `from dwave_interface.mean_field_base import ...` |
| `dwave_interface/qubo_converter.py` | 19 | `from my_functions.optimization import FoodProductionOptimizer` | `from dwave_interface.optimization import FoodProductionOptimizer` (Note: this module doesn't exist — keep the existing try/except) |
| `dwave_interface/qubo_converter.py` | 685 | `from my_functions.mean_field_base import ...` | `from dwave_interface.mean_field_base import ...` |

#### 2.3 Bare `food_grouping` → `algorithms.food_grouping` (4 files, 5 import lines)

| File | Line(s) | Old | New |
|------|---------|-----|-----|
| `algorithms/hierarchical_quantum_solver.py` | 40 | `from food_grouping import (...)` | `from algorithms.food_grouping import (...)` |
| `algorithms/hybrid_formulation.py` | 36, 718 | `from food_grouping import ...` | `from algorithms.food_grouping import ...` |
| `unified_benchmark/miqp_scorer.py` | 384 | `from food_grouping import FAMILY_ORDER` | `from algorithms.food_grouping import FAMILY_ORDER` |
| `unified_benchmark/quantum_solvers.py` | 63 | `from food_grouping import FOOD_TO_FAMILY, get_family` | `from algorithms.food_grouping import FOOD_TO_FAMILY, get_family` |
| `unified_benchmark/scenarios.py` | 268 | `from food_grouping import FAMILY_ORDER` | `from algorithms.food_grouping import FAMILY_ORDER` |

#### 2.4 Bare `solver_runner` / `solver_runner_X` cross-references (5 files)

These are within-package imports (file A in `benchmarks/` imports file B in `benchmarks/`). Since both are now in the same `benchmarks/` directory, relative imports work:

| File | Line(s) | Old | New |
|------|---------|-----|-----|
| `benchmarks/benchmarks.py` | 6 | `from solver_runner import create_cqm, solve_with_pulp, solve_with_dwave` | `from benchmarks.solver_runner import create_cqm, solve_with_pulp, solve_with_dwave` |
| `benchmarks/comprehensive_benchmark.py` | 43 | `import solver_runner_BINARY as solver_runner` | `import benchmarks.solver_runner_BINARY as solver_runner` |
| `benchmarks/rotation_benchmark.py` | 40 | `import solver_runner_ROTATION as solver_runner` | `import benchmarks.solver_runner_ROTATION as solver_runner` |
| `benchmarks/solver_runner_BINARY.py` | 1393, 1476 | `from solver_runner import create_cqm as create_cqm_continuous` / `from solver_runner import solve_with_pulp as ...` | `from benchmarks.solver_runner import create_cqm as ...` / `from benchmarks.solver_runner import solve_with_pulp as ...` |
| `benchmarks/solver_runner_ROTATION.py` | 2693, 2776 | `from solver_runner import create_cqm as ...` / `from solver_runner import solve_with_pulp as ...` | `from benchmarks.solver_runner import ...` |

#### 2.5 `from synergy_optimizer` → `from src.synergy_optimizer_pure` (1 file)

| File | Line | Old | New |
|------|------|-----|-----|
| `benchmarks/solver_runner_LQ.py` | 42 | `from synergy_optimizer import SynergyOptimizer` | `from src.synergy_optimizer_pure import SynergyOptimizer` (this is the fallback that already exists at line 50 — just keep the try/except as-is) |

No change needed — the existing try/except already falls back correctly.

#### 2.6 `from plot_config` → `from plotting.plot_config` (1 file)

| File | Line | Old | New |
|------|------|-----|-----|
| `plotting/crop_benefit_weight_analysis.py` | 28 | `from plot_config import (...)` | `from plotting.plot_config import (...)` |
| `plotting/plot_config.py` | 16 | `from plot_config import (...)` | **Remove** — this is a self-import (the file tries to import itself as a module check; this line is inside an `if __name__ == '__main__'` or similar guard) |

#### 2.7 Bare `from scenarios import` in `unified_benchmark/miqp_scorer.py` (1 line)

| File | Line | Old | New |
|------|------|-----|-----|
| `unified_benchmark/miqp_scorer.py` | 450 | `from scenarios import load_scenario` | `from unified_benchmark.scenarios import load_scenario` |

#### 2.8 `decomposition_strategies.py` lazy imports (low priority, 7 imports)

`algorithms/decomposition_strategies.py` has factory methods that lazy-import from bare module names like `solver_runner_DECOMPOSED`, `result_format_compat`, `result_formatter`, `decomposition_benders`, `decomposition_admm`, etc. **None of these modules were migrated.** These imports are all inside methods and will only fail at runtime when those specific strategies are invoked. 

**Decision**: Wrap each in try/except with a clear error message. Or leave as-is — they'll produce ImportError only if someone calls unused strategy paths.

### Success Criteria

**Automated**: `python -c "from unified_benchmark import create_run_entry, load_scenario"` succeeds.
**Manual**: `python benchmarks/unified_benchmark_cli.py --list-scenarios` prints available scenarios.

---

## Phase 3: Update Hardcoded File Path Strings

### Overview
Several files contain string literals referencing old directory names for data files and benchmark results.

### Changes Required

#### 3.1 `src/scenarios.py` — `"Inputs"` → `"data/inputs"` (~17 occurrences)

Every scenario function contains:
```python
excel_path = _os.path.join(project_root_excel, "Inputs", "Combined_Food_Data.xlsx")
```
Change to:
```python
excel_path = _os.path.join(project_root_excel, "data", "inputs", "Combined_Food_Data.xlsx")
```

Also line 1385 error message:
```python
"The 'full' scenario requires Combined_Food_Data.xlsx in the Inputs/ directory."
```
→
```python
"The 'full' scenario requires Combined_Food_Data.xlsx in the data/inputs/ directory."
```

#### 3.2 `benchmarks/solver_runner_ROTATION.py` — `"rotation_data/..."` → `"data/rotation/..."` (1 line)

Line 39:
```python
def load_rotation_matrix(matrix_path="rotation_data/rotation_crop_matrix.csv"):
```
→
```python
def load_rotation_matrix(matrix_path="data/rotation/rotation_crop_matrix.csv"):
```

#### 3.3 `plotting/crop_benefit_weight_analysis.py` — `"Inputs/..."` → `"data/inputs/..."` (1 line)

Line 41:
```python
def load_food_data(excel_path: str = "Inputs/Combined_Food_Data.xlsx"):
```
→
```python
def load_food_data(excel_path: str = "data/inputs/Combined_Food_Data.xlsx"):
```

#### 3.4 `utils/grid_refinement.py` — `"Benchmark Scripts"` → `"benchmarks"` (3 occurrences)

Lines 22, 44, 81: Replace `"Benchmark Scripts"` with `"benchmarks"` and
`"solver_runner_BINARY.py"` filename references remain the same.

#### 3.5 `utils/rotation_matrix.py` — `"rotation_data/"` → `"data/rotation/"` (4 lines)

Lines 89, 103-106: Update output directory path and print statements.

#### 3.6 Plotting scripts — `"@todo/..."` path strings (3 files)

These reference benchmark result JSON files from `@todo/` subdirectories. Since we didn't migrate those result files, these paths will need to either:
1. Point to the old repo (not ideal), or
2. Be updated once result files are regenerated in the new structure.

**Decision**: Leave as-is for now with a `# TODO: update path after regenerating results` comment. These are data-loading paths, not import paths, and the plot scripts won't be run until benchmark results exist.

### Success Criteria

**Automated**: `python -c "from src.scenarios import load_food_data; load_food_data('full')"` loads data from `data/inputs/`.
**Manual**: Verify `data/inputs/Combined_Food_Data.xlsx` is found.

---

## Phase 4: Create Missing `__init__.py` Files

### Overview
Several new directories need `__init__.py` for Python package imports.

### Changes Required

| Directory | Needs `__init__.py`? | Content |
|-----------|---------------------|---------|
| `algorithms/` | **Yes** — create empty | `""" Quantum algorithms and decomposition strategies. """` |
| `benchmarks/` | **Yes** — create empty | `""" Benchmark scripts and solver runners. """` |
| `plotting/` | **Yes** — create empty | `""" Plot generation and configuration. """` |
| `postprocessing/` | **Yes** — create empty | `""" Post-processing and solution repair. """` |
| `data/` | No — not a Python package | |
| `docs/` | No — not a Python package | |
| `src/` | Already exists | |
| `utils/` | Already exists (copied from `Utils/`) | |
| `unified_benchmark/` | Already exists (copied) | |
| `dwave_interface/` | Already exists (copied) | |

### Success Criteria

**Automated**: `python -c "import algorithms; import benchmarks; import plotting; import postprocessing"` succeeds.

---

## Phase 5: Validate & Smoke Test

### Overview
Run import checks and quick validation to confirm all paths resolve.

### Steps

1. **Import smoke test** (no D-Wave/Gurobi required):
```python
# From repo root:
python -c "
from src.scenarios import load_food_data
from src.data_models import OptimizationResult, OptimizationObjective
from utils.farm_sampler import generate_farms
from utils.patch_sampler import generate_farms as gen_patches
from utils.crop_aggregation import CROP_TO_FAMILY_MAPPING
from algorithms.food_grouping import FOOD_TO_FAMILY, FAMILY_ORDER
from unified_benchmark.core import MIQP_PARAMS
from unified_benchmark.scenarios import load_scenario
from unified_benchmark.miqp_scorer import compute_miqp_objective
print('All core imports OK')
"
```

2. **Data load test**:
```python
python -c "
from src.scenarios import load_food_data
data = load_food_data('full')
print(f'Loaded {len(data)} fields from full scenario')
"
```

3. **Rotation data test**:
```python
python -c "
import pandas as pd
df = pd.read_csv('data/rotation/rotation_crop_matrix.csv', index_col=0)
print(f'Rotation matrix: {df.shape}')
"
```

4. **Check for remaining old references** (should return 0 for critical ones):
```powershell
Select-String -Path *.py -Recurse -Pattern 'from Utils\.' | Measure-Object
Select-String -Path *.py -Recurse -Pattern 'from my_functions\.' | Measure-Object
```

### Success Criteria

All 4 checks pass without ImportError or FileNotFoundError.

---

## Testing Strategy

### Project Maturity Level
Active Development — migrating an existing codebase.

### Unit Tests
No existing tests are migrated. Import smoke tests serve as validation.

### Integration Tests
- Benchmark scripts should be runnable with `--help` flag
- `unified_benchmark_cli.py --list-scenarios` should return scenario list

---

## Rollback Plan

The new repo contains only copies. The original `OQI-UC002-DWave` repo is untouched. To rollback:
```powershell
Remove-Item -Recurse -Force "d:\Projects\UC002-Food-Production-Optimization"
```

---

## Summary: Edit Counts by Phase

| Phase | Files to Edit | Estimated Edits |
|-------|--------------|-----------------|
| Phase 1: sys.path fixes | ~10 files | ~15 edits |
| Phase 2: Import rewrites | ~18 files | ~45 edits |
| Phase 3: Path string updates | ~5 files | ~25 edits |
| Phase 4: New `__init__.py` | 4 new files | 4 creates |
| Phase 5: Validate | 0 files | 4 test commands |
| **Total** | **~20 unique files** | **~89 edits + 4 creates** |
