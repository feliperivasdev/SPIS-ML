import os
import sys
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import base64

# Configuración de rutas para que encuentre los módulos
sys.path.insert(0, os.path.dirname(__file__))

import modules.data_handler as data_handler
from modules.exploration_module import render_exploration_view
from modules.model_Gutenberg_Richter_module import run_gr_analysiser as run_gr_analysis
from modules.model_log_regression_module import run_log_regression_analysis
from preprocessor import preprocess_seismic_data

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)

app.layout = html.Div([
    # Solo guardamos el estado de la fase (0: Carga, 1: Dashboard)
    dcc.Store(id='app-state', data={'phase': 0}),
    html.Div(id='main-layout-container')
])

# --- VISTA DE CARGA (Fase 0) ---
def render_landing_page():
    return html.Div([
        dbc.Container([
            html.Div([
                html.H1("SISMOS ML - PASTO", className="display-4 fw-bold text-primary"),
                html.P("Análisis de datos sísmicos a gran escala (600MB+)", className="lead mb-5"),
                
                html.Div([
                    html.H5("Paso 1: Seleccionar archivo CSV"),
                    dcc.Upload(
                        id='upload-data',
                        children=dbc.Button("SELECCIONAR CSV", color="primary", size="lg", className="mb-3"),
                        multiple=False
                    ),
                    html.Div(id="file-name-display", className="text-muted mb-3"),
                    
                    html.Hr(),
                    
                    html.H5("Paso 2: Procesar e Iniciar"),
                    dbc.Button("PROCESAR Y ANALIZAR", id="btn-run-process", color="success", size="lg", className="shadow"),
                ], className="p-5 border rounded bg-white shadow-sm"),
                
                html.Div(id="load-status", className="mt-4")
            ], className="text-center", style={"marginTop": "15vh"})
        ])
    ], style={"height": "100vh", "backgroundColor": "#f8f9fa"})

# --- VISTA DE ANÁLISIS (Fase 1) ---
def render_main_dashboard():
    return html.Div([
        dbc.NavbarSimple(brand="Sistema de Gestión Sísmica - SPIS-ML", color="dark", dark=True, className="mb-0"),
        dbc.Tabs([
            dbc.Tab(label="Exploración Geográfica", tab_id="tab-exploration"),
            dbc.Tab(label="Modelo Gutenberg-Richter", tab_id="tab-gr"),
            dbc.Tab(label="Regresión Logarítmica", tab_id="tab-log"),
        ], id="tabs-navigation", active_tab="tab-exploration"),
        html.Div(id="tab-content", className="p-4")
    ])

# --- CALLBACKS DE CONTROL DE INTERFAZ ---
@app.callback(
    Output('main-layout-container', 'children'),
    Input('app-state', 'data')
)
def switch_phase(state):
    return render_landing_page() if state['phase'] == 0 else render_main_dashboard()

@app.callback(
    Output("tab-content", "children"),
    Input("tabs-navigation", "active_tab")
)
def render_tab_content(active_tab):
    df = data_handler.get_data()
    if df is None:
        return dbc.Alert("Error: No se encontró el archivo optimizado en /data.", color="danger")

    if active_tab == "tab-exploration":
        return render_exploration_view()
    elif active_tab == "tab-gr":
        return run_gr_analysis(df)
    elif active_tab == "tab-log":
        return run_log_regression_analysis(df)

# --- CALLBACK PARA PROCESAR EL ARCHIVO ---
@app.callback(
    [Output('app-state', 'data'), Output('load-status', 'children'), Output('file-name-display', 'children')],
    Input('btn-run-process', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def process_and_start(n_clicks, contents, filename):
    if not contents:
        return {'phase': 0}, dbc.Alert("Debe subir un archivo CSV primero.", color="warning"), ""

    try:
        # 1. Guardar el CSV físicamente en el servidor
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        data_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(data_dir, exist_ok=True)
        csv_path = os.path.join(data_dir, filename)
        
        with open(csv_path, 'wb') as f:
            f.write(decoded)

        # 2. Llamar al preprocesador (crea el .parquet)
        out_path = preprocess_seismic_data(csv_path)
        
        if out_path:
            return {'phase': 1}, "", f"Archivo: {filename}"
        else:
            return {'phase': 0}, dbc.Alert("Error durante el preprocesamiento.", color="danger"), filename

    except Exception as e:
        return {'phase': 0}, dbc.Alert(f"Error crítico: {str(e)}", color="danger"), ""

if __name__ == "__main__":
    app.run(debug=True)