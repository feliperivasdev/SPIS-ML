import pandas as pd
import numpy as np
import plotly.express as px
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import io
from fpdf import FPDF
import plotly.io as pio

def render_reports_module(df):
    min_mag, max_mag = df['mag'].min(), df['mag'].max()
    min_dep, max_dep = df['depth'].min(), df['depth'].max()
    min_date, max_date = df['time'].min(), df['time'].max()

    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("📊 Centro de Inteligencia y Reportes Gerenciales", className="text-primary fw-bold"),
                    html.P("Configure los filtros para generar un informe técnico-ejecutivo completo."),
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                # --- COLUMNA FILTROS ---
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Panel de Configuración", className="bg-primary text-white"),
                        dbc.CardBody([
                            html.Label("Magnitud de Interés (M):", className="fw-bold small"),
                            dcc.RangeSlider(id='rep-mag', min=0, max=10, step=0.1, value=[min_mag, max_mag],
                                            marks={i: str(i) for i in range(11)}),
                            
                            html.Label("Profundidad (Km):", className="fw-bold mt-3 small"),
                            dcc.RangeSlider(id='rep-depth', min=0, max=300, step=10, value=[min_dep, max_dep],
                                            marks={0: '0', 150: '150', 300: '300'}),

                            html.Label("Rango Temporal:", className="fw-bold mt-3 small"),
                            dcc.DatePickerRange(id='rep-dates', start_date=min_date, end_date=max_date, className="mb-3"),
                            
                            html.Hr(),
                            dbc.Button([html.I(className="bi bi-file-earmark-pdf-fill me-2"), "Generar Informe Gerencial"], 
                                       id="btn-pdf-gen", color="danger", className="w-100 mb-2 shadow"),
                            dbc.Button([html.I(className="bi bi-file-earmark-spreadsheet me-2"), "Exportar Base de Datos (CSV)"], 
                                       id="btn-csv-gen", color="success", className="w-100"),
                            
                            dcc.Download(id="down-pdf"),
                            dcc.Download(id="down-csv")
                        ])
                    ], className="shadow border-0")
                ], width=12, lg=4),

                # --- COLUMNA VISTA PREVIA ---
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Previsualización del Área de Análisis", className="fw-bold"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col(html.Div(id="ind-1"), width=4),
                                dbc.Col(html.Div(id="ind-2"), width=4),
                                dbc.Col(html.Div(id="ind-3"), width=4),
                            ], className="text-center mb-3 p-2 bg-light rounded"),
                            dcc.Graph(id="rep-map-view", style={"height": "48vh"}),
                        ])
                    ], className="shadow border-0")
                ], width=12, lg=8),
            ])
        ], fluid=True)
    ])

@callback(
    [Output("rep-map-view", "figure"), Output("ind-1", "children"), 
     Output("ind-2", "children"), Output("ind-3", "children")],
    [Input("rep-mag", "value"), Input("rep-depth", "value"),
     Input("rep-dates", "start_date"), Input("rep-dates", "end_date")]
)
def sync_report_ui(mags, depths, start, end):
    from modules import data_handler
    df = data_handler.get_data()
    if df is None: return px.scatter_geo(), "", "", ""

    dff = df[(df['mag'] >= mags[0]) & (df['mag'] <= mags[1]) &
             (df['depth'] >= depths[0]) & (df['depth'] <= depths[1]) &
             (df['time'] >= start) & (df['time'] <= end)]

    fig = px.scatter_geo(dff, lat="latitude", lon="longitude", color="mag", size="mag",
                         color_continuous_scale="Reds", projection="natural earth")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, template="plotly_white")

    i1 = [html.H4(f"{len(dff):,}"), html.P("Eventos", className="small mb-0")]
    i2 = [html.H4(f"{dff['mag'].max() if not dff.empty else 0:.1f}"), html.P("Max M", className="small mb-0")]
    i3 = [html.H4(f"{dff['depth'].mean() if not dff.empty else 0:.1f}"), html.P("P. Media", className="small mb-0")]

    return fig, i1, i2, i3

