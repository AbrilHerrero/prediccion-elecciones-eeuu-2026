"""Paso 3 — Análisis descriptivo (Módulo II, nivel 1: ¿qué pasó?).

Resume las variables principales con media, mediana y desviación estándar, las compara por
partido del presidente y muestra los indicadores nacionales de cada ciclo: bancas y cuota
demócrata a la Cámara antes (presidencial) y después (medio término).
Escribe salidas/descriptivo_variables.csv, salidas/descriptivo_por_partido.csv y
salidas/indicadores_nacionales.csv.

Requiere haber ejecutado 02_preprocesamiento.py.
Uso:  ../.venv/bin/python 03_descriptivo.py
"""

# %% Carga
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from comun import (AZUL_D, ETIQUETAS, GRIS, ROJO_R, SALIDAS, TINTA, TINTA_2,
                   cargar_preprocesado, estilo, guardar, titulo)

estilo()
df = cargar_preprocesado()

# %% 1. Media, mediana y desvío
titulo("1. MEDIA, MEDIANA Y DESVÍO ESTÁNDAR (filas estado x medio término, 2006–2022)")
variables = ["house_dem_share_2p", "pres_dem_share_2p_prev", "house_dem_share_2p_prev",
             "house_primary_dem_share_2p", "senate_dem_share_2p", "house_seat_share_d",
             "house_contested_share", "house_dem_swing", "president_party_swing",
             "house_dropoff_prev"]
resumen = df[variables].agg(["count", "mean", "median", "std", "min", "max"]).T
resumen["media - mediana"] = resumen["mean"] - resumen["median"]
resumen.index = [ETIQUETAS[v] for v in resumen.index]
print(resumen.round(3).to_string())
resumen.round(4).to_csv(SALIDAS / "descriptivo_variables.csv")

cuota, bancas = df["house_dem_share_2p"], df["house_seat_share_d"]
swing_pp = df["president_party_swing"]
print("\nLectura (media ≈ mediana -> simétrica; si difieren -> asimetría o atípicos):")
print(f" - Cuota D Cámara: media {cuota.mean():.3f} ≈ mediana {cuota.median():.3f} -> simétrica,")
print(f"   con desvío {cuota.std():.3f}: los estados son muy heterogéneos entre sí.")
print(f" - Proporción de bancas D: media {bancas.mean():.3f} vs mediana {bancas.median():.3f} ->")
print("   asimétrica: muchos estados chicos con todas sus bancas R. El sistema mayoritario por")
print("   distrito amplifica las diferencias de votos al convertirlas en bancas.")
print(f" - Swing del partido del presidente: media {swing_pp.mean():+.3f}, mediana "
      f"{swing_pp.median():+.3f}; negativo en {(swing_pp < 0).mean():.0%} de los casos.")

# %% 2. Por partido del presidente
titulo("2. POR PARTIDO DEL PRESIDENTE")
por_partido = df.groupby("pres_party")[["house_dem_share_2p", "house_dem_swing",
                                        "president_party_swing"]].agg(["mean", "median", "std"])
print(por_partido.round(3).to_string())
por_partido.round(4).to_csv(SALIDAS / "descriptivo_por_partido.csv")
print("\nCon presidente R el swing D es positivo; con presidente D, negativo: en los dos casos")
print("pierde el partido del presidente (president_party_swing < 0).")

# %% 3. Indicadores nacionales por ciclo
titulo("3. INDICADORES NACIONALES POR CICLO (presidencial anterior -> medio término)")
nacional = df.groupby("year").agg(
    presidente=("pres_party", "first"),
    bancas_d_antes=("house_seats_d_prev", "sum"),
    bancas_d_despues=("house_seats_d", "sum"),
    bancas_r_antes=("house_seats_r_prev", "sum"),
    bancas_r_despues=("house_seats_r", "sum"),
    cuota_d_antes=("nat_house_dem_share_2p_prev", "first"),
    cuota_d_despues=("nat_house_dem_share_2p", "first"),
)
signo = nacional["presidente"].map({"D": 1, "R": -1})
nacional["swing_nacional_partido_pres"] = signo * (nacional["cuota_d_despues"] - nacional["cuota_d_antes"])
es_d = nacional["presidente"] == "D"
nacional["bancas_perdidas_partido_pres"] = (
    nacional["bancas_d_antes"] - nacional["bancas_d_despues"]).where(
    es_d, nacional["bancas_r_antes"] - nacional["bancas_r_despues"])
