import pandas as pd
import os

DATA_PATH = "data/sismos_optimizado.parquet"

def get_data():
    if os.path.exists(DATA_PATH):
        return pd.read_parquet(DATA_PATH)
    return None