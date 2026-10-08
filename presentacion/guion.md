# Guion de la presentación — Medio término 2026

Qué decir en cada diapositiva de [`presentacion.html`](presentacion.html). Duración total
estimada: **20–25 minutos** (unos 50 segundos por diapositiva).

**Cómo usar la presentación:** abrirla en el navegador (Chrome o Firefox). Flechas ← → o la barra
espaciadora para avanzar, `F` para pantalla completa, `Inicio`/`Fin` para ir al principio o al
final. La dirección muestra el número de diapositiva (`presentacion.html#18` abre la 18). Para
exportarla a PDF: Imprimir → Guardar como PDF (sale una diapositiva por página).

Cada sección tiene:

- **Decir:** el contenido, en el orden en que conviene contarlo.
- **Frase clave:** la idea que tiene que quedar si el público se acuerda de una sola cosa.
- **Pase:** cómo conectar con la siguiente diapositiva.
- **Si preguntan:** respuestas cortas a preguntas probables.

---

## Bloque 1 — El problema (diapositivas 1 a 4, ~4 min)

### 1. Portada

**Decir:** El trabajo busca predecir la elección de medio término del 3 de noviembre de 2026 en
Estados Unidos, para la Cámara de Representantes. No usamos encuestas: usamos solo resultados
oficiales de las elecciones de 2004 a 2024. Son 11 elecciones, 250 casos para aprender (50
estados en 5 medio término) y 50 estados a predecir.

**Pase:** "Primero, qué pregunta queríamos responder."

### 2. Pregunta de investigación e hipótesis

**Decir:** Leer la pregunta. De ella salen tres hipótesis, que después vamos a contrastar con el
modelo:

- **H1:** el voto presidencial de un estado anticipa su voto a la Cámara dos años después.
- **H2:** el partido del presidente pierde votos en el medio término, sea demócrata o
  republicano.
- **H3:** pierde más donde estaba más fuerte.

La variable que predecimos es la cuota demócrata del voto bipartidista: votos D sobre votos D +
R. Usamos la bipartidista para que los terceros partidos no distorsionen la comparación.

**Frase clave:** "Todo el trabajo gira alrededor de estas tres hipótesis."

**Pase:** "Estas hipótesis no son inventadas: vienen de la literatura."

**Si preguntan por qué bipartidista:** en EE. UU. los terceros partidos sacan pocos votos y su
presencia varía por estado y año; con la cuota bipartidista un 52 % siempre significa lo mismo.

### 3. Estado del arte

**Decir:** Cuatro líneas de investigación nos orientaron:

- Los **modelos de fundamentos** predicen sin encuestas, con variables estructurales. Nuestro
  trabajo es esa capa, con resultados electorales.
- Las teorías de la **pérdida de medio término** explican H2: en la presidencial, el candidato
  arrastra votantes que en el medio término no van (*surge and decline*); además, los votantes
  moderados equilibran el poder del presidente.
- La **nacionalización** explica H1: cada vez hay menos voto dividido, así que el voto a la
  Cámara se parece cada vez más al presidencial.
- La **curva votos-bancas** de Gelman y King, que usamos para pasar de votos a bancas.

**Pase:** "Con esto en mente armamos el dataset."

### 4. El dataset

**Decir:** La decisión de diseño más importante: **cada fila une dos elecciones del mismo
estado**. A la izquierda, lo que se sabe antes de votar (la presidencial anterior, columnas
`_prev`). A la derecha, el resultado del medio término. Por ejemplo, la fila 2018 tiene los
predictores de 2016 y el resultado de 2018.

Tenemos presidentes de los dos partidos: 3 demócratas y 2 republicanos. La fila 2026 tiene los
predictores de 2024 y el resultado vacío: es lo que predecimos.

Trabajamos por estado y no por distrito porque los distritos cambian de fronteras con cada
redistribución, y los estados no.

**Frase clave:** "Cada fila es una pregunta: con lo que sabíamos dos años antes, ¿qué pasó en el
medio término?"

