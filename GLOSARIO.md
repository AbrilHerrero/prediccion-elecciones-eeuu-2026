# Glosario del dataset

Guía para leer `dataset_elecciones_estado.csv`: qué representa cada fila, cómo se arman los
nombres de las columnas y qué significa cada una. Los ejemplos usan los valores reales de
**Pensilvania (PA)**.

La fundamentación de las fuentes y las decisiones de construcción están en
[`fundamentacion_dataset.md`](fundamentacion_dataset.md).

---

## 1. Qué es una fila

Cada fila es **un estado en un año electoral**: 50 estados × 6 años (2016, 2018, 2020, 2022,
2024 y 2026) = **300 filas × 44 columnas**.

Es un **panel**: se observan las mismas unidades (estados) a lo largo del tiempo. Por eso hay
columnas que miran el ciclo anterior del mismo estado.

| `split` | Años | Contenido |
|---|---|---|
| `train` | 2016–2024 | Todas las variables, incluido el resultado. Se usan para aprender |
| `predict` | 2026 | Solo lo que se conoce antes de votar. El resultado está vacío: es lo que se predice |

---

## 2. Sufijos y prefijos

Los nombres de las columnas se arman combinando estas piezas.

### Prefijos: qué cargo o ámbito

| Prefijo | Significado | Ejemplo |
|---|---|---|
| `house_` | Cámara de Representantes (435 bancas, se renueva entera cada 2 años) | `house_seats` |
| `senate_` | Senado (100 bancas, se renueva 1/3 cada 2 años) | `senate_votes_d` |
| `pres_` | Elección presidencial (cada 4 años) | `pres_votes_total` |
| `nat_` | Valor **nacional** (todo el país) del mismo año | `nat_house_dem_share_2p` |

### Sufijos: partido, medida y tiempo

| Sufijo | Significado | Ejemplo |
|---|---|---|
| `_d` | Partido Demócrata | `house_seats_d` |
| `_r` | Partido Republicano | `house_seats_r` |
| `_other` | Otros partidos e independientes | `house_votes_other` |
| `_total` | Total de votos emitidos para ese cargo | `house_votes_total` |
| `dem_share` | Proporción (entre 0 y 1) que obtuvo el partido Demócrata | `pres_dem_share_2p` |
| `_2p` | *Two-party*: calculado solo sobre los votos D + R | `house_dem_share_2p` |
| `_rel` | Valor del estado **menos** el valor nacional del mismo año | `house_dem_share_2p_rel` |
| `_lag` | Valor del **ciclo anterior** (2 años antes) en el mismo estado | `house_dem_share_2p_lag` |
| `_prev` | Valor de la **última elección presidencial estrictamente anterior** al año de la fila | `pres_dem_share_2p_prev` |

### Cómo leer un nombre completo

```
house_dem_share_2p_rel_lag
│     │         │   │   └── del ciclo anterior
│     │         │   └────── relativo al valor nacional
│     │         └────────── sobre el voto D + R
│     └──────────────────── proporción demócrata
└────────────────────────── en la Cámara
```

→ "La cuota demócrata bipartidista a la Cámara del ciclo anterior, menos la nacional de ese ciclo".

---

## 3. Conceptos clave

### Cuota bipartidista (`_2p`)

```
dem_share_2p = votos D / (votos D + votos R)
```

PA 2024: 3.338.371 / (3.338.371 + 3.481.113) = **0,489** → los demócratas obtuvieron el 48,9 %
de los votos repartidos entre los dos partidos grandes.

Se calcula sobre D + R porque la elección se define entre esos dos partidos. Así, un estado con
muchos votos a terceros partidos se compara en la misma escala que el resto.

### Relativo al nacional (`_rel`)

```
_rel = valor del estado − valor nacional del mismo año
```

PA 2018: 0,551 − 0,545 = **+0,007**. Aísla la inclinación propia del estado de la "ola" nacional
de ese año. Es el análogo a nivel estado del índice **Cook PVI**.

### Rezagos (`_lag` y `_prev`)

Muestran el pasado del estado con información conocida **antes** de la elección de la fila. Usar
datos del mismo día de la elección (por ejemplo, el voto presidencial de 2020 para predecir la
Cámara de 2020) es **data leakage**: el modelo parece preciso al entrenar y falla al predecir.

`_prev` toma siempre la presidencial anterior al año de la fila:

| year | 2018 | 2020 | 2022 | 2024 | 2026 |
|---|---|---|---|---|---|
| `pres_dem_share_2p_prev` (PA) | 0,496 (de 2016) | 0,496 (de 2016) | 0,506 (de 2020) | 0,506 (de 2020) | 0,491 (de 2024) |

