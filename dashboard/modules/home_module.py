import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import requests
import pandas as pd
from datetime import datetime, timezone

# ==========================
# Datos en tiempo real (USGS)
# ==========================

USGS_ENDPOINT = "https://earthquake.usgs.gov/fdsnws/event/1/query"

def _safe_get_json(url: str, params: dict, timeout: int = 8) -> dict:
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

def fetch_usgs_events(min_magnitude: float = 4.5, hours: int = 24, limit: int = 50) -> pd.DataFrame:
    """
    Descarga eventos desde la API USGS en formato GeoJSON.
    - min_magnitude: magnitud mínima
    - hours: ventana temporal hacia atrás
    - limit: máximo de eventos a mostrar
    """
    now = datetime.now(timezone.utc)
    start = now - pd.Timedelta(hours=hours)

    params = {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": float(min_magnitude),
        "orderby": "time",
        "limit": int(limit),
    }

    data = _safe_get_json(USGS_ENDPOINT, params=params)
    features = data.get("features", []) if isinstance(data, dict) else []

    rows = []
    for f in features:
        prop = f.get("properties", {}) or {}
        geom = f.get("geometry", {}) or {}
        coords = geom.get("coordinates", [None, None, None]) or [None, None, None]

        # USGS: [lon, lat, depth_km]
        lon, lat, depth = (coords + [None, None, None])[:3]
        t_ms = prop.get("time")
        t = datetime.fromtimestamp(t_ms / 1000, tz=timezone.utc) if isinstance(t_ms, (int, float)) else None

        rows.append({
            "Tiempo (UTC)": t.strftime("%Y-%m-%d %H:%M:%S") if t else "N/A",
            "Mag": prop.get("mag"),
            "Prof. (km)": depth,
            "Lugar": prop.get("place"),
            "Lat": lat,
            "Lon": lon,
            "URL": prop.get("url"),
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["Mag"] = pd.to_numeric(df["Mag"], errors="coerce")
        df["Prof. (km)"] = pd.to_numeric(df["Prof. (km)"], errors="coerce")
    return df

def compute_kpis(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {
            "count": "N/A",
            "max_mag": "N/A",
            "last_mag": "N/A",
            "last_place": "N/A",
        }
    max_mag = df["Mag"].max(skipna=True)
    last_mag = df.iloc[0]["Mag"]
    last_place = df.iloc[0]["Lugar"]
    return {
        "count": int(len(df)),
        "max_mag": float(max_mag) if pd.notna(max_mag) else "N/A",
        "last_mag": float(last_mag) if pd.notna(last_mag) else "N/A",
        "last_place": last_place if isinstance(last_place, str) and last_place else "N/A",
    }

# =========
# Glosario
# =========

GLOSSARY = {
    "Fundamentos": [
        ("Sismo / Terremoto", "Liberación repentina de energía elástica acumulada en la litosfera que genera ondas sísmicas. En uso común, 'terremoto' suele referirse a eventos con daños o gran magnitud."),
        ("Ondas P", "Ondas compresionales (primarias). Son las más rápidas y viajan a través de sólidos, líquidos y gases."),
        ("Ondas S", "Ondas de corte (secundarias). Viajan más lento que las P y no se propagan en fluidos."),
        ("Ondas superficiales (Love/Rayleigh)", "Ondas que se propagan cerca de la superficie. Suelen asociarse a gran parte del daño estructural."),
        ("Magnitud", "Medida instrumental del tamaño del sismo relacionada con la energía liberada (p. ej., Mw). No es lo mismo que intensidad."),
        ("Intensidad (p. ej., Mercalli Modificada)", "Medida de los efectos observados del sismo en un lugar: percepción, daños, impacto en estructuras."),
        ("Momento sísmico (M0)", "Parámetro físico proporcional al área de ruptura, el desplazamiento y la rigidez del medio. Base de la magnitud momento (Mw)."),
        ("Magnitud momento (Mw)", "Escala de magnitud derivada del momento sísmico; es el estándar moderno para grandes eventos."),
    ],
    "Fuente y localización": [
        ("Hipocentro", "Punto dentro de la Tierra donde inicia la ruptura (origen de las ondas). Se describe por latitud, longitud y profundidad."),
        ("Epicentro", "Proyección del hipocentro en la superficie terrestre. Útil para describir la ubicación a nivel de superficie."),
        ("Profundidad focal", "Distancia vertical desde la superficie hasta el hipocentro. Influye en la intensidad sentida y el área afectada."),
        ("Mecanismo focal", "Descripción del tipo de falla y sentido de movimiento; suele representarse con 'beachballs'."),
        ("Falla", "Fractura o zona de discontinuidad donde ocurre desplazamiento relativo de bloques de roca."),
        ("Ruptura", "Proceso de propagación de la fractura a lo largo de una falla durante un sismo."),
        ("Aftershock / Réplica", "Sismos posteriores asociados al reajuste de esfuerzos en la región de ruptura."),
        ("Foreshock / Precursor", "Sismo que antecede a un evento principal en la misma zona (solo se identifica como tal a posteriori)."),
    ],
    "Tectónica": [
        ("Placas tectónicas", "Porciones rígidas de litosfera que se mueven sobre la astenosfera y generan deformación en sus bordes."),
        ("Subducción", "Proceso por el que una placa (usualmente oceánica) se hunde bajo otra. Genera sismos frecuentes y, a veces, grandes megaterremotos."),
        ("Zona de Wadati–Benioff", "Distribución de hipocentros que define el plano de subducción a profundidades crecientes."),
        ("Falla inversa", "Tipo de falla donde el bloque colgante sube respecto al yacente; común en ambientes compresivos."),
        ("Falla normal", "El bloque colgante desciende; común en extensión (rift, dorsales)."),
        ("Falla de rumbo (strike-slip)", "Movimiento principalmente horizontal; ejemplo: Falla de San Andrés."),
        ("Acoplamiento sísmico", "Grado en el que dos placas están 'pegadas' acumulando deformación elástica antes de deslizarse en un sismo."),
    ],
    "Estadística y peligrosidad": [
        ("Ley de Gutenberg–Richter", "Relación log-lineal entre magnitud y frecuencia: log10(N) = a − b·M. El parámetro b describe la proporción relativa de sismos grandes vs. pequeños."),
        ("Parámetro a (G–R)", "Representa la productividad sísmica o nivel de actividad de una región (cantidad total de eventos)."),
        ("Parámetro b (G–R)", "Pendiente de la relación. Valores cercanos a 1 son comunes; variaciones pueden reflejar heterogeneidad, estado de esfuerzos o completitud del catálogo."),
        ("Completitud del catálogo (Mc)", "Magnitud mínima por encima de la cual el catálogo se considera completo (sin pérdidas sistemáticas de eventos)."),
        ("Tasa de ocurrencia", "Número esperado de eventos en una ventana temporal dada para un umbral de magnitud."),
        ("Peligrosidad sísmica", "Probabilidad de exceder un nivel de movimiento del suelo en un periodo. Puede ser determinista o probabilista (PSHA)."),
        ("Riesgo sísmico", "Combinación de peligrosidad, exposición y vulnerabilidad. Relaciona amenaza con pérdidas esperadas."),
        ("Atenuación / GMPE", "Modelos que predicen parámetros del movimiento del suelo (PGA, SA) como función de magnitud, distancia y condiciones del sitio."),
    ],
    "Movimiento del suelo y sitio": [
        ("PGA", "Aceleración máxima del suelo (Peak Ground Acceleration). Indicador común del nivel de sacudida."),
        ("PGV", "Velocidad máxima del suelo (Peak Ground Velocity). A veces correlaciona mejor con daño en ciertos rangos."),
        ("Espectro de respuesta", "Respuesta máxima de un oscilador a diferentes periodos; clave para diseño sismo-resistente."),
        ("Efectos de sitio", "Amplificación o modificación local del movimiento por geología superficial, topografía o estratigrafía."),
        ("Licuefacción", "Pérdida de resistencia de suelos saturados por incremento de presión de poros durante sacudida."),
        ("Resonancia", "Amplificación cuando el periodo del movimiento del suelo se aproxima al periodo natural de la estructura o capa de suelo."),
    ],
    "Análisis espacial": [
        ("Densidad sísmica", "Medida (a menudo espacial) de concentración de eventos por unidad de área/volumen y tiempo; útil para identificar zonas activas."),
        ("Clustering", "Agrupamiento espacio-temporal de sismos (p. ej., secuencias de réplicas)."),
        ("Kernel Density Estimation (KDE)", "Técnica para estimar densidad espacial suavizada a partir de puntos (eventos)."),
    ],
    "Instrumentación y catálogo": [
        ("Sismómetro", "Instrumento que registra el movimiento del suelo; puede ser de banda ancha o de periodo corto."),
        ("Acelerógrafo", "Instrumento que registra aceleración del suelo, útil en ingeniería sísmica."),
        ("Red sismológica", "Conjunto de estaciones que detecta y localiza eventos, estimando magnitudes y parámetros."),
        ("Catálogo sísmico", "Base de datos de eventos con parámetros (tiempo, ubicación, magnitud, etc.). Su calidad depende de la red y el procesamiento."),
    ],
}

def _glossary_items_filtered(query: str):
    q = (query or "").strip().lower()
    if not q:
        return GLOSSARY
    out = {}
    for cat, items in GLOSSARY.items():
        filtered = []
        for term, desc in items:
            if q in term.lower() or q in desc.lower():
                filtered.append((term, desc))
        if filtered:
            out[cat] = filtered
    return out

def render_glossary(query: str = ""):
    data = _glossary_items_filtered(query)
    if not data:
        return dbc.Alert("No se encontraron términos para ese criterio de búsqueda.", color="warning", className="mb-0")

    accordion_items = []
    for cat, items in data.items():
        body = html.Div([
            html.Ul([
                html.Li([
                    html.B(term),
                    html.Br(),
                    html.Span(desc, className="text-muted"),
                ], className="mb-3")
                for term, desc in items
            ], className="mb-0")
        ])
        accordion_items.append(dbc.AccordionItem(body, title=cat))

    return dbc.Accordion(accordion_items, start_collapsed=True, always_open=True, className="shadow-sm")

# ==================
# Render del landing
# ==================

def render_home_module():
    return html.Div([
        # HERO
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("SPIS-ML", className="badge rounded-pill text-bg-primary mb-3"),
                        html.H1("Seismic Performance Intelligent System", className="display-5 fw-bold mb-2"),
                        html.P(
                            "Plataforma académica para exploración, modelado y comunicación de información sísmica. "
                            "Este home integra monitoreo global en tiempo casi real (USGS) y un glosario técnico-curado "
                            "para aprendizaje y consulta.",
                            className="lead text-muted"
                        ),
                       # dbc.Button("Ir a carga de datos", href="#upload-section", color="primary", size="lg", className="mt-2"),
                    ], className="py-4")
                ], md=7),
                dbc.Col([
                    dbc.Card([
                        # dbc.CardBody([
                        #     html.H5("Resumen del home", className="fw-bold"),
                        #     html.Ul([
                        #         html.Li("Monitoreo global de eventos recientes (ventana configurable)."),
                        #         html.Li("KPIs de actividad: conteo, máximo y último evento."),
                        #         html.Li("Mapa y tabla con eventos recientes."),
                        #         html.Li("Glosario académico de sismología y estadística sísmica."),
                        #     ], className="mb-0 text-muted")
                        # ])
                    ], className="shadow-sm border-0 my-4")
                ], md=5),
            ], className="align-items-center"),
        ], fluid=True, className="bg-body-tertiary border-bottom"),

        # Monitor en tiempo real
        dbc.Container([
            dcc.Interval(id="realtime-interval", interval=60 * 1000, n_intervals=0),
            dcc.Store(id="realtime-cache", data={"minmag": 4.5, "hours": 24, "limit": 50}),

            dbc.Row([
                dbc.Col([
                    html.H3("📡 Monitoreo global", className="fw-bold mb-1"),
                    html.P("Fuente: USGS Earthquake Hazards Program (GeoJSON). Actualización automática cada 60s.", className="text-muted mb-4"),
                ])
            ]),

            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.Div("Eventos (últimas 24h)", className="text-muted"),
                    html.Div(id="kpi-count", className="display-6 fw-bold"),
                ]), className="border-0 shadow-sm"), md=4),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.Div("Magnitud máxima", className="text-muted"),
                    html.Div(id="kpi-maxmag", className="display-6 fw-bold"),
                ]), className="border-0 shadow-sm"), md=4),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.Div("Último evento relevante", className="text-muted"),
                    html.Div(id="kpi-last", className="h5 fw-bold mb-0"),
                    html.Div(id="kpi-lastplace", className="text-muted"),
                ]), className="border-0 shadow-sm"), md=4),
            ], className="g-3 mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.Div([
                            html.Span("Filtros", className="fw-bold"),
                            html.Span(" (para el home)", className="text-muted"),
                        ]), className="bg-white"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Magnitud mínima", className="text-muted"),
                                    dcc.Slider(
                                        id="rt-minmag",
                                        min=2.5, max=7.0, step=0.5,
                                        value=4.5,
                                        marks={i: str(i) for i in range(3, 8)},
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    )
                                ], md=6),
                                dbc.Col([
                                    dbc.Label("Ventana temporal (horas)", className="text-muted"),
                                    dcc.Slider(
                                        id="rt-hours",
                                        min=6, max=72, step=6,
                                        value=24,
                                        marks={i: str(i) for i in range(6, 73, 12)},
                                        tooltip={"placement": "bottom", "always_visible": False},
                                    )
                                ], md=6),
                            ], className="g-3"),
                        ])
                    ], className="shadow-sm border-0")
                ])
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Mapa de eventos recientes", className="bg-white fw-bold"),
                        dbc.CardBody([
                            dcc.Graph(id="realtime-map", config={"displayModeBar": False}, style={"height": "420px"})
                        ])
                    ], className="shadow-sm border-0")
                ], lg=7),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Últimos eventos (tabla)", className="bg-white fw-bold"),
                        dbc.CardBody([
                            html.Div(id="realtime-table")
                        ])
                    ], className="shadow-sm border-0")
                ], lg=5),
            ], className="g-3 mb-5"),
        ], className="py-5"),

        # Glosario académico
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("Glosario académico de sismología", className="fw-bold mb-1"),
                    html.P(
                        "Definiciones técnicas, concisas y orientadas a análisis. "
                        "Incluye estadística sísmica (Gutenberg–Richter), tectónica y parámetros de ingeniería.",
                        className="text-muted mb-4"
                    ),
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.InputGroup([
                        dbc.Input(id="glossary-search", placeholder="Buscar término (p. ej., 'epicentro', 'subducción', 'b-value')...", type="text"),
                        dbc.Button("Limpiar", id="glossary-clear", color="secondary", outline=True),
                    ], className="mb-3"),
                    html.Div(id="glossary-accordion-container", children=render_glossary("")),
                    dbc.Alert(
                        [
                            html.B("Nota académica: "),
                            "las definiciones son de propósito educativo. Para investigación o decisiones de ingeniería, "
                            "use fuentes primarias y normas aplicables (p. ej., GMPE, PSHA, reglamentos sismo-resistentes).",
                        ],
                        color="light",
                        className="mt-3 border-0 shadow-sm"
                    )
                ], lg=10),
            ], className="justify-content-center"),
        ], className="pb-5"),
    ])

