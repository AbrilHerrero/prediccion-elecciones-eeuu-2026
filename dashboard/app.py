"""Dashboard de la predicción 2026: una API con FastAPI y una página estática que la consume.

Al arrancar entrena los modelos finales (tarda menos de un segundo) y después recalcula la
predicción para el clima nacional que elija el usuario.

Requiere haber ejecutado ../modelo/ejecutar_todo.py (lee las salidas de validación).
Uso:  python app.py   y abrir http://127.0.0.1:8000
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

CARPETA_DASHBOARD = Path(__file__).parent
CARPETA_MODELO = CARPETA_DASHBOARD.parent / "modelo"
sys.path.append(str(CARPETA_MODELO))

from comun_modelo import (BANCAS_PARA_MAYORIA_CAMARA, BANCAS_PARA_MAYORIA_SENADO,  # noqa: E402
                          SALIDAS_MODELO, SENADORES_QUE_NO_RENUEVAN_2026)
from motor_de_prediccion import (ESCENARIO_CENTRAL, entrenar_modelos_para_2026,  # noqa: E402
                                 escenarios_de_clima_nacional, predecir_con_clima_nacional)

GANANCIA_MINIMA_PP = -4.0
GANANCIA_MAXIMA_PP = 10.0
PASO_DEL_BARRIDO_PP = 0.5

modelos_2026 = entrenar_modelos_para_2026()
escenarios = escenarios_de_clima_nacional(modelos_2026)


def tabla_a_registros(tabla):
    """DataFrame -> lista de dicts apta para JSON (NaN -> null, tipos de numpy -> Python)."""
    return json.loads(tabla.to_json(orient="records"))


def resumen_a_json(resumen):
    return {clave: float(valor) for clave, valor in resumen.items()}


def calcular_barrido_de_climas():
    """Resumen nacional para cada clima entre el mínimo y el máximo, cada medio punto."""
    ganancias_pp = np.arange(GANANCIA_MINIMA_PP, GANANCIA_MAXIMA_PP + 0.001, PASO_DEL_BARRIDO_PP)
    barrido = []
    for ganancia_pp in ganancias_pp:
        resumen, _ = predecir_con_clima_nacional(modelos_2026, ganancia_pp / 100,
                                                 cantidad_de_simulaciones=5_000)
        barrido.append({"ganancia_democrata_pp": round(float(ganancia_pp), 2),
                        **resumen_a_json(resumen)})
    return barrido


barrido_de_climas = calcular_barrido_de_climas()

app = FastAPI(title="Predicción elecciones EE. UU. 2026")
app.mount("/static", StaticFiles(directory=CARPETA_DASHBOARD / "static"), name="static")


@app.get("/")
def pagina_principal():
    return FileResponse(CARPETA_DASHBOARD / "static" / "index.html")


@app.get("/api/contexto")
def contexto():
    """Datos fijos: escenarios, mayorías, antecedentes y validación de los modelos."""
    perdidas = modelos_2026["perdidas_del_presidente_en_medio_termino"]
    return {
        "cuota_nacional_2024": float(modelos_2026["cuota_nacional_2024"]),
        "perdidas_del_presidente_en_medio_termino": {
            int(anio): float(perdida) for anio, perdida in perdidas.items()},
        "escenarios": [{"nombre": nombre, "ganancia_democrata_pp": round(ganancia * 100, 2)}
                       for nombre, ganancia in escenarios.items()],
        "escenario_central": ESCENARIO_CENTRAL,
        "ganancia_minima_pp": GANANCIA_MINIMA_PP,
        "ganancia_maxima_pp": GANANCIA_MAXIMA_PP,
        "bancas_para_mayoria_camara": BANCAS_PARA_MAYORIA_CAMARA,
        "bancas_para_mayoria_senado": BANCAS_PARA_MAYORIA_SENADO,
        "senadores_que_no_renuevan": SENADORES_QUE_NO_RENUEVAN_2026,
        "error_historico_en_bancas": float(modelos_2026["error_historico_en_bancas"]),
        "desvio_del_error_senado_pp": float(
            modelos_2026["desvio_del_error_senado_por_estado"] * 100),
        "comparacion_de_modelos": tabla_a_registros(
            pd.read_csv(SALIDAS_MODELO / "comparacion_modelos_camara.csv")),
        "validacion_bancas": tabla_a_registros(
            pd.read_csv(SALIDAS_MODELO / "validacion_bancas_camara.csv")),
    }


@app.get("/api/prediccion")
def prediccion(ganancia_democrata_pp: float = Query(
        4.0, ge=GANANCIA_MINIMA_PP, le=GANANCIA_MAXIMA_PP,
        description="Puntos de cuota nacional que ganan los demócratas respecto de 2024")):
    resumen, por_estado = predecir_con_clima_nacional(modelos_2026, ganancia_democrata_pp / 100)
    return {"resumen": resumen_a_json(resumen),
            "estados": tabla_a_registros(por_estado.reset_index())}


@app.get("/api/barrido")
def barrido():
    """Bancas esperadas para todo el rango de climas (para los gráficos de líneas)."""
    return barrido_de_climas


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
