import os
import sys
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import base64

# Configuración de rutas
sys.path.insert(0, os.path.dirname(__file__))

import modules.data_handler as data_handler
from modules.exploration_module import render_exploration_view
from modules.model_Gutenberg_Richter_module import calcular_gutenberg_richter  as run_gr_analysis
from modules.model_log_regression_module import run_log_regression_analysis
from modules.model_comparison_module import render_model_comparison
from modules.density_module import render_density_analysis
from modules.reports_module import render_reports_module
from preprocessor import preprocess_seismic_data


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)

app.layout = html.Div([
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
                    dcc.Upload(id='upload-data', children=dbc.Button("SELECCIONAR CSV", color="primary", size="lg")),
                    html.Div(id="file-name-display", className="text-muted mt-2"),
                    html.Hr(),
                    html.H5("Paso 2: Procesar e Iniciar"),
                    dbc.Button("PROCESAR Y ANALIZAR", id="btn-run-process", color="success", size="lg"),
                ], className="p-5 border rounded bg-white shadow-sm"),
                html.Div(id="load-status", className="mt-4")
            ], className="text-center", style={"marginTop": "15vh"})
        ])
    ])

# --- VISTA DE DASHBOARD (Fase 1) ---
def render_main_dashboard():
    return html.Div([
        dbc.NavbarSimple(brand="Sistema de Gestión Sísmica - SPIS-ML", color="dark", dark=True),
        dbc.Tabs([
            dbc.Tab(label="Exploración Geográfica", tab_id="tab-exploration"),
            dbc.Tab(label="Modelo Gutenberg-Richter", tab_id="tab-gr"),
            dbc.Tab(label="Regresión Logarítmica", tab_id="tab-log"),
            dbc.Tab(label="Comparativa de Modelos", tab_id="tab-comparison"),
            dbc.Tab(label="Análisis de Densidad", tab_id="tab-density"),
            dbc.Tab(label="Generación de Reportes", tab_id="tab-reports"),
        ], id="tabs-navigation", active_tab="tab-exploration"),
        # Agregamos un Loading para que el usuario sepa que se están calculando los modelos
        dcc.Loading(html.Div(id="tab-content", className="p-4"), type="graph")
    ])

@app.callback(Output('main-layout-container', 'children'), Input('app-state', 'data'))
def switch_phase(state):
    return render_landing_page() if state['phase'] == 0 else render_main_dashboard()

@app.callback(Output("tab-content", "children"), Input("tabs-navigation", "active_tab"))
def render_tab_content(active_tab):
    df = data_handler.get_data()
    if df is None: return dbc.Alert("Error al leer datos.", color="danger")

    if active_tab == "tab-exploration": return render_exploration_view()
    elif active_tab == "tab-gr": return run_gr_analysis(df)
    elif active_tab == "tab-log": return run_log_regression_analysis(df)
    elif active_tab == "tab-comparison": return render_model_comparison(df)
    elif active_tab == "tab-density": return render_density_analysis(df)
    elif active_tab == "tab-reports": return render_reports_module(df)

@app.callback(
    [Output('app-state', 'data'), Output('load-status', 'children'), Output('file-name-display', 'children')],
    Input('btn-run-process', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def process_and_start(n_clicks, contents, filename):
    if not contents: return {'phase': 0}, dbc.Alert("Sube un CSV.", color="warning"), ""
    try:
        content_string = contents.split(',')[1]
        decoded = base64.b64decode(content_string)
        os.makedirs('data', exist_ok=True)
        csv_path = os.path.join('data', filename)
        with open(csv_path, 'wb') as f: f.write(decoded)
        if preprocess_seismic_data(csv_path):
            return {'phase': 1}, "", f"Archivo: {filename}"
        return {'phase': 0}, dbc.Alert("Error en preproceso.", color="danger"), filename
    except Exception as e: return {'phase': 0}, dbc.Alert(f"Error: {e}", color="danger"), ""

if __name__ == "__main__":
    app.run(debug=True)