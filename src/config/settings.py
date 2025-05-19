from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    def __init__(self):
        path = os.getenv("DATA_PATH")
        if not path:
            raise ValueError("DATA_PATH is not set in .env")
        self.DATA_PATH = Path(path)
        if not self.DATA_PATH.exists():
            raise FileNotFoundError(f"DATA_PATH does not exist: {self.DATA_PATH}")

settings = Settings()
