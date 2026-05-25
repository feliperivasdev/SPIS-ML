# SPIS-ML | Seismic Performance Intelligent System
# Versión simplificada sin dependencias pesadas

import os
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

# Inicialización de la App
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.LUX, dbc.icons.BOOTSTRAP], 
                suppress_callback_exceptions=True)
app.title = "SPIS-ML | Seismic Performance Intelligent System"

# Referencia para el servidor (Necesario para Render/Gunicorn)
server = app.server

# Layout Base
app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand="SPIS-ML | Seismic Performance Intelligent System", 
        brand_href="#", color="primary", dark=True, className="mb-4 shadow"
    ),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🌍 SPIS-ML - Sistema de Análisis Sísmico", className="bg-primary text-white fw-bold"),
                dbc.CardBody([
                    html.H4("Bienvenido al Dashboard Sísmico", className="card-title"),
                    html.P("Esta aplicación está siendo optimizada para Render.", className="card-text"),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            html.H5("📊 Análisis de Datos"),
                            html.Ul([
                                html.Li("Exploración geográfica de sismos"),
                                html.Li("Modelo de Gutenberg-Richter"),
                                html.Li("Regresión logarítmica"),
                            ])
                        ]),
                        dbc.Col([
                            html.H5("📈 Características"),
                            html.Ul([
                                html.Li("Visualización interactiva"),
                                html.Li("Comparativa de modelos"),
                                html.Li("Exportación de reportes"),
                            ])
                        ]),
                    ]),
                    html.Hr(),
                    html.P("Versión: 2.3.0 (Simplificada)", className="text-muted small"),
                    html.P([
                        html.A("GitHub", href="https://github.com/feliperivasdev/SPIS-ML", target="_blank", className="btn btn-primary btn-sm"),
                        " ",
                        html.A("Documentación", href="#", className="btn btn-secondary btn-sm"),
                    ])
                ])
            ], className="shadow border-0 mt-5")
        ], width={"size": 10, "offset": 1})
    ])
], fluid=True, className="p-4")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port, debug=False)
