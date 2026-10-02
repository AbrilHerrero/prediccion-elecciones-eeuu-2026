# Glosario del dataset

Guía para leer `dataset_midterms.csv`: qué representa cada fila, cómo se arman los nombres de
las columnas y qué significa cada una. Los ejemplos usan los valores reales de
**Pensilvania (PA) en 2018**.

La fundamentación de las fuentes y las decisiones de construcción están en
[`fundamentacion_dataset.md`](fundamentacion_dataset.md).

---

## 1. Qué es una fila

Cada fila es **un estado en una elección de medio término**: 50 estados × 6 años (2006, 2010,
2014, 2018, 2022 y 2026) = **300 filas × 42 columnas**.

Cada fila mira **dos elecciones del mismo estado**:

```
   presidencial anterior            medio término
   (2 años antes)                   (año de la fila)
   ─────────────────────            ─────────────────
   2016  ── predictores _prev ──►   2018  ── resultado
```

| Año de la fila | Presidencial anterior | Presidente durante el medio término |
|---|---|---|
| 2006 | 2004 | Bush (R) |
| 2010 | 2008 | Obama (D) |
| 2014 | 2012 | Obama (D) |
| 2018 | 2016 | Trump (R) |
| 2022 | 2020 | Biden (D) |
| 2026 | 2024 | Trump (R) |

| `split` | Años | Contenido |
|---|---|---|
| `train` | 2006–2022 | Predictores y resultado. Se usan para aprender |
| `predict` | 2026 | Solo los predictores. El resultado está vacío: es lo que se predice |

Es un **panel**: se observan las mismas unidades (estados) en varios momentos.

---

## 2. Sufijos y prefijos

Los nombres de las columnas se arman combinando estas piezas.

### Prefijos: qué cargo o ámbito

| Prefijo | Significado | Ejemplo |
|---|---|---|
| `house_` | Cámara de Representantes (435 bancas, se renueva entera cada 2 años) | `house_seats` |
| `senate_` | Senado (100 bancas; cada 2 años se renueva 1/3) | `senate_votes_d` |
| `pres_` | Elección presidencial (cada 4 años) | `pres_dem_share_2p_prev` |
| `nat_` | Valor **nacional** (suma de los 50 estados) | `nat_house_dem_share_2p` |
| `president_party_` | Medido desde el **partido del presidente**, sea D o R | `president_party_swing` |

### Sufijos: partido, medida y tiempo

| Sufijo | Significado | Ejemplo |
|---|---|---|
| `_d` | Partido Demócrata | `house_seats_d` |
| `_r` | Partido Republicano | `house_seats_r` |
| `_other` | Otros partidos e independientes | `house_votes_other` |
| `_total` | Total de votos emitidos para ese cargo | `house_votes_total` |
| `dem_share` | Proporción (entre 0 y 1) que obtuvo el partido Demócrata | `house_dem_share_2p` |
| `_2p` | *Two-party*: calculado solo sobre los votos D + R | `house_dem_share_2p` |
| `_rel` | Valor del estado **menos** el valor nacional del mismo año | `house_dem_share_2p_rel` |
| `_prev` | Valor de la **elección presidencial anterior** (2 años antes) en el mismo estado | `house_dem_share_2p_prev` |

**Sin sufijo `_prev`, la columna describe la elección de medio término de la fila.**

### Cómo leer un nombre completo

```
house_dem_share_2p_rel_prev
│     │         │   │   └── de la elección presidencial anterior
│     │         │   └────── relativo al valor nacional
│     │         └────────── sobre el voto D + R
│     └──────────────────── proporción demócrata
└────────────────────────── en la Cámara
```

→ "La cuota demócrata bipartidista a la Cámara en la presidencial anterior, menos la nacional
de ese año".

---

## 3. Conceptos clave

### Cuota bipartidista (`_2p`)

```
dem_share_2p = votos D / (votos D + votos R)
```

PA 2018: 2.712.665 / (2.712.665 + 2.206.260) = **0,551** → los demócratas obtuvieron el 55,1 %
de los votos repartidos entre los dos partidos grandes.

Se calcula sobre D + R porque la elección se define entre esos dos partidos. Así, un estado con
muchos votos a terceros partidos se compara en la misma escala que el resto.

