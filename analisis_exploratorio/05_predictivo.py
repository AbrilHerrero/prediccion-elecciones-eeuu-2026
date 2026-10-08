"""Paso 5 — Análisis predictivo (Módulo III: ¿qué va a pasar?).

Contrasta las hipótesis que dejó el análisis exploratorio y predice el medio término 2026:
    H1  el voto presidencial anterior anticipa el voto a la Cámara en el medio término
    H2  el partido del presidente pierde votos (castigo de medio término)
    H3  pierde más donde estaba más fuerte (regresión hacia el 50 %)

Entrena modelos sobre los medio término 2006–2022, los evalúa dejando afuera un medio término
por vez, elige el más simple entre los de menor error (regla de un error estándar), predice la
cuota demócrata de cada estado en 2026, la convierte en bancas con la curva votos-bancas nacional
de 2004–2024 y estima la incertidumbre por simulación.
Escribe las tablas en salidas/ (prefijo predictivo_) y las figuras 05_* en figuras/.

Uso:  ../.venv/bin/python 05_predictivo.py
"""

# %% Carga
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneGroupOut

from comun import (AZUL_D, GRIS, ROJO_R, SALIDAS, TINTA, TINTA_2, VIOLETA, cargar_dataset,
                   estilo, guardar, titulo)

estilo()
datos = cargar_dataset()
MAYORIA = 218
SIMULACIONES = 10_000
rng = np.random.default_rng(2026)

# %% 1. Variables desde el punto de vista del partido del presidente
titulo("1. VARIABLES DESDE EL PUNTO DE VISTA DEL PARTIDO DEL PRESIDENTE")
# Las teorías de medio término hablan del partido del presidente, no de un partido fijo. Pasar
# todo a ese punto de vista permite que un mismo modelo aprenda el castigo con presidentes D y R.
# Las cuotas se centran en 0,5: el intercepto queda como el castigo en un estado parejo.
signo = np.where(datos["pres_party"] == "D", 1, -1)


def del_partido_pres(cuota_d):
    """Devuelve la cuota del partido del presidente, centrada en 0,5, a partir de la cuota D."""
    return signo * (cuota_d - 0.5)


datos["x_presidente"] = del_partido_pres(datos["pres_dem_share_2p_prev"])
datos["x_camara"] = del_partido_pres(datos["house_dem_share_2p_prev"])
datos["x_bancas"] = del_partido_pres(datos["house_seat_share_d_prev"])
datos["x_nacional"] = del_partido_pres(datos["nat_house_dem_share_2p_prev"])
datos["y_partido_pres"] = del_partido_pres(datos["house_dem_share_2p"])
datos["signo"] = signo

train = datos[datos["split"] == "train"].reset_index(drop=True)
pred26 = datos[datos["split"] == "predict"].reset_index(drop=True)
Y = "house_dem_share_2p"
disputado = train["house_contested_share"] == 1
votos_2p = train["house_votes_d"] + train["house_votes_r"]
print(f"Entrenamiento: {len(train)} filas (5 medio término)   Predicción: {len(pred26)} filas (2026)")
print("Solo se usan predictores conocidos antes de votar y disponibles para 2026 (_prev).")

# %% 2. Modelos candidatos y validación dejando afuera un medio término
titulo("2. VALIDACIÓN: DEJAR AFUERA UN MEDIO TÉRMINO POR VEZ")
# Las 50 filas de un año comparten la misma ola nacional: no son independientes. Por eso se
# deja afuera un año entero por vez (5 pliegues), como si cada medio término fuera el futuro.
MODELOS = {
    "Lineal simple (voto presidencial)": (LinearRegression, ["x_presidente"]),
    "Lineal múltiple": (LinearRegression,
                        ["x_presidente", "x_camara", "x_bancas", "house_contested_share_prev"]),
    "Lineal múltiple + contexto nacional": (LinearRegression,
                                            ["x_presidente", "x_camara", "x_bancas",
                                             "house_contested_share_prev", "x_nacional"]),
    "Lineal múltiple + contexto nacional + sesgo partidario": (
        LinearRegression, ["x_presidente", "x_camara", "x_bancas", "house_contested_share_prev",
                           "x_nacional", "signo"]),
    "Bosque aleatorio": (lambda: RandomForestRegressor(n_estimators=500, min_samples_leaf=5,
                                                       random_state=0),
                         ["x_presidente", "x_camara", "x_bancas", "house_contested_share_prev"]),
}


