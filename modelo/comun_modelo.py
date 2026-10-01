"""Rutas, constantes y funciones compartidas por los scripts del modelo predictivo.

Reutiliza la paleta y el estilo gráfico de ../analisis_exploratorio/comun.py.
"""

import sys
from pathlib import Path

CARPETA_MODELO = Path(__file__).parent
sys.path.append(str(CARPETA_MODELO.parent / "analisis_exploratorio"))

# comun va primero: configura matplotlib para guardar PNG sin abrir ventanas.
from comun import (AZUL_D, DATASET, GRIS, GRIS_NEUTRO, ROJO_R, TINTA, TINTA_2,  # noqa: E402,F401
                   VIOLETA, estilo, titulo)

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.linear_model import LinearRegression, LogisticRegression  # noqa: E402
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict  # noqa: E402

FIGURAS_MODELO = CARPETA_MODELO / "figuras"
SALIDAS_MODELO = CARPETA_MODELO / "salidas"
FIGURAS_MODELO.mkdir(exist_ok=True)
SALIDAS_MODELO.mkdir(exist_ok=True)

# 2016 no tiene ciclo anterior en el panel (2014 no está incluido): se valida sobre 2018–2024.
ANIOS_CON_CICLO_ANTERIOR = [2018, 2020, 2022, 2024]

BANCAS_PARA_MAYORIA_CAMARA = 218
# Con el vicepresidente (R) desempatando, los demócratas necesitan 51 bancas.
BANCAS_PARA_MAYORIA_SENADO = 51
# Senadores que no renuevan en 2026 (119.º Congreso: 53 R, 45 D + 2 independientes que votan
# con los D). Renuevan la clase 2 (20 R, 13 D) y las especiales de Ohio y Florida (2 R).
# Los independientes (King, Sanders) se cuentan como D.
SENADORES_QUE_NO_RENUEVAN_2026 = {"D": 34, "R": 31}

# Estados con mapa de distritos nuevo para 2026 según fundamentacion_dataset.md (sección 9).
# La curva votos-bancas usa el mapa de 2024, así que en estos estados las bancas son menos
# confiables. Verificar el estado final de cada mapa antes de citar resultados.
ESTADOS_CON_MAPA_NUEVO_2026 = ["TX", "CA", "MO", "NC", "OH", "UT"]

# Elegidos en 05_validacion_cruzada.py: menor error con el modelo más simple de interpretar.
PREDICTORES_CAMARA = ["pres_dem_share_2p_rel_prev", "house_dem_share_2p_rel_lag"]
OBJETIVO_CAMARA = "house_dem_share_2p_rel"   # inclinación del estado respecto del país
PREDICTORES_SENADO = ["pres_dem_share_2p_rel_prev"]
PREDICTORES_BANCAS = ["ventaja_democrata_en_votos", "cuota_bancas_d_ciclo_anterior"]

NOMBRES_LEGIBLES = {
    "pres_dem_share_2p_rel_prev": "inclinación presidencial previa",
    "house_dem_share_2p_rel_lag": "inclinación a la Cámara en el ciclo anterior",
    "distritos_disputados_ciclo_anterior": "distritos disputados en el ciclo anterior",
    "ventaja_democrata_en_votos": "ventaja D en votos (cuota − 0,5)",
    "cuota_bancas_d_ciclo_anterior": "proporción de bancas D en el ciclo anterior",
}


def crear_modelo_camara():
    """Modelo elegido para la inclinación de cada estado en el voto a la Cámara."""
    return LinearRegression()


def crear_modelo_senado():
    """Modelo para la ventaja del candidato D al Senado sobre el voto nacional a la Cámara."""
    return LinearRegression()


def cargar_tabla_completa():
    """Dataset completo (2016–2026) con las columnas derivadas que usa el modelo.

    Todas las columnas nuevas miran al ciclo anterior, así que también existen para 2026.
    """
    tabla = pd.read_csv(DATASET).sort_values(["state", "year"]).reset_index(drop=True)
    por_estado = tabla.groupby("state")
    bancas_del_estado_ciclo_anterior = por_estado["house_seats"].shift()
    tabla["cuota_bancas_d_ciclo_anterior"] = (tabla["house_seats_d_lag"]
                                              / bancas_del_estado_ciclo_anterior)
    tabla["cuota_nacional_ciclo_anterior"] = por_estado["nat_house_dem_share_2p"].shift()
    tabla["distritos_disputados_ciclo_anterior"] = por_estado["house_contested_share"].shift()
    return tabla