print(nacional.round(3).to_string())
nacional.round(4).to_csv(SALIDAS / "indicadores_nacionales.csv")
print("\n2004: Sanders (VT) era independiente. 2018: NC-09 anulada y repetida en 2019. Mayoría = 218.")

# Figura: bancas antes y después de cada medio término (barras apiladas con línea de mayoría)
fig, ax = plt.subplots(figsize=(10, 4.8))
ancho = 0.36
for i, (anio, fila) in enumerate(nacional.iterrows()):
    for desplazamiento, d, r, rotulo in ((-ancho / 2 - 0.02, fila["bancas_d_antes"], fila["bancas_r_antes"], str(anio - 2)),
                                         (ancho / 2 + 0.02, fila["bancas_d_despues"], fila["bancas_r_despues"], str(anio))):
        x = i + desplazamiento
        ax.bar(x, d, width=ancho, color=AZUL_D, edgecolor="#fcfcfb", linewidth=1.5)
        ax.bar(x, r, width=ancho, bottom=d, color=ROJO_R, edgecolor="#fcfcfb", linewidth=1.5)
        ax.text(x, d / 2, str(int(d)), ha="center", va="center", color="white", fontsize=8, weight="bold")
        ax.text(x, d + r / 2, str(int(r)), ha="center", va="center", color="white", fontsize=8, weight="bold")
        ax.text(x, -14, rotulo, ha="center", va="top", fontsize=8, color=TINTA_2)
ax.axhline(218, color=TINTA, linewidth=1, linestyle="--")
ax.text(-0.62, 218, "mayoría\n(218)", fontsize=8, color=TINTA_2, ha="right", va="center")
ax.set_xlim(-1.05, len(nacional) - 0.5)
ax.set_xticks(range(len(nacional)),
              [f"\n\npres. {p}: pierde {int(b)}" for p, b in
               zip(nacional["presidente"], nacional["bancas_perdidas_partido_pres"])], fontsize=8)
ax.tick_params(axis="x", length=0)
ax.set_ylabel("Bancas")
ax.set_ylim(0, 450)
ax.grid(axis="x", visible=False)
ax.legend(handles=[Patch(color=AZUL_D, label="Demócratas"), Patch(color=ROJO_R, label="Republicanos")],
          loc="upper left", ncol=2, bbox_to_anchor=(0, 1.12))
ax.set_title("Bancas de la Cámara: presidencial anterior vs medio término", pad=28)
guardar(fig, "03_1_bancas_antes_despues")

# Figura: cuota D nacional antes y después de cada medio término
fig, ax = plt.subplots(figsize=(9, 4.4))
for anio, fila in nacional.iterrows():
    color = AZUL_D if fila["presidente"] == "D" else ROJO_R
    ax.plot([anio - 2, anio], [fila["cuota_d_antes"], fila["cuota_d_despues"]], color=color,
            linewidth=2.5, marker="o", markersize=7)
    ax.annotate(f"{(fila['cuota_d_despues'] - fila['cuota_d_antes']) * 100:+.1f} pp",
                (anio - 1, (fila["cuota_d_antes"] + fila["cuota_d_despues"]) / 2), xytext=(6, 0),
                textcoords="offset points", fontsize=9, color=TINTA, weight="bold", va="center")
ax.axhline(0.5, color=GRIS, linewidth=1)
ax.set_xticks(sorted({a for a in nacional.index} | {a - 2 for a in nacional.index}))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_ylabel("Cuota demócrata bipartidista (nacional)")
ax.plot([], [], color=ROJO_R, linewidth=2.5, label="presidente R")
ax.plot([], [], color=AZUL_D, linewidth=2.5, label="presidente D")
ax.legend(loc="lower left", fontsize=8)
ax.set_title("Voto D nacional a la Cámara: de la presidencial al medio término")
guardar(fig, "03_2_cuota_nacional")
