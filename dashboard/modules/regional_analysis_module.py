import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from modules import data_handler


# ---------------------------------------------------------------------------
# Utilidad: extraer región del campo 'place'
# ---------------------------------------------------------------------------

# Tabla de zonas sísmicas reconocibles basada en coordenadas
_ZONES = [
    # (lat_min, lat_max, lon_min, lon_max, nombre)
    # Colombia
    (-2,  2, -78, -75, "Nariño / Putumayo"),
    ( 2,  5, -77, -75, "Cauca / Valle del Cauca"),
    ( 5,  7, -76, -74, "Antioquia"),
    ( 4,  8, -77, -76, "Chocó"),
    ( 7, 11, -75, -72, "Costa Caribe / Norte de Colombia"),
    ( 0,  8, -75, -72, "Andes Colombianos"),
    # Ecuador y Perú
    (-5,  0, -82, -75, "Ecuador"),
    (-18, -5, -82, -65, "Perú"),
    # Chile y Argentina
    (-55,-18, -76, -62, "Chile / Argentina"),
    # México y Centroamérica
    (10, 33, -120, -80, "México / Centroamérica"),
    # Caribe
    (10, 25, -80, -60, "Caribe"),
    # Venezuela
    ( 0, 13, -73, -59, "Venezuela"),
    # Japón y Región del Pacífico
    (30, 50, 130, 147, "Japón"),
    (24, 42, 122, 132, "Taiwan / China"),
    ( 0, 30, 90, 130, "Asia del Sureste"),
    (-15, 15, 120, 150, "Filipinas / Papua"),
    (-50,-15, 140, 180, "Nueva Zelanda / Pacífico Sur"),
    # Alaska y Pacífico Norte
    (50, 72, -180, -130, "Alaska"),
    (40, 65, 130, 170, "Islas Kuriles / Kamchatka"),
    # Medio Oriente
    (25, 45, 40, 65, "Irán / Turquía"),
    # Mediterráneo
    (30, 48, 10, 45, "Mediterráneo"),
    # Indonesia
    (-10, 10, 95, 140, "Indonesia"),
    # Océano Pacífico central
    (-30, 30, -180, -130, "Pacífico Central"),
    # Atlántico
    (-60, 80, -60, -15, "Atlántico"),
    # India
    (5, 35, 65, 95, "India / Nepal"),
    # Siberia/Rusia
    (45, 80, 80, 170, "Rusia / Siberia"),
]

def _coord_to_region(lat, lon):
    for lat_min, lat_max, lon_min, lon_max, name in _ZONES:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return name
    return "Otra región"


def _extract_region(place_series):
    """Extrae la parte final de 'place' (tras la última coma) como región.
    Filtra valores vacíos, 'nan' y demasiado cortos."""
    extracted = place_series.astype(str).str.split(',').str[-1].str.strip()
    mask_invalid = (
        extracted.str.lower().isin(['nan', 'none', '']) |
        extracted.str.len().lt(2)
    )
    extracted[mask_invalid] = 'Región desconocida'
    return extracted


def _get_top_regions(df, n=20):
    df = df.copy()
    if 'place' not in df.columns or df['place'].isna().all():
        df['region'] = [_coord_to_region(la, lo)
                        for la, lo in zip(df['latitude'], df['longitude'])]
    else:
        df['region'] = _extract_region(df['place'])
    counts = df['region'].value_counts()
    return counts.head(n).index.tolist(), df