### Relativo al nacional (`_rel`)

```
_rel = valor del estado − valor nacional del mismo año
```

PA 2018: 0,551 − 0,544 = **+0,008**. Aísla la inclinación propia del estado de la "ola" nacional
de ese año. Es el análogo a nivel estado del índice **Cook PVI**.

### Predictores de la presidencial anterior (`_prev`)

Todo lo que termina en `_prev` se conocía **antes** de la elección de medio término. Usar datos
del mismo día de la elección que se quiere predecir es **data leakage**: el modelo parece preciso
al entrenar y falla al predecir. Por eso el Senado del mismo año no se usa como predictor
(se vota el mismo día que la Cámara).

### Swing

Cambio de la cuota de un partido respecto de la presidencial anterior.

- `house_dem_swing` lo mide para los demócratas. PA 2018: 0,551 − 0,459 = **+0,093**.
- `president_party_swing` lo mide para el **partido del presidente**. En 2018 el presidente era
  R, así que es el mismo número con el signo invertido: **−0,093** (los republicanos perdieron
  9,3 puntos).

`president_party_swing` es la variable que captura el efecto de medio término: es negativa
cuando el partido del presidente pierde, sin importar si es D o R.

### Elección de medio término

Elección federal en la mitad del mandato presidencial: se votan Cámara y Senado, pero no
Presidente. Históricamente, el partido del presidente pierde votos y bancas en ella.

### Distrito sin oposición

Distrito donde uno de los dos partidos no presentó candidato. El otro partido se lleva todos los
votos de ese distrito y la cuota del estado se distorsiona. En California y Washington (sistema
*top-two*) la general puede enfrentar a dos candidatos del mismo partido, con el mismo efecto.

### Roll-off

Proporción de votantes que eligió Presidente pero no votó para la Cámara. Es alto en estados con
distritos sin oposición: si no hay a quién votar, se deja en blanco.

---

## 4. Diccionario por grupos

### 4.1 Identificación y contexto (se conoce antes de votar)

| Columna | Tipo | Significado | PA 2018 |
|---|---|---|---|
| `year` | int | Año de la elección de medio término | 2018 |
| `state` | str | Código postal del estado | PA |
| `state_name` | str | Nombre del estado | Pennsylvania |
| `split` | str | `train` (2006–2022) o `predict` (2026) | train |
| `pres_party` | D/R | Partido del presidente en ejercicio el día de la elección | R |
| `house_seats` | int | Bancas asignadas al estado según su población (censo 2000 en 2006–2010; 2010 en 2014–2018; 2020 en 2022–2026) | 18 |
| `senate_race` | 0/1 | 1 si el estado elige (o elegirá, en 2026) senador ese año | 1 |

### 4.2 Predictores: presidencial anterior (`_prev`)

| Columna | Tipo | Significado | PA 2018 (de 2016) |
|---|---|---|---|
| `pres_dem_share_2p_prev` | float | Cuota D bipartidista a Presidente | 0,496 |
| `pres_dem_share_2p_rel_prev` | float | La misma, menos la nacional | −0,014 |
| `nat_pres_dem_share_2p_prev` | float | Cuota D nacional a Presidente | 0,510 |
| `house_dem_share_2p_prev` | float | Cuota D bipartidista a la Cámara | 0,459 |
| `house_dem_share_2p_rel_prev` | float | La misma, menos la nacional | −0,036 |
| `nat_house_dem_share_2p_prev` | float | Cuota D nacional a la Cámara | 0,495 |
| `house_seats_d_prev`, `house_seats_r_prev` | int | Bancas ganadas por cada partido | 5 / 13 |
| `house_seat_share_d_prev` | float | Bancas D / bancas del estado | 0,278 |
| `house_contested_share_prev` | float | Proporción de distritos con candidato D **y** R | 0,833 |
| `house_dropoff_prev` | float | Roll-off: 1 − votos a la Cámara / votos a Presidente | 0,065 |

En las filas 2026 estas columnas están completas (vienen de 2024): son la base para predecir.

### 4.3 Previas a la general del medio término

Ocurren el mismo año, pero antes del día de la elección general.