**Si preguntan por qué no por distrito:** las fronteras cambiaron en 2012, 2022 y otra vez en
2025–26; además el voto presidencial por distrito no está en las fuentes oficiales que usamos.

---

## Bloque 2 — El trayecto y el preprocesamiento (diapositivas 5 y 6, ~2 min)

### 5. El trayecto del proyecto

**Decir:** Contar el camino en cinco pasos:

1. El **primer dataset** era un panel 2016–2026 con solo dos medio término. Con dos casos el
   efecto de medio término se podía describir, pero no estimar.
2. Por eso lo **rediseñamos** alrededor de cinco medio término, 2006–2022.
3. El script de construcción **valida** cada elección: 435 distritos y las bancas oficiales por
   partido. Esa validación encontró errores en las propias fuentes del FEC (señalar el recuadro):
   Luisiana contaba dos veces a los votantes con balotaje, Nevada 2014 tenía columnas
   intercambiadas, y las etiquetas de partido cambian según la época.
4. Con el dataset validado hicimos el **exploratorio**.
5. Y por último el **predictivo**.

**Frase clave:** "Validar contra las cifras oficiales nos mostró que ni la fuente oficial estaba
libre de errores."

### 6. Preprocesamiento

**Cómo leer los gráficos.**

*Izquierda — dónde faltan datos:*

- **Eje X:** año.
- **Eje Y:** columnas del dataset que tienen datos faltantes.
- Cada número es el % de estados sin ese dato en ese año (más oscuro = faltan más).

*Derecha — valores extremos (diagrama de caja):*

- **Eje X:** año.
- **Eje Y:** porcentaje de voto demócrata de cada estado.
- La caja contiene a la mitad de los estados; la línea violeta es la mediana; las líneas finas
  llegan hasta los valores normales; los círculos con sigla son los casos raros.

**Decir:** Dos decisiones:

- **Faltantes (izquierda):** distinguimos estructurales de reales. El Senado falta porque cada
  dos años se elige un tercio: no hubo elección, así que no imputamos (sería inventar una
  elección). Las internas faltan en estados que nominan por convención. Los predictores están
  completos.
- **Atípicos (derecha):** Massachusetts, Rhode Island, las Dakotas. No son errores: son estados
  donde un partido no presentó candidato. Los conservamos y los marcamos con
  `todos_disputados`, para analizar con y sin ellos.

**Pase:** "Con los datos limpios, primero miramos qué pasó."

---

## Bloque 3 — Descriptivo y exploratorio: las correlaciones (diapositivas 7 a 16, ~8 min)

### 7. Descriptivo

**Cómo leer el gráfico.**

- **Eje X:** pares de años: la presidencial y el medio término siguiente.
- **Eje Y:** bancas (de 435).
- Azul = bancas demócratas; rojo = republicanas. La línea punteada es la mayoría (218). Abajo dice
  cuántas bancas perdió el partido del presidente.

**Decir:** El partido del presidente perdió bancas en los cinco medio término: 30, 64, 13, 42 y 9.
Pasó con presidentes demócratas y republicanos. Pero el tamaño varía mucho: 64 en 2010 y solo 9
en 2022. Esa variación es la "ola nacional", y va a ser la parte más difícil de predecir.

**Frase clave:** "El signo se repite siempre; el tamaño no."

### 8. Distribuciones

**Cómo leer los gráficos.** Cada barra cuenta cuántos casos (estado + año, por ejemplo
"Pensilvania 2018") cayeron en un rango de valores.

*Izquierda — cuánto votó a los demócratas cada estado:*

- **Eje X:** porcentaje de voto demócrata (0 = todo republicano, 0,5 = empate, 1 = todo
  demócrata).
- **Eje Y:** cuántos casos.
- Rojo = ganó el republicano; azul = ganó el demócrata.

*Derecha — cuánto ganó o perdió el partido del presidente:*

- **Eje X:** cambio en su voto respecto de la presidencial anterior (−0,1 = perdió 10 puntos;
  0 = sin cambio).
- **Eje Y:** cuántos casos.
- Violeta = perdió votos; gris = ganó.

**Decir:**

