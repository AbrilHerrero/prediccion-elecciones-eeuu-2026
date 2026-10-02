"""Paso 2 — Preprocesamiento (Módulo I: limpieza, integración, reducción y discretización).

Audita la calidad del dataset y genera salidas/dataset_preprocesado.csv con las filas
2006–2022, las variables elegidas para el análisis y cuatro columnas nuevas:
    todos_disputados          1 si todos los distritos del estado tuvieron candidato D y R
    partido_pres_camara_prev  cuota a la Cámara del partido del presidente en la presidencial anterior
    periodo                   "2006–2014" o "2018–2022", para comparar épocas
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
print("Celdas vacías por columna (filas 2006–2022):")
print(faltantes.to_string())

# Faltante estructural = el dato no existe (no hubo esa elección). Faltante real = existe pero
# no está en las fuentes.
print("\nFaltantes ESTRUCTURALES (no imputar: inventaría elecciones que no ocurrieron):")
print("  senate_*                  el estado no eligió senador ese año (cada ciclo se renueva 1/3)")
print("  senate_dem_share_2p       además, elecciones sin un D contra un R (ej.: Sanders en VT)")
print("Faltantes REALES:")
print("  house_primary_*           ni el D ni el R registraron votos en internas: Luisiana usa una")
print("                            interna abierta sin partidos; CT, UT, DE y SD nominaron por")
print("                            convención o sin interna disputada en esos años")
print("\nTodos los predictores _prev están completos.")
print("Decisión: sin imputación. Cada correlación usa los pares de filas con dato en ambas")
print("variables (eliminación por pares), que conserva la mayor muestra posible por análisis.")

# Mapa de faltantes: % de celdas vacías por columna y año
cols_mapa = faltantes.index.tolist()
mapa = train.groupby("year")[cols_mapa].apply(lambda g: g.isna().mean() * 100).T
fig, ax = plt.subplots(figsize=(7, 0.42 * len(cols_mapa) + 1.4))
im = ax.imshow(mapa.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(len(mapa.columns)), mapa.columns)
ax.set_yticks(range(len(mapa.index)), mapa.index, fontsize=8)
ax.grid(False)
for i in range(mapa.shape[0]):
    for j in range(mapa.shape[1]):
        v = mapa.values[i, j]
        if v > 0:
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8,
                    color="white" if v > 60 else TINTA_2)
fig.colorbar(im, ax=ax, label="% de estados sin dato", shrink=0.8)
ax.set_title("Datos faltantes por columna y año")
guardar(fig, "02_1_mapa_faltantes")

# %% 1.2 Columnas irrelevantes y redundantes
titulo("1.2 COLUMNAS IRRELEVANTES Y REDUNDANTES")
print("house_seats_r = house_seats - house_seats_d  -> redundante")
print("president_party_house_share_2p = cuota D o 1 - cuota D  -> otra escala del objetivo")
print("house_dem_share_2p_rel = cuota D - cuota nacional del año  -> otra escala del objetivo")
print("state_name repite a state  -> redundante")
print("state, split  -> identificadores/metadatos: no son predictores")
print("senate_*  -> se vota el mismo día que la Cámara: es otro resultado, no un predictor")
print("\nEscalas: los votos absolutos dependen de la población.")
tam = train[train["year"] == 2022].set_index("state")["house_votes_total"]
print(f"  Votos Cámara 2022: máx {tam.idxmax()} {tam.max():,.0f} / mín {tam.idxmin()} {tam.min():,.0f}")
print("Para comparar estados se usan proporciones (cuotas), no votos absolutos.")

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
print("el partido rival no presentó candidato en uno o más distritos.")
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
for (anio, valor), grupo in atipicos.groupby(["year", y]):
    ax.annotate("/".join(grupo["state"]), (anios.index(anio), valor), xytext=(7, 0),
                textcoords="offset points", fontsize=8, color=TINTA_2, va="center")
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
    "435 distritos por año": train.groupby("year")["house_seats"].sum().eq(435).all(),
    "proporciones entre 0 y 1": train.filter(regex=r"share(_2p)?(_prev)?$").stack().between(0, 1).all(),
    "votos no negativos": (train.filter(like="votes").stack() >= 0).all(),
    "bancas D + R <= bancas del estado": (train["house_seats_d"] + train["house_seats_r"]
                                          <= train["house_seats"]).all(),
    "swing = cuota - cuota previa": np.allclose(
        train["house_dem_swing"], train[y] - train["house_dem_share_2p_prev"], atol=1e-3),
}
for nombre, ok in controles.items():
    print(f"  [{'OK' if ok else 'FALLA'}] {nombre}")

# %% 2. Integración
titulo("2. INTEGRACIÓN")
print("El CSV integra 11 elecciones de dos fuentes oficiales (FEC 2004–2022 y Clerk de la Cámara")
print("2024), homologadas por ../construir_dataset_midterms.py, que valida las bancas contra las")
print("cifras oficiales. Bancas nacionales antes (presidencial) y después (medio término):")
bancas = train.groupby("year").agg(presidente=("pres_party", "first"),
                                   bancas_d_antes=("house_seats_d_prev", "sum"),
                                   bancas_d_despues=("house_seats_d", "sum"))
print(bancas.astype({"bancas_d_antes": int, "bancas_d_despues": int}).to_string())

# %% 3. Reducción + variables nuevas
titulo("3. REDUCCIÓN Y VARIABLES DERIVADAS")
train["todos_disputados"] = (train["house_contested_share"] == 1).astype(int)
train["partido_pres_camara_prev"] = np.where(train["pres_party"] == "D",
                                             train["house_dem_share_2p_prev"],
                                             1 - train["house_dem_share_2p_prev"])
train["periodo"] = np.where(train["year"] <= 2014, "2006–2014", "2018–2022")
print("Se descartan: votos absolutos, state_name, columnas redundantes y de control.")
print("Se agregan: todos_disputados, partido_pres_camara_prev, periodo.")
print(f"  Estados-año con todos los distritos disputados: {train['todos_disputados'].sum()} de {len(train)}")

# %% 4. Discretización
titulo("4. DISCRETIZACIÓN DE LA CUOTA D A LA CÁMARA")
cortes = [0, 0.45, 0.48, 0.52, 0.55, 1.0001]
niveles = ["Sólido R", "Inclinado R", "Competitivo", "Inclinado D", "Sólido D"]
train["categoria_camara"] = pd.cut(train[y], bins=cortes, labels=niveles, right=False)
print("Umbrales: <45 % Sólido R | 45–48 Inclinado R | 48–52 Competitivo | 52–55 Inclinado D | >=55 Sólido D")
print(train["categoria_camara"].value_counts().reindex(niveles).to_string())

columnas = [
    "year", "state", "periodo", "pres_party", "house_seats", "senate_race",
    "pres_dem_share_2p_prev", "pres_dem_share_2p_rel_prev", "house_dem_share_2p_prev",
    "house_dem_share_2p_rel_prev", "house_seat_share_d_prev", "house_contested_share_prev",
    "house_dropoff_prev", "partido_pres_camara_prev", "nat_house_dem_share_2p_prev",
    "house_primary_dem_share_2p", "house_contested_share", "todos_disputados",
    "house_dem_share_2p", "categoria_camara", "house_dem_share_2p_rel", "nat_house_dem_share_2p",
    "house_dem_swing", "president_party_swing", "house_seats_d", "house_seats_r",
    "house_seats_d_prev", "house_seats_r_prev",
    "house_seat_share_d", "senate_dem_share_2p",
]
train[columnas].to_csv(PREPROCESADO, index=False, float_format="%.4f")
print(f"\nDataset preprocesado: {len(train)} filas x {len(columnas)} columnas -> {PREPROCESADO.name}")
