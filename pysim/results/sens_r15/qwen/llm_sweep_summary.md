# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 14:43. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| todas | - | - | - | - | +0.59 (97/216) |
| con gemela | - | - | - | - | +0.61 (47/108) |
| sin gemela | - | - | - | - | +0.57 (50/108) |
| fallo step | - | - | - | - | +0.53 (26/72) |
| fallo intermittent | - | - | - | - | +0.58 (36/72) |
| fallo drift | - | - | - | - | +0.65 (35/72) |
| traza 100m-200m | - | - | - | - | +0.65 (50/72) |
| traza 200m-300m | - | - | - | - | +0.64 (18/72) |
| traza 500m-600m | - | - | - | - | +0.44 (29/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 21 |
| test_cases_200m-300m.td | - | - | - | - | 11 |
| test_cases_500m-600m.td | - | - | - | - | 19 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid | 103/216 | 76/216 | 5.6 | 293 |
