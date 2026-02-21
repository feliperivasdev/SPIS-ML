import pandas as pd
import os
import numpy as np

def preprocess_seismic_data(input_path, output_name="sismos_optimizado.parquet"):
    """
    Optimiza un CSV pesado convirtiéndolo a Parquet con tipos de datos eficientes.
    Soluciona el error de Mixed Timezones y detección de columnas.
    """
    print(f"🚀 Iniciando preprocesamiento de: {input_path}")
    output_path = os.path.join(os.path.dirname(input_path), output_name)

    # Columnas que necesitamos (Asegúrate de que 'magnitude' esté aquí)
    target_cols = ['time', 'date', 'latitude', 'longitude', 'depth', 'magnitude', 'place']
    
    try:
        header = pd.read_csv(input_path, nrows=0)
        # Identificar columnas ignorando mayúsculas/minúsculas
        cols_to_load = [c for c in header.columns if c.lower() in target_cols]
        print(f"📊 Columnas detectadas para carga: {cols_to_load}")

        df = pd.read_csv(input_path, usecols=cols_to_load)
        df.columns = [c.lower() for c in df.columns]

        # --- SOLUCIÓN AL ERROR DE TIMEZONE ---
        # 1. Si tienes 'date' y 'time' por separado, intentamos combinarlas
        # 2. Usamos utc=True para normalizar todas las zonas horarias a una sola
        if 'date' in df.columns and 'time' in df.columns:
            df['time'] = pd.to_datetime(df['date'] + ' ' + df['time'], utc=True, errors='coerce')
            df = df.drop(columns=['date'])
        else:
            df['time'] = pd.to_datetime(df['time'], utc=True, errors='coerce')

        # Renombrar 'magnitude' a 'mag' para que coincida con tus otros módulos
        if 'magnitude' in df.columns:
            df = df.rename(columns={'magnitude': 'mag'})

        # Limpieza de nulos críticos
        df = df.dropna(subset=['mag', 'time'])

        # --- DOWNCASTING (Optimización RAM) ---
        # Convertimos a float32 para ahorrar el 50% de memoria
        for col in ['latitude', 'longitude', 'depth', 'mag']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype(np.float32)

        # Guardar en Parquet
        df.to_parquet(output_path, compression='snappy', index=False)
        
        print("-" * 30)
        print(f"✅ ¡Preprocesamiento completado!")
        print(f"📂 Archivo generado: {output_path}")
        print(f"🚀 Tamaño optimizado: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
        print("-" * 30)
        
        return output_path

    except Exception as e:
        print(f"❌ Error crítico en el preprocesador: {e}")
        return None

if __name__ == "__main__":
    CSV_FILE = "data/database.csv" 
    if os.path.exists(CSV_FILE):
        preprocess_seismic_data(CSV_FILE)
    else:
        print(f"⚠️ El archivo {CSV_FILE} no existe.")