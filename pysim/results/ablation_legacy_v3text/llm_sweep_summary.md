# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 05:47. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | - | - | - | - | +0.03 (15/216) |
| con gemela | - | - | - | - | +0.01 (6/108) |
| sin gemela | - | - | - | - | +0.04 (9/108) |
| fallo step | - | - | - | - | +0.05 (7/72) |
| fallo intermittent | - | - | - | - | -0.02 (3/72) |
| fallo drift | - | - | - | - | +0.04 (5/72) |
| traza 100m-200m | - | - | - | - | -0.01 (1/72) |
| traza 200m-300m | - | - | - | - | +0.04 (2/72) |
| traza 500m-600m | - | - | - | - | +0.08 (12/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 0 |
| test_cases_200m-300m.td | - | - | - | - | 1 |
| test_cases_500m-600m.td | - | - | - | - | 6 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid:fable-5.1 | 21/216 | 21/216 | 0.6 | 1,102 |
