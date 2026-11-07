# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-15 23:17. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | - | - | - | - | +0.31 (68/216) |
| con gemela | - | - | - | - | +0.20 (29/108) |
| sin gemela | - | - | - | - | +0.38 (39/108) |
| fallo step | - | - | - | - | +0.30 (21/72) |
| fallo intermittent | - | - | - | - | +0.04 (19/72) |
| fallo drift | - | - | - | - | +0.46 (28/72) |
| traza 100m-200m | - | - | - | - | +0.39 (38/72) |
| traza 200m-300m | - | - | - | - | +0.20 (8/72) |
| traza 500m-600m | - | - | - | - | +0.29 (22/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 53 |
| test_cases_200m-300m.td | - | - | - | - | 35 |
| test_cases_500m-600m.td | - | - | - | - | 56 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid:fable-5.1 | 93/216 | 73/216 | 3.9 | 311 |
