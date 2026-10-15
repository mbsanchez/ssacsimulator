# Evaluación final en trazas reservadas — prompt v2

Generado 2026-10-11 20:25. Recuperación agregada (escenarios con beneficio neto).

| Grupo | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid | llm_c1 | llm_c2 |
|---|---|---|---|---|---|---|---|
| todas | - | - | - | - | - | - | - |
| con gemela | - | - | - | - | - | - | - |
| sin gemela | - | - | - | - | - | - | - |
| fallo step | - | - | - | - | - | - | - |
| fallo intermittent | - | - | - | - | - | - | - |
| fallo drift | - | - | - | - | - | - | - |
| traza 100m-200m | - | - | - | - | - | - | - |
| traza 200m-300m | - | - | - | - | - | - | - |
| traza 500m-600m | - | - | - | - | - | - | - |

## Coste de falsas alarmas sin fallo (min-pieza/h)

| Traza | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid | llm_c1 | llm_c2 |
|---|---|---|---|---|---|---|---|
| test_cases_100m-200m.td | - | - | - | - | 87 | 128 | 187 |
| test_cases_200m-300m.td | - | - | - | - | 58 | 101 | 191 |
| test_cases_500m-600m.td | - | - | - | - | 78 | 133 | 231 |

## Precisión de las acciones (escenarios con fallo)

Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). Un acierto que coincide con una reparación de rutina no cuenta.

| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |
|---|---|---|---|---|
| hybrid | 106/216 | 78/216 | 5.2 | 305 |
| llm_c1 | 90/216 | 41/216 | 7.6 | 390 |
| llm_c2 | 117/216 | 51/216 | 14.0 | 281 |
