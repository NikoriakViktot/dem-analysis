from ..adapter.file_writer import Writer
from ..adapter.file_reader import Reader

def write_geojson(gdf, path): return Writer(path).write_geojson(gdf)
def write_gpkg(gdf, path, layer="layer"): return Writer(path).write_gpkg(gdf, layer)

def read_parquet(path): return Reader(path).read_parquet()  # або .read_file() якщо окремо
def read_geojson(path): return Reader(path).read_parquet()
def read_gpkg(path): return Reader(path).read_gpkg()  # або .read_file() якщо окремо