> "Acá vemos cómo se distribuyen los datos. A la izquierda, el voto demócrata en cada estado: la
> mayoría está entre 30 y 70 %, y la forma es pareja a los dos lados. Los pocos casos extremos,
> como 0 % o 89 %, son estados donde un partido no presentó candidato.
>
> A la derecha, cuánto cambió el voto del partido del presidente: en el 86 % de los casos perdió
> votos, unos 5 puntos en el caso típico, sea demócrata o republicano.
>
> Y un dato que nos preocupa para el modelo: solo el 11 % de los casos fue parejo, entre 48 y
> 52 %. Son los que deciden la mayoría, y es donde tenemos menos ejemplos para aprender."

**Frase clave:** "El partido del presidente pierde votos en casi 9 de cada 10 casos."

**Si preguntan:**

- *¿Qué quiere decir que la distribución es "simétrica"?* Que tiene más o menos la misma forma a
  los dos lados del centro. Se comprueba porque la media (0,482) y la mediana (0,475) son casi
  iguales: si hubiera muchos valores extremos de un solo lado, arrastrarían a la media y se
  separaría de la mediana.
- *¿Qué son los casos de 0 % y de casi 90 %?* Distritos sin oposición. Dakota del Norte y Dakota
  del Sur 2022 tienen un solo distrito y los demócratas no presentaron candidato: 0 %. En
  Massachusetts 2006 los republicanos compitieron solo en 3 de los 10 distritos: 89 % D. Son
  valores reales pero distorsionados; por eso los marcamos con `todos_disputados`.
- *¿Por qué el swing se mide desde el partido del presidente y no desde los demócratas?* Porque
  medido como "cambio del voto D" sería negativo en 2010 (gobernaba Obama) y positivo en 2018
  (gobernaba Trump), y los dos se cancelarían. Desde el partido del presidente, el patrón es el
  mismo todos los años: pierde.
- *¿Qué es el "desbalance"?* Un término de ciencia de datos (desbalance de clases): una categoría
  tiene muchos menos ejemplos que las otras. Clasificamos los casos en sólido R (108), inclinado
  R (23), competitivo (27), inclinado D (17) y sólido D (75). Un modelo aprende sobre todo de las
  categorías con muchos ejemplos.
- *¿El desbalance arruina al modelo?* No: el modelo predice un número (la cuota D), no una
  categoría, así que no lo afecta como afectaría a un clasificador. Es un aviso: hay menos
  evidencia justo donde un error de 2 puntos cambia al ganador. Además, la mayoría se gana por
  distritos, no por estados; los estados competitivos son una aproximación.

### 9. Correlaciones X vs Y

**Cómo leer el gráfico.** Son cuatro gráficos de puntos; cada punto es un estado en un año.

- **Eje X:** un dato de la elección presidencial anterior (cambia en cada panel: voto a
  Presidente, voto a la Cámara, bancas e internas).
- **Eje Y:** porcentaje de voto demócrata en el medio término.
- Cuanto más se parecen los puntos a una línea, más fuerte es la relación (el número r arriba de
  cada panel). Violeta = todos los distritos tuvieron candidatos de los dos partidos; gris hueco =
  alguno sin oposición.

**Decir:** Cada punto es un estado en un medio término. La presidencial anterior, la Cámara
anterior y las bancas anteriores correlacionan fuerte con el resultado (0,75 a 0,79). Las
internas, menos (0,58). Pearson y Spearman coinciden, lo que indica que la relación es
aproximadamente lineal y no la generan unos pocos extremos. Eso ya sugiere que un modelo lineal va
a funcionar bien.

**Si preguntan la diferencia:** Pearson mide relación lineal sobre los valores; Spearman, relación
monótona sobre los rangos, y es robusto a atípicos.

### 10. Matriz de correlación

**Cómo leer el gráfico.**

- **Eje X y eje Y:** la misma lista de variables.
- Cada casillero es la correlación entre la variable de esa fila y la de esa columna, de −1 a 1.
- Azul = se mueven juntas; rojo = cuando una sube, la otra baja; blanco = sin relación. La
  primera fila es la importante: la relación de cada variable con el resultado.

