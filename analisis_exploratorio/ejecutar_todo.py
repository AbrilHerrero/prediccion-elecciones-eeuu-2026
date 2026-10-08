"""Ejecuta en orden los cinco pasos del análisis: exploratorio y predictivo.

Uso:  ../.venv/bin/python ejecutar_todo.py
"""

import runpy
from pathlib import Path

CARPETA = Path(__file__).parent
PASOS = ["01_carga_e_inspeccion.py", "02_preprocesamiento.py", "03_descriptivo.py",
         "04_exploratorio.py", "05_predictivo.py"]

for paso in PASOS:
    print(f"\n\n########## {paso} ##########")
    runpy.run_path(str(CARPETA / paso), run_name="__main__")
