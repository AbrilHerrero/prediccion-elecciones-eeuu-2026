"""Construye el dataset estado × ciclo electoral (2016–2026) para predecir las elecciones de medio término 2026.

Entradas (en la carpeta excelsElecciones/):
    federalelections2016.xlsx, federalelections2018.xlsx, federalelections2020.xlsx,
    federalelections2022.xlsx  -> FEC, "Federal Elections" (resultados oficiales certificados)
    2024presgeresults.xlsx     -> FEC, resultados presidenciales 2024
    2024election_clerk.pdf     -> Clerk of the House, "Statistics of the Presidential and
                                  Congressional Election of November 5, 2024"

Salida:
    dataset_elecciones_estado.csv  (una fila por estado y año; las filas 2026 llevan las
                                    variables objetivo vacías y split = "predict")

Uso:
    .venv/bin/python construir_dataset.py
"""

import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pdfplumber

BASE = Path(__file__).parent
FUENTES = BASE / "excelsElecciones"
SALIDA = BASE / "dataset_elecciones_estado.csv"

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

# Bancas por estado según los censos 2010 (elecciones 2012–2020) y 2020 (2022–2030).
BANCAS_2010 = {
    "AL": 7, "AK": 1, "AZ": 9, "AR": 4, "CA": 53, "CO": 7, "CT": 5, "DE": 1, "FL": 27, "GA": 14,
    "HI": 2, "ID": 2, "IL": 18, "IN": 9, "IA": 4, "KS": 4, "KY": 6, "LA": 6, "ME": 2, "MD": 8,
    "MA": 9, "MI": 14, "MN": 8, "MS": 4, "MO": 8, "MT": 1, "NE": 3, "NV": 4, "NH": 2, "NJ": 12,
    "NM": 3, "NY": 27, "NC": 13, "ND": 1, "OH": 16, "OK": 5, "OR": 5, "PA": 18, "RI": 2, "SC": 7,
    "SD": 1, "TN": 9, "TX": 36, "UT": 4, "VT": 1, "VA": 11, "WA": 10, "WV": 3, "WI": 8, "WY": 1,
}
BANCAS_2020 = {
    **BANCAS_2010,
    "CA": 52, "CO": 8, "FL": 28, "IL": 17, "MI": 13, "MT": 2, "NY": 26, "NC": 14, "OH": 15,
    "OR": 6, "PA": 17, "TX": 38, "WV": 2,
}

# Partido del presidente en ejercicio el día de la elección.
PARTIDO_PRESIDENTE = {2016: "D", 2018: "R", 2020: "R", 2022: "D", 2024: "D", 2026: "R"}

# Senado 2026: clase II (los mismos estados de la elección ordinaria de 2020) + especiales OH y FL.
SENADO_2026 = {
    "AL", "AK", "AR", "CO", "DE", "GA", "ID", "IL", "IA", "KS", "KY", "LA", "ME", "MA", "MI",
    "MN", "MS", "MT", "NE", "NH", "NJ", "NM", "NC", "OK", "OR", "RI", "SC", "SD", "TN", "TX",
    "VA", "WV", "WY", "OH", "FL",
}

# Elecciones generales no certificadas (NC-09 2018 se repitió en 2019): la banca no se asigna.
NO_CERTIFICADAS = {(2018, "NC", "09")}

# Hojas del FEC: tabla de votos por partido para Cámara y Senado, y detalle por distrito.
FEC = {
    2016: dict(archivo="federalelections2016.xlsx", camara="Table 7. House by Party",
               senado="Table 6. Senate by Party", distritos="2016 US House Results by State",
               presidente="Table 2. Electoral &  Pop Vote"),
    2018: dict(archivo="federalelections2018.xlsx", camara="Table 5. House by Party",
               senado="Table 4. Senate by Party", distritos="2018 US House Results by State"),
    2020: dict(archivo="federalelections2020.xlsx", camara="8. Table 7 House by Party",
               senado="7. Table 6 Senate by Party", distritos="13. US House Results by State",
               presidente="3. Table 2 Electoral & Pop Vote"),
    2022: dict(archivo="federalelections2022.xlsx", camara="6. Table 5 House by Party",
               senado="5. Table 4 Senate by Party", distritos="8. US House Results by State"),
}


