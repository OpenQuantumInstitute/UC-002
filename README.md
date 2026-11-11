# UC-002: Food Production Optimization

Open Quantum Institute use case 002. Crop-allocation and crop-rotation planning for farms, formulated as MILP/MIQP and benchmarked on classical (Gurobi) and quantum / hybrid (D-Wave) solvers.

## Layout

| Path | Contents |
| --- | --- |
| `src/` | Data models, scenario definitions, synergy optimizer |
| `algorithms/` | Formulation builders, decomposition strategies, hierarchical quantum solver, QPU benchmark |
| `dwave_interface/` | D-Wave QPU adapter, QUBO converter |
| `postprocessing/` | Solution repair |
| `unified_benchmark/` | Gurobi and quantum solver wrappers, MIQP scorer, benchmark core |
| `benchmarks/` | Scaling, rotation and comprehensive benchmark scripts, per-formulation solver runners |
| `plotting/`, `crop_weight_analysis/` | Plot generation and crop-weight analysis |
| `utils/` | Samplers, constraint validator, grid refinement, caches |
| `data/` | Input data (food data, rotation data) |
| `docs/` | `formulations.tex`, report (`docs/report/content_report.pdf`) |

## Setup

```bash
conda env create -f requirements.yml
conda activate oqi_vrp_environment
```

Gurobi and D-Wave Ocean SDK are not in `requirements.yml`. Install them separately; both need their own credentials (Gurobi licence, D-Wave API token).

## Usage

Run scripts from the repository root, for example:

```bash
python benchmarks/unified_benchmark_cli.py --help
python benchmarks/gurobi_scaling_benchmark.py
```

## Licence

[CC BY-SA 4.0](LICENSE). Share and adapt with attribution, under the same licence.
