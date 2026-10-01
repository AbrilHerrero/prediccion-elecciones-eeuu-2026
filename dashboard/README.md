# Dashboard de la predicción 2026

Una API con FastAPI y una página estática (HTML, CSS y JavaScript sin librerías) que la
consume. El usuario elige el clima nacional con un deslizador o con los cuatro escenarios, y
la página recalcula la Cámara y el Senado con los modelos de [`../modelo/`](../modelo/).

## Cómo correrlo

```bash
pip install -r ../requirements.txt     # solo la primera vez
python ../modelo/ejecutar_todo.py      # genera las salidas de validación que lee la API
python app.py                          # y abrir http://127.0.0.1:8000
```

## Qué muestra

- **Clima nacional:** deslizador de −4 a +10 puntos y los cuatro escenarios de `08_prediccion_2026.py`.
- **Indicadores:** bancas D esperadas en la Cámara (con el rango del error histórico) y en el
  Senado, y la probabilidad de control D del Senado.
- **Bancas según el clima:** cómo cambia cada cámara en todo el rango. Al hacer clic sobre el
  gráfico se elige ese clima.
- **Mapa de mosaicos:** cuota D prevista a la Cámara o probabilidad de victoria D en el Senado,
  por estado. Los estados con mapa de distritos nuevo en 2026 tienen borde grueso.
- **Las 35 elecciones al Senado**, ordenadas por probabilidad.
- **Tabla por estado**, ordenable, con todos los valores.
- **Validación:** error por método y bancas previstas vs reales, 2018–2024.

## API

| Ruta | Devuelve |
|---|---|
| `GET /api/contexto` | Escenarios, mayorías, antecedentes de medio término y tablas de validación |
| `GET /api/prediccion?ganancia_democrata_pp=4` | Resumen nacional y tabla por estado para ese clima |
| `GET /api/barrido` | Resumen nacional para cada clima entre −4 y +10, cada medio punto |

FastAPI también genera la documentación interactiva en `/docs`.

| Archivo | Qué contiene |
|---|---|
| `app.py` | La API: entrena los modelos al arrancar y responde con la lógica de `../modelo/motor_de_prediccion.py` |
| `static/index.html` | Estructura de la página |
| `static/estilo.css` | Paleta (la misma de los gráficos del análisis), modo claro y oscuro |
| `static/tablero.js` | Pide los datos y dibuja controles, gráficos, mapa y tablas |
