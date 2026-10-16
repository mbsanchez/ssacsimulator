# Controles del veto (solo reglas, detector por estación, diseño v2)

## Selección en la traza de desarrollo (recuperación a 24 h)

| Configuración | recuperación |
|---|---|
| burst|line120>=8 | +0.890 |
| burst_ctx|size>=3 | +0.889 |
| burst|size>=3 | +0.887 |
| burst_ctx|line120>=8 | +0.887 |
| burst|size>=4 | +0.883 |
| burst|line30>=5 | +0.872 |
| burst_ctx|size>=4 | +0.870 |
| burst|line30>=8 | +0.864 |
| burst_ctx|line30>=5 | +0.860 |
| burst|size>=6 | +0.859 |
| rules_adapt | +0.856 |
| burst_ctx|line30>=8 | +0.850 |
| burst_ctx|size>=6 | +0.846 |
| rules_adapt_ctx | +0.842 |
| burst_ctx|size>=2 | +0.838 |
| burst|size>=2 | +0.827 |
| burst_ctx|line30>=3 | +0.743 |
| burst|line30>=3 | +0.741 |
| burst_ctx|line120>=5 | +0.586 |
| burst|line120>=5 | +0.585 |
| burst_ctx|line120>=3 | +0.224 |
| burst|line120>=3 | +0.224 |

Elegidas: burst|line120>=8 y burst_ctx|size>=3.

## Evaluación

| Planificador | reservadas [IC 95 %] | validación [IC 95 %] | reparaciones falsas / escenario (reservadas) |
|---|---|---|---|
| rules_adapt | +0.167 [+0.049, +0.269] | +0.103 [-0.002, +0.192] | 5.9 |
| rules_adapt_ctx | +0.204 [+0.092, +0.301] | +0.165 [+0.066, +0.248] | 5.5 |
| burst|line120>=8 | +0.266 [+0.161, +0.360] | +0.331 [+0.250, +0.402] | 4.2 |
| burst_ctx|size>=3 | +0.337 [+0.238, +0.431] | +0.396 [+0.319, +0.466] | 2.8 |
| randveto|0 | +0.192 [+0.098, +0.288] | +0.182 [+0.113, +0.251] | 1.8 |
| randveto|1 | +0.169 [+0.076, +0.261] | +0.170 [+0.098, +0.241] | 1.6 |
| randveto|2 | +0.136 [+0.056, +0.220] | +0.122 [+0.031, +0.208] | 1.8 |
| randveto|3 | +0.162 [+0.056, +0.261] | +0.100 [+0.028, +0.172] | 2.4 |
| randveto|4 | +0.086 [-0.003, +0.175] | +0.178 [+0.097, +0.256] | 2.2 |

Veto aleatorio (tasa 0.7), media de 5 semillas: reservadas +0.149 (rango +0.086 a +0.192); validación +0.151 (rango +0.100 a +0.182).
