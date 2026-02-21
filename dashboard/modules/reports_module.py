import pandas as pd
import numpy as np
import plotly.express as px
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import io
from fpdf import FPDF
import plotly.io as pio

# Configuramos el motor de imágenes para que no dependa de navegadores externos si es posible
pio.kaleido.scope.default_format = "png"

def render_reports_module(df):
    min_mag, max_mag = df['mag'].min(), df['mag'].max()
    min_dep, max_dep = df['depth'].min(), df['depth'].max()
    min_date, max_date = df['time'].min(), df['time'].max()

    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("🛠️ Generador de Informes Técnicos Profesionales", className="text-primary fw-bold"),
                    html.P("Reportes con mapas interactivos y analítica avanzada."),
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Configuración del Informe", className="bg-primary text-white"),
                        dbc.CardBody([
                            html.Label("Magnitud (M):", className="fw-bold small"),
                            dcc.RangeSlider(id='rep-mag', min=0, max=10, step=0.1, value=[min_mag, max_mag],
                                            marks={i: str(i) for i in range(11)}),
                            
                            html.Label("Profundidad (Km):", className="fw-bold mt-3 small"),
                            dcc.RangeSlider(id='rep-depth', min=0, max=300, step=10, value=[min_dep, max_dep],
                                            marks={0: '0', 150: '150', 300: '300'}),

                            html.Label("Periodo:", className="fw-bold mt-3 small"),
                            dcc.DatePickerRange(id='rep-dates', start_date=min_date, end_date=max_date, className="mb-3"),
                            
                            html.Hr(),
                            dbc.Button([html.I(className="bi bi-file-pdf me-2"), "Descargar Reporte Completo (PDF)"], 
                                       id="btn-pdf-gen", color="danger", className="w-100 mb-2"),
                            dbc.Button([html.I(className="bi bi-file-csv me-2"), "Exportar Datos (CSV)"], 
                                       id="btn-csv-gen", color="success", className="w-100"),
                            
                            dcc.Download(id="down-pdf"),
                            dcc.Download(id="down-csv")
                        ])
                    ], className="shadow-sm border-0")
                ], width=12, lg=4),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Vista Previa del Mapa", className="fw-bold"),
                        dbc.CardBody([
                            dcc.Graph(id="rep-map-preview", style={"height": "50vh"}),
                        ])
                    ], className="shadow-sm border-0")
                ], width=12, lg=8),
            ])
        ], fluid=True)
    ])

@callback(
    Output("rep-map-preview", "figure"),
    [Input("rep-mag", "value"), Input("rep-depth", "value"),
     Input("rep-dates", "start_date"), Input("rep-dates", "end_date")]
)
def update_preview_map(mags, depths, start, end):
    from modules import data_handler
    df = data_handler.get_data()
    if df is None: return px.scatter_geo()

    dff = df[(df['mag'] >= mags[0]) & (df['mag'] <= mags[1]) &
             (df['depth'] >= depths[0]) & (df['depth'] <= depths[1]) &
             (df['time'] >= start) & (df['time'] <= end)]

    fig = px.scatter_geo(dff, lat="latitude", lon="longitude", color="mag", size="mag",
                         color_continuous_scale="Reds", projection="natural earth",
                         title="Área Filtrada para el Reporte")
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, template="plotly_white")
    return fig

@callback(
    Output("down-pdf", "data"),
    Input("btn-pdf-gen", "n_clicks"),
    [State("rep-mag", "value"), State("rep-depth", "value"),
     State("rep-dates", "start_date"), State("rep-dates", "end_date")],
    prevent_initial_call=True
)
def generate_pdf_with_map(n, mags, depths, start, end):
    from modules import data_handler
    df = data_handler.get_data()
    dff = df[(df['mag'] >= mags[0]) & (df['mag'] <= mags[1]) &
             (df['depth'] >= depths[0]) & (df['depth'] <= depths[1]) &
             (df['time'] >= start) & (df['time'] <= end)]

    # 1. Generamos la imagen del mapa de Plotly EXACTAMENTE como se ve
    fig = px.scatter_geo(dff, lat="latitude", lon="longitude", color="mag", size="mag",
                         color_continuous_scale="Reds", projection="natural earth")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, template="plotly_white")
    
    # Esta es la parte crítica: convertimos el gráfico interactivo a una imagen estática
    img_bytes = fig.to_image(format="png", width=800, height=450, scale=2)

    # 2. Construcción del PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(150, 0, 0)
    pdf.cell(0, 15, "INFORME TÉCNICO SISMOLÓGICO", ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "1. Mapa de Distribución Geográfica", ln=True)
    
    # Insertar la imagen de Plotly directamente
    with io.BytesIO(img_bytes) as img_io:
        pdf.image(img_io, x=10, w=190)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", '', 10)
    pdf.multi_cell(0, 7, f"Este reporte contiene {len(dff)} eventos sísmicos filtrados por el usuario.\n"
                         f"Rango de Magnitud: {mags[0]} a {mags[1]} M\n"
                         f"Rango de Profundidad: {depths[0]} a {depths[1]} km\n"
                         f"Periodo: {start} a {end}")

    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "2. Top 15 Eventos Seleccionados", ln=True)
    
    pdf.set_font("Helvetica", 'B', 9); pdf.set_fill_color(240, 240, 240)
    pdf.cell(45, 8, "Fecha", 1, 0, 'C', True); pdf.cell(30, 8, "Mag", 1, 0, 'C', True)
    pdf.cell(30, 8, "Prof (Km)", 1, 0, 'C', True); pdf.cell(85, 8, "Latitud / Longitud", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 8)
    for _, row in dff.nlargest(15, 'mag').iterrows():
        pdf.cell(45, 7, str(row['time'].date()), 1)
        pdf.cell(30, 7, f"{row['mag']:.2f}", 1, 0, 'C')
        pdf.cell(30, 7, f"{row['depth']:.1f}", 1, 0, 'C')
        pdf.cell(85, 7, f"{row['latitude']:.3f}, {row['longitude']:.3f}", 1, 1)

    pdf_output = pdf.output(dest='S')
    return dcc.send_bytes(bytes(pdf_output) if isinstance(pdf_output, bytearray) else pdf_output, "Reporte_Sismico_IA.pdf")