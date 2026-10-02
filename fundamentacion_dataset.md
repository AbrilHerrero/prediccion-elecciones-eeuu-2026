# Predicción de las elecciones de medio término de EE. UU. (3 de noviembre de 2026)

## Etapa 1 — Construcción y fundamentación del dataset

Archivos de esta entrega:

| Archivo | Contenido |
|---|---|
| `dataset_midterms.csv` | Panel estado × elección de medio término, 2006–2026 (300 filas × 42 columnas) |
| `construir_dataset_midterms.py` | Script que genera el CSV desde las fuentes originales (reproducible) |
| `fundamentacion_dataset.md` | Este documento |
| `GLOSARIO.md` | Significado de cada columna, con ejemplos |
| `excelsMidterms/`, `excelPres/` (locales, fuera del repositorio) | Fuentes primarias sin modificar (ver sección 4) |

Para regenerar el dataset: `.venv/bin/python construir_dataset_midterms.py`

---

## 1. Objetivo y pregunta de investigación

**Objetivo general:** predecir el resultado de la elección de medio término del 3 de noviembre de
2026 en EE. UU. para la Cámara de Representantes (435 bancas).

**Objetivo de esta etapa:** construir, a partir de fuentes oficiales, un dataset de las
elecciones de medio término anteriores que permita medir qué información disponible **antes**
de votar se relaciona con el resultado en cada estado.

**Pregunta de investigación:** *¿Cuánto anticipa el resultado de la elección presidencial
anterior (voto a Presidente, voto a la Cámara y bancas en cada estado) el voto a la Cámara en
la elección de medio término siguiente, y cuánto pierde en ella el partido del presidente?*

**Variable objetivo principal:** `house_dem_share_2p`, la proporción demócrata del voto
bipartidista a la Cámara en cada estado: D / (D + R).

**Variables objetivo secundarias:** `president_party_swing` (cuánto cambió el voto del partido
del presidente respecto de la presidencial anterior) y `house_seats_d` (bancas ganadas).

## 2. Tipo de estudio

El trabajo combina dos enfoques, en dos etapas:

1. **Exploratorio-descriptivo (esta etapa).** Describimos y medimos correlaciones para generar
   hipótesis sobre qué variables tienen poder predictivo y qué problemas de calidad tienen los
   datos (distritos sin candidato opositor, sistemas electorales distintos por estado).
2. **Predictivo (etapas siguientes).** Con las variables elegidas, entrenamos modelos sobre los
   medio término 2006–2022 y los aplicamos a las filas 2026 (`split = "predict"`).

Es un estudio **observacional, retrospectivo y longitudinal (panel)**: se observan los mismos 50
estados en 5 elecciones de medio término, sin intervenir sobre ellos.

## 3. Estado del arte

La predicción electoral en EE. UU. tiene una literatura amplia. Se agrupa en cuatro líneas, y este
dataset toma elementos de cada una.

### 3.1 Modelos de "fundamentos" (fundamentals)

Predicen el resultado con variables estructurales, sin encuestas.

- **Fair (1978)** y **Abramowitz (1988, modelo "Time for Change")** modelan el voto presidencial
  con el crecimiento económico, la aprobación presidencial y la cantidad de mandatos del partido
  en el poder.
- Para las elecciones de medio término, **Tufte (1975)** mostró que la pérdida de votos del
  partido del presidente se explica por la aprobación presidencial y el ingreso real disponible.

### 3.2 Teorías de la pérdida en medio término

El partido del presidente pierde bancas en casi todas las elecciones de medio término desde la
Guerra Civil. Hay tres explicaciones principales:

- **"Surge and decline"** (A. Campbell, 1960; J. E. Campbell, 1987): en la elección
  presidencial, el entusiasmo por el candidato ganador arrastra votantes periféricos. En el medio
  término esos votantes no van a votar, y el partido del presidente pierde ese impulso.
- **Balance o castigo** (Erikson, 1988): los votantes moderados compensan el poder del
  presidente votando al partido opositor.
- **Referéndum:** la elección de medio término funciona como un plebiscito sobre la gestión
  (Tufte, 1975).

**Implicancia para el diseño:** la pérdida es del *partido del presidente*, no de un partido
fijo. Por eso el dataset mide el cambio desde ese punto de vista (`president_party_swing`) y
guarda `pres_party`. Para 2026 el presidente es republicano (Trump), así que la teoría predice
un desplazamiento hacia los demócratas.

