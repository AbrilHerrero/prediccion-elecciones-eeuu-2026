"""Construye el dataset estado × elección de medio término (2006–2026).

Cada fila es un estado en un año de medio término. Las columnas sin sufijo son el resultado de
esa elección; las columnas `_prev` vienen de la elección presidencial dos años anterior, la
última información electoral disponible antes de votar.

Entradas:
    excelsMidterms/federalelections{2006,2010,2014,2018,2022}.xls[x]
        -> FEC, "Federal Elections" de cada año de medio término
    excelPres/federalelections{2004,2008,2012,2016,2020}.xls[x]
        -> FEC, "Federal Elections" de cada año presidencial
    excelPres/2024presgeresults.xlsx -> FEC, resultados presidenciales 2024
    excelPres/2024election_clerk.pdf -> Clerk of the House, "Statistics of the Presidential and
                                        Congressional Election of November 5, 2024"

Salida:
    dataset_midterms.csv  (las filas 2026 llevan split = "predict" y el resultado vacío)

Uso:
    .venv/bin/python construir_dataset_midterms.py
"""

import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pdfplumber

BASE = Path(__file__).parent
FUENTES_MIDTERMS = BASE / "excelsMidterms"
FUENTES_PRES = BASE / "excelPres"
SALIDA = BASE / "dataset_midterms.csv"

ESTADOS = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}

MIDTERMS = (2006, 2010, 2014, 2018, 2022)
A_PREDECIR = 2026

# Partido del presidente en ejercicio el día de cada elección de medio término.
PARTIDO_PRESIDENTE = {2006: "R", 2010: "D", 2014: "D", 2018: "R", 2022: "D", 2026: "R"}

# Bancas oficiales (D, R) de la Cámara por año. 2004: Sanders (VT) era independiente.
# 2018: NC-09 no se certificó (la elección se anuló y se repitió en 2019).
BANCAS_OFICIALES = {
    2004: (202, 232), 2006: (233, 202), 2008: (257, 178), 2010: (193, 242), 2012: (201, 234),
    2014: (188, 247), 2016: (194, 241), 2018: (235, 199), 2020: (222, 213), 2022: (213, 222),
    2024: (215, 220),
}
NO_CERTIFICADAS = {(2018, "NC", "09")}

# Senado 2026: clase II (los mismos estados de la elección ordinaria de 2020) + especiales OH y FL.
SENADO_2026 = {
    "AL", "AK", "AR", "CO", "DE", "GA", "ID", "IL", "IA", "KS", "KY", "LA", "ME", "MA", "MI",
    "MN", "MS", "MT", "NE", "NH", "NJ", "NM", "NC", "OK", "OR", "RI", "SC", "SD", "TN", "TX",
    "VA", "WV", "WY", "OH", "FL",
}

# Patrones de las hojas del FEC: sus nombres cambian de un año a otro.
HOJA_CAMARA = r"House (Votes )?by Party"
HOJA_SENADO = r"Senate (Votes )?by Party"
HOJA_PRESIDENTE = r"Elec\w* &\s*Pop"
HOJA_DISTRITOS = r"House.*Res"


# ---------------------------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------------------------

def num(valor):
    """Convierte una celda en número; devuelve 0 para vacío o texto no numérico."""
    v = pd.to_numeric(valor, errors="coerce")
    return 0 if pd.isna(v) else float(v)


def cuota_2p(d, r):
    """Proporción demócrata del voto bipartidista D / (D + R); NaN si ambos son cero."""
    total = d + r
    return (d / total).where(total > 0)


def libro_fec(anio):
    """Devuelve el libro Excel "Federal Elections" del FEC para un año entre 2004 y 2022."""
    carpeta = FUENTES_MIDTERMS if anio in MIDTERMS else FUENTES_PRES
    return pd.ExcelFile(next(carpeta.glob(f"federalelections{anio}.xls*")))


