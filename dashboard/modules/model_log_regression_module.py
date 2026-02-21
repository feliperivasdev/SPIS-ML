import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import linregress
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from dash import html, dcc
import dash_bootstrap_components as dbc

def run_log_regression_analysis(df, magnitude_col='Magnitude'):
    """
    Segundo Modelo: Regresión Lineal en Escala Logarítmica
    """
    # 1. Preparación de datos
    # Aceptar nombres alternativos de columna y forzar tipo numérico para evitar dtype object
    if magnitude_col not in df.columns and 'mag' in df.columns:
        magnitude_col = 'mag'

    df_clean = df.dropna(subset=[magnitude_col]).copy()
    df_clean[magnitude_col] = pd.to_numeric(df_clean[magnitude_col], errors='coerce')
    df_clean = df_clean.dropna(subset=[magnitude_col])
    magnitudes = np.sort(df_clean[magnitude_col].astype(float).values)[::-1]
    N_obs = np.arange(1, len(magnitudes) + 1)
    
    # 2. Transformación Logarítmica
    log_N_obs = np.log10(N_obs)

    # 3. Ajuste Lineal
    slope, intercept, r, p, se = linregress(magnitudes, log_N_obs)
    a = intercept
    b = -slope
    
    # Predicciones
    log_N_pred = intercept + slope * magnitudes

    # 4. Métricas
    rmse = np.sqrt(mean_squared_error(log_N_obs, log_N_pred))
    mae = mean_absolute_error(log_N_obs, log_N_pred)
    r2 = r2_score(log_N_obs, log_N_pred)
    
    mean_obs = np.mean(log_N_obs)
    rmse_pct = (rmse / mean_obs) * 100

    # 5. Gráfica interactiva con Plotly
    fig = go.Figure()
    
    # Datos Observados
    fig.add_trace(go.Scatter(
        x=magnitudes, y=log_N_obs, 
        mode='markers', name='Obs (log N)',
        marker=dict(color='blue', opacity=0.6, size=5)
    ))
    
    # Línea de Ajuste
    fig.add_trace(go.Scatter(
        x=magnitudes, y=log_N_pred, 
        mode='lines', name=f'Ajuste (a={a:.2f}, b={b:.2f})',
        line=dict(color='red', width=2)
    ))

    fig.update_layout(
        title="Regresión Lineal: Ley de Gutenberg–Richter (Log)",
        xaxis_title="Magnitud M",
        yaxis_title="log₁₀ N(M)",
        template="plotly_white",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
    )

    # 6. Layout de retorno para el Dashboard
    return html.Div([
        dbc.Row([
            dbc.Col(render_metric_card("Parámetro a", f"{a:.4f}"), width=3),
            dbc.Col(render_metric_card("Parámetro b", f"{b:.4f}"), width=3),
            dbc.Col(render_metric_card("R² Score", f"{r2:.3f}"), width=3),
            dbc.Col(render_metric_card("RMSE (%)", f"{rmse_pct:.2f}%"), width=3),
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig)
            ])
        ], className="shadow-sm")
    ])

def render_metric_card(title, value):
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1"),
            html.H3(value, className="text-primary fw-bold")
        ])
    ], className="shadow-sm border-start border-primary border-4")