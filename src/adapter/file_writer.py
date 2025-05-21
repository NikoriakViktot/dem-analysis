from src.adapter.file_resolver import resolve
import pandas as pd
import geopandas as gpd
import xarray as xr
from pathlib import Path


class Writer:
    """
    Writer class for saving tabular and geospatial data to resolved paths.
    Supports CSV, Parquet, GeoTIFF, GeoJSON, and GeoPackage.
    """

    def __init__(self, path: str | Path):
        self.full_path = resolve(path)
        self.full_path.parent.mkdir(parents=True, exist_ok=True)

    def write_csv(self, df: pd.DataFrame, index: bool = False):
        df.to_csv(self.full_path, index=index)

    def write_parquet(self, df: pd.DataFrame | gpd.GeoDataFrame):
        df.to_parquet(self.full_path, index=False)

    def write_tiff(self, data: xr.DataArray, dtype="float32"):
        """
        Saves xarray.DataArray as GeoTIFF.
        Assumes .rio metadata exists.
        """
        data.rio.to_raster(self.full_path, dtype=dtype)

    def write_geojson(self, gdf: gpd.GeoDataFrame):
        if not self.full_path.name.endswith(".geojson"):
            raise ValueError("GeoJSON filename must end with .geojson")
        gdf.to_file(self.full_path, driver="GeoJSON")

    def write_gpkg(self, gdf: gpd.GeoDataFrame, layer: str = "layer"):
        if not self.full_path.name.endswith(".gpkg"):
            raise ValueError("GeoPackage filename must end with .gpkg")
        gdf.to_file(self.full_path, driver="GPKG", layer=layer)
