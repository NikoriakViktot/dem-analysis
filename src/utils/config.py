# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # шукає .env у корені проєкту

# Повертає шлях до даних
def get_data_path():
    return os.getenv("DATA_PATH")

# Приклад використання
if __name__ == "__main__":
    print("Дані зберігаються у:", get_data_path())
