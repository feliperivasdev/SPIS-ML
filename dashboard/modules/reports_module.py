import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import io
import matplotlib
matplotlib.use('Agg') # Modo no interactivo para servidores/Dash
import matplotlib.pyplot as plt
from fpdf import FPDF

def render_reports_module(df):
    # Valores iniciales dinámicos
    min_mag, max_mag = df['mag'].min(), df['mag'].max()
    min_dep, max_dep = df['depth'].min(), df['depth'].max()
    min_date, max_date = df['time'].min(), df['time'].max()

    return html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H3("🛠️ Generador de Informes Técnicos Avanzados", className="text-primary fw-bold"),
                    html.P("Seleccione los parámetros. El reporte incluirá Mapas, Histogramas y Perfiles Geológicos."),
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                # --- PANEL DE FILTROS ---
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Parámetros del Informe", className="bg-primary text-white"),
                        dbc.CardBody([
                            html.Label("Rango de Magnitud (M):", className="fw-bold small"),
                            dcc.RangeSlider(id='rep-mag', min=0, max=10, step=0.1, value=[min_mag, max_mag],
                                            marks={i: str(i) for i in range(11)}),
                            
                            html.Label("Profundidad (Km):", className="fw-bold mt-3 small"),
                            dcc.RangeSlider(id='rep-depth', min=0, max=300, step=10, value=[min_dep, max_dep],
                                            marks={0: '0', 150: '150', 300: '300'}),

                            html.Label("Rango de Fechas:", className="fw-bold mt-3 small"),
                            dcc.DatePickerRange(id='rep-dates', start_date=min_date, end_date=max_date, className="mb-3"),
                            
                            html.Hr(),
                            dbc.Button([html.I(className="bi bi-file-pdf me-2"), "Generar Reporte Completo (PDF)"], 
                                       id="btn-pdf-gen", color="danger", className="w-100 mb-2"),
                            dbc.Button([html.I(className="bi bi-file-csv me-2"), "Exportar Datos (CSV)"], 
                                       id="btn-csv-gen", color="success", className="w-100"),
                            
                            dcc.Download(id="down-pdf"),
                            dcc.Download(id="down-csv")
                        ])
                    ], className="shadow-sm border-0")
                ], width=12, lg=4),

                # --- VISTA PREVIA ---
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Vista Previa de Distribución", className="fw-bold"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col(html.Div(id="st-1"), width=4),
                                dbc.Col(html.Div(id="st-2"), width=4),
                                dbc.Col(html.Div(id="st-3"), width=4),
                            ], className="text-center mb-2 bg-light p-2 rounded"),
                            dcc.Graph(id="rep-map-preview", style={"height": "45vh"}),
                        ])
                    ], className="shadow-sm border-0")
                ], width=12, lg=8),
            ])
        ], fluid=True)
    ])

# --- CALLBACK PARA VISTA PREVIA ---
@callback(
    [Output("rep-map-preview", "figure"), Output("st-1", "children"), 
     Output("st-2", "children"), Output("st-3", "children")],
    [Input("rep-mag", "value"), Input("rep-depth", "value"),
     Input("rep-dates", "start_date"), Input("rep-dates", "end_date")]
)
def update_report_ui(mags, depths, start, end):
    from modules import data_handler
    df = data_handler.get_data()
    if df is None: return go.Figure(), "", "", ""

    dff = df[(df['mag'] >= mags[0]) & (df['mag'] <= mags[1]) &
             (df['depth'] >= depths[0]) & (df['depth'] <= depths[1]) &
             (df['time'] >= start) & (df['time'] <= end)]

    fig = px.scatter_geo(dff, lat="latitude", lon="longitude", color="mag", size="mag",
                         color_continuous_scale="Reds", projection="natural earth",
                         title="Área de Cobertura del Reporte")
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

    s1 = [html.H4(f"{len(dff)}"), html.P("Sismos", className="small mb-0")]
    s2 = [html.H4(f"{dff['mag'].max() if not dff.empty else 0:.1f}"), html.P("Máx Mag", className="small mb-0")]
    s3 = [html.H4(f"{dff['depth'].mean() if not dff.empty else 0:.1f}"), html.P("Prof Prom", className="small mb-0")]

    return fig, s1, s2, s3