def hoja(libro, patron):
    """Devuelve el nombre de la única hoja del libro que coincide con el patrón.

    Lanza AssertionError si ninguna o más de una hoja coincide.
    """
    hojas = [h for h in libro.sheet_names if re.search(patron, h, re.I)]
    assert len(hojas) == 1, (patron, hojas)
    return hojas[0]


ETIQUETAS_D = {"D", "DEM", "DFL", "DNL"}    # DFL: Minnesota; DNL: Dakota del Norte (Democratic-NPL)
ETIQUETAS_R = {"R", "REP", "GOP"}


def familia(partido):
    """Clasifica un código de partido del FEC en "D", "R" u "O".

    Una etiqueta compuesta ("D/WF", "W(DEM)/DEM", "D(UND)") cuenta para el primer partido
    mayor que nombra, sin contar las partes de voto escrito a mano (W(...)), que solas
    cuentan como "O".
    """
    for parte in str(partido).upper().split("/"):
        parte = re.sub(r"[*#\s]", "", parte)
        if not parte.startswith("W"):
            parte = re.sub(r"\(.*\)$", "", parte)              # D(UND) -> D
        if parte in ETIQUETAS_D:
            return "D"
        if parte in ETIQUETAS_R:
            return "R"
    return "O"


def nombre_limpio(nombre):
    """Normaliza el nombre de un candidato para unir sus líneas de fusión (quita marcas de nota)."""
    return re.sub(r"\s+", " ", re.sub(r"[#*]", "", str(nombre))).strip()


# ---------------------------------------------------------------------------------------------
# FEC (2004–2022)
# ---------------------------------------------------------------------------------------------

def tabla_por_partido(libro, nombre_hoja):
    """Lee una tabla "votes cast by party" del FEC.

    Devuelve un DataFrame indexado por estado (solo los 50 estados con dato) con las columnas
    prim_d, prim_r, prim_o, ge_d, ge_r, ge_o.
    """
    x = pd.read_excel(libro, sheet_name=nombre_hoja, header=None)
    abreviaturas = x.apply(lambda c: c.astype(str).str.strip().str.rstrip("*"))
    col = next(c for c in x.columns if abreviaturas[c].isin(ESTADOS).sum() >= 20)
    es_estado = abreviaturas[col].isin(ESTADOS)
    x = x[es_estado].set_index(abreviaturas.loc[es_estado, col])
    assert x.index.is_unique, nombre_hoja
    x = x[[col + i for i in range(1, 7)]]
    x.columns = ["prim_d", "prim_r", "prim_o", "ge_d", "ge_r", "ge_o"]
    return x.apply(lambda c: c.map(num))


def presidente_fec(libro):
    """Lee el voto popular presidencial por estado.

    Devuelve un DataFrame indexado por estado con pres_votes_d, pres_votes_r y pres_votes_total.
    """
    x = pd.read_excel(libro, sheet_name=hoja(libro, HOJA_PRESIDENTE), header=None)
    cabecera = x.head(6).astype(str)

    def ultima_columna(texto):     # la última columna con ese rótulo es la del voto popular
        return max(c for c in x.columns if cabecera[c].str.contains(texto, regex=False).any())

    x[0] = x[0].astype(str).str.strip().str.rstrip("*")      # ME*, NE*: reparten electores
    x = x[x[0].isin(ESTADOS)].set_index(0)
    return pd.DataFrame({
        "pres_votes_d": x[ultima_columna("(D)")].map(num),
        "pres_votes_r": x[ultima_columna("(R)")].map(num),
        "pres_votes_total": x[ultima_columna("Total")].map(num),
    })