def a_cuota_d(filas, y_partido_pres):
    """Devuelve la cuota D que corresponde a una cuota centrada del partido del presidente."""
    return 0.5 + filas["signo"].to_numpy() * y_partido_pres


grupos = LeaveOneGroupOut()
fuera_de_muestra = pd.DataFrame(index=train.index)
for nombre, (crear, columnas) in MODELOS.items():
    pred = np.empty(len(train))
    for idx_ent, idx_val in grupos.split(train, groups=train["year"]):
        modelo = crear().fit(train.loc[idx_ent, columnas], train.loc[idx_ent, "y_partido_pres"])
        pred[idx_val] = a_cuota_d(train.loc[idx_val], modelo.predict(train.loc[idx_val, columnas]))
    fuera_de_muestra[nombre] = pred

# Líneas base del análisis exploratorio, recalculadas igual (castigo de los OTROS años)
nac = train.groupby("year")[["signo", "nat_house_dem_share_2p", "nat_house_dem_share_2p_prev"]].first()
cambio = nac["signo"] * (nac["nat_house_dem_share_2p"] - nac["nat_house_dem_share_2p_prev"])
castigo_otros = train["year"].map({a: cambio.drop(a).mean() for a in cambio.index})
LINEAS_BASE = {
    "Base: repetir la Cámara anterior": train["house_dem_share_2p_prev"],
    "Base: presidencial anterior + castigo medio": train["pres_dem_share_2p_prev"]
                                                  + train["signo"] * castigo_otros,
}
for nombre, pred in LINEAS_BASE.items():
    fuera_de_muestra[nombre] = pred


def metricas(pred):
    """Devuelve las métricas de error de una predicción de cuota D fuera de muestra."""
    error = pred - train[Y]
    nacional = (pred * votos_2p).groupby(train["year"]).sum() / votos_2p.groupby(train["year"]).sum()
    error_nacional = nacional - train.groupby("year")["nat_house_dem_share_2p"].first()
    error_relativo = error - error.groupby(train["year"]).transform("mean")
    return pd.Series({
        "MAE (pp)": error.abs().mean() * 100,
        "MAE disputados (pp)": error[disputado].abs().mean() * 100,
        "RMSE (pp)": np.sqrt((error ** 2).mean()) * 100,
        "R²": 1 - (error ** 2).sum() / ((train[Y] - train[Y].mean()) ** 2).sum(),
        "Acierta el partido que gana el voto del estado": ((pred > 0.5) == (train[Y] > 0.5)).mean(),
        "Error nacional medio (pp)": error_nacional.abs().mean() * 100,
        "MAE con la ola conocida (pp)": error_relativo.abs().mean() * 100,
    })


comparacion = fuera_de_muestra.apply(metricas).T
# Error estándar del MAE: desvío de los 5 MAE por año / raíz de 5
mae_por_anio = fuera_de_muestra.sub(train[Y], axis=0).abs().groupby(train["year"]).mean() * 100
comparacion["EE del MAE (pp)"] = mae_por_anio.std() / np.sqrt(len(mae_por_anio))
comparacion["variables"] = [len(MODELOS[n][1]) if n in MODELOS else 0 for n in comparacion.index]
comparacion = comparacion.sort_values("MAE (pp)")
print(comparacion.round(3).to_string())
comparacion.round(4).to_csv(SALIDAS / "predictivo_comparacion_modelos.csv")

# Regla de un error estándar: el modelo más simple cuyo MAE no supera al mejor + 1 EE. Las
# variables nacionales se estiman con solo 4–5 olas: cada una extra arriesga sobreajuste.
propios = comparacion.loc[list(MODELOS)]
mejor = propios["MAE (pp)"].idxmin()
umbral = propios.loc[mejor, "MAE (pp)"] + propios.loc[mejor, "EE del MAE (pp)"]
ELEGIDO = propios[propios["MAE (pp)"] <= umbral].sort_values(["variables", "MAE (pp)"]).index[0]
base = comparacion.loc["Base: presidencial anterior + castigo medio", "MAE (pp)"]
print(f"\nMenor MAE: {mejor} ({propios.loc[mejor, 'MAE (pp)']:.2f} pp, umbral 1 EE = {umbral:.2f} pp)")
print(f"Modelo elegido (el más simple dentro del umbral): {ELEGIDO}")
print(f"  MAE {comparacion.loc[ELEGIDO, 'MAE (pp)']:.2f} pp vs línea base {base:.2f} pp")
print("'MAE con la ola conocida' resta el error medio de cada año: mide qué tan bien ordena a los")
print("estados entre sí. La diferencia con el MAE total es el costo de no conocer la ola nacional.")

