"""Paso 4 — Análisis exploratorio (Módulo II, nivel 2: ¿hay patrones?).

Explora distribuciones, desbalance de categorías y correlaciones entre variables:
histogramas, diagramas de dispersión X/Y con r de Pearson, matriz de correlación,
comparación de correlaciones en el subconjunto de estados con todos sus distritos disputados
y el efecto de medio término sobre el partido del presidente.
Escribe las matrices y tablas en salidas/.

Requiere haber ejecutado 02_preprocesamiento.py.
Uso:  ../.venv/bin/python 04_exploratorio.py
"""

# %% Carga
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comun import (AZUL_D, DIVERGENTE, ETIQUETAS, GRIS, GRIS_NEUTRO, ROJO_R, SALIDAS, TINTA,
                   TINTA_2, VIOLETA, cargar_preprocesado, estilo, guardar, titulo)

estilo()
df = cargar_preprocesado()
Y = "house_dem_share_2p"
disputados = df[df["todos_disputados"] == 1]
print(f"Filas: {len(df)} (todas) / {len(disputados)} (estados con todos sus distritos disputados)")

# %% 2.1 Histogramas
titulo("2.1 DISTRIBUCIONES (histogramas)")
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
ax = axes[0]
bins = np.arange(0, 1.0001, 0.05)
_, bordes, barras = ax.hist(df[Y], bins=bins, edgecolor="#fcfcfb", linewidth=2)
for barra, izq in zip(barras, bordes[:-1]):
    barra.set_facecolor(AZUL_D if izq >= 0.5 else ROJO_R)   # a qué partido favorece el estado
ax.axvline(0.5, color=TINTA, linewidth=1, linestyle="--")
ax.axvline(df[Y].mean(), color=VIOLETA, linewidth=2, label=f"media {df[Y].mean():.3f}")
ax.axvline(df[Y].median(), color=GRIS, linewidth=2, linestyle=":", label=f"mediana {df[Y].median():.3f}")
ax.set_xlabel("Cuota demócrata bipartidista a la Cámara")
ax.set_ylabel("Estado-año (frecuencia)")
ax.legend()
ax.set_title("Cuota D a la Cámara (2016–2024)")

ax = axes[1]
sw = df["house_dem_swing"].dropna()
ax.hist(sw, bins=np.arange(-0.3, 0.3001, 0.025), color=VIOLETA, edgecolor="#fcfcfb", linewidth=2)
ax.axvline(0, color=TINTA, linewidth=1, linestyle="--")
ax.set_xlabel("Cambio en la cuota D respecto del ciclo anterior")
ax.set_ylabel("Estado-año (frecuencia)")
ax.set_title("Swing demócrata entre ciclos")
guardar(fig, "04_1_histogramas")
print(f"Cuota D: media {df[Y].mean():.3f}, mediana {df[Y].median():.3f} -> distribución simétrica,")
print("con colas en 0 y 1 por estados donde un partido no presentó candidatos")
print(f"Swing: media {sw.mean():+.3f}, desvío {sw.std():.3f}; colas por distritos que pasan a"
      " estar o dejar de estar disputados")

# %% 2.1.2 Desbalance de categorías
titulo("2.1.2 DESBALANCE DE CATEGORÍAS (cuota D discretizada)")
niveles = ["Sólido R", "Inclinado R", "Competitivo", "Inclinado D", "Sólido D"]
conteo = df["categoria_camara"].value_counts().reindex(niveles)
print(conteo.to_string())
colores = [ROJO_R, "#ec9a99", "#bdbcb6", "#86b6ef", AZUL_D]
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(niveles, conteo.values, color=colores, width=0.6, edgecolor="#fcfcfb", linewidth=2)
for i, v in enumerate(conteo.values):
    ax.text(i, v + 2, f"{v}  ({v / conteo.sum():.0%})", ha="center", fontsize=9, color=TINTA_2)
ax.grid(axis="x", visible=False)
ax.set_ylabel("Estado-año")
ax.set_title("Estados por categoría de competitividad (2016–2024)")
guardar(fig, "04_2_desbalance_categorias")
print("Solo ~12 % de los casos es 'Competitivo': un modelo va a tener pocos ejemplos justo")
print("en la franja que define la mayoría.")

