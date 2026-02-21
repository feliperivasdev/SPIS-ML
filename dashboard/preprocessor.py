import pandas as pd
import os
import numpy as np

def preprocess_seismic_data(input_path, output_name="sismos_optimizado.parquet"):
    """
    Optimiza un CSV pesado convirtiéndolo a Parquet con tipos de datos eficientes.
    """
    print(f"🚀 Iniciando preprocesamiento de: {input_path}")
    
    # Definir la ruta de salida en la misma carpeta que el input
    output_path = os.path.join(os.path.dirname(input_path), output_name)

    # Definimos las columnas que necesitamos (en minúsculas para nuestra lógica)
    target_cols = ['time', 'latitude', 'longitude', 'depth', 'mag', 'place']
    
    try:
        # 1. Escaneo rápido de columnas para evitar el error de Pylance
        header = pd.read_csv(input_path, nrows=0)
        
        # Identificar qué columnas del CSV original coinciden con nuestro interés
        # (Sin importar si el CSV dice 'Magnitude', 'MAG' o 'mag')
        cols_to_load = [c for c in header.columns if c.lower() in target_cols]
        
        print(f"📊 Columnas detectadas para carga: {cols_to_load}")

        # 2. Carga optimizada
        df = pd.read_csv(input_path, usecols=cols_to_load)
        
        # Estandarizamos nombres a minúsculas
        df.columns = [c.lower() for c in df.columns]

        # 3. Limpieza y Formateo
        # Convertir tiempo (fundamental para el modelo LSTM y Gutenberg)
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        
        # Limpieza de nulos en columnas críticas
        df = df.dropna(subset=['mag', 'time'])

        # 4. DOWNCASTING (Ahorro masivo de memoria RAM)
        # Convertimos de float64 (8 bytes) a float32 (4 bytes)
        # Para coordenadas y magnitud, la precisión de 32 bits es más que suficiente.
        float_cols = df.select_dtypes(include=['float']).columns
        for col in float_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float32)

        # 5. Exportación a Parquet
        # Requiere: pip install pyarrow fastparquet
        df.to_parquet(output_path, compression='snappy', index=False)
        
        print("-" * 30)
        print(f"✅ ¡Preprocesamiento completado!")
        print(f"📂 Archivo generado: {output_path}")
        print(f"📉 Tamaño original: {os.path.getsize(input_path) / (1024*1024):.2f} MB")
        print(f"🚀 Tamaño optimizado: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
        print("-" * 30)
        
        return output_path

    except Exception as e:
        print(f"❌ Error crítico en el preprocesador: {e}")
        return None

if __name__ == "__main__":
    # Ruta al archivo original
    CSV_FILE = "data/database.csv" 
    
    if os.path.exists(CSV_FILE):
        preprocess_seismic_data(CSV_FILE)
    else:
        print(f"⚠️ El archivo {CSV_FILE} no existe. Verifica la ruta.")