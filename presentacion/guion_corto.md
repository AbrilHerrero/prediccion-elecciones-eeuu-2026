# Guion de la presentación — Medio término 2026

Qué decir en cada diapositiva de [`presentacion_corta.html`](presentacion_corta.html). Son 8 diapositivas,
unos **6–8 minutos** en total.

**Cómo usar la presentación:** abrirla en el navegador. Flechas ← → o la barra espaciadora para
avanzar, `F` para pantalla completa. Para exportarla a PDF: Imprimir → Guardar como PDF.

---

### 1. Portada

**Decir:**

> "Nuestro trabajo intenta responder quién va a ganar el Congreso de Estados Unidos en la
> elección del 3 de noviembre de 2026. Y lo hacemos sin encuestas: solo con los resultados
> oficiales de las elecciones pasadas."

---

### 2. Qué se vota y qué queremos saber

**Decir:**

> "En Estados Unidos, la Cámara de Representantes tiene 435 bancas, y el partido que llega a
> 218 tiene la mayoría. Se vota cada dos años, y la elección que cae a mitad del mandato del
> presidente se llama 'de medio término'. Compiten dos partidos, demócratas y republicanos, y hoy
> el presidente es republicano.
>
> Nuestra pregunta es simple: ¿podemos anticipar el resultado mirando cómo votó cada estado en
> la elección presidencial de dos años antes?"

**Frase clave:** "Mirar el pasado para predecir el próximo resultado."

---

### 3. Nuestras tres hipótesis

**Decir:**

> "Partimos de tres ideas:
>
> 1. Un estado vota en el medio término parecido a como votó dos años antes.
> 2. El partido del presidente paga un costo: pierde votos, sea demócrata o republicano.
> 3. Donde había ganado por mucho, pierde más.
>
> Para comprobarlas comparamos las cinco elecciones de medio término desde 2006 con la
> presidencial anterior a cada una. Son 250 casos: 50 estados por 5 elecciones."

---

### 4. Las tres hipótesis se cumplieron

**Cómo leer el gráfico.**

- **Eje X:** pares de años: la elección presidencial y el medio término siguiente (por ejemplo,
  2016 y 2018).
- **Eje Y:** bancas (de 435).
- Azul = bancas demócratas; rojo = republicanas. La línea punteada es la mayoría (218). Abajo
  dice cuántas bancas perdió el partido del presidente.

**Decir:**

> "Las tres se cumplieron. El gráfico muestra la más clara: en cada par de barras, la de la
> izquierda es después de la presidencial y la de la derecha, dos años después. En las cinco
> elecciones el partido del presidente perdió bancas, con presidentes de los dos partidos: 30,
> 64, 13, 42 y 9.
>
> Además, los estados votan casi igual que dos años antes, y cada vez más. Y donde el partido
> del presidente había ganado por mucho, su ventaja se achicó más."

**Frase clave:** "El partido del presidente perdió las cinco veces."

---

### 5. El modelo

**Decir:**

> "Con esto armamos el modelo, que es una fórmula que aprende de las elecciones pasadas. Funciona
> en cuatro pasos: parte de cómo votó cada estado en 2024, le resta al partido del presidente lo
> que suele perder en un medio término, obtiene el voto de cada partido en los 50 estados y
> convierte el total en bancas.
>
> ¿Cómo sabemos que funciona? Lo pusimos a prueba con el pasado: le tapamos una elección, lo
> entrenamos con las otras cuatro y le pedimos que la adivinara. Se equivocó en promedio 3,5
> puntos por estado, y acertó qué partido sacó más votos en 92 de cada 100 casos."

**Frase clave:** "Antes de predecir el futuro, le hicimos adivinar el pasado."

**Si preguntan qué tipo de modelo es:** una regresión lineal, es decir, una fórmula que combina
los datos de la elección anterior con un peso para cada uno. Probamos también un modelo más
complejo (bosque aleatorio) y no funcionó mejor.

---

