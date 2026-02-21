
# import numpy as np
# import pandas as pd
# import plotly.graph_objects as go
# from dash import dcc, html
# import dash_bootstrap_components as dbc
# from sklearn.preprocessing import MinMaxScaler
# from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
# import tensorflow as tf
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import LSTM, Dense, Dropout
# from tensorflow.keras.optimizers import Nadam

# def create_dataset(dataset, look_back=100):
#     dataX, dataY = [], []
#     for i in range(len(dataset) - look_back - 1):
#         a = dataset[i:(i + look_back), 0]
#         dataX.append(a)
#         dataY.append(dataset[i + look_back, 0])
#     return np.array(dataX), np.array(dataY)

# def run_lstm_analysis(df, magnitude_col='Magnitude'):
#     """
#     Tercer Modelo: Red Neuronal LSTM para predicción de series temporales.
#     """
#     # 1. Preparación de datos (Sample para no saturar si es 600MB)
#     series = df[magnitude_col].dropna().values.reshape(-1, 1).astype('float32')
    
#     # Normalización
#     scaler = MinMaxScaler(feature_range=(0, 1))
#     dataset_scaled = scaler.fit_transform(series)

#     # Solo tomamos una parte para el entrenamiento rápido en el Dashboard
#     # (En producción, cargarías un modelo ya entrenado .h5)
#     look_back = 100
#     train_size = int(len(dataset_scaled) * 0.7)
#     train, test = dataset_scaled[0:train_size,:], dataset_scaled[train_size:len(dataset_scaled),:]

#     trainX, trainY = create_dataset(train, look_back)
#     testX, testY = create_dataset(test, look_back)

#     # Reshape [samples, time steps, features]
#     trainX = np.reshape(trainX, (trainX.shape[0], look_back, 1))
#     testX = np.reshape(testX, (testX.shape[0], look_back, 1))

#     # 2. Modelo (Arquitectura simplificada para el Dashboard)
#     model = Sequential([
#         LSTM(32, input_shape=(look_back, 1), activation='tanh'),
#         Dropout(0.2),
#         Dense(1)
#     ])
#     model.compile(optimizer=Nadam(learning_rate=0.001), loss='mse')
    
#     # Entrenamos poco para que el dashboard no muera (puedes ajustar)
#     model.fit(trainX, trainY, epochs=5, batch_size=64, verbose=0)

#     # 3. Predicciones
#     train_predict = model.predict(trainX)
#     test_predict = model.predict(testX)

#     # Invertir normalización
#     train_predict = scaler.inverse_transform(train_predict)
#     test_predict = scaler.inverse_transform(test_predict)
#     y_test_real = scaler.inverse_transform(testY.reshape(-1, 1))

#     # 4. Métricas
#     rmse = np.sqrt(mean_squared_error(y_test_real, test_predict))
#     r2 = r2_score(y_test_real, test_predict)

#     # 5. Gráfica Comparativa (Real vs Predicción)
#     fig = go.Figure()
#     fig.add_trace(go.Scatter(y=y_test_real.flatten()[:200], name="Real", line=dict(color="blue")))
#     fig.add_trace(go.Scatter(y=test_predict.flatten()[:200], name="Predicción LSTM", line=dict(color="red", dash='dash')))
    
#     fig.update_layout(
#         title="Predicción de Magnitud: Real vs LSTM (Últimos 200 eventos)",
#         xaxis_title="Tiempo Secuencial",
#         yaxis_title="Magnitud",
#         template="plotly_white"
#     )

#     return html.Div([
#         dbc.Row([
#             dbc.Col(render_info_card("RMSE", f"{rmse:.4f}"), width=4),
#             dbc.Col(render_info_card("R² Score", f"{r2:.4f}"), width=4),
#             dbc.Col(render_info_card("Estado", "Modelo Entrenado"), width=4),
#         ], className="mb-4"),
#         dcc.Graph(figure=fig)
#     ])

# def render_info_card(title, value):
#     return dbc.Card([
#         dbc.CardBody([
#             html.H6(title, className="text-muted"),
#             html.H3(value, className="text-info")
#         ])
#     ], className="shadow-sm border-top border-info border-4")