# ---------------------------------------------------------------------------
# Layout principal
# ---------------------------------------------------------------------------
def render_regional_analysis(df):
    _, df_tagged = _get_top_regions(df)
    top_regions = df_tagged['region'].value_counts().head(20).index.tolist()
    region_options = [{'label': r, 'value': r} for r in top_regions]

    # Default "Nariño" para la pestaña Nacional vs Local
    narino_default = next(
        (r for r in top_regions if 'nari' in r.lower()),
        top_regions[0] if top_regions else None
    )

    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("🌎 Análisis Regional Comparativo", className="text-primary fw-bold"),
                    html.P("Compara regiones, analiza evolución temporal y alterna entre escala nacional y local.")
                ], width=12)
            ], className="mb-3"),

            dbc.Tabs([
                # -----------------------------------------------------------
                # PESTAÑA 1: Comparar dos regiones lado a lado
                # -----------------------------------------------------------
                dbc.Tab(label="⚖ Comparar Regiones", tab_id="rtab-compare", children=[
                    dbc.Row([
                        dbc.Col([
                            html.Label("Región A", className="fw-bold mt-3"),
                            dcc.Dropdown(id="reg-a", options=region_options,
                                         value=top_regions[0] if top_regions else None,
                                         clearable=False),
                        ], width=12, lg=4),
                        dbc.Col([
                            html.Label("Región B", className="fw-bold mt-3"),
                            dcc.Dropdown(id="reg-b", options=region_options,
                                         value=top_regions[1] if len(top_regions) > 1 else None,
                                         clearable=False),
                        ], width=12, lg=4),
                        dbc.Col([
                            html.Label("Métrica de comparación", className="fw-bold mt-3"),
                            dcc.Dropdown(id="reg-metric",
                                         options=[
                                             {'label': 'Magnitud promedio', 'value': 'mag_mean'},
                                             {'label': 'Total de eventos', 'value': 'count'},
                                             {'label': 'Profundidad media', 'value': 'depth_mean'},
                                             {'label': 'Magnitud máxima', 'value': 'mag_max'},
                                         ],
                                         value='mag_mean', clearable=False),
                        ], width=12, lg=4),
                    ], className="mb-4 align-items-end"),

                    dbc.Row([
                        dbc.Col(html.Div(id="cmp-kpis-a"), width=12, lg=6),
                        dbc.Col(html.Div(id="cmp-kpis-b"), width=12, lg=6),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(dcc.Graph(id="cmp-map-a"), width=12, lg=6),
                        dbc.Col(dcc.Graph(id="cmp-map-b"), width=12, lg=6),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(dcc.Graph(id="cmp-bar"), width=12),
                    ])
                ]),

                # -----------------------------------------------------------
                # PESTAÑA 2: Evolución por región
                # -----------------------------------------------------------
                dbc.Tab(label="📈 Evolución por Región", tab_id="rtab-evolution", children=[
                    dbc.Row([
                        dbc.Col([
                            html.Label("Regiones a mostrar", className="fw-bold mt-3"),
                            dcc.Dropdown(id="evo-regions", options=region_options,
                                         value=top_regions[:5] if len(top_regions) >= 5 else top_regions,
                                         multi=True),
                        ], width=12, lg=6),
                        dbc.Col([
                            html.Label("Granularidad temporal", className="fw-bold mt-3"),
                            dcc.RadioItems(id="evo-granularity",
                                           options=[
                                               {'label': ' Mensual', 'value': 'M'},
                                               {'label': ' Anual', 'value': 'Y'},
                                           ],
                                           value='Y', inline=True,
                                           className="mt-2"),
                        ], width=12, lg=3),
                        dbc.Col([
                            html.Label("Variable", className="fw-bold mt-3"),
                            dcc.RadioItems(id="evo-variable",
                                           options=[
                                               {'label': ' Nº eventos', 'value': 'count'},
                                               {'label': ' Mag. promedio', 'value': 'mag'},
                                           ],
                                           value='count', inline=True,
                                           className="mt-2"),
                        ], width=12, lg=3),
                    ], className="mb-4 align-items-end"),

                    dcc.Graph(id="evo-line", style={"height": "55vh"}),
                    dbc.Row([
                        dbc.Col(dcc.Graph(id="evo-heatmap"), width=12)
                    ])
                ]),

                # -----------------------------------------------------------
                # PESTAÑA 3: Escala nacional vs local
                # -----------------------------------------------------------
                dbc.Tab(label="🔭 Nacional vs Local", tab_id="rtab-scale", children=[
                    dbc.Row([
                        dbc.Col([
                            html.Label("Región de enfoque (escala local)", className="fw-bold mt-3"),
                            dcc.Dropdown(id="scale-region", options=region_options,
                                         value=narino_default,
                                         clearable=False),
                        ], width=12, lg=6),
                        dbc.Col([
                            html.Label("Magnitud mínima a mostrar", className="fw-bold mt-3"),
                            dcc.Slider(id="scale-mag", min=0, max=9, step=0.5, value=4,
                                       marks={i: str(i) for i in range(10)}),
                        ], width=12, lg=6),
                    ], className="mb-4 align-items-end"),

                    dbc.Row([
                        dbc.Col([
                            html.H6("Escala Nacional", className="text-center fw-bold text-primary mt-2"),
                            dcc.Graph(id="scale-national"),
                        ], width=12, lg=6),
                        dbc.Col([
                            html.H6("Escala Local (región seleccionada)", className="text-center fw-bold text-danger mt-2"),
                            dcc.Graph(id="scale-local"),
                        ], width=12, lg=6),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col(dcc.Graph(id="scale-depth-compare"), width=12)
                    ])
                ]),
            ], id="rtabs", active_tab="rtab-compare"),
        ], fluid=True)
    ])


