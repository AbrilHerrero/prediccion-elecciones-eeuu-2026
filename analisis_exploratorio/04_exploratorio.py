"""Paso 4 — Análisis exploratorio (Módulo II, nivel 2: ¿hay patrones?).

Explora distribuciones, desbalance de categorías y correlaciones entre los predictores de la
presidencial anterior y el voto en el medio término: dispersión X/Y con r de Pearson, matriz
de correlación, subconjunto de estados con todos sus distritos disputados, evolución de las
correlaciones por año, efecto de medio término y líneas base de error para el modelo.
Escribe las matrices y tablas en salidas/.

Requiere haber ejecutado 02_preprocesamiento.py.
Uso:  ../.venv/bin/python 04_exploratorio.py
"""

# %% Carga
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comun import (AZUL_D, DIVERGENTE, ETIQUETAS, GRIS, ROJO_R, SALIDAS, TINTA, TINTA_2,
                   VIOLETA, cargar_preprocesado, estilo, guardar, titulo)

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
ax.set_title("Cuota D a la Cámara en el medio término")

ax = axes[1]
sw = df["president_party_swing"]
_, bordes, barras = ax.hist(sw, bins=np.arange(-0.35, 0.3501, 0.025), edgecolor="#fcfcfb", linewidth=2)
for barra, izq in zip(barras, bordes[:-1]):
    barra.set_facecolor(VIOLETA if izq < 0 else GRIS)        # violeta: el partido del presidente pierde
ax.axvline(0, color=TINTA, linewidth=1, linestyle="--")
ax.axvline(sw.median(), color=TINTA_2, linewidth=2, linestyle=":", label=f"mediana {sw.median():+.3f}")
ax.set_xlabel("Cambio en la cuota del partido del presidente\nvs la presidencial anterior")
ax.set_ylabel("Estado-año (frecuencia)")
ax.legend()
ax.set_title("Swing del partido del presidente")
guardar(fig, "04_1_histogramas")
print(f"Cuota D: media {df[Y].mean():.3f}, mediana {df[Y].median():.3f} -> distribución simétrica,")
print("con colas por estados donde un partido no presentó candidatos")
print(f"Swing del partido del presidente: mediana {sw.median():+.3f}; negativo en "
      f"{(sw < 0).mean():.0%} de los estado-año")

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
ax.set_title("Estados por categoría de competitividad (medio término 2006–2022)")
guardar(fig, "04_2_desbalance_categorias")
print(f"Solo {conteo['Competitivo'] / conteo.sum():.0%} de los casos es 'Competitivo': un modelo va a")
print("tener pocos ejemplos justo en la franja que define la mayoría.")

# %% 2.2 Dispersión X vs Y con r de Pearson
titulo("2.2 RELACIONES X vs Y (dispersión + r de Pearson)")
predictores = ["pres_dem_share_2p_prev", "house_dem_share_2p_prev",
               "house_seat_share_d_prev", "house_primary_dem_share_2p"]
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
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect("equal")
    print(f"  {ETIQUETAS[x]:48s} r = {r:.3f}   solo disputados r = {r_disp:.3f}   n = {len(pares)}")
axes.flat[0].legend(loc="upper left", fontsize=8)
fig.suptitle("Cuota D a la Cámara en el medio término vs posibles predictores (línea punteada: y = x)",
             fontsize=13, weight="bold", color=TINTA)
fig.tight_layout()
guardar(fig, "04_3_dispersion_predictores")

# %% 2.2.2 Matriz de correlación
titulo("2.2.2 MATRIZ DE CORRELACIÓN")
variables = [Y, "pres_dem_share_2p_prev", "house_dem_share_2p_prev", "house_seat_share_d_prev",
             "house_primary_dem_share_2p", "senate_dem_share_2p", "house_contested_share",
             "house_dropoff_prev", "partido_pres_camara_prev", "president_party_swing"]
pearson = df[variables].corr(method="pearson")
spearman = df[variables].corr(method="spearman")
pearson.round(4).to_csv(SALIDAS / "correlacion_pearson.csv")
spearman.round(4).to_csv(SALIDAS / "correlacion_spearman.csv")
print("Correlación con la cuota D a la Cámara:")
print(pd.DataFrame({"Pearson": pearson[Y], "Spearman": spearman[Y]}).drop(Y)
      .rename(index=ETIQUETAS).sort_values("Pearson", ascending=False).round(3).to_string())

fig, ax = plt.subplots(figsize=(9.5, 8.5))
im = ax.imshow(pearson.values, cmap=DIVERGENTE, vmin=-1, vmax=1)
nombres = [ETIQUETAS[v] for v in variables]
ax.set_xticks(range(len(variables)), nombres, rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(variables)), nombres, fontsize=8)
ax.grid(False)
for i in range(len(variables)):
    for j in range(len(variables)):
        v = pearson.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                color="white" if abs(v) > 0.6 else TINTA)
