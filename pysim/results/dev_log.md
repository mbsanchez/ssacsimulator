# Registro de desarrollo de los planificadores LLM

Protocolo: el prompt y el contexto recuperado se iteran **solo** sobre la traza
`test_cases_0-100m.td`. Las trazas 100m-200m, 200m-300m y 500m-600m quedan
reservadas para la evaluación final, con el prompt congelado. Cada entrada
registra una versión probada; ninguna se borra.

Caso central: fallo x3 desde t₀ + 600 min, reparación 60 min, α = 0,5,
contingencia, detector legacy. Calibración de tasas base sobre 100m-200m.

## 2026-10-05 — prompt v1, model qwen2.5:7b, trace test_cases_0-100m.td

Primera versión. Solo dos casos, ejecutados a mano (antes de existir `dev_llm.py`).

| Caso | rules_cal | rules_adapt | rules_twin | c1 | c2 |
|---|---|---|---|---|---|
| L0_S2 step | +0.73 · 35 FP | -0.01 · 4 FP | +0.78 · 26 FP | +0.80 · 26 FP | +0.74 · 48 FP |
| L3_S29 step | +0.65 · 37 FP | +0.82 · 6 FP | -0.19 · 32 FP | -0.16 · 32 FP | +0.65 · 49 FP |

Observaciones que motivan la v2:
- C1 reproduce exactamente el control `rules_twin`: actúa solo donde hay gemela libre.
- C2 detecta el fallo sin gemela que C1 ignora, pero empata con `rules_cal` con más falsos positivos.
- C2 repara estaciones que él mismo describe como sanas; invierte la regla sobre reparaciones sin efecto; afirma gemelas inexistentes; toma por "tasa alta" una alarma en las 2 primeras horas.

## 2026-10-05 11:25 — prompt v2, model qwen2.5:7b, trace test_cases_0-100m.td

v2: veredicto obligatorio por estación antes de la acción (el código descarta acciones incoherentes); historia insuficiente < 8 h; alarmas observadas frente a esperadas en 2 h y 24 h; resultado de reparaciones digerido; estado de la gemela dentro del bloque de cada estación.

| Caso | rules_cal | rules_adapt | rules_twin | c2 |
|---|---|---|---|---|
| fault-free | 284/h · 36 FP | 26/h · 4 FP | 214/h · 27 FP | 165/h · 22 FP |
| L0_S2 step | +0.73 · 35 FP | -0.02 · 4 FP | +0.78 · 26 FP | +0.82 · 21 FP |
| L3_S29 step | +0.65 · 37 FP | +0.82 · 6 FP | -0.19 · 32 FP | +0.76 · 24 FP |
| L0_S8 drift | +0.77 · 37 FP | +0.94 · 6 FP | -0.17 · 32 FP | +0.86 · 20 FP |

Fault-free: false-alarm cost in piece-minutes per hour. Faults: recovery vs. no action. FP = repairs of healthy stations.

- c2: 171 calls, verdicts {'insufficient_evidence': 630, 'degraded': 115, 'normal': 120, 'self_inflicted': 49}, problems {'no free twin': 16}

Observaciones sobre la v2:
- C2 supera a `rules_cal` en los cuatro casos y reduce a la mitad los falsos positivos de la v1 (48 → 21 en L0_S2). Es el único planificador sin ningún caso malo (peor: +0.76; `rules_adapt` cae a −0.02 en L0_S2).
- `rules_adapt` sigue siendo el más preciso sin fallo (26/h frente a 165/h) y el mejor en L3_S29 y L0_S8.
- **En L0_S2 los aciertos no son detecciones.** C2 obtuvo sus 41 respuestas de la caché de la corrida sin fallo: recibió los mismos prompts con y sin fallo, así que su reparación de L0_S2 fue de rutina. `rules_cal` y `rules_twin` hacen también el mismo número de acciones que sin fallo. El detector legacy apenas ve este fallo. De aquí sale la métrica de **acierto específico** de `llm_sweep.py`.
- 630 de 914 veredictos son "insufficient_evidence", sobre todo durante las 8 h iniciales sin historia.
- Rendimiento: ~19 s por llamada nueva con prompts de ~1.900 tokens, con la máquina en presión de memoria (9,5 GB de swap). Sin truncado: prompt máximo 3.261 tokens < 4.096.

## 2026-10-06 06:49 — prompts (hybrid: v2+h1), model qwen2.5:7b, trace test_cases_0-100m.td

h1: híbrido. La regla adaptativa selecciona las estaciones; el LLM (contexto de C2 + sufijo h1) confirma o veta y elige la acción. Una estación vetada no se reconsulta durante 120 min. Control nuevo: rules_adapt_ctx (adaptativa que no actúa sobre estaciones que reciben carga desviada).

| Caso | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid |
|---|---|---|---|---|---|
| fault-free | 284/h · 36 FP | 26/h · 4 FP | 214/h · 27 FP | 18/h · 2 FP | 8/h · 1 FP |
| L0_S2 step | +0.73 · 35 FP | -0.02 · 4 FP | +0.78 · 26 FP | -0.01 · 2 FP | -0.01 · 1 FP |
| L3_S29 step | +0.65 · 37 FP | +0.82 · 6 FP | -0.19 · 32 FP | +0.83 · 5 FP | +0.84 · 4 FP |
| L0_S8 drift | +0.77 · 37 FP | +0.94 · 6 FP | -0.17 · 32 FP | +0.94 · 5 FP | +0.94 · 5 FP |

Fault-free: false-alarm cost in piece-minutes per hour. Faults: recovery vs. no action. FP = repairs of healthy stations.

- hybrid: 17 calls, verdicts {'degraded': 16, 'self_inflicted': 4}, problems none
