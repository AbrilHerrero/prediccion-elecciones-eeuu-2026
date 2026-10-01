"""Entrenamiento de los modelos finales y predicción de 2026 para un clima nacional dado.

Lo usan 08_prediccion_2026.py (escenarios fijos) y el dashboard (clima elegido por el usuario).
Requiere haber ejecutado 06 y 07: de sus salidas toma el error histórico en bancas y el
desvío del error por estado en el Senado.
"""

import numpy as np
import pandas as pd

from comun_modelo import (BANCAS_PARA_MAYORIA_SENADO, ESTADOS_CON_MAPA_NUEVO_2026,
                          OBJETIVO_CAMARA, PREDICTORES_CAMARA, PREDICTORES_SENADO, SALIDAS_MODELO,
                          SENADORES_QUE_NO_RENUEVAN_2026, ajustar_curva_votos_bancas,
                          bancas_d_esperadas, cargar_tabla_completa, crear_modelo_camara,
                          crear_modelo_senado, elecciones_al_senado_d_contra_r,
                          filas_de_entrenamiento, filas_2026)

ESCENARIO_CENTRAL = "promedio de 2018 y 2022"


def leer_salida_de_validacion(nombre_archivo, script_que_la_genera):
    ruta = SALIDAS_MODELO / nombre_archivo
    if not ruta.exists():
        raise FileNotFoundError(f"Falta {ruta}: primero ejecutá {script_que_la_genera}")
    return pd.read_csv(ruta)


def perdidas_del_presidente_en_medio_termino(tabla):
    """Cambio de la cuota nacional del partido del presidente en cada medio término."""
    cuota_nacional_por_anio = tabla[tabla["split"] == "train"].groupby("year")[
        ["nat_house_dem_share_2p", "is_midterm", "pres_party"]].first()
    cambio_nacional_d = cuota_nacional_por_anio["nat_house_dem_share_2p"].diff()
    signo_del_presidente = np.where(cuota_nacional_por_anio["pres_party"] == "D", 1, -1)
    cambio_del_partido_del_presidente = cambio_nacional_d * signo_del_presidente
    return cambio_del_partido_del_presidente[cuota_nacional_por_anio["is_midterm"] == 1]


def entrenar_modelos_para_2026():
    """Entrena los modelos con 2018–2024 y devuelve todo lo necesario para predecir 2026."""
    tabla = cargar_tabla_completa()
    entrenamiento = filas_de_entrenamiento(tabla)
    estados_2026 = filas_2026(tabla).set_index("state")

    validacion_bancas = leer_salida_de_validacion("validacion_bancas_camara.csv",
                                                  "06_curva_votos_bancas.py")
    validacion_senado = leer_salida_de_validacion("validacion_senado.csv", "07_senado.py")

    modelo_camara = crear_modelo_camara().fit(entrenamiento[PREDICTORES_CAMARA],
                                              entrenamiento[OBJETIVO_CAMARA])
    inclinacion_camara_2026 = pd.Series(
        modelo_camara.predict(estados_2026[PREDICTORES_CAMARA]), index=estados_2026.index)
    # La cuota nacional es el promedio de los estados ponderado por votos. Se centra la
    # inclinación con los votos de 2024 para que el país sume exactamente el clima elegido.
    votos_bipartidistas_2024 = (tabla[tabla["year"] == 2024].set_index("state")
                                [["house_votes_d", "house_votes_r"]].sum(axis=1))
    correccion_de_centrado = np.average(
        inclinacion_camara_2026, weights=votos_bipartidistas_2024[inclinacion_camara_2026.index])

    elecciones_d_contra_r = elecciones_al_senado_d_contra_r(entrenamiento)
    modelo_senado = crear_modelo_senado().fit(elecciones_d_contra_r[PREDICTORES_SENADO],
                                              elecciones_d_contra_r["ventaja_candidato_d_senado"])
    estados_con_senado_2026 = estados_2026[estados_2026["senate_race"] == 1]
    ventaja_candidato_d_senado_2026 = pd.Series(
        modelo_senado.predict(estados_con_senado_2026[PREDICTORES_SENADO]),
        index=estados_con_senado_2026.index)

    perdidas = perdidas_del_presidente_en_medio_termino(tabla)
    return {
        "estados_2026": estados_2026,
        "inclinacion_camara_2026": inclinacion_camara_2026 - correccion_de_centrado,
        "correccion_de_centrado": correccion_de_centrado,
        "ventaja_candidato_d_senado_2026": ventaja_candidato_d_senado_2026,
        "curva_votos_bancas": ajustar_curva_votos_bancas(entrenamiento),
        "cuota_nacional_2024": tabla.loc[tabla["year"] == 2024, "nat_house_dem_share_2p"].iloc[0],
        "perdidas_del_presidente_en_medio_termino": perdidas,
        "error_historico_en_bancas": (validacion_bancas["B_cadena_completa"]
                                      - validacion_bancas["bancas_d_reales"]).abs().mean(),
        "desvio_del_error_senado_por_estado": validacion_senado["residuo"].std(),
    }


