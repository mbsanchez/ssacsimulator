# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-16 00:00. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| todas | - | - | - | - | - |
| con gemela | - | - | - | - | - |
| sin gemela | - | - | - | - | - |
| fallo step | - | - | - | - | - |
| fallo intermittent | - | - | - | - | - |
| fallo drift | - | - | - | - | - |
| traza 300m-400m | - | - | - | - | - |
| traza 400m-500m | - | - | - | - | - |
| traza 600m-700m | - | - | - | - | - |
| traza 700m-800m | - | - | - | - | - |
| traza 800m-900m | - | - | - | - | - |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| test_cases_300m-400m.td | - | - | - | - | 90 |
| test_cases_400m-500m.td | - | - | - | - | 99 |
| test_cases_600m-700m.td | - | - | - | - | 92 |
| test_cases_700m-800m.td | - | - | - | - | 131 |
| test_cases_800m-900m.td | - | - | - | - | 110 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid | 186/360 | 149/360 | 7.1 | 221 |