# ---------------------------------------------------------------------------
# Helper: tarjeta KPI
# ---------------------------------------------------------------------------
def _kpi_row(region, df_r, color):
    if df_r.empty:
        return dbc.Alert(f"Sin datos para {region}", color="warning")
    return dbc.Card([
        dbc.CardHeader(html.H6(f"📍 {region}", className="mb-0 fw-bold"), className=f"bg-{color} text-white"),
        dbc.CardBody(dbc.Row([
            dbc.Col([html.H4(f"{len(df_r):,}", className=f"text-{color} fw-bold"), html.P("Eventos", className="small mb-0")], width=4, className="text-center"),
            dbc.Col([html.H4(f"{df_r['mag'].mean():.2f}", className="text-dark fw-bold"), html.P("Mag. media", className="small mb-0")], width=4, className="text-center"),
            dbc.Col([html.H4(f"{df_r['mag'].max():.1f}", className="text-danger fw-bold"), html.P("Mag. máx.", className="small mb-0")], width=4, className="text-center"),
        ]))
    ], className="shadow-sm mb-2")


# ---------------------------------------------------------------------------
# Callback: Comparar regiones
# ---------------------------------------------------------------------------
@callback(
    [Output("cmp-kpis-a", "children"),
     Output("cmp-kpis-b", "children"),
     Output("cmp-map-a", "figure"),
     Output("cmp-map-b", "figure"),
     Output("cmp-bar", "figure")],
    [Input("reg-a", "value"),
     Input("reg-b", "value"),
     Input("reg-metric", "value")]
)
def update_comparison(reg_a, reg_b, metric):
    df = data_handler.get_data()
    if df is None or not reg_a or not reg_b:
        empty = go.Figure()
        return "", "", empty, empty, empty

    _, df_tagged = _get_top_regions(df)

    df_a = df_tagged[df_tagged['region'] == reg_a]
    df_b = df_tagged[df_tagged['region'] == reg_b]

    kpi_a = _kpi_row(reg_a, df_a, "primary")
    kpi_b = _kpi_row(reg_b, df_b, "danger")

    def _map(dff, title, color):
        if dff.empty:
            return go.Figure().update_layout(title=f"Sin datos: {title}")
        fig = px.scatter_geo(
            dff, lat='latitude', lon='longitude',
            size='mag', color='mag',
            color_continuous_scale=color,
            projection='natural earth',
            title=title,
            hover_name='place' if 'place' in dff.columns else None
        )
        fig.update_layout(margin={"t": 40, "b": 0, "l": 0, "r": 0},
                          coloraxis_showscale=False, template='plotly_white')
        return fig

    fig_a = _map(df_a, f"Mapa: {reg_a}", "Blues")
    fig_b = _map(df_b, f"Mapa: {reg_b}", "Reds")

    # Barra comparativa por año
    metric_map = {
        'mag_mean': ('mag', 'mean', 'Magnitud promedio'),
        'count': (None, 'count', 'Nº de eventos'),
        'depth_mean': ('depth', 'mean', 'Profundidad media (km)'),
        'mag_max': ('mag', 'max', 'Magnitud máxima'),
    }
    col, agg, label = metric_map[metric]

    def _agg_by_year(dff, region_name):
        tmp = dff.copy()
        tmp['year'] = pd.to_datetime(tmp['time'], errors='coerce').dt.year
        if col:
            g = tmp.groupby('year')[col].agg(agg).reset_index()
            g.columns = ['year', label]
        else:
            g = tmp.groupby('year').size().reset_index(name=label)
        g['region'] = region_name
        return g

    combined = pd.concat([_agg_by_year(df_a, reg_a), _agg_by_year(df_b, reg_b)], ignore_index=True)
    fig_bar = px.bar(
        combined, x='year', y=label, color='region',
        barmode='group', title=f"{label} por año: {reg_a} vs {reg_b}",
        color_discrete_map={reg_a: '#0d6efd', reg_b: '#dc3545'},
        template='plotly_white'
    )
    fig_bar.update_layout(margin={"t": 50, "b": 20})

    return kpi_a, kpi_b, fig_a, fig_b, fig_bar