fig, ax = plt.subplots(figsize=(9, 4.2))
orden = comparacion["MAE (pp)"].sort_values(ascending=False)
colores = [VIOLETA if n == ELEGIDO else ("#bdbcb6" if n in LINEAS_BASE else GRIS) for n in orden.index]
ax.barh(orden.index, orden.values, color=colores, height=0.6, edgecolor="#fcfcfb", linewidth=2)
for i, v in enumerate(orden.values):
    ax.text(v + 0.06, i, f"{v:.2f} pp", va="center", fontsize=9, color=TINTA_2,
            bbox=dict(facecolor="#fcfcfb", edgecolor="none", pad=1))
ax.axvline(base, color=TINTA_2, linewidth=1, linestyle="--", zorder=1)
ax.set_xlabel("Error absoluto medio en la cuota D por estado (pp, fuera de muestra)")
ax.set_xlim(0, orden.max() * 1.15)
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=9)
ax.set_title("Error de cada modelo al predecir un medio término que no vio\n"
             "(violeta: elegido · gris claro: líneas base · punteada: mejor línea base)", fontsize=11)
guardar(fig, "05_1_comparacion_modelos")

# %% 3. Contraste de hipótesis con modelos lineales de una variable
titulo("3. CONTRASTE DE HIPÓTESIS (coeficientes en cada pliegue)")
# Cada hipótesis se lee en un coeficiente; reestimarlo dejando afuera cada año muestra si el
# signo depende de un medio término en particular.
coeficientes = []
for idx_ent, _ in grupos.split(train, groups=train["year"]):
    ent = train.loc[idx_ent]
    pres = LinearRegression().fit(ent[["x_presidente"]], ent["y_partido_pres"])
    cam = LinearRegression().fit(ent[["x_camara"]], ent["y_partido_pres"])
    coeficientes.append({"año dejado afuera": sorted(set(train["year"]) - set(ent["year"]))[0],
                         "castigo en estado parejo (pp)": pres.intercept_ * 100,
                         "pendiente voto presidencial": pres.coef_[0],
                         "pendiente voto a la Cámara": cam.coef_[0]})
coef = pd.DataFrame(coeficientes).set_index("año dejado afuera")
print(coef.round(3).to_string())
coef.round(4).to_csv(SALIDAS / "predictivo_coeficientes.csv")
pres = LinearRegression().fit(train[["x_presidente"]], train["y_partido_pres"])
cam = LinearRegression().fit(train[["x_camara"]], train["y_partido_pres"])
castigo = pres.intercept_ * 100
print(f"\nCon los 5 medio término: cuota partido pres. = 0,5 {castigo / 100:+.4f} "
      f"+ {pres.coef_[0]:.3f} x (cuota presidencial previa - 0,5)")
print(f"H1 (la presidencial anticipa): pendiente > 0 en los 5 pliegues -> "
      f"{(coef['pendiente voto presidencial'] > 0).all()}")
print(f"H2 (castigo de medio término): castigo < 0 en los 5 pliegues -> "
      f"{(coef['castigo en estado parejo (pp)'] < 0).all()}  ({castigo:+.1f} pp en un estado parejo)")
print(f"H3 (pierde más donde era más fuerte): pendiente Cámara < 1 en los 5 pliegues -> "
      f"{(coef['pendiente voto a la Cámara'] < 1).all()}  (pendiente {cam.coef_[0]:.2f})")
print(f"   Por cada 10 pp sobre el 50 % en la Cámara, el partido del presidente conserva "
      f"{cam.coef_[0] * 10:.1f} pp: el voto a la Cámara vuelve hacia el 50 %.")
print(f"   Sobre el voto presidencial la pendiente es {pres.coef_[0]:.2f} ≈ 1: el castigo es parejo.")
print("   La 'pérdida extra' es del voto a la Cámara (candidatos sin rival, legisladores en ejercicio)")
print("   que vuelve hacia la base partidaria que marca el voto presidencial.")

fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
for ax, col, ref, texto in [
    (axes[0], "castigo en estado parejo (pp)", 0, "H2 · Castigo en un estado 50–50 (pp)"),
    (axes[1], "pendiente voto presidencial", 1, "H1 · Pendiente sobre el voto presidencial"),
    (axes[2], "pendiente voto a la Cámara", 1, "H3 · Pendiente sobre el voto a la Cámara"),
]:
    ax.axhline(ref, color=TINTA_2, linewidth=1, linestyle="--")
    ax.plot(coef.index, coef[col], color=VIOLETA, marker="o", markersize=9, linewidth=0,
            markeredgecolor="#fcfcfb", markeredgewidth=2)
    for a, v in coef[col].items():
        ax.annotate(f"{v:.2f}", (a, v), xytext=(9, 0), textcoords="offset points", va="center",
                    fontsize=9, color=TINTA_2)
    ax.set_xticks(coef.index)
    ax.set_xlabel("Medio término dejado afuera al entrenar")
    ax.set_title(texto, fontsize=11)
axes[0].set_ylim(min(coef.iloc[:, 0].min() * 1.3, -1), 0.8)
axes[1].set_ylim(0, 1.15)
axes[2].set_ylim(0, 1.15)
fig.suptitle("Los coeficientes mantienen su lado de la referencia sin importar qué año se deje afuera",
             fontsize=12, weight="bold", color=TINTA)
fig.tight_layout()
guardar(fig, "05_4_coeficientes_por_pliegue")

# %% 4. Diagnóstico del modelo elegido
titulo(f"4. DIAGNÓSTICO DEL MODELO ELEGIDO: {ELEGIDO}")
pred = fuera_de_muestra[ELEGIDO]
error = pred - train[Y]
por_anio = pd.DataFrame({
    "presidente": train.groupby("year")["pres_party"].first(),
    "MAE (pp)": error.abs().groupby(train["year"]).mean() * 100,
    "cuota D nacional real": train.groupby("year")["nat_house_dem_share_2p"].first(),
    "cuota D nacional predicha": (pred * votos_2p).groupby(train["year"]).sum()
                                 / votos_2p.groupby(train["year"]).sum(),
})
por_anio["error nacional (pp)"] = (por_anio["cuota D nacional predicha"]
                                   - por_anio["cuota D nacional real"]) * 100
print(por_anio.round(3).to_string())
por_anio.round(4).to_csv(SALIDAS / "predictivo_error_por_anio.csv")
print("El error nacional es la parte de la ola que el modelo no anticipa. Es chico (1–2 pp), pero")
print("negativo los 5 años: el modelo subestima al demócrata. Por eso se probó el sesgo partidario.")

fig, ax = plt.subplots(figsize=(6.5, 6.2))
ax.scatter(pred[~disputado], train.loc[~disputado, Y], s=34, facecolors="none", edgecolors=GRIS,
           linewidths=1.1, label="con distritos sin oposición")
ax.scatter(pred[disputado], train.loc[disputado, Y], s=34, color=VIOLETA, edgecolors="#fcfcfb",
           linewidths=0.8, label="todos disputados")
ax.plot([0, 1], [0, 1], color=TINTA_2, linewidth=1, linestyle="--")
ax.set_xlim(0.15, 0.95)
ax.set_ylim(0, 1.02)
ax.set_aspect("equal")
ax.set_xlabel("Cuota D predicha (sin ver ese medio término)")
ax.set_ylabel("Cuota D real")
ax.legend(loc="upper left", fontsize=8)
r2 = comparacion.loc[ELEGIDO, "R²"]
ax.set_title(f"Predicho vs real, fuera de muestra (R² = {r2:.2f})", fontsize=11)
guardar(fig, "05_2_predicho_vs_real")

fig, ax = plt.subplots(figsize=(8, 4))
colores = [AZUL_D if p == "D" else ROJO_R for p in por_anio["presidente"]]
ax.bar([f"{a}\npres. {p}" for a, p in por_anio["presidente"].items()],
       por_anio["error nacional (pp)"], color=colores, width=0.55, edgecolor="#fcfcfb", linewidth=2)
for i, v in enumerate(por_anio["error nacional (pp)"]):
    ax.text(i, v + (0.25 if v >= 0 else -0.25), f"{v:+.1f} pp", ha="center",
            va="bottom" if v >= 0 else "top", fontsize=9, color=TINTA)
