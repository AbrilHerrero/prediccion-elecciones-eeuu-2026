"""Paso 6 — De votos a bancas en la Cámara.

Ajusta una curva votos-bancas (Gelman & King, 1994) con una regresión logística sobre bancas
individuales: la probabilidad de que una banca del estado la gane un demócrata, según
    - la ventaja D en votos del estado (cuota D − 0,5), y
    - la proporción de bancas D que tuvo el estado en el ciclo anterior, que resume cómo
      está dibujado su mapa de distritos.

Se valida dejando un año afuera, de dos maneras:
    A. con la cuota D real de cada estado: mide solo el error de la curva;
    B. con la cuota D prevista en el paso 5: mide el error de la cadena completa
       (votos + bancas), con el clima nacional real del año.

Escribe salidas/validacion_bancas_camara.csv, que usa 08_prediccion_2026.py.
Uso:  python 06_curva_votos_bancas.py
"""

# %% Carga
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comun_modelo import (ANIOS_CON_CICLO_ANTERIOR, AZUL_D, GRIS, OBJETIVO_CAMARA,
                          PREDICTORES_BANCAS, PREDICTORES_CAMARA, ROJO_R, SALIDAS_MODELO, TINTA,
                          TINTA_2, VIOLETA, ajustar_curva_votos_bancas, bancas_d_esperadas,
                          cargar_tabla_completa, crear_modelo_camara, estilo,
                          filas_de_entrenamiento, guardar, predecir_dejando_un_anio_afuera,
                          titulo)

estilo()
tabla = cargar_tabla_completa()
entrenamiento = filas_de_entrenamiento(tabla)
inclinacion_prevista = predecir_dejando_un_anio_afuera(crear_modelo_camara(), entrenamiento,
                                                       PREDICTORES_CAMARA, OBJETIVO_CAMARA)
cuota_prevista_paso_5 = entrenamiento["nat_house_dem_share_2p"] + inclinacion_prevista

# %% 1. Validación dejando un año afuera
titulo("1. BANCAS D NACIONALES: PREVISTAS vs REALES (dejando un año afuera)")
curvas_a_comparar = {
    "solo votos": ["ventaja_democrata_en_votos"],
    "votos + bancas anteriores": PREDICTORES_BANCAS,
}
filas_por_anio = []
for anio_afuera in ANIOS_CON_CICLO_ANTERIOR:
    anios_para_entrenar = entrenamiento[entrenamiento["year"] != anio_afuera]
    anio_a_predecir = entrenamiento[entrenamiento["year"] == anio_afuera]
    fila = {"year": anio_afuera, "bancas_d_reales": int(anio_a_predecir["house_seats_d"].sum())}
    for nombre_curva, predictores in curvas_a_comparar.items():
        curva = ajustar_curva_votos_bancas(anios_para_entrenar, predictores)
        fila[f"A_{nombre_curva}"] = bancas_d_esperadas(
            curva, anio_a_predecir["house_dem_share_2p"], anio_a_predecir, predictores).sum()
    curva_elegida = ajustar_curva_votos_bancas(anios_para_entrenar)
    fila["B_cadena_completa"] = bancas_d_esperadas(
        curva_elegida, cuota_prevista_paso_5[anio_a_predecir.index], anio_a_predecir).sum()
    filas_por_anio.append(fila)

validacion = pd.DataFrame(filas_por_anio)
columnas_previstas = [c for c in validacion.columns if c.startswith(("A_", "B_"))]
print(validacion.round(1).to_string(index=False))
print("\nError absoluto medio en bancas D nacionales:")
errores = {c: (validacion[c] - validacion["bancas_d_reales"]).abs().mean()
           for c in columnas_previstas}
for columna, error in errores.items():
    print(f"  {columna:32s} {error:5.1f} bancas")
validacion.round(2).to_csv(SALIDAS_MODELO / "validacion_bancas_camara.csv", index=False)

print("\nLectura: agregar las bancas del ciclo anterior mejora la curva, porque cada estado")
print("tiene su propio mapa. Aun así, el error nacional ronda ±10–15 bancas: es la")
print("incertidumbre de pasar de votos por estado a bancas sin datos por distrito. Los mapas")
print("redibujados para 2026 no están en los datos, así que en esos estados el error puede ser mayor.")

# %% 2. Curva final y gráfico
titulo("2. CURVA FINAL (entrenada con 2018–2024)")
curva_final = ajustar_curva_votos_bancas(entrenamiento)
for predictor, coeficiente in zip(PREDICTORES_BANCAS, curva_final.coef_[0]):
    print(f"  {predictor:34s} {coeficiente:+.2f}")
print(f"  {'constante':34s} {curva_final.intercept_[0]:+.2f}")

curva_solo_votos = ajustar_curva_votos_bancas(entrenamiento, ["ventaja_democrata_en_votos"])
cuotas_para_dibujar = np.linspace(0.2, 0.8, 200)
probabilidad_dibujada = curva_solo_votos.predict_proba(
    pd.DataFrame({"ventaja_democrata_en_votos": cuotas_para_dibujar - 0.5}))[:, 1]

fig, ax = plt.subplots(figsize=(7.5, 6))
ax.scatter(entrenamiento["house_dem_share_2p"], entrenamiento["house_seat_share_d"],
           s=entrenamiento["house_seats"] * 6, color=VIOLETA, alpha=0.35, edgecolors="#fcfcfb",
           linewidths=0.6, label="estado-año (tamaño = bancas)")
ax.plot(cuotas_para_dibujar, probabilidad_dibujada, color=TINTA, linewidth=2,
        label="curva promedio (solo votos)")
ax.axvline(0.5, color=GRIS, linewidth=1, linestyle="--")
ax.axhline(0.5, color=GRIS, linewidth=1, linestyle="--")
ax.axvspan(0, 0.5, color=ROJO_R, alpha=0.04)
ax.axvspan(0.5, 1, color=AZUL_D, alpha=0.04)
ax.set_xlim(0.15, 0.85)
ax.set_ylim(-0.03, 1.03)
ax.set_xlabel("Cuota D del voto bipartidista a la Cámara")
ax.set_ylabel("Proporción de bancas D del estado")
ax.legend(loc="lower right", fontsize=8)
ax.set_title("Curva votos-bancas por estado (2018–2024)")
ax.text(0.16, 0.9, "La dispersión vertical refleja el mapa de cada estado:\n"
        "por eso el modelo suma las bancas del ciclo anterior", fontsize=8, color=TINTA_2)
guardar(fig, "06_1_curva_votos_bancas")