# --- GENERADOR DE PDF CON GRÁFICAS RELEVANTES ---
@callback(
    Output("down-pdf", "data"),
    Input("btn-pdf-gen", "n_clicks"),
    [State("rep-mag", "value"), State("rep-depth", "value"),
     State("rep-dates", "start_date"), State("rep-dates", "end_date")],
    prevent_initial_call=True
)
def create_full_pdf_report(n, mags, depths, start, end):
    from modules import data_handler
    df = data_handler.get_data()
    dff = df[(df['mag'] >= mags[0]) & (df['mag'] <= mags[1]) &
             (df['depth'] >= depths[0]) & (df['depth'] <= depths[1]) &
             (df['time'] >= start) & (df['time'] <= end)]

    # --- GENERAR GRÁFICAS CON MATPLOTLIB (Bytes) ---
    def get_plot_bytes(plot_func):
        buf = io.BytesIO()
        plot_func()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        return buf

    # Gráfico 1: Mapa de Dispersión
    def plot_map():
        plt.figure(figsize=(8, 5))
        sc = plt.scatter(dff['longitude'], dff['latitude'], c=dff['mag'], 
                         s=dff['mag']*10, cmap='Reds', alpha=0.6, edgecolors='none')
        plt.colorbar(sc, label='Magnitud (M)')
        plt.title('Distribución Geográfica de Eventos')
        plt.xlabel('Longitud'); plt.ylabel('Latitud')
        plt.grid(True, linestyle='--', alpha=0.5)

    # Gráfico 2: Histograma de Magnitudes
    def plot_hist():
        plt.figure(figsize=(8, 4))
        plt.hist(dff['mag'], bins=15, color='darkred', edgecolor='white', alpha=0.7)
        plt.title('Frecuencia de Magnitudes (Distribución)')
        plt.xlabel('Magnitud (M)'); plt.ylabel('Cantidad de Sismos')

    # Gráfico 3: Perfil de Profundidad
    def plot_depth():
        plt.figure(figsize=(8, 4))
        plt.scatter(dff['mag'], dff['depth'], c=dff['depth'], cmap='Reds_r', alpha=0.5)
        plt.gca().invert_yaxis()
        plt.title('Perfil de Profundidad vs Magnitud')
        plt.xlabel('Magnitud (M)'); plt.ylabel('Profundidad (Km)')

    img_map = get_plot_bytes(plot_map)
    img_hist = get_plot_bytes(plot_hist)
    img_depth = get_plot_bytes(plot_depth)

    # --- CONSTRUCCIÓN DEL PDF ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 18)
    pdf.set_text_color(150, 0, 0)
    pdf.cell(0, 15, "INFORME TÉCNICO SISMOLÓGICO", ln=True, align='C')
    
    pdf.set_font("Helvetica", '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, f"Fecha de reporte: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(10)

    # Sección 1: Parámetros y Mapa
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "1. Localización y Parámetros de Selección", ln=True)
    pdf.set_font("Helvetica", '', 10)
    pdf.multi_cell(0, 7, f"El presente reporte analiza un total de {len(dff)} eventos sísmicos filtrados bajo los siguientes criterios:\n"
                         f"Magnitud: {mags[0]} a {mags[1]} M | Profundidad: {depths[0]} a {depths[1]} Km\n"
                         f"Periodo: {start} a {end}")
    pdf.image(img_map, x=15, w=180)
    pdf.ln(5)

    # Sección 2: Análisis Estadístico
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "2. Análisis de Magnitud y Profundidad", ln=True)
    pdf.image(img_hist, x=15, w=180)
    pdf.ln(5)
    pdf.image(img_depth, x=15, w=180)

    # Sección 3: Tabla de Datos Críticos
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, "3. Listado de Eventos de Mayor Relevancia (Top 15)", ln=True)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(45, 8, "Fecha", 1, 0, 'C', True); pdf.cell(30, 8, "Mag", 1, 0, 'C', True)
    pdf.cell(30, 8, "Prof (Km)", 1, 0, 'C', True); pdf.cell(85, 8, "Ubicación Coordenadas", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 8)
    for _, row in dff.nlargest(15, 'mag').iterrows():
        pdf.cell(45, 7, str(row['time'].date()), 1)
        pdf.cell(30, 7, f"{row['mag']:.2f}", 1, 0, 'C')
        pdf.cell(30, 7, f"{row['depth']:.1f}", 1, 0, 'C')
        pdf.cell(85, 7, f"Lat: {row['latitude']:.3f}, Lon: {row['longitude']:.3f}", 1, 1)

    return dcc.send_bytes(bytes(pdf.output()), "Reporte_Sismico_Avanzado.pdf")

@callback(
    Output("down-csv", "data"),
    Input("btn-csv-gen", "n_clicks"),
    [State("rep-mag", "value"), State("rep-depth", "value"),
     State("rep-dates", "start_date"), State("rep-dates", "end_date")],
    prevent_initial_call=True
)
def export_csv_filtered(n, mags, depths, start, end):
    from modules import data_handler
    df = data_handler.get_data()
    dff = df[(df['mag'] >= mags[0]) & (df['mag'] <= mags[1]) &
             (df['depth'] >= depths[0]) & (df['depth'] <= depths[1]) &
             (df['time'] >= start) & (df['time'] <= end)]
    return dcc.send_data_frame(dff.to_csv, "catalogo_filtrado.csv", index=False)