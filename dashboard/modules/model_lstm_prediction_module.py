import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    load_model = None

def create_dataset(dataset, look_back=100):
    dataX, dataY = [], []
    for i in range(len(dataset) - look_back - 1):
        a = dataset[i:(i + look_back), 0]
        dataX.append(a)
        dataY.append(dataset[i + look_back, 0])
    return np.array(dataX), np.array(dataY)

# Cargar modelo pre-entrenado
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'lstm_trained.h5')
model = None
MODEL_AVAILABLE = False

if TF_AVAILABLE and load_model is not None:
    try:
        model = load_model(MODEL_PATH)
        print(f"✓ Modelo LSTM cargado desde {MODEL_PATH}")
        MODEL_AVAILABLE = True
    except Exception as e:
        print(f"⚠ Error cargando LSTM: {str(e)}")
        model = None
        MODEL_AVAILABLE = False
else:
    print("⚠ TensorFlow no disponible. LSTM desactivado.")

def run_lstm_prediction(df, magnitude_col='mag'):
    """
    LSTM Pre-entrenado para predicción de series temporales sísmicas.
    """
    if not MODEL_AVAILABLE or model is None:
        return html.Div([
            dbc.Alert("Modelo LSTM no disponible. Entrena en Colab y sube lstm_trained.h5", color="warning")
        ])

    # 1. Preparación de datos
    series = df[magnitude_col].dropna().values.reshape(-1, 1).astype('float32')

    # Normalización
    scaler = MinMaxScaler(feature_range=(0, 1))
    dataset_scaled = scaler.fit_transform(series)

    # Split train/test
    look_back = 100
    train_size = int(len(dataset_scaled) * 0.7)
    train, test = dataset_scaled[0:train_size,:], dataset_scaled[train_size:len(dataset_scaled),:]

    trainX, trainY = create_dataset(train, look_back)
    testX, testY = create_dataset(test, look_back)

    # Reshape [samples, time steps, features]
    trainX = np.reshape(trainX, (trainX.shape[0], look_back, 1))
    testX = np.reshape(testX, (testX.shape[0], look_back, 1))

    # 2. Usar modelo pre-entrenado (sin entrenar)

    # 3. Predicciones (sin entrenar)
    train_predict = model.predict(trainX, verbose=0)
    test_predict = model.predict(testX, verbose=0)

    # Invertir normalización
    train_predict = scaler.inverse_transform(train_predict)
    test_predict = scaler.inverse_transform(test_predict)
    y_test_real = scaler.inverse_transform(testY.reshape(-1, 1))

    # 4. Métricas
    rmse = np.sqrt(mean_squared_error(y_test_real, test_predict))
    r2 = r2_score(y_test_real, test_predict)

    # 5. Gráfica Comparativa (Real vs Predicción)
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=y_test_real.flatten()[:200], name="Real", line=dict(color="blue")))
    fig.add_trace(go.Scatter(y=test_predict.flatten()[:200], name="Predicción LSTM", line=dict(color="red", dash='dash')))
    
    fig.update_layout(
        title="Predicción de Magnitud: Real vs LSTM (Últimos 200 eventos)",
        xaxis_title="Tiempo Secuencial",
        yaxis_title="Magnitud",
        template="plotly_white"
    )

    return html.Div([
        html.H3("🧠 Predicción LSTM", className="text-primary fw-bold mb-4"),
        dbc.Row([
            dbc.Col(render_info_card("RMSE", f"{rmse:.4f}"), width=4),
            dbc.Col(render_info_card("R² Score", f"{r2:.4f}"), width=4),
            dbc.Col(render_info_card("Estado", "Pre-entrenado"), width=4),
        ], className="mb-4"),
        dcc.Graph(figure=fig)
    ])

def render_info_card(title, value):
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="text-muted"),
            html.H3(value, className="text-info")
        ])
    ], className="shadow-sm border-top border-info border-4")