@callback(
    Output("down-pdf", "data"),
    Input("btn-pdf-gen", "n_clicks"),
    [State("rep-mag", "value"), State("rep-depth", "value"),
     State("rep-dates", "start_date"), State("rep-dates", "end_date")],
    prevent_initial_call=True
)
def generate_executive_pdf(n, mags, depths, start, end):
    from modules import data_handler
    df = data_handler.get_data()
    dff = df[(df['mag'] >= mags[0]) & (df['mag'] <= mags[1]) &
             (df['depth'] >= depths[0]) & (df['depth'] <= depths[1]) &
             (df['time'] >= start) & (df['time'] <= end)]

    # --- GENERAR IMÁGENES DE PLOTLY PARA EL PDF ---
    # 1. Mapa
    fig_map = px.scatter_geo(dff, lat="latitude", lon="longitude", color="mag", size="mag",
                             color_continuous_scale="Reds", projection="natural earth")
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, template="plotly_white")
    img_map = fig_map.to_image(format="png", width=1000, height=500, scale=2)

    # 2. Histograma
    fig_hist = px.histogram(dff, x="mag", nbins=20, color_discrete_sequence=['darkred'], title="Distribución de Magnitudes")
    fig_hist.update_layout(template="plotly_white")
    img_hist = fig_hist.to_image(format="png", width=800, height=400)

    # 3. Perfil de Profundidad
    fig_depth = px.scatter(dff, x="mag", y="depth", color="depth", color_continuous_scale="Reds_r")
    fig_depth.update_layout(yaxis=dict(autorange="reversed"), template="plotly_white", title="Perfil de Subducción")
    img_depth = fig_depth.to_image(format="png", width=800, height=400)

    # --- CONSTRUCCIÓN DEL PDF ---
    pdf = FPDF()
    
    # PÁGINA 1: PORTADA Y MAPA
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 22); pdf.set_text_color(150, 0, 0)
    pdf.cell(0, 20, "INFORME GERENCIAL DE RIESGO SÍSMICO", ln=True, align='C')
    
    pdf.set_font("Helvetica", '', 12); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Generado por Sistema SPIS-ML | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "1. Distribución Geográfica de Eventos Seleccionados", ln=True)
    with io.BytesIO(img_map) as img_io:
        pdf.image(img_io, x=10, w=190)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 11); pdf.set_fill_color(245, 245, 245)
    pdf.cell(0, 10, " INDICADORES CLAVE DEL PERIODO", ln=True, fill=True)
    pdf.set_font("Helvetica", '', 10)
    pdf.cell(0, 8, f" - Total de sismos analizados: {len(dff):,}", ln=True)
    pdf.cell(0, 8, f" - Magnitud máxima registrada: {dff['mag'].max():.1f} M", ln=True)
    pdf.cell(0, 8, f" - Promedio de profundidad: {dff['depth'].mean():.1f} km", ln=True)

    # PÁGINA 2: ANALÍTICA GRÁFICA
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "2. Análisis Estadístico y Geológico", ln=True)
    
    with io.BytesIO(img_hist) as img_io:
        pdf.image(img_io, x=15, w=180)
    pdf.ln(5)
    with io.BytesIO(img_depth) as img_io:
        pdf.image(img_io, x=15, w=180)

    # PÁGINA 3: TABLA DE DATOS
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "3. Catálogo de Eventos Críticos (Top 20)", ln=True)
    
    pdf.set_font("Helvetica", 'B', 9); pdf.set_fill_color(200, 0, 0); pdf.set_text_color(255, 255, 255)
    pdf.cell(45, 8, "Fecha UTC", 1, 0, 'C', True)
    pdf.cell(30, 8, "Mag (M)", 1, 0, 'C', True)
    pdf.cell(30, 8, "Prof (Km)", 1, 0, 'C', True)
    pdf.cell(85, 8, "Coordenadas (Lat, Lon)", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 8); pdf.set_text_color(0, 0, 0)
    for _, row in dff.nlargest(20, 'mag').iterrows():
        pdf.cell(45, 7, str(row['time'].date()), 1, 0, 'C')
        pdf.cell(30, 7, f"{row['mag']:.1f}", 1, 0, 'C')
        pdf.cell(30, 7, f"{row['depth']:.1f}", 1, 0, 'C')
        pdf.cell(85, 7, f"Lat: {row['latitude']:.3f}, Lon: {row['longitude']:.3f}", 1, 1, 'C')

    pdf_bytes = pdf.output(dest='S')
    return dcc.send_bytes(bytes(pdf_bytes) if isinstance(pdf_bytes, bytearray) else pdf_bytes, "Informe_Gerencial_Sismico.pdf")