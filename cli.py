import argparse
import json
import sys
from typing import Dict, Any


import os
from datetime import datetime, timedelta


def load_currency_data() -> Dict[str, Any]:
    """
    Загружает данные о валютах из файла currency_rate.json
    Если файл есть и моложе 24 часов — читает из файла, иначе — обновляет.
    """
    file_path = "currency_rate.json"
    
    # Проверяем, существует ли файл и моложе ли он 24 часов
    from storage import is_file_fresh, read_from_file
    if is_file_fresh(file_path):
        # Читаем из файла
        try:
            return read_from_file()
        except json.JSONDecodeError:
            print("Ошибка: файл currency_rate.json содержит некорректные данные.")
            print("Файл будет обновлен.")
        except FileNotFoundError:
            print("Файл currency_rate.json не найден. Обновляем данные...")
    else:
        print("Файл currency_rate.json старше 24 часов. Обновляем данные...")
    
    # Обновляем данные
    try:
        from api_client import update_currency_rates
        update_currency_rates()
        
        # После обновления читаем файл
        return read_from_file()
    except ImportError:
        print("Ошибка: не удалось импортировать функции обновления курсов валют из api_client.py")
        print("Пожалуйста, убедитесь, что все необходимые модули установлены.")
        return {}
    except Exception as e:
        print(f"Ошибка при обновлении данных: {str(e)}")
        print("Пожалуйста, проверьте подключение к интернету и повторите попытку.")
        return {}


