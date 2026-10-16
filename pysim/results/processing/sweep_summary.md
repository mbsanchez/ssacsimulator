## Coste de las falsas alarmas — corridas SIN fallo

Minutos-pieza perdidos por hora de operación, solo por actuar sobre ruido. Punto central.

| Traza | rules_naive | rules_cal | rules_adapt | rules_twin |
|---|---|---|---|---|
| test_cases_0-100m.td | 709 | 197 | 76 | 359 |
| test_cases_100m-200m.td | 232 | 88 | 119 | 122 |
| test_cases_200m-300m.td | 201 | 116 | 80 | 91 |
| test_cases_500m-600m.td | 254 | 116 | 96 | 112 |

## Rejilla central — recuperación agregada (escenarios con beneficio neto > 0)

Diseño v2. Recuperación agregada a 24 h = 1 − Σ exceso en [t0, t0+24 h) (política) / ídem (no hacer nada). Detector por estación (results/detector_choice.json); 4 trazas (desarrollo + 3 reservadas); fallo x3, reparación 60 min, α = 0,5, contingencia; 3 inicios por escenario.

| Grupo | rules_naive | rules_cal | rules_adapt | rules_twin |
|---|---|---|---|---|
| todas |  -0.03 (84/288) |  +0.53 (136/288) |  +0.59 (137/288) |  -0.06 (63/288) |
| con gemela |  -0.21 (34/144) |  +0.46 (62/144) |  +0.54 (65/144) |  +0.38 (63/144) |
| sin gemela |  +0.09 (50/144) |  +0.57 (74/144) |  +0.62 (72/144) |  -0.36 (0/144) |
| fallo step |  +0.21 (43/96) |  +0.62 (46/96) |  +0.66 (46/96) |  +0.06 (26/96) |
| fallo intermittent |  -0.93 (4/96) |  +0.18 (40/96) |  +0.30 (40/96) |  -0.51 (8/96) |
| fallo drift |  +0.09 (37/96) |  +0.57 (50/96) |  +0.65 (51/96) |  -0.01 (29/96) |
| traza 0-100m |  +0.12 (38/72) |  +0.77 (71/72) |  +0.86 (72/72) |  +0.02 (27/72) |
| traza 100m-200m |  -0.18 (18/72) |  +0.33 (38/72) |  +0.24 (33/72) |  -0.11 (19/72) |
| traza 200m-300m |  -0.47 (12/72) |  -0.00 (12/72) |  +0.10 (12/72) |  -0.36 (5/72) |
| traza 500m-600m |  -0.26 (16/72) |  -0.08 (15/72) |  +0.10 (20/72) |  -0.22 (12/72) |

## Sensibilidad uno-a-uno — recuperación agregada

Todas las formas de fallo. Cada fila cambia un único parámetro respecto al punto central.

| Variación | rules_cal | rules_adapt | rules_twin |
|---|---|---|---|
| **central** |  +0.53 (136/288) |  +0.59 (137/288) |  -0.06 (63/288) |
| alpha=0 |  +0.67 (156/288) |  +0.71 (161/288) |  +0.26 (92/288) |
| alpha=1 |  +0.40 (119/288) |  +0.47 (123/288) |  -0.35 (40/288) |
| factor=1.5 |  -0.55 (47/288) |  -0.29 (60/288) |  -1.38 (5/288) |
| factor=5 |  +0.68 (155/288) |  +0.72 (156/288) |  +0.14 (78/288) |
| mode=stop |  -1.11 (29/288) |  -0.91 (40/288) |  -0.51 (35/288) |
| repair_min=15 |  +0.77 (166/288) |  +0.80 (170/288) |  +0.27 (93/288) |
| repair_min=240 |  -0.43 (54/288) |  -0.13 (73/288) |  -1.24 (13/288) |

### Por forma de fallo — `rules_adapt` / `rules_cal`

| Variación | step | intermittent | drift |
|---|---|---|---|
| **central** | +0.66 / +0.62 | +0.30 / +0.18 | +0.65 / +0.57 |
| alpha=0 | +0.74 / +0.72 | +0.55 / +0.49 | +0.75 / +0.69 |
| alpha=1 | +0.57 / +0.54 | +0.05 / -0.06 | +0.54 / +0.45 |
| factor=1.5 | +0.04 / -0.13 | -1.54 / -1.98 | -0.12 / -0.40 |
| factor=5 | +0.73 / +0.71 | +0.57 / +0.52 | +0.77 / +0.72 |
| mode=stop | -0.42 / -0.50 | -2.88 / -3.27 | -0.62 / -0.86 |
| repair_min=15 | +0.80 / +0.78 | +0.74 / +0.69 | +0.83 / +0.79 |
| repair_min=240 | +0.16 / -0.03 | -1.15 / -1.74 | -0.03 / -0.32 |

## Desglose del coste — rejilla central, medias por escenario (minutos-pieza)

| Planificador | exceso | mant. sobre fallo | mant. falsos | latencia 1ª acción (min) | contingencia | congestión |
|---|---|---|---|---|---|---|
| noop | 9,544 | 0.0 | 0.0 | nan | 0 | 0 |
| rules_naive | 9,824 | 1.5 | 21.2 | 142 | 16,122 | 7,014 |
| rules_cal | 4,524 | 0.8 | 7.0 | 43 | 5,922 | 3,468 |
| rules_adapt | 3,897 | 0.7 | 6.3 | 56 | 4,318 | 2,281 |
| rules_twin | 10,136 | 0.7 | 9.2 | 152 | 2,158 | 8,877 |
