# Paper

Build: `tectonic -X compile main.tex` (Tectonic 0.17).

Figures: `../pysim/.venv/bin/python figures.py` regenerates `figures/*.pdf` from `../pysim/results/llm_sweep_rows.csv`.

Every number in the text comes from `../pysim/results/` (`sweep_summary.md`, `llm_sweep_summary.md`, `stats.md`). Items marked TODO (red in the PDF) must be completed by the authors.

## Versión de lectura en español

`main_es.tex` / `main_es.pdf` es una traducción para lectura; **no se envía a la revista** (el manuscrito es `main.tex`). Usa las figuras de `figures/es/`, generadas con `../pysim/.venv/bin/python figures.py --lang es` (etiquetas en español, coma decimal). Si cambia `main.tex`, la traducción se actualiza a mano.
