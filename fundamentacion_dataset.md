# Predicción de las elecciones de medio término de EE. UU. (3 de noviembre de 2026)

## Etapa 1 — Construcción y fundamentación del dataset

Archivos de esta entrega:

| Archivo | Contenido |
|---|---|
| `dataset_elecciones_estado.csv` | Panel estado × ciclo electoral, 2016–2026 (300 filas × 44 columnas) |
| `construir_dataset.py` | Script que genera el CSV desde las fuentes originales (reproducible) |
| `fundamentacion_dataset.md` | Este documento |
| `excelsElecciones/` (local, fuera del repositorio) | Fuentes primarias sin modificar: `federalelections20XX.xlsx`, `2024presgeresults.xlsx`, `2024election_clerk.pdf` |

Para regenerar el dataset: `.venv/bin/python construir_dataset.py`

---

## 1. Objetivo y pregunta de investigación

**Objetivo general:** predecir el resultado de las elecciones federales del 3 de noviembre de 2026 en EE. UU.: la Cámara de Representantes (435 bancas) y el Senado (35 bancas en juego).

**Objetivo de esta etapa:** construir un dataset a partir de fuentes oficiales para encontrar las variables que se correlacionan con el voto por partido en cada estado. Esas variables van a ser la base del modelo predictivo.

**Pregunta de investigación:** *¿Qué características observables de un estado en elecciones anteriores (su voto presidencial, su voto a la Cámara en el ciclo previo, su voto al Senado, la participación en internas y el tipo de ciclo) predicen la proporción de voto demócrata a la Cámara, y cuánto cambia esa relación en las elecciones de medio término?*

**Variable objetivo principal:** `house_dem_share_2p`, la proporción demócrata del voto bipartidista a la Cámara en cada estado: D / (D + R).

**Variables objetivo secundarias:** `house_seats_d` (bancas ganadas) y `senate_dem_share_2p`.

## 2. Tipo de estudio

El trabajo combina dos enfoques, en dos etapas:

1. **Exploratorio-descriptivo (esta etapa).** Todavía no sabemos cuáles variables de estas fuentes tienen poder predictivo, ni qué problemas de calidad tienen (distritos sin candidato opositor, sistemas electorales distintos por estado). Primero describimos y medimos correlaciones, para generar hipótesis en vez de confirmarlas.
2. **Predictivo (etapas siguientes).** Con las variables elegidas, entrenamos modelos sobre 2016–2024 y los aplicamos a las filas 2026 del dataset (`split = "predict"`).

Es un estudio **observacional, retrospectivo y longitudinal (panel)**. Se observan las mismas 50 unidades (estados) en 5 ciclos electorales, sin intervenir sobre ellas.

## 3. Estado del arte

La predicción electoral en EE. UU. tiene una literatura amplia. Se agrupa en cuatro líneas, y este dataset toma elementos de cada una.

### 3.1 Modelos de "fundamentos" (fundamentals)

Predicen el resultado con variables estructurales, sin encuestas.

- **Fair (1978)** y **Abramowitz (1988, modelo "Time for Change")** modelan el voto presidencial con el crecimiento económico, la aprobación presidencial y la cantidad de mandatos del partido en el poder.
- Para las elecciones de medio término, **Tufte (1975)** mostró que la pérdida de votos del partido del presidente se explica por la aprobación presidencial y el ingreso real disponible.

### 3.2 Teorías de la pérdida en medio término

El partido del presidente pierde bancas en casi todas las elecciones de medio término desde la Guerra Civil. Hay tres explicaciones principales:

- **"Surge and decline"** (A. Campbell, 1960; J. E. Campbell, 1987): en la elección presidencial, el entusiasmo por el candidato ganador arrastra votantes periféricos. En el medio término esos votantes no van a votar, y el partido del presidente pierde ese impulso.
- **Balance o castigo** (Erikson, 1988): los votantes moderados compensan el poder del presidente votando al partido opositor.
- **Referéndum:** la elección de medio término funciona como un plebiscito sobre la gestión (Tufte, 1975).

**Implicancia para 2026:** el presidente es republicano (Trump), así que la teoría predice un desplazamiento hacia los demócratas. Por eso el dataset incluye `is_midterm`, `pres_party` y `president_party_house_share_2p`.