### 3.3 Nacionalización y declive del voto dividido

Desde los años 2000, el voto a la Cámara está cada vez más alineado con el voto presidencial en
cada estado y distrito:

- El valor de ser el legislador en ejercicio (incumbencia) cae (Jacobson, 2015).
- El voto dividido entre partidos casi desaparece, por la "partidización negativa": se vota
  contra el partido rival más que a favor del propio (Abramowitz & Webster, 2016).
- La política estadual y local pasa a reflejar la nacional (Hopkins, 2018).

Por eso índices como el **Cook PVI** usan el voto presidencial relativo al nacional para medir la
inclinación partidaria de un distrito. Nuestras variables `pres_dem_share_2p_rel_prev` y
`house_dem_share_2p_rel_prev` son análogos a nivel estado. Como el período cubre 2006–2022, el
dataset permite además **medir** si esa nacionalización ocurrió (sección 8.2).

### 3.4 Modelos con encuestas y bayesianos

- **Bafumi, Erikson & Wlezien (2010):** predicen las bancas de la Cámara a partir de la encuesta
  genérica ("¿a qué partido votaría para el Congreso?").
- **Linzer (2013):** modelo bayesiano dinámico que combina fundamentos con encuestas estaduales.
- **Heidemanns, Gelman & Morris (2020):** modelo de *The Economist*, también bayesiano.
- **FiveThirtyEight:** combina encuestas, fundamentos y calificaciones de expertos.

En todos, los fundamentos estructurales funcionan como *prior* y las encuestas lo actualizan.

### 3.5 De votos a bancas

La relación entre votos y bancas depende del mapa de distritos. **Gelman & King (1994)**
formalizaron la curva votos-bancas y el sesgo partidario. El supuesto más simple es el **swing
uniforme**: todos los distritos se mueven lo mismo que el promedio nacional. Lo usamos como línea
base en la sección 8.4.

### 3.6 Dónde se ubica este trabajo

Construimos la capa de **fundamentos electorales**, que es la base de todos los enfoques
anteriores. Usamos solo resultados oficiales certificados. Las encuestas, la aprobación
presidencial y la economía se proponen como extensiones en la sección 10.

## 4. Fuentes de datos

### 4.1 Fuentes utilizadas

