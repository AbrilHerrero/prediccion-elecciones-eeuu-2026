"""Paso 1 — Carga e inspección inicial del dataset.

Verifica el entorno, carga el CSV con pandas y muestra su estructura: dimensiones,
primeras filas, tipos de dato, filas por año y los tres grupos de columnas
(contexto, predictores `_prev` y resultado).

Uso:  ../.venv/bin/python 01_carga_e_inspeccion.py
"""

# %% Entorno
import sys

import pandas as pd

from comun import cargar_dataset, titulo

titulo("1. ENTORNO")
print("Python:", sys.version.split()[0])
print("pandas:", pd.__version__)

# %% Carga
df = cargar_dataset()

titulo("2. DIMENSIONES")
print(f"{df.shape[0]} filas x {df.shape[1]} columnas")
print("Unidad de análisis: estado x elección de medio término")

# %% Primeras filas (df.head)
titulo("3. PRIMERAS FILAS  —  df.head()")
columnas_clave = ["year", "state", "split", "pres_party", "pres_dem_share_2p_prev",
                  "house_dem_share_2p_prev", "house_dem_share_2p", "president_party_swing"]
print(df[columnas_clave].head(10).to_string(index=False))

# %% Tipos de dato
titulo("4. TIPOS DE DATO  —  df.dtypes")
print(df.dtypes.value_counts().to_string())
print("\nColumnas de texto:", list(df.select_dtypes("object").columns))

# %% Grupos de columnas
titulo("5. GRUPOS DE COLUMNAS")
prev = [c for c in df.columns if c.endswith("_prev")]
print(f"Predictores de la presidencial anterior (_prev): {len(prev)}")
for c in prev:
    print("  ", c)
print("Las columnas sin sufijo describen la elección de medio término de la fila.")

# %% Filas por año y split
titulo("6. FILAS POR AÑO")
print(df.groupby(["year", "split", "pres_party"]).size().rename("filas").to_string())

print("\nLas filas 2026 (split = predict) tienen vacío el resultado:")
print("se excluyen de todo el análisis exploratorio.")
