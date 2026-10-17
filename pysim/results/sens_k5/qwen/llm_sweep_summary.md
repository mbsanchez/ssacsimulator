# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 14:09. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| todas | - | - | - | - | +0.47 (91/216) |
| con gemela | - | - | - | - | +0.42 (41/108) |
| sin gemela | - | - | - | - | +0.50 (50/108) |
| fallo step | - | - | - | - | +0.41 (25/72) |
| fallo intermittent | - | - | - | - | +0.39 (35/72) |
| fallo drift | - | - | - | - | +0.56 (31/72) |
| traza 100m-200m | - | - | - | - | +0.58 (49/72) |
| traza 200m-300m | - | - | - | - | +0.41 (16/72) |
| traza 500m-600m | - | - | - | - | +0.34 (26/72) |

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
| hybrid | 106/216 | 79/216 | 5.2 | 234 |
