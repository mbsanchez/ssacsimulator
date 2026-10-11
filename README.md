# SSACSimulator

Simulator of a self-coordinated manufacturing line with self-* (autonomic) properties, over the Bosch Production Line Performance dataset, and the code, results and manuscript of:

> M. Sánchez, E. Exposito. *From detection to action: closing the autonomic loop of a self-coordinated manufacturing line with rule-based and retrieval-augmented LLM planners.* Manuscript submitted to *Computers in Industry*.

The original 2020 simulator (Qt/C++) is described in M. Sánchez et al., *Computers in Industry* 2020 and *Journal of Industrial Information Integration* 2020 (see `paper/refs.bib`).

## Contents

| Path | What it is |
|---|---|
| `SSACSimulator/`, `QGVCore/`, `SSACSimulator.pro`, `CMakeLists.txt` | The original 2020 Qt/C++ simulator (Monitor and Analyze only). |
| `pysim/` | Headless Python port of the simulator, the closed MAPE-K loop (action space, symbolic validator, fault injection, effect model), the rule-based and LLM planners, and the experiment scripts. See `pysim/README.md` (in Spanish). |
| `pysim/results/` | Every result reported in the paper: per-run rows, per-LLM-call decisions with the model's stated reasons, summaries, statistics, and the development log of every prompt version. |
| `paper/` | LaTeX source of the manuscript (`main.tex`), a Spanish reading version (`main_es.tex`), `figures.py` (regenerates every figure from `pysim/results/`) and the prompts used for the adversarial review. |
| `DataSets I4.0/PreProcess/` | The 2020 preprocessing scripts that derive the process model and event traces from the Bosch dataset. |

## Data

The study uses the [Bosch Production Line Performance](https://www.kaggle.com/c/bosch-production-line-performance) dataset, distributed by Kaggle under the competition's rules. **This repository does not redistribute it, nor the files derived from it.** To rerun the simulations, download the dataset from Kaggle, derive the process model and traces with the scripts in `DataSets I4.0/PreProcess/`, and place them in `DataSets I4.0/` (or point the environment variable `SSAC_DATA` to their folder). The files used in the paper are:

| File | Bytes | SHA-256 |
|---|---:|---|
| `bosch_pl_tm_model.pg` | 6 652 | `0c4872c41a35b8e505b58d8507ff9a06cd70a0d40172090f99c44fedaa2a965f` |
| `process_graph_trimmed_mean.pg` | 6 651 | `895a11df5ba36f3ffe6c8b96074e930b7e4d857b91e47a69d2b67fa4a2b24170` |
| `test_cases_0-100m.td` | 3 427 616 | `4363970b562b0a4e9cc4905512c69b5989bb8adbaa9e5d299dcf32cef47546a7` |
| `test_cases_100m-200m.td` | 3 506 005 | `3f277e50f59bcdb14a4ba7a638ca9e22cbe75c60fbd8f6fb6f6cc71c62e5677b` |
| `test_cases_200m-300m.td` | 3 619 078 | `b8bbdd864dcbd11dcc74cf7e41312c38732cc35262238c294c9add826128bdec` |
| `test_cases_500m-600m.td` | 3 626 343 | `df4304d73bae96196743d2065c41b5fc6b94c4330f3582e36913266982ced770` |

The derived files are available from the corresponding author on request, to holders of the Kaggle dataset.

**Without the data** you can still recompute every table, statistic and figure of the paper from the stored results:

```sh
cd pysim && python3 -m venv .venv && .venv/bin/pip install scipy matplotlib pytest
.venv/bin/python stats.py                 # results/stats.md
.venv/bin/python trace_bootstrap.py       # results/trace_bootstrap.md
.venv/bin/python rule_sweep.py --summary  # results/rule_sweep_summary.md
.venv/bin/python llm_sweep.py --summary   # results/llm_sweep_summary.md
cd ../paper && ../pysim/.venv/bin/python figures.py
```

and run the tests that do not need the data (`.venv/bin/pytest tests`; those that need it are skipped).

**With the data**: `sweep.py` and `rule_sweep.py` rerun the rule-based experiments in minutes. The LLM experiments (`llm_sweep.py`, `dev_llm.py`) need a local Ollama server with `qwen2.5:7b`, or the Claude Agent SDK for Claude Fable 5.1; their decisions are not bit-reproducible, which is why every decision and stated reason is stored in `pysim/results/llm_sweep_calls.csv`.

The simulator itself uses only the Python standard library; the statistics and figures use SciPy and matplotlib.

## License

LGPL-3.0, see `LICENSE.txt`.
