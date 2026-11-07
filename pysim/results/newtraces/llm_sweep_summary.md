# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-17 23:40. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 | llm_c2:fable-5.1 |
|---|---|---|---|---|---|---|
| todas | +0.27 (130/360) | +0.10 (109/360) | -0.31 (55/360) | +0.17 (119/360) | +0.49 (144/360) | +0.29 (141/360) |
| con gemela | -0.01 (52/180) | -0.20 (44/180) | -0.06 (55/180) | -0.11 (49/180) | +0.31 (61/180) | +0.01 (58/180) |
| sin gemela | +0.44 (78/180) | +0.28 (65/180) | -0.46 (0/180) | +0.33 (70/180) | +0.59 (83/180) | +0.45 (83/180) |
| fallo step | +0.38 (52/120) | +0.21 (49/120) | -0.23 (22/120) | +0.27 (51/120) | +0.51 (49/120) | +0.38 (53/120) |
| fallo intermittent | -0.31 (29/120) | -0.64 (16/120) | -1.03 (9/120) | -0.51 (22/120) | +0.15 (38/120) | -0.27 (32/120) |
| fallo drift | +0.38 (49/120) | +0.27 (44/120) | -0.12 (24/120) | +0.32 (46/120) | +0.59 (57/120) | +0.40 (56/120) |
| traza 300m-400m | -0.25 (13/72) | -0.59 (10/72) | -0.56 (4/72) | -0.50 (11/72) | +0.09 (12/72) | -0.21 (16/72) |
| traza 400m-500m | +0.49 (34/72) | +0.33 (29/72) | +0.00 (19/72) | +0.43 (31/72) | +0.65 (34/72) | +0.53 (36/72) |
| traza 600m-700m | +0.20 (16/72) | +0.10 (13/72) | -0.58 (6/72) | +0.13 (15/72) | +0.55 (21/72) | +0.09 (18/72) |
| traza 700m-800m | +0.37 (33/72) | +0.05 (27/72) | -0.53 (10/72) | +0.07 (27/72) | +0.47 (34/72) | +0.32 (34/72) |
| traza 800m-900m | +0.21 (34/72) | +0.15 (30/72) | -0.26 (16/72) | +0.22 (35/72) | +0.46 (43/72) | +0.28 (37/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 | llm_c2:fable-5.1 |
|---|---|---|---|---|---|---|
| test_cases_300m-400m.td | 72 | 116 | 95 | 105 | 32 | 75 |
| test_cases_400m-500m.td | 118 | 152 | 126 | 123 | 48 | 95 |
| test_cases_600m-700m.td | 81 | 114 | 130 | 108 | 20 | 98 |
| test_cases_700m-800m.td | 122 | 152 | 229 | 143 | 40 | 103 |
| test_cases_800m-900m.td | 124 | 148 | 146 | 129 | 44 | 118 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 181/360 | 163/360 | 6.3 | 214 |
| rules_adapt | 187/360 | 147/360 | 8.7 | 210 |
| rules_twin | 88/360 | 63/360 | 7.8 | 275 |
| rules_adapt_ctx | 187/360 | 146/360 | 7.8 | 221 |
| hybrid:fable-5.1 | 170/360 | 159/360 | 2.7 | 300 |
| llm_c2:fable-5.1 | 185/360 | 157/360 | 7.5 | 215 |
