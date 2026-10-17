# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 16:53. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| todas | - | - | - | - | +0.18 (71/216) |
| con gemela | - | - | - | - | +0.05 (31/108) |
| sin gemela | - | - | - | - | +0.25 (40/108) |
| fallo step | - | - | - | - | +0.24 (23/72) |
| fallo intermittent | - | - | - | - | -0.24 (18/72) |
| fallo drift | - | - | - | - | +0.30 (30/72) |
| traza 100m-200m | - | - | - | - | +0.23 (37/72) |
| traza 200m-300m | - | - | - | - | +0.13 (13/72) |
| traza 500m-600m | - | - | - | - | +0.12 (21/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 121 |
| test_cases_200m-300m.td | - | - | - | - | 71 |
| test_cases_500m-600m.td | - | - | - | - | 97 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid | 106/216 | 78/216 | 5.0 | 305 |