def escenarios_de_clima_nacional(modelos_2026):
    """Ganancia de los demócratas (la oposición) respecto de 2024, por escenario."""
    ganancia_media_de_la_oposicion = -modelos_2026["perdidas_del_presidente_en_medio_termino"].mean()
    return {
        "sin efecto de medio término": 0.0,
        "efecto moderado": 0.02,
        ESCENARIO_CENTRAL: round(ganancia_media_de_la_oposicion, 4),
        "ola demócrata": 0.06,
    }


def predecir_con_clima_nacional(modelos_2026, ganancia_democrata,
                                cantidad_de_simulaciones=20_000, semilla=2026):
    """Predice Cámara y Senado 2026 si los demócratas ganan `ganancia_democrata` (en
    proporción, 0.04 = 4 puntos) de cuota nacional respecto de 2024.

    Devuelve (resumen nacional como dict, tabla por estado como DataFrame).
    """
    estados_2026 = modelos_2026["estados_2026"]
    cuota_nacional = modelos_2026["cuota_nacional_2024"] + ganancia_democrata

    cuota_d_camara = (cuota_nacional + modelos_2026["inclinacion_camara_2026"]).clip(0, 1)
    bancas_d_por_estado = bancas_d_esperadas(modelos_2026["curva_votos_bancas"], cuota_d_camara,
                                             estados_2026)
    bancas_d_camara = bancas_d_por_estado.sum()
    error_historico = modelos_2026["error_historico_en_bancas"]

    # Senado: se simula el error de cada elección (independiente entre estados) con el desvío
    # medido en 07, y se cuenta en cuántas simulaciones los D llegan a la mayoría.
    cuota_d_senado = cuota_nacional + modelos_2026["ventaja_candidato_d_senado_2026"]
    generador_aleatorio = np.random.default_rng(semilla)
    error_simulado = generador_aleatorio.normal(
        0, modelos_2026["desvio_del_error_senado_por_estado"],
        size=(cantidad_de_simulaciones, len(cuota_d_senado)))
    victorias_d_simuladas = (cuota_d_senado.to_numpy() + error_simulado) > 0.5
    probabilidad_victoria_d = pd.Series(victorias_d_simuladas.mean(axis=0),
                                        index=cuota_d_senado.index)
    senadores_d_simulados = (SENADORES_QUE_NO_RENUEVAN_2026["D"]
                             + victorias_d_simuladas.sum(axis=1))

    resumen = {
        "ganancia_democrata": ganancia_democrata,
        "cuota_d_nacional": cuota_nacional,
        "camara_bancas_d_esperadas": bancas_d_camara,
        "camara_rango_inferior": bancas_d_camara - error_historico,
        "camara_rango_superior": bancas_d_camara + error_historico,
        "senado_bancas_d_esperadas": senadores_d_simulados.mean(),
        "senado_probabilidad_control_d": (senadores_d_simulados
                                          >= BANCAS_PARA_MAYORIA_SENADO).mean(),
    }
    por_estado = pd.DataFrame({
        "state_name": estados_2026["state_name"],
        "house_seats": estados_2026["house_seats"],
        "camara_cuota_d_prevista": cuota_d_camara,
        "camara_bancas_d_esperadas": bancas_d_por_estado,
        "mapa_nuevo_2026": estados_2026.index.isin(ESTADOS_CON_MAPA_NUEVO_2026),
        "senado_cuota_d_prevista": cuota_d_senado,
        "senado_probabilidad_victoria_d": probabilidad_victoria_d,
    })
    por_estado.index.name = "state"
    return resumen, por_estado