ax.axhline(0, color=TINTA, linewidth=1)
ax.set_ylabel("Cuota D nacional: predicha − real (pp)")
ax.grid(axis="x", visible=False)
ax.set_ylim(por_anio["error nacional (pp)"].min() - 1.2, por_anio["error nacional (pp)"].max() + 1.2)
ax.set_title("Error en la cuota D nacional: chico, pero siempre del mismo lado")
guardar(fig, "05_3_error_nacional_por_anio")

# %% 5. De votos a bancas
titulo("5. CURVA VOTOS-BANCAS NACIONAL (11 elecciones, 2004–2024)")
# Recta de bancas D sobre la cuota D nacional. Su pendiente es el "swing ratio" (bancas por punto
# de voto) y su corte con 218 marca qué cuota necesita D para la mayoría con los mapas de cada época.
pares = pd.concat([
    train.groupby("year").agg(cuota=("nat_house_dem_share_2p", "first"), bancas=("house_seats_d", "sum")),
    datos.groupby("year").agg(cuota=("nat_house_dem_share_2p_prev", "first"),
                              bancas=("house_seats_d_prev", "sum")).rename(index=lambda a: a - 2),
]).sort_index()
pendiente_b, ordenada_b = np.polyfit(pares["cuota"], pares["bancas"], 1)
residuo_loo = pd.Series({
    a: pares.loc[a, "bancas"] - np.polyval(np.polyfit(pares.drop(a)["cuota"],
                                                      pares.drop(a)["bancas"], 1), pares.loc[a, "cuota"])
    for a in pares.index})
sd_curva = np.sqrt((residuo_loo ** 2).mean())
cuota_mayoria = (MAYORIA - ordenada_b) / pendiente_b
pares["bancas predichas (sin ese año)"] = pares["bancas"] - residuo_loo
print(pares.round(3).to_string())
pares.round(4).to_csv(SALIDAS / "predictivo_curva_bancas.csv")
print(f"\nbancas D = {ordenada_b:.1f} + {pendiente_b:.1f} x cuota D nacional")
print(f"  {pendiente_b / 100:.1f} bancas por punto de voto; D necesita {cuota_mayoria:.1%} para {MAYORIA}")
print(f"  Error dejando afuera cada elección: {sd_curva:.1f} bancas (RMSE)")
print("Por encima de 50 %: los mapas de 2012–2020 favorecían a R (2012: D 50,6 % y 201 bancas).")

# %% 6. Predicción 2026
titulo("6. PREDICCIÓN 2026 (presidente republicano)")
crear, columnas = MODELOS[ELEGIDO]
final = crear().fit(train[columnas], train["y_partido_pres"])
pred26["cuota_d_predicha"] = a_cuota_d(pred26, final.predict(pred26[columnas]))
pred26["cambio_vs_2024 (pp)"] = (pred26["cuota_d_predicha"] - pred26["house_dem_share_2p_prev"]) * 100
# Peso de cada estado en el voto nacional: votos D + R a la Cámara en el medio término 2022
peso26 = pred26["state"].map(train[train["year"] == 2022].set_index("state")
                             .eval("house_votes_d + house_votes_r"))
nacional26 = (pred26["cuota_d_predicha"] * peso26).sum() / peso26.sum()
bancas26 = ordenada_b + pendiente_b * nacional26
print(f"Cuota D nacional predicha: {nacional26:.1%}  (2024: {pred26['nat_house_dem_share_2p_prev'].iloc[0]:.1%})")
print(f"Bancas D esperadas: {bancas26:.0f} de 435  (mayoría: {MAYORIA}; 2024: "
      f"{pred26['house_seats_d_prev'].sum():.0f})")
print(f"Estados donde el voto D sube: {(pred26['cambio_vs_2024 (pp)'] > 0).sum()} de 50")
print(f"Estados con cuota D > 50 %: {(pred26['cuota_d_predicha'] > 0.5).sum()} "
      f"(2024: {(pred26['house_dem_share_2p_prev'] > 0.5).sum()})")

