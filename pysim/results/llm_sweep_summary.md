# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-06 07:57. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | llm_c2 | llm_c1 | hybrid |
|---|---|---|---|---|---|---|---|
| todas | +0.45 (52/72) | +0.52 (52/72) | -0.31 (16/72) | +0.54 (53/72) | +0.20 (39/72) | +0.15 (33/72) | +0.41 (45/72) |
| con gemela | +0.24 (21/36) | +0.32 (23/36) | +0.07 (16/36) | +0.35 (24/36) | -0.07 (15/36) | +0.07 (16/36) | +0.40 (25/36) |
| sin gemela | +0.56 (31/36) | +0.62 (29/36) | -0.50 (0/36) | +0.63 (29/36) | +0.34 (24/36) | +0.20 (17/36) | +0.42 (20/36) |
| fallo step | +0.56 (22/24) | +0.62 (22/24) | -0.16 (8/24) | +0.63 (22/24) | +0.36 (17/24) | +0.31 (15/24) | +0.50 (20/24) |
| fallo intermittent | -0.20 (8/24) | -0.06 (10/24) | -1.10 (1/24) | -0.02 (11/24) | -0.69 (5/24) | -0.59 (5/24) | -0.10 (8/24) |
| fallo drift | +0.55 (22/24) | +0.62 (20/24) | -0.18 (7/24) | +0.64 (20/24) | +0.35 (17/24) | +0.25 (13/24) | +0.50 (17/24) |
| traza 100m-200m | +0.63 (21/24) | +0.75 (22/24) | -0.06 (9/24) | +0.75 (22/24) | +0.54 (21/24) | +0.57 (20/24) | +0.50 (18/24) |
| traza 200m-300m | +0.15 (13/24) | +0.23 (12/24) | -0.64 (3/24) | +0.29 (13/24) | -0.28 (6/24) | -0.12 (7/24) | +0.10 (8/24) |
| traza 500m-600m | +0.47 (18/24) | +0.48 (18/24) | -0.33 (4/24) | +0.49 (18/24) | +0.18 (12/24) | -0.16 (6/24) | +0.59 (19/24) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | llm_c2 | llm_c1 | hybrid |
|---|---|---|---|---|---|---|---|
| test_cases_100m-200m.td | 94 | 20 | 113 | 20 | 122 | 90 | 9 |
| test_cases_200m-300m.td | 121 | 71 | 155 | 60 | 164 | 153 | 41 |
| test_cases_500m-600m.td | 108 | 111 | 158 | 111 | 190 | 165 | 63 |

## Precisión de las acciones (escenarios con fallo)

Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 72/72 | 32/72 | 48.8 | 222 |
| rules_adapt | 72/72 | 57/72 | 32.8 | 3,090 |
| rules_twin | 36/72 | 9/72 | 65.0 | 150 |
| rules_adapt_ctx | 72/72 | 57/72 | 31.2 | 3,090 |
| llm_c2 | 72/72 | 31/72 | 74.0 | 360 |
| llm_c1 | 57/72 | 22/72 | 61.6 | 234 |
| hybrid | 59/72 | 50/72 | 24.0 | 3,270 |
