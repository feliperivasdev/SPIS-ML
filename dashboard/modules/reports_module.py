import pandas as pd
import numpy as np
import plotly.express as px
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc

def render_reports_module(df):
    # Valores iniciales para los filtros
    min_mag, max_mag = df['mag'].min(), df['mag'].max()
    min_dep, max_dep = df['depth'].min(), df['depth'].max()
    min_date, max_date = df['time'].min(), df['time'].max()

    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("🛠️ Configurador de Reportes Personalizados", className="text-primary fw-bold"),
                    html.P("Filtra los parámetros específicos para generar tu informe técnico."),
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                # PANEL DE FILTROS (Izquierda)
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Parámetros del Reporte", className="bg-primary text-white"),
                        dbc.CardBody([
                            html.Label("Rango de Magnitud (M):", className="fw-bold"),
                            dcc.RangeSlider(id='report-mag-slider', min=0, max=10, step=0.1, 
                                            value=[min_mag, max_mag], marks={i: str(i) for i in range(11)}),
                            
                            html.Label("Rango de Profundidad (Km):", className="fw-bold mt-3"),
                            dcc.RangeSlider(id='report-depth-slider', min=0, max=300, step=10, 
                                            value=[min_dep, max_dep], marks={0: '0', 150: '150', 300: '300'}),

                            html.Label("Periodo de Tiempo:", className="fw-bold mt-3"),
                            dcc.DatePickerRange(
                                id='report-date-picker',
                                min_date_allowed=min_date,
                                max_date_allowed=max_date,
                                start_date=min_date,
                                end_date=max_date,
                                className="mb-3"
                            ),
                            
                            html.Hr(),
                            dbc.Button([html.I(className="bi bi-download me-2"), "Exportar CSV Filtrado"], 
                                       id="btn-download-csv", color="success", className="w-100 mb-2"),
                            dcc.Download(id="download-dataframe-csv"),
                        ])
                    ], className="shadow-sm")
                ], width=12, lg=4),

                # VISTA PREVIA DINÁMICA (Derecha)
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Vista Previa del Reporte Seleccionado"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col(html.Div(id="report-stat-1"), width=4),
                                dbc.Col(html.Div(id="report-stat-2"), width=4),
                                dbc.Col(html.Div(id="report-stat-3"), width=4),
                            ], className="text-center mb-3"),
                            dcc.Graph(id="report-preview-map", style={"height": "40vh"}),
                        ])
                    ], className="shadow-sm")
                ], width=12, lg=8),
            ])
        ], fluid=True)
    ])

@callback(
    [Output("report-preview-map", "figure"),
     Output("report-stat-1", "children"),
     Output("report-stat-2", "children"),
     Output("report-stat-3", "children")],
    [Input("report-mag-slider", "value"),
     Input("report-depth-slider", "value"),
     Input("report-date-picker", "start_date"),
     Input("report-date-picker", "end_date")]
)
def update_report_preview(mag_range, depth_range, start_date, end_date):
    from modules import data_handler
    df = data_handler.get_data()
    if df is None: return px.scatter_mapbox(), "", "", ""

    # Filtrado dinámico según la selección del usuario
    dff = df[
        (df['mag'] >= mag_range[0]) & (df['mag'] <= mag_range[1]) &
        (df['depth'] >= depth_range[0]) & (df['depth'] <= depth_range[1]) &
        (df['time'] >= start_date) & (df['time'] <= end_date)
    ]

    # Mapa dinámico del reporte
    fig = px.scatter_mapbox(
        dff, lat="latitude", lon="longitude", color="mag", size="mag",
        color_continuous_scale="Reds", zoom=0,
        center=dict(lat=dff['latitude'].mean() if not dff.empty else 1.2, 
                    lon=dff['longitude'].mean() if not dff.empty else -77.2),
        mapbox_style="carto-positron"
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, template="plotly_white")

    # Estadísticas dinámicas
    stat1 = html.Div([html.H4(f"{len(dff)}"), html.P("Sismos en Selección", className="small")])
    stat2 = html.Div([html.H4(f"{dff['mag'].max() if not dff.empty else 0}"), html.P("Mag. Máxima", className="small")])
    stat3 = html.Div([html.H4(f"{dff['depth'].mean():.1f}" if not dff.empty else 0), html.P("Prof. Media (Km)", className="small")])

    return fig, stat1, stat2, stat3

@callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    [State("report-mag-slider", "value"),
     State("report-depth-slider", "value"),
     State("report-date-picker", "start_date"),
     State("report-date-picker", "end_date")],
    prevent_initial_call=True,
)
def export_filtered_csv(n_clicks, mag_range, depth_range, start_date, end_date):
    from modules import data_handler
    df = data_handler.get_data()
    
    dff = df[
        (df['mag'] >= mag_range[0]) & (df['mag'] <= mag_range[1]) &
        (df['depth'] >= depth_range[0]) & (df['depth'] <= depth_range[1]) &
        (df['time'] >= start_date) & (df['time'] <= end_date)
    ]
    
    return dcc.send_data_frame(dff.to_csv, f"reporte_personalizado_{start_date}.csv", index=False)