# %% 2.2 Dispersión X vs Y con r de Pearson
titulo("2.2 RELACIONES X vs Y (dispersión + r de Pearson)")
predictores = ["pres_dem_share_2p_prev", "house_dem_share_2p_lag",
               "senate_dem_share_2p", "house_primary_dem_share_2p"]
fig, axes = plt.subplots(2, 2, figsize=(11, 10))
for ax, x in zip(axes.flat, predictores):
    pares = df[[x, Y, "todos_disputados"]].dropna()
    otros = pares[pares["todos_disputados"] == 0]
    todos = pares[pares["todos_disputados"] == 1]
    ax.scatter(otros[x], otros[Y], s=36, facecolors="none", edgecolors=GRIS, linewidths=1.2,
               label="con distritos sin oposición")
    ax.scatter(todos[x], todos[Y], s=36, color=VIOLETA, edgecolors="#fcfcfb", linewidths=0.8,
               label="todos disputados")
    ax.plot([0, 1], [0, 1], color=TINTA_2, linewidth=1, linestyle="--")
    r = pares[x].corr(pares[Y])
    r_disp = todos[x].corr(todos[Y])
    ax.set_title(f"r = {r:.2f}   (solo disputados: {r_disp:.2f}, n = {len(pares)})",
                 fontsize=10, weight="normal", color=TINTA)
    ax.set_xlabel(ETIQUETAS[x])
    ax.set_ylabel(ETIQUETAS[Y])
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect("equal")
    print(f"  {ETIQUETAS[x]:42s} r = {r:.3f}   solo disputados r = {r_disp:.3f}   n = {len(pares)}")
axes.flat[0].legend(loc="upper left", fontsize=8)
fig.suptitle("Cuota D a la Cámara vs posibles predictores (línea punteada: y = x)",
             fontsize=13, weight="bold", color=TINTA)
fig.tight_layout()
guardar(fig, "04_3_dispersion_predictores")

# %% 2.2.2 Matriz de correlación
titulo("2.2.2 MATRIZ DE CORRELACIÓN")
variables = [Y, "pres_dem_share_2p_prev", "house_dem_share_2p_lag", "pres_dem_share_2p",
             "senate_dem_share_2p", "house_primary_dem_share_2p", "house_seat_share_d",
             "house_contested_share", "house_dropoff", "is_midterm"]
pearson = df[variables].corr(method="pearson")
spearman = df[variables].corr(method="spearman")
pearson.round(4).to_csv(SALIDAS / "correlacion_pearson.csv")
spearman.round(4).to_csv(SALIDAS / "correlacion_spearman.csv")
print("Correlación con la cuota D a la Cámara:")
print(pd.DataFrame({"Pearson": pearson[Y], "Spearman": spearman[Y]}).drop(Y)
      .rename(index=ETIQUETAS).sort_values("Pearson", ascending=False).round(3).to_string())

fig, ax = plt.subplots(figsize=(9, 8))
im = ax.imshow(pearson.values, cmap=DIVERGENTE, vmin=-1, vmax=1)
nombres = [ETIQUETAS[v] for v in variables]
ax.set_xticks(range(len(variables)), nombres, rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(variables)), nombres, fontsize=8)
ax.grid(False)
for i in range(len(variables)):
    for j in range(len(variables)):
        v = pearson.values[i, j]
        if np.isnan(v):   # sin variación conjunta: is_midterm es constante donde la otra tiene dato
            ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, color=GRIS_NEUTRO))
            ax.text(j, i, "—", ha="center", va="center", fontsize=8, color=GRIS)
            continue
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                color="white" if abs(v) > 0.6 else TINTA)
fig.colorbar(im, ax=ax, shrink=0.75, label="r de Pearson")
ax.set_title("Matriz de correlación de Pearson (eliminación por pares)", pad=22)
ax.text(0.5, 1.01, "— : correlación no definida (en las filas con dato, una de las dos variables "
        "es constante)", transform=ax.transAxes, ha="center", va="bottom", fontsize=8,
        color=TINTA_2)
guardar(fig, "04_4_matriz_correlacion")

# %% 2.2.3 Subconjuntos: todos vs solo disputados
titulo("2.2.3 CORRELACIONES EN SUBCONJUNTOS")
comparacion = pd.DataFrame({
    "todos": df[variables].corr()[Y],
    "solo disputados": disputados[variables].corr()[Y],
}).drop([Y, "house_contested_share"])
comparacion["diferencia"] = comparacion["solo disputados"] - comparacion["todos"]
comparacion.index = [ETIQUETAS[v] for v in comparacion.index]
comparacion = comparacion.sort_values("solo disputados")
print(comparacion.round(3).to_string())
comparacion.round(4).to_csv(SALIDAS / "correlacion_subconjuntos.csv")