# Sensibilidad: el modelo de menor MAE, aunque no lo elija la regla de un error estándar
if mejor != ELEGIDO:
    crear_m, columnas_m = MODELOS[mejor]
    alt = a_cuota_d(pred26, crear_m().fit(train[columnas_m], train["y_partido_pres"])
                    .predict(pred26[columnas_m]))
    nacional_alt = (alt * peso26).sum() / peso26.sum()
    print(f"Sensibilidad ({mejor}): cuota D {nacional_alt:.1%}, "
          f"{ordenada_b + pendiente_b * nacional_alt:.0f} bancas D")

# %% 7. Incertidumbre por simulación
titulo("7. INCERTIDUMBRE (simulación de Monte Carlo)")
# Tres fuentes de error, medidas fuera de muestra: la ola nacional (una por año, desvío de los
# 5 errores nacionales), el desvío propio de cada estado una vez descontada la ola y el error de
# la curva votos-bancas.
sd_nacional = np.sqrt((por_anio["error nacional (pp)"] ** 2).mean()) / 100
sd_estado = (error - error.groupby(train["year"]).transform("mean")).std()
ola = rng.normal(0, sd_nacional, size=(SIMULACIONES, 1))
ruido = rng.normal(0, sd_estado, size=(SIMULACIONES, len(pred26)))
cuotas_sim = np.clip(pred26["cuota_d_predicha"].to_numpy() + ola + ruido, 0, 1)
nacional_sim = (cuotas_sim * peso26.to_numpy()).sum(axis=1) / peso26.sum()
bancas_sim = ordenada_b + pendiente_b * nacional_sim + rng.normal(0, sd_curva, SIMULACIONES)
p_mayoria = (bancas_sim >= MAYORIA).mean()
resumen = pd.Series({
    "cuota D nacional (mediana)": np.median(nacional_sim),
    "cuota D nacional (p10)": np.percentile(nacional_sim, 10),
    "cuota D nacional (p90)": np.percentile(nacional_sim, 90),
    "bancas D (mediana)": np.median(bancas_sim),
    "bancas D (p10)": np.percentile(bancas_sim, 10),
    "bancas D (p90)": np.percentile(bancas_sim, 90),
    "probabilidad de mayoría D": p_mayoria,
    "desvío de la ola nacional (pp)": sd_nacional * 100,
    "desvío propio de cada estado (pp)": sd_estado * 100,
    "error de la curva votos-bancas (bancas)": sd_curva,
})
print(resumen.round(3).to_string())
resumen.round(4).to_csv(SALIDAS / "predictivo_resumen_2026.csv", header=["valor"])
print("La ola nacional se estima con solo 5 medio término: el intervalo es orientativo.")

pred26[["state", "house_seats", "pres_dem_share_2p_prev", "house_dem_share_2p_prev",
        "cuota_d_predicha", "cambio_vs_2024 (pp)"]].sort_values(
    "cuota_d_predicha").round(4).to_csv(SALIDAS / "predictivo_estados_2026.csv", index=False)

fig, ax = plt.subplots(figsize=(8.5, 4.3))
# Bordes cada 3 bancas alineados con la mayoría: ninguna barra mezcla los dos colores
bordes = np.arange(MAYORIA - 3 * np.ceil((MAYORIA - bancas_sim.min()) / 3), bancas_sim.max() + 3, 3)
_, bordes, barras = ax.hist(bancas_sim, bins=bordes, edgecolor="#fcfcfb", linewidth=1.5)
for barra, izq in zip(barras, bordes[:-1]):
    barra.set_facecolor(AZUL_D if izq >= MAYORIA else ROJO_R)
ax.axvline(MAYORIA, color=TINTA, linewidth=1, linestyle="--")
ax.text(MAYORIA - 1.5, ax.get_ylim()[1] * 0.92, f"mayoría ({MAYORIA})", fontsize=9, color=TINTA,
        ha="right")
ax.axvline(np.median(bancas_sim), color=VIOLETA, linewidth=2)
ax.text(np.median(bancas_sim) + 1.5, ax.get_ylim()[1] * 0.97, f"mediana {np.median(bancas_sim):.0f}",
        fontsize=9, color=TINTA, va="top", bbox=dict(facecolor="#fcfcfb", edgecolor="none", pad=2))
ax.set_xlabel("Bancas demócratas en la Cámara (de 435)")
ax.set_ylabel("Simulaciones")
ax.grid(axis="x", visible=False)
ax.set_title(f"Bancas D en 2026: {SIMULACIONES:,} simulaciones · mayoría D en el "
             f"{p_mayoria:.0%}".replace(",", "."))
