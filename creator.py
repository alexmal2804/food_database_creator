import openai
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Загрузка переменных окружения из .env файла
load_dotenv()

# Конфигурация
OPENAI_API_KEY = os.getenv('REACT_APP_OPENAI_API_KEY')  # Загружаем ключ из переменных окружения
OUTPUT_FILE = "food_database.json"
TIMESTAMP = int(datetime(2025, 5, 30).timestamp())
MODEL_NAME = "gpt-4o-mini-search-preview"  # Специальная модель для поиска фактов

def get_real_food_data(api_key, category, count=100):
    """Получение реальных данных о продуктах из указанной категории с использованием поисковой модели"""
    try:
        print(f"Используемый API ключ: {api_key[:5]}...{api_key[-5:] if api_key else ''}")
        print(f"Используемая модель: {MODEL_NAME}")
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.aitunnel.ru/v1"  # Убрали слеш в конце
        )
        
        # Уменьшаем количество запрашиваемых продуктов для тестирования
        count = min(count, 3)  # Еще уменьшаем для теста
        
        # Более простой промпт
        prompt = (
            f"Приведи {count} примеров продуктов/блюд из категории '{category}'. "
            f"Для каждого укажи точные данные о пищевой ценности на 100 грамм.\n"
            "Формат ответа: JSON-массив объектов с полями:\n"
            "- Title: название на русском языке\n"
            "- Calories: калорийность (ккал, число)\n"
            "- Protein: белки (г, число с одной цифрой после запятой)\n"
            "- Fat: жиры (г, число с одной цифрой после запятой)\n"
            "- Carbohydrates: углеводы (г, число с одной цифрой после запятой)\n\n"
            "Важно: \n"
            "1. Указывай только реально существующие блюда и продукты\n"
            "2. Для готовых блюд укажи полное название (например, 'Салат Цезарь с курицей')\n"
            "3. Значения должны быть реалистичными и соответствовать официальным источникам\n"
            "4. Не добавляй никаких комментариев вне JSON"
        )
        
        print(f"Отправка запроса для категории: {category}")
        print(f"Промпт: {prompt[:100]}...")  # Выводим начало промпта для отладки
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Ты помощник, который отвечает только в формате JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Немного увеличиваем температуру
                max_tokens=1000
            )
        except Exception as api_error:
            print(f"Ошибка API: {str(api_error)}")
            print(f"Тип ошибки: {type(api_error).__name__}")
            if hasattr(api_error, 'response'):
                print(f"Ответ сервера: {api_error.response}")
            raise
        
        print("Получен ответ от API")
        content = response.choices[0].message.content
        print(f"Сырой ответ: {content[:200]}...")  # Выводим начало ответа для отладки
        
        # Используем регулярное выражение для извлечения JSON из текста
        import re
        
        # Пытаемся найти JSON в тексте (внутри ```json ... ``` или ``` ... ```)
        json_match = re.search(r'```(?:json\n)?([\s\S]*?)```', content)
        if json_match:
            json_str = json_match.group(1).strip()
            print(f"Извлечен JSON из блока кода")
        else:
            # Если не нашли блок кода, пробуем обработать как есть
            print("Блок кода не найден, обрабатываем как есть")
            json_str = content
        
        print(f"Очищенный ответ: {json_str[:200]}...")
        
        # Пытаемся распарсить JSON
        try:
            data = json.loads(json_str)
            
            # Обрабатываем разные форматы ответа
            if isinstance(data, dict):
                if "items" in data:
                    items = data["items"]
                else:
                    # Если в ответе нет ключа 'items', но есть другие ключи, используем весь словарь
                    items = [data]
            elif isinstance(data, list):
                items = data
            else:
                print(f"Неожиданный формат ответа: {type(data)}")
                items = []
                
            print(f"Успешно распаршено {len(items)} элементов")
            return items
            
        except json.JSONDecodeError as je:
            print(f"Ошибка парсинга JSON: {je}")
            print(f"Строка с ошибкой: {json_str}")
            return []
        
    except Exception as e:
        print(f"Ошибка при обработке категории {category}: {str(e)}")
        raise  # Пробрасываем исключение для обработки в вызывающем коде

