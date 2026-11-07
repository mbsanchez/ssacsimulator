# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 15:05. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| todas | - | - | - | - | +0.40 (86/216) |
| con gemela | - | - | - | - | +0.38 (41/108) |
| sin gemela | - | - | - | - | +0.42 (45/108) |
| fallo step | - | - | - | - | +0.40 (25/72) |
| fallo intermittent | - | - | - | - | +0.21 (29/72) |
| fallo drift | - | - | - | - | +0.49 (32/72) |
| traza 100m-200m | - | - | - | - | +0.49 (46/72) |
| traza 200m-300m | - | - | - | - | +0.38 (16/72) |
| traza 500m-600m | - | - | - | - | +0.27 (24/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 62 |
| test_cases_200m-300m.td | - | - | - | - | 44 |
| test_cases_500m-600m.td | - | - | - | - | 57 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid | 105/216 | 77/216 | 5.5 | 305 |
