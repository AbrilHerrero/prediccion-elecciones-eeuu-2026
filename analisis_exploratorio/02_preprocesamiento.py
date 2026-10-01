"""Paso 2 — Preprocesamiento (Módulo I: limpieza, integración, reducción y discretización).

Audita la calidad del dataset y genera salidas/dataset_preprocesado.csv con las filas
2016–2024, las variables elegidas para el análisis y tres columnas nuevas:
    todos_disputados          1 si todos los distritos del estado tuvieron candidato D y R
    swing_partido_presidente  cambio en la cuota del partido del presidente vs el ciclo anterior
    categoria_camara          discretización ordinal de la cuota D a la Cámara

Uso:  ../.venv/bin/python 02_preprocesamiento.py
"""

# %% Carga
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comun import GRIS, PREPROCESADO, TINTA_2, VIOLETA, cargar_dataset, estilo, guardar, titulo

estilo()
df = cargar_dataset()
train = df[df["split"] == "train"].copy()

# %% 1.1 Datos faltantes
titulo("1.1 DATOS FALTANTES")
faltantes = train.isna().sum()
faltantes = faltantes[faltantes > 0].sort_values(ascending=False)
print("Celdas vacías por columna (filas 2016–2024):")
print(faltantes.to_string())

# Faltante estructural = el dato no existe (no hubo esa elección). Faltante real = existe pero
# no está en las fuentes.
estructurales = {
    "pres_*": "no hay elección presidencial en años de medio término (2018, 2022)",
    "senate_*": "el estado no eligió senador ese año (1/3 del Senado por ciclo)",
    "*_lag, *_prev, house_dem_swing": "2016 es el primer año del panel (2014 no está incluido)",
}
reales = {
    "house_primary_*": "internas 2024: el Clerk no las publica; y estados sin internas disputadas",
}
print("\nFaltantes ESTRUCTURALES (no imputar: inventaría elecciones que no ocurrieron):")
for k, v in estructurales.items():
    print(f"  {k:32s} {v}")
print("Faltantes REALES:")
for k, v in reales.items():
    print(f"  {k:32s} {v}")
print("\nDecisión: sin imputación. Cada correlación usa los pares de filas con dato en ambas")
print("variables (eliminación por pares), que conserva la mayor muestra posible por análisis.")

# Mapa de faltantes: % de celdas vacías por columna y año
cols_mapa = faltantes.index.tolist()
mapa = train.groupby("year")[cols_mapa].apply(lambda g: g.isna().mean() * 100).T
fig, ax = plt.subplots(figsize=(7, 0.32 * len(cols_mapa) + 1.2))
im = ax.imshow(mapa.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(len(mapa.columns)), mapa.columns)
ax.set_yticks(range(len(mapa.index)), mapa.index, fontsize=8)
ax.grid(False)
for i in range(mapa.shape[0]):
    for j in range(mapa.shape[1]):
        v = mapa.values[i, j]
        if v > 0:
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7,
                    color="white" if v > 60 else TINTA_2)
fig.colorbar(im, ax=ax, label="% de estados sin dato", shrink=0.6)
ax.set_title("Datos faltantes por columna y año")
guardar(fig, "02_1_mapa_faltantes")

# %% 1.2 Columnas irrelevantes y redundantes
titulo("1.2 COLUMNAS IRRELEVANTES Y REDUNDANTES")
r_margen = train[["house_dem_share_2p", "house_margin_d"]].corr().iloc[0, 1]
print(f"house_margin_d vs house_dem_share_2p: r = {r_margen:.3f}  -> redundante, se usa la cuota")
print("house_seats_r = house_seats - house_seats_d (salvo NC-09 2018)  -> redundante")
print("state_name repite a state  -> redundante")
print("state, split  -> identificadores/metadatos: no son predictores")
print("\nEscalas: los votos absolutos dependen de la población (CA ~15 M vs WY ~0,27 M).")
print("Para comparar estados se usan proporciones (cuotas), no votos absolutos.")
tam = train[train["year"] == 2024].set_index("state")["house_votes_total"]
print(f"  Votos Cámara 2024: máx {tam.idxmax()} {tam.max():,.0f} / mín {tam.idxmin()} {tam.min():,.0f}")

# %% 1.3 Valores extremos
titulo("1.3 VALORES EXTREMOS (regla 1,5 x IQR)")
y = "house_dem_share_2p"
q1, q3 = train[y].quantile([0.25, 0.75])
iqr = q3 - q1
lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
atipicos = train[(train[y] < lim_inf) | (train[y] > lim_sup)]
print(f"Límites: [{lim_inf:.3f}, {lim_sup:.3f}]  -> {len(atipicos)} valores atípicos")
print(atipicos[["year", "state", y, "house_districts_no_d", "house_districts_no_r"]]
      .to_string(index=False))