def distritos_fec(libro, anio):
    """Resume por estado los resultados por distrito de la Cámara.

    Las elecciones especiales por mandato incompleto celebradas el mismo día quedan afuera.
    En los distritos con balotaje (Luisiana, Georgia) cuentan los votos del balotaje, que es
    la vuelta que decide la banca.

    Devuelve un DataFrame indexado por estado con:
        house_votes_d/_r/_other  votos a la Cámara por partido; las líneas de fusión de otros
                                 partidos (WF, CON, IND) cuentan como "other"
        house_seats              distritos del estado
        house_seats_d/_r         bancas ganadas por cada partido
        house_districts_no_d     distritos sin candidato demócrata en la general (idem _no_r)
        house_districts_dr       distritos con candidato demócrata y republicano
    """
    x = pd.read_excel(libro, sheet_name=hoja(libro, HOJA_DISTRITOS), dtype=str)
    x.columns = [str(c).strip() for c in x.columns]
    col_distrito = "DISTRICT" if "DISTRICT" in x.columns else "D"
    col_nombre = next(c for c in ("CANDIDATE NAME", "LAST NAME, FIRST", "CANDIDATE NAME (Last, First)")
                      if c in x.columns)
    col_general = next(c for c in x.columns if c.startswith("GENERAL") and "%" not in c)
    cols_runoff = [c for c in x.columns if c.startswith("GE RUNOFF") and "%" not in c]

    x["estado"] = x["STATE ABBREVIATION"].str.strip()
    # Sin partido = fila de total combinado de un candidato de fusión (repite sus líneas).
    x = x[x["estado"].isin(ESTADOS) & x[col_nombre].notna() & x["PARTY"].notna()].copy()
    distrito = x[col_distrito].fillna("").str.strip()
    x["distrito"] = distrito.str.extract(r"^(\d+)", expand=False)          # descarta Senado
    x["especial"] = distrito.str.contains(r"\*|UNEXPIRED", case=False)      # mandato incompleto
    x = x[x["distrito"].notna()]
    x["familia"] = x["PARTY"].map(familia)
    x["candidato"] = x[col_nombre].map(nombre_limpio)
    x["votos"] = x[col_general].map(num)
    x["ganador_fec"] = (x["GE WINNER INDICATOR"].fillna("").str.strip().eq("W")
                        if "GE WINNER INDICATOR" in x else False)       # marcado desde 2012
    x["sin_rival"] = x[col_general].fillna("").str.strip().str.startswith("Unopposed")
    x["votos_runoff"] = x[cols_runoff].apply(lambda c: c.map(num)).sum(axis=1) if cols_runoff else 0.0

    filas = []
    for (estado, numero), g in x[~x["especial"]].groupby(["estado", "distrito"]):
        en_general = g[(g["votos"] > 0) | g["sin_rival"]]
        assert not en_general.empty, (anio, estado, numero)
        # Un candidato puede figurar en varias líneas de partido (fusión): se suman sus votos.
        candidatos = en_general.groupby("candidato").agg(
            votos=("votos", "sum"), runoff=("votos_runoff", "sum"), sin_rival=("sin_rival", "any"),
            ganador_fec=("ganador_fec", "any"),
            familia=("familia", lambda s: "D" if "D" in set(s) else "R" if "R" in set(s) else "O"),
        )
        # Orden de prioridad: marca de ganador del FEC (cubre el voto preferencial de Maine),
        # candidato sin rival, balotaje y, por último, más votos en la general.
        if candidatos["ganador_fec"].any():
            ganador = candidatos[candidatos["ganador_fec"]]
        elif candidatos["sin_rival"].any():
            ganador = candidatos[candidatos["sin_rival"]]
        elif candidatos["runoff"].sum() > 0:
            ganador = candidatos.sort_values("runoff", ascending=False)
        else:
            ganador = candidatos.sort_values("votos", ascending=False)
        presentes = set(candidatos["familia"])
        certificada = (anio, estado, numero) not in NO_CERTIFICADAS
        decisivos = g["votos_runoff"] if g["votos_runoff"].sum() > 0 else g["votos"]
        por_familia = decisivos.groupby(g["familia"]).sum()
        filas.append(dict(state=estado, ganador=ganador["familia"].iloc[0] if certificada else None,
                          sin_d="D" not in presentes, sin_r="R" not in presentes,
                          dr={"D", "R"} <= presentes,
                          **{f"votos_{f}": por_familia.get(f, 0.0) for f in "DRO"}))

    resumen = pd.DataFrame(filas).groupby("state").agg(
        house_seats=("ganador", "size"),
        house_seats_d=("ganador", lambda s: (s == "D").sum()),
        house_seats_r=("ganador", lambda s: (s == "R").sum()),
        house_districts_no_d=("sin_d", "sum"),
        house_districts_no_r=("sin_r", "sum"),
        house_districts_dr=("dr", "sum"),
        house_votes_d=("votos_D", "sum"),
        house_votes_r=("votos_R", "sum"),
        house_votes_other=("votos_O", "sum"),
    )
    return resumen


