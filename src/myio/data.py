from ..adapter.file_reader import Reader
from ..adapter.file_writer import Writer

def reader(path): return Reader(path)

def read_csv(path): return Reader(path).read_csv()

def read_parquet(bbox=None, **kwargs):
    if bbox is not None and hasattr(bbox, "bounds"):
        bbox = bbox.bounds
    return Reader().read_parquet(bbox=bbox, **kwargs)

def read_gpkg( **kwargs): return Reader().read_gpkg(**kwargs)


def writer(path): return Writer(path)

def write_csv(df, path): return Writer(path).write_csv(df)
def write_parquet(df, path): return Writer(path).write_parquet(df)