guardar(fig, "05_6_bancas_2026")

fig, ax = plt.subplots(figsize=(8, 5))
medio_termino = pares.index.isin(train["year"].unique())
ax.scatter(pares.loc[~medio_termino, "cuota"], pares.loc[~medio_termino, "bancas"], s=48,
           facecolors="#fcfcfb", edgecolors=GRIS, linewidths=1.5, label="presidencial", zorder=3)
ax.scatter(pares.loc[medio_termino, "cuota"], pares.loc[medio_termino, "bancas"], s=48, color=GRIS,
           edgecolors="#fcfcfb", linewidths=1, label="medio término", zorder=3)
for a, fila in pares.iterrows():
    ax.annotate(str(a), (fila["cuota"], fila["bancas"]), xytext=(6, -3), textcoords="offset points",
                fontsize=8, color=TINTA_2)
xs = np.linspace(0.455, 0.57, 2)
ax.plot(xs, ordenada_b + pendiente_b * xs, color=TINTA_2, linewidth=1.5, zorder=2)
p10, p90 = np.percentile(nacional_sim, [10, 90])
ax.errorbar(nacional26, bancas26, xerr=[[nacional26 - p10], [p90 - nacional26]], fmt="o",
            color=VIOLETA, markersize=10, markeredgecolor="#fcfcfb", markeredgewidth=2, capsize=4,
            linewidth=2, label="2026 predicho (p10–p90 del voto)", zorder=4)
ax.axhline(MAYORIA, color=TINTA, linewidth=1, linestyle="--")
ax.axvline(0.5, color=GRIS, linewidth=1, linestyle=":")
ax.text(0.457, MAYORIA + 2, f"mayoría ({MAYORIA})", fontsize=9, color=TINTA)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_xlabel("Cuota D nacional del voto bipartidista a la Cámara")
ax.set_ylabel("Bancas demócratas")
ax.legend(loc="lower right", fontsize=8)
ax.set_title(f"De votos a bancas: {pendiente_b / 100:.1f} bancas por punto; D necesita "
             f"{cuota_mayoria:.1%} para la mayoría", fontsize=11)
guardar(fig, "05_7_curva_votos_bancas")

fig, ax = plt.subplots(figsize=(7.5, 11))
orden26 = pred26.sort_values("cuota_d_predicha").reset_index(drop=True)
for i, fila in orden26.iterrows():
    ax.plot([fila["house_dem_share_2p_prev"], fila["cuota_d_predicha"]], [i, i], color="#d6d5cf",
            linewidth=2, zorder=1)
ax.scatter(orden26["house_dem_share_2p_prev"], orden26.index, s=36, facecolors="#fcfcfb",
           edgecolors=GRIS, linewidths=1.3, zorder=2, label="2024 (Cámara)")
ax.scatter(orden26["cuota_d_predicha"], orden26.index, s=48, zorder=3,
           color=[AZUL_D if v >= 0.5 else ROJO_R for v in orden26["cuota_d_predicha"]],
           edgecolors="#fcfcfb", linewidths=1, label="2026 predicho")
ax.axvline(0.5, color=TINTA_2, linewidth=1, linestyle="--")
ax.set_yticks(orden26.index, orden26["state"], fontsize=8)
ax.set_ylim(-1, len(orden26))
ax.grid(axis="y", visible=False)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_xlabel("Cuota demócrata bipartidista a la Cámara")
ax.legend(loc="lower right", fontsize=8)
ax.set_title("Predicción 2026 por estado (gris: resultado 2024)", fontsize=11)
guardar(fig, "05_5_prediccion_2026_estados")

print("\nConclusiones predictivas:")
print(" 1. Las tres hipótesis se sostienen al dejar afuera cualquier medio término: la presidencial")
print("    anticipa (H1), el partido del presidente pierde (H2) y el voto a la Cámara vuelve hacia")
print("    el 50 % (H3); sobre el voto presidencial el castigo es parejo.")
print(" 2. Error medio de 3,5 pp por estado (la línea base daba 4,3). Casi todo es propio de cada")
print("    estado; la ola nacional erra 1–2 pp, pero no se compensa entre estados y mueve las bancas.")
print(" 3. Para 2026 (presidente R) predice un desplazamiento hacia los demócratas.")
print(" No incluye encuestas, aprobación presidencial ni los mapas redibujados en 2025–2026.")