def estado_limpio(col):
    """Normaliza la columna de estado de una tabla del FEC (quita espacios y asteriscos de nota)."""
    return col.astype(str).str.strip().str.rstrip("*")


def num(valor):
    """Convierte una celda del FEC en número; devuelve 0 para vacío o texto no numérico."""
    v = pd.to_numeric(valor, errors="coerce")
    return 0 if pd.isna(v) else float(v)


def tabla_por_partido(archivo, hoja):
    """Lee una tabla "votes cast by party" del FEC.

    Devuelve un DataFrame indexado por abreviatura de estado (solo los 50 estados) con las
    columnas prim_d, prim_r, prim_o, ge_d, ge_r, ge_o.
    """
    x = pd.read_excel(FUENTES / archivo, sheet_name=hoja, header=None)
    x[0] = estado_limpio(x[0])
    x = x[x[0].isin(ESTADOS)].set_index(0).iloc[:, :6]
    x.columns = ["prim_d", "prim_r", "prim_o", "ge_d", "ge_r", "ge_o"]
    return x.apply(lambda col: col.map(num))


def familia_fec(partido):
    """Clasifica un código de partido del FEC en "D", "R" u "O" (candidaturas de fusión incluidas)."""
    p = str(partido).strip()
    if p in ("D", "DFL", "D/R") or p.startswith(("D/", "D*")):
        return "D"
    if p == "R" or p.startswith(("R/", "R*")):
        return "R"
    return "O"


def distritos_fec(anio):
    """Resume la hoja de resultados por distrito del FEC para un año.

    Devuelve un DataFrame indexado por estado con house_seats_d, house_seats_r, los conteos
    de distritos sin candidatura demócrata (house_districts_no_d) o republicana
    (house_districts_no_r) en la elección general, y los votos D/R/otros de las elecciones
    especiales por mandato incompleto celebradas el mismo día (especial_d, especial_r, especial_o).
    """
    cfg = FEC[anio]
    x = pd.read_excel(FUENTES / cfg["archivo"], sheet_name=cfg["distritos"], dtype=str)
    x.columns = [str(c).strip() for c in x.columns]
    col_d = "D" if "D" in x.columns else "DISTRICT"
    x = x[x["STATE ABBREVIATION"].isin(ESTADOS) & x[col_d].notna() & x["PARTY"].notna()].copy()
    x = x[x["CANDIDATE NAME"].notna() & ~x["TOTAL VOTES"].fillna("").str.contains("Votes")]
    x["familia"] = x["PARTY"].map(familia_fec)
    x["votos_ge"] = x["GENERAL VOTES"].map(num)
    especiales = x[x[col_d].str.upper().str.contains("UNEXPIRED")]  # vacantes, mismo día
    votos_especiales = especiales.pivot_table(index="STATE ABBREVIATION", columns="familia",
                                              values="votos_ge", aggfunc="sum")
    x = x[~x.index.isin(especiales.index)]
    x["distrito"] = x[col_d].str.extract(r"(\d+)", expand=False)
    runoff = [c for c in x.columns if c.startswith("GE RUNOFF ELECTION VOTES")][0]
    x["votos_runoff"] = x[runoff].map(num)
    x["ganador"] = x["GE WINNER INDICATOR"].fillna("").str.strip().eq("W")

    filas = []
    for (estado, distrito), g in x.groupby(["STATE ABBREVIATION", "distrito"]):
        certificada = (anio, estado, distrito) not in NO_CERTIFICADAS
        ganadores = g[g["ganador"] & g["familia"].isin(["D", "R"])]
        if ganadores.empty:
            # Sin marca de ganador: decide el balotaje si existió, si no el voto general.
            col = "votos_runoff" if g["votos_runoff"].sum() > 0 else "votos_ge"
            ganadores = g.sort_values(col, ascending=False)
        presentes = set(g.loc[g["votos_ge"] > 0, "familia"])
        filas.append(dict(state=estado, ganador=ganadores["familia"].iloc[0] if certificada else None,
                          sin_d="D" not in presentes, sin_r="R" not in presentes))
    d = pd.DataFrame(filas)
    resumen = d.groupby("state").agg(
        house_seats_d=("ganador", lambda s: (s == "D").sum()),
        house_seats_r=("ganador", lambda s: (s == "R").sum()),
        house_districts_no_d=("sin_d", "sum"),
        house_districts_no_r=("sin_r", "sum"),
    )
    for fam in "DRO":
        col = votos_especiales[fam] if fam in votos_especiales else pd.Series(dtype=float)
        resumen[f"especial_{fam.lower()}"] = col.reindex(resumen.index).fillna(0)
    return resumen