| Columna | Tipo | Significado | PA 2018 |
|---|---|---|---|
| `house_primary_votes_d`, `house_primary_votes_r` | int | Votos en las internas a la Cámara de cada partido | 784.604 / 682.324 |
| `house_primary_dem_share_2p` | float | Proporción de votantes de internas que votó en la interna D | 0,535 |
| `house_districts_no_d`, `house_districts_no_r` | int | Distritos sin candidato D / R en la general | 0 / 1 |
| `house_contested_share` | float | Proporción de distritos con candidato D **y** R | 0,944 (17 de 18) |

Vacías en 2026: el FEC todavía no publicó las internas ni las candidaturas de 2026.

### 4.4 Resultado: Cámara de Representantes

| Columna | Tipo | Significado | PA 2018 |
|---|---|---|---|
| `house_votes_d`, `house_votes_r` | int | Votos demócratas / republicanos a la Cámara | 2.712.665 / 2.206.260 |
| `house_votes_other` | int | Votos a otros partidos e independientes | 23.338 |
| `house_votes_total` | int | Total de votos a la Cámara | 4.942.263 |
| **`house_dem_share_2p`** | float | **Variable objetivo.** D / (D + R) | 0,551 |
| `house_dem_share_2p_rel` | float | `house_dem_share_2p` − cuota D nacional | +0,008 |
| `nat_house_dem_share_2p` | float | Cuota D nacional a la Cámara | 0,544 |
| `president_party_house_share_2p` | float | Cuota bipartidista del partido del presidente | 0,449 |
| `house_dem_swing` | float | `house_dem_share_2p` − `house_dem_share_2p_prev` | +0,093 |
| `president_party_swing` | float | El swing visto desde el partido del presidente | −0,093 |
| `house_seats_d`, `house_seats_r` | int | Bancas ganadas por cada partido | 9 / 9 |
| `house_seat_share_d` | float | Bancas D / bancas del estado | 0,500 |

En los estados con fusión de listas (NY, CT), los votos D y R cuentan solo la línea del partido
principal; las líneas aliadas (Working Families, Conservative) quedan en `_other`. En Luisiana y
Georgia, cuando un distrito fue a balotaje, cuentan los votos del balotaje.

NC-09 2018 queda sin asignar (la elección fue anulada y repetida en 2019), así que ese año
`house_seats_d + house_seats_r` suma 12 de las 13 bancas de Carolina del Norte.

### 4.5 Resultado: Senado (mismo día que la Cámara)

| Columna | Tipo | Significado | PA 2018 |
|---|---|---|---|
| `senate_dr_contest` | 0/1 | 1 si la elección enfrentó a un candidato D con uno R | 1 |
| `senate_votes_d`, `senate_votes_r` | int | Votos al Senado (se suman si hubo dos elecciones en el año) | 2.792.437 / 2.134.848 |
| `senate_votes_other` | int | Votos a otros | 83.683 |
| `senate_dem_share_2p` | float | D / (D + R). Se completa solo si `senate_dr_contest` = 1 | 0,567 |

### 4.6 Columnas agregadas en el preprocesamiento

Las crea `analisis_exploratorio/02_preprocesamiento.py` y están en
`analisis_exploratorio/salidas/dataset_preprocesado.csv`.

| Columna | Tipo | Significado |
|---|---|---|
| `todos_disputados` | 0/1 | 1 si todos los distritos del estado tuvieron candidato D y R (`house_contested_share` = 1) |
| `partido_pres_camara_prev` | float | Cuota a la Cámara del partido del presidente en la presidencial anterior |
| `periodo` | str | "2006–2014" o "2018–2022" |
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

| Columnas vacías | Filas | Motivo |
|---|---|---|
| `senate_votes_*` | Estados sin elección al Senado ese año | Cada 2 años se renueva 1/3 de las bancas (33–35), así que 16 o 17 estados no eligen senador |
| `senate_dem_share_2p` | Además, elecciones sin enfrentamiento D vs R | Por ejemplo, Sanders (independiente) en Vermont |
| `house_primary_*` | 10 filas de 2006–2022 | Ni el D ni el R registraron votos en internas: Luisiana usa una interna sin partidos; CT, UT, DE y SD nominaron por convención o sin interna disputada |
| Resultado e internas | 2026 | Es lo que se predice / todavía no publicado |

Todos los predictores `_prev` están completos en las 300 filas.