def get_currency_info(currency_code: str) -> None:
    """
    Показывает информацию о конкретной валюте
    """
    data = load_currency_data()
    
    # Валидация кода валюты
    all_currencies = set()
    for curr in data.keys():
        all_currencies.add(curr)
        if 'rates' in data[curr]:
            for rate_curr in data[curr]['rates'].keys():
                all_currencies.add(rate_curr)
    
    currency_code_upper = currency_code.upper()
    if currency_code_upper not in all_currencies:
        print(f"Валюта {currency_code} недоступна.")
        print(f"Доступные валюты: {', '.join(sorted(list(all_currencies)))}")
        return
    
    # Проверяем, есть ли валюта в основных или в доступных
    found = False
    currency_data = None
    is_main_currency = False
    
    # Сначала проверяем основные валюты
    if currency_code_upper in data:
        currency_data = data[currency_code_upper]
        is_main_currency = True
        found = True
    else:
        # Ищем валюту среди всех доступных валют
        for main_curr in data:
            if 'rates' in data[main_curr] and currency_code_upper in data[main_curr]['rates']:
                # Создаем "виртуальную" информацию о валюте
                # Для этого находим основную валюту, в которой представлена целевая валюта
                currency_data = data[main_curr]
                is_main_currency = False
                found = True
                break
    
    if not found:
        print(f"Валюта {currency_code} недоступна.")
        print(f"Доступные валюты: {', '.join(sorted(list(all_currencies)))}")
        return
    
    print(f"Информация о валюте {currency_code_upper}:")
    print("-" * 50)
    
    if is_main_currency:
        print(f"Код: {currency_code_upper}")
        print(f"Базовая валюта: {currency_data['base_code']}")
        print(f"Провайдер: {currency_data['provider']}")
        print(f"Последнее обновление: {currency_data['time_last_update_utc']}")
        print(f"Следующее обновление: {currency_data['time_next_update_utc']}")
        
        # Показываем курсы базовых валют к выбранной валюте
        rates = currency_data['rates']
        print("\nКотировки базовых валют к выбранной валюте:")
        
        # Базовые валюты, которые мы хотим отобразить
        base_currencies = ["USD", "EUR", "GBP", "RUB"]
        
        for base_curr in base_currencies:
            if base_curr in rates:
                rate = rates[base_curr]
                print(f" 1 {base_curr} = {rate} {currency_code_upper}")
            else:
                # Если напрямую нет курса, вычисляем через базовую валюту
                base_code = currency_data['base_code']
                if base_code in rates and base_curr in data:
                    # Получаем курс базовой валюты к целевой валюте
                    base_to_target = rates[base_code]
                    # Получаем курс базовой валюты к базе базовой валюты
                    base_curr_rates = data[base_curr]['rates']
                    base_curr_to_base = base_curr_rates[base_code]
                    
                    # Рассчитываем курс: base_curr к target
                    rate = base_to_target / base_curr_to_base
                    print(f"  1 {base_curr} = {rate} {currency_code_upper}")
    else:
        print(f"Код: {currency_code_upper}")
        print("Информация о валюте доступна в качестве целевой валюты")
        print(f"Базовая валюта: {currency_data['base_code']}")
        print(f"Провайдер: {currency_data['provider']}")
        print(f"Последнее обновление: {currency_data['time_last_update_utc']}")
        print(f"Следующее обновление: {currency_data['time_next_update_utc']}")
        
        # Показываем курсы базовых валют к выбранной валюте
        rates = currency_data['rates']
        print(f"\nКотировки базовых валют к {currency_code_upper}:")
        
        # Базовые валюты, которые мы хотим отобразить
        base_currencies = ["USD", "EUR", "GBP", "RUB"]
        
        for base_curr in base_currencies:
            if currency_code_upper in rates and base_curr in rates:
                # Прямой курс базовой валюты к целевой
                base_to_target_rate = rates[currency_code_upper]
                base_to_base_curr_rate = rates[base_curr]
                # Рассчитываем курс: 1 base_curr = X currency_code_upper
                rate = base_to_base_curr_rate / base_to_target_rate
                print(f"  1 {base_curr} = {rate} {currency_code_upper}")
            elif base_curr == currency_code_upper:
                print(f"  1 {base_curr} = 1.0 {currency_code_upper}")
            else:
                # Пытаемся вычислить через базовую валюту
                base_code = currency_data['base_code']
                if base_curr in data and currency_code_upper in data and currency_code_upper in data[base_code]['rates']:
                    # Получаем курс базовой валюты к целевой валюте
                    base_to_target = 1 / data[base_code]['rates'][currency_code_upper]
                    # Получаем курс базовой валюты к базе базовой валюты
                    if base_curr in data and base_code in data[base_curr]['rates']:
                        base_curr_to_base = data[base_curr]['rates'][base_code]
                        # Рассчитываем курс: base_curr к target
                        rate = base_curr_to_base * base_to_target
                        print(f"  1 {base_curr} = {rate} {currency_code_upper}")
                    elif base_curr == base_code:
                        print(f"  1 {base_curr} = {base_to_target} {currency_code_upper}")
                elif currency_code_upper in data and base_curr in data[base_code]['rates'] and currency_code_upper in data[base_curr]['rates']:
                    # Пытаемся использовать обе валюты через их отношения к базовой валюте
                    base_to_base_curr_rate = data[base_code]['rates'][base_curr]
                    base_to_target_rate = data[base_code]['rates'][currency_code_upper]
                    rate = base_to_base_curr_rate / base_to_target_rate
                    print(f"  1 {base_curr} = {rate} {currency_code_upper}")


def list_currencies() -> None:
    """
    Показывает список доступных валют
    """
    data = load_currency_data()
    
    # Собираем все уникальные валюты из всех источников
    all_currencies = set()
    
    # Добавляем основные валюты (ключи словаря)
    for currency in data.keys():
        all_currencies.add(currency)
        
        # Добавляем все валюты из rates
        currency_data = data[currency]
        if 'rates' in currency_data:
            for rate_currency in currency_data['rates'].keys():
                all_currencies.add(rate_currency)
    
    print("Доступные валюты:")
    print("-" * 50)
    sorted_currencies = sorted(list(all_currencies))
    for currency in sorted_currencies:
        print(f"{currency}")
    
    print(f"\nВсего валют: {len(sorted_currencies)}")