### 6. La predicción para 2026

**Cómo leer el gráfico.**

- La barra son las 435 bancas: azul = demócratas, rojo = republicanos.
- La línea punteada marca la mayoría (218).
- El corchete de abajo es el rango probable: entre 217 y 256 bancas demócratas.

**Decir:**

> "Para 2026, con presidente republicano, el modelo predice que los demócratas sacan el 54 % de
> los votos, contra 48,7 % en 2024. Eso les daría unas 236 bancas, más de las 218 que necesitan.
>
> Como toda predicción tiene error, simulamos 10.000 elecciones con los errores que tuvo el
> modelo en el pasado. En 88 de cada 100 los demócratas ganan la mayoría. O sea, es lo más
> probable, pero no es seguro."

**Si preguntan qué significa el 54 %:** es la parte demócrata de los votos que fueron a
demócratas o republicanos en todo el país: demócratas ÷ (demócratas + republicanos). Lo que falta
hasta el 100 % es republicano: 54 % demócrata = 46 % republicano.

**Frase clave:** "Mayoría demócrata en 88 de cada 100 escenarios."

---

### 7. La predicción, estado por estado

**Cómo leer el gráfico.**

- **Eje Y:** los 50 estados, ordenados por la predicción.
- **Eje X:** porcentaje de voto demócrata.
- Círculo gris = resultado 2024; punto de color = predicción 2026 (azul si pasa el 50 %, rojo si
  no). La línea entre los dos muestra cuánto se mueve el estado.

**Decir:**

> "Si miramos estado por estado, 46 de los 50 votarían más a los demócratas que en 2024. Y siete
> pasarían a votar más demócrata que republicano: Michigan, Pensilvania, Nevada, Wisconsin,
> Georgia, Arizona y Carolina del Norte. Son justamente los estados más disputados en las
> elecciones presidenciales."

**Si preguntan qué significa el porcentaje:** es la parte demócrata de los votos que fueron a
demócratas o republicanos: demócratas ÷ (demócratas + republicanos). Dejamos afuera a los demás
partidos, que sacan muy pocos votos. Como solo quedan dos partidos, lo que falta hasta el 100 % es
republicano: Michigan 53,6 % demócrata = 46,4 % republicano. Por eso, más del 50 % ya significa que
los demócratas sacan más votos.

**Frase clave:** "El cambio pasa en los estados más disputados."

**Si preguntan por qué algunos estados bajan:** Vermont y Massachusetts tenían en 2024 distritos
donde los republicanos no presentaron candidato, así que el voto demócrata estaba inflado. El
modelo espera que eso no se repita igual.

---

### 8. En resumen

**Decir:**

> "En resumen: cómo votó un estado en la presidencial anticipa bien cómo vota dos años después, y
> el partido del presidente siempre pierde en el medio término. Con esas dos ideas, el modelo
> predice una mayoría demócrata en 2026.
>
> Hay que leerlo con cuidado: no usa encuestas, tiene solo cinco elecciones para aprender y
> algunos estados cambiaron sus distritos en 2025 y 2026. El 3 de noviembre vamos a ver cuánto le
> acertamos."

---

## Preguntas que pueden aparecer

| Pregunta | Respuesta corta |
|---|---|
| ¿Por qué no usaron encuestas? | Queríamos ver cuánto se puede predecir solo con resultados oficiales. Sumar encuestas sería el próximo paso. |
| ¿Por qué desde 2006? | Antes la gente votaba más distinto para presidente y para el Congreso, y la relación era más débil. |
| ¿El modelo sabe que el presidente es Trump? | Sabe que es republicano. No usa nada de la persona. |
| ¿Qué es "3,5 puntos de error"? | En promedio, la predicción quedó a 3,5 puntos del resultado real: si un estado votó 50 % demócrata, el modelo decía algo como 46,5 % o 53,5 %. |
| ¿Dónde está el código? | `analisis_exploratorio/05_predictivo.py`. |