def filas_de_entrenamiento(tabla):
    """Filas 2018–2024: tienen resultado y ciclo anterior."""
    return tabla[(tabla["split"] == "train")
                 & tabla["year"].isin(ANIOS_CON_CICLO_ANTERIOR)].copy()


def filas_2026(tabla):
    return tabla[tabla["split"] == "predict"].copy()


def elecciones_al_senado_d_contra_r(filas):
    """Elecciones al Senado con un D contra un R, sin independientes fuertes (los votos 'otros'
    superaron al candidato D: King en Maine, Osborn en Nebraska, la especial apartidaria de
    Mississippi 2018). Agrega la ventaja del candidato D sobre el voto nacional a la Cámara."""
    elecciones = filas[(filas["senate_dr_contest"] == 1) & filas["senate_dem_share_2p"].notna()]
    hubo_independiente_fuerte = elecciones["senate_votes_other"] > elecciones["senate_votes_d"]
    elecciones = elecciones[~hubo_independiente_fuerte].copy()
    elecciones["ventaja_candidato_d_senado"] = (elecciones["senate_dem_share_2p"]
                                                - elecciones["nat_house_dem_share_2p"])
    return elecciones


def predecir_dejando_un_anio_afuera(modelo, filas, predictores, objetivo):
    """Para cada año, entrena con los demás y predice ese año. Simula predecir una elección
    que el modelo no vio. Devuelve una Serie alineada con `filas`."""
    prediccion = cross_val_predict(modelo, filas[predictores], filas[objetivo],
                                   groups=filas["year"], cv=LeaveOneGroupOut())
    return pd.Series(prediccion, index=filas.index)


def error_medio_en_puntos(prediccion, real):
    """Error absoluto medio en puntos porcentuales."""
    return (prediccion - real).abs().mean() * 100


# --- Curva votos-bancas -----------------------------------------------------------------

def predictores_de_bancas(cuota_democrata, filas):
    return pd.DataFrame({
        "ventaja_democrata_en_votos": cuota_democrata - 0.5,
        "cuota_bancas_d_ciclo_anterior": filas["cuota_bancas_d_ciclo_anterior"],
    }, index=filas.index)


def ajustar_curva_votos_bancas(filas, predictores=PREDICTORES_BANCAS):
    """Regresión logística sobre bancas individuales: cada estado-año aporta una fila
    'ganó D' con peso = bancas D y una fila 'ganó R' con peso = bancas R."""
    ganadas_d = filas.assign(gano_d=1, peso=filas["house_seats_d"])
    ganadas_r = filas.assign(gano_d=0, peso=filas["house_seats_r"])
    bancas_individuales = pd.concat([ganadas_d, ganadas_r])
    bancas_individuales = bancas_individuales[bancas_individuales["peso"] > 0]
    tabla_x = predictores_de_bancas(bancas_individuales["house_dem_share_2p"],
                                    bancas_individuales)[predictores]
    curva = LogisticRegression(C=1e6)   # C alto: prácticamente sin regularización
    curva.fit(tabla_x, bancas_individuales["gano_d"], sample_weight=bancas_individuales["peso"])
    return curva


def bancas_d_esperadas(curva, cuota_democrata, filas, predictores=PREDICTORES_BANCAS):
    """Bancas D esperadas por estado = bancas del estado × probabilidad de que una gane D."""
    tabla_x = predictores_de_bancas(cuota_democrata, filas)[predictores]
    probabilidad_banca_d = curva.predict_proba(tabla_x)[:, 1]
    return pd.Series(probabilidad_banca_d * filas["house_seats"].to_numpy(), index=filas.index)


def guardar(fig, nombre):
    """Guarda la figura como figuras/<nombre>.png, la cierra e informa la ruta."""
    ruta = FIGURAS_MODELO / f"{nombre}.png"
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> figura guardada: {ruta.relative_to(CARPETA_MODELO)}")