def convert_currency(from_currency: str, to_currency: str, amount: float) -> None:
    """
    Конвертирует сумму из одной валюты в другую
    """
    data = load_currency_data()
    
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # Валидация кодов валют
    all_currencies = set()
    for curr in data.keys():
        all_currencies.add(curr)
        if 'rates' in data[curr]:
            for rate_curr in data[curr]['rates'].keys():
                all_currencies.add(rate_curr)
    
    if from_currency not in all_currencies:
        print(f"Валюта {from_currency} недоступна.")
        print(f"Доступные валюты: {', '.join(sorted(list(all_currencies)))}")
        return
    
    if to_currency not in all_currencies:
        print(f"Валюта {to_currency} недоступна.")
        print(f"Доступные валюты: {', '.join(sorted(list(all_currencies)))}")
        return
    
    if from_currency == to_currency:
        print(f"{amount} {from_currency} = {amount:.4f} {to_currency}")
        return
    
    # Проверяем, является ли from_currency основной валютой
    if from_currency in data:
        rates_data_from = data[from_currency]
        base_code_from = rates_data_from['base_code']
        from_rates = rates_data_from['rates']
        
        # Проверяем, является ли to_currency основной валютой
        if to_currency in data:
            rates_data_to = data[to_currency]
            base_code_to = rates_data_to['base_code']
            to_rates = rates_data_to['rates']
            
            # Если прямой курс доступен
            if to_currency in from_rates:
                rate = from_rates[to_currency]
                result = amount * rate
                print(f"{amount} {from_currency} = {result:.4f} {to_currency}")
                return
            
            # Проверяем, можно ли получить курс через базовую валюту
            # Если обе валюты имеют общий базовый код
            if base_code_from == base_code_to:
                # Конвертируем через общую базовую валюту
                # 1. Сначала конвертируем from_currency в базовую валюту
                if from_currency == base_code_from:
                    base_amount = amount
                else:
                    # from_currency к базовой валюте
                    base_amount = amount / from_rates[from_currency]
                
                # 2. Затем конвертируем базовую валюту в to_currency
                if to_currency == base_code_to:
                    result = base_amount
                else:
                    # базовая валюта к to_currency
                    result = base_amount * to_rates[to_currency]
                    
                print(f"{amount} {from_currency} = {result:.4f} {to_currency}")
                return
            
            # Если базовые валюты разные, нужно использовать обе для пересчета
            # 1. Конвертируем from_currency в его базовую валюту
            if from_currency == base_code_from:
                base_amount = amount
            else:
                base_amount = amount / from_rates[from_currency]
            
            # 2. Конвертируем базовую валюту from в базовую валюту to
            # Для этого нужно знать курс base_code_from к base_code_to
            if base_code_from == rates_data_to['base_code']:
                # base_code_from к base_code_to уже есть
                intermediate_amount = base_amount * to_rates[base_code_from]
            elif base_code_to == rates_data_from['base_code']:
                # base_code_to к base_code_from уже есть, обращаем курс
                intermediate_amount = base_amount / from_rates[base_code_to]
            else:
                # Обе базовые валюты разные, используем третью валюту как промежуточную
                # Используем USD как промежуточную валюту, если она есть
                if 'USD' in from_rates and 'USD' in to_rates:
                    usd_amount = base_amount * from_rates['USD']
                    result = usd_amount / to_rates['USD']
                    print(f"{amount} {from_currency} = {result:.4f} {to_currency}")
                    return
                else:
                    # Используем другую промежуточную валюту, доступную в обеих таблицах
                    common_currencies = set(from_rates.keys()) & set(to_rates.keys())
                    if common_currencies:
                        intermediate_curr = list(common_currencies)[0]
                        intermediate_amount = base_amount * from_rates[intermediate_curr]
                        result = intermediate_amount / to_rates[intermediate_curr]
                        print(f"{amount} {from_currency} = {result:.4f} {to_currency}")
                        return
                    else:
                        print(f"Не удалось найти путь для конвертации {from_currency} в {to_currency}")
                        return
            
            # 3. Конвертируем базовую валюту to в целевую валюту
            if to_currency == base_code_to:
                final_result = intermediate_amount
            else:
                final_result = intermediate_amount * to_rates[to_currency]
            
            print(f"{amount} {from_currency} = {final_result:.4f} {to_currency}")
            return
        else:
            # to_currency не является основной валютой, но доступна в rates
            # Ищем основную валюту, в которой представлена to_currency
            base_curr_data = None
            for main_curr in data:
                if 'rates' in data[main_curr] and to_currency in data[main_curr]['rates']:
                    base_curr_data = data[main_curr]
                    break
            
            if base_curr_data is None:
                print(f"Не удалось найти путь для конвертации {from_currency} в {to_currency}")
                return
            
            # Сначала конвертируем from_currency в базовую валюту base_curr_data
            if from_currency == base_curr_data['base_code']:
                base_amount = amount
            elif from_currency in from_rates:
                base_amount = amount / from_rates[from_currency]
            else:
                print(f"Не удалось найти путь для конвертации {from_currency} в {to_currency}")
                return
            
            # Затем конвертируем из базовой валюты в to_currency
            if to_currency in base_curr_data['rates']:
                result = base_amount * base_curr_data['rates'][to_currency]
                print(f"{amount} {from_currency} = {result:.4f} {to_currency}")
                return
            else:
                print(f"Не удалось найти путь для конвертации {from_currency} в {to_currency}")
                return
    else:
        # from_currency не является основной валютой, но доступна в rates
        # Ищем основную валюту, в которой представлена from_currency
        base_curr_data_from = None
        for main_curr in data:
            if 'rates' in data[main_curr] and from_currency in data[main_curr]['rates']:
                base_curr_data_from = data[main_curr]
                break
        
        if base_curr_data_from is None:
            print(f"Не удалось найти путь для конвертации {from_currency} в {to_currency}")
            return
        
        # Конвертируем from_currency в базовую валюту
        base_rate_from = base_curr_data_from['rates'][from_currency]
        base_amount = amount / base_rate_from
        
        # Теперь конвертируем базовую валюту в to_currency
        if to_currency in data:
            # to_currency - основная валюта
            to_rates = data[to_currency]['rates']
            if base_curr_data_from['base_code'] in to_rates:
                result = base_amount * to_rates[base_curr_data_from['base_code']]
                print(f"{amount} {from_currency} = {result:.4f} {to_currency}")
                return
            else:
                print(f"Не удалось найти путь для конвертации {from_currency} в {to_currency}")
                return
        else:
            # to_currency тоже не основная валюта
            base_curr_data_to = None
            for main_curr in data:
                if 'rates' in data[main_curr] and to_currency in data[main_curr]['rates']:
                    base_curr_data_to = data[main_curr]
                    break
            
            if base_curr_data_to is None:
                print(f"Не удалось найти путь для конвертации {from_currency} в {to_currency}")
                return
            
            # Конвертируем базовую валюту из from в базовую валюту to
            if base_curr_data_from['base_code'] == base_curr_data_to['base_code']:
                # Та же базовая валюта
                if to_currency in base_curr_data_to['rates']:
                    result = base_amount * base_curr_data_to['rates'][to_currency]
                    print(f"{amount} {from_currency} = {result:.4f} {to_currency}")
                    return
            else:
                # Разные базовые валюты, используем промежуточную валюту
                if base_curr_data_to['base_code'] in base_curr_data_from['rates']:
                    intermediate_amount = base_amount * base_curr_data_from['rates'][base_curr_data_to['base_code']]
                    if to_currency in base_curr_data_to['rates']:
                        result = intermediate_amount * base_curr_data_to['rates'][to_currency]
                        print(f"{amount} {from_currency} = {result:.4f} {to_currency}")
                        return
                else:
                    print(f"Не удалось найти путь для конвертации {from_currency} в {to_currency}")
                    return


