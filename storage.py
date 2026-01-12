import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any


def save_to_file(data: Dict[str, Any], file_path: str = "currency_rate.json") -> bool:
    """
    Сохраняет данные в файл
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(f"Данные сохранены в {file_path}")
        return True
    except IOError as e:
        print(f"Ошибка при сохранении файла: {e}")
        return False


def read_from_file(file_path: str = "currency_rate.json") -> Dict[str, Any]:
    """
    Читает данные из файла
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {file_path} не найден")
    except json.JSONDecodeError:
        raise json.JSONDecodeError(f"Файл {file_path} содержит некорректные данные", "", 0)


def is_file_fresh(file_path: str = "currency_rate.json", hours: int = 24) -> bool:
    """
    Проверяет, является ли файл свежим (не старше указанного количества часов)
    """
    if not os.path.exists(file_path):
        return False
    
    mod_time = os.path.getmtime(file_path)
    mod_datetime = datetime.fromtimestamp(mod_time)
    current_time = datetime.now()
    
    return current_time - mod_datetime < timedelta(hours=hours)


def get_modification_time(file_path: str = "currency_rate.json") -> str:
    """
    Возвращает время последнего изменения файла
    """
    if os.path.exists(file_path):
        mod_time = os.path.getmtime(file_path)
        mod_datetime = datetime.fromtimestamp(mod_time)
        return mod_datetime.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return "Файл не найден"