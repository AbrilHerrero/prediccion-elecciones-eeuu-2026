"""Paso 5 — Validación cruzada del modelo de voto a la Cámara.

Separa la cuota D de cada estado en dos partes:
    cuota D del estado = cuota D nacional + inclinación del estado respecto del país
y modela solo la inclinación, que es estable y se puede predecir con datos previos. La cuota
nacional (el "clima nacional") se trata aparte, con escenarios, en 08_prediccion_2026.py.

Por eso todas las comparaciones de este paso usan la cuota nacional real del año evaluado:
miden cuán bien el método ubica a cada estado respecto del país.

Validación: se deja un año afuera (2018, 2020, 2022 o 2024), se entrena con los demás y se
predice ese año. Un reparto aleatorio de filas mezclaría estados del mismo año entre
entrenamiento y prueba, y daría un error más optimista que el real.

Escribe salidas/comparacion_modelos_camara.csv.
Uso:  python 05_validacion_cruzada.py
"""

# %% Carga
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from comun_modelo import (GRIS, NOMBRES_LEGIBLES, OBJETIVO_CAMARA, PREDICTORES_CAMARA,
                          SALIDAS_MODELO, TINTA, TINTA_2, VIOLETA, cargar_tabla_completa,
                          crear_modelo_camara, error_medio_en_puntos, estilo,
                          filas_de_entrenamiento, guardar, predecir_dejando_un_anio_afuera,
                          titulo)

estilo()
tabla = cargar_tabla_completa()
entrenamiento = filas_de_entrenamiento(tabla)
cuota_real = entrenamiento["house_dem_share_2p"]
cuota_nacional_real = entrenamiento["nat_house_dem_share_2p"]
estado_con_todos_los_distritos_disputados = entrenamiento["house_contested_share"] == 1
print(f"Filas de validación: {len(entrenamiento)} estado-año (2018–2024), de las cuales "
      f"{estado_con_todos_los_distritos_disputados.sum()} con todos los distritos disputados")

resultados = []


def registrar(metodo, tipo, prediccion):
    resultados.append({
        "metodo": metodo,
        "tipo": tipo,
        "error_todos_pp": error_medio_en_puntos(prediccion, cuota_real),
        "error_solo_disputados_pp": error_medio_en_puntos(
            prediccion[estado_con_todos_los_distritos_disputados],
            cuota_real[estado_con_todos_los_distritos_disputados]),
    })


# %% 1. Líneas base
titulo("1. LÍNEAS BASE (métodos ingenuos)")
cambio_nacional = cuota_nacional_real - entrenamiento["cuota_nacional_ciclo_anterior"]
registrar("Repetir el ciclo anterior", "línea base", entrenamiento["house_dem_share_2p_lag"])
registrar("Usar la última presidencial", "línea base", entrenamiento["pres_dem_share_2p_prev"])
registrar("Swing uniforme", "línea base", entrenamiento["house_dem_share_2p_lag"] + cambio_nacional)
print(pd.DataFrame(resultados).round(2).to_string(index=False))
print("Coinciden con la sección 8 de fundamentacion_dataset.md. El swing uniforme es la vara:")
print("un modelo que no lo supere no aporta.")

# %% 2. Modelos: tres algoritmos x tres conjuntos de predictores
titulo("2. MODELOS (dejando un año afuera)")
conjuntos_de_predictores = {
    "presidencial previa": ["pres_dem_share_2p_rel_prev"],
    "presidencial + Cámara anterior": ["pres_dem_share_2p_rel_prev",
                                       "house_dem_share_2p_rel_lag"],
    "presidencial + Cámara anterior + disputados": ["pres_dem_share_2p_rel_prev",
                                                    "house_dem_share_2p_rel_lag",
                                                    "distritos_disputados_ciclo_anterior"],
}
algoritmos = {
    "Regresión lineal": LinearRegression(),
    "Ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "Gradient boosting": GradientBoostingRegressor(max_depth=2, n_estimators=150,
                                                   learning_rate=0.05, random_state=0),
}
for nombre_conjunto, predictores in conjuntos_de_predictores.items():
    for nombre_algoritmo, algoritmo in algoritmos.items():
        inclinacion_prevista = predecir_dejando_un_anio_afuera(algoritmo, entrenamiento,
                                                               predictores, OBJETIVO_CAMARA)
        registrar(f"{nombre_algoritmo} · {nombre_conjunto}", "modelo",
                  cuota_nacional_real + inclinacion_prevista)

comparacion = pd.DataFrame(resultados).sort_values("error_todos_pp").reset_index(drop=True)
print(comparacion.round(2).to_string(index=False))
comparacion.round(4).to_csv(SALIDAS_MODELO / "comparacion_modelos_camara.csv", index=False)

