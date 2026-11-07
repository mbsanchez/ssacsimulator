# Diagnóstico de las capas Analyze (trazas reservadas, diseño v2, sin planificador)

Detectado: alguna alarma nombra a la estación averiada en las 24 h tras el inicio. Retraso: mediana, en horas, desde el inicio hasta esa primera alarma (escenarios detectados). Falsas alarmas: ejecuciones sin fallo de las tres trazas reservadas, traza completa.

## Detección por forma de fallo

| Detector | step: detectado / retraso (h) | intermittent: detectado / retraso (h) | drift: detectado / retraso (h) | todas |
|---|---|---|---|---|
| legacy | 34/72 / 8.5 | 35/72 / 12.0 | 39/72 / 13.5 | 108/216 / 10.9 |
| per-station (binomial) | 34/72 / 1.7 | 48/72 / 5.6 | 40/72 / 4.4 | 122/216 / 3.5 |
| per-station (threshold control) | 39/72 / 2.0 | 48/72 / 4.5 | 47/72 / 6.9 | 134/216 / 4.7 |

## Detección por estación (todas las formas)

| Detector | L0_S2 | L0_S4 | L0_S6 | L3_S35 | L0_S1 | L0_S8 | L3_S29 | L3_S33 |
|---|---|---|---|---|---|---|---|---|
| legacy | 12/27 | 10/27 | 13/27 | 14/27 | 14/27 | 12/27 | 13/27 | 20/27 |
| per-station (binomial) | 15/27 | 14/27 | 13/27 | 21/27 | 14/27 | 10/27 | 17/27 | 18/27 |
| per-station (threshold control) | 15/27 | 14/27 | 15/27 | 21/27 | 16/27 | 12/27 | 19/27 | 22/27 |

## Alarmas sin fallo

| Detector | alarmas por hora (media de las trazas) | estaciones por alarma |
|---|---|---|
| legacy | 0.61 | 7.6 |
| per-station (binomial) | 1.62 | 2.0 |
| per-station (threshold control) | 4.36 | 3.4 |

## Reglas con cada detector por estación (recuperación a 24 h, hiperparámetros por defecto)

| Detector | rules_cal | rules_adapt | rules_adapt_ctx |
|---|---|---|---|
| per-station (binomial) | +0.131 | +0.167 | +0.204 |
| per-station (threshold control) | -0.379 | -0.386 | -0.353 |