fig.colorbar(im, ax=ax, shrink=0.75, label="r de Pearson")
ax.set_title("Matriz de correlación de Pearson (eliminación por pares)")
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
ax.set_yticks(pos, comparacion.index, fontsize=8)
ax.axvline(0, color=TINTA_2, linewidth=1)
ax.set_xlim(-0.6, 1.05)
ax.set_xlabel("r de Pearson con la cuota D a la Cámara")
ax.grid(axis="y", visible=False)
ax.legend(loc="lower right", fontsize=8)
ax.set_title("Correlación con la cuota D: todos los estados vs solo disputados")
guardar(fig, "04_5_correlacion_subconjuntos")

# %% 2.2.4 Correlaciones por año: ¿se nacionalizó el voto?
titulo("2.2.4 CORRELACIONES POR AÑO (nacionalización)")
por_anio = pd.DataFrame({
    ETIQUETAS[x]: df.groupby("year")[[x, Y]].apply(lambda g, x=x: g[x].corr(g[Y]))
    for x in ("pres_dem_share_2p_prev", "house_dem_share_2p_prev")
})
por_anio["Cuota D Presidente, solo disputados"] = disputados.groupby("year")[
    ["pres_dem_share_2p_prev", Y]].apply(lambda g: g["pres_dem_share_2p_prev"].corr(g[Y]))
print(por_anio.round(3).to_string())
por_anio.round(4).to_csv(SALIDAS / "correlacion_por_anio.csv")
por_periodo = df.groupby("periodo")[["pres_dem_share_2p_prev", "house_dem_share_2p_prev", Y]].apply(
    lambda g: pd.Series({"r Presidente": g["pres_dem_share_2p_prev"].corr(g[Y]),
                         "r Cámara": g["house_dem_share_2p_prev"].corr(g[Y]), "n": len(g)}))
print("\nPor período:")
print(por_periodo.round(3).to_string())

fig, ax = plt.subplots(figsize=(8, 4.3))
estilos = [(VIOLETA, "-", "o"), (GRIS, "--", "s"), (TINTA_2, ":", "^")]
for (columna, serie), (color, linea, marca) in zip(por_anio.items(), estilos):
    ax.plot(serie.index, serie.values, color=color, linestyle=linea, marker=marca, linewidth=2,
            markersize=7, label=columna)
ax.set_xticks(por_anio.index)
ax.set_ylim(0.4, 1)
ax.set_ylabel("r de Pearson con la cuota D a la Cámara")
ax.legend(loc="lower right", fontsize=8)
ax.set_title("¿Cuánto anticipa la presidencial anterior al medio término?")
guardar(fig, "04_6_correlacion_por_anio")

# %% 2.3 Efecto de medio término
titulo("2.3 EFECTO DE MEDIO TÉRMINO SOBRE EL PARTIDO DEL PRESIDENTE")
swing = df.groupby(["year", "pres_party"])["president_party_swing"]
tabla = swing.agg(["median", "mean", "std", "count"])
tabla["% estados en que pierde"] = swing.apply(lambda s: (s < 0).mean())
print(tabla.round(3).to_string())
tabla.round(4).to_csv(SALIDAS / "efecto_medio_termino.csv")

fig, ax = plt.subplots(figsize=(8.5, 4.5))
anios = sorted(df["year"].unique())
partido = df.groupby("year")["pres_party"].first()
for i, a in enumerate(anios):
    datos = df.loc[df["year"] == a, "president_party_swing"]
    color = AZUL_D if partido[a] == "D" else ROJO_R
    ax.boxplot([datos], positions=[i], widths=0.5, patch_artist=True,
               boxprops=dict(facecolor=color, edgecolor=color, alpha=0.35),
               medianprops=dict(color=color, linewidth=2.5),
               whiskerprops=dict(color=color), capprops=dict(color=color),
               flierprops=dict(marker="o", markersize=5, markeredgecolor=color))
    ax.text(i + 0.3, datos.median(), f"{datos.median() * 100:+.1f} pp", fontsize=9, color=TINTA,
            va="center", weight="bold")
ax.axhline(0, color=TINTA, linewidth=1)
ax.set_xticks(range(len(anios)), [f"{a}\npres. {partido[a]}" for a in anios])
ax.set_xlim(-0.5, len(anios) - 0.1)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v * 100:+.0f} pp"))
ax.set_ylabel("Swing del partido del presidente")
ax.set_title("En los cinco medio término, el partido del presidente pierde votos")
guardar(fig, "04_7_efecto_medio_termino")