**Decir:** La matriz sirve para decidir qué entra al modelo:

- Los tres predictores de la presidencial anterior correlacionan mucho entre sí (0,77 a 0,86):
  miden lo mismo desde ángulos distintos.
- El Senado correlaciona 0,70, pero se vota el mismo día, así que no es un predictor: es otro
  resultado.
- Las internas tienen señal, pero no tenemos datos de 2026.

**Frase clave:** "Una variable puede correlacionar mucho y aun así no servir para predecir, si no
se conoce antes de votar."

### 11. Subconjuntos

**Cómo leer el gráfico.**

- **Eje Y:** cada variable.
- **Eje X:** su correlación con el voto demócrata en el medio término (0 = ninguna relación,
  1 = relación perfecta).
- Gris = todos los estados; violeta = solo los estados donde todos los distritos tuvieron
  candidatos de los dos partidos. Hay que comparar las dos barras de cada variable.

**Decir:** Recalculamos las correlaciones solo con los estados donde todos los distritos tuvieron
candidato de los dos partidos. La de la Cámara anterior baja y la presidencial sube. ¿Por qué? Un
estado con un distrito sin rival suele tenerlo en las dos elecciones, entonces la misma
distorsión aparece en el predictor y en el resultado e infla la correlación. El voto presidencial
no tiene ese problema.

**Frase clave:** "En los estados disputados, el mejor predictor es el voto presidencial."

### 12. Nacionalización (H1)

**Cómo leer el gráfico.**

- **Eje X:** año del medio término.
- **Eje Y:** correlación entre la presidencial anterior y el resultado de ese año (más alto = la
  presidencial anticipa mejor).
- Cada línea es un predictor: violeta = voto a Presidente; gris rayada = voto a la Cámara;
  punteada = voto a Presidente, solo en estados con todos los distritos disputados.

**Decir:** Calculamos la correlación año por año. Con el voto presidencial pasa de 0,68 en
2006–2014 a 0,86 en 2018–2022, y en los estados disputados de los últimos años llega a 0,97–0,98.
Es la nacionalización que describe la literatura, medida con nuestros datos.

**Frase clave:** "La presidencial anticipa cada vez mejor al medio término."

### 13. Efecto de medio término (H2)

**Cómo leer el gráfico.** Una caja por año; cada caja resume los 50 estados.

- **Eje X:** año y partido del presidente.
- **Eje Y:** cuánto ganó o perdió el partido del presidente, en puntos (0 = sin cambio).
- La caja contiene a la mitad de los estados; la línea gruesa con el número es la mediana; los
  círculos son estados raros. El color es el partido del presidente.

**Decir:** El *swing* es el cambio en la cuota del partido del presidente respecto de la
presidencial anterior. Es negativo en los cinco años, entre −1,9 y −8,6 puntos en el estado
mediano, y el partido pierde en el 70 % a 96 % de los estados. Por eso, en el modelo medimos todo
**desde el partido del presidente** y no desde un partido fijo.

### 14. Dónde pierde más (H3)

**Cómo leer el gráfico.** Cada punto es un estado en un año.

- **Eje X:** cuánto había sacado el partido del presidente en la Cámara dos años antes.
- **Eje Y:** cuánto ganó o perdió en el medio término.
- La recta baja hacia la derecha: cuanto más fuerte estaba, más perdió.

**Decir:** Eje horizontal: cuánto había sacado el partido del presidente en la Cámara; eje
vertical: cuánto cambió. La correlación es −0,52: donde estaba más fuerte, pierde más. Es
consistente con *surge and decline* y con regresión a la media. Para el modelo significa que el
castigo no es igual en todos los estados.

### 15. Resumen de correlaciones

**Decir:** Esta tabla resume todo el exploratorio. Recorrerla por la última columna, que es lo
importante: qué hicimos con cada correlación.

- Presidencial y Cámara anteriores: predictores principales.
- Nacionalización: usamos presidentes de ambas épocas, sabiendo que la relación reciente es más
  fuerte.
