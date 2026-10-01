"""Paso 1 — Carga e inspección inicial del dataset.

Verifica el entorno, carga el CSV con pandas y muestra su estructura: dimensiones,
primeras filas, tipos de dato y cantidad de filas por año y por split.

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
print("Unidad de análisis: estado x año electoral")

# %% Primeras filas (df.head)
titulo("3. PRIMERAS FILAS  —  df.head()")
columnas_clave = ["year", "state", "split", "is_midterm", "pres_party",
                  "house_dem_share_2p", "house_seats_d", "house_seats_r", "pres_dem_share_2p_prev"]
print(df[columnas_clave].head(10).to_string(index=False))

# %% Tipos de dato
titulo("4. TIPOS DE DATO  —  df.dtypes")
print(df.dtypes.value_counts().to_string())
print("\nColumnas de texto:", list(df.select_dtypes("object").columns))

# %% Filas por año y split
titulo("5. FILAS POR AÑO")
print(df.groupby(["year", "split"]).size().rename("filas").to_string())

print("\nLas filas 2026 (split = predict) tienen vacías las variables objetivo:")
print("se excluyen de todo el análisis exploratorio.")
