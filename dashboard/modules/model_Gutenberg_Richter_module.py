import pandas as pd
import numpy as np
import scipy.stats
from sklearn.metrics import r2_score
import plotly.graph_objects as go
from dash import html, dcc
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

    # 3. CÁLCULO DINÁMICO DEL R² (Sin valores fijos)
    log_n_pred = intercept + slope * magnitudes
    # Aquí calculamos el R² comparando lo observado vs la predicción lineal
    r2_dinamico = r2_score(log_n_obs, log_n_pred) 

    # 4. Probabilidad
    n_target = 10**(a - b * 8.5)
    prob_1_anio = (1 - np.exp(-(n_target / 44.19) * 1)) * 100

    # 5. Interfaz (Mostrando 4 decimales para mayor precisión académica)
    return html.Div([
        dbc.Row([
            render_metric_card("Parámetro a", f"{a:.4f}", "primary"),
            render_metric_card("Parámetro b", f"{b:.4f}", "success"),
            render_metric_card("R² Calculado", f"{r2_dinamico:.4f}", "info"),
            render_metric_card("Prob. M>8.5", f"{prob_1_anio:.4f}%", "danger"),
        ], className="mb-4"),
        dbc.Card(dbc.CardBody(dcc.Graph(
            figure=go.Figure()
            .add_trace(go.Scatter(x=magnitudes, y=n_obs, mode='markers', name='Datos Reales'))
            .add_trace(go.Scatter(x=magnitudes, y=10**log_n_pred, mode='lines', name='Ajuste G-R'))
            .update_layout(yaxis_type="log", template="plotly_white", title="Modelo Gutenberg-Richter Real")
        )), className="shadow-sm")
    ])

def render_metric_card(title, value, color):
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1"),
            html.H3(value, className=f"text-{color} fw-bold")
        ])
    ], className=f"shadow-sm border-start border-{color} border-4"), width=3)