- La correlación negativa con el swing nos dice que la pendiente tiene que ser menor que 1 (H3).
- Senado e internas quedan afuera aunque correlacionen, porque no se conocen antes de votar
  o no hay datos para 2026.

**Frase clave:** "Correlación no implica causalidad: estas relaciones eligen variables, no
prueban causas."

### 16. Líneas base

**Decir:** Antes de modelar, medimos cuánto erra una regla simple. Repetir la elección anterior
erra 6,6 puntos por estado. La mejor regla honesta, "presidencial anterior más el castigo promedio
de los otros años", erra **4,3 puntos**. Ese es el listón: un modelo que no baje de ahí no aporta
nada.

La última fila erra menos, pero hace trampa: usa el cambio nacional real, que no se conoce antes
de votar. Sirve como referencia de cuánto ganaríamos si acertáramos la ola.

**Pase:** "Con esto pasamos al modelo predictivo."

---

## Bloque 4 — El modelo predictivo (diapositivas 17 a 22, ~6 min)

### 17. Tres decisiones de diseño

**Decir:**

1. **Todo desde el partido del presidente.** Si el presidente es demócrata, usamos la cuota D; si
   es republicano, 1 menos la cuota D. Así un mismo modelo aprende el castigo con presidentes de
   los dos partidos. Además centramos en 0,5, para que el intercepto se lea directamente como el
   castigo en un estado parejo.
2. **Solo lo que se sabe antes de votar.**
3. **La validación (señalar la grilla).** Las 50 filas de un año comparten la misma ola nacional.
   Si mezcláramos las filas al azar, el modelo vería estados de 2010 al entrenar y le iría bien en
   otros estados de 2010 porque ya "conoce" la ola. Por eso dejamos afuera un medio término entero
   por vez: entrenamos con cuatro y predecimos el quinto, como si fuera el futuro.

**Frase clave:** "Cada medio término se predice sin haberlo visto."

**Si preguntan cómo se llama:** validación cruzada por grupos, *leave-one-group-out*.

### 18. Comparación de modelos

**Cómo leer el gráfico.**

- **Eje Y:** cada modelo o regla simple.
- **Eje X:** error promedio por estado, en puntos (barra más corta = mejor).
- Violeta = modelo elegido; gris claro = reglas simples (líneas base); línea punteada = la mejor
  regla simple (4,3).

**Decir:** Comparamos cinco modelos contra las dos líneas base. El elegido (violeta) erra
**3,5 puntos** por estado, contra 4,3 de la línea base.

¿Por qué no elegimos el de menor error? El de arriba agrega un "sesgo partidario" y erra 0,11
puntos menos, pero esa diferencia está dentro del margen de error de la estimación, y agrega un
parámetro que se estima con apenas cinco olas nacionales. Usamos la **regla de un error
estándar**: entre los modelos que empatan estadísticamente, el más simple.

El bosque aleatorio no le gana a la regresión lineal: con 250 filas y relaciones casi lineales, la
flexibilidad extra no ayuda.

**Frase clave:** "Más complejo no es mejor: con pocos datos, gana el modelo simple bien
validado."

**Si preguntan por la regla:** viene de Breiman y de *The Elements of Statistical Learning*. El
error estándar sale de la variación del error entre los cinco años.

### 19. Contraste de hipótesis

**Cómo leer el gráfico.** Un panel por hipótesis.

- **Eje X:** qué año se dejó afuera al entrenar.
- **Eje Y:** el valor del coeficiente calculado sin ese año.
- La línea punteada es la referencia de la hipótesis (0 para el castigo, 1 para las pendientes).
  Si los 5 puntos quedan del mismo lado, el resultado no depende de un año en particular.

**Decir:** Para cada hipótesis miramos un coeficiente y lo reestimamos cinco veces, dejando
afuera un año distinto cada vez. Si el signo no depende de qué año sacamos, la hipótesis es
robusta.

- **H1, se sostiene:** la pendiente sobre el voto presidencial es casi 1. Un punto más en la
  presidencial es un punto más en el medio término.
- **H2, se sostiene:** en un estado parejo, el partido del presidente pierde entre 4,6 y 5,5
  puntos, en los cinco casos.
