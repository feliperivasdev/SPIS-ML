import pandas as pd
import numpy as np
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
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Reproductor Sísmico del Periodo Filtrado", className="fw-bold"),
                        dbc.CardBody([
                            html.Div(id="storytelling-summary", className="mb-3"),
                            dbc.Row([
                                dbc.Col(dcc.Graph(id="storytelling-map-animation", style={"height": "40vh"}), width=12, lg=7),
                                dbc.Col(dcc.Graph(id="storytelling-trend", style={"height": "40vh"}), width=12, lg=5),
                            ])
                        ])
                    ], className="shadow-sm border-0 mt-4")
                ], width=12)
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
    Output("date_picker", "end_date"),
    Output("storytelling-summary", "children"),
    Output("storytelling-map-animation", "figure"),
    Output("storytelling-trend", "figure")],
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
        story_empty = html.P("No hay datos disponibles para construir el storytelling.", className="text-muted")
        return [go.Figure()] * 3 + ["0", "0", "0", mag_range, start, end, story_empty, go.Figure(), go.Figure()]

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

    # 9. Storytelling dinámico con los mismos filtros
    if dff_sorted.empty:
        story_summary = html.P("No hay eventos en el rango seleccionado para generar narrativa.", className="text-muted")
        story_map_anim = px.scatter_geo(title="Sin datos para reproducción")
        story_fig = px.line(title="Sin datos para sismograma")
    else:
        fecha_min = pd.to_datetime(dff_sorted['time'], errors='coerce').min()
        fecha_max = pd.to_datetime(dff_sorted['time'], errors='coerce').max()
        evento_max = dff_sorted.loc[dff_sorted['mag'].idxmax()]
        profundidad_media = dff_sorted['depth'].mean()
        pct_superficiales = ((dff_sorted['depth'] <= 70).sum() / len(dff_sorted)) * 100

        zona_top = "No disponible"
        if 'place' in dff_sorted.columns and dff_sorted['place'].notna().any():
            zona_top = dff_sorted['place'].mode().iloc[0]

        story_summary = html.Div([
            html.P(
                f"En este filtro se observan {len(dff_sorted):,} eventos entre "
                f"{fecha_min.strftime('%Y-%m-%d') if pd.notna(fecha_min) else 'N/A'} y "
                f"{fecha_max.strftime('%Y-%m-%d') if pd.notna(fecha_max) else 'N/A'}."
            ),
            html.Ul([
                html.Li(f"Evento de mayor magnitud: M {evento_max['mag']:.2f} con profundidad {evento_max['depth']:.1f} km."),
                html.Li(f"Profundidad media del periodo: {profundidad_media:.1f} km."),
                html.Li(f"Proporción de sismos superficiales (≤70 km): {pct_superficiales:.1f}%"),
                html.Li(f"Zona con mayor recurrencia en el filtro: {zona_top}."),
                html.Li("El mapa incluye controles Play/Pause para reproducir la secuencia sísmica.")
            ], className="mb-0")
        ])

        trend_df = dff_sorted.copy()
        trend_df['time'] = pd.to_datetime(trend_df['time'], errors='coerce')
        trend_df = trend_df.dropna(subset=['time'])
        trend_df = trend_df.sort_values('time')

        # Mapa animado (tipo páginas de monitoreo sísmico)
        span_days = (trend_df['time'].max() - trend_df['time'].min()).days if not trend_df.empty else 0
        if span_days <= 90:
            trend_df['frame_tiempo'] = trend_df['time'].dt.strftime('%Y-%m-%d')
        else:
            trend_df['frame_tiempo'] = trend_df['time'].dt.to_period('M').astype(str)

        if trend_df.empty or not {'latitude', 'longitude'}.issubset(trend_df.columns):
            story_map_anim = px.scatter_geo(title="Sin datos geográficos para reproducción")
        else:
            story_map_anim = px.scatter_geo(
                trend_df,
                lat='latitude',
                lon='longitude',
                size='mag',
                color='mag',
                hover_name='place' if 'place' in trend_df.columns else None,
                animation_frame='frame_tiempo',
                projection='natural earth',
                color_continuous_scale='Turbo',
                title='Mapa Animado de Eventos'
            )
            story_map_anim.update_layout(template="plotly_white", margin={"t":40, "b":0})

        # Sismograma visual continuo (estilo traza cardiográfica)
        if trend_df.empty:
            story_fig = px.line(title="Sin datos temporales para sismograma")
        else:
            wave_events = trend_df[['time', 'mag']].copy()
            max_wave_events = 300
            if len(wave_events) > max_wave_events:
                wave_events = wave_events.sample(n=max_wave_events, random_state=42).sort_values('time')

            t_min = wave_events['time'].min().timestamp()
            t_max = wave_events['time'].max().timestamp()
            if t_max == t_min:
                t_max = t_min + 1

            n_points = max(800, min(2400, len(wave_events) * 14))
            x_norm = np.linspace(0, 1, n_points)
            signal = 0.04 * np.sin(np.linspace(0, 40, n_points))

            mag_min = wave_events['mag'].min()
            mag_span = max(wave_events['mag'].max() - mag_min, 0.01)
            base_width = np.clip(0.22 / max(len(wave_events), 1), 0.0008, 0.012)

            for _, row in wave_events.iterrows():
                peak_pos = (row['time'].timestamp() - t_min) / (t_max - t_min)
                amp = 0.55 + 1.45 * ((row['mag'] - mag_min) / mag_span)
                width = base_width

                q_wave = -0.28 * amp * np.exp(-((x_norm - (peak_pos - 1.4 * width)) / (0.75 * width)) ** 2)
                r_wave = 1.20 * amp * np.exp(-((x_norm - peak_pos) / (0.45 * width)) ** 2)
                s_wave = -0.40 * amp * np.exp(-((x_norm - (peak_pos + 1.3 * width)) / (0.70 * width)) ** 2)
                t_wave = 0.22 * amp * np.exp(-((x_norm - (peak_pos + 4.8 * width)) / (2.2 * width)) ** 2)
                signal += q_wave + r_wave + s_wave + t_wave

            signal = np.clip(signal, -1.5, 3.4)
            x_time = pd.to_datetime(t_min + x_norm * (t_max - t_min), unit='s')

            story_fig = go.Figure()
            story_fig.add_trace(go.Scatter(
                x=x_time,
                y=signal,
                mode='lines',
                line=dict(color='#0d6efd', width=2.0, shape='spline'),
                name='Señal sísmica sintética'
            ))
            story_fig.update_layout(
                title='Sismograma Sintético del Periodo Filtrado',
                xaxis_title='Tiempo',
                yaxis_title='Amplitud relativa',
                template='plotly_white',
                margin={"t":40, "b":10},
                showlegend=False
            )
            story_fig.update_xaxes(showgrid=True, gridcolor='rgba(120,120,120,0.18)')
            story_fig.update_yaxes(showgrid=True, gridcolor='rgba(120,120,120,0.18)', zeroline=True, zerolinewidth=1)

    return fig_map, info_panel, fig_time, total, avg_mag, max_depth, mag_range, start, end, story_summary, story_map_anim, story_fig