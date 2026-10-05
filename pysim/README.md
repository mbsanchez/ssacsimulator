# Motor SSAC headless (Python)

Puerto a Python, sin interfaz gráfica, del núcleo de simulación de
**SSACSimulator** (Qt/C++), para poder ejecutar experimentos en lote.

Paper base: M. Sánchez, E. Exposito, J. Aguilar, *Implementing self-\* autonomic
properties in self-coordinated manufacturing processes for the Industry 4.0
context*, Computers in Industry 121, 103247 (2020).

---

## Qué se portó y qué no

| Original (C++/Qt) | LOC | Aquí |
|---|---|---|
| `businessprocess.{h,cpp}` | 571 | `ssac/model.py` |
| `simulationevent.{h,cpp}` | 446 | `ssac/events.py` |
| `simulationengine.{h,cpp}` | 422 | `ssac/engine.py` |
| `smartobject.{h,cpp}` — reloj | 275 | `ssac/engine.py` (`Piece`), solo el reloj |
| `smartobject` — pintado y geometría slerp | — | **descartado** |
| `MainWindow`, `QGraphicsViewEc`, `QGVCore` | 1.219 | **descartado** |

La GUI Qt se conserva intacta en el repositorio original; sirve para generar
figuras y la demostración del paper. Este puerto es para los experimentos.

## Uso

```bash
python3 run_sim.py \
  --model  "DataSets I4.0/bosch_pl_tm_model.pg" \
  --events "DataSets I4.0/test_cases_0-100m.td" \
  --jsonl  detections.jsonl
```

Opciones: `--all-events` (el original se detiene en 100.000), `--speed N`
(granularidad del reloj, por defecto 150), `--max-ticks N`.

```bash
python3 -m pytest tests/ -q      # 14 tests, ~73 s
```

Sin dependencias fuera de la biblioteca estándar (`pytest` solo para los tests).

---

## Lo que el original implementa realmente

Esto es el hallazgo central de la revisión del código, y es la base del
reencuadre del paper nuevo.

| Fase MAPE-K | Estado en el código publicado |
|---|---|
| **Monitor** | ✅ Real: lectura de eventos, reloj virtual, conteo de tiempos por arista y global |
| **Analyze** | ⚠️ Tres umbrales cableados |
| **Plan** | ❌ **Ausente** |
| **Execute** | ❌ **Ausente** |
| **K (Knowledge)** | ❌ **Ausente**: hay grafo de proceso y un predictor Bosch entrenado offline, no ontología ni base de reglas |

`emitReconfiguration()` emite una señal que la GUI convierte en una línea de log
—*"launching the autonomous cycle for reconfiguration"*— y nada más. El ciclo
autonómico se anuncia; no se planifica ni se ejecuta.

Los tres umbrales del Analyze:

```
estación :  media(duración de la arista)  >  tiempo_referencia_arista * 1.3
estaciones: nº actores marcados en un lote simultáneo  >  10% de los actores
global   :  media(vida de pieza)  >  process_througout_time * 1.1
```

Este puerto mantiene esa frontera explícita en lugar de disimularla: `Detection`
registra la emisión y nada actúa sobre ella.

---

## Resultados sobre el dataset publicado

`bosch_pl_tm_model.pg` + `test_cases_0-100m.td`, velocidad por defecto 150:

```
actores 54 · aristas 285 (84 visibles) · throughout 6420 min · casos 1.183.165
eventos procesados 100.000 · piezas entradas 10.295 · completadas 6.715 · atascadas 3.580

PREDICTED_FAILURE      0
STATION_FAILURE       39
GLOBAL_FAILURE         0
```

Las tres observaciones que esto produce son material directo para la motivación
del paper nuevo:

**1. Solo uno de los tres detectores self-\* se dispara.** 39 detecciones, todas
de tipo estación.

**2. `PREDICTED_FAILURE` nunca se dispara, y casi no puede.** No es un defecto
del puerto: la columna `prediction` de este fichero solo contiene −1 y 0. En los
cuatro ficheros `.td` del repositorio hay en total **15 filas** con
`prediction == 1` sobre 400.000 eventos (0 / 0 / 3 / 12). Las 15 son el primer
evento de su caso, así que las 15 sí dispararían — pero el detector está
ejercitado por el 0,004% de los datos.

**3. `GLOBAL_FAILURE` es inalcanzable con estos datos.** El umbral es
6420 × 1,1 = 7062 min; la vida media de pieza medida es **635,6 min**, un orden
de magnitud por debajo. La condición no puede cumplirse: o el
`process_througout_time` no corresponde a estos datos, o el detector está
descalibrado.

