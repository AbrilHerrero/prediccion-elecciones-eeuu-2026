# Análisis exploratorio — Elecciones EE. UU. 2016–2024

Scripts en Python + pandas + matplotlib que procesan `../dataset_elecciones_estado.csv` y
generan gráficos y tablas para estudiar las correlaciones entre variables. Siguen el modelo
de la materia (*Preprocesamiento de Datos y Técnicas de Análisis*):

| Script | Etapa del modelo de clase | Qué hace |
|---|---|---|
| `01_carga_e_inspeccion.py` | Entorno y carga | Versión de Python y pandas, `read_csv`, `head()`, `dtypes`, filas por año |
| `02_preprocesamiento.py` | **Módulo I** — Limpieza, integración, reducción, discretización | Faltantes (estructurales vs reales), columnas redundantes, atípicos (1,5 × IQR), controles de consistencia, variables derivadas y discretización de la cuota D en 5 categorías |
| `03_descriptivo.py` | **Módulo II · Nivel 1** — Descriptivo (¿qué pasó?) | Media, mediana, desvío; comparación por tipo de ciclo; bancas y voto nacional por año |
| `04_exploratorio.py` | **Módulo II · Nivel 2** — Exploratorio (¿hay patrones?) | Histogramas, desbalance de categorías, dispersión X/Y con r de Pearson, matriz de correlación, análisis por subconjuntos, efecto de medio término |
| `ejecutar_todo.py` | — | Corre los cuatro pasos en orden |
| `comun.py` | — | Rutas, carga del CSV, colores y estilo de gráficos compartidos |

## Cómo correrlo

Desde esta carpeta, con el entorno virtual del TP:

```bash
cd /Users/abrilherrero/Documents/Facu2026/Ciencia_de_Datos/TP/analisis_exploratorio
../.venv/bin/pip install -r requirements.txt   # solo la primera vez
../.venv/bin/python ejecutar_todo.py           # o cada script por separado, en orden
```

`03` y `04` leen `salidas/dataset_preprocesado.csv`, que genera `02`.

**Como notebook:** cada script está dividido en celdas con `# %%`. En VS Code (extensión
Jupyter) aparece "Run Cell" sobre cada una y se ejecutan como en Colab. Para Google Colab:
subí `dataset_elecciones_estado.csv` y `comun.py`, y pegá las celdas de cada script.

## Salidas

- `figuras/`: los gráficos en PNG, numerados según el script que los genera.
- `salidas/`: tablas en CSV (dataset preprocesado, estadísticos, matrices de correlación).
- La consola muestra los resultados numéricos y su interpretación paso a paso.

## Qué muestra cada figura

| Figura | Pregunta que responde |
|---|---|
| `02_1_mapa_faltantes` | ¿Dónde faltan datos y por qué? Los bloques de 100 % son estructurales (no hubo esa elección) |
| `02_2_boxplot_atipicos` | ¿Hay valores extremos? Son estados sin candidato opositor (VT, MA, SD, ND): reales pero distorsionados |
| `03_1_bancas_por_anio` | ¿Quién controló la Cámara en cada ciclo? |
| `03_2_cuota_nacional` | ¿Cómo evolucionó el voto D nacional a la Cámara y a Presidente? |
| `04_1_histogramas` | ¿Cómo se distribuye la cuota D por estado y cuánto cambia entre ciclos? |
| `04_2_desbalance_categorias` | ¿Cuántos estados son competitivos? Solo ~12 %: una clase minoritaria |
| `04_3_dispersion_predictores` | ¿Qué variables se mueven junto con la cuota D a la Cámara? |
| `04_4_matriz_correlacion` | Correlación de Pearson entre todas las variables de análisis |
| `04_5_correlacion_subconjuntos` | ¿Cambian las correlaciones al quitar los estados con distritos sin oposición? |
| `04_6_efecto_medio_termino` | ¿El partido del presidente pierde votos en medio término? |

## Hallazgos principales

1. **El voto presidencial previo es el mejor predictor** de la cuota D a la Cámara
   (r = 0,88; 0,95 en estados con todos sus distritos disputados). Coincide con la
   nacionalización del voto descrita en `../fundamentacion_dataset.md`.
2. **Los distritos sin oposición son ruido de medición.** Al quitarlos, las correlaciones
   de los predictores principales suben entre 0,03 y 0,06. Es el mismo razonamiento del
   caso de clase alcohol-mortalidad, donde el subconjunto revela la relación real.
3. **El efecto de medio término está en el cambio, no en el nivel.** `is_midterm` casi no
   se correlaciona con la cuota D (r = 0,04), pero sí con el swing del partido del
   presidente (r = −0,48): −5,2 pp en 2018 (pres. R) y −1,9 pp en 2022 (pres. D).
4. **Pocos casos competitivos:** solo 29 de 250 estado-año caen entre 48 % y 52 %.

Correlación no implica causalidad: estos resultados orientan la elección de variables para
el modelo predictivo de la próxima etapa.