### 3.3 Nacionalización y declive del voto dividido

Desde los años 2000, el voto a la Cámara está cada vez más alineado con el voto presidencial en cada estado y distrito:

- El valor de ser el legislador en ejercicio (incumbencia) cae (Jacobson, 2015).
- El voto dividido entre partidos casi desaparece, por la "partidización negativa": se vota contra el partido rival más que a favor del propio (Abramowitz & Webster, 2016).
- La política estadual y local pasa a reflejar la nacional (Hopkins, 2018).

Por eso índices como el **Cook PVI** usan el voto presidencial relativo al nacional para medir la inclinación partidaria de un distrito. Nuestras variables `pres_dem_share_2p_rel_prev` y `house_dem_share_2p_rel_lag` son análogos a nivel estado.

### 3.4 Modelos con encuestas y bayesianos

- **Bafumi, Erikson & Wlezien (2010):** predicen las bancas de la Cámara a partir de la encuesta genérica ("¿a qué partido votaría para el Congreso?").
- **Linzer (2013):** modelo bayesiano dinámico que combina fundamentos con encuestas estaduales.
- **Heidemanns, Gelman & Morris (2020):** modelo de *The Economist*, también bayesiano.
- **FiveThirtyEight:** combina encuestas, fundamentos y calificaciones de expertos.

En todos, los fundamentos estructurales funcionan como *prior* y las encuestas lo actualizan.

### 3.5 De votos a bancas

La relación entre votos y bancas depende del mapa de distritos. **Gelman & King (1994)** formalizaron la curva votos-bancas y el sesgo partidario. El supuesto más simple es el **swing uniforme**: todos los distritos se mueven lo mismo que el promedio nacional. Lo usamos como línea base en la sección 8.

### 3.6 Dónde se ubica este trabajo

Construimos la capa de **fundamentos electorales**, que es la base de todos los enfoques anteriores. Usamos solo resultados oficiales certificados. Las encuestas, la aprobación presidencial y la economía se proponen como extensiones en la sección 10.

## 4. Fuentes de datos

### 4.1 Fuentes utilizadas

