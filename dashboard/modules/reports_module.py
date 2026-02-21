import pandas as pd
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import io

def render_reports_module(df):
    """
    Módulo 5: Generación de Reportes Dinámicos.
    """
    total_sismos = len(df)
    mag_max = df['mag'].max()
    fecha_min = df['time'].min().strftime('%Y-%m-%d')
    fecha_max = df['time'].max().strftime('%Y-%m-%d')

    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("📄 Generador de Reportes Técnicos", className="text-primary fw-bold"),
                    html.P("Exporta los datos y el análisis estadístico según el filtrado actual."),
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                # TARJETA DE EXPORTACIÓN DE DATOS
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Exportar Datos Crudos"),
                        dbc.CardBody([
                            html.P("Descarga el catálogo sísmico filtrado en formato compatible con Excel o software de análisis estadístico."),
                            dbc.Button([html.I(className="bi bi-file-earmark-excel me-2"), "Descargar CSV"], 
                                       id="btn-download-csv", color="success", className="w-100 mb-3"),
                            dcc.Download(id="download-dataframe-csv"),
                        ])
                    ], className="shadow-sm")
                ], width=12, lg=6),

                # TARJETA DE REPORTE EJECUTIVO
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Resumen Estadístico (PDF/Impresión)"),
                        dbc.CardBody([
                            html.P("Genera una ficha con los indicadores clave de la selección actual para informes oficiales."),
                            dbc.Button([html.I(className="bi bi-file-pdf me-2"), "Generar Vista de Impresión"], 
                                       id="btn-print-report", color="danger", className="w-100"),
                        ])
                    ], className="shadow-sm")
                ], width=12, lg=6),
            ], className="mb-4"),

            # VISTA PREVIA DEL REPORTE (Lo que se imprimiría)
            dbc.Row([
                dbc.Col([
                    html.Div(id="report-preview", className="p-4 border bg-light rounded shadow-inner")
                ], width=12)
            ])
        ], fluid=True)
    ])

@callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    prevent_initial_call=True,
)
def export_csv(n_clicks):
    from modules import data_handler
    df = data_handler.get_data()
    return dcc.send_data_frame(df.to_csv, "reporte_sismico_personalizado.csv", index=False)

@callback(
    Output("report-preview", "children"),
    Input("btn-print-report", "n_clicks"),
)
def update_report_preview(n_clicks):
    from modules import data_handler
    df = data_handler.get_data()
    
    if df is None: return "No hay datos cargados."

    # Cálculos dinámicos para el reporte
    return html.Div([
        html.Div([
            html.H2("REPORTE SISMOLÓGICO DE INGENIERÍA", className="text-center fw-bold"),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.P([html.B("Periodo: "), f"{df['time'].min().date()} a {df['time'].max().date()}"]),
                    html.P([html.B("Total de Eventos: "), f"{len(df)}"]),
                ], width=6),
                dbc.Col([
                    html.P([html.B("Magnitud Máxima: "), f"{df['mag'].max()} M"]),
                    html.P([html.B("Promedio de Profundidad: "), f"{df['depth'].mean():.2f} km"]),
                ], width=6),
            ]),
            html.Hr(),
            html.H5("Distribución de Magnitudes"),
            html.P(f"El catálogo muestra que el { (len(df[df['mag'] < 3]) / len(df) * 100):.1f}% de los sismos son micro-sismos (M < 3.0)."),
            html.Br(),
            html.Footer("Generado automáticamente por SPIS-ML Dashboard", className="text-muted small text-center")
        ], id="printable-area")
    ])