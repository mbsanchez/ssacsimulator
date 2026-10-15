# Híbridos frente a reglas reajustadas — detector por estación, diseño v2

Δ = recuperación a 24 h (híbrido) − ídem (regla); IC 95 % bootstrap estratificado por traza (10 000, semilla 0); Wilcoxon emparejado sobre el exceso a 24 h por escenario.

| Híbrido | Regla | Δ | IC 95 % | híbrido mejor en | p |
|---|---|---|---|---|---|
| hybrid:fable-5.1 | calibrada, elegida en desarrollo `w=240 a=0.0001` | +0.146 | [+0.076, +0.218] | 116/216 | 3.6e-11 |
| hybrid:fable-5.1 | adaptativa + veto, elegida en desarrollo `w=240 a=0.001 h=1440` | +0.230 | [+0.159, +0.305] | 143/216 | 6.2e-18 |
| hybrid:fable-5.1 | adaptativa + veto, óptimo en reservadas `w=180 a=0.0001 h=720` | +0.131 | [+0.060, +0.205] | 128/216 | 5.2e-13 |
| hybrid | calibrada, elegida en desarrollo `w=240 a=0.0001` | +0.023 | [-0.019, +0.071] | 82/216 | 0.53 |
| hybrid | adaptativa + veto, elegida en desarrollo `w=240 a=0.001 h=1440` | +0.106 | [+0.084, +0.132] | 129/216 | 8.5e-18 |
| hybrid | adaptativa + veto, óptimo en reservadas `w=180 a=0.0001 h=720` | +0.008 | [-0.030, +0.051] | 64/216 | 0.02 |