fig, ax = plt.subplots(figsize=(9, 5.5))
pos = np.arange(len(comparacion))
alto = 0.38
ax.barh(pos - alto / 2, comparacion["todos"], height=alto, color=GRIS, label="todos los estados",
        edgecolor="#fcfcfb", linewidth=1.5)
ax.barh(pos + alto / 2, comparacion["solo disputados"], height=alto, color=VIOLETA,
        label="solo con todos los distritos disputados", edgecolor="#fcfcfb", linewidth=1.5)
ax.set_yticks(pos, comparacion.index, fontsize=9)
ax.axvline(0, color=TINTA_2, linewidth=1)
ax.set_xlim(-0.3, 1.05)
ax.set_xlabel("r de Pearson con la cuota D a la Cámara")
ax.grid(axis="y", visible=False)
ax.legend(loc="lower right", fontsize=8)
ax.set_title("Sin distritos sin oposición, los predictores principales correlacionan más")
guardar(fig, "04_5_correlacion_subconjuntos")

# %% 2.3 Efecto de medio término
titulo("2.3 EFECTO DE MEDIO TÉRMINO SOBRE EL PARTIDO DEL PRESIDENTE")
sw = df.dropna(subset=["swing_partido_presidente"])
tabla = sw.groupby(["year", "pres_party", "tipo_ciclo"])["swing_partido_presidente"].agg(
    ["median", "mean", "std", "count"])
print(tabla.round(3).to_string())
r_mt = sw["is_midterm"].corr(sw["swing_partido_presidente"])
r_nivel = df["is_midterm"].corr(df[Y])
print(f"\nr(is_midterm, cuota D)                    = {r_nivel:+.3f}  -> casi nula")
print(f"r(is_midterm, swing partido del presidente) = {r_mt:+.3f}  -> la señal está en el cambio")
tabla.round(4).to_csv(SALIDAS / "efecto_medio_termino.csv")

fig, ax = plt.subplots(figsize=(8, 4.5))
anios = sorted(sw["year"].unique())
for i, a in enumerate(anios):
    datos = sw.loc[sw["year"] == a, "swing_partido_presidente"]
    color = VIOLETA if sw.loc[sw["year"] == a, "is_midterm"].iloc[0] == 1 else GRIS
    ax.boxplot([datos], positions=[i], widths=0.5, patch_artist=True,
               boxprops=dict(facecolor=color, edgecolor=color, alpha=0.35),
               medianprops=dict(color=color, linewidth=2.5),
               whiskerprops=dict(color=color), capprops=dict(color=color),
               flierprops=dict(marker="o", markersize=5, markeredgecolor=color))
    ax.text(i + 0.3, datos.median(), f"{datos.median():+.1%}", fontsize=9, color=TINTA,
            va="center", weight="bold")
ax.axhline(0, color=TINTA, linewidth=1)
partido = sw.groupby("year")["pres_party"].first()
ax.set_xticks(range(len(anios)), [f"{a}\npres. {partido[a]}" for a in anios])
ax.set_xlim(-0.5, len(anios) - 0.2)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0%}"))
ax.set_ylabel("Swing del partido del presidente")
ax.plot([], [], color=VIOLETA, linewidth=6, alpha=0.5, label="medio término")
ax.plot([], [], color=GRIS, linewidth=6, alpha=0.5, label="año presidencial")
ax.legend(loc="upper right", fontsize=8)
ax.set_title("En medio término, el partido del presidente pierde votos")
guardar(fig, "04_6_efecto_medio_termino")

print("\nConclusiones exploratorias:")
print(" 1. El voto presidencial previo es el predictor más fuerte (nacionalización del voto).")
print(" 2. Los distritos sin oposición agregan ruido: hay que tratarlos antes de modelar.")
print(" 3. El efecto de medio término aparece en el swing del partido del presidente, no en el")
print("    nivel de voto D: la variable útil es la interacción medio término x partido.")
print(" Correlación no implica causalidad: estas relaciones orientan el modelo, no lo prueban.")