def eleccion_fec(anio):
    """Devuelve los resultados por estado de un año del FEC (2004–2022).

    DataFrame indexado por estado con votos y bancas de la Cámara, votos en las internas a la
    Cámara, votos al Senado (NaN si el estado no eligió senador) y, en años presidenciales,
    votos a presidente.
    """
    libro = libro_fec(anio)
    camara = tabla_por_partido(libro, hoja(libro, HOJA_CAMARA))
    senado = tabla_por_partido(libro, hoja(libro, HOJA_SENADO))
    df = distritos_fec(libro, anio).reindex(sorted(ESTADOS))
    df["house_primary_votes_d"] = camara["prim_d"]
    df["house_primary_votes_r"] = camara["prim_r"]
    df = df.join(senado[["ge_d", "ge_r", "ge_o"]].rename(columns={
        "ge_d": "senate_votes_d", "ge_r": "senate_votes_r", "ge_o": "senate_votes_other"}))
    if anio % 4 == 0:
        df = df.join(presidente_fec(libro))
    return df


# ---------------------------------------------------------------------------------------------
# 2024: FEC (presidente) y Clerk de la Cámara (PDF)
# ---------------------------------------------------------------------------------------------

TERRITORIOS = {"DISTRICT OF COLUMBIA", "GUAM", "PUERTO RICO", "AMERICAN SAMOA", "VIRGIN ISLANDS",
               "NORTHERN MARIANA ISLANDS"}


def presidente_2024():
    """Lee el voto popular presidencial 2024 por estado (FEC, 2024presgeresults.xlsx)."""
    x = pd.read_excel(FUENTES_PRES / "2024presgeresults.xlsx")
    x = x[x["STATE"].isin(ESTADOS)].set_index("STATE")
    return pd.DataFrame({
        "pres_votes_d": x["HARRIS"].map(num),
        "pres_votes_r": x["TRUMP"].map(num),
        "pres_votes_total": x["TOTAL VOTES"].map(num),
    })


def lineas_rotadas(pagina):
    """Reconstruye como texto las filas de una tabla impresa rotada 90° en una página del PDF."""
    filas = defaultdict(list)
    for c in pagina.chars:
        if not c["upright"]:
            filas[round(c["x0"])].append(c)
    agrupadas = []
    for x0 in sorted(filas):
        if agrupadas and x0 - agrupadas[-1][0] <= 2:
            agrupadas[-1][1].extend(filas[x0])
        else:
            agrupadas.append([x0, list(filas[x0])])
    salida = []
    for _, chars in agrupadas:
        chars.sort(key=lambda c: -c["top"])
        texto, previo = "", None
        for c in chars:
            if previo is not None and previo["top"] - c["bottom"] > 2.5:
                texto += " | "
            texto += c["text"]
            previo = c
        salida.append(re.sub(r"\.{3,}", "…", texto).replace("\xa0", " "))
    return salida


def recapitulacion_clerk(lineas):
    """Interpreta una tabla "Recapitulation of Votes Cast" del Clerk.

    Devuelve un DataFrame indexado por estado con ge_d, ge_r, ge_o y ge_total.
    Lanza AssertionError si una fila no suma su propio total.
    """
    nombres = {v: k for k, v in ESTADOS.items()}
    filas = {}
    for linea in lineas:
        estado = next((n for n in nombres if linea.startswith(n + " …")), None)
        if estado is None:
            continue
        resto = linea[len(estado):].replace("|", " ").strip()
        resto = resto[1:] if resto.startswith("…") else resto                # puntos guía
        celdas = [0.0 if t == "…" else float(t.replace(",", ""))
                  for t in re.findall(r"[\d,]+|…", resto)]
        assert len(celdas) == 9, (estado, celdas)
        rep, dem, *otros, total = celdas
        assert abs(rep + dem + sum(otros) - total) < 1, estado
        filas[nombres[estado]] = dict(ge_r=rep, ge_d=dem, ge_o=sum(otros), ge_total=total)
    return pd.DataFrame.from_dict(filas, orient="index")