def presidente_fec(anio):
    """Lee el voto popular presidencial por estado del FEC (2016 o 2020).

    Devuelve un DataFrame indexado por estado con pres_votes_d, pres_votes_r, pres_votes_total.
    """
    cfg = FEC[anio]
    x = pd.read_excel(FUENTES / cfg["archivo"], sheet_name=cfg["presidente"], header=None)
    cab = x.iloc[3].astype(str)
    col_d = [i for i, c in cab.items() if "(D)" in c][1]                # la 2.ª es voto popular
    col_r = [i for i, c in cab.items() if "(R)" in c][1]
    x[0] = estado_limpio(x[0])
    x = x[x[0].isin(ESTADOS)].set_index(0)
    return pd.DataFrame({
        "pres_votes_d": x[col_d].map(num),
        "pres_votes_r": x[col_r].map(num),
        "pres_votes_total": x[6].map(num),
    })


def presidente_2024():
    """Lee el voto popular presidencial 2024 por estado (FEC, 2024presgeresults.xlsx)."""
    x = pd.read_excel(FUENTES / "2024presgeresults.xlsx")
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
    """Interpreta una tabla "Recapitulation of Votes Cast" del Clerk (Senado o Cámara 2024).

    Devuelve un DataFrame indexado por estado con ge_d, ge_r, ge_o y ge_total.
    Columnas de la tabla: Republican, Democratic, Independent, Libertarian, Green,
    Constitution, Other Parties, Write-in, Total.
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


TERRITORIOS = {"DISTRICT OF COLUMBIA", "GUAM", "PUERTO RICO", "AMERICAN SAMOA", "VIRGIN ISLANDS",
               "NORTHERN MARIANA ISLANDS"}


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

    Devuelve un DataFrame indexado por estado con house_seats_d, house_seats_r,
    house_districts_no_d, house_districts_no_r y boletas_sin_voto (en blanco, nulas, sobre/sub
    votos y rondas de voto preferencial, que el Clerk suma en la columna "Other" de la tabla).
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
        filas[est] = dict(
            house_seats_d=ganadores.count("D"),
            house_seats_r=ganadores.count("R"),
            house_districts_no_d=sum("D" not in {f for f, _ in c} for c in dist.values()),
            house_districts_no_r=sum("R" not in {f for f, _ in c} for c in dist.values()),
            boletas_sin_voto=boletas_sin_voto[est],
        )
    return pd.DataFrame.from_dict(filas, orient="index")


def datos_clerk_2024():
    """Extrae del PDF del Clerk los totales 2024 de Cámara y Senado y el detalle por distrito."""
    with pdfplumber.open(FUENTES / "2024election_clerk.pdf") as pdf:
        rotadas = {i: lineas_rotadas(p) for i, p in enumerate(pdf.pages)
                   if sum(not c["upright"] for c in p.chars) > len(p.chars) / 2}
        texto = "\n".join((p.extract_text() or "") for p in pdf.pages)
    senado = camara = None
    for lineas in rotadas.values():
        titulo = " ".join(lineas[:1])
        if "Recapitulation of Votes Cast for United States Senators" in titulo:
            senado = recapitulacion_clerk(lineas)
        elif "Recapitulation of Votes Cast for United States Representatives" in titulo:
            camara = recapitulacion_clerk(lineas)
    return camara, senado, distritos_clerk(texto)


def cuota_2p(d, r):
    """Proporción demócrata del voto bipartidista D / (D + R); NaN si ambos son cero."""
    total = d + r
    return (d / total).where(total > 0)


def construir():
    """Arma el panel estado × año y lo escribe en SALIDA.

    Devuelve el DataFrame resultante. Lanza AssertionError si las bancas reconstruidas no
    coinciden con las oficiales o si alguna tabla del Clerk no suma su propio total.
    """
    filas = []
    for anio in (2016, 2018, 2020, 2022):
        cfg = FEC[anio]
        camara = tabla_por_partido(cfg["archivo"], cfg["camara"])
        senado = tabla_por_partido(cfg["archivo"], cfg["senado"])
        dist = distritos_fec(anio)
        pres = presidente_fec(anio) if "presidente" in cfg else None
        for est in ESTADOS:
            resumen = dist.loc[est].to_dict()
            esp = {f: resumen.pop(f"especial_{f}") for f in "dro"}
            fila = dict(year=anio, state=est,
                        house_votes_d=camara.at[est, "ge_d"] - esp["d"],
                        house_votes_r=camara.at[est, "ge_r"] - esp["r"],
                        house_votes_other=camara.at[est, "ge_o"] - esp["o"],
                        house_primary_votes_d=camara.at[est, "prim_d"],
                        house_primary_votes_r=camara.at[est, "prim_r"],
                        senate_votes_d=senado.at[est, "ge_d"], senate_votes_r=senado.at[est, "ge_r"],
                        senate_votes_other=senado.at[est, "ge_o"],
                        **resumen)
            if pres is not None:
                fila.update(pres.loc[est].to_dict())
            filas.append(fila)

    camara24, senado24, dist24 = datos_clerk_2024()
    pres24 = presidente_2024()
    for est in ESTADOS:
        resumen = dist24.loc[est].to_dict()
        sin_voto = resumen.pop("boletas_sin_voto")
        fila = dict(year=2024, state=est,
                    house_votes_d=camara24.at[est, "ge_d"], house_votes_r=camara24.at[est, "ge_r"],
                    house_votes_other=max(camara24.at[est, "ge_o"] - sin_voto, 0),
                    **resumen, **pres24.loc[est].to_dict())
        if est in senado24.index:
            fila.update(senate_votes_d=senado24.at[est, "ge_d"],
                        senate_votes_r=senado24.at[est, "ge_r"],
                        senate_votes_other=senado24.at[est, "ge_o"])
        filas.append(fila)

    for est in ESTADOS:
        filas.append(dict(year=2026, state=est))

    df = pd.DataFrame(filas)
    df.insert(1, "state_name", df["state"].map(ESTADOS))

    # Contexto del ciclo
    df["is_midterm"] = (df["year"] % 4 == 2).astype(int)
    df["pres_party"] = df["year"].map(PARTIDO_PRESIDENTE)
    df["house_seats"] = [BANCAS_2010[s] if y <= 2020 else BANCAS_2020[s]
                         for s, y in zip(df["state"], df["year"])]
    df["split"] = df["year"].map(lambda y: "predict" if y == 2026 else "train")

    # Cámara: totales y cuotas
    df["house_votes_total"] = df[["house_votes_d", "house_votes_r", "house_votes_other"]].sum(axis=1, min_count=1)
    df["house_dem_share_2p"] = cuota_2p(df["house_votes_d"], df["house_votes_r"])
    df["house_margin_d"] = (df["house_votes_d"] - df["house_votes_r"]) / df["house_votes_total"]
    df["house_seat_share_d"] = df["house_seats_d"] / df["house_seats"]
    df["house_contested_share"] = 1 - (df[["house_districts_no_d", "house_districts_no_r"]].sum(axis=1, min_count=1) / df["house_seats"])
    df["house_primary_dem_share_2p"] = cuota_2p(df["house_primary_votes_d"], df["house_primary_votes_r"])

    # Senado: solo hay dato cuando hubo elección en el estado
    tot_sen = df[["senate_votes_d", "senate_votes_r", "senate_votes_other"]].sum(axis=1, min_count=1)
    df["senate_race"] = (tot_sen > 0).astype(int)
    df.loc[df["year"] == 2026, "senate_race"] = df["state"].isin(SENADO_2026).astype(int)
    df.loc[tot_sen.fillna(0) == 0, ["senate_votes_d", "senate_votes_r", "senate_votes_other"]] = float("nan")
    df["senate_dr_contest"] = ((df["senate_votes_d"] > 0) & (df["senate_votes_r"] > 0)).astype(int)
    df["senate_dem_share_2p"] = cuota_2p(df["senate_votes_d"], df["senate_votes_r"]).where(df["senate_dr_contest"] == 1)
    df.loc[df["year"] == 2026, "senate_dr_contest"] = float("nan")

    # Presidencial
    df["pres_dem_share_2p"] = cuota_2p(df["pres_votes_d"], df["pres_votes_r"])
    df["house_dropoff"] = 1 - df["house_votes_total"] / df["pres_votes_total"]

    # Referencias nacionales (suma de los 50 estados) y desvíos del estado respecto de ellas
    nac = df.groupby("year")[["house_votes_d", "house_votes_r", "pres_votes_d", "pres_votes_r"]].sum(min_count=1)
    nac["nat_house_dem_share_2p"] = cuota_2p(nac["house_votes_d"], nac["house_votes_r"])
    nac["nat_pres_dem_share_2p"] = cuota_2p(nac["pres_votes_d"], nac["pres_votes_r"])
    df = df.merge(nac[["nat_house_dem_share_2p", "nat_pres_dem_share_2p"]], left_on="year", right_index=True, how="left")
    df["house_dem_share_2p_rel"] = df["house_dem_share_2p"] - df["nat_house_dem_share_2p"]
    df["pres_dem_share_2p_rel"] = df["pres_dem_share_2p"] - df["nat_pres_dem_share_2p"]
    df["president_party_house_share_2p"] = df["house_dem_share_2p"].where(df["pres_party"] == "D", 1 - df["house_dem_share_2p"])

    # Rezagos: ciclo anterior de Cámara y última presidencial estrictamente anterior
    df = df.sort_values(["state", "year"]).reset_index(drop=True)
    g = df.groupby("state")
    df["house_dem_share_2p_lag"] = g["house_dem_share_2p"].shift(1)
    df["house_dem_share_2p_rel_lag"] = g["house_dem_share_2p_rel"].shift(1)
    df["house_seats_d_lag"] = g["house_seats_d"].shift(1)
    df["house_dem_swing"] = df["house_dem_share_2p"] - df["house_dem_share_2p_lag"]
    df["pres_dem_share_2p_prev"] = g["pres_dem_share_2p"].transform(lambda s: s.shift(1).ffill())
    df["pres_dem_share_2p_rel_prev"] = g["pres_dem_share_2p_rel"].transform(lambda s: s.shift(1).ffill())

    # Controles contra cifras oficiales
    bancas = df[df["split"] == "train"].groupby("year")[["house_seats_d", "house_seats_r"]].sum()
    oficiales = {2016: (194, 241), 2018: (235, 199), 2020: (222, 213), 2022: (213, 222), 2024: (215, 220)}
    for anio, (d, r) in oficiales.items():
        assert tuple(bancas.loc[anio].astype(int)) == (d, r), (anio, tuple(bancas.loc[anio]))

    columnas = [
        "year", "state", "state_name", "split", "is_midterm", "pres_party", "house_seats",
        "house_votes_d", "house_votes_r", "house_votes_other", "house_votes_total",
        "house_dem_share_2p", "house_margin_d", "house_dem_share_2p_rel",
        "president_party_house_share_2p",
        "house_seats_d", "house_seats_r", "house_seat_share_d",
        "house_districts_no_d", "house_districts_no_r", "house_contested_share",
        "house_primary_votes_d", "house_primary_votes_r", "house_primary_dem_share_2p",
        "senate_race", "senate_dr_contest", "senate_votes_d", "senate_votes_r", "senate_votes_other",
        "senate_dem_share_2p",
        "pres_votes_d", "pres_votes_r", "pres_votes_total", "pres_dem_share_2p", "pres_dem_share_2p_rel",
        "house_dropoff", "nat_house_dem_share_2p", "nat_pres_dem_share_2p",
        "house_dem_share_2p_lag", "house_dem_share_2p_rel_lag", "house_dem_swing", "house_seats_d_lag",
        "pres_dem_share_2p_prev", "pres_dem_share_2p_rel_prev",
    ]
    df = df[columnas].sort_values(["year", "state"])
    enteras = [c for c in columnas if c.startswith(("house_votes", "senate_votes", "pres_votes",
                                                     "house_primary_votes", "house_seats",
                                                     "house_districts"))]
    df[enteras] = df[enteras].round().astype("Int64")
    df.to_csv(SALIDA, index=False, float_format="%.4f")
    return df


if __name__ == "__main__":
    tabla = construir()
    print(f"{SALIDA.name}: {len(tabla)} filas × {tabla.shape[1]} columnas")
