"""Ejecuta en orden los cuatro pasos del modelo predictivo.

Uso:  python ejecutar_todo.py
"""

import runpy
from pathlib import Path

CARPETA = Path(__file__).parent
PASOS = ["05_validacion_cruzada.py", "06_curva_votos_bancas.py", "07_senado.py",
         "08_prediccion_2026.py"]

for paso in PASOS:
    print(f"\n\n########## {paso} ##########")
    runpy.run_path(str(CARPETA / paso), run_name="__main__")
