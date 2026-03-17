import pandas as pd
import numpy as np
import scipy.stats
from sklearn.metrics import r2_score
import plotly.graph_objects as go
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

def calcular_gutenberg_richter(df, magnitud_col='mag'):
    # 1. Preparación de datos reales
    df_clean = df.dropna(subset=[magnitud_col]).copy()
    df_clean[magnitud_col] = pd.to_numeric(df_clean[magnitud_col], errors='coerce')
    df_clean = df_clean.dropna(subset=[magnitud_col])

    magnitudes = np.sort(df_clean[magnitud_col].values)[::-1]
    n_obs = np.arange(1, len(magnitudes) + 1)
    log_n_obs = np.log10(n_obs)

    # 2. Ajuste Lineal Matemático
    slope, intercept, r_val, p_val, se = scipy.stats.linregress(magnitudes, log_n_obs)
    a, b = intercept, -slope

    # 3. CÁLCULO DINÁMICO DEL R²
    log_n_pred = intercept + slope * magnitudes
    r2_dinamico = r2_score(log_n_obs, log_n_pred)

    # 4. Calcular años totales para tasa anual
    total_years = 1.0
    if 'time' in df_clean.columns:
        try:
            fechas = pd.to_datetime(df_clean['time'], errors='coerce').dropna()
            if len(fechas) > 1:
                total_years = max((fechas.max() - fechas.min()).days / 365.25, 1.0)
        except Exception:
            total_years = 1.0

    # 5. Probabilidad por defecto (M > 8.5, 1 año)
    n_target_default = 10 ** (a - b * 8.5)
    tasa_anual_default = n_target_default / total_years
    prob_default = (1 - np.exp(-tasa_anual_default * 1)) * 100

    # 6. Gráfico G-R
    fig_gr = (
        go.Figure()
        .add_trace(go.Scatter(x=magnitudes, y=n_obs, mode='markers', name='Datos Reales',
                              marker=dict(color='steelblue', opacity=0.5)))
        .add_trace(go.Scatter(x=magnitudes, y=10**log_n_pred, mode='lines', name='Ajuste G-R',
                              line=dict(color='crimson', width=2)))
    )
    fig_gr.update_layout(
        yaxis_type="log", template="plotly_white",
        title="Modelo Gutenberg-Richter Real",
        xaxis_title="Magnitud (M)", yaxis_title="Número de Eventos N(≥M)"
    )

    # 7. Rango dinámico de magnitudes para el slider
    mag_min_val = float(np.floor(magnitudes.min() * 10) / 10)
    mag_max_val = float(np.ceil(magnitudes.max() * 10) / 10)
    mag_default = round(min(8.5, mag_max_val), 1)

    # Marks para el slider
    marks_step = round((mag_max_val - mag_min_val) / 4, 1)
    slider_marks = {round(mag_min_val + i * marks_step, 1): f"{round(mag_min_val + i * marks_step, 1)}"
                    for i in range(5)}

    # 8. Interfaz
    return html.Div([
        # Store con parámetros del modelo
        dcc.Store(id='gr-params-store', data={'a': a, 'b': b, 'total_years': total_years,
                                               'mag_min': mag_min_val, 'mag_max': mag_max_val}),

        # Tarjetas estáticas
        dbc.Row([
            render_metric_card("Parámetro a", f"{a:.4f}", "primary"),
            render_metric_card("Parámetro b", f"{b:.4f}", "success"),
            render_metric_card("R² Calculado", f"{r2_dinamico:.4f}", "info"),
            render_metric_card("Prob. M>8.5", f"{prob_default:.4f}%", "danger"),
        ], className="mb-4"),

        # Gráfico G-R
        dbc.Card(dbc.CardBody(dcc.Graph(figure=fig_gr)), className="shadow-sm mb-4"),

        # ── CALCULADORA INTERACTIVA DE PROBABILIDAD ──────────────────────────
        dbc.Card([
            dbc.CardHeader(html.H5("🎯 Calculadora de Probabilidad Interactiva", className="mb-0 text-primary")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Magnitud mínima (M ≥):", className="fw-semibold"),
                        dcc.Slider(
                            id='gr-mag-slider',
                            min=mag_min_val, max=mag_max_val, step=0.1,
                            value=mag_default,
                            marks=slider_marks,
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                    ], width=12, lg=7, className="mb-3 mb-lg-0"),
                    dbc.Col([
                        html.Label("Horizonte de predicción (años):", className="fw-semibold"),
                        dbc.Input(
                            id='gr-years-input', type='number',
                            min=1, max=200, step=1, value=1,
                            placeholder="Ej: 10"
                        ),
                        html.Div(
                            html.Small("Ingresa los años hacia el futuro para calcular la probabilidad.",
                                       className="text-muted"),
                            className="mt-1"
                        )
                    ], width=12, lg=5),
                ], className="align-items-center mb-4"),

                # Panel de resultado
                html.Div(id='gr-prob-output', className="mt-2")
            ])
        ], className="shadow-sm border-0")
    ])


@callback(
    Output('gr-prob-output', 'children'),
    [Input('gr-mag-slider', 'value'),
     Input('gr-years-input', 'value'),
     Input('gr-params-store', 'data')]
)
def update_gr_probability(selected_mag, selected_years, params):
    if params is None or selected_mag is None or selected_years is None:
        return dbc.Alert("Selecciona los parámetros para calcular.", color="secondary")

    try:
        a = params['a']
        b = params['b']
        total_years = params['total_years']
        years = max(int(selected_years), 1)

        # Tasa anual de eventos con M ≥ selected_mag
        n_expected = 10 ** (a - b * selected_mag)
        tasa_anual = n_expected / total_years

        # Probabilidad de Poisson en el horizonte de tiempo
        prob = (1 - np.exp(-tasa_anual * years)) * 100
        prob = min(prob, 100.0)

        color = "success" if prob < 25 else "warning" if prob < 60 else "danger"
        label = "Baja" if prob < 25 else "Moderada" if prob < 60 else "Alta"

        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6("Magnitud seleccionada", className="text-muted mb-1"),
                        html.H3(f"M ≥ {selected_mag:.1f}", className="fw-bold")
                    ], width=4),
                    dbc.Col([
                        html.H6("Horizonte de predicción", className="text-muted mb-1"),
                        html.H3(f"{years} año{'s' if years != 1 else ''}", className="fw-bold")
                    ], width=4),
                    dbc.Col([
                        html.H6("Probabilidad estimada", className="text-muted mb-1"),
                        html.H2(f"{prob:.2f}%", className=f"fw-bold text-{color}"),
                        dbc.Badge(f"Riesgo {label}", color=color, className="mt-1")
                    ], width=4),
                ], className="text-center"),
                html.Hr(),
                html.Small([
                    html.Strong("Método: "), "Distribución de Poisson — P = 1 − e",
                    html.Sup("−λt"),
                    f"  |  Tasa anual estimada (λ): {tasa_anual:.4f} eventos/año  |  "
                    f"Parámetros G-R: a={a:.4f}, b={b:.4f}  |  "
                    f"Período del catálogo: {total_years:.1f} años"
                ], className="text-muted")
            ])
        ], className=f"border-{color} border-2")
    except Exception as e:
        return dbc.Alert(f"Error al calcular: {str(e)}", color="danger")


def render_metric_card(title, value, color):
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1"),
            html.H3(value, className=f"text-{color} fw-bold")
        ])
    ], className=f"shadow-sm border-start border-{color} border-4"), width=3)