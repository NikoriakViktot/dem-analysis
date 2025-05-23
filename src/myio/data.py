from ..adapter.file_reader import Reader
from ..adapter.file_writer import Writer

def read_csv(path): return Reader(path).read_csv()
def read_parquet(path): return Reader(path).read_parquet()
def read_gpkg(path): return Reader(path).read_gpkg()

def write_csv(df, path): return Writer(path).write_csv(df)
def write_parquet(df, path): return Writer(path).write_parquet(df)
