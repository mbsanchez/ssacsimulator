# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-17 08:32. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| todas | - | - | - | - | +0.42 (76/216) |
| con gemela | - | - | - | - | +0.33 (33/108) |
| sin gemela | - | - | - | - | +0.47 (43/108) |
| fallo step | - | - | - | - | +0.37 (21/72) |
| fallo intermittent | - | - | - | - | +0.27 (28/72) |
| fallo drift | - | - | - | - | +0.54 (27/72) |
| traza 100m-200m | - | - | - | - | +0.50 (42/72) |
| traza 200m-300m | - | - | - | - | +0.30 (11/72) |
| traza 500m-600m | - | - | - | - | +0.37 (23/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid:fable-5.1 |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 31 |
| test_cases_200m-300m.td | - | - | - | - | 21 |
| test_cases_500m-600m.td | - | - | - | - | 29 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid:fable-5.1 | 87/216 | 79/216 | 1.9 | 305 |
