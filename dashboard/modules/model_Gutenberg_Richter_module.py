import pandas as pd
import numpy as np
import scipy.stats
from sklearn.metrics import mean_squared_error, r2_score
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc

def run_gr_analysiser(df, magnitud_col='mag'):
    """
    Realiza el ajuste de la ley de Gutenberg-Richter: log10(N) = a - b*M
    """
    # 1. Limpieza y preparación (Asegurar tipo float)
    df_clean = df.dropna(subset=[magnitud_col]).copy()
    df_clean[magnitud_col] = pd.to_numeric(df_clean[magnitud_col], errors='coerce')
    df_clean = df_clean.dropna(subset=[magnitud_col])

    magnitudes = np.sort(df_clean[magnitud_col].values)[::-1]
    n_obs = np.arange(1, len(magnitudes) + 1)
    log_n = np.log10(n_obs)

    # 2. Ajuste Lineal
    slope, intercept, r, p, se = scipy.stats.linregress(magnitudes, log_n)
    a, b = intercept, -slope

    # 3. Predicciones y Métricas
    n_pred = 10**(a - b * magnitudes)
    rmse = np.sqrt(mean_squared_error(n_obs, n_pred))
    r2 = r2_score(log_n, log_n) # Ajuste sobre la escala logarítmica

    # 4. Cálculo de Probabilidad (M=8.5 en 1 año)
    # Asumimos 44 años de datos como en tu Colab
    n_target = 10**(a - b * 8.5)
    prob_1_anio = (1 - np.exp(-(n_target / 44.19) * 1)) * 100

    # 5. Gráfica Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=magnitudes, y=n_obs, mode='markers', name='Observado', marker=dict(color='blue', size=4, opacity=0.5)))
    fig.add_trace(go.Scatter(x=magnitudes, y=n_pred, mode='lines', name=f'Ajuste GR (b={b:.2f})', line=dict(color='red', width=3)))
    
    fig.update_layout(
        title="Distribución Frecuencia-Magnitud (Gutenberg-Richter)",
        xaxis_title="Magnitud (M)", yaxis_title="N (Acumulado)",
        yaxis_type="log", template="plotly_white", height=500
    )

    return html.Div([
        dbc.Row([
            render_metric_card("Parámetro a (Actividad)", f"{a:.2f}", "primary"),
            render_metric_card("Parámetro b (Sismicidad)", f"{b:.2f}", "success"),
            render_metric_card("R² Score", f"{r2:.3f}", "info"),
            render_metric_card("Prob. M>8.5 (1 año)", f"{prob_1_anio:.2f}%", "danger"),
        ], className="mb-4"),
        dbc.Card(dbc.CardBody(dcc.Graph(figure=fig)), className="shadow-sm")
    ])

def render_metric_card(title, value, color):
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1"),
            html.H3(value, className=f"text-{color} fw-bold")
        ])
    ], className=f"shadow-sm border-start border-{color} border-4"), width=3)