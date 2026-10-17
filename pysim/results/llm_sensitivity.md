# Sensibilidad de los planificadores (trazas reservadas, detector por estación, diseño v2)

Recuperación neta a 24 h. `rules_burst*` en la condición central: `results/veto_controls/` (misma configuración).

| Condición | escenarios | rules_cal | rules_adapt | rules_adapt_ctx | rules_cal_rt | rules_adapt_ctx_rt | rules_burst | rules_burst_ctx | hybrid | hybrid:fable-5.1 | Fable − burst_ctx [IC 95 %] | Fable − mejor regla [IC 95 %] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| central (k = 3, 60 min, α = 0,5, contingencia) | 216 | +0.13 | +0.17 | +0.20 | +0.27 | +0.18 | +0.27 | +0.34 | +0.29 | +0.41 | +0.08 [+0.01, +0.14] | +0.08 [+0.01, +0.14] (rules_burst_ctx) |
| k = 1,5 | 216 | -1.51 | -1.47 | -1.30 | -0.79 | -1.37 | -0.90 | -0.44 | -0.95 | -0.07 | +0.37 [+0.29, +0.46] | +0.37 [+0.29, +0.46] (rules_burst_ctx) |
| k = 5 | 216 | +0.37 | +0.41 | +0.43 | +0.43 | +0.41 | +0.44 | +0.47 | +0.47 | +0.50 | +0.02 [-0.04, +0.08] | +0.02 [-0.04, +0.08] (rules_burst_ctx) |
| reparación 15 min | 216 | +0.54 | +0.58 | +0.58 | +0.53 | +0.56 | +0.57 | +0.53 | +0.59 | +0.56 | +0.03 [-0.01, +0.08] | -0.03 [-0.08, +0.02] (rules_adapt) |
| reparación 240 min | 216 | -1.22 | -1.22 | -0.86 | -0.81 | -0.94 | -0.82 | -0.20 | -0.90 | -0.09 | +0.11 [+0.02, +0.20] | +0.11 [+0.02, +0.20] (rules_burst_ctx) |
| modo parada | 216 | -2.48 | -2.55 | -1.75 | -1.40 | -1.37 | -1.70 | -0.76 | -1.86 | -0.56 | +0.20 [+0.11, +0.30] | +0.20 [+0.11, +0.30] (rules_burst_ctx) |
| α = 0 | 216 | +0.37 | +0.41 | +0.46 | +0.43 | +0.46 | +0.44 | +0.45 | +0.40 | +0.46 | +0.01 [-0.05, +0.07] | +0.00 [-0.06, +0.06] (rules_adapt_ctx) |
| α = 1 | 216 | -0.07 | -0.03 | -0.01 | +0.13 | -0.04 | +0.14 | +0.23 | +0.18 | +0.36 | +0.13 [+0.06, +0.20] | +0.13 [+0.06, +0.20] (rules_burst_ctx) |
| causa común (4 estaciones) | 54 | +0.50 | +0.52 | +0.53 | +0.51 | +0.53 | +0.41 | +0.36 | +0.55 | +0.43 | +0.07 [-0.02, +0.15] | -0.10 [-0.17, -0.05] (rules_adapt_ctx) |

## Réplicas del híbrido Fable sin reutilizar respuestas de la evaluación reservada

| Ejecución | recuperación 24 h [IC 95 %] | Δ frente a rules_adapt_ctx | llamadas nuevas |
|---|---|---|---|
| original | +0.413 [+0.318, +0.501] | +0.208 | – |
| réplica 1 | +0.427 [+0.332, +0.518] | +0.223 | 337 |
| réplica 2 | +0.415 [+0.319, +0.508] | +0.211 | 328 |
| réplica 3 | +0.417 [+0.321, +0.508] | +0.213 | 323 |