**4. 45 de 285 aristas tienen tiempo de referencia 0,0**, lo que pone su umbral
en 0: cualquier duración positiva marca la estación como fallando. De ahí que
`STATION_FAILURE` sea el único que aparece.

En conjunto: el sistema de 2020 no solo carece de Plan y Execute — su capa
Analyze está apenas ejercitada por su propio dataset publicado. Eso refuerza el
encuadre *"From Detection to Action"* en lugar de debilitarlo.

---

## Fidelidad: detalles que cambian resultados

Están documentados en el código, pero conviene tenerlos a la vista.

- **Límite de 100.000 eventos.** El original fija
  `DATA_INITIAL_CHUNK_LENGHT = 100000` y nunca vuelve a llamar a
  `getNextChunck`, así que una corrida cubre como máximo los primeros 100.000
  eventos del fichero. `max_events` reproduce eso por defecto; `--all-events`
  lee el fichero completo.

- **Umbrales en binario32.** El C++ guarda los tiempos de referencia como
  `float` y compara contra literales `1.3f` / `1.1f`. Calcularlo en doble
  precisión desplaza comparaciones en el límite, así que `ssac/numeric.f32()`
  redondea a 32 bits donde el original lo hacía.

- **Filas malformadas.** El original descarta una fila solo si **ambos**
  `duration` y `start` fallan al parsear (`if(!durationOk && !startTimeOk)` —
  AND, no OR). Una fila con duración basura pero `start` válido **se conserva**
  con duración 0,0, porque `QString::toDouble` devuelve 0.0 al fallar. Parece un
  bug; es el comportamiento publicado, así que se reproduce y se cuenta en
  `LoadReport`.

- **La bandera `show`.** En la aplicación Qt una pieza solo sigue una arista que
  se añadió a la escena, que es exactamente el conjunto con `show == True`. Sin
  gráficos usamos la bandera directamente. Importa: con `show == False` el
  `endActor` de la pieza queda vacío, la pieza nunca alcanza un actor final y
  **se queda en el sistema para siempre** — de ahí las 3.580 piezas atascadas.

- **Una desviación deliberada.** En C++ `dxMillis = eventStartTime - _currentTimeMillis`
  es sin signo, así que un evento fuera de orden provoca desbordamiento y un
  `dx` enorme: comportamiento indefinido. Aquí se acota a 0 y se cuenta en
  `RunStats.clock_regressions`, para que un fichero no monótono sea visible en
  lugar de corromper la corrida en silencio. Con los datos publicados el
  contador queda en 0.

---

## Lo que todavía NO está validado

Los 14 tests fijan que el puerto se comporta como **el código fuente C++ leído**,
y que el dataset publicado produce los números de arriba. **No** demuestran
paridad con el binario Qt: para eso hay que compilar el original y comparar.

Para cerrar la puerta del 17 de octubre como corresponde:

1. Compilar `SSACSimulator` (Qt5 + GraphViz; `CMAKE_MINIMUM_REQUIRED(2.6)`, así
   que probablemente haya que modernizar el build o usar un Qt5 antiguo).
2. Cargar el mismo `.pg` y `.td`, velocidad 150, y volcar el panel de log.
3. Comparar el número y el orden de las líneas de reconfiguración contra
   `detections.jsonl`. Esperado: 39 líneas de estación, ninguna de predicción,
   ninguna global.

Si no coinciden, la discrepancia está en una de las zonas marcadas arriba, y la
candidata más probable es el acoplamiento `show` / `gvEdge`.

## Rendimiento

~0,2–0,4 s por corrida (antes ~12 s en la traza corta y varios minutos en la de
10.098 min).

El original avanza el reloj de animación de **todas** las piezas en **cada**
tick. Pero una pieza solo puede salir del sistema si su `end_actor` es un nodo
final, y el reloj de cualquier otra pieza nunca se observa: `set_path()` lo
reinicia en su siguiente evento. Así que solo hace falta avanzar las piezas que
van hacia END —un puñado en cada momento—, frente a miles de piezas atascadas.
El orden de salida se conserva con un número de secuencia.

El bucle original sigue disponible (`step_all_pieces=True`) como oráculo, y
`tests/test_parity.py::test_fast_path_is_identical_to_original_loop` comprueba
que ambos dan exactamente las mismas detecciones, decisiones, vidas de pieza y
estadísticas, también con fallos, planificador y el detector por estación.

Un primer intento —recorrer solo las piezas "en animación"— fue **más lento**:
casi todas lo están. La observación útil no era quién anima, sino quién puede
salir.