# %% 2.3.2 ¿Dónde pierde más el partido del presidente?
titulo("2.3.2 SWING DEL PARTIDO DEL PRESIDENTE vs SU RESULTADO ANTERIOR")
x, s = "partido_pres_camara_prev", "president_party_swing"
r_todos = df[x].corr(df[s])
r_disp = disputados[x].corr(disputados[s])
print(f"r(cuota previa del partido del presidente, swing) = {r_todos:+.3f}   solo disputados: {r_disp:+.3f}")
print("Negativo: donde el partido del presidente había sacado más votos, pierde más.")
print("Es consistente con 'surge and decline' (se van los votantes que arrastró la presidencial)")
print("y con regresión a la media.")

fig, ax = plt.subplots(figsize=(7.5, 5.5))
otros = df[df["todos_disputados"] == 0]
ax.scatter(otros[x], otros[s], s=32, facecolors="none", edgecolors=GRIS, linewidths=1.1,
           label="con distritos sin oposición")
ax.scatter(disputados[x], disputados[s], s=32, color=VIOLETA, edgecolors="#fcfcfb",
           linewidths=0.8, label="todos disputados")
pendiente, ordenada = np.polyfit(disputados[x], disputados[s], 1)
xs = np.linspace(disputados[x].min(), disputados[x].max(), 2)
ax.plot(xs, ordenada + pendiente * xs, color=VIOLETA, linewidth=2, label="recta (solo disputados)")
ax.axhline(0, color=TINTA, linewidth=1)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v * 100:+.0f} pp"))
ax.set_xlabel("Cuota del partido del presidente en la Cámara (presidencial anterior)")
ax.set_ylabel("Swing del partido del presidente")
ax.legend(loc="upper right", fontsize=8)
ax.set_title(f"Pierde más donde estaba más fuerte (r = {r_todos:.2f}; disputados {r_disp:.2f})",
             fontsize=11)
guardar(fig, "04_8_swing_vs_resultado_previo")

# %% 2.4 Líneas base para el modelo
titulo("2.4 LÍNEAS BASE (error absoluto medio en la cuota D, en puntos porcentuales)")
signo = np.where(df["pres_party"] == "D", 1, -1)
nacional = df.groupby("year").agg(antes=("nat_house_dem_share_2p_prev", "first"),
                                  despues=("nat_house_dem_share_2p", "first"),
                                  partido=("pres_party", "first"))
castigo = np.where(nacional["partido"] == "D", 1, -1) * (nacional["despues"] - nacional["antes"])
castigo = pd.Series(castigo, index=nacional.index)
# Castigo promedio de los OTROS medio término: lo que se sabría antes de votar
castigo_previo = df["year"].map({a: castigo.drop(a).mean() for a in castigo.index})
cambio_nacional = df["nat_house_dem_share_2p"] - df["nat_house_dem_share_2p_prev"]
metodos = {
    "Repetir la Cámara de la presidencial anterior": df["house_dem_share_2p_prev"],
    "Usar el voto presidencial anterior": df["pres_dem_share_2p_prev"],
    "Cámara anterior + castigo medio de los otros medio término": df["house_dem_share_2p_prev"] + signo * castigo_previo,
    "Presidencial anterior + castigo medio de los otros medio término": df["pres_dem_share_2p_prev"] + signo * castigo_previo,
    "Swing uniforme con el cambio nacional real (cota optimista)": df["house_dem_share_2p_prev"] + cambio_nacional,
}
lineas_base = pd.DataFrame({
    "MAE todos (pp)": {k: (v - df[Y]).abs().mean() * 100 for k, v in metodos.items()},
    "MAE solo disputados (pp)": {k: (v - df[Y])[df["todos_disputados"] == 1].abs().mean() * 100
                                 for k, v in metodos.items()},
})
print(lineas_base.round(2).to_string())
lineas_base.round(3).to_csv(SALIDAS / "lineas_base.csv")
print("\nEl castigo de cada año se estima con los OTROS cuatro medio término, para no usar")
print("información que no se conocía antes de votar. El swing uniforme usa el cambio nacional")
print("real: es una cota de lo que se lograría acertando la ola nacional.")

print("\nConclusiones exploratorias:")
print(" 1. La presidencial anterior anticipa bien el medio término, y mejor en los años recientes.")
print(" 2. Los distritos sin oposición distorsionan las medidas de la Cámara en las dos elecciones a")
print("    la vez, lo que infla su correlación; el voto presidencial no tiene ese problema.")
print(" 3. El partido del presidente pierde votos en los cinco medio término, y pierde más donde")
print("    estaba más fuerte.")
print(" 4. Sumar el castigo esperado al voto presidencial anterior ya mejora a repetir el pasado.")
print(" Correlación no implica causalidad: estas relaciones orientan el modelo, no lo prueban.")
