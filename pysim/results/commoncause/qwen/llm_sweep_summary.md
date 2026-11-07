# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 15:23. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| todas | - | - | - | - | +0.55 (34/54) |
| con gemela | - | - | - | - | - |
| sin gemela | - | - | - | - | +0.55 (34/54) |
| fallo step | - | - | - | - | +0.55 (10/18) |
| fallo intermittent | - | - | - | - | +0.49 (15/18) |
| fallo drift | - | - | - | - | +0.58 (9/18) |
| traza 100m-200m | - | - | - | - | +0.61 (15/18) |
| traza 200m-300m | - | - | - | - | +0.49 (10/18) |
| traza 500m-600m | - | - | - | - | +0.33 (9/18) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 87 |
| test_cases_200m-300m.td | - | - | - | - | 58 |
| test_cases_500m-600m.td | - | - | - | - | 78 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid | 38/54 | 0/54 | 4.7 | 84 |
