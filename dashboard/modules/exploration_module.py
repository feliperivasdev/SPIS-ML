import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State, ctx
import plotly.express as px
import io
import base64

def render_exploration_view():
    return html.Div([
        dbc.Container([
            dbc.Row([
                # --- PANEL IZQUIERDO: FILTROS DINÁMICOS ---
                dbc.Col([
                    html.Div([
                        html.H4("🔍 Exploración Inteligente", className="mb-4 text-primary"),
                        
                        html.Label("Búsqueda por Magnitud"),
                        dcc.RangeSlider(
                            id="mag_range", min=0, max=10, step=0.1, value=[4, 9],
                            marks={i: str(i) for i in range(11)},
                            className="mb-4"
                        ),
                        
                        html.Label("Rango de Fecha"),
                        dcc.DatePickerRange(
                            id="date_picker",
                            className="mb-4 w-100"
                        ),

                        html.Hr(),
                        html.H6("🧠 Evento Seleccionado"),
                        html.Div(id="selected-event-info", children=[
                            html.P("Haz clic en un sismo en el mapa para analizarlo.", className="text-muted small")
                        ]),
                        
                        html.Hr(),
                        dbc.Button("Encontrar Eventos Similares", id="btn-similar", color="info", className="w-100 mb-2"),
                        
                    ], className="p-4 shadow-sm bg-white rounded", style={"height": "90vh", "overflowY": "auto"})
                ], width=3),

                # --- PANEL DERECHO: MAPA Y GRÁFICOS RESALTADOS ---
                dbc.Col([
                    html.Div([
                        dcc.Loading(
                            dcc.Graph(id="mapa-sismos", style={"height": "60vh"}, config={'displayModeBar': True})
                        ),
                        html.Div([
                            dbc.Row([
                                dbc.Col(dcc.Graph(id="graph-time-series", style={"height": "30vh"}), width=6),
                                dbc.Col(dcc.Graph(id="graph-depth-dist", style={"height": "30vh"}), width=6),
                            ])
                        ], className="mt-3")
                    ], className="p-2 shadow-sm bg-white rounded")
                ], width=9)
            ])
        ], fluid=True, className="mt-3")
    ])

# --- LÓGICA DE ACTUALIZACIÓN ---
@callback(
    [Output("mapa-sismos", "figure"),
     Output("selected-event-info", "children"),
     Output("graph-time-series", "figure")],
    [Input("mag_range", "value"),
     Input("date_picker", "start_date"),
     Input("date_picker", "end_date"),
     Input("mapa-sismos", "clickData")],
    [State("stored-data-raw", "data")]
)
def update_intelligence(mag_range, start, end, clickData, contents):
    if not contents:
        return px.scatter_mapbox(lat=[0], lon=[0]), "Cargue un archivo primero", px.line()

    # 1. Carga eficiente (Aquí podrías usar una caché para no repetir esto)
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
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception:
        return px.scatter_mapbox(lat=[0], lon=[0]), "Error leyendo datos", px.line()
    
    # Pre-procesamiento básico
    df['time'] = pd.to_datetime(df['time'])
    
    # 2. Filtros dinámicos
    mask = (df['mag'] >= mag_range[0]) & (df['mag'] <= mag_range[1])
    dff = df[mask]

    # 3. Lógica de "Seleccionar sismo directamente en el mapa"
    info_panel = html.P("Haz clic en un sismo en el mapa para analizarlo.", className="text-muted small")
    highlight_point = None
    
    if clickData:
        point_idx = clickData['points'][0]['pointIndex']
        # Obtenemos los datos del punto clicado
        selected_row = dff.iloc[point_idx]
        highlight_point = selected_row
        
        info_panel = html.Div([
            html.B(f"📍 {selected_row['place']}"),
            html.P(f"Magnitud: {selected_row['mag']}"),
            html.P(f"Profundidad: {selected_row['depth']} km"),
            html.P(f"Fecha: {selected_row['time'].strftime('%Y-%m-%d')}")
        ], className="alert alert-primary p-2")

    # 4. Crear Mapa
    fig_map = px.scatter_mapbox(
        dff, lat="latitude", lon="longitude", size="mag", color="mag",
        hover_name="place", mapbox_style="carto-positron", zoom=2,
        color_continuous_scale="Viridis"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, clickmode='event+select')

    # 5. Gráfico de serie temporal con resaltado
    fig_time = px.scatter(dff, x="time", y="mag", title="Evolución Temporal")
    if highlight_point is not None:
        fig_time.add_scatter(x=[highlight_point['time']], y=[highlight_point['mag']], 
                             mode="markers", marker=dict(size=15, color="red"), name="Seleccionado")

    return fig_map, info_panel, fig_time