# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-15 03:34. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 | llm_c1:fable-5.1 | llm_c2:fable-5.1 |
|---|---|---|---|---|---|---|---|
| todas | +0.13 (65/216) | +0.17 (65/216) | -0.20 (36/216) | +0.20 (70/216) | +0.41 (76/216) | +0.08 (18/216) | +0.14 (64/216) |
| con gemela | +0.00 (27/108) | +0.05 (29/108) | +0.14 (36/108) | +0.07 (31/108) | +0.35 (34/108) | +0.07 (10/108) | +0.00 (28/108) |
| sin gemela | +0.21 (38/108) | +0.24 (36/108) | -0.41 (0/108) | +0.29 (39/108) | +0.45 (42/108) | +0.09 (8/108) | +0.22 (36/108) |
| fallo step | +0.23 (22/72) | +0.23 (22/72) | -0.07 (14/72) | +0.26 (24/72) | +0.35 (21/72) | +0.02 (3/72) | +0.23 (23/72) |
| fallo intermittent | -0.29 (17/72) | -0.27 (16/72) | -0.64 (5/72) | -0.20 (18/72) | +0.29 (28/72) | +0.10 (9/72) | -0.25 (15/72) |
| fallo drift | +0.22 (26/72) | +0.30 (27/72) | -0.13 (17/72) | +0.33 (28/72) | +0.53 (27/72) | +0.14 (6/72) | +0.22 (26/72) |
| traza 100m-200m | +0.33 (38/72) | +0.24 (33/72) | -0.11 (19/72) | +0.28 (36/72) | +0.51 (42/72) | +0.09 (11/72) | +0.27 (34/72) |
| traza 200m-300m | -0.00 (12/72) | +0.10 (12/72) | -0.36 (5/72) | +0.12 (14/72) | +0.27 (11/72) | +0.14 (4/72) | +0.02 (10/72) |
| traza 500m-600m | -0.08 (15/72) | +0.10 (20/72) | -0.22 (12/72) | +0.15 (20/72) | +0.37 (23/72) | +0.02 (3/72) | +0.01 (20/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 | llm_c1:fable-5.1 | llm_c2:fable-5.1 |
|---|---|---|---|---|---|---|---|
| test_cases_100m-200m.td | 88 | 119 | 122 | 105 | 20 | 1 | 85 |
| test_cases_200m-300m.td | 116 | 80 | 91 | 78 | 24 | 2 | 90 |
| test_cases_500m-600m.td | 116 | 96 | 112 | 83 | 33 | 0 | 125 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 101/216 | 76/216 | 5.5 | 218 |
| rules_adapt | 108/216 | 76/216 | 5.9 | 311 |
| rules_twin | 60/216 | 13/216 | 6.2 | 362 |
| rules_adapt_ctx | 108/216 | 76/216 | 5.5 | 311 |
| hybrid:fable-5.1 | 87/216 | 79/216 | 1.8 | 345 |
| llm_c1:fable-5.1 | 19/216 | 19/216 | 0.1 | 408 |
| llm_c2:fable-5.1 | 105/216 | 81/216 | 7.1 | 208 |
