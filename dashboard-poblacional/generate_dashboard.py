"""
Dashboard de proyecciones poblacionales de Argentina (2028-2035).

Script Python que carga datos de los últimos 4 censos nacionales (1991, 2001, 2010, 2022),
ajusta regresión exponencial por provincia, y genera un archivo HTML estático autocontenido
con gráficos Plotly interactivos.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

# ---------------------------------------------------------------------------
# 1. Configuration Layer
# ---------------------------------------------------------------------------

ZONAS: dict[str, list[str]] = {
    "Norte": [
        "Jujuy",
        "Salta",
        "Tucumán",
        "Catamarca",
        "La Rioja",
        "Santiago del Estero",
        "Chaco",
        "Formosa",
        "Corrientes",
        "Misiones",
    ],
    "Este/Centro": ["Buenos Aires", "CABA", "Córdoba", "Santa Fe", "Entre Ríos"],
    "Oeste": ["Mendoza", "San Juan", "San Luis"],
    "Sur": [
        "La Pampa",
        "Neuquén",
        "Río Negro",
        "Chubut",
        "Santa Cruz",
        "Tierra del Fuego",
    ],
}

TODAS_LAS_PROVINCIAS: list[str] = [p for provs in ZONAS.values() for p in provs]
ANIOS_PROYECCION: list[int] = list(range(2024, 2036))

# Tasa de crecimiento nacional promedio (fallback para 1 solo punto censal)
_TASA_NACIONAL_PROMEDIO: float = 0.012


@dataclass(frozen=True)
class AppConfig:
    """Configuración inmutable de la aplicación."""

    data_path: str = "data/censos.csv"
    partidos_path: str = "data/partidos_bsas.csv"
    comunas_path: str = "data/comunas_caba.csv"
    output_path: str = "dashboard.html"


def load_config() -> AppConfig:
    """Carga configuración desde variables de entorno con defaults seguros."""
    return AppConfig(
        data_path=os.environ.get("DASHBOARD_DATA_PATH", "data/censos.csv"),
        partidos_path=os.environ.get("DASHBOARD_PARTIDOS_PATH", "data/partidos_bsas.csv"),
        comunas_path=os.environ.get("DASHBOARD_COMUNAS_PATH", "data/comunas_caba.csv"),
        output_path=os.environ.get("DASHBOARD_OUTPUT_PATH", "dashboard.html"),
    )


# ---------------------------------------------------------------------------
# 2. Data Layer
# ---------------------------------------------------------------------------

_CENSUS_YEARS: list[int] = [1991, 2001, 2010, 2022]


def load_census_data(path: str) -> pd.DataFrame:
    """Carga datos multi-censales desde CSV.

    Expected CSV format::

        provincia,1991,2001,2010,2022
        Buenos Aires,12594974,13827203,15625084,17541141
        ...

    Returns:
        DataFrame con columnas: provincia + columnas de años censales disponibles.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si faltan columnas requeridas o el formato es inválido.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo de datos no encontrado: {path}")

    df = pd.read_csv(path)

    if "provincia" not in df.columns:
        raise ValueError(
            "El CSV no contiene la columna 'provincia'. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    # Detectar columnas de años censales presentes
    year_cols = [str(y) for y in _CENSUS_YEARS if str(y) in df.columns]
    if not year_cols:
        raise ValueError(
            "El CSV no contiene ninguna columna de año censal válida "
            f"(esperadas: {_CENSUS_YEARS}). Columnas encontradas: {list(df.columns)}"
        )

    result = df[["provincia"] + year_cols].copy()
    return result


def validate_census_data(df: pd.DataFrame) -> pd.DataFrame:
    """Valida estructura y completitud del DataFrame censal.

    Verifica que las columnas de años sean numéricas y que los valores
    de población sean positivos.

    Returns:
        DataFrame limpio con solo las columnas válidas.

    Raises:
        ValueError: Si el formato es inválido.
    """
    year_cols = [c for c in df.columns if c != "provincia"]

    # Convertir a numérico, coerciendo errores a NaN
    cleaned = df.copy()
    for col in year_cols:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    # Verificar que al menos una columna de año tiene datos válidos
    valid_year_cols = [
        c for c in year_cols if cleaned[c].notna().any()
    ]
    if not valid_year_cols:
        raise ValueError(
            "Ninguna columna de año censal contiene valores numéricos válidos."
        )

    # Verificar valores positivos (ignorar NaN)
    for col in valid_year_cols:
        non_null = cleaned[col].dropna()
        if (non_null <= 0).any():
            raise ValueError(
                f"La columna '{col}' contiene valores de población no positivos."
            )

    return cleaned[["provincia"] + valid_year_cols]


# ---------------------------------------------------------------------------
# 3b. Sub-unit Data Layer (partidos PBA / comunas CABA)
# ---------------------------------------------------------------------------

_SUBUNIT_CENSUS_YEARS: list[int] = [2001, 2010, 2022]


def load_subunit_data(path: str, id_col: str) -> pd.DataFrame:
    """Carga datos censales de sub-unidades (partidos o comunas) desde CSV.

    Args:
        path: Ruta al CSV.
        id_col: Nombre de la columna identificadora ('partido' o 'comuna').

    Returns:
        DataFrame con columnas: id_col, lat, lon + años censales disponibles.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si faltan columnas requeridas.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    df = pd.read_csv(path)
    required = {id_col, "lat", "lon"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Columnas faltantes en {path}: {missing}")
    year_cols = [str(y) for y in _SUBUNIT_CENSUS_YEARS if str(y) in df.columns]
    if not year_cols:
        raise ValueError(f"Sin columnas de años censales en {path}")
    keep = [id_col, "lat", "lon"] + (["barrios"] if "barrios" in df.columns else []) + year_cols
    return df[[c for c in keep if c in df.columns]].copy()


def project_subunit_population(df: pd.DataFrame, id_col: str) -> list[dict]:
    """Proyecta población 2024-2035 para cada sub-unidad usando regresión exponencial.

    Args:
        df: DataFrame con id_col, lat, lon y columnas de años censales.
        id_col: Nombre de la columna identificadora.

    Returns:
        Lista de dicts con id_col, lat, lon, pop (dict año→valor), label opcional.
    """
    year_cols = [c for c in df.columns if c not in {id_col, "lat", "lon", "barrios"}]
    available_years = [int(c) for c in year_cols]
    results = []

    for _, row in df.iterrows():
        name = str(row[id_col])
        lat = float(row["lat"])
        lon = float(row["lon"])
        label = str(row["barrios"]) if "barrios" in df.columns else ""

        years_valid: list[int] = []
        pops_valid: list[float] = []
        for yr, col in zip(available_years, year_cols):
            val = row[col]
            if pd.notna(val) and float(val) > 0:
                years_valid.append(yr)
                pops_valid.append(float(val))

        if not years_valid:
            continue

        a, b = fit_exponential(years_valid, pops_valid)
        pop_by_year = {str(yr): round(float(a * np.exp(b * yr))) for yr in ANIOS_PROYECCION}

        entry: dict = {"name": name, "lat": lat, "lon": lon, "pop": pop_by_year}
        if label:
            entry["label"] = label
        results.append(entry)

    return results





def _exponential_model(t: np.ndarray, a: float, b: float) -> np.ndarray:
    """Modelo exponencial P(t) = a * exp(b * t)."""
    return a * np.exp(b * t)


def fit_exponential(
    years: list[int], populations: list[float]
) -> tuple[float, float]:
    """Ajusta modelo exponencial P(t) = a * exp(b * t) a los datos censales.

    Normaliza los años restando el mínimo para evitar overflow numérico.

    Args:
        years: Lista de años censales disponibles (mínimo 1).
        populations: Población correspondiente a cada año.

    Returns:
        Tupla (a, b) donde a es la población base y b es la tasa de crecimiento.
    """
    if len(years) == 1:
        # Un solo punto: usar tasa nacional promedio
        a = float(populations[0])
        b = _TASA_NACIONAL_PROMEDIO
        return a, b

    t = np.array(years, dtype=float)
    p = np.array(populations, dtype=float)

    # Normalizar años para estabilidad numérica
    t_min = t.min()
    t_norm = t - t_min

    try:
        popt, _ = curve_fit(
            _exponential_model,
            t_norm,
            p,
            p0=[p[0], 0.01],
            maxfev=10000,
        )
        a_norm, b = popt
        # Ajustar 'a' para que sea válido en el espacio de años originales
        # P(t) = a_norm * exp(b*(t - t_min)) = (a_norm * exp(-b*t_min)) * exp(b*t)
        a = float(a_norm * np.exp(-b * t_min))
        return a, float(b)
    except RuntimeError:
        # Fallback: usar tasa nacional promedio
        print(
            f"  Advertencia: curve_fit no convergió. Usando tasa nacional promedio.",
            file=sys.stderr,
        )
        a = float(populations[0])
        b = _TASA_NACIONAL_PROMEDIO
        return a, b


def get_zona_for_provincia(provincia: str) -> str:
    """Retorna la zona geográfica de una provincia.

    Args:
        provincia: Nombre exacto de la provincia.

    Returns:
        Nombre de la zona geográfica.

    Raises:
        ValueError: Si la provincia no está en ninguna zona.
    """
    for zona, provincias in ZONAS.items():
        if provincia in provincias:
            return zona
    raise ValueError(
        f"Provincia '{provincia}' no encontrada en ninguna zona. "
        f"Provincias válidas: {TODAS_LAS_PROVINCIAS}"
    )


def project_population(census_df: pd.DataFrame) -> pd.DataFrame:
    """Genera proyecciones 2028-2035 usando regresión exponencial por provincia.

    Para cada provincia:
      1. Toma todos los años censales disponibles como puntos de ajuste.
      2. Ajusta P(t) = a * exp(b * t) con scipy.optimize.curve_fit.
      3. Evalúa el modelo en 2028-2035.

    Args:
        census_df: DataFrame con columnas provincia + años censales.

    Returns:
        DataFrame con columnas: provincia, zona, 2028, 2029, ..., 2035, crecimiento_pct
    """
    year_cols = [c for c in census_df.columns if c != "provincia"]
    available_years = [int(c) for c in year_cols]

    rows: list[dict] = []

    for _, row in census_df.iterrows():
        provincia = str(row["provincia"])

        # Obtener zona (skip si no reconocida)
        try:
            zona = get_zona_for_provincia(provincia)
        except ValueError:
            print(
                f"  Advertencia: provincia '{provincia}' no reconocida. Se omite.",
                file=sys.stderr,
            )
            continue

        # Recopilar puntos censales válidos (no NaN, positivos)
        years_valid: list[int] = []
        pops_valid: list[float] = []
        for yr, col in zip(available_years, year_cols):
            val = row[col]
            if pd.notna(val) and float(val) > 0:
                years_valid.append(yr)
                pops_valid.append(float(val))

        if not years_valid:
            print(
                f"  Advertencia: sin datos válidos para '{provincia}'. Se omite.",
                file=sys.stderr,
            )
            continue

        a, b = fit_exponential(years_valid, pops_valid)

        # Proyectar años 2028-2035
        proj_row: dict = {"provincia": provincia, "zona": zona}
        for yr in ANIOS_PROYECCION:
            proj_row[yr] = float(a * np.exp(b * yr))

        pop_2028 = proj_row[2028]
        pop_2035 = proj_row[2035]
        proj_row["crecimiento_pct"] = calculate_growth_percentage(pop_2028, pop_2035)

        rows.append(proj_row)

    result = pd.DataFrame(rows)
    return result


# ---------------------------------------------------------------------------
# 4. Transform Layer
# ---------------------------------------------------------------------------


def format_population(value: float) -> str:
    """Formatea valores poblacionales en formato abreviado.

    Rules:
        >= 1_000_000 → "45.0M"
        >= 1_000     → "500K"
        < 1_000      → "750"

    Args:
        value: Valor de población a formatear.

    Returns:
        Cadena con el valor formateado.
    """
    if value >= 1_000_000:
        return f"{value / 1e6:.1f}M"
    if value >= 1_000:
        return f"{value / 1e3:.0f}K"
    return str(int(value))


def calculate_growth_percentage(pop_start: float, pop_end: float) -> float:
    """Calcula el porcentaje de crecimiento entre dos valores de población.

    Args:
        pop_start: Población inicial.
        pop_end: Población final.

    Returns:
        Porcentaje de crecimiento. Retorna 0.0 si pop_start == 0.
    """
    if pop_start == 0:
        return 0.0
    return ((pop_end - pop_start) / pop_start) * 100


def aggregate_by_zona(df: pd.DataFrame) -> pd.DataFrame:
    """Suma población por zona para cada año proyectado y calcula crecimiento_pct.

    Args:
        df: DataFrame maestro con columnas provincia, zona, 2028..2035, crecimiento_pct.

    Returns:
        DataFrame con columnas: zona, 2028..2035, crecimiento_pct
    """
    year_cols = [yr for yr in ANIOS_PROYECCION]
    agg_dict = {yr: "sum" for yr in year_cols}
    zone_df = df.groupby("zona", as_index=False).agg(agg_dict)

    zone_df["crecimiento_pct"] = zone_df.apply(
        lambda r: calculate_growth_percentage(r[2028], r[2035]), axis=1
    )
    return zone_df


def rank_provinces_by_growth(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena provincias descendentemente por crecimiento_pct.

    Args:
        df: DataFrame maestro con columna crecimiento_pct.

    Returns:
        DataFrame ordenado descendentemente por crecimiento_pct con índice reseteado.
    """
    return df.sort_values("crecimiento_pct", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 5. Chart Layer
# ---------------------------------------------------------------------------

# Coordenadas centrales aproximadas de cada provincia (lat, lon)
_PROVINCE_COORDS: dict[str, tuple[float, float]] = {
    "Buenos Aires":        (-36.6769, -60.5588),
    "CABA":                (-34.6037, -58.3816),
    "Córdoba":             (-31.4135, -64.1811),
    "Santa Fe":            (-30.7069, -60.9498),
    "Mendoza":             (-34.6430, -68.1274),
    "Tucumán":             (-26.8241, -65.2226),
    "Entre Ríos":          (-31.7746, -60.4956),
    "Salta":               (-24.7821, -65.4232),
    "Misiones":            (-27.4269, -55.9461),
    "Chaco":               (-26.3850, -60.7658),
    "Corrientes":          (-28.4696, -58.8341),
    "Santiago del Estero": (-27.7951, -64.2615),
    "San Juan":            (-30.8653, -68.8894),
    "Jujuy":               (-23.2082, -65.3010),
    "Río Negro":           (-40.8135, -63.0000),
    "Neuquén":             (-38.9516, -68.0591),
    "Formosa":             (-24.8948, -59.9271),
    "Chubut":              (-43.2930, -65.1023),
    "San Luis":            (-33.2950, -66.3356),
    "Catamarca":           (-28.4696, -65.7795),
    "La Rioja":            (-29.4130, -66.8560),
    "La Pampa":            (-36.6148, -64.2839),
    "Santa Cruz":          (-51.6230, -69.2184),
    "Tierra del Fuego":    (-54.8019, -68.3030),
}

# Colores de zona para el mapa
_ZONA_COLORS: dict[str, str] = {
    "Norte":      "#f59e0b",
    "Este/Centro": "#3b82f6",
    "Oeste":      "#8b5cf6",
    "Sur":        "#10b981",
}


def build_map_data(proj_df: pd.DataFrame) -> dict:
    """Construye datos JSON para el mapa interactivo por provincia.

    Incluye coordenadas, población proyectada por año, zona y color.

    Args:
        proj_df: DataFrame maestro con proyecciones por provincia.

    Returns:
        Dict con lista 'provinces', cada elemento con lat, lon, zona,
        color y dict 'pop' con población por año (2028-2035).
    """
    provinces_data = []
    for _, row in proj_df.iterrows():
        prov = str(row["provincia"])
        zona = str(row["zona"])
        coords = _PROVINCE_COORDS.get(prov)
        if coords is None:
            continue
        pop_by_year = {str(yr): round(float(row[yr])) for yr in ANIOS_PROYECCION}
        provinces_data.append({
            "name": prov,
            "zona": zona,
            "color": _ZONA_COLORS.get(zona, "#64748b"),
            "lat": coords[0],
            "lon": coords[1],
            "pop": pop_by_year,
        })

    # Datos de zonas agregadas
    zones_data = []
    zone_centers: dict[str, tuple[float, float]] = {
        "Norte":       (-25.5, -62.0),
        "Este/Centro": (-33.5, -61.0),
        "Oeste":       (-32.5, -67.5),
        "Sur":         (-45.0, -67.0),
    }
    for zona, center in zone_centers.items():
        zone_rows = proj_df[proj_df["zona"] == zona]
        if zone_rows.empty:
            continue
        pop_by_year = {
            str(yr): round(float(zone_rows[yr].sum()))
            for yr in ANIOS_PROYECCION
        }
        zones_data.append({
            "name": zona,
            "color": _ZONA_COLORS.get(zona, "#64748b"),
            "lat": center[0],
            "lon": center[1],
            "pop": pop_by_year,
        })

    return {"provinces": provinces_data, "zones": zones_data}


def build_line_chart_data(proj_df: pd.DataFrame) -> dict:
    """Construye datos JSON para el gráfico de línea temporal.

    Genera un trace por provincia más un trace de total país.

    Args:
        proj_df: DataFrame maestro con proyecciones por provincia.

    Returns:
        Dict con claves 'all' (total país) y nombre de cada provincia,
        cada uno con listas x (años) e y (poblaciones).
    """
    years = ANIOS_PROYECCION
    data: dict = {}

    # Total país
    total_y = []
    for yr in years:
        total_y.append(float(proj_df[yr].sum()))
    data["all"] = {"x": years, "y": total_y, "name": "Argentina Total"}

    # Por provincia
    for _, row in proj_df.iterrows():
        prov = str(row["provincia"])
        data[prov] = {
            "x": years,
            "y": [float(row[yr]) for yr in years],
            "name": prov,
        }

    return data


def build_bar_chart_data(ranked_df: pd.DataFrame) -> dict:
    """Construye datos JSON para el gráfico de barras horizontales.

    Barras ordenadas ascendentemente (para que la mayor quede arriba en horizontal).

    Args:
        ranked_df: DataFrame ordenado por crecimiento_pct descendente.

    Returns:
        Dict con listas 'provinces', 'growths' ordenadas ascendentemente.
    """
    # Ordenar ascendente para que en barras horizontales la mayor quede arriba
    sorted_asc = ranked_df.sort_values("crecimiento_pct", ascending=True)
    return {
        "provinces": sorted_asc["provincia"].tolist(),
        "growths": [round(float(v), 4) for v in sorted_asc["crecimiento_pct"]],
    }


def build_zone_chart_data(zone_df: pd.DataFrame) -> dict:
    """Construye datos JSON para el gráfico de zonas geográficas.

    Zonas ordenadas descendentemente por crecimiento_pct.

    Args:
        zone_df: DataFrame de zonas con crecimiento_pct.

    Returns:
        Dict con listas 'zones' y 'growths' ordenadas descendentemente.
    """
    sorted_desc = zone_df.sort_values("crecimiento_pct", ascending=False)
    return {
        "zones": sorted_desc["zona"].tolist(),
        "growths": [round(float(v), 4) for v in sorted_desc["crecimiento_pct"]],
    }


# ---------------------------------------------------------------------------
# 6. HTML Export Layer
# ---------------------------------------------------------------------------


def _build_zone_map(proj_df: pd.DataFrame) -> dict[str, str]:
    """Construye mapa provincia → zona desde el DataFrame de proyecciones."""
    return {
        str(row["provincia"]): str(row["zona"])
        for _, row in proj_df.iterrows()
    }


def render_html(
    line_data: dict,
    bar_data: dict,
    zone_data: dict,
    map_data: dict,
    partidos_data: list[dict],
    comunas_data: list[dict],
    provinces: list[str],
    zone_map: dict[str, str],
    output_path: str,
) -> None:
    """Genera el archivo HTML autocontenido con todos los gráficos y la lógica JS."""
    line_json = json.dumps(line_data, ensure_ascii=False)
    bar_json = json.dumps(bar_data, ensure_ascii=False)
    zone_json = json.dumps(zone_data, ensure_ascii=False)
    map_json = json.dumps(map_data, ensure_ascii=False)
    partidos_json = json.dumps(partidos_data, ensure_ascii=False)
    comunas_json = json.dumps(comunas_data, ensure_ascii=False)
    zone_map_json = json.dumps(zone_map, ensure_ascii=False)
    provinces_json = json.dumps(sorted(provinces), ensure_ascii=False)

    html = _build_html_template(
        line_json, bar_json, zone_json, map_json,
        partidos_json, comunas_json, zone_map_json, provinces_json
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def _build_html_template(
    line_json: str,
    bar_json: str,
    zone_json: str,
    map_json: str,
    partidos_json: str,
    comunas_json: str,
    zone_map_json: str,
    provinces_json: str,
) -> str:
    """Construye el string HTML completo con datos y lógica JS embebidos."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Proyecciones Poblacionales Argentina 2024-2035</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root {{
            --bg:        #f5f7fa;
            --surface:   #ffffff;
            --border:    #e2e8f0;
            --text:      #333333;
            --text-muted:#64748b;
            --text-head: #1e293b;
            --input-bg:  #ffffff;
            --shadow:    rgba(0,0,0,0.08);
            --sep:       #e2e8f0;
            --yr-color:  #1a2332;
        }}
        body.dark {{
            --bg:        #0f172a;
            --surface:   #1e293b;
            --border:    #334155;
            --text:      #e2e8f0;
            --text-muted:#94a3b8;
            --text-head: #f1f5f9;
            --input-bg:  #1e293b;
            --shadow:    rgba(0,0,0,0.4);
            --sep:       #334155;
            --yr-color:  #e2e8f0;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); color: var(--text); transition: background 0.3s, color 0.3s; }}

        /* ── Header ── */
        .header {{ background: #1a2332; color: white; padding: 20px 40px; display: flex; align-items: center; justify-content: space-between; }}
        .header-text h1 {{ font-size: 1.6rem; font-weight: 600; }}
        .header-text p {{ font-size: 0.9rem; color: #94a3b8; margin-top: 4px; }}

        /* ── Dark mode toggle ── */
        .dark-toggle {{
            display: flex; align-items: center; gap: 10px;
            background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
            border-radius: 50px; padding: 6px 14px; cursor: pointer;
            color: #e2e8f0; font-size: 0.85rem; font-weight: 600;
            transition: background 0.2s; white-space: nowrap; user-select: none;
        }}
        .dark-toggle:hover {{ background: rgba(255,255,255,0.15); }}
        .toggle-track {{
            width: 40px; height: 22px; background: #475569; border-radius: 11px;
            position: relative; transition: background 0.3s; flex-shrink: 0;
        }}
        body.dark .toggle-track {{ background: #3b82f6; }}
        .toggle-thumb {{
            width: 16px; height: 16px; background: white; border-radius: 50%;
            position: absolute; top: 3px; left: 3px; transition: transform 0.3s;
        }}
        body.dark .toggle-thumb {{ transform: translateX(18px); }}

        /* ── Solapas ── */
        .tabs {{ background: #1a2332; padding: 0 40px; display: flex; gap: 4px; }}
        .tab-btn {{
            padding: 12px 24px; border: none; background: transparent;
            color: #94a3b8; cursor: pointer; font-size: 0.95rem; font-weight: 600;
            border-bottom: 3px solid transparent; transition: all 0.2s;
        }}
        .tab-btn:hover {{ color: white; }}
        .tab-btn.active {{ color: white; border-bottom-color: #3b82f6; }}
        .tab-panel {{ display: none; }}
        .tab-panel.active {{ display: block; }}

        .controls {{ padding: 16px 40px; background: var(--surface); border-bottom: 1px solid var(--border); display: flex; align-items: center; flex-wrap: wrap; gap: 16px; transition: background 0.3s; }}
        .controls label {{ font-weight: 600; margin-right: 8px; font-size: 0.95rem; color: var(--text); }}
        .controls select {{ padding: 8px 16px; font-size: 0.95rem; border: 1px solid var(--border); border-radius: 6px; background: var(--input-bg); color: var(--text); min-width: 240px; cursor: pointer; transition: background 0.3s, border-color 0.3s; }}
        .controls select:focus {{ outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }}
        .separator {{ width: 1px; height: 32px; background: var(--sep); }}
        .charts-container {{ padding: 24px 40px; display: flex; flex-direction: column; gap: 28px; }}
        .chart-card {{ background: var(--surface); border-radius: 10px; padding: 24px; box-shadow: 0 1px 3px var(--shadow); transition: background 0.3s, box-shadow 0.3s; }}
        .chart-card h2 {{ font-size: 1.1rem; color: var(--text-head); margin-bottom: 16px; font-weight: 600; }}
        .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 28px; }}
        @media (max-width: 1024px) {{ .chart-row {{ grid-template-columns: 1fr; }} }}

        /* ── Mapas ── */
        .leaflet-map {{ height: 580px; border-radius: 8px; }}
        .map-controls {{ display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }}
        .map-view-btns {{ display: flex; gap: 8px; }}
        .map-view-btns button {{ padding: 6px 16px; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); color: var(--text); cursor: pointer; font-size: 0.88rem; font-weight: 600; transition: all 0.15s; }}
        .map-view-btns button.active {{ background: #1a2332; color: white; border-color: #1a2332; }}
        .year-slider-wrap {{ display: flex; align-items: center; gap: 12px; flex: 1; min-width: 260px; }}
        .year-slider-wrap label {{ font-weight: 600; font-size: 0.95rem; white-space: nowrap; color: var(--text); }}
        input[type=range] {{ flex: 1; accent-color: #3b82f6; cursor: pointer; }}
        .yr-display {{ font-size: 1.1rem; font-weight: 700; color: var(--yr-color); min-width: 48px; text-align: center; }}
        .play-btn {{ padding: 6px 14px; border: 1px solid #3b82f6; border-radius: 6px; background: #3b82f6; color: white; cursor: pointer; font-size: 0.88rem; font-weight: 600; }}
        .play-btn:hover {{ background: #2563eb; }}
        .map-legend {{ background: var(--surface); padding: 10px 14px; border-radius: 8px; box-shadow: 0 1px 4px var(--shadow); font-size: 0.82rem; line-height: 1.8; max-width: 200px; color: var(--text); }}
        .map-legend b {{ display: block; margin-bottom: 4px; font-size: 0.88rem; }}
        .legend-dot {{ display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }}
        footer {{ text-align: center; padding: 20px; color: var(--text-muted); font-size: 0.8rem; background: var(--surface); border-top: 1px solid var(--border); transition: background 0.3s; }}

        /* ── Dark mode: Leaflet tiles overlay ── */
        body.dark .leaflet-tile {{ filter: invert(1) hue-rotate(180deg) brightness(0.85) contrast(0.9); }}
        body.dark .leaflet-container {{ background: #1e293b; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-text">
            <h1>Proyecciones Poblacionales Argentina 2024-2035</h1>
            <p>Dashboard interactivo basado en datos oficiales INDEC · Censos 2001, 2010, 2022</p>
        </div>
        <button class="dark-toggle" onclick="toggleDark()" title="Alternar modo oscuro">
            <span id="dark-icon">🌙</span>
            <div class="toggle-track"><div class="toggle-thumb"></div></div>
            <span id="dark-label">Modo oscuro</span>
        </button>
    </div>

    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('argentina')">🇦🇷 Argentina</button>
        <button class="tab-btn" onclick="switchTab('bsas')">🗺️ Buenos Aires — Partidos</button>
        <button class="tab-btn" onclick="switchTab('caba')">🏙️ CABA — Comunas</button>
        <button class="tab-btn" onclick="switchTab('resumen')">📋 Resumen y Beneficios</button>
    </div>

    <div id="tab-argentina" class="tab-panel active">
        <div class="controls">
            <label for="province-filter">Filtrar por:</label>
            <select id="province-filter">
                <option value="all">Argentina (País Completo)</option>
            </select>
            <span class="separator"></span>
            <label for="year-start">Proyección desde:</label>
            <select id="year-start">
            </select>
        </div>
        <div class="charts-container">
            <div class="chart-card">
                <h2>🗺️ Mapa Poblacional Interactivo</h2>
                <div class="map-controls">
                    <div class="map-view-btns">
                        <button id="btn-pais" class="active" onclick="setMapView('pais')">🇦🇷 País</button>
                        <button id="btn-zona" onclick="setMapView('zona')">📍 Zonas</button>
                        <button id="btn-provincia" onclick="setMapView('provincia')">🏛️ Provincias</button>
                    </div>
                    <div class="year-slider-wrap">
                        <label>Año:</label>
                        <input type="range" id="year-slider" min="2024" max="2035" step="1" value="2024">
                        <span id="year-display" class="yr-display">2024</span>
                        <button class="play-btn" id="play-btn" onclick="togglePlay('main')">▶ Play</button>
                    </div>
                </div>
                <div id="map" class="leaflet-map"></div>
            </div>
            <div class="chart-card">
                <h2>📈 Evolución Temporal de la Población</h2>
                <div id="line-chart"></div>
            </div>
            <div class="chart-row">
                <div class="chart-card">
                    <h2>📊 Provincias por Crecimiento Proyectado (%)</h2>
                    <div id="bar-chart"></div>
                </div>
                <div class="chart-card">
                    <h2>📊 Zonas Geográficas por Crecimiento (%)</h2>
                    <div id="zone-chart"></div>
                </div>
            </div>
        </div>
    </div>

    <div id="tab-bsas" class="tab-panel">
        <div class="charts-container">
            <div class="chart-card">
                <h2>🗺️ Provincia de Buenos Aires — Proyección por Partido 2024-2035</h2>
                <div class="map-controls">
                    <div class="year-slider-wrap">
                        <label>Año:</label>
                        <input type="range" id="bsas-slider" min="2024" max="2035" step="1" value="2024">
                        <span id="bsas-year-display" class="yr-display">2024</span>
                        <button class="play-btn" id="bsas-play-btn" onclick="togglePlay('bsas')">▶ Play</button>
                    </div>
                </div>
                <div id="map-bsas" class="leaflet-map"></div>
            </div>
            <div class="chart-card">
                <h2>📊 Top 20 Partidos por Crecimiento Proyectado 2024→2035 (%)</h2>
                <div id="bsas-bar-chart"></div>
            </div>
        </div>
    </div>

    <div id="tab-caba" class="tab-panel">
        <div class="charts-container">
            <div class="chart-card">
                <h2>🏙️ Ciudad Autónoma de Buenos Aires — Proyección por Comuna 2024-2035</h2>
                <div class="map-controls">
                    <div class="year-slider-wrap">
                        <label>Año:</label>
                        <input type="range" id="caba-slider" min="2024" max="2035" step="1" value="2024">
                        <span id="caba-year-display" class="yr-display">2024</span>
                        <button class="play-btn" id="caba-play-btn" onclick="togglePlay('caba')">▶ Play</button>
                    </div>
                </div>
                <div id="map-caba" class="leaflet-map"></div>
            </div>
            <div class="chart-card">
                <h2>📊 Comunas por Crecimiento Proyectado 2024→2035 (%)</h2>
                <div id="caba-bar-chart"></div>
            </div>
        </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════
         SOLAPA 4: RESUMEN Y BENEFICIOS
    ══════════════════════════════════════════════════════════════════════ -->
    <div id="tab-resumen" class="tab-panel">
        <div class="charts-container" style="max-width:1100px;margin:0 auto;">

            <div class="chart-card" style="background:linear-gradient(135deg,#1a2332 0%,#1e3a5f 100%);color:white;">
                <h2 style="color:white;font-size:1.4rem;margin-bottom:8px;">
                    📊 Proyecciones Poblacionales Argentina 2024–2035
                </h2>
                <p style="color:#94a3b8;font-size:1rem;line-height:1.6;">
                    Análisis basado en datos censales oficiales del INDEC (2001, 2010, 2022) con modelo de
                    regresión exponencial P(t) = a·e^(b·t) aplicado a nivel nacional, provincial,
                    por partido de la Provincia de Buenos Aires y por comuna de CABA.
                </p>
            </div>

            <div class="chart-card">
                <h2>🔍 ¿Qué se analizó?</h2>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:8px;">
                    <div style="background:#f8fafc;border-radius:8px;padding:16px;border-left:4px solid #3b82f6;">
                        <b style="color:#1e293b;">Cobertura geográfica</b>
                        <ul style="margin-top:8px;padding-left:18px;color:#475569;line-height:2;">
                            <li>🇦🇷 24 provincias argentinas</li>
                            <li>📍 4 zonas geográficas (Norte, Sur, Este/Centro, Oeste)</li>
                            <li>🗺️ 135 partidos de la Provincia de Buenos Aires</li>
                            <li>🏙️ 15 comunas de la Ciudad Autónoma de Buenos Aires</li>
                        </ul>
                    </div>
                    <div style="background:#f8fafc;border-radius:8px;padding:16px;border-left:4px solid #10b981;">
                        <b style="color:#1e293b;">Metodología</b>
                        <ul style="margin-top:8px;padding-left:18px;color:#475569;line-height:2;">
                            <li>📈 Modelo exponencial ajustado con scipy curve_fit</li>
                            <li>📅 Horizonte de proyección: 2024 a 2035</li>
                            <li>🔢 Datos base: censos 2001, 2010 y 2022</li>
                            <li>⚠️ Fallback a tasa nacional promedio (1.2%) cuando hay un solo punto censal</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="chart-card">
                <h2>💡 ¿Para qué sirve este análisis?</h2>
                <p style="color:#64748b;margin-bottom:20px;line-height:1.6;">
                    Conocer con anticipación dónde y cuánto crecerá la población permite al Estado y al sector privado
                    tomar decisiones de inversión y planificación con años de ventaja. A continuación, los principales
                    dominios de aplicación:
                </p>
                <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px;">

                    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
                        <div style="font-size:2rem;margin-bottom:8px;">⚡</div>
                        <b style="color:#1e293b;font-size:1rem;">Energía y servicios públicos</b>
                        <p style="color:#64748b;margin-top:6px;font-size:0.9rem;line-height:1.6;">
                            Anticipar la demanda eléctrica, de gas y agua potable por zona permite dimensionar
                            subestaciones, gasoductos y plantas potabilizadoras antes de que la demanda supere
                            la capacidad instalada, evitando cortes y sobrecargas.
                        </p>
                    </div>

                    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
                        <div style="font-size:2rem;margin-bottom:8px;">🏗️</div>
                        <b style="color:#1e293b;font-size:1rem;">Infraestructura edilicia y vivienda</b>
                        <p style="color:#64748b;margin-top:6px;font-size:0.9rem;line-height:1.6;">
                            Proyectar el déficit habitacional por partido o comuna permite priorizar planes de
                            vivienda social, regularización dominial y densificación urbana en los focos de
                            mayor crecimiento proyectado.
                        </p>
                    </div>

                    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
                        <div style="font-size:2rem;margin-bottom:8px;">🛣️</div>
                        <b style="color:#1e293b;font-size:1rem;">Vialidad: rutas, autopistas y calles</b>
                        <p style="color:#64748b;margin-top:6px;font-size:0.9rem;line-height:1.6;">
                            El crecimiento poblacional en partidos del conurbano bonaerense como La Matanza,
                            Florencio Varela o Pilar implica mayor tránsito. Planificar ampliaciones viales
                            hoy evita cuellos de botella en 5 años.
                        </p>
                    </div>

                    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
                        <div style="font-size:2rem;margin-bottom:8px;">💡</div>
                        <b style="color:#1e293b;font-size:1rem;">Iluminación y espacio público</b>
                        <p style="color:#64748b;margin-top:6px;font-size:0.9rem;line-height:1.6;">
                            La expansión de nuevos barrios requiere planificación de alumbrado público,
                            señalética y mobiliario urbano. Conocer el ritmo de crecimiento por zona
                            permite presupuestar estas obras con anticipación.
                        </p>
                    </div>

                    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
                        <div style="font-size:2rem;margin-bottom:8px;">🏥</div>
                        <b style="color:#1e293b;font-size:1rem;">Salud y equipamiento sanitario</b>
                        <p style="color:#64748b;margin-top:6px;font-size:0.9rem;line-height:1.6;">
                            Proyectar la población por franja etaria y zona permite dimensionar la red
                            hospitalaria, centros de salud primaria, camas disponibles y dotación de
                            profesionales médicos donde más se necesitarán.
                        </p>
                    </div>

                    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
                        <div style="font-size:2rem;margin-bottom:8px;">🎓</div>
                        <b style="color:#1e293b;font-size:1rem;">Educación</b>
                        <p style="color:#64748b;margin-top:6px;font-size:0.9rem;line-height:1.6;">
                            Anticipar el crecimiento de la población en edad escolar permite planificar
                            la construcción de escuelas, jardines de infantes y universidades en los
                            distritos con mayor proyección de crecimiento.
                        </p>
                    </div>

                    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
                        <div style="font-size:2rem;margin-bottom:8px;">🚌</div>
                        <b style="color:#1e293b;font-size:1rem;">Transporte público</b>
                        <p style="color:#64748b;margin-top:6px;font-size:0.9rem;line-height:1.6;">
                            Diseñar nuevas líneas de colectivo, extensiones de subte o corredores de
                            BRT en función del crecimiento proyectado reduce la congestión y mejora
                            la conectividad antes de que el problema sea crítico.
                        </p>
                    </div>

                    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
                        <div style="font-size:2rem;margin-bottom:8px;">🌳</div>
                        <b style="color:#1e293b;font-size:1rem;">Medio ambiente y espacios verdes</b>
                        <p style="color:#64748b;margin-top:6px;font-size:0.9rem;line-height:1.6;">
                            La densificación sin planificación verde genera islas de calor urbano.
                            Proyectar el crecimiento permite reservar suelo para parques, arbolado
                            y corredores ecológicos antes de que el suelo sea ocupado.
                        </p>
                    </div>

                    <div style="border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
                        <div style="font-size:2rem;margin-bottom:8px;">🗳️</div>
                        <b style="color:#1e293b;font-size:1rem;">Planificación electoral y administrativa</b>
                        <p style="color:#64748b;margin-top:6px;font-size:0.9rem;line-height:1.6;">
                            Los cambios en la distribución poblacional impactan en la representación
                            legislativa, la asignación de fondos de coparticipación y la creación
                            de nuevos municipios o comunas.
                        </p>
                    </div>

                </div>
            </div>

            <div class="chart-card" style="background:#f0fdf4;border:1px solid #bbf7d0;">
                <h2 style="color:#166534;">🚀 Valor diferencial: anticipación basada en datos</h2>
                <p style="color:#15803d;line-height:1.8;font-size:0.95rem;">
                    Este dashboard demuestra que con <b>datos abiertos del Estado argentino</b> y herramientas
                    de IA accesibles es posible construir en horas un sistema de soporte a la decisión que
                    antes requería meses de trabajo especializado. La combinación de datos censales del INDEC,
                    modelos matemáticos de proyección y visualización interactiva permite a cualquier organismo
                    público o privado:
                </p>
                <ul style="margin-top:12px;padding-left:24px;color:#166534;line-height:2.2;font-size:0.95rem;">
                    <li><b>Identificar</b> los territorios de mayor presión demográfica en los próximos 10 años</li>
                    <li><b>Priorizar</b> inversiones en infraestructura donde el impacto será mayor</li>
                    <li><b>Justificar</b> presupuestos con evidencia cuantitativa ante organismos de financiamiento</li>
                    <li><b>Coordinar</b> entre ministerios y jurisdicciones usando una visión territorial compartida</li>
                    <li><b>Actualizar</b> las proyecciones automáticamente cuando se publiquen nuevos datos censales</li>
                </ul>
            </div>

            <div class="chart-card" style="background:#eff6ff;border:1px solid #bfdbfe;">
                <h2 style="color:#1e40af;">🛠️ Stack tecnológico utilizado</h2>
                <div style="display:flex;flex-wrap:wrap;gap:10px;margin-top:12px;">
                    <span style="background:#1e40af;color:white;padding:6px 14px;border-radius:20px;font-size:0.85rem;">Python 3.14</span>
                    <span style="background:#0369a1;color:white;padding:6px 14px;border-radius:20px;font-size:0.85rem;">pandas</span>
                    <span style="background:#0369a1;color:white;padding:6px 14px;border-radius:20px;font-size:0.85rem;">scipy · curve_fit</span>
                    <span style="background:#0369a1;color:white;padding:6px 14px;border-radius:20px;font-size:0.85rem;">numpy</span>
                    <span style="background:#065f46;color:white;padding:6px 14px;border-radius:20px;font-size:0.85rem;">Leaflet.js</span>
                    <span style="background:#065f46;color:white;padding:6px 14px;border-radius:20px;font-size:0.85rem;">Plotly.js</span>
                    <span style="background:#7c3aed;color:white;padding:6px 14px;border-radius:20px;font-size:0.85rem;">HTML estático autocontenido</span>
                    <span style="background:#b45309;color:white;padding:6px 14px;border-radius:20px;font-size:0.85rem;">Datos abiertos INDEC</span>
                    <span style="background:#1a2332;color:white;padding:6px 14px;border-radius:20px;font-size:0.85rem;">Kiro IDE + IA</span>
                </div>
                <p style="color:#1e40af;margin-top:16px;font-size:0.88rem;line-height:1.6;">
                    El resultado es un archivo HTML único, sin dependencias de servidor, que puede distribuirse
                    por correo, publicarse en cualquier sitio web o integrarse en un portal de datos abiertos.
                </p>
            </div>

            <div class="chart-card" style="background:#fefce8;border:1px solid #fde68a;">
                <h2 style="color:#92400e;">⚠️ Limitaciones y consideraciones</h2>
                <ul style="padding-left:20px;color:#78350f;line-height:2.2;font-size:0.9rem;margin-top:8px;">
                    <li>Las proyecciones asumen continuidad de las tendencias históricas; eventos disruptivos (migraciones masivas, pandemias, políticas de vivienda) pueden alterar los resultados.</li>
                    <li>Los datos de partidos de PBA y comunas de CABA están basados en los censos 2001, 2010 y 2022; la granularidad es menor que a nivel provincial.</li>
                    <li>El modelo exponencial es una aproximación; para análisis de política pública se recomienda complementar con modelos de cohortes por edad y sexo.</li>
                    <li>Las coordenadas de los marcadores en el mapa son centroides aproximados, no polígonos exactos de cada jurisdicción.</li>
                </ul>
            </div>

        </div>
    </div>

    <footer>Generado con datos oficiales INDEC · Regresión exponencial P(t) = a·e^(b·t) · Jornada IA para Gobierno 2025</footer>

    <script>
    const LINE_DATA    = {line_json};
    const BAR_DATA     = {bar_json};
    const ZONE_DATA    = {zone_json};
    const MAP_DATA     = {map_json};
    const PARTIDOS     = {partidos_json};
    const COMUNAS      = {comunas_json};
    const ZONE_MAP     = {zone_map_json};
    const PROVINCES    = {provinces_json};
    const ALL_YEARS    = [2024,2025,2026,2027,2028,2029,2030,2031,2032,2033,2034,2035];
    const COLORS = {{ primary:'#3b82f6', highlight:'#ef4444' }};

    // ── HELPERS ───────────────────────────────────────────────────────────────
    function formatPop(v) {{
        if (v>=1e6) return (v/1e6).toFixed(2)+' M';
        if (v>=1e3) return (v/1e3).toFixed(1)+' K';
        return Math.round(v).toString();
    }}
    function calcGrowth(pop, yr1, yr2) {{
        const p1=pop[String(yr1)], p2=pop[String(yr2)];
        return p1 ? ((p2-p1)/p1)*100 : 0;
    }}
    function activeYears() {{
        const s=parseInt(document.getElementById('year-start').value||'2024');
        return ALL_YEARS.filter(y=>y>=s);
    }}
    function radius(pop) {{ return Math.max(6, Math.min(55, Math.sqrt(pop/3000))); }}
    function popupHtml(name, sub, pop, year, growth) {{
        return `<div style="min-width:180px"><b style="font-size:1rem">${{name}}</b><br>
        <span style="color:#64748b;font-size:0.82rem">${{sub}}</span><hr style="margin:6px 0">
        <b>Año:</b> ${{year}}<br><b>Población:</b> ${{formatPop(pop)}}<br>
        <b>Crecimiento 2024→${{year}}:</b> ${{growth.toFixed(2)}}%</div>`;
    }}

    // ── SOLAPAS ───────────────────────────────────────────────────────────────
    function switchTab(name) {{
        document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
        document.getElementById('tab-'+name).classList.add('active');
        event.target.classList.add('active');
        if(name==='bsas') {{ setTimeout(()=>{{ bsasMap.invalidateSize(); renderBsasMap(parseInt(document.getElementById('bsas-slider').value)); renderBsasBar(); }},50); }}
        if(name==='caba') {{ setTimeout(()=>{{ cabaMap.invalidateSize(); renderCabaMap(parseInt(document.getElementById('caba-slider').value)); renderCabaBar(); }},50); }}
    }}

    // ── DROPDOWNS ARGENTINA ───────────────────────────────────────────────────
    const provSel=document.getElementById('province-filter');
    PROVINCES.forEach(p=>{{ const o=document.createElement('option'); o.value=p; o.textContent=p; provSel.appendChild(o); }});
    const yrSel=document.getElementById('year-start');
    ALL_YEARS.forEach(y=>{{ const o=document.createElement('option'); o.value=y; o.textContent=y; yrSel.appendChild(o); }});

    // ══════════════════════════════════════════════════════════════════════════
    // MAPA ARGENTINA
    // ══════════════════════════════════════════════════════════════════════════
    const leafMap=L.map('map').setView([-38,-63],4);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{
        attribution:'© OpenStreetMap © CARTO',subdomains:'abcd',maxZoom:19
    }}).addTo(leafMap);
    const argLegend=L.control({{position:'bottomright'}});
    argLegend.onAdd=function(){{
        const d=L.DomUtil.create('div','map-legend');
        const zc={{'Norte':'#f59e0b','Este/Centro':'#3b82f6','Oeste':'#8b5cf6','Sur':'#10b981'}};
        d.innerHTML='<b>Zonas</b>'+Object.entries(zc).map(([z,c])=>
            `<div><span class="legend-dot" style="background:${{c}}"></span>${{z}}</div>`).join('');
        return d;
    }};
    argLegend.addTo(leafMap);

    let argMarkers=[], currentView='pais', currentYear=2024;
    function clearArgMarkers(){{ argMarkers.forEach(m=>leafMap.removeLayer(m)); argMarkers=[]; }}

    function renderMap(view,year){{
        clearArgMarkers(); currentView=view; currentYear=year;
        const yr=String(year);
        if(view==='pais'){{
            const total=MAP_DATA.provinces.reduce((s,p)=>s+(p.pop[yr]||0),0);
            const base=MAP_DATA.provinces.reduce((s,p)=>s+(p.pop['2024']||0),0);
            const g=base?((total-base)/base)*100:0;
            const m=L.circleMarker([-38,-63],{{radius:40,color:'#1a2332',fillColor:'#3b82f6',fillOpacity:0.7,weight:2}}).addTo(leafMap);
            m.bindPopup(`<b>Argentina</b><hr style="margin:6px 0"><b>Año:</b> ${{year}}<br><b>Población:</b> ${{formatPop(total)}}<br><b>Crecimiento 2024→${{year}}:</b> ${{g.toFixed(2)}}%`);
            m.bindTooltip(`🇦🇷 Argentina<br>${{formatPop(total)}}`,{{permanent:false,direction:'top'}});
            argMarkers.push(m);
        }} else if(view==='zona'){{
            MAP_DATA.zones.forEach(z=>{{
                const pop=z.pop[yr]||0,g=calcGrowth(z.pop,2024,year);
                const m=L.circleMarker([z.lat,z.lon],{{radius:radius(pop),color:'#fff',fillColor:z.color,fillOpacity:0.82,weight:2}}).addTo(leafMap);
                m.bindPopup(popupHtml(z.name,'Zona',pop,year,g));
                m.bindTooltip(`<b>${{z.name}}</b><br>${{formatPop(pop)}}`,{{permanent:true,direction:'top'}});
                argMarkers.push(m);
            }});
        }} else {{
            MAP_DATA.provinces.forEach(p=>{{
                const pop=p.pop[yr]||0,g=calcGrowth(p.pop,2024,year);
                const m=L.circleMarker([p.lat,p.lon],{{radius:radius(pop),color:'#fff',fillColor:p.color,fillOpacity:0.82,weight:1.5}}).addTo(leafMap);
                m.bindPopup(popupHtml(p.name,p.zona,pop,year,g));
                m.bindTooltip(`<b>${{p.name}}</b><br>${{formatPop(pop)}}`,{{permanent:false,direction:'top'}});
                argMarkers.push(m);
            }});
        }}
    }}
    function setMapView(v){{
        ['pais','zona','provincia'].forEach(x=>document.getElementById('btn-'+x).classList.toggle('active',x===v));
        renderMap(v,currentYear);
    }}
    const argSlider=document.getElementById('year-slider');
    const argYrDisp=document.getElementById('year-display');
    argSlider.addEventListener('input',function(){{ argYrDisp.textContent=this.value; renderMap(currentView,parseInt(this.value)); }});

    // ══════════════════════════════════════════════════════════════════════════
    // MAPA BUENOS AIRES — PARTIDOS
    // ══════════════════════════════════════════════════════════════════════════
    const bsasMap=L.map('map-bsas').setView([-35.5,-59.5],7);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{
        attribution:'© OpenStreetMap © CARTO',subdomains:'abcd',maxZoom:19
    }}).addTo(bsasMap);

    // Escala de color por población (azul claro → azul oscuro)
    function bsasColor(pop){{
        if(pop>500000) return '#1e3a8a';
        if(pop>200000) return '#1d4ed8';
        if(pop>100000) return '#3b82f6';
        if(pop>50000)  return '#60a5fa';
        if(pop>20000)  return '#93c5fd';
        return '#bfdbfe';
    }}

    let bsasMarkers=[], bsasCurrentYear=2024;
    function clearBsasMarkers(){{ bsasMarkers.forEach(m=>bsasMap.removeLayer(m)); bsasMarkers=[]; }}

    function renderBsasMap(year){{
        clearBsasMarkers(); bsasCurrentYear=year;
        const yr=String(year);
        PARTIDOS.forEach(p=>{{
            const pop=p.pop[yr]||0, g=calcGrowth(p.pop,2024,year);
            const r=Math.max(5,Math.min(30,Math.sqrt(pop/5000)));
            const m=L.circleMarker([p.lat,p.lon],{{
                radius:r, color:'#fff', fillColor:bsasColor(pop),
                fillOpacity:0.85, weight:1
            }}).addTo(bsasMap);
            m.bindPopup(popupHtml(p.name,'Partido PBA',pop,year,g));
            m.bindTooltip(`<b>${{p.name}}</b><br>${{formatPop(pop)}}`,{{permanent:false,direction:'top'}});
            bsasMarkers.push(m);
        }});
    }}

    function renderBsasBar(){{
        const entries=PARTIDOS.map(p=>({{name:p.name,growth:calcGrowth(p.pop,2024,2035)}}))
            .sort((a,b)=>b.growth-a.growth).slice(0,20).reverse();
        Plotly.react('bsas-bar-chart',[{{
            y:entries.map(e=>e.name), x:entries.map(e=>e.growth),
            type:'bar', orientation:'h',
            marker:{{color:'#3b82f6'}},
            text:entries.map(e=>e.growth.toFixed(2)+'%'),
            textposition:'outside', textfont:{{size:10}}
        }}],{{
            margin:{{t:10,b:40,l:180,r:80}},
            xaxis:{{title:'Crecimiento 2024→2035 (%)',ticksuffix:'%'}},
            yaxis:{{automargin:true}},
            height:600, font:{{family:'Segoe UI,sans-serif',size:11}}
        }},{{responsive:true,displayModeBar:false}});
    }}

    const bsasSlider=document.getElementById('bsas-slider');
    const bsasYrDisp=document.getElementById('bsas-year-display');
    bsasSlider.addEventListener('input',function(){{ bsasYrDisp.textContent=this.value; renderBsasMap(parseInt(this.value)); }});

    // ══════════════════════════════════════════════════════════════════════════
    // MAPA CABA — COMUNAS
    // ══════════════════════════════════════════════════════════════════════════
    const cabaMap=L.map('map-caba').setView([-34.615,-58.44],12);
    L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{
        attribution:'© OpenStreetMap © CARTO',subdomains:'abcd',maxZoom:19
    }}).addTo(cabaMap);

    const cabaColors=['#6366f1','#8b5cf6','#a855f7','#ec4899','#f43f5e',
                      '#ef4444','#f97316','#f59e0b','#eab308','#84cc16',
                      '#22c55e','#10b981','#14b8a6','#06b6d4','#0ea5e9'];

    let cabaMarkers=[], cabaCurrentYear=2024;
    function clearCabaMarkers(){{ cabaMarkers.forEach(m=>cabaMap.removeLayer(m)); cabaMarkers=[]; }}

    function renderCabaMap(year){{
        clearCabaMarkers(); cabaCurrentYear=year;
        const yr=String(year);
        COMUNAS.forEach((c,i)=>{{
            const pop=c.pop[yr]||0, g=calcGrowth(c.pop,2024,year);
            const r=Math.max(12,Math.min(35,Math.sqrt(pop/800)));
            const m=L.circleMarker([c.lat,c.lon],{{
                radius:r, color:'#fff',
                fillColor:cabaColors[i%cabaColors.length],
                fillOpacity:0.85, weight:1.5
            }}).addTo(cabaMap);
            const barrios=c.label||'';
            m.bindPopup(`<div style="min-width:200px"><b>${{c.name}}</b><br>
                <span style="color:#64748b;font-size:0.8rem">${{barrios}}</span>
                <hr style="margin:6px 0">
                <b>Año:</b> ${{year}}<br><b>Población:</b> ${{formatPop(pop)}}<br>
                <b>Crecimiento 2024→${{year}}:</b> ${{g.toFixed(2)}}%</div>`);
            m.bindTooltip(`<b>${{c.name}}</b><br>${{formatPop(pop)}}`,{{permanent:true,direction:'top'}});
            cabaMarkers.push(m);
        }});
    }}

    function renderCabaBar(){{
        const entries=COMUNAS.map(c=>({{name:c.name,growth:calcGrowth(c.pop,2024,2035)}}))
            .sort((a,b)=>a.growth-b.growth);
        Plotly.react('caba-bar-chart',[{{
            y:entries.map(e=>e.name), x:entries.map(e=>e.growth),
            type:'bar', orientation:'h',
            marker:{{color:cabaColors.slice(0,entries.length)}},
            text:entries.map(e=>e.growth.toFixed(2)+'%'),
            textposition:'outside', textfont:{{size:11}}
        }}],{{
            margin:{{t:10,b:40,l:120,r:80}},
            xaxis:{{title:'Crecimiento 2024→2035 (%)',ticksuffix:'%'}},
            yaxis:{{automargin:true}},
            height:500, font:{{family:'Segoe UI,sans-serif',size:12}}
        }},{{responsive:true,displayModeBar:false}});
    }}

    const cabaSlider=document.getElementById('caba-slider');
    const cabaYrDisp=document.getElementById('caba-year-display');
    cabaSlider.addEventListener('input',function(){{ cabaYrDisp.textContent=this.value; renderCabaMap(parseInt(this.value)); }});

    // ── PLAY/PAUSE UNIFICADO ──────────────────────────────────────────────────
    const playIntervals={{}};
    function togglePlay(ctx){{
        const configs={{
            main:  {{slider:argSlider,  disp:argYrDisp,  btn:'play-btn',      render:(y)=>renderMap(currentView,y),  min:2024,max:2035}},
            bsas:  {{slider:bsasSlider, disp:bsasYrDisp, btn:'bsas-play-btn', render:renderBsasMap, min:2024,max:2035}},
            caba:  {{slider:cabaSlider, disp:cabaYrDisp, btn:'caba-play-btn', render:renderCabaMap, min:2024,max:2035}},
        }};
        const cfg=configs[ctx];
        const btn=document.getElementById(cfg.btn);
        if(playIntervals[ctx]){{
            clearInterval(playIntervals[ctx]); delete playIntervals[ctx]; btn.textContent='▶ Play';
        }} else {{
            btn.textContent='⏸ Pausa';
            playIntervals[ctx]=setInterval(()=>{{
                let yr=parseInt(cfg.slider.value);
                yr=yr>=cfg.max?cfg.min:yr+1;
                cfg.slider.value=yr; cfg.disp.textContent=yr; cfg.render(yr);
            }},900);
        }}
    }}

    // ── GRÁFICOS ARGENTINA ────────────────────────────────────────────────────
    function renderLineChart(sel){{
        const years=activeYears(),key=sel==='all'?'all':sel,d=LINE_DATA[key];
        const idxs=d.x.map((x,i)=>years.includes(x)?i:-1).filter(i=>i>=0);
        const xV=idxs.map(i=>d.x[i]),yV=idxs.map(i=>d.y[i]);
        const yMin=Math.min(...yV),yMax=Math.max(...yV),step=(yMax-yMin)/5;
        const ticks=Array.from({{length:6}},(_,i)=>Math.round(yMin+step*i));
        Plotly.react('line-chart',[{{x:xV,y:yV,mode:'lines+markers',name:d.name,
            line:{{color:COLORS.primary,width:3}},marker:{{size:7}}}}],
            {{margin:{{t:20,b:50,l:80,r:30}},xaxis:{{title:'Año',dtick:1}},
            yaxis:{{title:'Población',tickvals:ticks,ticktext:ticks.map(formatPop)}},
            hovermode:'x unified',height:340,font:{{family:'Segoe UI,sans-serif'}}}},
            {{responsive:true,displayModeBar:false}});
    }}
    function renderBarChart(sel){{
        const years=activeYears(),yr1=years[0],yr2=years[years.length-1];
        const entries=MAP_DATA.provinces.map(p=>({{name:p.name,growth:calcGrowth(p.pop,yr1,yr2)}}))
            .sort((a,b)=>a.growth-b.growth);
        const colors=entries.map(e=>(sel!=='all'&&e.name===sel)?COLORS.highlight:COLORS.primary);
        Plotly.react('bar-chart',[{{y:entries.map(e=>e.name),x:entries.map(e=>e.growth),
            type:'bar',orientation:'h',marker:{{color:colors}},
            text:entries.map(e=>e.growth.toFixed(2)+'%'),textposition:'outside',textfont:{{size:10}}}}],
            {{margin:{{t:10,b:40,l:150,r:70}},xaxis:{{title:`Crecimiento ${{yr1}}→${{yr2}} (%)`,ticksuffix:'%'}},
            yaxis:{{automargin:true}},height:700,font:{{family:'Segoe UI,sans-serif',size:11}}}},
            {{responsive:true,displayModeBar:false}});
    }}
    function renderZoneChart(sel){{
        const years=activeYears(),yr1=years[0],yr2=years[years.length-1];
        const selZone=ZONE_MAP[sel];
        const entries=MAP_DATA.zones.map(z=>{{
            const g=calcGrowth(z.pop,yr1,yr2);
            return {{name:z.name,growth:g,color:(sel!=='all'&&z.name===selZone)?COLORS.highlight:z.color}};
        }}).sort((a,b)=>b.growth-a.growth);
        Plotly.react('zone-chart',[{{x:entries.map(e=>e.name),y:entries.map(e=>e.growth),
            type:'bar',marker:{{color:entries.map(e=>e.color)}},
            text:entries.map(e=>e.growth.toFixed(2)+'%'),textposition:'outside',textfont:{{size:12}}}}],
            {{margin:{{t:10,b:60,l:60,r:30}},xaxis:{{title:'Zona Geográfica'}},
            yaxis:{{title:`Crecimiento ${{yr1}}→${{yr2}} (%)`,ticksuffix:'%'}},
            height:700,font:{{family:'Segoe UI,sans-serif'}}}},
            {{responsive:true,displayModeBar:false}});
    }}
    function renderAll(){{
        const sel=provSel.value;
        renderLineChart(sel); renderBarChart(sel); renderZoneChart(sel);
    }}

    // ── DARK MODE ─────────────────────────────────────────────────────────────
    function toggleDark() {{
        const isDark = document.body.classList.toggle('dark');
        document.getElementById('dark-icon').textContent  = isDark ? '☀️' : '🌙';
        document.getElementById('dark-label').textContent = isDark ? 'Modo claro' : 'Modo oscuro';
        // Actualizar fondo de los gráficos Plotly
        const plotBg   = isDark ? '#1e293b' : '#ffffff';
        const paperBg  = isDark ? '#1e293b' : '#ffffff';
        const fontColor= isDark ? '#e2e8f0' : '#333333';
        const gridColor= isDark ? '#334155' : '#e2e8f0';
        ['line-chart','bar-chart','zone-chart','bsas-bar-chart','caba-bar-chart'].forEach(id => {{
            const el = document.getElementById(id);
            if (el && el.data) {{
                Plotly.relayout(id, {{
                    'plot_bgcolor':  plotBg,
                    'paper_bgcolor': paperBg,
                    'font.color':    fontColor,
                    'xaxis.gridcolor': gridColor,
                    'yaxis.gridcolor': gridColor,
                    'xaxis.linecolor': gridColor,
                    'yaxis.linecolor': gridColor,
                }});
            }}
        }});
        localStorage.setItem('darkMode', isDark ? '1' : '0');
    }}

    // Restaurar preferencia guardada
    if (localStorage.getItem('darkMode') === '1') toggleDark();

    // ── RENDER INICIAL ────────────────────────────────────────────────────────
    renderAll();
    renderMap('pais',2024);
    renderBsasBar();
    renderCabaBar();

    provSel.addEventListener('change',renderAll);
    yrSel.addEventListener('change',renderAll);
    </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# 7. Main Entry Point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    # 1. Cargar configuración
    config = load_config()

    # 2. Cargar datos censales
    try:
        census_df = load_census_data(config.data_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print(
            "Asegúrese de que el archivo de datos existe en la ruta configurada.",
            file=sys.stderr,
        )
        sys.exit(1)
    except ValueError as e:
        print(f"Error en formato de datos: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Validar datos
    try:
        census_df = validate_census_data(census_df)
    except ValueError as e:
        print(f"Error en validación de datos: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Proyectar población
    try:
        proj_df = project_population(census_df)
    except Exception as e:
        print(f"Error en proyección de población: {e}", file=sys.stderr)
        sys.exit(1)

    if proj_df.empty:
        print(
            "Error: No se pudieron generar proyecciones. "
            "Verifique que el CSV contiene provincias válidas.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 5. Agregar por zona
    zone_df = aggregate_by_zona(proj_df)

    # 6. Rankear provincias por crecimiento
    ranked_df = rank_provinces_by_growth(proj_df)

    # 7. Construir datos de gráficos
    line_data = build_line_chart_data(proj_df)
    bar_data = build_bar_chart_data(ranked_df)
    zone_chart_data = build_zone_chart_data(zone_df)
    map_data = build_map_data(proj_df)
    zone_map = _build_zone_map(proj_df)
    provinces = proj_df["provincia"].tolist()

    # 7b. Cargar y proyectar partidos de Buenos Aires
    try:
        partidos_df = load_subunit_data(config.partidos_path, "partido")
        partidos_data = project_subunit_population(partidos_df, "partido")
    except (FileNotFoundError, ValueError) as e:
        print(f"Advertencia: no se pudieron cargar partidos PBA: {e}", file=sys.stderr)
        partidos_data = []

    # 7c. Cargar y proyectar comunas de CABA
    try:
        comunas_df = load_subunit_data(config.comunas_path, "comuna")
        comunas_data = project_subunit_population(comunas_df, "comuna")
    except (FileNotFoundError, ValueError) as e:
        print(f"Advertencia: no se pudieron cargar comunas CABA: {e}", file=sys.stderr)
        comunas_data = []

    # 8. Generar HTML
    try:
        render_html(
            line_data=line_data,
            bar_data=bar_data,
            zone_data=zone_chart_data,
            map_data=map_data,
            partidos_data=partidos_data,
            comunas_data=comunas_data,
            provinces=provinces,
            zone_map=zone_map,
            output_path=config.output_path,
        )
    except OSError as e:
        print(f"Error al escribir el archivo HTML: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Dashboard generado exitosamente: {config.output_path}")
