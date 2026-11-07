# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 01:15. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | - | - | - | - | +0.41 (77/216) |
| con gemela | - | - | - | - | +0.32 (33/108) |
| sin gemela | - | - | - | - | +0.47 (44/108) |
| fallo step | - | - | - | - | +0.37 (22/72) |
| fallo intermittent | - | - | - | - | +0.25 (28/72) |
| fallo drift | - | - | - | - | +0.53 (27/72) |
| traza 100m-200m | - | - | - | - | +0.48 (42/72) |
| traza 200m-300m | - | - | - | - | +0.33 (12/72) |
| traza 500m-600m | - | - | - | - | +0.37 (23/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 34 |
| test_cases_200m-300m.td | - | - | - | - | 32 |
| test_cases_500m-600m.td | - | - | - | - | 33 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid:fable-5.1 | 88/216 | 80/216 | 2.2 | 299 |
