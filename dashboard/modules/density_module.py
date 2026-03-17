import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc

def render_density_analysis(df):
    """
    Módulo 4: Análisis de Densidad Espacial y Hotspots (Versión Final Morada).
    """
    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("Inteligencia de Densidad Sísmica", className="text-primary fw-bold"),
                    html.P("Haz clic en los focos de calor rojos del mapa para analizar el perfil de subducción."),
                ], width=12)
            ], className="mb-4"),

            # FILA 1: MAPA SOLO, ANCHO COMPLETO Y MÁS GRANDE
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Mapa de Concentración (Hotspots Morados)"),
                        dbc.CardBody([
                            dcc.Graph(id="mapa-densidad", style={"height": "72vh"})
                        ])
                    ], className="shadow-sm")
                ], width=12),
            ], className="mb-4"),

            # FILA 2: TOP 5 DEBAJO DEL MAPA
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Top 5 Eventos de Mayor Magnitud"),
                        dbc.CardBody(id="top-zones-table", style={"fontSize": "0.85rem"})
                    ], className="shadow-sm")
                ], width=12),
            ], className="mb-4"),

            # FILA 3: HISTOGRAMA Y PERFIL HIPOCENTRAL LADO A LADO
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Distribución Frecuente por Profundidad"),
                        dbc.CardBody([
                            dcc.Graph(id="graph-depth-hist", style={"height": "40vh"})
                        ])
                    ], className="shadow-sm")
                ], width=12, lg=6),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Perfil Hipocentral Seleccionado (Corte Transversal)"),
                        dbc.CardBody([
                            dcc.Graph(id="graph-depth-profile", style={"height": "40vh"})
                        ])
                    ], className="shadow-sm")
                ], width=12, lg=6),
            ]),

        ], fluid=True)
    ])

@callback(
    [Output("mapa-densidad", "figure"),
     Output("graph-depth-profile", "figure"),
     Output("graph-depth-hist", "figure"),
     Output("top-zones-table", "children")],
    [Input("mapa-densidad", "clickData")]
)
def update_density_module(clickData):
    from modules import data_handler
    df = data_handler.get_data()
    
    if df is None:
        return go.Figure(), go.Figure(), go.Figure(), "Sin datos"

    # 1. MAPA DE CALOR: Blanco + Morado
    fig_map = px.density_mapbox(
        df, lat='latitude', lon='longitude', z='mag',
        radius=15, zoom=6,
        center=dict(lat=1.2136, lon=-77.2811),
        mapbox_style="carto-positron", # Fondo Blanco
        color_continuous_scale="Reds" # Hotspots Morados
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, clickmode='event+select')

    # 2. LÓGICA DE FILTRADO CRUZADO
    dff = df
    selected_info = ""
    if clickData:
        lat_c = clickData['points'][0]['lat']
        lon_c = clickData['points'][0]['lon']
        # Filtro de proximidad (radio de 0.4 grados)
        dff = df[(df['latitude'].between(lat_c - 0.4, lat_c + 0.4)) &
                 (df['longitude'].between(lon_c - 0.4, lon_c + 0.4))]
        selected_info = f" (Zona: {lat_c:.2f}, {lon_c:.2f})"

    # 3. PERFIL DE PROFUNDIDAD (Scatter Morado)
    fig_depth = px.scatter(
        dff, x="mag", y="depth", color="mag", size="mag",
        color_continuous_scale="Purples",
        title=f"Distribución de Hipocentros{selected_info}",
        labels={"mag": "Magnitud", "depth": "Profundidad (km)"}
    )
    fig_depth.update_layout(yaxis=dict(autorange="reversed"), template="plotly_white")

    # 4. HISTOGRAMA DE PROFUNDIDAD (Morado)
    fig_hist = px.histogram(
        dff, x="depth", nbins=15,
        color_discrete_sequence=["#076fee"], # Morado institucional
        title="Frecuencia por Profundidad"
    )
    fig_hist.update_layout(template="plotly_white", margin=dict(t=30, b=0, l=0, r=0))

    # 5. TABLA TOP 5 (Seguridad contra KeyError: 'place')
    cols = df.columns.tolist()
    col_nombre = 'place' if 'place' in cols else 'location' if 'location' in cols else None
    
    if col_nombre:
        top_df = df.nlargest(5, 'mag')[[col_nombre, 'mag', 'depth']]
        top_df.columns = ['Ubicación', 'M', 'P(km)']
    else:
        top_df = df.nlargest(5, 'mag').copy()
        top_df['Ubicación'] = top_df.apply(lambda r: f"Lat {r['latitude']:.1f}, Lon {r['longitude']:.1f}", axis=1)
        top_df = top_df[['Ubicación', 'mag', 'depth']]
        top_df.columns = ['Ubicación (Coords)', 'M', 'P(km)']

    table = dbc.Table.from_dataframe(
        top_df, striped=True, bordered=True, hover=True, size="sm", className="mb-0"
    )

    return fig_map, fig_depth, fig_hist, table