def update_currency_rates():
    """
    Обновляет курсы валют, вызывая функцию из api_client.py
    """
    try:
        # Импортируем функцию обновления курсов валют
        from api_client import update_currency_rates
        print("Обновление курсов валют...")
        update_currency_rates()
        print("Курсы валют успешно обновлены!")
    except ImportError:
        print("Ошибка: не удалось импортировать функцию обновления курсов валют из api_client.py")
        print("Пожалуйста, убедитесь, что все необходимые модули установлены.")
    except Exception as e:
        print(f"Ошибка при обновлении курсов валют: {str(e)}")
        print("Пожалуйста, проверьте подключение к интернету и повторите попытку.")


def interactive_menu():
    """
    Интерактивное меню для работы с валютами
    """
    while True:
        print("\n" + "="*60)
        print("ИНТЕРФЕЙС ДЛЯ РАБОТЫ С ВАЛЮТАМИ")
        print("="*60)
        print("1 - Информация о конкретной валюте")
        print("2 - Список всех валют")
        print("3 - Конвертация валют")
        print("4 - Обновить курсы валют")
        print("0 - Выход")
        print("-"*60)
        
        choice = input("Выберите действие (0-4): ").strip()
        
        if choice == "0":
            print("Выход из программы.")
            break
        elif choice == "1":
            currency = input("Введите код валюты (например, USD): ").strip()
            if currency:
                # Валидация кода валюты
                data = load_currency_data()
                all_currencies = set()
                for curr in data.keys():
                    all_currencies.add(curr)
                    if 'rates' in data[curr]:
                        for rate_curr in data[curr]['rates'].keys():
                            all_currencies.add(rate_curr)
                
                currency_upper = currency.upper()
                if currency_upper not in all_currencies:
                    print(f"Валюта {currency} недоступна.")
                    print(f"Доступные валюты: {', '.join(sorted(list(all_currencies)))}")
                else:
                    get_currency_info(currency)
            else:
                print("Код валюты не может быть пустым!")
        elif choice == "2":
            list_currencies()
        elif choice == "3":
            from_curr = input("Введите код валюты из которой конвертировать (например, USD): ").strip()
            to_curr = input("Введите код валюты в которую конвертировать (например, EUR): ").strip()
            amount_str = input("Введите сумму для конвертации: ").strip()
            
            if from_curr and to_curr and amount_str:
                try:
                    amount = float(amount_str)
                    # Валидация кодов валют
                    data = load_currency_data()
                    all_currencies = set()
                    for curr in data.keys():
                        all_currencies.add(curr)
                        if 'rates' in data[curr]:
                            for rate_curr in data[curr]['rates'].keys():
                                all_currencies.add(rate_curr)
                    
                    from_curr_upper = from_curr.upper()
                    to_curr_upper = to_curr.upper()
                    
                    if from_curr_upper not in all_currencies:
                        print(f"Валюта {from_curr} недоступна.")
                        print(f"Доступные валюты: {', '.join(sorted(list(all_currencies)))}")
                    elif to_curr_upper not in all_currencies:
                        print(f"Валюта {to_curr} недоступна.")
                        print(f"Доступные валюты: {', '.join(sorted(list(all_currencies)))}")
                    else:
                        convert_currency(from_curr, to_curr, amount)
                except ValueError:
                    print(f"Ошибка: '{amount_str}' не является допустимым числом.")
            else:
                print("Все поля должны быть заполнены!")
        elif choice == "4":
            update_currency_rates()
        else:
            print("Неверный выбор! Пожалуйста, введите число от 0 до 4.")


def main():
    # Запускаем интерактивное меню
    interactive_menu()


if __name__ == "__main__":
    main()