def generate_full_database(api_key, target_count=1500):
    """Генерация полной базы данных продуктов"""
    categories = [
        # Основные категории продуктов
        "овощи", "фрукты", "ягоды", "зелень", "грибы",
        "мясо и птица", "рыба и морепродукты", "яйца",
        "молочные продукты", "сыры", "творог и творожные продукты",
        "крупы и злаки", "макаронные изделия", "хлеб и выпечка",
        "орехи и семена", "бобовые",
        
        # Напитки
        "свежевыжатые соки", "морсы и компоты", "минеральная вода и лимонады",
        "чай и травяные настои", "кофе и какао напитки",
        
        # Русская кухня
        "первые блюда русской кухни", "вторые блюда русской кухни", "салаты русской кухни",
        "выпечка русской кухни", "десерты русской кухни",
        
        # Кавказская кухня
        "первые блюда кавказской кухни", "вторые блюда кавказской кухни", "салаты кавказской кухни",
        "выпечка кавказской кухни", "соусы кавказской кухни",
        
        # Европейская кухня
        "первые блюда европейской кухни", "вторые блюда европейской кухни", "салаты европейской кухни",
        "десерты европейской кухни", "соусы европейской кухни",
        
        # Азиатская кухня
        "первые блюда азиатской кухни", "вторые блюда азиатской кухни", "салаты азиатской кухни",
        "десерты азиатской кухни", "соусы азиатской кухни",
        
        # Итальянская кухня
        "паста и ризотто итальянской кухни", "пицца и фокачча итальянской кухни",
        "салаты и закуски итальянской кухни", "десерты итальянской кухни",
        "соусы и заправки итальянской кухни",
        
        # Среднеазиатская кухня
        "первые блюда среднеазиатской кухни", "вторые блюда среднеазиатской кухни",
        "салаты и закуски среднеазиатской кухни", "выпечка среднеазиатской кухни",
        "соусы и приправы среднеазиатской кухни",
        
        # Турецкая кухня
        "первые блюда турецкой кухни", "вторые блюда турецкой кухни",
        "салаты и мезе турецкой кухни", "выпечка турецкой кухни",
        "десерты турецкой кухни", "напитки турецкой кухни",
        
        # Низкокалорийные варианты
        "низкокалорийные завтраки", "низкокалорийные обеды", "низкокалорийные ужины",
        "низкокалорийные десерты", "низкокалорийные перекусы",
        
        # Вегетарианские и веганские блюда
        "вегетарианские первые блюда", "вегетарианские вторые блюда", "вегетарианские салаты",
        "веганские блюда", "безглютеновые блюда"
    ]
    
    food_data = []
    unique_titles = set()
    
    print(f"Используем модель {MODEL_NAME} для сбора данных...")
    print("Источники: USDA, Роспотребнадзор, официальные таблицы калорийности")
    print(f"Всего категорий для обработки: {len(categories)}")
    print(f"Целевое количество записей: {target_count}")
    
    for category in categories:
        try:
            print(f"\n{'='*50}\nОбработка категории: {category}")
            # Запрашиваем по 12 примеров для каждой категории
            products = get_real_food_data(api_key, category, count=12)
            new_count = 0
            
            for product in products:
                title = product["Title"]
                
                # Проверка уникальности и валидности данных
                if title in unique_titles:
                    continue
                if not all(key in product for key in ["Calories", "Protein", "Fat", "Carbohydrates"]):
                    continue
                    
                unique_titles.add(title)
                
                # Добавление служебных полей
                product["dateload"] = TIMESTAMP
                product["shared"] = False
                
                # Преобразование типов
                product["Protein"] = int(product["Protein"])
                product["Fat"] = int(product["Fat"])
                product["Carbohydrates"] = int(product["Carbohydrates"])
                product["Calories"] = str(product["Calories"])
                
                food_data.append(product)
                new_count += 1
                
                if len(food_data) >= target_count:
                    break
            
            print(f"Добавлено: {new_count} | Всего: {len(food_data)}/{target_count}")
            
            if len(food_data) >= target_count:
                break
                
            time.sleep(3)  # Соблюдение лимитов API
            
        except Exception as e:
            print(f"Ошибка: {str(e)}. Повтор через 5 сек...")
            time.sleep(5)
    
    return food_data[:target_count]

def save_to_json(data, filename):
    """Сохранение данных в JSON-файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nФайл сохранен: {filename}")

def main():
    if not OPENAI_API_KEY or OPENAI_API_KEY == "ВАШ_API_КЛЮЧ":
        print("Ошибка: Необходимо установить корректный API ключ OpenAI")
        print("Пожалуйста, создайте файл .env с переменной REACT_APP_OPENAI_API_KEY=ваш_ключ")
        return
    
    # Генерация базы данных
    food_database = generate_full_database(OPENAI_API_KEY, 3000)
    
    # Сохранение результатов
    save_to_json(food_database, OUTPUT_FILE)
    print(f"Успешно собрано {len(food_database)} записей")

if __name__ == "__main__":
    main()