# ==================
# Callbacks del home
# ==================

def register_home_callbacks(app):
    """
    Registra callbacks del home en una instancia Dash.
    Llamar una sola vez, idealmente justo después de crear `app`.
    """

    @app.callback(
        Output("realtime-cache", "data"),
        Input("rt-minmag", "value"),
        Input("rt-hours", "value"),
        State("realtime-cache", "data"),
    )
    def _update_rt_config(minmag, hours, cache):
        cache = cache or {}
        cache.update({"minmag": float(minmag or 4.5), "hours": int(hours or 24), "limit": int(cache.get("limit", 50))})
        return cache

    @app.callback(
        Output("kpi-count", "children"),
        Output("kpi-maxmag", "children"),
        Output("kpi-last", "children"),
        Output("kpi-lastplace", "children"),
        Output("realtime-table", "children"),
        Output("realtime-map", "figure"),
        Input("realtime-interval", "n_intervals"),
        State("realtime-cache", "data"),
    )
    def _refresh_realtime(_n, cache):
        cache = cache or {"minmag": 4.5, "hours": 24, "limit": 50}
        df = fetch_usgs_events(min_magnitude=cache.get("minmag", 4.5), hours=cache.get("hours", 24), limit=cache.get("limit", 50))
        kpi = compute_kpis(df)

        # Tabla (top 10)
        if df is None or df.empty:
            table = dbc.Alert("No hay datos disponibles en este momento (o la API no respondió).", color="warning")
        else:
            view = df.head(10).copy()
            # Enlaces clicables
            view["Detalle"] = view["URL"].apply(lambda u: html.A("Ver", href=u, target="_blank") if isinstance(u, str) and u else "—")
            view = view.drop(columns=["URL"])

            header = [html.Thead(html.Tr([html.Th(c) for c in view.columns]))]
            body_rows = []
            for _, r in view.iterrows():
                body_rows.append(html.Tr([html.Td(r[c]) for c in view.columns]))
            body = [html.Tbody(body_rows)]
            table = dbc.Table(header + body, bordered=False, hover=True, responsive=True, size="sm", className="mb-0")

        # Mapa (Scattergeo)
        fig = {
            "data": [],
            "layout": {
                "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
                "geo": {
                    "showland": True,
                    "landcolor": "rgb(245,245,245)",
                    "showocean": True,
                    "oceancolor": "rgb(235,242,250)",
                    "projection": {"type": "natural earth"},
                },
            },
        }
        if df is not None and not df.empty:
            fig["data"] = [{
                "type": "scattergeo",
                "lat": df["Lat"],
                "lon": df["Lon"],
                "text": df.apply(lambda r: f"{r.get('Mag','N/A')} M — {r.get('Lugar','')}", axis=1),
                "mode": "markers",
                "marker": {
                    "size": (df["Mag"].fillna(0).clip(lower=0) * 3 + 4).tolist(),
                    "opacity": 0.75,
                },
            }]

        last_line = f"{kpi['last_mag']} M" if kpi["last_mag"] != "N/A" else "N/A"
        return (
            str(kpi["count"]),
            f"{kpi['max_mag']:.1f} M" if isinstance(kpi["max_mag"], (int, float)) else "N/A",
            last_line,
            kpi["last_place"],
            table,
            fig,
        )

    @app.callback(
        Output("glossary-search", "value"),
        Input("glossary-clear", "n_clicks"),
        prevent_initial_call=True,
    )
    def _clear_glossary(_n):
        return ""

    @app.callback(
        Output("glossary-accordion-container", "children"),
        Input("glossary-search", "value"),
    )
    def _filter_glossary(q):
        return render_glossary(q or "")