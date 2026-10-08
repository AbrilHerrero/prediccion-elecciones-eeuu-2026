# Análisis exploratorio y predictivo — Elecciones de medio término 2006–2022

Scripts en Python + pandas + matplotlib que procesan `../dataset_midterms.csv` y generan
gráficos y tablas para estudiar qué información de la presidencial anterior anticipa el voto en
el medio término. Siguen el modelo de la materia (*Preprocesamiento de Datos y Técnicas de
Análisis*):

| Script | Etapa del modelo de clase | Qué hace |
|---|---|---|
| `01_carga_e_inspeccion.py` | Entorno y carga | Versión de Python y pandas, `read_csv`, `head()`, `dtypes`, grupos de columnas, filas por año |
| `02_preprocesamiento.py` | **Módulo I** — Limpieza, integración, reducción, discretización | Faltantes (estructurales vs reales), columnas redundantes, atípicos (1,5 × IQR), controles de consistencia, variables derivadas y discretización de la cuota D en 5 categorías |
| `03_descriptivo.py` | **Módulo II · Nivel 1** — Descriptivo (¿qué pasó?) | Media, mediana, desvío; comparación por partido del presidente; bancas y voto nacional antes y después de cada medio término |
| `04_exploratorio.py` | **Módulo II · Nivel 2** — Exploratorio (¿hay patrones?) | Histogramas, desbalance de categorías, dispersión X/Y con r de Pearson, matriz de correlación, subconjuntos, correlaciones por año, efecto de medio término y líneas base |
| `05_predictivo.py` | **Módulo III** — Predictivo (¿qué va a pasar?) | Contraste de hipótesis, validación dejando afuera un medio término, comparación de modelos, curva votos-bancas, predicción 2026 y simulación de incertidumbre |
| `ejecutar_todo.py` | — | Corre los cinco pasos en orden |
| `comun.py` | — | Rutas, carga del CSV, colores y estilo de gráficos compartidos |

## Cómo correrlo

Desde esta carpeta, con el entorno virtual del TP:

```bash
../.venv/bin/pip install -r requirements.txt   # solo la primera vez
../.venv/bin/python ejecutar_todo.py           # o cada script por separado, en orden
```

`03` y `04` leen `salidas/dataset_preprocesado.csv`, que genera `02`. `05` lee el dataset completo
(necesita las filas 2026) y usa scikit-learn.

**Como notebook:** cada script está dividido en celdas con `# %%`. En VS Code (extensión
Jupyter) aparece "Run Cell" sobre cada una y se ejecutan como en Colab. Para Google Colab:
subí `dataset_midterms.csv` y `comun.py`, y pegá las celdas de cada script.

## Cómo está organizado el código

### `comun.py`

Concentra lo que comparten los cuatro scripts, para no repetirlo:

- **Rutas** (`DATASET`, `FIGURAS`, `SALIDAS`, `PREPROCESADO`) calculadas a partir de la ubicación
  del archivo, así los scripts funcionan desde cualquier directorio.
- **Carga:** `cargar_dataset()` lee el CSV completo; `cargar_preprocesado()` lee el que genera
  `02` y lanza `FileNotFoundError` con un mensaje claro si todavía no se corrió.
- **Estilo:** `estilo()` fija el formato de todos los gráficos, `guardar(fig, nombre)` guarda el
  PNG en `figuras/` y `titulo(texto)` imprime los encabezados de consola.
- **Colores y etiquetas:** azul D / rojo R, violeta para destacar un subconjunto, y `ETIQUETAS`,
  que traduce los nombres de columna a texto legible en los gráficos.

### Patrón de cada script

Todos siguen la misma estructura: cargan datos con `comun`, dividen el trabajo en celdas
`# %%` numeradas como las secciones del modelo de clase, imprimen los resultados con su
interpretación y guardan figuras y tablas. Los números de las figuras indican el script que las
genera (`04_3_...` es la tercera figura de `04`).

### Qué hace cada sección de código

| Script | Sección | Técnica en pandas / numpy |
|---|---|---|
| `02` | 1.1 Faltantes | `isna().sum()` por columna; `groupby("year")` para el mapa de calor |
| `02` | 1.3 Atípicos | `quantile([0.25, 0.75])` para el IQR y filtro booleano con los límites |
| `02` | 1.4 Consistencia | Un diccionario de controles booleanos (`duplicated`, `between`, `np.allclose`) |
| `02` | 3. Derivadas | `np.where` para crear columnas condicionales (por ejemplo, la cuota del partido del presidente) |
| `02` | 4. Discretización | `pd.cut` con cortes y etiquetas ordinales |
| `03` | 1–2 Resúmenes | `agg(["mean", "median", "std", ...])` y `groupby("pres_party")` |
| `03` | 3. Nacionales | `groupby("year").agg(...)` con agregaciones con nombre |
| `04` | 2.2 Correlaciones | `Series.corr` (Pearson) y `DataFrame.corr(method="spearman")`; eliminación por pares automática |
| `04` | 2.2.4 Por año | `groupby("year")[...].apply(...)` calculando una correlación por grupo |
| `04` | 2.4 Líneas base | Predicciones ingenuas como columnas y error absoluto medio; el castigo de cada año se promedia sobre los otros años (`castigo.drop(a).mean()`) |
| `05` | 1. Variables | Cuotas pasadas al punto de vista del partido del presidente y centradas en 0,5 (`signo * (cuota - 0.5)`) |
| `05` | 2. Validación | `LeaveOneGroupOut` con `groups=year`: cada pliegue deja afuera un medio término entero; regla de un error estándar para elegir modelo |
| `05` | 3. Hipótesis | `LinearRegression` reestimada en cada pliegue; se mira el signo del intercepto y de las pendientes |
| `05` | 5. Bancas | `np.polyfit` de bancas D sobre la cuota D nacional en 11 elecciones; error dejando afuera cada una |
| `05` | 7. Incertidumbre | Monte Carlo con `numpy.random.default_rng`: ola nacional + desvío por estado + error de la curva |

