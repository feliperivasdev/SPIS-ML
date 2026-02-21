import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc

def render_density_analysis(df):
    """
    Módulo 4: Análisis de Densidad Espacial y Mapas de Calor.
    """
    df_clean = df.dropna(subset=['latitude', 'longitude', 'mag', 'depth']).copy()

    # 1. Mapa de Calor (Heatmap)
    # Usamos Density Mapbox para ver la concentración de energía
    fig_heatmap = px.density_mapbox(
        df_clean, 
        lat='latitude', 
        lon='longitude', 
        z='mag', 
        radius=15,
        center=dict(lat=1.2136, lon=-77.2811), # Centrado en Pasto
        zoom=7,
        mapbox_style="stamen-terrain",
        color_continuous_scale="Inferno",
        title="Mapa de Calor de Intensidad Sísmica"
    )
    fig_heatmap.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

    # 2. Análisis Profundidad vs Magnitud (Estructura interna)
    fig_depth = px.scatter(
        df_clean,
        x="mag",
        y="depth",
        color="depth",
        size="mag",
        color_continuous_scale="RdYlGn_r",
        labels={"mag": "Magnitud", "depth": "Profundidad (km)"},
        title="Relación Magnitud vs Profundidad"
    )
    fig_depth.update_layout(yaxis=dict(autorange="reversed"), template="plotly_white")

    # 3. Layout del Módulo
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H3("🔥 Análisis de Densidad y Hotspots", className="text-primary fw-bold"),
                html.P("Identificación visual de las zonas con mayor acumulación de energía liberada."),
            ], width=12)
        ], className="mb-4"),

        dbc.Row([
            # Columna del Mapa de Calor
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Distribución Espacial de Energía (Heatmap)"),
                    dbc.CardBody([
                        dcc.Graph(figure=fig_heatmap, style={"height": "60vh"})
                    ])
                ], className="shadow-sm")
            ], width=12, lg=7),

            # Columna de Análisis de Profundidad
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Análisis de Subducción / Profundidad"),
                    dbc.CardBody([
                        dcc.Graph(figure=fig_depth, style={"height": "60vh"})
                    ])
                ], className="shadow-sm")
            ], width=12, lg=5),
        ]),

        # Tarjeta informativa inferior
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H5("💡 Interpretación de Densidad"),
                    html.P([
                        "Las zonas en color blanco/amarillo intenso en el mapa representan puntos de ",
                        html.B("alta recurrencia sísmica"), ". Si estos puntos coinciden con fallas geológicas activas, ",
                        "indican una liberación constante de energía."
                    ])
                ], color="dark", className="mt-4")
            ], width=12)
        ])
    ])