## Capa Plan / Execute (nueva — no existe en el original)

| Módulo | Qué hace |
|---|---|
| `ssac/topology.py` | Detecta estaciones gemelas: mismos predecesores y sucesores en aristas visibles. **29 de 52** estaciones tienen gemela (p. ej. L0_S2/L0_S3, 339k/334k casos). |
| `ssac/actions.py` | Espacio de acciones (`Reroute`, `Restore`, `Maintenance`, `NoOp`) y el **validador simbólico** contra el grafo y el estado actual. |
| `ssac/intervention.py` | Inyección de fallos y modelo de efectos de las acciones (Execute). |
| `ssac/planning.py` | Interfaz de planificador y las tres líneas base por reglas. |
| `ssac/calibration.py` | Tasas base de alarmas por estación, aprendidas de una traza sin fallos. |
| `ssac/metrics.py` | Retraso en exceso por pieza frente a una corrida de referencia sin fallo. |
| `experiment.py` | Runner: referencia, no-acción y planificadores, por escenario. |
| `sweep.py` | Barrido de sensibilidad en paralelo; escribe `results/`. |

### Supuestos del modelo de efectos

Son las decisiones de modelado que un revisor va a cuestionar. Las que no se
pueden fundamentar en datos —el dataset Bosch está anonimizado y no trae
capacidades, tiempos de reparación ni averías etiquetadas— son **ejes del
barrido de sensibilidad** (`sweep.py`), no valores fijos.

- **Simulación dirigida por traza.** Los instantes de inicio vienen de los datos y no se desplazan. Fallos y acciones actúan sobre las *duraciones*. El retraso no se propaga como cola: el modelo estima tiempo perdido por pieza, no es una simulación de colas. Sin capacidades por estación no es posible hacerlo mejor.
- **Efectos aditivos, proporcionales al tiempo de proceso τ_S.** Una "transición" Bosch es el tiempo entre dos marcas de estación y mide sobre todo **espera**, no trabajo: mediana 0 min, p90 30 min, pero p99 de 4.000–6.000 min, y en tres de las cuatro trazas más del 84% del tiempo total está en transiciones de más de un día (almacén, buffers, retrabajo). Por eso ningún efecto multiplica la transición completa: todos **suman** una cantidad proporcional a τ_S, la mediana de las transiciones de hasta 60 min que salen de S por aristas visibles. τ_S es muy estable entre trazas (12 min en L0_S2, 6 min —la granularidad de las marcas— en casi todas las demás). Forma parte del mundo simulado; ningún planificador la ve.
- **Fallos sintéticos, tres formas.** Toda transición que sale de S suma `(k(t) − 1)·τ_S`:
  - *escalón*: k desde t₀ (rotura súbita);
  - *intermitente*: k durante 60 min, normal durante 120 min, y se repite (contacto flojo);
  - *deriva*: k sube linealmente de 1 a k en 600 min y se mantiene (desgaste).
- **Reroute(S, T, f):** una fracción determinista f de las piezas que entran en S va a su gemela T (selección por CRC32 del id de caso: reproducible). T se congestiona: suma `α·f_total·τ_T`. **α no tiene base empírica**; se barre en {0; 0,5; 1}.
- **Maintenance(S, d):** los fallos de S iniciados antes de `t + d` se eliminan en `t + d`, y en ese momento se levanta cualquier reroute de S. **d no se conoce**; se barre en {15; 60; 240} min. Durante la reparación hay dos modos:
  - *contingencia* (por defecto): capacidad de respaldo fuera del modelo procesa las piezas, sumando `(1,5 − 1)·τ_S`; el fallo no aplica. Refleja que una planta como la de Bosch tiene planes de contingencia y no para la línea por mantener una estación.
  - *parada*: las piezas esperan a que termine la reparación (`+ (t_fin − t)`). Es la cota pesimista.

  En ambos modos, mantener una estación sana cuesta algo y no arregla nada: por eso las falsas alarmas tienen coste.

> **Corrección importante.** Una versión anterior multiplicaba la duración completa de la transición. Con transiciones de hasta un mes, eso hacía que un fallo o una acción estirasen días de almacenamiento, y los costes dependían de qué transiciones largas caían dentro de una ventana de acción. Los primeros resultados que se obtuvieron con ese modelo (recuperaciones de −25 o −58) eran artefactos y se han descartado. `tests/test_interventions.py::test_effects_do_not_stretch_waiting_time` fija el comportamiento correcto.

### Planificadores