| Fuente | Organismo | Documento | Años | Qué aporta |
|---|---|---|---|---|
| [FEC – Election results and voting information](https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/) | Federal Election Commission | *Federal Elections 2016 / 2018 / 2020 / 2022* (`federalelectionsXXXX.xlsx`) | 2016–2022 | Votos por partido y estado (Cámara, Senado, internas), resultados por distrito y candidato, voto presidencial por estado |
| Ídem | FEC | *2024 Presidential General Election Results* (`2024presgeresults.xlsx`, publicado el 16/01/2025) | 2024 | Voto presidencial por estado y candidato |
| [Election Statistics, 1920 to Present](https://history.house.gov/Institution/Election-Statistics/Election-Statistics/) | Clerk of the U.S. House of Representatives | *Statistics of the Presidential and Congressional Election of November 5, 2024* (`2024election_clerk.pdf`) | 2024 | Votos a la Cámara y al Senado por estado y partido, resultados por distrito |

**Por qué se usó el Clerk para 2024:** el FEC todavía no publicó *Federal Elections 2024*. Para 2024 solo tiene los resultados presidenciales. El Clerk de la Cámara es la otra fuente oficial que recopila los conteos certificados por cada estado desde 1920, así que completa la serie sin recurrir a fuentes secundarias.

### 4.2 Criterios de selección de las fuentes

1. **Autoridad y oficialidad.** Ambas son organismos federales que compilan los resultados **certificados** por las autoridades electorales de cada estado. Se descartaron agregadores periodísticos o académicos para los datos base, porque son fuentes secundarias.
2. **Trazabilidad.** Cada cifra del CSV se puede rastrear hasta una hoja y una celda del Excel del FEC, o hasta una tabla del PDF del Clerk. El script documenta cada paso.
3. **Consistencia temporal.** El FEC usa la misma estructura de tablas en todas sus ediciones. Esto permite construir una serie homogénea sin recodificar a mano.
4. **Granularidad.** Las fuentes tienen datos por estado y por distrito-candidato. Así se puede elegir la unidad de análisis y derivar variables (bancas ganadas, distritos sin oposición).
5. **Cobertura de los tres cargos.** Presidente, Senado y Cámara en la misma fuente permiten medir la correlación entre cargos.
6. **Actualidad.** Se incluye el ciclo más reciente (2024), el más informativo para predecir 2026.
7. **Acceso abierto y reproducibilidad.** Son obras del gobierno federal, de dominio público y gratuitas.

### 4.3 Criterio de selección del período (2016–2024)

- **Relevancia:** es la era de mayor nacionalización del voto (sección 3.3), y los dos candidatos presidenciales de 2016, 2020 y 2024 incluyen a Trump. El comportamiento electoral reciente es el mejor análogo para 2026.
- **Variación en el contexto:** incluye dos elecciones de medio término, una con presidente republicano (2018) y otra con presidente demócrata (2022). Esto permite observar el efecto de medio término en ambas direcciones.
- **Dos repartos de bancas:** los censos 2010 (elecciones hasta 2020) y 2020 (desde 2022).
- **Trade-off:** dos elecciones de medio término son pocas para estimar el efecto con precisión. El FEC publica ediciones desde 1982, y extender la serie hacia atrás (2014, 2010, 2006) es el primer paso sugerido para ampliar la muestra.

## 5. Unidad de análisis y diseño del dataset

**Unidad:** estado × año electoral. Son 50 estados × 6 años (2016, 2018, 2020, 2022, 2024 y 2026) = 300 filas. DC y los territorios quedan afuera porque sus delegados no votan en la Cámara.

### ¿Por qué estado y no distrito?

| Criterio | Estado | Distrito |
|---|---|---|
| Estabilidad de fronteras | Fijas | Cambian con cada redistribución (2022, y redistribuciones de mitad de década en 2025–26) |
| Unión con Presidente y Senado | Directa (ambos se votan por estado) | El voto presidencial por distrito requiere otras fuentes |
| Cantidad de observaciones | 250 con resultado | ~2.175 |
| Información sobre candidatos | Se pierde | Incumbencia, banca abierta |

**Conclusión:** para una primera etapa exploratoria, el estado da un panel limpio y comparable en el tiempo. Además, el Senado se elige por estado. El costo es no modelar directamente la conversión de votos en bancas, que se aborda después con una curva votos-bancas.

### Filas 2026

Las filas 2026 (`split = "predict"`) tienen completas las variables conocidas antes de la elección:

- tipo de ciclo y partido del presidente;
- bancas asignadas por estado;
- si hay elección al Senado en el estado;
- los rezagos (resultados de 2024).

Las variables objetivo quedan vacías. Así el mismo archivo sirve para entrenar (filas `train`) y para predecir.

## 6. Construcción y decisiones de procesamiento

1. **Votos a la Cámara y al Senado por partido (2016–2022).** Salen de las tablas *"Votes Cast for the U.S. House/Senate by Party"* del FEC, columnas de elección general y primaria.
2. **Elecciones especiales del mismo día.** Algunas vacantes se eligieron el mismo día que la elección general (por ejemplo, HI-01 y KY-01 en 2016). Sus votos se restan de los totales del estado, que el FEC suma en sus tablas. Sin esta corrección, Hawái 2016 mostraba más votos a la Cámara que a Presidente.
3. **Bancas ganadas.** Se usa el indicador de ganador (`GE WINNER INDICATOR`) de la hoja por distrito, agrupando las candidaturas de fusión por partido principal (por ejemplo, D/WF → D). Hay tres casos especiales:
    - Si falta la marca de ganador, decide la segunda vuelta si existió (LA-05 2020) o el voto general (IN-02 2022).
    - NC-09 2018 no se asigna, porque la elección fue anulada y se repitió en 2019.
    - **Validación:** el total nacional coincide con las cifras oficiales en los cinco ciclos (2016: 194 D / 241 R; 2018: 235 / 199; 2020: 222 / 213; 2022: 213 / 222; 2024: 215 / 220). El script falla si no coinciden.
4. **Datos 2024 desde el PDF del Clerk.**
    - Las tablas resumen (*"Recapitulation of Votes Cast for United States Representatives / Senators"*) están impresas rotadas 90°. Se reconstruyen a partir de la posición de cada carácter, y el script verifica que cada fila sume su propio total.
    - Las bancas y los distritos sin oposición salen del listado por candidato.
    - Las boletas en blanco o nulas y las rondas de voto preferencial ("Continuing/Exhausted Ballots" en Maine) se restan de la columna "otros", para que coincida con la definición del FEC.
5. **Voto presidencial.** Sale de la *Table 2* del FEC para 2016 y 2020, y de `2024presgeresults.xlsx` para 2024.
6. **Variables derivadas.** Cuotas bipartidistas; desvíos respecto del promedio nacional (suma de los 50 estados); rezagos del ciclo anterior; swing; roll-off (votantes que votan a Presidente pero no a la Cámara).
7. **Validación nacional.** La cuota demócrata bipartidista de la Cámara calculada coincide con el voto popular nacional conocido: 2016 49,4 %; 2018 54,5 %; 2020 51,5 %; 2022 48,7 %; 2024 48,7 %.

## 7. Diccionario de datos

Convención: `_d` = demócrata, `_r` = republicano, `_2p` = sobre el voto bipartidista D + R, `_rel` = desvío respecto del valor nacional del mismo año, `_lag` = ciclo bienal anterior, `_prev` = última elección presidencial anterior.

| Columna | Tipo | Descripción |
|---|---|---|
| `year` | int | Año de la elección general |
| `state`, `state_name` | str | Código postal y nombre del estado |
| `split` | str | `train` (2016–2024, con resultado) o `predict` (2026) |
| `is_midterm` | 0/1 | 1 si es elección de medio término |
| `pres_party` | D/R | Partido del presidente en ejercicio el día de la elección |
| `house_seats` | int | Bancas asignadas al estado (censo 2010 hasta 2020; censo 2020 desde 2022) |
| `house_votes_d/_r/_other/_total` | int | Votos a la Cámara en la elección general, por partido. En los estados con fusión de listas (NY, CT) cuenta solo la línea del partido principal, igual que el FEC |
| **`house_dem_share_2p`** | float | **Objetivo.** D / (D + R) en la Cámara |
| `house_margin_d` | float | (D − R) / total |
| `house_dem_share_2p_rel` | float | `house_dem_share_2p` − cuota nacional |
| `president_party_house_share_2p` | float | Cuota bipartidista del partido del presidente |
| `house_seats_d/_r` | int | Bancas ganadas por partido |
| `house_seat_share_d` | float | Bancas D / bancas del estado |
| `house_districts_no_d/_no_r` | int | Distritos sin candidato D / R en la general (sin oposición, o dos candidatos del mismo partido en CA y WA) |
| `house_contested_share` | float | Proporción de distritos con candidatos D y R |
| `house_primary_votes_d/_r` | int | Votos en las internas a la Cámara (incluye segundas vueltas). Disponible 2016–2022 |
| `house_primary_dem_share_2p` | float | Cuota D del voto en internas |
| `senate_race` | 0/1 | Hubo (o habrá, en 2026) elección al Senado en el estado |
| `senate_dr_contest` | 0/1 | La elección al Senado enfrentó a un D con un R |
| `senate_votes_d/_r/_other` | int | Votos al Senado en la general (se suman si hubo dos elecciones en el año) |
| `senate_dem_share_2p` | float | D / (D + R) en el Senado. Solo se completa si `senate_dr_contest = 1` |
| `pres_votes_d/_r/_total` | int | Voto presidencial (solo años presidenciales) |
| `pres_dem_share_2p`, `pres_dem_share_2p_rel` | float | Cuota D presidencial y desvío respecto del nacional (análogo al PVI) |
| `house_dropoff` | float | 1 − votos Cámara / votos Presidente (roll-off) |
| `nat_house_dem_share_2p`, `nat_pres_dem_share_2p` | float | Referencias nacionales del año |
| `house_dem_share_2p_lag`, `house_dem_share_2p_rel_lag`, `house_seats_d_lag` | float | Valores del ciclo anterior |
| `house_dem_swing` | float | Cambio en la cuota D respecto del ciclo anterior |
| `pres_dem_share_2p_prev`, `pres_dem_share_2p_rel_prev` | float | Última presidencial **estrictamente anterior** al año de la fila. Así no se filtra información del mismo año (en 2026 es la de 2024) |

**Faltantes esperados:**

- Presidente en años de medio término.
- Senado en los estados sin elección.
- Rezagos en 2016, porque 2014 no está incluido.
- Internas en 2024: el Clerk no las publica.
- Variables objetivo en 2026.

## 8. Análisis exploratorio preliminar

Correlación con `house_dem_share_2p` (filas de 2016 a 2024 con dato):

| Variable | Pearson | Spearman | Pearson (solo estados con todos sus distritos disputados, n = 159) |
|---|---|---|---|
| `pres_dem_share_2p` (mismo año) | 0,906 | 0,972 | 0,968 |
| `pres_dem_share_2p_prev` | 0,884 | 0,937 | 0,947 |
| `house_dem_share_2p_lag` | 0,867 | 0,932 | 0,901 |
| `house_seat_share_d` | 0,841 | 0,901 | 0,898 |
| `senate_dem_share_2p` | 0,798 | 0,892 | 0,823 |
| `house_primary_dem_share_2p` | 0,732 | 0,773 | 0,689 |
| `is_midterm` | 0,039 | 0,076 | 0,069 |

**Lectura de la tabla:**

1. **La nacionalización se confirma.** El voto presidencial previo explica la mayor parte de la variación entre estados (r ≈ 0,88–0,95). Es el mejor predictor disponible para 2026, porque la presidencial de 2024 ya ocurrió.
2. **Los distritos sin oposición son ruido de medición.** Al quedarse solo con los estados donde todos los distritos están disputados, las correlaciones suben (de 0,884 a 0,947). Hay que tratar esos distritos antes de modelar, por ejemplo imputando el voto esperado.
3. **La participación en internas tiene señal, pero más débil.** Esto coincide con lo que la literatura considera evidencia mixta. Tampoco está disponible para 2024 y 2026 en estas fuentes.
4. **`is_midterm` casi no se correlaciona con el nivel de voto demócrata**, y eso es esperable. El efecto de medio término no favorece siempre a un mismo partido: favorece al opositor al presidente. Se ve en el cambio (swing) medido desde el punto de vista del partido del presidente:

| Año | Presidente | Medio término | Cuota D nacional (Cámara) | Swing mediano del partido del presidente |
|---|---|---|---|---|
| 2018 | R | Sí | 54,5 % | −5,2 pp |
| 2020 | R | No | 51,5 % | +3,4 pp |
| 2022 | D | Sí | 48,7 % | −1,9 pp |
| 2024 | D | No | 48,7 % | +0,1 pp |

   En las dos elecciones de medio término el partido del presidente perdió terreno en el estado mediano. Esto coincide con la teoría de la sección 3.2 y sugiere que la variable útil es la interacción `is_midterm × pres_party`.

**Líneas base para comparar modelos futuros** (error absoluto medio en `house_dem_share_2p`, 2018–2024):

| Método ingenuo | MAE |
|---|---|
| Repetir el resultado del ciclo anterior | 4,57 pp |
| Usar la última presidencial | 4,36 pp |
| Swing uniforme (ciclo anterior + cambio nacional) | 3,52 pp |

Un modelo que no supere 3,5 pp de error medio no aporta sobre el swing uniforme.

## 9. Limitaciones y sesgos conocidos

- **Distritos sin oposición y sistema "top-two".** En CA y WA la general puede enfrentar a dos candidatos del mismo partido. Estos casos distorsionan la cuota del estado; se identifican con `house_districts_no_d/_no_r`.
- **Fusión de listas (NY, CT).** El voto de líneas aliadas (Working Families, Conservative) queda en "otros". Es el mismo criterio en todos los años.
- **Voto preferencial (Maine desde 2018, Alaska desde 2022) y sistema "jungle" de Luisiana.** Se usan los votos de la elección general reportados por cada fuente.
- **Senado.** Los independientes que compiten sin rival demócrata o con apoyo demócrata (Sanders en VT, King en ME, McMullin en UT 2022, Osborn en NE 2024) hacen que la cuota D/R no represente el alineamiento real. Cuando hay dos elecciones en el mismo año (por ejemplo, GA 2020 o NE 2024) los votos se suman.
- **Pocas elecciones de medio término (2).** El efecto de medio término se puede describir, pero no estimar con precisión.
- **Falacia ecológica.** Las correlaciones son entre estados, no entre individuos.
- **Redistribución de distritos de mitad de década (2025–2026).** Afecta la conversión de votos a bancas en 2026, no la cuota de voto por estado. Según la información disponible hasta mediados de 2026, hubo mapas nuevos en Texas, California (Proposición 50), Missouri, Carolina del Norte, Ohio y Utah, y había otros casos en curso (Virginia, Florida, y el fallo *Louisiana v. Callais* sobre la Voting Rights Act). **Hay que verificar el estado final de cada mapa a la fecha** antes de estimar bancas.
- **Totales 2024 del Clerk.** Las cuotas D/R coinciden exactamente con el Clerk. En `house_votes_other` y `house_dropoff` puede quedar alguna diferencia menor de definición respecto del FEC.

## 10. Próximos pasos propuestos

1. **Extender la serie hacia atrás** (FEC 2006–2014) para tener más elecciones de medio término.
2. **Agregar fundamentos no electorales**, siguiendo la sección 3:
    - aprobación presidencial (Gallup);
    - encuesta genérica al Congreso (promedios de encuestas);
    - ingreso real disponible y desempleo por estado (BEA y BLS);
    - participación sobre la población habilitada para votar (U.S. Elections Project);
    - demografía (Census ACS).
3. **Resultados de las internas 2026**, desde las secretarías de Estado de cada estado, para completar `house_primary_*` en las filas a predecir.
4. **Financiamiento de campaña:** la API OpenFEC (misma fuente) tiene recaudación por candidato, que se puede agregar por estado.
5. **Modelado:**
    - regresión o modelo jerárquico de `house_dem_share_2p` sobre `pres_dem_share_2p_rel_prev`, `house_dem_share_2p_rel_lag` y la interacción `is_midterm × pres_party`;
    - agregación al nivel nacional;
    - conversión a bancas con una curva votos-bancas calculada sobre los mapas 2026.

## Referencias

- Abramowitz, A. I. (1988). An improved model for predicting presidential election outcomes. *PS: Political Science & Politics*, 21(4), 843–847.
- Abramowitz, A. I., & Webster, S. (2016). The rise of negative partisanship and the nationalization of U.S. elections in the 21st century. *Electoral Studies*, 41, 12–22.
- Bafumi, J., Erikson, R. S., & Wlezien, C. (2010). Forecasting House seats from generic congressional polls: The 2010 midterm election. *PS: Political Science & Politics*, 43(4), 633–636.
- Campbell, A. (1960). Surge and decline: A study of electoral change. *Public Opinion Quarterly*, 24(3), 397–418.
- Campbell, J. E. (1987). The revised theory of surge and decline. *American Journal of Political Science*, 31(4), 965–979.
- Erikson, R. S. (1988). The puzzle of midterm loss. *The Journal of Politics*, 50(4), 1011–1029.
- Fair, R. C. (1978). The effect of economic events on votes for president. *The Review of Economics and Statistics*, 60(2), 159–173.
- Gelman, A., & King, G. (1994). A unified method of evaluating electoral systems and redistricting plans. *American Journal of Political Science*, 38(2), 514–554.
- Heidemanns, M., Gelman, A., & Morris, G. E. (2020). An updated dynamic Bayesian forecasting model for the US presidential election. *Harvard Data Science Review*, 2(4).
- Hopkins, D. J. (2018). *The Increasingly United States: How and Why American Political Behavior Nationalized*. University of Chicago Press.
- Jacobson, G. C. (2015). It's nothing personal: The decline of the incumbency advantage in US House elections. *The Journal of Politics*, 77(3), 861–873.
- Linzer, D. A. (2013). Dynamic Bayesian forecasting of presidential elections in the states. *Journal of the American Statistical Association*, 108(501), 124–134.
- Tufte, E. R. (1975). Determinants of the outcomes of midterm congressional elections. *American Political Science Review*, 69(3), 812–826.

**Fuentes de datos:**

- Federal Election Commission. *Federal Elections 2016; 2018; 2020; 2022* y *2024 Presidential General Election Results*. https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/
- Clerk of the U.S. House of Representatives. *Statistics of the Presidential and Congressional Election of November 5, 2024*. https://history.house.gov/Institution/Election-Statistics/Election-Statistics/
