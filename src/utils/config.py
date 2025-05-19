from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def get_data_path() -> Path:
    """
    Визначає абсолютний шлях до директорії з даними.
    1. З .env → DATA_PATH
    2. З системної змінної середовища
    3. За замовчуванням: в кореневій директорії проєкту — ./data
    """
    path_from_env = os.getenv("DATA_PATH")
    if path_from_env:
        path = Path(path_from_env)
        if path.exists():
            return path
        else:
            raise FileNotFoundError(f"❌ DATA_PATH із .env або env не існує: {path}")

    default_path = Path(__file__).resolve().parents[2] / "data"
    if default_path.exists():
        return default_path

    raise FileNotFoundError("❌ Не вказано DATA_PATH і не знайдено ./data. Створи .env або передай через змінну середовища.")