## Salidas

- `figuras/`: los gráficos en PNG.
- `salidas/`: tablas en CSV (dataset preprocesado, estadísticos, matrices de correlación,
  efecto de medio término, líneas base y, con prefijo `predictivo_`, las del modelo).
- La consola muestra los resultados numéricos y su interpretación paso a paso.

## Qué muestra cada figura

| Figura | Pregunta que responde |
|---|---|
| `02_1_mapa_faltantes` | ¿Dónde faltan datos y por qué? Solo Senado (estados sin elección) e internas |
| `02_2_boxplot_atipicos` | ¿Hay valores extremos? Son estados sin candidato opositor (MA, RI, ND, SD): reales pero distorsionados |
| `03_1_bancas_antes_despues` | ¿Cuántas bancas perdió el partido del presidente en cada medio término? |
| `03_2_cuota_nacional` | ¿Cómo cambió el voto D nacional de la presidencial al medio término? |
| `04_1_histogramas` | ¿Cómo se distribuyen la cuota D y el swing del partido del presidente? |
| `04_2_desbalance_categorias` | ¿Cuántos estados son competitivos? Solo 11 %: una clase minoritaria |
| `04_3_dispersion_predictores` | ¿Qué variables de la presidencial anterior se mueven junto con la cuota D? |
| `04_4_matriz_correlacion` | Correlación de Pearson entre todas las variables de análisis |
| `04_5_correlacion_subconjuntos` | ¿Cambian las correlaciones al quitar los estados con distritos sin oposición? |
| `04_6_correlacion_por_anio` | ¿La presidencial anterior anticipa mejor el medio término en los años recientes? |
| `04_7_efecto_medio_termino` | ¿El partido del presidente pierde votos en cada medio término? |
| `04_8_swing_vs_resultado_previo` | ¿Pierde más donde estaba más fuerte? |
| `05_1_comparacion_modelos` | ¿Qué modelo erra menos al predecir un medio término que no vio? |
| `05_2_predicho_vs_real` | ¿Qué tan cerca queda la predicción fuera de muestra de cada estado? |
| `05_3_error_nacional_por_anio` | ¿Cuánto erra el modelo la ola nacional de cada año? |
| `05_4_coeficientes_por_pliegue` | ¿Se sostienen H1, H2 y H3 al dejar afuera cualquier año? |
| `05_5_prediccion_2026_estados` | ¿Qué cuota D predice el modelo para cada estado en 2026? |
| `05_6_bancas_2026` | ¿Cuántas bancas D y con qué probabilidad de mayoría? |
| `05_7_curva_votos_bancas` | ¿Cuántas bancas da cada punto de voto nacional? |

## Hallazgos principales

1. **La presidencial anterior anticipa bien el medio término** (r = 0,76 con el voto
   presidencial y 0,79 con el voto a la Cámara), y **cada vez mejor**: de 0,68 en 2006–2014 a
   0,86 en 2018–2022 para el voto presidencial. Es la nacionalización del voto descrita en
   `../fundamentacion_dataset.md`.
2. **Los distritos sin oposición distorsionan las medidas de la Cámara** en las dos elecciones a
   la vez, lo que infla su correlación. En los estados disputados el mejor predictor es el voto
   presidencial (0,78).
3. **El partido del presidente perdió votos en los cinco medio término**, con presidentes de
   ambos partidos: de −1,9 pp (2022) a −8,6 pp (2010) en el estado mediano, y en 70–96 % de los
   estados. Además **pierde más donde estaba más fuerte** (r = −0,52).
4. **Línea base a superar:** sumar el castigo promedio de los otros medio término al voto
   presidencial anterior da un error medio de 4,3 pp.
5. **Pocos casos competitivos:** 27 de 250 estado-año caen entre 48 % y 52 %.

Correlación no implica causalidad: estos resultados orientan la elección de variables para
el modelo predictivo.

## Resultados del modelo predictivo

1. **Las tres hipótesis se sostienen al dejar afuera cualquier medio término:** la presidencial
   anticipa (pendiente ≈ 1), el partido del presidente pierde 4,6–5,5 pp en un estado parejo y el
   voto a la Cámara vuelve hacia el 50 % (pendiente 0,70–0,80).
2. **Modelo elegido:** regresión lineal múltiple con contexto nacional. Error medio fuera de
   muestra de 3,5 pp por estado, contra 4,3 pp de la mejor línea base.
3. **Predicción 2026:** 54,0 % D del voto bipartidista a la Cámara (p10–p90: 51,7–56,2 %) y
   236 bancas D (p10–p90: 217–256); mayoría D en el 88 % de las simulaciones.
4. Usa solo fundamentos electorales: no incluye encuestas, aprobación presidencial ni los mapas
   redibujados en 2025–2026.
