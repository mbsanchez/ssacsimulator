# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-11 15:34. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 | llm_c2:fable-5.1 |
|---|---|---|---|---|---|---|
| todas | -0.03 (34/216) | -0.03 (42/216) | -0.35 (20/216) | -0.02 (40/216) | +0.03 (19/216) | +0.07 (36/216) |
| con gemela | -0.08 (13/108) | -0.19 (16/108) | -0.15 (20/108) | -0.18 (15/108) | -0.03 (6/108) | +0.00 (14/108) |
| sin gemela | -0.01 (21/108) | +0.06 (26/108) | -0.47 (0/108) | +0.08 (25/108) | +0.07 (13/108) | +0.11 (22/108) |
| fallo step | +0.04 (14/72) | +0.06 (20/72) | -0.26 (9/72) | +0.08 (20/72) | +0.09 (10/72) | +0.13 (14/72) |
| fallo intermittent | -0.38 (3/72) | -0.44 (3/72) | -0.76 (2/72) | -0.40 (3/72) | -0.03 (4/72) | -0.17 (5/72) |
| fallo drift | +0.04 (17/72) | +0.06 (19/72) | -0.27 (9/72) | +0.06 (17/72) | +0.00 (5/72) | +0.12 (17/72) |
| traza 100m-200m | +0.08 (9/72) | +0.08 (15/72) | -0.07 (13/72) | +0.08 (15/72) | +0.01 (2/72) | +0.07 (9/72) |
| traza 200m-300m | -0.23 (6/72) | -0.38 (5/72) | -0.72 (0/72) | -0.34 (4/72) | -0.01 (3/72) | -0.06 (4/72) |
| traza 500m-600m | -0.06 (19/72) | +0.07 (22/72) | -0.52 (7/72) | +0.08 (21/72) | +0.11 (14/72) | +0.18 (23/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 | llm_c2:fable-5.1 |
|---|---|---|---|---|---|---|
| test_cases_100m-200m.td | 94 | 20 | 113 | 20 | 0 | 37 |
| test_cases_200m-300m.td | 121 | 71 | 155 | 60 | 13 | 55 |
| test_cases_500m-600m.td | 108 | 111 | 158 | 111 | 7 | 83 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 62/216 | 42/216 | 4.4 | 826 |
| rules_adapt | 77/216 | 52/216 | 6.2 | 800 |
| rules_twin | 47/216 | 26/216 | 7.1 | 646 |
| rules_adapt_ctx | 75/216 | 50/216 | 5.9 | 784 |
| hybrid:fable-5.1 | 24/216 | 24/216 | 0.9 | 1,060 |
| llm_c2:fable-5.1 | 54/216 | 38/216 | 3.9 | 730 |
