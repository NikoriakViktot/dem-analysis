from src.adapter.file_resolver import resolve
import geopandas as gpd
import pandas as pd
import rioxarray as rxr
import xdem
import rasterio
from pathlib import Path


class Reader:
    """
    Reader class for loading geospatial and tabular data using unified paths.
    Supports .parquet, .csv, and raster formats (.tif) with flexible output.
    """

    def __init__(self, path: str | Path):
        self.full_path = resolve(path)



    def read_csv(self) -> pd.DataFrame:
        """Read a CSV file and return DataFrame."""
        return pd.read_csv(self.full_path)

    def read_gpkg(self) -> gpd.GeoDataFrame:
        """Read a GeoParquet file and return GeoDataFrame."""
        return gpd.read_file(self.full_path)


    def read_parquet(self) -> gpd.GeoDataFrame:
        """Read a GeoParquet file and return GeoDataFrame."""
        return gpd.read_parquet(self.full_path)



    def read_dem(self, mode: str = "array"):
        """
        Read a DEM from a GeoTIFF file with specified mode.

        Parameters:
            path (str or Path): Relative or absolute path to the DEM file.
            mode (str): One of 'array', 'xdem', or 'rasterio'.

        Returns:
            DEM object depending on the mode:
                - 'array': xarray.DataArray
                - 'xdem': xdem.DEM
                - 'rasterio': rasterio.io.DatasetReader
        """
        if mode == "array":
            return rxr.open_rasterio(self.full_path, masked=True).squeeze()
        elif mode == "xdem":
            return xdem.DEM(self.full_path)
        elif mode == "rasterio":
            return rasterio.open(self.full_path)
        else:
            raise ValueError("Invalid mode. Choose 'array', 'xdem', or 'rasterio'.")