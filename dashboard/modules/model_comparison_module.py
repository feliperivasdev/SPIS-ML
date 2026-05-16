import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc
from scipy.stats import linregress
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    load_model = None

# Cargar LSTM pre-entrenado
lstm_model = None
LSTM_AVAILABLE = False

if TF_AVAILABLE and load_model is not None:
    try:
        MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'lstm_trained.h5')
        lstm_model = load_model(MODEL_PATH)
        LSTM_AVAILABLE = True
    except:
        lstm_model = None
        LSTM_AVAILABLE = False

def create_dataset(dataset, look_back=100):
    dataX, dataY = [], []
    for i in range(len(dataset) - look_back - 1):
        a = dataset[i:(i + look_back), 0]
        dataX.append(a)
        dataY.append(dataset[i + look_back, 0])
    return np.array(dataX), np.array(dataY)

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

    # Cálculos para LSTM
    r2_lstm = 0.0
    if LSTM_AVAILABLE and lstm_model is not None:
        try:
            series = df_clean['mag'].values.reshape(-1, 1).astype('float32')
            scaler = MinMaxScaler(feature_range=(0, 1))
            dataset_scaled = scaler.fit_transform(series)

            look_back = 100
            train_size = int(len(dataset_scaled) * 0.7)
            test = dataset_scaled[train_size:, :]

            trainX, trainY = create_dataset(dataset_scaled[:train_size], look_back)
            testX, testY = create_dataset(test, look_back)
            testX = np.reshape(testX, (testX.shape[0], look_back, 1))

            test_predict = lstm_model.predict(testX, verbose=0)
            test_predict_real = scaler.inverse_transform(test_predict)
            testY_real = scaler.inverse_transform(testY.reshape(-1, 1))

            r2_lstm = r2_score(testY_real, test_predict_real)
        except:
            r2_lstm = 0.0

    # Determinación del mejor modelo
    modelos_r2 = {'Gutenberg-Richter': r2_gr, 'Regresión Logarítmica': r2_log}
    if LSTM_AVAILABLE and r2_lstm > 0:
        modelos_r2['LSTM Predicción'] = r2_lstm
    mejor_modelo = max(modelos_r2, key=modelos_r2.get)
    
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
    bars = [
        go.Bar(name='Gutenberg-Richter', x=['R²'], y=[r2_gr], marker_color='#2ECC71', text=[f"{r2_gr:.4f}"], textposition='auto'),
        go.Bar(name='Regresión Logarítmica', x=['R²'], y=[r2_log], marker_color='#F1C40F', text=[f"{r2_log:.4f}"], textposition='auto')
    ]

    if LSTM_AVAILABLE and r2_lstm > 0:
        bars.append(go.Bar(name='LSTM Predicción', x=['R²'], y=[r2_lstm], marker_color='#3498DB', text=[f"{r2_lstm:.4f}"], textposition='auto'))

    fig = go.Figure(data=bars)
    fig.update_layout(barmode='group', template="plotly_white", yaxis=dict(range=[0.0, 1.0]), height=350)

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
                        ] + ([html.Tr([html.Td("LSTM Predicción"), html.Td(f"{r2_lstm:.4f}", className="fw-bold text-info")])] if (LSTM_AVAILABLE and r2_lstm > 0) else []))
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