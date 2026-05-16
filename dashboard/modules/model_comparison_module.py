import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from scipy.stats import linregress
from sklearn.metrics import r2_score

def render_model_comparison(df):
    # 1. Preparación de datos y cálculos dinámicos
    df_clean = df.dropna(subset=['mag']).copy()
    magnitudes = np.sort(df_clean['mag'].astype(float).values)[::-1]
    n_obs = np.arange(1, len(magnitudes) + 1)
    log_n_obs = np.log10(n_obs)

    # Cálculos para Gutenberg-Richter (Evaluación Log)
    slope, intercept, r_val, p_val, se = linregress(magnitudes, log_n_obs)
    log_n_pred = intercept + slope * magnitudes
    r2_gr = r2_score(log_n_obs, log_n_pred)

    # Cálculos para Regresión Logarítmica (Evaluación Lineal)
    n_pred_linear = 10**log_n_pred
    r2_log = r2_score(n_obs, n_pred_linear)

    # Determinación del mejor modelo
    mejor_modelo = "Gutenberg-Richter" if r2_gr > r2_log else "Regresión Logarítmica"
    
    # 2. Componente de Ficha Técnica
    ficha_tecnica = dbc.Card([
        dbc.CardHeader(html.H5("Ficha Técnica del Análisis", className="mb-0 text-black")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.P([html.B("Total Eventos Analizados: "), f"{len(df_clean):,}"]),
                    html.P([html.B("Rango Magnitud: "), f"{df_clean['mag'].min():.1f} - {df_clean['mag'].max():.1f} M"]),
                ], width=6),
                dbc.Col([
                    html.P([html.B("Modelo Ganador: "), html.Span(mejor_modelo, className="text-success fw-bold")]),
                    html.P([html.B("Fecha de Análisis: "), pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')]),
                ], width=6),
            ]),
            html.Hr(),
            html.P([
                html.I(className="bi bi-info-circle-fill me-2"),
                "Los cálculos se realizaron utilizando el catálogo optimizado en formato Parquet, "
                "asegurando la integridad de los datos de la región de Pasto."
            ], className="small text-muted mb-0")
        ])
    ], color="dark", outline=True, className="shadow-sm mt-4")

    # 3. Gráfico Comparativo
    fig = go.Figure(data=[
        go.Bar(name='Gutenberg-Richter', x=['R²'], y=[r2_gr], marker_color='#2ECC71', text=[f"{r2_gr:.4f}"], textposition='auto'),
        go.Bar(name='Regresión Logarítmica', x=['R²'], y=[r2_log], marker_color='#F1C40F', text=[f"{r2_log:.4f}"], textposition='auto')
    ])
    fig.update_layout(barmode='group', template="plotly_white", yaxis=dict(range=[0.8, 1.0]), height=300)

    # 4. Layout Final
    return html.Div([
        html.H3("⚖️ Comparativa y Validación Final", className="text-primary fw-bold mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Métricas de Precisión"),
                    dbc.CardBody(dbc.Table([
                        html.Thead(html.Tr([html.Th("Modelo"), html.Th("R² Calculado")])),
                        html.Tbody([
                            html.Tr([html.Td("Gutenberg-Richter"), html.Td(f"{r2_gr:.4f}", className="fw-bold")]),
                            html.Tr([html.Td("Regresión Logarítmica"), html.Td(f"{r2_log:.4f}", className="fw-bold")]),
                        ])
                    ], bordered=True, hover=True))
                ], className="shadow-sm")
            ], width=6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Contraste Visual R²"),
                dbc.CardBody(dcc.Graph(figure=fig))
            ], className="shadow-sm"), width=6),
        ]),
        
        ficha_tecnica,
        
        dbc.Alert(
            f"Basado en el coeficiente de determinación R², el modelo {mejor_modelo} proporciona el mejor ajuste estadístico para los datos sísmicos analizados.",
            color="success", className="mt-4 shadow-sm border-start border-4"
        )
    ])