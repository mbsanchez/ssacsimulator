## Coste de las falsas alarmas — corridas SIN fallo

Minutos-pieza perdidos por hora de operación, solo por actuar sobre ruido. Punto central.

| Traza | rules_naive | rules_cal | rules_adapt | rules_twin |
|---|---|---|---|---|
| test_cases_0-100m.td | 457 | 284 | 26 | 214 |
| test_cases_100m-200m.td | 264 | 94 | 20 | 113 |
| test_cases_200m-300m.td | 307 | 121 | 71 | 155 |
| test_cases_500m-600m.td | 340 | 108 | 111 | 158 |

## Rejilla central — recuperación agregada (escenarios con beneficio neto > 0)

Recuperación agregada = 1 − Σ exceso(política) / Σ exceso(no hacer nada). Detector legacy; fallo x3, reparación 60 min, α = 0,5, contingencia.

| Grupo | rules_naive | rules_cal | rules_adapt | rules_twin |
|---|---|---|---|---|
| todas |  -0.11 (37/96) |  +0.49 (73/96) |  +0.56 (69/96) |  -0.17 (28/96) |
| con gemela |  -0.49 (11/48) |  +0.33 (30/48) |  +0.35 (29/48) |  +0.27 (28/48) |
| sin gemela |  +0.11 (26/48) |  +0.58 (43/48) |  +0.68 (40/48) |  -0.42 (0/48) |
| fallo step |  +0.14 (17/32) |  +0.59 (30/32) |  +0.64 (29/32) |  -0.05 (12/32) |
| fallo intermittent |  -1.40 (3/32) |  -0.09 (13/32) |  +0.07 (13/32) |  -0.78 (5/32) |
| fallo drift |  +0.10 (17/32) |  +0.60 (30/32) |  +0.66 (27/32) |  -0.07 (11/32) |
| traza 0-100m |  +0.43 (19/24) |  +0.58 (21/24) |  +0.66 (17/24) |  +0.14 (12/24) |
| traza 100m-200m |  +0.04 (10/24) |  +0.63 (21/24) |  +0.75 (22/24) |  -0.06 (9/24) |
| traza 200m-300m |  -0.87 (4/24) |  +0.15 (13/24) |  +0.23 (12/24) |  -0.64 (3/24) |
| traza 500m-600m |  -0.39 (4/24) |  +0.47 (18/24) |  +0.48 (18/24) |  -0.33 (4/24) |

## Sensibilidad uno-a-uno — recuperación agregada

Fallo escalón. Cada fila cambia un único parámetro respecto al punto central.

| Variación | rules_cal | rules_adapt | rules_twin |
|---|---|---|---|
| **central** |  +0.59 (30/32) |  +0.64 (29/32) |  -0.05 (12/32) |
| alpha=0 |  +0.74 (32/32) |  +0.73 (29/32) |  +0.23 (16/32) |
| alpha=1 |  +0.47 (25/32) |  +0.56 (25/32) |  -0.33 (8/32) |
| factor=1.5 |  -0.39 (10/32) |  +0.10 (18/32) |  -1.22 (1/32) |
| factor=5 |  +0.75 (32/32) |  +0.73 (29/32) |  +0.15 (16/32) |
| mode=stop |  -1.17 (0/32) |  -0.27 (13/32) |  -1.01 (4/32) |
| repair_min=15 |  +0.84 (32/32) |  +0.78 (29/32) |  +0.25 (16/32) |
| repair_min=240 |  -0.80 (5/32) |  +0.12 (17/32) |  -1.18 (2/32) |

## Desglose del coste — rejilla central, medias por escenario (minutos-pieza)

| Planificador | exceso | mant. sobre fallo | mant. falsos | latencia 1ª acción (min) | contingencia | congestión |
|---|---|---|---|---|---|---|
| noop | 38,190 | 0.0 | 0.0 | nan | 0 | 0 |
| rules_naive | 42,241 | 2.7 | 122.5 | 180 | 26,738 | 13,394 |
| rules_cal | 19,437 | 1.3 | 45.7 | 234 | 10,286 | 6,051 |
| rules_adapt | 16,682 | 1.4 | 25.8 | 3,024 | 5,101 | 3,819 |
| rules_twin | 44,666 | 1.1 | 55.8 | 177 | 5,762 | 13,898 |
