# Controles del veto, segunda parte (solo reglas, detector por estación, diseño v2)

## 1. Todas las configuraciones del control de ráfagas

| Configuración | desarrollo | reservadas | validación |
|---|---|---|---|
| burst_ctx|size>=2 | +0.838 | +0.369 | +0.502 |
| burst|size>=2 | +0.827 | +0.347 | +0.486 |
| burst_ctx|size>=3 (elegida) | +0.889 | +0.337 | +0.396 |
| burst|size>=3 | +0.887 | +0.314 | +0.371 |
| burst_ctx|line30>=5 | +0.860 | +0.298 | +0.434 |
| burst_ctx|size>=4 | +0.870 | +0.298 | +0.339 |
| burst_ctx|line120>=8 | +0.887 | +0.282 | +0.378 |
| burst|line30>=5 | +0.872 | +0.278 | +0.414 |
| burst_ctx|size>=6 | +0.846 | +0.271 | +0.244 |
| burst|line120>=8 (elegida) | +0.890 | +0.266 | +0.331 |
| burst_ctx|line120>=5 | +0.586 | +0.266 | +0.468 |
| burst_ctx|line30>=3 | +0.743 | +0.263 | +0.378 |
| burst|size>=4 | +0.883 | +0.260 | +0.288 |
| burst|line30>=3 | +0.741 | +0.251 | +0.378 |
| burst|line120>=5 | +0.585 | +0.241 | +0.429 |
| burst_ctx|line30>=8 | +0.850 | +0.241 | +0.263 |
| burst|size>=6 | +0.859 | +0.240 | +0.182 |
| burst|line30>=8 | +0.864 | +0.215 | +0.201 |
| burst_ctx|line120>=3 | +0.224 | +0.178 | +0.219 |
| burst|line120>=3 | +0.224 | +0.170 | +0.230 |

Mejor en reservadas: burst_ctx|size>=2; mejor en validación: burst_ctx|size>=2.

## Margen del híbrido Fable

| Frente a | conjunto | Δ | IC 95 % estratificado | IC 95 % por grupos traza × estación | mejor / peor |
|---|---|---|---|---|---|
| burst_ctx|size>=3 (elegida) | reservadas | +0.075 | [+0.012, +0.140] | [+0.014, +0.143] | 124 / 19 |
| burst_ctx|size>=2 (mejor en reservadas) | reservadas | +0.043 | [-0.034, +0.117] | [-0.044, +0.124] | 40 / 86 |
| sustained|10 (exceso sostenido (elegida)) | reservadas | +0.075 | [+0.012, +0.140] | [+0.014, +0.143] | 124 / 19 |
| burst_ctx|size>=3 (elegida) | validación | +0.091 | [+0.038, +0.151] | [+0.030, +0.165] | 212 / 75 |
| burst_ctx|size>=2 (mejor en reservadas) | validación | -0.014 | [-0.070, +0.046] | [-0.072, +0.048] | 91 / 184 |
| sustained|10 (exceso sostenido (elegida)) | validación | +0.134 | [+0.083, +0.193] | [+0.073, +0.207] | 224 / 63 |
| burst_ctx|size>=2 (mejor en validación) | validación | -0.014 | [-0.070, +0.046] | [-0.072, +0.048] | 91 / 184 |

## 2. Control con exceso sostenido: selección en desarrollo

| R | desarrollo |
|---|---|
| 1.5 | +0.855 |
| 2 | +0.877 |
| 3 | +0.871 |
| 5 | +0.871 |
| 10 | +0.889 |

Elegido: sustained|10. Reservadas +0.337 [+0.238, +0.431]; validación +0.353 [+0.273, +0.423]; reparaciones falsas por escenario (reservadas) 2.8.
