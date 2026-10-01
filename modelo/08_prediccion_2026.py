"""Paso 8 — Predicción de las elecciones del 3 de noviembre de 2026.

Entrena los modelos de los pasos 5–7 con todos los datos 2018–2024 y los aplica a las filas
2026. El clima nacional no se puede estimar con estos datos (solo hay dos elecciones de medio
término, 2018 y 2022), así que se plantean escenarios de cuánto gana la oposición (los
demócratas, porque el presidente es republicano) respecto de 2024:

    sin efecto de medio término      +0 puntos
    efecto moderado                  +2 puntos
    promedio de 2018 y 2022          lo que perdió en promedio el partido del presidente
    ola demócrata                    +6 puntos

Para cada escenario:
    Cámara: cuota D por estado -> bancas D esperadas (curva del paso 6), con el error
            histórico de la cadena completa como margen.
    Senado: cuota D en las 35 elecciones -> probabilidad de victoria D por estado y de control
            del Senado, simulando el error por estado medido en el paso 7.

La lógica de predicción está en motor_de_prediccion.py (la comparte el dashboard).
Requiere haber ejecutado 06 y 07 (lee sus salidas).
Escribe salidas/prediccion_2026_por_estado.csv y salidas/resumen_nacional_2026.csv.
Uso:  python 08_prediccion_2026.py
"""

# %% Carga
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comun_modelo import (AZUL_D, BANCAS_PARA_MAYORIA_CAMARA, BANCAS_PARA_MAYORIA_SENADO, GRIS,
                          GRIS_NEUTRO, ROJO_R, SALIDAS_MODELO, TINTA, TINTA_2, VIOLETA, estilo,
                          guardar, titulo)
from motor_de_prediccion import (ESCENARIO_CENTRAL, entrenar_modelos_para_2026,
                                 escenarios_de_clima_nacional, predecir_con_clima_nacional)

estilo()
modelos_2026 = entrenar_modelos_para_2026()
error_historico_en_bancas = modelos_2026["error_historico_en_bancas"]

# %% 1. Clima nacional: lo que muestran 2018 y 2022
titulo("1. CLIMA NACIONAL: ESCENARIOS")
print("Cambio nacional del partido del presidente en elecciones de medio término:")
print((modelos_2026["perdidas_del_presidente_en_medio_termino"] * 100).round(2).to_string())
ganancia_democrata_por_escenario = escenarios_de_clima_nacional(modelos_2026)
for escenario, ganancia in ganancia_democrata_por_escenario.items():
    print(f"  {escenario:30s} +{ganancia * 100:.1f} pp  -> cuota D nacional "
          f"{(modelos_2026['cuota_nacional_2024'] + ganancia):.1%}")

# %% 2. Inclinación de cada estado en 2026
titulo("2. INCLINACIÓN DE CADA ESTADO EN 2026 (modelo del paso 5)")
print(f"Corrección de centrado: {modelos_2026['correccion_de_centrado'] * 100:+.2f} pp")
print("(la cuota nacional es el promedio ponderado de los estados; se centra con los votos 2024)")

# %% 3. Escenarios
titulo("3. RESULTADO POR ESCENARIO")
filas_resumen = []
tablas_por_estado = []
for escenario, ganancia in ganancia_democrata_por_escenario.items():
    resumen_del_escenario, por_estado_del_escenario = predecir_con_clima_nacional(modelos_2026,
                                                                                 ganancia)
    filas_resumen.append({"escenario": escenario, **resumen_del_escenario})
    tablas_por_estado.append(por_estado_del_escenario.reset_index().assign(escenario=escenario))

resumen = pd.DataFrame(filas_resumen)
por_estado = pd.concat(tablas_por_estado, ignore_index=True)
resumen.round(4).to_csv(SALIDAS_MODELO / "resumen_nacional_2026.csv", index=False)
por_estado.round(4).to_csv(SALIDAS_MODELO / "prediccion_2026_por_estado.csv", index=False)

for _, fila in resumen.iterrows():
    print(f"\n{fila['escenario']}  (cuota D nacional {fila['cuota_d_nacional']:.1%})")
    print(f"  Cámara: {fila['camara_bancas_d_esperadas']:.0f} bancas D esperadas "
          f"(rango histórico {fila['camara_rango_inferior']:.0f}–"
          f"{fila['camara_rango_superior']:.0f}; mayoría = {BANCAS_PARA_MAYORIA_CAMARA})")
    print(f"  Senado: {fila['senado_bancas_d_esperadas']:.1f} bancas D esperadas; "
          f"probabilidad de control D {fila['senado_probabilidad_control_d']:.0%}")

# %% 4. Detalle del escenario central
titulo(f"4. DETALLE DEL ESCENARIO CENTRAL: {ESCENARIO_CENTRAL}")
central = por_estado[por_estado["escenario"] == ESCENARIO_CENTRAL].set_index("state")
competitivos = central[central["camara_cuota_d_prevista"].between(0.45, 0.55)]
print("Estados competitivos en la Cámara (cuota D prevista entre 45 % y 55 %):")
print(competitivos[["house_seats", "camara_cuota_d_prevista", "camara_bancas_d_esperadas",
                    "mapa_nuevo_2026"]].sort_values("camara_cuota_d_prevista").round(3)
      .to_string())