| Fuente | Organismo | Documento | Años | Qué aporta |
|---|---|---|---|---|
| [FEC – Election results and voting information](https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/) | Federal Election Commission | *Federal Elections 2004 … 2022* (`federalelectionsXXXX.xls[x]`) | 2004–2022 | Resultados por distrito y candidato (Cámara), votos por partido y estado (Senado, internas), voto presidencial por estado |
| Ídem | FEC | *2024 Presidential General Election Results* (`2024presgeresults.xlsx`) | 2024 | Voto presidencial por estado y candidato |
| [Election Statistics, 1920 to Present](https://history.house.gov/Institution/Election-Statistics/Election-Statistics/) | Clerk of the U.S. House of Representatives | *Statistics of the Presidential and Congressional Election of November 5, 2024* (`2024election_clerk.pdf`) | 2024 | Votos a la Cámara por estado y partido, resultados por distrito |

Organización local de los archivos (no se suben al repositorio):

| Carpeta | Archivos | Para qué se usan |
|---|---|---|
| `excelsMidterms/` | `federalelections2006.xls`, `2010.xls`, `2014.xls`, `2018.xlsx`, `2022.xlsx` | Resultado de cada medio término e internas |
| `excelPres/` | `federalelections2004.xls`, `2008.xls`, `2012.xls`, `2016.xlsx`, `2020.xlsx`, `2024presgeresults.xlsx`, `2024election_clerk.pdf` | Predictores (`_prev`) de la presidencial anterior |

**Por qué se usó el Clerk para 2024:** al construir el dataset, el FEC solo tenía publicados los
resultados presidenciales de 2024. El Clerk de la Cámara es la otra fuente oficial que recopila
los conteos certificados por cada estado, así que completa la serie sin recurrir a fuentes
secundarias.

### 4.2 Criterios de selección de las fuentes

1. **Autoridad y oficialidad.** Ambas son organismos federales que compilan los resultados
   **certificados** por las autoridades electorales de cada estado. Se descartaron agregadores
   periodísticos o académicos para los datos base, porque son fuentes secundarias.
2. **Trazabilidad.** Cada cifra del CSV se puede rastrear hasta una hoja del Excel del FEC o una
   tabla del PDF del Clerk. El script documenta cada paso.
3. **Consistencia temporal.** El FEC publica las mismas tablas en todas sus ediciones (aunque con
   nombres de hoja y columnas que cambian), lo que permite una serie homogénea de 20 años.
4. **Granularidad.** Las fuentes tienen datos por distrito y candidato. Así se pueden derivar
   variables (bancas ganadas, distritos sin oposición) y controlar los totales.
5. **Cobertura de los tres cargos.** Presidente, Senado y Cámara en la misma fuente.
6. **Acceso abierto y reproducibilidad.** Son obras del gobierno federal, de dominio público y
   gratuitas.

### 4.3 Criterio de selección del período (medio término 2006–2022)

- **Solo elecciones de medio término como filas.** La pregunta es sobre una elección de medio
  término, y estas se comportan distinto de las presidenciales (no hay candidato presidencial
  que arrastre votos, cae la participación y el partido del presidente pierde). Mezclar ambos
  tipos obligaría al modelo a aprender las dos dinámicas con los mismos datos.
- **Cinco elecciones de medio término**, con presidentes de los dos partidos: 2006 (R), 2010
  (D), 2014 (D), 2018 (R) y 2022 (D). Con las dos de la versión anterior del dataset
  (2018 y 2022) el efecto se podía describir, pero no estimar.
- **Por qué no antes de 2006.** Antes de mediados de los 2000 el voto dividido era mucho más
  común (sección 3.3), y la relación entre el voto presidencial y el voto a la Cámara era más
  débil. Incluso dentro del período elegido se ve el cambio: 2006 es el año con menor
  correlación (sección 8.2). Extender más atrás aumenta la muestra a costa de mezclar épocas con
  comportamientos distintos.
- **Tres repartos de bancas:** censo 2000 (2006–2010), censo 2010 (2014–2018) y censo 2020
  (2022–2026). Por eso el dataset trabaja con proporciones y no con cantidades de bancas.

## 5. Unidad de análisis y diseño del dataset

**Unidad:** estado × elección de medio término. Son 50 estados × 6 años (2006, 2010, 2014,
2018, 2022 y 2026) = 300 filas. DC y los territorios quedan afuera porque sus delegados no votan
en la Cámara.

### Cada fila une dos elecciones

| Bloque de columnas | Elección de origen | Ejemplo para la fila 2018 |
|---|---|---|
| Predictores (`_prev`) | Presidencial anterior | Voto a Presidente, a la Cámara y bancas en 2016 |
| Previas a la general | Medio término, antes del día de la elección | Internas 2018, candidaturas por distrito |
| Resultado | Medio término | Voto y bancas a la Cámara 2018 |

Los predictores vienen de la presidencial **inmediatamente anterior** porque es la última
información electoral disponible antes de votar, y porque así se mide exactamente lo que dice la
teoría de la sección 3.2: cuánto cambia el voto entre la presidencial y el medio término.

### ¿Por qué estado y no distrito?

| Criterio | Estado | Distrito |
|---|---|---|
| Estabilidad de fronteras | Fijas | Cambian con cada redistribución (2002, 2012, 2022, y redistribuciones de mitad de década en 2025–26) |
| Unión con Presidente y Senado | Directa (ambos se votan por estado) | El voto presidencial por distrito requiere otras fuentes |
| Cantidad de observaciones | 250 con resultado | ~2.175 |
| Información sobre candidatos | Se pierde | Incumbencia, banca abierta |

**Conclusión:** para una primera etapa exploratoria, el estado da un panel limpio y comparable en
el tiempo a pesar de los cambios de mapa. El costo es no modelar directamente la conversión de
votos en bancas, que se aborda después con una curva votos-bancas.

### Filas 2026

Las filas 2026 (`split = "predict"`) tienen completos los predictores `_prev` (de la elección
2024), el partido del presidente, las bancas por estado y si hay elección al Senado. El resultado
queda vacío. Así el mismo archivo sirve para entrenar (filas `train`) y para predecir.

## 6. Construcción: cómo funciona `construir_dataset_midterms.py`

El script lee las fuentes, arma una tabla de resultados por estado para **cada una de las 11
elecciones** (2004 a 2024), la valida y después une cada medio término con su presidencial
anterior.

| Paso | Función | Qué hace |
|---|---|---|
| 1 | `libro_fec`, `hoja` | Abre el Excel del año y busca cada hoja por un patrón de nombre (por ejemplo `House (Votes )?by Party`), porque los nombres cambian entre ediciones. Si ninguna o más de una hoja coincide, el script falla |
| 2 | `distritos_fec` | Lee los resultados por distrito y candidato: votos a la Cámara por partido, bancas ganadas y distritos sin candidato D o R |
| 3 | `tabla_por_partido` | Lee las tablas por partido del FEC: internas a la Cámara y votos al Senado |
| 4 | `presidente_fec`, `presidente_2024` | Lee el voto popular presidencial por estado |
| 5 | `eleccion_2024` y auxiliares | Extrae la Cámara 2024 del PDF del Clerk |
| 6 | `controlar_bancas` | Verifica que haya 435 distritos y que las bancas por partido coincidan con las oficiales |
| 7 | `con_derivadas` | Calcula cuotas, referencias nacionales y desvíos de cada elección |
| 8 | `construir` | Une cada medio término con su presidencial anterior (`_prev`), calcula los swings y escribe el CSV |

### Decisiones de procesamiento

1. **Ganador de cada distrito.** Antes de 2012 el FEC no marca al ganador, así que se calcula.
   Primero se suman los votos de cada candidato en todas sus líneas de partido (las fusiones de
   NY y CT: el mismo candidato figura como D y como Working Families). Después se aplica este
   orden de prioridad:
    1. la marca de ganador del FEC, si existe (cubre el voto preferencial de Maine 2018);
    2. un candidato sin rival ("Unopposed");
    3. el balotaje, si existió (Luisiana, Georgia);
    4. el que más votos sacó en la general.
2. **Votos a la Cámara: suma de los distritos, no la tabla por partido.** Al validar se encontró
   que la tabla por partido del FEC tiene dos problemas:
    - En Luisiana suma la primera vuelta de noviembre y el balotaje de diciembre, contando dos
      veces a los mismos votantes.
    - En Nevada 2014 tiene intercambiados los votos republicanos y los de otros partidos.

   Sumar los distritos usa la misma hoja que las bancas, toma en cada distrito la vuelta que
   decidió la banca y deja afuera las elecciones especiales por mandato incompleto celebradas el
   mismo día.
3. **Etiquetas de partido.** Se normalizan las variantes de cada época: `D`, `DEM`, `DFL`
   (Minnesota) y `DNL` (Dakota del Norte) son demócratas; `R`, `REP` y `GOP` (Washington) son
   republicanos. Las etiquetas compuestas cuentan para el primer partido mayor que nombran
   (`D/WF`, `W(DEM)/DEM`, `D(UND)`); los votos escritos a mano (`W(...)`) cuentan como otros.
4. **Filas repetidas.** En 2004 el FEC agrega una fila sin partido con el total combinado de cada
   candidato de fusión. Se descarta, porque repetía sus votos (en NY-29 daba ganador al
   candidato equivocado).
5. **Casos especiales.** NC-09 2018 no se asigna (elección anulada y repetida en 2019). Bernie
   Sanders (VT, 2004) cuenta como independiente.
6. **Datos 2024 desde el PDF del Clerk.** Las tablas resumen están impresas rotadas 90°; se
   reconstruyen a partir de la posición de cada carácter y el script verifica que cada fila sume
   su propio total. Las boletas en blanco o nulas se restan de "otros".
7. **Validaciones.** El script falla si algo no coincide con las cifras oficiales:
    - 435 distritos en cada una de las 11 elecciones;
    - bancas por partido: 2004 202 D / 232 R; 2006 233 / 202; 2008 257 / 178; 2010 193 / 242;
      2012 201 / 234; 2014 188 / 247; 2016 194 / 241; 2018 235 / 199; 2020 222 / 213;
      2022 213 / 222; 2024 215 / 220.

   Además, la cuota D nacional calculada coincide con el voto popular conocido: por ejemplo,
   54,1 % en 2006, 46,5 % en 2010 y 47,1 % en 2014.

## 7. Diccionario de datos

El significado de cada columna, con ejemplos, está en [`GLOSARIO.md`](GLOSARIO.md). En resumen:

| Grupo | Columnas principales |
|---|---|
| Contexto | `year`, `state`, `split`, `pres_party`, `house_seats`, `senate_race` |
| Predictores (`_prev`) | `pres_dem_share_2p_prev`, `house_dem_share_2p_prev`, sus versiones `_rel`, `house_seat_share_d_prev`, `house_contested_share_prev`, `house_dropoff_prev` |
| Previas a la general | `house_primary_dem_share_2p`, `house_contested_share`, `house_districts_no_d/_no_r` |
| Resultado | **`house_dem_share_2p`**, `house_dem_swing`, `president_party_swing`, `house_seats_d/_r`, `senate_dem_share_2p` |

**Faltantes esperados:** Senado en los estados sin elección; internas en 10 filas (estados que
nominan por convención o sin interna partidaria); resultado e internas en 2026. Los predictores
`_prev` están completos.

## 8. Análisis exploratorio preliminar

El detalle, con gráficos, está en [`analisis_exploratorio/`](analisis_exploratorio/).

### 8.1 Correlaciones con `house_dem_share_2p`

| Variable | Pearson | Spearman | Pearson, solo estados con todos sus distritos disputados (n = 167) |
|---|---|---|---|
| `house_dem_share_2p_prev` | 0,793 | 0,801 | 0,769 |
| `pres_dem_share_2p_prev` | 0,760 | 0,797 | 0,783 |
| `house_seat_share_d_prev` | 0,753 | 0,774 | 0,778 |
| `senate_dem_share_2p` (mismo día) | 0,701 | 0,774 | 0,684 |
| `house_primary_dem_share_2p` | 0,580 | 0,627 | 0,507 |

1. **La presidencial anterior anticipa bien el medio término** (r ≈ 0,76–0,79).
2. **Los distritos sin oposición distorsionan las medidas de la Cámara.** Cuando un estado tiene
   un distrito sin oposición, suele tenerlo en las dos elecciones, y la misma distorsión aparece
   en el predictor y en el resultado. Eso infla la correlación de `house_dem_share_2p_prev`, que
   baja al quitar esos estados. El voto presidencial no tiene ese problema y queda como el mejor
   predictor en los estados disputados.
3. **Las internas tienen señal, pero más débil**, y no están disponibles para 2026 en estas
   fuentes.

### 8.2 Nacionalización: la relación se hizo más fuerte

| Período | r (Presidente anterior) | r (Cámara anterior) |
|---|---|---|
| 2006–2014 | 0,675 | 0,715 |
| 2018–2022 | 0,860 | 0,888 |

Por año, la correlación con el voto presidencial anterior pasa de 0,62 en 2006 a 0,88–0,96 desde
2010 (0,97–0,98 en los estados disputados de 2018 y 2022). Es la nacionalización de la sección
3.3 medida con nuestros datos. Para 2026, la relación reciente es la más relevante.

### 8.3 Efecto de medio término

| Año | Presidente | Bancas perdidas por su partido | Swing nacional del partido del presidente | Swing en el estado mediano | Estados en que pierde |
|---|---|---|---|---|---|
| 2006 | R | 30 | −5,5 pp | −6,5 pp | 96 % |
| 2010 | D | 64 | −8,9 pp | −8,6 pp | 96 % |
| 2014 | D | 13 | −3,5 pp | −3,6 pp | 78 % |
| 2018 | R | 42* | −4,9 pp | −5,2 pp | 90 % |
| 2022 | D | 9 | −2,9 pp | −1,9 pp | 70 % |

\* NC-09 quedó sin asignar; contándola (la ganó un republicano en 2019), la pérdida es de 41.

En las cinco elecciones el partido del presidente perdió votos y bancas, con presidentes de los
dos partidos. Además, **pierde más donde estaba más fuerte**: la correlación entre su cuota
previa a la Cámara y su swing es −0,52 (−0,66 en los estados disputados). Es consistente con
"surge and decline" y con regresión a la media.

### 8.4 Líneas base para comparar modelos futuros

Error absoluto medio en `house_dem_share_2p`, en puntos porcentuales:

| Método ingenuo | MAE todos | MAE disputados |
|---|---|---|
| Repetir la Cámara de la presidencial anterior | 6,56 | 6,50 |
| Usar el voto presidencial anterior | 6,00 | 5,31 |
| Cámara anterior + castigo medio de los otros medio término | 4,75 | 5,18 |
| **Presidencial anterior + castigo medio de los otros medio término** | **4,31** | **4,13** |
| Swing uniforme con el cambio nacional real (cota optimista) | 3,81 | 3,99 |

El "castigo medio" de cada año se calcula con los otros cuatro medio término, para no usar
información que no se conocía antes de votar. El swing uniforme usa el cambio nacional real, así
que no es una predicción posible: indica cuánto se ganaría acertando la ola nacional.

**Un modelo que no baje de 4,3 pp de error medio no aporta sobre la regla "presidencial anterior
más castigo promedio".**

## 9. Limitaciones y sesgos conocidos

- **Distritos sin oposición y sistema "top-two".** En CA y WA la general puede enfrentar a dos
  candidatos del mismo partido. Estos casos distorsionan la cuota del estado; se identifican con
  `house_districts_no_d/_no_r` y `house_contested_share`.
- **Fusión de listas (NY, CT).** El voto de líneas aliadas (Working Families, Conservative) queda
  en "otros". Es el mismo criterio en todos los años.
- **Voto preferencial (Maine desde 2018, Alaska desde 2022) y balotajes (Luisiana, Georgia).** Se
  usan los votos de la vuelta que decidió la banca, según cada fuente.
- **Roll-off atípico en Luisiana 2008.** El huracán Gustav postergó las internas; dos distritos
  votaron la general en diciembre con muy baja participación y otros dos no tuvieron rival. Eso
  da un roll-off de 47 % en `house_dropoff_prev` de LA 2010.
- **Senado.** Los independientes que compiten sin rival demócrata o con apoyo demócrata (Sanders
  en VT, King en ME, McMullin en UT 2022) hacen que la cuota D/R no represente el alineamiento
  real. Cuando hay dos elecciones en el mismo año se suman.
- **Cinco elecciones de medio término.** Son 250 filas, pero el efecto nacional de cada año es uno
  solo: para la "ola" nacional hay 5 observaciones, no 250.
- **Falacia ecológica.** Las correlaciones son entre estados, no entre individuos.
- **Redistribución de distritos de mitad de década (2025–2026).** Afecta la conversión de votos a
  bancas en 2026, no la cuota de voto por estado. Según la información disponible hasta mediados
  de 2026, hubo mapas nuevos en Texas, California (Proposición 50), Missouri, Carolina del Norte,
  Ohio y Utah, y había otros casos en curso (Virginia, Florida, y el fallo *Louisiana v. Callais*
  sobre la Voting Rights Act). **Hay que verificar el estado final de cada mapa a la fecha** antes
  de estimar bancas.
- **Totales 2024 del Clerk.** Las cuotas D/R coinciden exactamente con el Clerk. En
  `house_dropoff_prev` de 2026 puede quedar alguna diferencia menor de definición respecto del FEC.

## 10. Próximos pasos propuestos

1. **Agregar fundamentos no electorales a nivel nacional**, que explican el tamaño de la ola de
   cada año (sección 3):
    - aprobación presidencial (Gallup);
    - encuesta genérica al Congreso (promedios de encuestas);
    - ingreso real disponible y desempleo (BEA y BLS).
2. **Resultados de las internas 2026**, desde las secretarías de Estado de cada estado, para
   completar `house_primary_*` en las filas a predecir.
3. **Modelado:**
    - regresión o modelo jerárquico de `house_dem_share_2p` sobre `pres_dem_share_2p_rel_prev`,
      el partido del presidente y la cuota previa de su partido;
    - validación dejando afuera un medio término por vez (las filas de un mismo año no son
      independientes);
    - agregación al nivel nacional y conversión a bancas con una curva votos-bancas sobre los
      mapas 2026.

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

- Federal Election Commission. *Federal Elections 2004; 2006; 2008; 2010; 2012; 2014; 2016; 2018; 2020; 2022* y *2024 Presidential General Election Results*. https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/
- Clerk of the U.S. House of Representatives. *Statistics of the Presidential and Congressional Election of November 5, 2024*. https://history.house.gov/Institution/Election-Statistics/Election-Statistics/
