"""Paso 3 — Análisis descriptivo (Módulo II, nivel 1: ¿qué pasó?).

Resume las variables principales con media, mediana y desviación estándar, y muestra los
indicadores nacionales por año: bancas por partido y cuota demócrata a la Cámara y a Presidente.
Escribe salidas/descriptivo_variables.csv y salidas/descriptivo_por_ciclo.csv.

Requiere haber ejecutado 02_preprocesamiento.py.
Uso:  ../.venv/bin/python 03_descriptivo.py
"""

# %% Carga
import matplotlib.pyplot as plt

from comun import (AZUL_D, ETIQUETAS, GRIS, ROJO_R, SALIDAS, TINTA, TINTA_2, VIOLETA,
                   cargar_preprocesado, estilo, guardar, titulo)

estilo()
df = cargar_preprocesado()

# %% 1. Media, mediana y desvío
titulo("1. MEDIA, MEDIANA Y DESVÍO ESTÁNDAR (filas estado x año, 2016–2024)")
variables = ["house_dem_share_2p", "pres_dem_share_2p", "senate_dem_share_2p",
             "house_primary_dem_share_2p", "house_seat_share_d", "house_contested_share",
             "house_dem_swing", "house_dropoff"]
resumen = df[variables].agg(["count", "mean", "median", "std", "min", "max"]).T
resumen["media - mediana"] = resumen["mean"] - resumen["median"]
resumen.index = [ETIQUETAS[v] for v in resumen.index]
print(resumen.round(3).to_string())
resumen.round(4).to_csv(SALIDAS / "descriptivo_variables.csv")

cuota = df["house_dem_share_2p"]
bancas = df["house_seat_share_d"]
print("\nLectura (media ≈ mediana -> simétrica; si difieren -> asimetría o atípicos):")
print(f" - Cuota D Cámara: media {cuota.mean():.3f} ≈ mediana {cuota.median():.3f} -> simétrica,")
print(f"   con desvío {cuota.std():.3f}: los estados son muy heterogéneos entre sí.")
print(f" - Proporción de bancas D: media {bancas.mean():.3f} vs mediana {bancas.median():.3f} ->")
print("   asimétrica: muchos estados chicos con todas sus bancas R y pocos estados grandes D.")
print("   El paso de votos a bancas amplifica las diferencias (sistema mayoritario por distrito).")


# %% 2. Por tipo de ciclo
titulo("2. POR TIPO DE CICLO")
por_ciclo = df.groupby("tipo_ciclo")[["house_dem_share_2p", "house_dem_swing",
                                      "swing_partido_presidente"]].agg(["mean", "median", "std"])
print(por_ciclo.round(3).to_string())
por_ciclo.round(4).to_csv(SALIDAS / "descriptivo_por_ciclo.csv")

# %% 3. Indicadores nacionales por año
titulo("3. INDICADORES NACIONALES POR AÑO")
nacional = df.groupby("year").agg(
    presidente=("pres_party", "first"),
    ciclo=("tipo_ciclo", "first"),
    bancas_d=("house_seats_d", "sum"),
    bancas_r=("house_seats_r", "sum"),
    cuota_d_camara=("nat_house_dem_share_2p", "first"),
    cuota_d_presidente=("nat_pres_dem_share_2p", "first"),
)
nacional[["bancas_d", "bancas_r"]] = nacional[["bancas_d", "bancas_r"]].astype(int)
print(nacional.round(3).to_string())
print("\n2018: 434 bancas asignadas (NC-09 anulada y repetida en 2019). Mayoría = 218.")

# Figura: bancas por partido y año (barras apiladas con línea de mayoría)
fig, ax = plt.subplots(figsize=(8, 4.5))
x = range(len(nacional))
ax.bar(x, nacional["bancas_d"], width=0.6, color=AZUL_D, label="Demócratas",
       edgecolor="#fcfcfb", linewidth=2)
ax.bar(x, nacional["bancas_r"], width=0.6, bottom=nacional["bancas_d"], color=ROJO_R,
       label="Republicanos", edgecolor="#fcfcfb", linewidth=2)
for i, (d, r) in enumerate(zip(nacional["bancas_d"], nacional["bancas_r"])):
    ax.text(i, d / 2, str(d), ha="center", va="center", color="white", fontsize=10, weight="bold")
    ax.text(i, d + r / 2, str(r), ha="center", va="center", color="white", fontsize=10, weight="bold")
ax.axhline(218, color=TINTA, linewidth=1, linestyle="--")
ax.text(-0.45, 223, "mayoría\n(218)", fontsize=8, color=TINTA_2, ha="right", va="bottom")
ax.set_xlim(-0.9, len(nacional) - 0.5)
etiquetas_x = [f"{a}\n{'medio término' if c == 'medio término' else 'presidencial'}\npres. {p}"
               for a, c, p in zip(nacional.index, nacional["ciclo"], nacional["presidente"])]
ax.set_xticks(list(x), etiquetas_x, fontsize=8)
ax.set_ylabel("Bancas")
ax.set_ylim(0, 450)
ax.grid(axis="x", visible=False)
ax.legend(loc="upper left", ncol=2, bbox_to_anchor=(0, 1.1))
ax.set_title("Bancas de la Cámara por partido", pad=24)
guardar(fig, "03_1_bancas_por_anio")

# Figura: cuota D nacional Cámara vs Presidente
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(nacional.index, nacional["cuota_d_camara"], color=VIOLETA, linewidth=2, marker="o",
        markersize=8, label="Cámara")
pres = nacional["cuota_d_presidente"].dropna()
ax.plot(pres.index, pres, color=GRIS, linewidth=2, marker="s", markersize=8, linestyle="--",
        label="Presidente")
for a, v in nacional["cuota_d_camara"].items():
    ax.annotate(f"{v:.1%}", (a, v), xytext=(0, 9), textcoords="offset points", ha="center",
                fontsize=8, color=TINTA_2)
ax.axhline(0.5, color=GRIS, linewidth=1)
ax.axvspan(2017, 2019, color="#ecebf7", zorder=0)
ax.axvspan(2021, 2023, color="#ecebf7", zorder=0)
ax.text(2018, 0.475, "medio\ntérmino", ha="center", fontsize=8, color=VIOLETA)
ax.text(2022, 0.475, "medio\ntérmino", ha="center", fontsize=8, color=VIOLETA)
ax.set_xticks(nacional.index)
ax.set_ylim(0.47, 0.56)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_ylabel("Cuota demócrata bipartidista (nacional)")
ax.legend(loc="upper right")
ax.set_title("Voto demócrata nacional: Cámara vs Presidente")
guardar(fig, "03_2_cuota_nacional")