print("\nDiagnóstico: son resultados reales (no errores de carga), pero están inflados porque")
print("el partido rival no presentó candidato en uno o más distritos (ej.: VT, MA).")
print("Decisión: se conservan y se marca 'todos_disputados' para analizar con y sin ellos.")

fig, ax = plt.subplots(figsize=(8, 4.2))
anios = sorted(train["year"].unique())
datos = [train.loc[train["year"] == a, y] for a in anios]
ax.boxplot(datos, positions=range(len(anios)), widths=0.5, patch_artist=True,
           boxprops=dict(facecolor="#e8e7e2", edgecolor=GRIS),
           medianprops=dict(color=VIOLETA, linewidth=2),
           whiskerprops=dict(color=GRIS), capprops=dict(color=GRIS),
           flierprops=dict(marker="o", markersize=6, markerfacecolor="white",
                           markeredgecolor=TINTA_2))
for _, fila in atipicos.iterrows():
    x = anios.index(fila["year"])
    ax.annotate(fila["state"], (x, fila[y]), xytext=(7, 0), textcoords="offset points",
                fontsize=8, color=TINTA_2, va="center")
ax.axhline(0.5, color=GRIS, linewidth=1, linestyle="--")
ax.set_xticks(range(len(anios)), anios)
ax.set_ylabel("Cuota demócrata bipartidista")
ax.set_title("Cuota D a la Cámara por estado: distribución por año")
guardar(fig, "02_2_boxplot_atipicos")

# %% 1.4 Consistencia y formato
titulo("1.4 CONSISTENCIA Y FORMATO")
controles = {
    "50 estados por año": train.groupby("year")["state"].nunique().eq(50).all(),
    "sin filas duplicadas (year, state)": not train.duplicated(["year", "state"]).any(),
    "proporciones entre 0 y 1": train.filter(regex=r"share(_2p)?(_lag|_prev)?$").stack().between(0, 1).all(),
    "votos no negativos": (train.filter(like="votes").stack() >= 0).all(),
    "bancas D + R <= bancas del estado": (train["house_seats_d"] + train["house_seats_r"]
                                          <= train["house_seats"]).all(),
}
for nombre, ok in controles.items():
    print(f"  [{'OK' if ok else 'FALLA'}] {nombre}")

# %% 2. Integración
titulo("2. INTEGRACIÓN")
print("El CSV integra dos fuentes oficiales (FEC 2016–2022 y Clerk de la Cámara 2024),")
print("homologadas por ../construir_dataset.py. Control: suma nacional de bancas por año.")
print(train.groupby("year")[["house_seats_d", "house_seats_r"]].sum().astype(int).to_string())

# %% 3. Reducción + variables nuevas
titulo("3. REDUCCIÓN Y VARIABLES DERIVADAS")
train["todos_disputados"] = (train["house_contested_share"] == 1).astype(int)
train["swing_partido_presidente"] = np.where(train["pres_party"] == "D",
                                             train["house_dem_swing"], -train["house_dem_swing"])
train["tipo_ciclo"] = np.where(train["is_midterm"] == 1, "medio término", "presidencial")
print("Se descartan: votos absolutos, state_name, house_margin_d y columnas de")
print("control. Se agregan: todos_disputados, swing_partido_presidente, tipo_ciclo.")

# %% 4. Discretización
titulo("4. DISCRETIZACIÓN DE LA CUOTA D A LA CÁMARA")
cortes = [0, 0.45, 0.48, 0.52, 0.55, 1.0001]
niveles = ["Sólido R", "Inclinado R", "Competitivo", "Inclinado D", "Sólido D"]
train["categoria_camara"] = pd.cut(train[y], bins=cortes, labels=niveles, right=False)
print("Umbrales: <45 % Sólido R | 45–48 Inclinado R | 48–52 Competitivo | 52–55 Inclinado D | >=55 Sólido D")
print(train["categoria_camara"].value_counts().reindex(niveles).to_string())

columnas = [
    "year", "state", "tipo_ciclo", "is_midterm", "pres_party", "house_seats",
    "house_dem_share_2p", "categoria_camara", "house_dem_share_2p_rel", "house_seats_d",
    "house_seats_r", "house_seat_share_d",
    "house_contested_share", "todos_disputados", "house_primary_dem_share_2p",
    "senate_race", "senate_dem_share_2p", "pres_dem_share_2p", "pres_dem_share_2p_rel",
    "house_dropoff", "nat_house_dem_share_2p", "nat_pres_dem_share_2p", "house_dem_share_2p_lag", "house_dem_swing",
    "swing_partido_presidente", "pres_dem_share_2p_prev", "pres_dem_share_2p_rel_prev",
]
train[columnas].to_csv(PREPROCESADO, index=False, float_format="%.4f")
print(f"\nDataset preprocesado: {len(train)} filas x {len(columnas)} columnas -> {PREPROCESADO.name}")
