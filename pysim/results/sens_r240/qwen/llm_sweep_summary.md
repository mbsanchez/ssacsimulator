# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 16:10. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| todas | - | - | - | - | -0.90 (21/216) |
| con gemela | - | - | - | - | -1.41 (6/108) |
| sin gemela | - | - | - | - | -0.58 (15/108) |
| fallo step | - | - | - | - | -0.50 (13/72) |
| fallo intermittent | - | - | - | - | -2.31 (0/72) |
| fallo drift | - | - | - | - | -0.65 (8/72) |
| traza 100m-200m | - | - | - | - | -0.74 (10/72) |
| traza 200m-300m | - | - | - | - | -0.97 (6/72) |
| traza 500m-600m | - | - | - | - | -1.10 (5/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 296 |
| test_cases_200m-300m.td | - | - | - | - | 208 |
| test_cases_500m-600m.td | - | - | - | - | 387 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid | 104/216 | 70/216 | 5.6 | 329 |