### Swing

Cambio de la cuota de un partido respecto del ciclo anterior. PA 2018: 0,551 − 0,459 = **+0,093**
→ los demócratas subieron 9,3 puntos.

### Elección de medio término

Elección federal en la mitad del mandato presidencial: se votan Cámara y Senado, pero no
Presidente (2018, 2022, 2026). Históricamente, el partido del presidente pierde votos en ellas.

### Distrito sin oposición

Distrito donde uno de los dos partidos no presentó candidato. El otro partido se lleva todos los
votos de ese distrito y la cuota del estado se distorsiona. En California y Washington (sistema
*top-two*) la general puede enfrentar a dos candidatos del mismo partido, con el mismo efecto.

---

## 4. Diccionario por grupos

### 4.1 Identificación y contexto

| Columna | Tipo | Significado | PA 2018 |
|---|---|---|---|
| `year` | int | Año de la elección general | 2018 |
| `state` | str | Código postal del estado | PA |
| `state_name` | str | Nombre del estado | Pennsylvania |
| `split` | str | `train` (2016–2024) o `predict` (2026) | train |
| `is_midterm` | 0/1 | 1 si es elección de medio término (2018, 2022, 2026) | 1 |
| `pres_party` | D/R | Partido del presidente en ejercicio el día de la elección | R |
| `house_seats` | int | Bancas asignadas al estado según su población (censo 2010 hasta 2020; censo 2020 desde 2022) | 18 |

Partido del presidente por año: 2016 **D** (Obama) · 2018 y 2020 **R** (Trump) · 2022 y 2024
**D** (Biden) · 2026 **R** (Trump).

### 4.2 Cámara de Representantes: votos

| Columna | Tipo | Significado | PA 2024 |
|---|---|---|---|
| `house_votes_d` | int | Votos demócratas a la Cámara en la elección general | 3.338.371 |
| `house_votes_r` | int | Votos republicanos | 3.481.113 |
| `house_votes_other` | int | Votos a otros partidos e independientes | 0 |
| `house_votes_total` | int | Total de votos a la Cámara | 6.819.484 |
| **`house_dem_share_2p`** | float | **Variable objetivo.** D / (D + R) | 0,489 |
| `house_margin_d` | float | (D − R) / total. Positivo = ganó D | −0,021 |
| `house_dem_share_2p_rel` | float | `house_dem_share_2p` − cuota D nacional | +0,003 |
| `president_party_house_share_2p` | float | Cuota bipartidista del partido del presidente (igual a la cuota D si `pres_party` = D; 1 − cuota D si es R) | 0,489 |

En los estados con fusión de listas (NY, CT), los votos D y R cuentan solo la línea del partido
principal; las líneas aliadas (Working Families, Conservative) quedan en `_other`.

### 4.3 Cámara: bancas y competencia

| Columna | Tipo | Significado | PA 2016 |
|---|---|---|---|
| `house_seats_d` | int | Bancas ganadas por los demócratas | 5 |
| `house_seats_r` | int | Bancas ganadas por los republicanos | 13 |
| `house_seat_share_d` | float | Bancas D / bancas del estado | 0,278 |
| `house_districts_no_d` | int | Distritos sin candidato demócrata en la general | 5 |
| `house_districts_no_r` | int | Distritos sin candidato republicano en la general | 2 |
| `house_contested_share` | float | Proporción de distritos con candidato D **y** R | 0,611 (11 de 18) |

NC-09 2018 queda sin asignar (la elección fue anulada y repetida en 2019), así que ese año
`house_seats_d + house_seats_r` suma 12 de las 13 bancas de Carolina del Norte.

### 4.4 Internas (primarias) a la Cámara

| Columna | Tipo | Significado | PA 2018 |
|---|---|---|---|
| `house_primary_votes_d` | int | Votos en las internas demócratas (incluye segundas vueltas) | 784.604 |
| `house_primary_votes_r` | int | Votos en las internas republicanas | 682.324 |
| `house_primary_dem_share_2p` | float | Proporción de votantes de internas que votó en la interna D | 0,535 |

Disponibles para 2016–2022.

### 4.5 Senado

