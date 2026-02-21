import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import io
from fpdf import FPDF

def render_reports_module(df):
    # Valores iniciales para los filtros
    min_mag, max_mag = df['mag'].min(), df['mag'].max()
    min_dep, max_dep = df['depth'].min(), df['depth'].max()
    min_date, max_date = df['time'].min(), df['time'].max()

    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("🛠️ Configurador de Reportes Dinámicos", className="text-primary fw-bold"),
                    html.P("Filtra los parámetros y exporta los resultados en PDF o CSV."),
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                # PANEL DE FILTROS
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
                                min_date_allowed=min_date, max_date_allowed=max_date,
                                start_date=min_date, end_date=max_date, className="mb-3"
                            ),
                            
                            html.Hr(),
                            dbc.Button([html.I(className="bi bi-file-earmark-excel me-2"), "Descargar CSV"], 
                                       id="btn-download-csv", color="success", className="w-100 mb-2"),
                            # Cambiamos a un botón que abra el PDF en el navegador para evitar el error de Kaleido
                            dbc.Button([html.I(className="bi bi-file-pdf me-2"), "Descargar Reporte PDF"], 
                                       id="btn-download-pdf", color="danger", className="w-100"),
                            
                            dcc.Download(id="download-dataframe-csv"),
                            dcc.Download(id="download-pdf")
                        ])
                    ], className="shadow-sm")
                ], width=12, lg=4),

                # VISTA PREVIA
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Vista Previa del Mapa (Escala Roja)"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col(html.Div(id="report-stat-1"), width=4),
                                dbc.Col(html.Div(id="report-stat-2"), width=4),
                                dbc.Col(html.Div(id="report-stat-3"), width=4),
                            ], className="text-center mb-3"),
                            dcc.Graph(id="report-preview-map", style={"height": "45vh"}),
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
    if df is None: return go.Figure(), "", "", ""

    dff = df[
        (df['mag'] >= mag_range[0]) & (df['mag'] <= mag_range[1]) &
        (df['depth'] >= depth_range[0]) & (df['depth'] <= depth_range[1]) &
        (df['time'] >= start_date) & (df['time'] <= end_date)
    ]

    # MAPA CON TODO EL MUNDO (Sin centrar en coordenadas fijas) y escala REDS
    fig = px.scatter_geo(
        dff, lat="latitude", lon="longitude", color="mag", size="mag",
        color_continuous_scale="Reds",
        title="Distribución Global de Sismos Filtrados",
        projection="natural earth" # Esto permite ver todo el mapa mundi
    )
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, template="plotly_white")

    stat1 = html.Div([html.H4(f"{len(dff)}"), html.P("Sismos Filtrados", className="small")])
    stat2 = html.Div([html.H4(f"{dff['mag'].max() if not dff.empty else 0}"), html.P("Mag. Máxima", className="small")])
    stat3 = html.Div([html.H4(f"{dff['depth'].mean():.1f}" if not dff.empty else 0), html.P("Prof. Media (Km)", className="small")])

    return fig, stat1, stat2, stat3

@callback(
    Output("download-pdf", "data"),
    Input("btn-download-pdf", "n_clicks"),
    [State("report-mag-slider", "value"),
     State("report-depth-slider", "value"),
     State("report-date-picker", "start_date"),
     State("report-date-picker", "end_date")],
    prevent_initial_call=True
)
def generate_pdf_no_kaleido(n_clicks, mag_range, depth_range, start_date, end_date):
    from modules import data_handler
    df = data_handler.get_data()
    dff = df[
        (df['mag'] >= mag_range[0]) & (df['mag'] <= mag_range[1]) &
        (df['depth'] >= depth_range[0]) & (df['depth'] <= depth_range[1]) &
        (df['time'] >= start_date) & (df['time'] <= end_date)
    ]

    # Crear el PDF (Sin imagen para evitar el error del navegador/kaleido)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "REPORTE SISMOLÓGICO DE INGENIERÍA - SPIS-ML", ln=True, align='C')

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. PARÁMETROS DE FILTRADO", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"- Rango Magnitud: {mag_range[0]} - {mag_range[1]} M", ln=True)
    pdf.cell(0, 8, f"- Rango Profundidad: {depth_range[0]} - {depth_range[1]} Km", ln=True)
    pdf.cell(0, 8, f"- Fecha: {start_date} a {end_date}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. RESUMEN ESTADÍSTICO", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"- Total de sismos en el periodo: {len(dff)}", ln=True)
    pdf.cell(0, 8, f"- Magnitud máxima registrada: {dff['mag'].max()} M", ln=True)
    pdf.cell(0, 8, f"- Profundidad media: {dff['depth'].mean():.2f} Km", ln=True)

    # Tabla de sismos más importantes
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. TOP 15 SISMOS REGISTRADOS (MÁXIMA MAGNITUD)", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(50, 8, "Fecha", 1); pdf.cell(40, 8, "Magnitud", 1); pdf.cell(50, 8, "Profundidad", 1); pdf.cell(50, 8, "Lat/Lon", 1); pdf.ln()

    pdf.set_font("Arial", '', 9)
    top_15 = dff.nlargest(15, 'mag')
    for _, row in top_15.iterrows():
        pdf.cell(50, 7, str(row['time'].date()), 1)
        pdf.cell(40, 7, f"{row['mag']} M", 1)
        pdf.cell(50, 7, f"{row['depth']} Km", 1)
        pdf.cell(50, 7, f"{row['latitude']:.2f}, {row['longitude']:.2f}", 1)
        pdf.ln()

    # --- CAMBIO AQUÍ PARA SOLUCIONAR EL TYPEERROR ---
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, bytearray):
        pdf_bytes = bytes(pdf_output)
    else:
        pdf_bytes = pdf_output

    return dcc.send_bytes(pdf_bytes, "reporte_sismico_ia.pdf")

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
    return dcc.send_data_frame(dff.to_csv, "datos_sismicos_filtrados.csv", index=False)