# ---------------------------------------------------------------------------
# Callback: Evolución por región
# ---------------------------------------------------------------------------
@callback(
    [Output("evo-line", "figure"),
     Output("evo-heatmap", "figure")],
    [Input("evo-regions", "value"),
     Input("evo-granularity", "value"),
     Input("evo-variable", "value")]
)
def update_evolution(regions, granularity, variable):
    df = data_handler.get_data()
    if df is None or not regions:
        return go.Figure(), go.Figure()

    _, df_tagged = _get_top_regions(df)
    df_f = df_tagged[df_tagged['region'].isin(regions)].copy()
    df_f['time'] = pd.to_datetime(df_f['time'], errors='coerce')
    df_f = df_f.dropna(subset=['time'])

    fmt = '%Y-%m' if granularity == 'M' else '%Y'
    df_f['periodo'] = df_f['time'].dt.strftime(fmt)

    if variable == 'count':
        grp = df_f.groupby(['periodo', 'region']).size().reset_index(name='valor')
        y_label = 'Número de eventos'
    else:
        grp = df_f.groupby(['periodo', 'region'])['mag'].mean().reset_index(name='valor')
        y_label = 'Magnitud promedio'

    fig_line = px.line(
        grp, x='periodo', y='valor', color='region',
        markers=True, title=f"Evolución por región — {y_label}",
        labels={'periodo': 'Periodo', 'valor': y_label},
        template='plotly_white'
    )
    fig_line.update_layout(margin={"t": 50, "b": 20}, legend_title_text='Región')

    # Heatmap región × periodo
    pivot = grp.pivot(index='region', columns='periodo', values='valor').fillna(0)
    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale='YlOrRd',
        hovertemplate='Región: %{y}<br>Periodo: %{x}<br>Valor: %{z:.2f}<extra></extra>'
    ))
    fig_heat.update_layout(
        title=f"Mapa de calor — {y_label}",
        xaxis_title='Periodo', yaxis_title='Región',
        template='plotly_white', margin={"t": 50, "b": 20},
        height=max(300, len(pivot) * 35)
    )

    return fig_line, fig_heat


# ---------------------------------------------------------------------------
# Callback: Escala nacional vs local
# ---------------------------------------------------------------------------
@callback(
    [Output("scale-national", "figure"),
     Output("scale-local", "figure"),
     Output("scale-depth-compare", "figure")],
    [Input("scale-region", "value"),
     Input("scale-mag", "value")]
)
def update_scale(region, min_mag):
    df = data_handler.get_data()
    if df is None or not region:
        return go.Figure(), go.Figure(), go.Figure()

    _, df_tagged = _get_top_regions(df)
    df_national = df_tagged[df_tagged['mag'] >= min_mag]
    df_local = df_tagged[(df_tagged['region'] == region) & (df_tagged['mag'] >= min_mag)]

    def _base_map(dff, title, color_scale, zoom=1):
        if dff.empty:
            return go.Figure().update_layout(title=f"Sin datos: {title}")
        fig = px.scatter_geo(
            dff, lat='latitude', lon='longitude',
            size='mag', color='depth',
            color_continuous_scale=color_scale,
            projection='natural earth', title=title,
            hover_name='place' if 'place' in dff.columns else None,
            hover_data={'mag': ':.2f', 'depth': ':.1f'}
        )
        fig.update_layout(margin={"t": 10, "b": 0, "l": 0, "r": 0},
                          template='plotly_white', height=380)
        return fig

    fig_nat = _base_map(df_national, "", 'Viridis')
    fig_loc = _base_map(df_local, "", 'Reds')

    # Ajuste de zoom automático para escala local
    if not df_local.empty:
        lat_c = df_local['latitude'].mean()
        lon_c = df_local['longitude'].mean()
        lat_range = df_local['latitude'].max() - df_local['latitude'].min() + 5
        lon_range = df_local['longitude'].max() - df_local['longitude'].min() + 5
        fig_loc.update_geos(
            center=dict(lat=lat_c, lon=lon_c),
            lataxis_range=[lat_c - lat_range, lat_c + lat_range],
            lonaxis_range=[lon_c - lon_range, lon_c + lon_range]
        )

    # Gráfica comparativa de profundidad nacional vs local
    fig_depth = go.Figure()
    fig_depth.add_trace(go.Histogram(
        x=df_national['depth'], name='Nacional',
        opacity=0.55, marker_color='#0d6efd',
        nbinsx=40, histnorm='probability density'
    ))
    fig_depth.add_trace(go.Histogram(
        x=df_local['depth'], name=f'Local ({region})',
        opacity=0.70, marker_color='#dc3545',
        nbinsx=40, histnorm='probability density'
    ))
    fig_depth.update_layout(
        barmode='overlay',
        title='Distribución de profundidad: Nacional vs Local',
        xaxis_title='Profundidad (km)', yaxis_title='Densidad',
        template='plotly_white', legend_title_text='Escala',
        margin={"t": 50, "b": 20}
    )

    return fig_nat, fig_loc, fig_depth