def familia_clerk(partido):
    """Clasifica la etiqueta de partido del Clerk en "D", "R" u "O"."""
    p = partido.strip().lower()
    if p.startswith("republican"):
        return "R"
    if p.startswith("democrat"):
        return "D"
    return "O"


def distritos_clerk(texto):
    """Resume por estado los resultados 2024 por distrito del documento del Clerk.

    Devuelve un DataFrame indexado por estado con las mismas columnas de bancas y distritos que
    distritos_fec, más boletas_sin_voto (en blanco, nulas, sobre/sub votos y rondas de voto
    preferencial, que el Clerk suma en la columna "Other" de su tabla).
    """
    mayus = {v.upper(): k for k, v in ESTADOS.items()}
    no_voto = re.compile(r"^(Blank|Void|Under ?Votes|Over ?Votes|Continuing Ballots|"
                         r"Exhausted Ballots)", re.I)
    no_candidato = re.compile(r"^(Scattering|Scattered|Write-in|Total|None of these)", re.I)
    boletas_sin_voto = defaultdict(int)
    resultados = defaultdict(lambda: defaultdict(list))
    estado, en_seccion, distrito = None, False, None
    for linea in texto.split("\n"):
        linea = linea.strip()
        m = re.match(r"^([A-Z][A-Z ]+?)(—Continued)?$", linea)
        if m and (m.group(1) in mayus or m.group(1) in TERRITORIOS):
            nuevo = mayus.get(m.group(1))                              # None para territorios
            if nuevo != estado:
                distrito = None
            estado, en_seccion = nuevo, False
            continue
        if linea.startswith("FOR "):
            en_seccion = linea.startswith("FOR UNITED STATES REPRESENTATIVE")
            continue
        if linea.startswith("Recapitulation"):
            en_seccion = False
            continue
        if not en_seccion or estado is None:
            continue
        linea = re.sub(r"\.{3,}\s*\(1\)$", "... 0", linea)      # sin oposición: no figura en boleta
        m = re.match(r"^(?:(\d+)\.\s+)?(.+?)\s*\.{3,}\s*([\d,]+)$", linea)
        if not m:
            continue
        numero, nombre, votos = m.group(1), m.group(2), int(m.group(3).replace(",", ""))
        distrito = numero or distrito or "AL"
        if no_voto.match(nombre):
            boletas_sin_voto[estado] += votos
            continue
        if no_candidato.match(nombre):
            continue
        candidatos = resultados[estado][distrito]
        if "," in nombre and len(nombre.split(",")[0].split()) >= 2:
            candidatos.append([familia_clerk(nombre.rsplit(",", 1)[1]), votos])
        elif candidatos:
            candidatos[-1][1] += votos                               # línea de fusión (NY, CT)
    filas = {}
    for est, dist in resultados.items():
        ganadores = [max(c, key=lambda v: v[1])[0] for c in dist.values()]
        presentes = [{f for f, _ in c} for c in dist.values()]
        filas[est] = dict(
            house_seats=len(dist),
            house_seats_d=ganadores.count("D"),
            house_seats_r=ganadores.count("R"),
            house_districts_no_d=sum("D" not in p for p in presentes),
            house_districts_no_r=sum("R" not in p for p in presentes),
            house_districts_dr=sum({"D", "R"} <= p for p in presentes),
            boletas_sin_voto=boletas_sin_voto[est],
        )
    return pd.DataFrame.from_dict(filas, orient="index")


