import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output
import plotly.express as px
import modules.data_handler as data_handler

def render_exploration_view():
    return html.Div([
        dbc.Row([
            # Panel de Filtros
            dbc.Col([
                html.Div([
                    html.H4("🔍 Filtros Dinámicos", className="text-primary fw-bold mb-4"),
                    
                    html.Label("Rango de Magnitud", className="fw-bold"),
                    dcc.RangeSlider(
                        id="mag_range", min=0, max=10, step=0.1, value=[4, 8],
                        marks={i: str(i) for i in range(11)},
                        className="mb-4"
                    ),
                    
                    html.Label("Rango de Fechas", className="fw-bold"),
                    dcc.DatePickerRange(
                        id="date_picker",
                        className="w-100 mb-4",
                        display_format='YYYY-MM-DD'
                    ),
                    
                    html.Hr(),
                    html.H6("🧠 Info del Evento", className="text-secondary"),
                    html.Div(id="selected-event-info", children=[
                        html.P("Haz clic en un sismo del mapa para ver sus detalles.", className="small text-muted italic")
                    ], className="p-3 border rounded bg-light")
                    
                ], className="p-4 shadow-sm bg-white rounded", style={"minHeight": "80vh"})
            ], width=3),

            # Visualizaciones
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Loading(
                            type="default",
                            children=dcc.Graph(id="mapa-sismos", style={"height": "50vh"})
                        ),
                        html.Hr(),
                        dcc.Graph(id="graph-time-series", style={"height": "30vh"})
                    ])
                ], className="shadow-sm")
            ], width=9)
        ])
    ])

@callback(
    [Output("mapa-sismos", "figure"),
     Output("selected-event-info", "children"),
     Output("graph-time-series", "figure")],
    [Input("mag_range", "value"),
     Input("date_picker", "start_date"),
     Input("date_picker", "end_date"),
     Input("mapa-sismos", "clickData")]
)
def update_exploration_ui(mag_range, start_date, end_date, clickData):
    df = data_handler.get_data()
    
    if df is None:
        empty_fig = px.scatter_mapbox(lat=[0], lon=[0], zoom=1).update_layout(mapbox_style="carto-positron")
        return empty_fig, "No hay datos.", px.line()

    # 1. Filtrado
    dff = df[(df['mag'] >= mag_range[0]) & (df['mag'] <= mag_range[1])]
    
    if start_date and end_date:
        dff = dff[(dff['time'] >= start_date) & (dff['time'] <= end_date)]

    # 2. Mapa
    fig_map = px.scatter_mapbox(
        dff, lat="latitude", lon="longitude", size="mag", color="mag",
        hover_name="place", mapbox_style="carto-positron", zoom=2,
        color_continuous_scale="Viridis"
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, clickmode='event+select')

    # 3. Info Panel
    info = html.P("Haz clic en un sismo del mapa.", className="small text-muted")
    if clickData:
        p = clickData['points'][0]
        lugar = p.get('hovertext', 'Desconocido')
        mag = p.get('marker.size', 'N/A')
        info = html.Div([
            html.B(f"📍 {lugar}"),
            html.P(f"Magnitud: {mag}", className="mb-0")
        ])

    # 4. Serie Temporal
    dff_sorted = dff.sort_values('time')
    fig_time = px.line(dff_sorted, x='time', y='mag', title="Evolución de Magnitudes")
    fig_time.update_layout(template="plotly_white", margin={"t":30})

    return fig_map, info, fig_time