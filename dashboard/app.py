import os
import sys
import dash
from dash import html, dcc, Input, Output, State, callback

# Asegurar que el directorio `dashboard` esté en sys.path cuando se ejecute
# el script desde la raíz del repositorio (permite `from modules...` funcionar).
sys.path.insert(0, os.path.dirname(__file__))
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64

# Importamos nuestras vistas modulares
from modules.exploration_module import render_exploration_view
from modules.model_Gutenberg_Richter_module import calcular_gutenberg_richter as run_gr_analysis
from modules.model_log_regression_module import run_log_regression_analysis
import modules.data_handler as data_handler
from preprocessor import preprocess_seismic_data
import os
import json

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)

app.layout = html.Div([
    dcc.Store(id='app-state', data={'phase': 0}),
    # Almacenamos el contenido del CSV para no leer el disco cada vez
    dcc.Store(id='stored-data-raw'), 
    
    html.Div(id='main-layout-container')
])

# --- VISTA DE CARGA (Fase 0) ---
def render_landing_page():
    return html.Div([
        dbc.Container([
            html.Div([
                html.H1("SISMOS ML - PASTO", className="display-4 fw-bold"),
                html.P("Análisis estadístico y predictivo de eventos sísmicos", className="lead mb-5"),
                dcc.Upload(
                    id='upload-data',
                    children=dbc.Button("ABRIR ARCHIVO CSV", color="primary", size="lg", className="px-5 shadow"),
                    multiple=False
                ),
                html.Div([
                    dbc.Button("Preprocesar y Guardar (Parquet)", id="btn-preprocess", color="secondary", className="mt-3 me-2"),
                    dbc.Button("Cargar datos optimizados", id="btn-load-optimized", color="info", className="mt-3"),
                ], className="text-center"),
                html.Div(id="load-status", className="mt-4")
            ], className="text-center p-5 shadow-lg rounded bg-white", style={"marginTop": "20vh"})
        ])
    ], style={"height": "100vh", "backgroundColor": "#f4f4f4"})

# --- VISTA DE ANÁLISIS (Fase 1 con Pestañas) ---
def render_main_dashboard():
    return html.Div([
        dbc.NavbarSimple(brand="Sistema Integral de Gestión Sísmica", color="dark", dark=True, className="mb-0"),
        dbc.Tabs([
            dbc.Tab(label="Exploración Geográfica", tab_id="tab-exploration"),
            dbc.Tab(label="Modelo Gutenberg-Richter", tab_id="tab-gr"),
            dbc.Tab(label="Regresión Logarítmica", tab_id="tab-log"),
        ], id="tabs-navigation", active_tab="tab-exploration"),
        
        html.Div(id="tab-content", className="p-4")
    ])

# --- CONTROLADOR DE FASES ---
@app.callback(
    Output('main-layout-container', 'children'),
    Input('app-state', 'data')
)
def switch_phase(state):
    if state['phase'] == 0:
        return render_landing_page()
    return render_main_dashboard()

# --- CONTROLADOR DE PESTAÑAS (Aquí ocurre la magia) ---
@app.callback(
    Output("tab-content", "children"),
    Input("tabs-navigation", "active_tab"),
    State("stored-data-raw", "data")
)
def render_tab_content(active_tab, contents):
    if not contents:
        return dbc.Alert("No hay datos cargados.", color="danger")

    # `contents` ahora es un dict con {'type': 'csv'|'json', 'data': ...}
    df = None
    try:
        if isinstance(contents, dict):
            if contents.get('type') == 'csv':
                content_type, content_string = contents['data'].split(',')
                decoded = base64.b64decode(content_string)
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif contents.get('type') == 'json':
                df = pd.read_json(contents['data'], orient='records')
        else:
            # backward compatibility: raw csv string
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        return dbc.Alert(f"Error leyendo los datos: {e}", color="danger")

    if active_tab == "tab-exploration":
        return render_exploration_view()
    
    elif active_tab == "tab-gr":
        return html.Div([
            html.H3("Ajuste de Ley Gutenberg-Richter", className="mb-4"),
            run_gr_analysis(df)
        ])
    
    elif active_tab == "tab-log":
        return html.Div([
            html.H3("Regresión Lineal en Escala Logarítmica", className="mb-4"),
            run_log_regression_analysis(df)
        ])

# --- CALLBACK PARA CARGAR EL ARCHIVO ---
@app.callback(
    [Output('app-state', 'data'), Output('stored-data-raw', 'data'), Output('load-status', 'children')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def process_initial_upload(contents, filename):
    if contents and filename and filename.endswith('.csv'):
        # Guardamos el contenido en la store como tipo 'csv' (base64)
        return {'phase': 1}, {'type': 'csv', 'data': contents}, ""
    return {'phase': 0}, None, dbc.Alert("Formato no válido", color="warning")


@app.callback(
    [Output('app-state', 'data'), Output('stored-data-raw', 'data'), Output('load-status', 'children')],
    Input('btn-load-optimized', 'n_clicks'),
    prevent_initial_call=True
)
def load_optimized(_):
    # Intentar cargar el parquet preprocesado desde disco
    df = data_handler.get_data()
    if df is None:
        return {'phase': 0}, None, dbc.Alert("No se encontró el archivo preprocesado. Ejecuta el preprocesador primero.", color="warning")

    # Serializamos a JSON para almacenarlo en dcc.Store
    try:
        payload = {'type': 'json', 'data': df.to_json(orient='records', date_format='iso')}
        return {'phase': 1}, payload, dbc.Alert("Datos optimizados cargados.", color="success")
    except Exception as e:
        return {'phase': 0}, None, dbc.Alert(f"Error al serializar los datos: {e}", color="danger")


@app.callback(
    [Output('app-state', 'data'), Output('stored-data-raw', 'data'), Output('load-status', 'children')],
    Input('btn-preprocess', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def preprocess_and_save(n_clicks, contents, filename):
    if not contents:
        return {'phase': 0}, None, dbc.Alert("Sube un CSV antes de preprocesar.", color="warning")

    # Escribimos temporalmente el CSV al disco y llamamos al preprocesador
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        temp_dir = os.path.join(os.getcwd(), 'data')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, filename or 'uploaded.csv')
        with open(temp_path, 'wb') as f:
            f.write(decoded)

        out = preprocess_seismic_data(temp_path)
        if out is None:
            return {'phase': 0}, None, dbc.Alert("El preprocesador falló.", color="danger")

        # Cargar parquet generado y almacenar en la store
        df = data_handler.get_data()
        payload = {'type': 'json', 'data': df.to_json(orient='records', date_format='iso')}
        return {'phase': 1}, payload, dbc.Alert("Preprocesamiento completado y datos cargados.", color="success")

    except Exception as e:
        return {'phase': 0}, None, dbc.Alert(f"Error en preprocesamiento: {e}", color="danger")

if __name__ == "__main__":
    app.run(debug=True)