senado_central = central.dropna(subset=["senado_cuota_d_prevista"]).sort_values(
    "senado_cuota_d_prevista")
print("\nSenado, las 35 elecciones de 2026 (de más R a más D):")
print(senado_central[["senado_cuota_d_prevista", "senado_probabilidad_victoria_d"]].round(3)
      .to_string())
print("\nAtención: en Nebraska compite un independiente (Osborn) sin candidato D; la cuota")
print("prevista corresponde a un D genérico y no representa esa elección.")

# %% 5. Gráficos
fig, (eje_camara, eje_senado) = plt.subplots(1, 2, figsize=(12, 4.8))
posiciones = np.arange(len(resumen))
etiquetas = [e.replace(" de ", "\nde ").replace(" demócrata", "\ndemócrata")
             for e in resumen["escenario"]]
colores = [VIOLETA if e == ESCENARIO_CENTRAL else GRIS for e in resumen["escenario"]]

eje_camara.bar(posiciones, resumen["camara_bancas_d_esperadas"], color=colores, width=0.6,
               yerr=error_historico_en_bancas, ecolor=TINTA_2, capsize=4)
eje_camara.axhline(BANCAS_PARA_MAYORIA_CAMARA, color=TINTA, linewidth=1, linestyle="--")
eje_camara.text(-0.45, BANCAS_PARA_MAYORIA_CAMARA + 3, "mayoría: 218", fontsize=8, color=TINTA)
for posicion, bancas in zip(posiciones, resumen["camara_bancas_d_esperadas"]):
    eje_camara.text(posicion, 150, f"{bancas:.0f}", ha="center", fontsize=10, color="white",
                    weight="bold")
eje_camara.set_ylim(140, 280)
eje_camara.set_xticks(posiciones, etiquetas, fontsize=8)
eje_camara.set_ylabel("Bancas D esperadas")
eje_camara.set_title("Cámara (barra de error: error histórico)")

eje_senado.bar(posiciones, resumen["senado_bancas_d_esperadas"], color=colores, width=0.6)
eje_senado.axhline(BANCAS_PARA_MAYORIA_SENADO, color=TINTA, linewidth=1, linestyle="--")
eje_senado.text(-0.45, BANCAS_PARA_MAYORIA_SENADO + 0.3, "mayoría D: 51", fontsize=8,
                color=TINTA)
for posicion, fila in zip(posiciones, resumen.itertuples()):
    eje_senado.text(posicion, 41, f"{fila.senado_bancas_d_esperadas:.1f}", ha="center",
                    fontsize=10, color="white", weight="bold")
    eje_senado.text(posicion, fila.senado_bancas_d_esperadas + 0.3,
                    f"control D: {fila.senado_probabilidad_control_d:.0%}", ha="center",
                    fontsize=8, color=TINTA)
eje_senado.set_ylim(40, 56)
eje_senado.set_xticks(posiciones, etiquetas, fontsize=8)
eje_senado.set_ylabel("Bancas D esperadas (incluye las que no renuevan)")
eje_senado.set_title("Senado")
fig.suptitle("Predicción 2026 según el clima nacional", fontsize=13, weight="bold",
             color=TINTA)
fig.tight_layout()
guardar(fig, "08_1_bancas_por_escenario")

ordenados = central.sort_values("camara_cuota_d_prevista")
fig, ax = plt.subplots(figsize=(7, 12))
posiciones_estados = np.arange(len(ordenados))
ax.axvspan(0.48, 0.52, color=GRIS_NEUTRO, zorder=0)
ax.axvline(0.5, color=TINTA_2, linewidth=1, linestyle="--")
color_por_partido = np.where(ordenados["camara_cuota_d_prevista"] >= 0.5, AZUL_D, ROJO_R)
con_mapa_nuevo = ordenados["mapa_nuevo_2026"].to_numpy()
ax.scatter(ordenados["camara_cuota_d_prevista"][~con_mapa_nuevo],
           posiciones_estados[~con_mapa_nuevo], color=color_por_partido[~con_mapa_nuevo], s=40)
ax.scatter(ordenados["camara_cuota_d_prevista"][con_mapa_nuevo],
           posiciones_estados[con_mapa_nuevo], facecolors="none",
           edgecolors=color_por_partido[con_mapa_nuevo], s=60, linewidths=1.8,
           label="mapa de distritos nuevo en 2026")
ax.set_yticks(posiciones_estados, ordenados.index, fontsize=8)
ax.set_ylim(-1, len(ordenados))
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_xlabel("Cuota D prevista a la Cámara (franja gris: 48 %–52 %)")
ax.legend(loc="lower right", fontsize=8)
ax.set_title(f"Cuota D prevista por estado, 2026\nescenario: {ESCENARIO_CENTRAL}")
guardar(fig, "08_2_cuota_prevista_por_estado")