| Columna | Tipo | Significado | PA 2018 |
|---|---|---|---|
| `senate_race` | 0/1 | 1 si el estado elige (o elegirá, en 2026) senador ese año | 1 |
| `senate_dr_contest` | 0/1 | 1 si la elección enfrentó a un candidato D con uno R | 1 |
| `senate_votes_d` | int | Votos demócratas al Senado (se suman si hubo dos elecciones en el año) | 2.792.437 |
| `senate_votes_r` | int | Votos republicanos al Senado | 2.134.848 |
| `senate_votes_other` | int | Votos a otros | 83.683 |
| `senate_dem_share_2p` | float | D / (D + R). Se completa solo si `senate_dr_contest` = 1 | 0,567 |

### 4.6 Presidente (solo 2016, 2020 y 2024)

| Columna | Tipo | Significado | PA 2016 |
|---|---|---|---|
| `pres_votes_d` | int | Votos al candidato presidencial demócrata | 2.926.441 |
| `pres_votes_r` | int | Votos al candidato republicano | 2.970.733 |
| `pres_votes_total` | int | Total de votos presidenciales | 6.165.478 |
| `pres_dem_share_2p` | float | Cuota D bipartidista presidencial | 0,496 |
| `pres_dem_share_2p_rel` | float | Cuota D presidencial − la nacional (análogo al PVI) | −0,014 |
| `house_dropoff` | float | 1 − votos a la Cámara / votos a Presidente: proporción de votantes que eligió Presidente y dejó en blanco la Cámara | 0,065 |

### 4.7 Referencias nacionales

| Columna | Tipo | Significado | 2018 |
|---|---|---|---|
| `nat_house_dem_share_2p` | float | Cuota D bipartidista nacional a la Cámara | 0,545 |
| `nat_pres_dem_share_2p` | float | Cuota D bipartidista nacional a Presidente (solo años presidenciales) | — |

Cuota D nacional a la Cámara por año: 2016 49,4 % · 2018 54,5 % · 2020 51,5 % · 2022 48,7 % ·
2024 48,7 %.

### 4.8 Rezagos: el pasado del estado

| Columna | Tipo | Significado | PA 2018 |
|---|---|---|---|
| `house_dem_share_2p_lag` | float | Cuota D a la Cámara del ciclo anterior | 0,459 (de 2016) |
| `house_dem_share_2p_rel_lag` | float | La misma, relativa al nacional de ese ciclo | −0,035 |
| `house_seats_d_lag` | int | Bancas D del ciclo anterior | 5 |
| `house_dem_swing` | float | Cuota D actual − cuota D del ciclo anterior | +0,093 |
| `pres_dem_share_2p_prev` | float | Cuota D de la última presidencial anterior | 0,496 (de 2016) |
| `pres_dem_share_2p_rel_prev` | float | La misma, relativa a la nacional | −0,014 |

En las filas 2026 estas columnas están completas (toman los valores de 2024): son la base para
predecir.

### 4.9 Columnas agregadas en el preprocesamiento

Las crea `analisis_exploratorio/02_preprocesamiento.py` y están en
`analisis_exploratorio/salidas/dataset_preprocesado.csv`.

| Columna | Tipo | Significado |
|---|---|---|
| `todos_disputados` | 0/1 | 1 si todos los distritos del estado tuvieron candidato D y R (`house_contested_share` = 1) |
| `swing_partido_presidente` | float | Swing visto desde el partido del presidente: `house_dem_swing` si `pres_party` = D, y su opuesto si es R |
| `tipo_ciclo` | str | "medio término" o "presidencial" |
| `categoria_camara` | str | Cuota D a la Cámara discretizada en 5 niveles (ver abajo) |

| Categoría | Cuota D a la Cámara |
|---|---|
| Sólido R | < 45 % |
| Inclinado R | 45 % – 48 % |
| Competitivo | 48 % – 52 % |
| Inclinado D | 52 % – 55 % |
| Sólido D | ≥ 55 % |

---

## 5. Celdas vacías

Casi todas son **faltantes estructurales**: el dato corresponde a una elección que ese año no
se realizó. Por eso se dejan vacías en vez de imputarse.

| Columnas vacías | Filas | Motivo |
|---|---|---|
| `pres_*`, `house_dropoff`, `nat_pres_dem_share_2p` | 2018, 2022, 2026 | Años sin elección presidencial |
| `senate_*` | Estados sin elección al Senado ese año | Cada estado elige 1/3 del Senado por ciclo |
| `senate_dem_share_2p` | Elecciones al Senado sin enfrentamiento D vs R | Por ejemplo, Sanders (independiente) en Vermont |
| `*_lag`, `*_prev`, `house_dem_swing` | 2016 | Primer año del panel |
| `house_primary_*` | 2024 y 2026 | El Clerk publica solo la elección general |
| Variables de resultado (votos, cuotas, bancas, `nat_*`) | 2026 | Es lo que se predice |
