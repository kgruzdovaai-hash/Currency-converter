import requests
from typing import Dict, Any, Optional
from storage import save_to_file, read_from_file, is_file_fresh


FAVORITE_CURRENCIES = ["USD", "EUR", "GBP", "RUB"]


def get_currency_rate(currency_code: str) -> Optional[Dict[str, Any]]:
    """
    Получает курсы валют для указанной валюты через API
    """
    URL = f"https://open.er-api.com/v6/latest/{currency_code}"

    try:
        response = requests.get(URL)
        if response.status_code != 200:
            print(f"Ошибка при запросе к API: {response.status_code}")
            return None
        
        data = response.json()
        return data
    except requests.exceptions.ConnectionError:
        print("Ошибка сети: не удается подключиться к API. Пожалуйста, проверьте подключение к интернету.")
        return None
    except requests.exceptions.Timeout:
        print("Ошибка сети: превышено время ожидания запроса. Пожалуйста, проверьте подключение к интернету.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети при запросе курсов валют: {e}")
        return None
    except ValueError:  # json.JSONDecodeError is subclass of ValueError
        print("Ошибка при декодировании JSON ответа от API")
        return None


def update_currency_rates(file_path: str = "currency_rate.json") -> None:
    """
    Обновляет курсы валют, делая запросы к API для избранных валют
    """
    all_data = {}
    for currency in FAVORITE_CURRENCIES:
        rate = get_currency_rate(currency)
        if rate is not None:
            all_data[currency] = rate
        else:
            print(f"Не удалось получить данные для валюты {currency}")
    
    if all_data:
        save_to_file(all_data, file_path)
        print(f"Данные обновлены в {file_path}")
    else:
        print("Не удалось обновить данные для каких-либо валют")