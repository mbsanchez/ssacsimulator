# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 16:41. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| todas | - | - | - | - | -1.86 (6/216) |
| con gemela | - | - | - | - | -2.42 (3/108) |
| sin gemela | - | - | - | - | -1.52 (3/108) |
| fallo step | - | - | - | - | -1.21 (2/72) |
| fallo intermittent | - | - | - | - | -4.45 (0/72) |
| fallo drift | - | - | - | - | -1.34 (4/72) |
| traza 100m-200m | - | - | - | - | -1.80 (2/72) |
| traza 200m-300m | - | - | - | - | -1.62 (2/72) |
| traza 500m-600m | - | - | - | - | -2.15 (2/72) |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 530 |
| test_cases_200m-300m.td | - | - | - | - | 314 |
| test_cases_500m-600m.td | - | - | - | - | 578 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid | 104/216 | 76/216 | 5.2 | 305 |