def eleccion_2024():
    """Devuelve los resultados por estado de 2024: Cámara (Clerk) y presidente (FEC)."""
    with pdfplumber.open(FUENTES_PRES / "2024election_clerk.pdf") as pdf:
        rotadas = [lineas_rotadas(p) for p in pdf.pages
                   if sum(not c["upright"] for c in p.chars) > len(p.chars) / 2]
        texto = "\n".join((p.extract_text() or "") for p in pdf.pages)
    camara = next(recapitulacion_clerk(lineas) for lineas in rotadas
                  if "Recapitulation of Votes Cast for United States Representatives" in " ".join(lineas[:1]))
    dist = distritos_clerk(texto)
    df = pd.DataFrame(index=sorted(ESTADOS))
    df["house_votes_d"] = camara["ge_d"]
    df["house_votes_r"] = camara["ge_r"]
    df["house_votes_other"] = (camara["ge_o"] - dist["boletas_sin_voto"]).clip(lower=0)
    df = df.join(dist.drop(columns="boletas_sin_voto")).join(presidente_2024())
    return df


# ---------------------------------------------------------------------------------------------
# Armado del dataset
# ---------------------------------------------------------------------------------------------

def con_derivadas(df):
    """Agrega a los resultados de un año las cuotas, las referencias nacionales y los desvíos."""
    df = df.copy()
    df["house_votes_total"] = df[["house_votes_d", "house_votes_r", "house_votes_other"]].sum(axis=1)
    df["house_dem_share_2p"] = cuota_2p(df["house_votes_d"], df["house_votes_r"])
    df["house_seat_share_d"] = df["house_seats_d"] / df["house_seats"]
    df["house_contested_share"] = df["house_districts_dr"] / df["house_seats"]
    df["nat_house_dem_share_2p"] = df["house_votes_d"].sum() / (df["house_votes_d"].sum() + df["house_votes_r"].sum())
    df["house_dem_share_2p_rel"] = df["house_dem_share_2p"] - df["nat_house_dem_share_2p"]
    if "house_primary_votes_d" in df:
        df["house_primary_dem_share_2p"] = cuota_2p(df["house_primary_votes_d"], df["house_primary_votes_r"])
    if "senate_votes_d" in df:
        tot = df[["senate_votes_d", "senate_votes_r", "senate_votes_other"]].sum(axis=1, min_count=1)
        df["senate_race"] = (tot > 0).astype(int)
        df.loc[df["senate_race"] == 0, ["senate_votes_d", "senate_votes_r", "senate_votes_other"]] = float("nan")
        df["senate_dr_contest"] = ((df["senate_votes_d"] > 0) & (df["senate_votes_r"] > 0)).astype(int)
        df["senate_dem_share_2p"] = cuota_2p(df["senate_votes_d"], df["senate_votes_r"]).where(df["senate_dr_contest"] == 1)
    if "pres_votes_d" in df:
        df["pres_dem_share_2p"] = cuota_2p(df["pres_votes_d"], df["pres_votes_r"])
        df["nat_pres_dem_share_2p"] = df["pres_votes_d"].sum() / (df["pres_votes_d"].sum() + df["pres_votes_r"].sum())
        df["pres_dem_share_2p_rel"] = df["pres_dem_share_2p"] - df["nat_pres_dem_share_2p"]
        df["house_dropoff"] = 1 - df["house_votes_total"] / df["pres_votes_total"]
    return df


def controlar_bancas(anio, df):
    """Verifica distritos y bancas reconstruidos contra las cifras oficiales del año.

    Lanza AssertionError si el total de distritos no es 435 o si las bancas por partido no
    coinciden con BANCAS_OFICIALES.
    """
    assert df["house_seats"].sum() == 435, (anio, df["house_seats"].sum())
    obtenidas = (int(df["house_seats_d"].sum()), int(df["house_seats_r"].sum()))
    assert obtenidas == BANCAS_OFICIALES[anio], (anio, obtenidas, BANCAS_OFICIALES[anio])


