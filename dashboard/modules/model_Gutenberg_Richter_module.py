import pandas as pd
import numpy as np
import scipy.stats
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc

def calcular_gutenberg_richter(df, magnitud_col='mag'):
    """
    Realiza el ajuste de la ley de Gutenberg-Richter: log10(N) = a - b*M
    """
    # Limpieza rápida y asegurarnos que la columna es numérica
    if magnitud_col not in df.columns and 'mag' in df.columns:
        magnitud_col = 'mag'

    df_clean = df.dropna(subset=[magnitud_col]).copy()
    df_clean[magnitud_col] = pd.to_numeric(df_clean[magnitud_col], errors='coerce')
    df_clean = df_clean.dropna(subset=[magnitud_col])

    # 1. Ordenar magnitudes y calcular N acumulado
    magnitudes = np.sort(df_clean[magnitud_col].astype(float).values)[::-1]
    N_obs = np.arange(1, len(magnitudes) + 1)

    # 2. Ajuste Lineal (Regresión sobre log10)
    # log10(N) = slope * M + intercept
    slope, intercept, r, p, se = scipy.stats.linregress(magnitudes, np.log10(N_obs))
    a = intercept
    b = -slope

    # 3. Predicciones y Métricas
    N_pred = 10**(a - b * magnitudes)
    rmse = np.sqrt(mean_squared_error(N_obs, N_pred))
    r2 = r2_score(N_obs, N_pred)

    # 4. Cálculo de Probabilidad (Ejemplo M=8.5, T=1 año)
    # Asumimos que el dataset cubre 44.19 años según tu Colab
    M_target = 8.5
    N_target = 10**(a - b * M_target)
    tasa_anual = N_target / 44.19
    prob_1_anio = (1 - np.exp(-tasa_anual * 1)) * 100

    # 5. Generar la Gráfica en Plotly (para que sea interactiva en Dash)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=magnitudes, y=N_obs, mode='markers', name='Observado', marker=dict(color='blue', size=4)))
    fig.add_trace(go.Scatter(x=magnitudes, y=N_pred, mode='lines', name=f'Ajuste (b={b:.2f})', line=dict(color='red', width=3)))
    
    fig.update_layout(
        title="Ley de Gutenberg-Richter (Distribución Frecuencia-Magnitud)",
        xaxis_title="Magnitud (M)",
        yaxis_title="N (Acumulado)",
        yaxis_type="log",
        template="plotly_white"
    )

    def render_metric_card(title, value):
        return dbc.Card([
            dbc.CardBody([
                html.H6(title, className="text-muted mb-1"),
                html.H3(value, className="text-primary fw-bold")
            ])
        ], className="shadow-sm border-start border-primary border-4")

    # Layout compatible con Dash (similar al otro módulo)
    layout = html.Div([
        dbc.Row([
            dbc.Col(render_metric_card("Parámetro a", f"{a:.4f}"), width=3),
            dbc.Col(render_metric_card("Parámetro b", f"{b:.4f}"), width=3),
            dbc.Col(render_metric_card("RMSE", f"{rmse:.2f}"), width=3),
            dbc.Col(render_metric_card("Prob. 1 año (%)", f"{prob_1_anio:.2f}%"), width=3),
        ], className="mb-4"),

        dbc.Card([
            dbc.CardBody([
                dcc.Graph(figure=fig)
            ])
        ], className="shadow-sm")
    ])

    return layout


def run_gr_analysis(df, magnitud_col='mag'):
    """Compatibilidad: wrapper que expone la API esperada por la app."""
    return calcular_gutenberg_richter(df, magnitud_col=magnitud_col)