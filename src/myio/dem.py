from ..adapter.file_reader import Reader
from ..adapter.file_writer import Writer

def read_dem(path, mode="array"): return Reader(path).read_dem(mode)
def write_dem(data, path, dtype="float32"): return Writer(path).write_tiff(data, dtype)