mejor = comparacion.iloc[0]
swing_uniforme = comparacion.set_index("metodo").loc["Swing uniforme", "error_todos_pp"]
print(f"\nMenor error: {mejor['metodo']} ({mejor['error_todos_pp']:.2f} pp), "
      f"{swing_uniforme - mejor['error_todos_pp']:.2f} pp mejor que el swing uniforme.")
print("Gradient boosting no mejora: con 200 filas, un modelo flexible sobreajusta.")
print("Se elige la regresión lineal con presidencial + Cámara anterior: queda a centésimas de")
print("Ridge y sus coeficientes se leen directo. El tercer predictor no aporta.")

# %% 3. Modelo elegido: coeficientes
titulo("3. MODELO ELEGIDO: COEFICIENTES (entrenado con 2018–2024)")
modelo_camara = crear_modelo_camara().fit(entrenamiento[PREDICTORES_CAMARA],
                                          entrenamiento[OBJETIVO_CAMARA])
for predictor, coeficiente in zip(PREDICTORES_CAMARA, modelo_camara.coef_):
    print(f"  {NOMBRES_LEGIBLES[predictor]:46s} {coeficiente:+.3f}")
print(f"  {'constante':46s} {modelo_camara.intercept_:+.4f}")
print("Lectura: si un estado votó a Presidente 10 puntos más D que el país y a la Cámara 10")
print(f"puntos más D en el ciclo anterior, el modelo lo ubica "
      f"{10 * modelo_camara.coef_.sum():.1f} puntos más D que el país.")

# %% 4. Errores por año y gráficos
titulo("4. ERROR DEL MODELO ELEGIDO POR AÑO")
inclinacion_prevista = predecir_dejando_un_anio_afuera(crear_modelo_camara(), entrenamiento,
                                                       PREDICTORES_CAMARA, OBJETIVO_CAMARA)
cuota_prevista = cuota_nacional_real + inclinacion_prevista
error_por_anio = (cuota_prevista - cuota_real).abs().groupby(entrenamiento["year"]).mean() * 100
print(error_por_anio.round(2).to_string())

mayores_errores = entrenamiento.assign(prevista=cuota_prevista,
                                       error_pp=(cuota_prevista - cuota_real) * 100)
mayores_errores = mayores_errores.reindex(
    mayores_errores["error_pp"].abs().sort_values(ascending=False).index).head(8)
print("\nMayores errores (en general, estados con distritos sin oposición):")
print(mayores_errores[["year", "state", "house_dem_share_2p", "prevista", "error_pp",
                       "house_contested_share"]].round(3).to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 6))
colores = [GRIS if tipo == "línea base" else VIOLETA for tipo in comparacion["tipo"]]
posiciones = range(len(comparacion))
ax.barh(posiciones, comparacion["error_todos_pp"], color=colores, height=0.6,
        edgecolor="#fcfcfb", linewidth=1.5)
for posicion, error in zip(posiciones, comparacion["error_todos_pp"]):
    ax.text(error + 0.05, posicion, f"{error:.2f}", va="center", fontsize=8, color=TINTA_2)
ax.axvline(swing_uniforme, color=TINTA, linewidth=1, linestyle="--")
ax.set_yticks(posiciones, comparacion["metodo"], fontsize=8)
ax.invert_yaxis()
ax.grid(axis="y", visible=False)
ax.set_xlabel("Error absoluto medio en la cuota D por estado (puntos porcentuales)")
ax.plot([], [], color=GRIS, linewidth=6, label="línea base")
ax.plot([], [], color=VIOLETA, linewidth=6, label="modelo")
ax.set_xlim(0, 5.3)
ax.legend(loc="upper right", fontsize=8)
ax.set_title("Error por método, dejando un año afuera (línea: swing uniforme)")
guardar(fig, "05_1_error_por_metodo")

fig, ax = plt.subplots(figsize=(6.5, 6.5))
con_oposicion = estado_con_todos_los_distritos_disputados
ax.scatter(cuota_prevista[~con_oposicion], cuota_real[~con_oposicion], s=36, facecolors="none",
           edgecolors=GRIS, linewidths=1.2, label="con distritos sin oposición")
ax.scatter(cuota_prevista[con_oposicion], cuota_real[con_oposicion], s=36, color=VIOLETA,
           edgecolors="#fcfcfb", linewidths=0.8, label="todos disputados")
ax.plot([0, 1], [0, 1], color=TINTA_2, linewidth=1, linestyle="--")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_aspect("equal")
ax.set_xlabel("Cuota D prevista (año dejado afuera)")
ax.set_ylabel("Cuota D real")
ax.legend(loc="upper left", fontsize=8)
ax.set_title("Modelo elegido: previsto vs real (2018–2024)")
guardar(fig, "05_2_previsto_vs_real")
