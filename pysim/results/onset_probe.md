# Diseño del inicio del fallo: comprobación solo con reglas

Trazas reservadas. «original»: inicio a 600 min, una reparación elimina todo fallo iniciado antes de que termine. «clears_fixed»: inicio a 600 min, solo se eliminan los fallos activos al empezar la reparación. «random_onset»: regla corregida y 3 inicios por escenario, uniformes entre 24 h tras el primer evento y 24 h antes del último (semilla 0); 216 escenarios.

| Planificador | diseño | todas | escalón | intermitente | deriva |
|---|---|---|---|---|---|
| rules_naive | original | +0.016 | +0.233 | -1.182 | +0.207 |
| rules_naive | clears_fixed | -0.048 | +0.153 | -1.269 | +0.168 |
| rules_naive | random_onset | -0.647 | -0.405 | -2.495 | -0.259 |
| rules_cal | original | +0.449 | +0.564 | -0.197 | +0.555 |
| rules_cal | clears_fixed | +0.431 | +0.534 | -0.225 | +0.553 |
| rules_cal | random_onset | -0.213 | -0.059 | -1.259 | -0.010 |
| rules_adapt | original | +0.519 | +0.618 | -0.064 | +0.620 |
| rules_adapt | clears_fixed | +0.519 | +0.618 | -0.064 | +0.620 |
| rules_adapt | random_onset | +0.159 | +0.248 | -0.551 | +0.311 |
| rules_adapt_ctx | original | +0.538 | +0.632 | -0.021 | +0.635 |
| rules_adapt_ctx | clears_fixed | +0.538 | +0.632 | -0.021 | +0.635 |
| rules_adapt_ctx | random_onset | +0.187 | +0.265 | -0.475 | +0.333 |
| rules_twin | original | -0.307 | -0.159 | -1.104 | -0.183 |
| rules_twin | clears_fixed | -0.345 | -0.207 | -1.150 | -0.207 |
| rules_twin | random_onset | -0.707 | -0.545 | -1.886 | -0.467 |
