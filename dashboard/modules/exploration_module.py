import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State, ctx
import plotly.express as px
import plotly.graph_objects as go
from modules import data_handler

def render_exploration_view():
    """
    Vista final del Módulo 1: Exploración con KPIs, Mapa, Serie Temporal y Funciones de IA.
    """
    return html.Div([
        dbc.Container([
            # --- FILA 1: INDICADORES CLAVE (KPIs) ---
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Eventos Filtrados", className="text-muted mb-1"),
                        html.H2(id="kpi-total", className="text-primary fw-bold")
                    ])
                ], className="shadow-sm border-0 border-start border-primary border-4"), width=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Magnitud Promedio", className="text-muted mb-1"),
                        html.H2(id="kpi-avg-mag", className="text-success fw-bold")
                    ])
                ], className="shadow-sm border-0 border-start border-success border-4"), width=4),
                
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H6("Profundidad Máxima", className="text-muted mb-1"),
                        html.H2(id="kpi-max-depth", className="text-danger fw-bold")
                    ])
                ], className="shadow-sm border-0 border-start border-danger border-4"), width=4),
            ], className="mb-4 mt-3"),

            dbc.Row([
                # --- PANEL IZQUIERDO: CONTROLES ---
                dbc.Col([
                    html.Div([
                        html.H4("🔍 Filtros", className="mb-4 text-primary fw-bold"),
                        
                        html.Label("Rango de Magnitud", className="fw-bold"),
                        dcc.RangeSlider(
                            id="mag_range", min=0, max=10, step=0.1, value=[4, 8],
                            marks={i: str(i) for i in range(11)}, className="mb-4"
                        ),
                        
                        html.Label("Rango de Fecha", className="fw-bold"),
                        dcc.DatePickerRange(
                            id="date_picker", className="mb-4 w-100", display_format='YYYY-MM-DD'
                        ),

                        html.Hr(),
                        html.H6("🧠 Evento Seleccionado", className="text-secondary"),
                        html.Div(id="selected-event-info", className="p-3 border rounded bg-light mb-3", style={"minHeight": "80px"}),
                        
                        dbc.Button("ENCONTRAR SIMILARES", id="btn-similar", color="info", className="w-100 mb-2 fw-bold shadow-sm"),
                        dbc.Button("RESETEAR FILTROS", id="btn-reset", color="secondary", outline=True, className="w-100")
                        
                    ], className="p-4 shadow-sm bg-white rounded", style={"height": "100%"})
                ], width=12, lg=3),

                # --- PANEL DERECHO: MAPA Y GRÁFICO ---
                dbc.Col([
                    html.Div([
                        dcc.Loading(
                            type="circle", 
                            children=dcc.Graph(id="mapa-sismos", style={"height": "50vh"})
                        ),
                        html.Div([
                            html.H5("Evolución Temporal y Resaltado", className="mt-3 ms-2 fw-bold"),
                            dcc.Graph(id="graph-time-series", style={"height": "30vh"})
                        ])
                    ], className="p-2 shadow-sm bg-white rounded")
                ], width=12, lg=9)
            ])
        ], fluid=True)
    ])

@callback(
    [Output("mapa-sismos", "figure"),
     Output("selected-event-info", "children"),
     Output("graph-time-series", "figure"),
     Output("kpi-total", "children"),
     Output("kpi-avg-mag", "children"),
     Output("kpi-max-depth", "children"),
     Output("mag_range", "value"),
     Output("date_picker", "start_date"),
     Output("date_picker", "end_date")],
    [Input("mag_range", "value"),
     Input("date_picker", "start_date"),
     Input("date_picker", "end_date"),
     Input("mapa-sismos", "clickData"),
     Input("btn-similar", "n_clicks"),
     Input("btn-reset", "n_clicks")],
    [State("mapa-sismos", "clickData")]
)
def update_exploration_ui(mag_range, start, end, clickData, n_sim, n_res, current_click):
    # 1. Obtención de datos centralizada
    df = data_handler.get_data()
    if df is None:
        return [go.Figure()] * 3 + ["0", "0", "0", mag_range, start, end]

    # 2. Identificar el activador (Trigger)
    trigger = ctx.triggered_id

    # 3. Lógica de Reseteo
    if trigger == "btn-reset":
        mag_range, start, end = [4, 8], None, None

    # 4. Filtrado Dinámico
    dff = df[(df['mag'] >= mag_range[0]) & (df['mag'] <= mag_range[1])]
    if start and end:
        dff = dff[(dff['time'] >= start) & (dff['time'] <= end)]

    # 5. Lógica de "Eventos Similares"
    if trigger == "btn-similar" and current_click:
        t_mag = current_click['points'][0]['marker.size']
        dff = df[(df['mag'] >= t_mag - 0.2) & (df['mag'] <= t_mag + 0.2)].head(200)

    # 6. Cálculos de KPIs
    if not dff.empty:
        total = f"{len(dff):,}"
        avg_mag = f"{dff['mag'].mean():.2f}"
        max_depth = f"{dff['depth'].max():.1f} km"
    else:
        total, avg_mag, max_depth = "0", "0", "0 km"

    # 7. Construcción de Gráficos
    # MAPA
    fig_map = px.scatter_mapbox(
        dff, lat="latitude", lon="longitude", size="mag", color="mag",
        hover_name="place" if "place" in dff.columns else None,
        mapbox_style="carto-positron", zoom=1,
        color_continuous_scale="Viridis"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, clickmode='event+select')

    # SERIE TEMPORAL (Scatter para permitir resaltado)
    dff_sorted = dff.sort_values('time')
    if dff_sorted.empty:
        fig_time = px.scatter(title="Sin datos bajo estos filtros")
    else:
        fig_time = px.scatter(
            dff_sorted, x='time', y='mag', 
            labels={'time': 'Fecha', 'mag': 'Magnitud'},
            opacity=0.4, template="plotly_white"
        )
    
    # 8. Lógica de Resaltado (Highlight)
    info_panel = html.P("Haz clic en un sismo para detalles.", className="text-muted small italic")
    
    if clickData and not dff_sorted.empty:
        p = clickData['points'][0]
        lugar = p.get('hovertext', 'Ubicación desconocida')
        m_size = p.get('marker.size', 0)
        
        info_panel = html.Div([
            html.B(lugar, className="text-primary d-block"),
            html.Span(f"Magnitud: {m_size}", className="badge bg-primary")
        ])
        
        # Añadir el Diamante Rojo de resaltado en la serie temporal
        # Intentamos obtener la fecha del punto, si no, la primera del DF
        punto_x = p.get('x') if 'x' in p else dff_sorted['time'].iloc[0]
        fig_time.add_trace(go.Scatter(
            x=[punto_x], y=[m_size],
            mode="markers",
            marker=dict(size=14, color="red", symbol="diamond", line=dict(width=2, color="white")),
            name="Seleccionado"
        ))

    fig_time.update_layout(showlegend=False, margin={"t":10, "b":10})

    return fig_map, info_panel, fig_time, total, avg_mag, max_depth, mag_range, start, end