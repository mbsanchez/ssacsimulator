# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-18 19:42. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | +0.50 (31/54) | +0.52 (33/54) | - | +0.53 (33/54) | +0.43 (29/54) |
| con gemela | - | - | - | - | - |
| sin gemela | +0.50 (31/54) | +0.52 (33/54) | - | +0.53 (33/54) | +0.43 (29/54) |
| fallo step | +0.52 (9/18) | +0.53 (10/18) | - | +0.54 (10/18) | +0.45 (6/18) |
| fallo intermittent | +0.40 (13/18) | +0.43 (14/18) | - | +0.46 (14/18) | +0.30 (14/18) |
| fallo drift | +0.53 (9/18) | +0.56 (9/18) | - | +0.57 (9/18) | +0.48 (9/18) |
| traza 100m-200m | +0.59 (14/18) | +0.59 (15/18) | - | +0.61 (15/18) | +0.47 (11/18) |
| traza 200m-300m | +0.39 (10/18) | +0.43 (10/18) | - | +0.45 (10/18) | +0.39 (9/18) |
| traza 500m-600m | +0.23 (7/18) | +0.30 (8/18) | - | +0.30 (8/18) | +0.30 (9/18) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | 88 | 119 | - | 105 | 20 |
| test_cases_200m-300m.td | 116 | 80 | - | 78 | 24 |
| test_cases_500m-600m.td | 116 | 96 | - | 83 | 33 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| rules_cal | 37/54 | 0/54 | 5.2 | 72 |
| rules_adapt | 38/54 | 0/54 | 5.4 | 90 |
| rules_adapt_ctx | 38/54 | 0/54 | 4.7 | 72 |
| hybrid:fable-5.1 | 32/54 | 0/54 | 1.8 | 110 |