PREDICTORES_PREV = [
    "pres_dem_share_2p", "pres_dem_share_2p_rel", "nat_pres_dem_share_2p",
    "house_dem_share_2p", "house_dem_share_2p_rel", "nat_house_dem_share_2p",
    "house_seats_d", "house_seats_r", "house_seat_share_d", "house_contested_share", "house_dropoff",
]

COLUMNAS = [
    # Identificación y contexto
    "year", "state", "state_name", "split", "pres_party", "house_seats", "senate_race",
    # Predictores: elección presidencial anterior (dos años antes)
    "pres_dem_share_2p_prev", "pres_dem_share_2p_rel_prev", "nat_pres_dem_share_2p_prev",
    "house_dem_share_2p_prev", "house_dem_share_2p_rel_prev", "nat_house_dem_share_2p_prev",
    "house_seats_d_prev", "house_seats_r_prev", "house_seat_share_d_prev", "house_contested_share_prev",
    "house_dropoff_prev",
    # Previas a la general del mismo año
    "house_primary_votes_d", "house_primary_votes_r", "house_primary_dem_share_2p",
    "house_districts_no_d", "house_districts_no_r", "house_contested_share",
    # Resultado: Cámara
    "house_votes_d", "house_votes_r", "house_votes_other", "house_votes_total",
    "house_dem_share_2p", "house_dem_share_2p_rel", "nat_house_dem_share_2p",
    "president_party_house_share_2p", "house_dem_swing", "president_party_swing",
    "house_seats_d", "house_seats_r", "house_seat_share_d",
    # Resultado: Senado
    "senate_dr_contest", "senate_votes_d", "senate_votes_r", "senate_votes_other",
    "senate_dem_share_2p",
]


def construir():
    """Arma el dataset estado × medio término y lo escribe en SALIDA.

    Devuelve el DataFrame resultante. Lanza AssertionError si los distritos o las bancas
    reconstruidas de algún año no coinciden con las cifras oficiales.
    """
    anios = sorted({a for m in MIDTERMS for a in (m - 2, m)} | {A_PREDECIR - 2})
    resultados = {}
    for anio in anios:
        crudo = eleccion_2024() if anio == 2024 else eleccion_fec(anio)
        controlar_bancas(anio, crudo)
        resultados[anio] = con_derivadas(crudo)

    bloques = []
    for anio in (*MIDTERMS, A_PREDECIR):
        previo = resultados[anio - 2][PREDICTORES_PREV].add_suffix("_prev")
        if anio == A_PREDECIR:
            actual = pd.DataFrame(index=sorted(ESTADOS))
            actual["house_seats"] = resultados[anio - 2]["house_seats"]   # mismo censo (2020)
            actual["senate_race"] = actual.index.isin(SENADO_2026).astype(int)
        else:
            actual = resultados[anio]
        bloque = actual.join(previo)
        bloque["year"] = anio
        bloques.append(bloque)

    df = pd.concat(bloques).rename_axis("state").reset_index()
    df["state_name"] = df["state"].map(ESTADOS)
    df["split"] = (df["year"] == A_PREDECIR).map({True: "predict", False: "train"})
    df["pres_party"] = df["year"].map(PARTIDO_PRESIDENTE)
    del_presidente = df["pres_party"] == "D"
    df["president_party_house_share_2p"] = df["house_dem_share_2p"].where(del_presidente, 1 - df["house_dem_share_2p"])
    df["house_dem_swing"] = df["house_dem_share_2p"] - df["house_dem_share_2p_prev"]
    df["president_party_swing"] = df["house_dem_swing"].where(del_presidente, -df["house_dem_swing"])

    df = df.reindex(columns=COLUMNAS).sort_values(["year", "state"])
    enteras = [c for c in COLUMNAS if c.startswith(("house_votes", "senate_votes", "house_primary_votes",
                                                     "house_seats", "house_districts"))
               and "share" not in c]
    df[enteras] = df[enteras].round().astype("Int64")
    df.to_csv(SALIDA, index=False, float_format="%.4f")
    return df


if __name__ == "__main__":
    tabla = construir()
    print(f"{SALIDA.name}: {len(tabla)} filas × {tabla.shape[1]} columnas")
