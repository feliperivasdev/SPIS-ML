import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import linregress
from sklearn.metrics import mean_squared_error, r2_score
from dash import html, dcc
import dash_bootstrap_components as dbc

def run_log_regression_analysis(df, magnitude_col='mag'):
    """
    Segundo Modelo: Regresión Lineal evaluada en ESCALA LINEAL.
    Diferencia el error real del error logarítmico para la comparativa.
    """
    # 1. Preparación de datos
    if magnitude_col not in df.columns and 'mag' in df.columns:
        magnitude_col = 'mag'

    df_clean = df.dropna(subset=[magnitude_col]).copy()
    df_clean[magnitude_col] = pd.to_numeric(df_clean[magnitude_col], errors='coerce')
    df_clean = df_clean.dropna(subset=[magnitude_col])
    
    magnitudes = np.sort(df_clean[magnitude_col].astype(float).values)[::-1]
    n_obs = np.arange(1, len(magnitudes) + 1)
    log_n_obs = np.log10(n_obs)

    # 2. Ajuste Lineal (Matemática de la regresión)
    slope, intercept, r_val, p_val, std_err = linregress(magnitudes, log_n_obs)
    a = intercept
    b = -slope
    
    # 3. Predicciones
    log_n_pred = intercept + slope * magnitudes
    n_pred_linear = 10**log_n_pred # Convertimos de logaritmo a número real de sismos

    # 4. CÁLCULO DE MÉTRICAS (Evaluación sobre NÚMERO REAL de sismos)
    # Esto es lo que hará que el R2 sea diferente al de Gutenberg-Richter
    r2_lineal = r2_score(n_obs, n_pred_linear) 
    rmse_lineal = np.sqrt(mean_squared_error(n_obs, n_pred_linear))

    # 5. Gráfica Interactiva
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=magnitudes, y=n_obs, mode='markers', name='Obs (N real)', marker=dict(color='blue', opacity=0.4)))
    fig.add_trace(go.Scatter(x=magnitudes, y=n_pred_linear, mode='lines', name='Ajuste Lineal', line=dict(color='green', width=3)))

    fig.update_layout(
        title="Regresión: Evaluación en Frecuencia Real (Escala Lineal)",
        xaxis_title="Magnitud (M)", yaxis_title="Número de Eventos (N)",
        template="plotly_white", height=500
    )

    # 6. Interfaz con 4 decimales para evitar el redondeo a 1.000
    return html.Div([
        dbc.Row([
            render_metric_card("Parámetro a (Intercepto)", f"{a:.4f}", "primary"),
            render_metric_card("Parámetro b (Pendiente)", f"{b:.4f}", "success"),
            render_metric_card("R² (Precisión Lineal)", f"{r2_lineal:.4f}", "info"),
            render_metric_card("RMSE (Error Real)", f"{rmse_lineal:.2f}", "warning"),
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardHeader(html.H5("Análisis de Dispersión Lineal", className="mb-0")),
            dbc.CardBody(dcc.Graph(figure=fig))
        ], className="shadow-sm")
    ])

def render_metric_card(title, value, color):
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1 small"),
            html.H3(value, className=f"text-{color} fw-bold")
        ])
    ], className=f"shadow-sm border-start border-{color} border-4"), width=3)