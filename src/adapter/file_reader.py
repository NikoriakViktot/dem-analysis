from src.adapter.file_resolver import resolve
import geopandas as gpd
import pandas as pd

def read_parquet(path):
    return gpd.read_parquet(resolve(path))

def read_csv(path):
    return pd.read_csv(resolve(path))