- **H3, se sostiene con un matiz:** la pendiente sobre el voto a la Cámara es 0,75, menor que 1:
  donde el partido del presidente estaba más fuerte, pierde más. Pero sobre el voto presidencial
  la pendiente es 1. Es decir: el castigo es parejo en términos de la base partidaria; lo que
  "regresa" es el voto a la Cámara, que estaba inflado por legisladores en ejercicio o distritos
  sin rival, hacia lo que marca el voto presidencial.

**Frase clave:** "Las tres hipótesis se sostienen al sacar cualquier año, y H3 nos enseñó algo que
no esperábamos."

### 20. El modelo elegido

**Decir:** Esta es la ecuación. Tres lecturas:

- El voto presidencial y el de la Cámara se reparten el peso. Combinarlos compensa la distorsión
  de los distritos sin rival.
- El coeficiente nacional es negativo: cuanto mejor le fue al partido del presidente en todo el
  país, más pierde después. Es *surge and decline* a escala nacional.
- En 2024 los republicanos sacaron el 51,3 % nacional, así que ese término les suma
  aproximadamente un punto más de castigo en 2026.

### 21. Diagnóstico

**Cómo leer los gráficos.**

*Izquierda — predicción contra realidad:*

- **Eje X:** lo que predijo el modelo para un estado, sin haber visto ese año.
- **Eje Y:** lo que pasó realmente.
- La diagonal punteada es la predicción perfecta: cuanto más cerca de la línea, mejor.

*Derecha — error nacional por año:*

- **Eje X:** año y partido del presidente.
- **Eje Y:** error en el voto demócrata de todo el país (predicho − real). Negativo = el modelo
  predijo menos voto demócrata del que hubo.

**Decir:**

- **Izquierda:** predicción contra realidad, siempre fuera de muestra. R² de 0,82, y acierta qué
  partido gana el voto del estado en el 92 % de los casos. Los peores errores son los puntos
  grises, estados con distritos sin oposición.
- **Derecha:** el error nacional por año. Es chico, de 1 a 2 puntos, pero siempre del mismo lado:
  el modelo subestima a los demócratas. Si eso se repite, la predicción de 2026 es conservadora.

**Frase clave:** "El modelo es más bien conservador con los demócratas."

### 22. De votos a bancas

**Cómo leer el gráfico.** Cada punto es una elección (2004–2024); hueco = presidencial, relleno
= medio término.

- **Eje X:** porcentaje de voto demócrata en todo el país.
- **Eje Y:** bancas que ganaron los demócratas.
- La recta es la tendencia; la línea punteada horizontal, la mayoría (218). El punto violeta es
  la predicción 2026, y su barra horizontal, el rango probable.

**Decir:** El modelo predice votos, pero la mayoría se define en bancas. Ajustamos una recta con
las 11 elecciones de 2004 a 2024: cada punto de voto nacional son 6,3 bancas, y los demócratas
necesitan alrededor del 51,1 % para llegar a 218. Que haga falta más del 50 % es el sesgo de los
mapas: en 2012 los demócratas ganaron el voto popular y sacaron solo 201 bancas.

Primero probamos una curva estado por estado, pero exageraba las olas y erraba hasta 20 bancas,
así que la descartamos.

**Si preguntan por 2022 y 2024:** quedan por encima de la recta: con los mapas del censo 2020 los
demócratas sacaron unas 10 bancas más de lo que predice la recta. Los redibujos de 2025–2026
empujan en sentido contrario. Está en las limitaciones.

---

## Bloque 5 — Resultado y cierre (diapositivas 23 a 26, ~4 min)

### 23. Predicción 2026

**Cómo leer el gráfico.**

- **Eje X:** bancas demócratas.
- **Eje Y:** en cuántas de las 10.000 simulaciones salió esa cantidad.
- Azul = mayoría demócrata (218 o más); rojo = no llega. La línea violeta es la mediana (236).

**Decir:** Con presidente republicano, el modelo predice:

