from pathlib import Path
from src.config.settings import settings

def resolve(path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return settings.DATA_PATH / path
