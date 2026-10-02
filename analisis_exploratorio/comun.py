"""Rutas, carga de datos y estilo gráfico compartidos por los scripts del análisis exploratorio."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # los gráficos se guardan como PNG en figuras/
import matplotlib.pyplot as plt
import pandas as pd

CARPETA = Path(__file__).parent
DATASET = CARPETA.parent / "dataset_midterms.csv"
FIGURAS = CARPETA / "figuras"
SALIDAS = CARPETA / "salidas"
PREPROCESADO = SALIDAS / "dataset_preprocesado.csv"

FIGURAS.mkdir(exist_ok=True)
SALIDAS.mkdir(exist_ok=True)

# Colores (paleta validada para daltonismo). Partido: convención azul D / rojo R.
AZUL_D = "#2a78d6"
ROJO_R = "#e34948"
VIOLETA = "#4a3aa7"   # subconjunto o período destacado
GRIS = "#898781"      # referencia / resto de los datos
GRIS_NEUTRO = "#f0efec"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
GRILLA = "#e1e0d9"

# Escala divergente rojo -> gris -> azul para cuotas demócratas (0 = R, 1 = D)
DIVERGENTE = matplotlib.colors.LinearSegmentedColormap.from_list(
    "rojo_azul", [ROJO_R, GRIS_NEUTRO, AZUL_D]
)

# Etiquetas legibles para las variables que se grafican
ETIQUETAS = {
    "house_dem_share_2p": "Cuota D Cámara",
    "house_dem_share_2p_prev": "Cuota D Cámara (presidencial anterior)",
    "pres_dem_share_2p_prev": "Cuota D Presidente (presidencial anterior)",
    "house_seat_share_d_prev": "Proporción de bancas D (presidencial anterior)",
    "house_primary_dem_share_2p": "Cuota D internas",
    "house_contested_share": "Distritos disputados D vs R",
    "house_dropoff_prev": "Roll-off Cámara (presidencial anterior)",
    "senate_dem_share_2p": "Cuota D Senado (mismo día)",
    "house_seat_share_d": "Proporción de bancas D",
    "house_dem_swing": "Swing D",
    "president_party_swing": "Swing del partido del presidente",
    "partido_pres_camara_prev": "Cuota del partido del presidente en la Cámara (presidencial anterior)",
}


def estilo():
    """Aplica el estilo gráfico común (grilla tenue, ejes discretos, tipografía del sistema)."""
    plt.rcParams.update({
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "figure.facecolor": "#fcfcfb",
        "axes.facecolor": "#fcfcfb",
        "axes.edgecolor": "#c3c2b7",
        "axes.labelcolor": TINTA_2,
        "axes.titlecolor": TINTA,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRILLA,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "xtick.color": GRIS,
        "ytick.color": GRIS,
        "legend.frameon": False,
        "font.family": "sans-serif",
    })


def cargar_dataset():
    """Devuelve el dataset completo (filas de entrenamiento 2006–2022 y de predicción 2026)."""
    return pd.read_csv(DATASET)


def cargar_preprocesado():
    """Devuelve el dataset preprocesado por 02_preprocesamiento.py.

    Lanza FileNotFoundError si todavía no se ejecutó ese script.
    """
    if not PREPROCESADO.exists():
        raise FileNotFoundError("Primero ejecutá 02_preprocesamiento.py")
    return pd.read_csv(PREPROCESADO)


def guardar(fig, nombre):
    """Guarda la figura como figuras/<nombre>.png, la cierra e informa la ruta."""
    ruta = FIGURAS / f"{nombre}.png"
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> figura guardada: {ruta.relative_to(CARPETA)}")


def titulo(texto):
    """Imprime un encabezado de sección en consola."""
    print("\n" + "=" * 70 + f"\n{texto}\n" + "=" * 70)