| | Qué hace | Conocimiento que usa |
|---|---|---|
| `noop` | Detecta y no hace nada — lo que hace el sistema de 2020 | — |
| `rules_naive` | Actúa sobre cada estación nombrada en una alarma | ninguno |
| `rules_cal` | Actúa cuando la cuenta de alarmas en 120 min es improbable (cola de Poisson, α = 1e-3) bajo una tasa base aprendida en **otra** traza | tasas base históricas |
| `rules_adapt` | Igual, pero la tasa base es la de los 1.440 min anteriores de la **misma** traza, de forma causal | historia reciente propia |

Los tres que actúan comparten la misma respuesta: desviar a una gemela libre si existe, y reparar.

### Resultados del barrido (`sweep.py`)

968 corridas: 4 trazas (cada una con los planificadores calibrados en **otra**), 8 estaciones (4 con gemela, 4 sin), 3 formas de fallo, más sensibilidad uno-a-uno y corridas sin fallo. Detector original (legacy). ~1 minuto en 7 núcleos. Datos completos en `results/sweep.csv`.

La métrica es la **recuperación agregada**, `1 − Σ exceso(política) / Σ exceso(no hacer nada)`, y entre paréntesis en cuántos escenarios la política tiene beneficio neto. No se usa la mediana de recuperaciones por escenario: cuando un fallo cuesta poco, dividir por él un coste fijo de falsas alarmas da cocientes sin sentido.

#### Coste de las falsas alarmas — corridas SIN fallo

Minutos-pieza perdidos por hora de operación, solo por actuar sobre ruido. Punto central.

| Traza | rules_naive | rules_cal | rules_adapt |
|---|---|---|---|
| test_cases_0-100m.td | 457 | 284 | 26 |
| test_cases_100m-200m.td | 264 | 94 | 20 |
| test_cases_200m-300m.td | 307 | 121 | 71 |
| test_cases_500m-600m.td | 340 | 108 | 111 |

#### Rejilla central — recuperación agregada (escenarios con beneficio neto > 0)

Recuperación agregada = 1 − Σ exceso(política) / Σ exceso(no hacer nada). Detector legacy; fallo x3, reparación 60 min, α = 0,5, contingencia.

| Grupo | rules_naive | rules_cal | rules_adapt |
|---|---|---|---|
| todas |  -0.11 (37/96) |  +0.49 (73/96) |  +0.56 (69/96) |
| con gemela |  -0.49 (11/48) |  +0.33 (30/48) |  +0.35 (29/48) |
| sin gemela |  +0.11 (26/48) |  +0.58 (43/48) |  +0.68 (40/48) |
| fallo step |  +0.14 (17/32) |  +0.59 (30/32) |  +0.64 (29/32) |
| fallo intermittent |  -1.40 (3/32) |  -0.09 (13/32) |  +0.07 (13/32) |
| fallo drift |  +0.10 (17/32) |  +0.60 (30/32) |  +0.66 (27/32) |
| traza 0-100m |  +0.43 (19/24) |  +0.58 (21/24) |  +0.66 (17/24) |
| traza 100m-200m |  +0.04 (10/24) |  +0.63 (21/24) |  +0.75 (22/24) |
| traza 200m-300m |  -0.87 (4/24) |  +0.15 (13/24) |  +0.23 (12/24) |
| traza 500m-600m |  -0.39 (4/24) |  +0.47 (18/24) |  +0.48 (18/24) |

#### Sensibilidad uno-a-uno — recuperación agregada

Fallo escalón. Cada fila cambia un único parámetro respecto al punto central.

| Variación | rules_cal | rules_adapt |
|---|---|---|
| **central** |  +0.59 (30/32) |  +0.64 (29/32) |
| alpha=0 |  +0.74 (32/32) |  +0.73 (29/32) |
| alpha=1 |  +0.47 (25/32) |  +0.56 (25/32) |
| factor=1.5 |  -0.39 (10/32) |  +0.10 (18/32) |
| factor=5 |  +0.75 (32/32) |  +0.73 (29/32) |
| mode=stop |  -1.17 (0/32) |  -0.27 (13/32) |
| repair_min=15 |  +0.84 (32/32) |  +0.78 (29/32) |
| repair_min=240 |  -0.80 (5/32) |  +0.12 (17/32) |

#### Desglose del coste — rejilla central, medias por escenario (minutos-pieza)

