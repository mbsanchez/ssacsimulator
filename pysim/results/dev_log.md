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

## 2026-10-06 09:42 — prompts (hybrid: v2+h1, c2: v2), model claude-fable-5-1, trace test_cases_0-100m.td

Piloto con Claude Fable 5.1 vía Agent SDK (plan Max), effort low. Prompts v2 / v2+h1 congelados, sin reajuste para este modelo. Objetivo: comparar con Qwen en desarrollo y medir el consumo de la cuota semanal de Fable (1% antes del piloto).

| Caso | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid | c2 |
|---|---|---|---|---|---|---|
| fault-free | 284/h · 36 FP | 26/h · 4 FP | 214/h · 27 FP | 18/h · 2 FP | 0/h · 0 FP | 179/h · 25 FP |
| L0_S2 step | +0.73 · 35 FP | -0.02 · 4 FP | +0.78 · 26 FP | -0.01 · 2 FP | +0.00 · 0 FP | +0.81 · 24 FP |
| L3_S29 step | +0.65 · 37 FP | +0.82 · 6 FP | -0.19 · 32 FP | +0.83 · 5 FP | +0.84 · 4 FP | +0.76 · 25 FP |
| L0_S8 drift | +0.77 · 37 FP | +0.94 · 6 FP | -0.17 · 32 FP | +0.94 · 5 FP | +0.95 · 4 FP | +0.87 · 22 FP |

Fault-free: false-alarm cost in piece-minutes per hour. Faults: recovery vs. no action. FP = repairs of healthy stations.

- hybrid: 15 calls, verdicts {'insufficient_evidence': 3, 'normal': 3, 'degraded': 10}, problems none
- c2: 151 calls, verdicts {'insufficient_evidence': 566, 'degraded': 99, 'self_inflicted': 84, 'normal': 21}, problems none
- backend agent-sdk, effort low: 166 calls (92 cached), API-equivalent cost $33.83, retries 0

> **Entrada anterior INVÁLIDA (piloto Fable 5.1).** El Agent SDK cargaba los conectores MCP de la cuenta de claude.ai (Atlassian, Google Drive, etc.) en cada llamada: ~19.000 tokens de definiciones de herramientas ajenas al experimento, visibles para el modelo. Se corrige con `--strict-mcp-config` sin configuración MCP (`ssac/agent_sdk_client.py`, harness `strict-mcp-v1`, incluido en la clave de caché para que ninguna respuesta contaminada se reutilice). Coste equivalente por llamada: ~$0,46 → ~$0,025. Sus cifras no se usan; el piloto se repite a continuación.

## 2026-10-06 10:00 — prompts (hybrid: v2+h1, c2: v2), model claude-fable-5-1, trace test_cases_0-100m.td

Piloto Fable 5.1 REPETIDO con harness limpio (strict-mcp-v1: sin conectores MCP). Prompts v2 / v2+h1 congelados, effort low.

| Caso | rules_cal | rules_adapt | rules_twin | rules_adapt_ctx | hybrid | c2 |
|---|---|---|---|---|---|---|
| fault-free | 284/h · 36 FP | 26/h · 4 FP | 214/h · 27 FP | 18/h · 2 FP | 9/h · 1 FP | 158/h · 22 FP |
| L0_S2 step | +0.73 · 35 FP | -0.02 · 4 FP | +0.78 · 26 FP | -0.01 · 2 FP | -0.01 · 1 FP | +0.81 · 21 FP |
| L3_S29 step | +0.65 · 37 FP | +0.82 · 6 FP | -0.19 · 32 FP | +0.83 · 5 FP | +0.84 · 3 FP | +0.78 · 22 FP |
| L0_S8 drift | +0.77 · 37 FP | +0.94 · 6 FP | -0.17 · 32 FP | +0.94 · 5 FP | +0.95 · 4 FP | +0.88 · 22 FP |

Fault-free: false-alarm cost in piece-minutes per hour. Faults: recovery vs. no action. FP = repairs of healthy stations.

- hybrid: 15 calls, verdicts {'normal': 4, 'degraded': 11, 'insufficient_evidence': 1}, problems none
- c2: 170 calls, verdicts {'insufficient_evidence': 853, 'degraded': 90, 'self_inflicted': 40, 'normal': 38}, problems none
- backend agent-sdk, effort low: 185 calls (102 cached), API-equivalent cost $7.74, retries 0

## 2026-10-11 — Diseño de evaluación v2 (registrado antes de ejecutar ningún LLM con él)

**Motivo.** Una auditoría adversarial del diseño de evaluación mostró que el diseño v1 premia reparaciones rutinarias que coinciden con el instante fijo del fallo: (a) todo fallo se inyectaba 600 min después del primer evento, justo después del calentamiento de 8 h de la memoria de C2, que concentra ahí una ráfaga de reparaciones (C2-Fable hace 21 de sus 33 reparaciones sin fallo de 100m-200m en [t0−120, t0+240]); (b) una reparación eliminaba también los fallos iniciados *durante* ella (C2-Fable repara L0_S1 en 200m-300m 12 min antes del fallo y el fallo no cuesta nada). Sin los 3 escenarios afectados, Δ(C2-Fable − adaptativa+veto) pasa de +0,043 a +0,016. Una comprobación solo con reglas (`onset_probe.py`, `results/onset_probe.md`) muestra además que la recuperación sobre la traza completa depende fuertemente del instante del fallo (adaptativa+veto: +0,54 con inicio a 600 min, +0,19 con inicios aleatorios).

**Qué no cambia.** Prompts (v2, v2+h1), modelos, planificadores, hiperparámetros por defecto de las reglas, estaciones, formas y severidad (k=3), trazas reservadas y calibración cruzada. Ningún prompt se modifica.

**Qué cambia (v2).**
1. *Regla de reparación*: una reparación elimina solo los fallos ya activos cuando empieza (`EffectModel.repair_clears="active_at_start"`, nuevo valor por defecto).
2. *Inicio del fallo*: 3 inicios por (traza, estación, forma), uniformes entre 24 h después del primer evento y 24 h antes del último, generados con una semilla derivada del nombre del escenario (`ssac/onsets.py`). 216 escenarios con fallo en las reservadas (antes 72).
3. *Métrica primaria*: recuperación agregada en un horizonte de 24 h tras el inicio del fallo, sobre el retraso añadido a las transiciones que ocurren en [t0, t0+24 h). Secundaria: la misma con 8 h (un turno). La recuperación sobre la traza completa deja de calcularse para los escenarios con fallo, porque cada corrida se detiene en t0+24 h.
4. *Reparaciones falsas, aciertos y latencia*: contados dentro del horizonte de 24 h.
5. *Coste de falsas alarmas*: sin cambios (corridas sin fallo, traza completa).
6. *Reglas reajustadas*: la rejilla se vuelve a seleccionar en la traza de desarrollo con el diseño v2.
7. *Estadística*: estimando primario la diferencia de recuperación a 24 h con bootstrap estratificado por traza; secundarios, Wilcoxon emparejado por escenario y bootstrap de dos niveles por traza.

Los resultados v1 quedan en el historial de git (etiqueta `design-v1`).