- **54 % de voto demócrata** a la Cámara, contra 48,7 % en 2024.
- **236 bancas demócratas**: hacen falta 218 para la mayoría.
- Simulamos 10.000 elecciones sumando los tres errores que medimos fuera de muestra: la ola
  nacional, el desvío de cada estado y el error de la curva de bancas. En el **88 %** de las
  simulaciones los demócratas obtienen la mayoría. El rango entre el percentil 10 y el 90 va de
  217 a 256 bancas.

**Frase clave:** "Los fundamentos electorales apuntan a una mayoría demócrata, aunque no está
asegurada."

**Si preguntan si 88 % es una probabilidad real:** es la probabilidad *dentro del modelo*. La ola
nacional se estima con solo 5 elecciones, así que el intervalo es orientativo; un modelo con
encuestas lo achicaría.

### 24. Por estado

**Cómo leer el gráfico.**

- **Eje Y:** los 50 estados, ordenados por la predicción.
- **Eje X:** porcentaje de voto demócrata.
- Círculo gris hueco = resultado 2024; punto de color = predicción 2026 (azul si pasa el 50 %,
  rojo si no). La línea entre los dos muestra cuánto se mueve el estado.

**Decir:** 46 de los 50 estados se mueven hacia los demócratas. Siete pasan a tener más del 50 %
de voto demócrata, y son justamente los estados bisagra de las presidenciales: Michigan,
Pensilvania, Nevada, Wisconsin, Georgia, Arizona y Carolina del Norte. Los que bajan, como Vermont
y Massachusetts, son estados donde en 2024 los republicanos no presentaron candidato en algunos
distritos: el modelo espera que esa distorsión no se repita igual.

### 25. Limitaciones

**Decir:**

- Tenemos 250 filas, pero la ola nacional se observa solo **5 veces**.
- Usamos solo resultados electorales: no hay encuestas, aprobación presidencial ni economía, que
  son lo que explica el tamaño de cada ola.
- En 2025–2026 varios estados redibujaron sus distritos. Eso cambia cuántas bancas da cada voto,
  no la cuota de voto. Hay que verificar los mapas finales.
- Los distritos sin oposición siguen siendo la principal fuente de error.

### 26. Conclusiones

**Decir:** Volver a la pregunta del principio:

- Sí: la presidencial anterior anticipa el medio término, casi uno a uno, y cada vez mejor.
- El partido del presidente pierde unos 5 puntos en un estado parejo, sea del partido que sea.
- El voto a la Cámara vuelve hacia el 50 %.
- Un modelo lineal simple y bien validado baja el error de 4,3 a 3,5 puntos, y uno más complejo no
  lo mejora.
- Para 2026: 54 % demócrata, unas 236 bancas, mayoría demócrata en el 88 % de las simulaciones.

Próximos pasos: sumar encuestas para estimar la ola, pasar a nivel distrito con los mapas nuevos
y, el 3 de noviembre, comparar con el resultado real.

**Frase clave para cerrar:** "En un mes vamos a saber cuánto le erramos."

---

## Preguntas generales que pueden aparecer

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué regresión lineal y no algo más sofisticado? | Lo probamos: el bosque aleatorio erra más (4,2 vs 3,5 pp). La relación es casi lineal (Pearson ≈ Spearman) y hay pocos datos. |
| ¿No hay fuga de información? | No: solo usamos predictores de la presidencial anterior, y cada año se predice con un modelo que no lo vio. Las líneas base también calculan el castigo con los otros años. |
| ¿Cuánto pesa la falta de encuestas? | El desvío propio de cada estado es de 4,9 pp y el de la ola nacional, de 1,4 pp. Las encuestas ayudarían sobre todo con la ola. |
| ¿Por qué 2006 y no antes? | Antes el voto dividido era mucho más común y la relación presidencial-Cámara era más débil. Ya en 2006 se ve la correlación más baja de la serie. |
| ¿El modelo sabe que el presidente es Trump? | Sabe que es republicano: todo se mide desde el partido del presidente. No usa nada específico de la persona. |
| ¿Dónde está el código? | `analisis_exploratorio/05_predictivo.py`; se corre con `../.venv/bin/python 05_predictivo.py` desde esa carpeta. |