| Planificador | exceso | mant. sobre fallo | mant. falsos | latencia 1ª acción (min) | contingencia | congestión |
|---|---|---|---|---|---|---|
| noop | 38,190 | 0.0 | 0.0 | nan | 0 | 0 |
| rules_naive | 42,241 | 2.7 | 122.5 | 180 | 26,738 | 13,394 |
| rules_cal | 19,437 | 1.3 | 45.7 | 234 | 10,286 | 6,051 |
| rules_adapt | 16,682 | 1.4 | 25.8 | 3,024 | 5,101 | 3,819 |


### Qué dicen

1. **Una regla clásica bien hecha sí funciona en el caso central.** `rules_cal` y `rules_adapt` recuperan el 49% y el 56% del coste de los fallos, con beneficio neto en 73 y 69 de 96 escenarios. Ese es el listón que tiene que superar el planificador LLM.
2. **Conectar las alarmas directamente a acciones no ayuda** (`rules_naive`, −0,11; pierde en 59 de 96 escenarios). Hace 122 mantenimientos falsos de media por escenario.
3. **El triaje de alarmas es la clave.** Sin ningún fallo, actuar sobre el ruido cuesta 264–457 min-pieza por hora a `rules_naive`, 94–284 a `rules_cal` y 20–111 a `rules_adapt`.
4. **La adaptativa compra precisión con lentitud.** Su primera acción sobre la estación averiada llega con una mediana de **~3.000 min**, frente a ~230 min de la calibrada.
5. **Lo que rompe a las reglas** —el margen que tiene el LLM—:
   - fallos **intermitentes** (−0,09 / +0,07);
   - fallos **leves**, k = 1,5 (−0,39 / +0,10);
   - reparaciones **largas**, 240 min (−0,80 / +0,12);
   - modo **parada** (−1,17 / −0,27).
6. **Robusto frente a α**: el signo no cambia entre α = 0 y α = 1. El supuesto inventado de la congestión no decide el resultado.
7. **La traza 200m-300m es la más difícil** para todos (+0,15 / +0,23).
8. **Las acciones generan sus propios síntomas**: desviar L3_S36 a L3_S35 la congestiona, y L3_S35 alarma y se desvía de vuelta. Una regla no puede reconocer una alarma como autoinducida; un planificador con acceso a su propio log sí podría.

## Planificadores LLM (C1, C2)

Modelo local **qwen2.5:7b** vía Ollama (coste cero, reproducible). Cliente en
`ssac/llm.py`: solo biblioteca estándar, temperatura 0 y semilla fija, y una
caché SQLite (`cache/llm_cache.sqlite`) indexada por la petición completa, que
hace los barridos reanudables y reproducibles sin GPU.

| | Qué ve | Módulo |
|---|---|---|
| **C1** | La alarma, qué estaciones son accionables, si tienen gemela libre, y las intervenciones en curso. La misma información estructural que las reglas. | `ssac/llm_planner.py` |
| **C2** | C1 + **conocimiento recuperado** de la memoria operativa: alarmas observadas frente a las esperadas con la tasa normal (2 h y 24 h), carga que el propio controlador está desviando hacia la estación, efecto de reparaciones anteriores y registros recientes. | `ssac/rag_planner.py` |
| `rules_twin` | **Control**, no método: repara toda estación marcada que tenga gemela libre e ignora las demás. Es la heurística que C1 v1 resultó seguir. | `ssac/planning.py` |

Reparto de responsabilidades, deliberadamente estrecho: el LLM da un
**veredicto por estación** (degradada / normal / autoinducida / evidencia
insuficiente) y elige el **tipo** de acción; el código elige la gemela y
descarta toda acción incoherente con el veredicto; el esquema JSON restringe
las estaciones a las accionables (el decodificador no puede inventar otra); y
toda acción pasa por el validador simbólico.

La recuperación es por clave (estación) y por recencia, no por embeddings:
sobre un log estructurado el nombre de la estación es una clave exacta. Todas
las cifras las calcula el código; el LLM nunca hace aritmética sobre el log.

### Protocolo

- **Desarrollo** (`dev_llm.py`): el prompt y el contexto se iteran **solo**
  sobre la traza 0-100m. Cada versión queda en `results/dev_log.md`.
- **Evaluación final** (`llm_sweep.py`, lanzado con `run_overnight.sh`): prompt
  congelado, solo las tres trazas reservadas. Reanudable; guarda cada decisión
  del LLM en `results/llm_sweep_calls.csv` para el análisis cualitativo.

## Próximo paso

1. **C1**: planificador LLM sin recuperación.
2. **C2**: planificador LLM con RAG sobre conocimiento de operación — historial de alarmas por estación, topología, log de las propias intervenciones.
3. **C3**: C2 con el validador simbólico (ya implementado en `ssac/actions.py`).
