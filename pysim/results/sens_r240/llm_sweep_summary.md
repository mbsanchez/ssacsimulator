# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-18 19:33. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | -1.22 (19/216) | -1.22 (13/216) | - | -0.86 (20/216) | -0.09 (50/216) |
| con gemela | -1.84 (5/108) | -1.84 (3/108) | - | -1.36 (5/108) | -0.36 (14/108) |
| sin gemela | -0.85 (14/108) | -0.84 (10/108) | - | -0.55 (15/108) | +0.08 (36/108) |
| fallo step | -0.70 (10/72) | -0.75 (6/72) | - | -0.52 (10/72) | -0.06 (18/72) |
| fallo intermittent | -2.92 (2/72) | -2.87 (0/72) | - | -2.19 (1/72) | -0.64 (15/72) |
| fallo drift | -0.98 (7/72) | -0.94 (7/72) | - | -0.60 (9/72) | +0.14 (17/72) |
| traza 100m-200m | -0.58 (14/72) | -0.89 (6/72) | - | -0.52 (10/72) | +0.12 (26/72) |
| traza 200m-300m | -1.81 (3/72) | -1.64 (6/72) | - | -1.29 (6/72) | -0.40 (7/72) |
| traza 500m-600m | -1.78 (2/72) | -1.41 (1/72) | - | -1.05 (4/72) | -0.16 (17/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | 274 | 323 | - | 256 | 77 |
| test_cases_200m-300m.td | 390 | 301 | - | 259 | 109 |
| test_cases_500m-600m.td | 533 | 461 | - | 366 | 178 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 101/216 | 75/216 | 5.6 | 218 |
| rules_adapt | 107/216 | 68/216 | 6.2 | 339 |
| rules_adapt_ctx | 106/216 | 69/216 | 4.8 | 339 |
| hybrid:fable-5.1 | 85/216 | 75/216 | 2.1 | 317 |
