import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import linregress
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from dash import html, dcc
import dash_bootstrap_components as dbc

def run_log_regression_analysis(df, magnitude_col='mag'):
    """
    Segundo Modelo: Regresión Lineal optimizada en Escala Logarítmica.
    Calcula el ajuste directo sobre log10(N) y devuelve la interfaz para Dash.
    """
    # 1. Preparación de datos (Normalización de nombres y tipos)
    if magnitude_col not in df.columns and 'mag' in df.columns:
        magnitude_col = 'mag'

    df_clean = df.dropna(subset=[magnitude_col]).copy()
    df_clean[magnitude_col] = pd.to_numeric(df_clean[magnitude_col], errors='coerce')
    df_clean = df_clean.dropna(subset=[magnitude_col])
    
    # Ordenar magnitudes de mayor a menor y calcular N acumulado
    magnitudes = np.sort(df_clean[magnitude_col].astype(float).values)[::-1]
    n_obs = np.arange(1, len(magnitudes) + 1)
    
    # 2. Transformación Logarítmica (El núcleo del modelo)
    log_n_obs = np.log10(n_obs)

    # 3. Ajuste Lineal (Regresión Lineal Simple)
    slope, intercept, r_val, p_val, std_err = linregress(magnitudes, log_n_obs)
    a = intercept
    b = -slope
    
    # Predicciones en escala logarítmica
    log_n_pred = intercept + slope * magnitudes

    # 4. Cálculo de Métricas de Error
    rmse = np.sqrt(mean_squared_error(log_n_obs, log_n_pred))
    mae = mean_absolute_error(log_n_obs, log_n_pred)
    r2 = r2_score(log_n_obs, log_n_pred)
    
    # Error porcentual respecto al promedio logarítmico
    mean_log_obs = np.mean(log_n_obs)
    rmse_pct = (rmse / mean_log_obs) * 100 if mean_log_obs != 0 else 0

    # 5. Gráfica Interactiva con Plotly
    fig = go.Figure()
    
    # Scatter de puntos observados (en escala logarítmica)
    fig.add_trace(go.Scatter(
        x=magnitudes, y=log_n_obs, 
        mode='markers', name='Datos Observados (log N)',
        marker=dict(color='rgba(0, 123, 255, 0.5)', size=5)
    ))
    
    # Línea de tendencia (Regresión)
    fig.add_trace(go.Scatter(
        x=magnitudes, y=log_n_pred, 
        mode='lines', name=f'Ajuste Log-Lineal (b={b:.2f})',
        line=dict(color='red', width=3)
    ))

    fig.update_layout(
        title="Regresión Lineal sobre Escala Logarítmica",
        xaxis_title="Magnitud (M)",
        yaxis_title="log₁₀ N(M)",
        template="plotly_white",
        height=500,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99)
    )

    # 6. Construcción de la Interfaz (Cards + Graph)
    return html.Div([
        dbc.Row([
            render_metric_card("Parámetro a (Intercepto)", f"{a:.4f}", "primary"),
            render_metric_card("Parámetro b (Pendiente)", f"{b:.4f}", "success"),
            render_metric_card("R² (Bondad de Ajuste)", f"{r2:.3f}", "info"),
            render_metric_card("RMSE (Error Log)", f"{rmse:.4f}", "warning"),
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardHeader(html.H5("Visualización de la Regresión", className="mb-0")),
            dbc.CardBody(dcc.Graph(figure=fig))
        ], className="shadow-sm")
    ])

def render_metric_card(title, value, color):
    """Función auxiliar para generar tarjetas de métricas consistentes."""
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted mb-1 small"),
            html.H3(value, className=f"text-{color} fw-bold")
        ])
    ], className=f"shadow-sm border-start border-{color} border-4"), width=3)