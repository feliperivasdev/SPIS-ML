# SPIS-ML | Seismic Performance Intelligent System
# Version: 2.2.0
# Author: Felipe Rivas
# GitHub: https://github.com/feliperivasdev

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
from modules.model_Gutenberg_Richter_module import calcular_gutenberg_richter as run_gr_analysis
from modules.model_log_regression_module import run_log_regression_analysis
from modules.model_comparison_module import render_model_comparison
from modules.density_module import render_density_analysis
from modules.reports_module import render_reports_module
from modules.regional_analysis_module import render_regional_analysis
from modules.home_module import render_home_module, register_home_callbacks
from preprocessor import preprocess_seismic_data

# 1. Inicialización de la App
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.LUX, dbc.icons.BOOTSTRAP], 
                suppress_callback_exceptions=True)
app.title = "SPIS-ML | Seismic Performance Intelligent System"

# 2. Referencia para el servidor (Necesario para Render/Gunicorn)
server = app.server

# 3. Registrar los callbacks del módulo Home
register_home_callbacks(app)

# 4. Layout Base
app.layout = html.Div([
    dcc.Store(id='app-state', data={'phase': 0}), # 0: Home, 1: Dashboard
    html.Div(id='main-layout-container'),
    # Componente para scroll automático
    html.Div(id='scroll-target') 
])

# --- VISTA DE BIENVENIDA Y CARGA (Fase 0) ---
def render_landing_page():
    return html.Div([
        render_home_module(), 
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Hr(className="my-5"),
                    html.H2("Configuración de Datos", className="text-center mb-4", id="upload-anchor"),
                    dbc.Card([
                        dbc.CardHeader("📥 Carga de Dataset (CSV)", className="bg-primary text-white fw-bold"),
                        dbc.CardBody([
                            dcc.Upload(
                                id='upload-data',
                                children=html.Div(['Arrastra o ', html.A('Selecciona tu archivo')]),
                                style={
                                    'width': '100%', 'height': '80px', 'lineHeight': '80px',
                                    'borderWidth': '2px', 'borderStyle': 'dashed',
                                    'borderRadius': '10px', 'textAlign': 'center', 'margin': '10px 0'
                                },
                                multiple=False
                            ),
                            html.Div(id='file-name-display', className="text-center mb-3 text-primary fw-bold"),
                            dbc.Button("🚀 Procesar e Iniciar Dashboard", id="btn-run-process", color="success", className="w-100 shadow-sm"),
                            html.Div(id='load-status', className="mt-3")
                        ])
                    ], className="shadow border-0 mb-5")
                ], width={"size": 8, "offset": 2})
            ])
        ], id="upload-section")
    ])

# --- VISTA DE DASHBOARD TÉCNICO (Fase 1) ---
def render_main_dashboard():
    return html.Div([
        dbc.NavbarSimple(
            brand="SPIS-ML | Seismic Performance Intelligent System", 
            brand_href="#", color="primary", dark=True, className="mb-2 shadow"
        ),
        dbc.Tabs([
            dbc.Tab(label="Exploración Geográfica", tab_id="tab-exploration"),
            dbc.Tab(label="Gutenberg-Richter", tab_id="tab-gr"),
            dbc.Tab(label="LSTM", tab_id="tab-log"),
            dbc.Tab(label="Comparativa de Modelos", tab_id="tab-comparison"),
            dbc.Tab(label="Densidad Sísmica", tab_id="tab-density"),
            dbc.Tab(label="Análisis Regional", tab_id="tab-regional"),
            dbc.Tab(label="Reportes Gerenciales", tab_id="tab-reports"),
        ], id="tabs-navigation", active_tab="tab-exploration", className="px-4"),
        
        dcc.Loading(
            html.Div(id="tab-content", className="p-4"), 
            type="dot", color="#e84118"
        )
    ])

# --- CALLBACKS DE NAVEGACIÓN ---

# Switch de Fase (Landing vs Dashboard)
@app.callback(
    Output('main-layout-container', 'children'), 
    Input('app-state', 'data')
)
def switch_phase(state):
    if state.get('phase') == 1:
        return render_main_dashboard()
    return render_landing_page()

# Renderizado de pestañas dentro del Dashboard
@app.callback(
    Output("tab-content", "children"), 
    Input("tabs-navigation", "active_tab")
)
def render_tab_content(active_tab):
    df = data_handler.get_data()
    if df is None:
        return dbc.Alert("Los datos no están disponibles. Por favor, recarga el archivo.", color="warning", className="m-4")

    if active_tab == "tab-exploration": return render_exploration_view()
    elif active_tab == "tab-gr": return run_gr_analysis(df)
    elif active_tab == "tab-log": return run_log_regression_analysis(df)
    elif active_tab == "tab-comparison": return render_model_comparison(df)
    elif active_tab == "tab-density": return render_density_analysis(df)
    elif active_tab == "tab-regional": return render_regional_analysis(df)
    elif active_tab == "tab-reports": return render_reports_module(df)

# --- CALLBACK PARA MOSTRAR NOMBRE DE ARCHIVO ---
@app.callback(
    Output('file-name-display', 'children'),
    Input('upload-data', 'filename'),
    prevent_initial_call=True
)
def show_filename(filename):
    if filename:
        return f"📄 Archivo seleccionado: {filename}"
    return ""

# --- CALLBACK DE PROCESAMIENTO ---
@app.callback(
    [Output('app-state', 'data'), Output('load-status', 'children')],
    Input('btn-run-process', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def process_and_start(n_clicks, contents, filename):
    if not contents:
        return dash.no_update, dbc.Alert("Por favor selecciona un archivo CSV.", color="warning")
    
    try:
        content_string = contents.split(',')[1]
        decoded = base64.b64decode(content_string)
        
        # En Render usamos 'data' o '/tmp'
        os.makedirs('data', exist_ok=True)
        csv_path = os.path.join('data', filename)
        with open(csv_path, 'wb') as f:
            f.write(decoded)
        
        # Llamar al preprocesador (el que limpia los 600MB)
        if preprocess_seismic_data(csv_path):
            return {'phase': 1}, dbc.Alert(f"✅ Dataset {filename} procesado correctamente. Iniciando dashboard...", color="success")
        else:
            return {'phase': 0}, dbc.Alert("❌ El preprocesador falló. Revisa el formato.", color="danger")
            
    except Exception as e:
        return {'phase': 0}, dbc.Alert(f"❌ Error crítico en el servidor: {str(e)}", color="danger")

if __name__ == "__main__":
    app.run(debug=True)