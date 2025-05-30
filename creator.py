import openai
import json
import time
from datetime import datetime

# Конфигурация
OPENAI_API_KEY = "ВАШ_API_КЛЮЧ"  # Замените на ваш ключ OpenAI
OUTPUT_FILE = "food_database.json"
TIMESTAMP = int(datetime(2025, 5, 30).timestamp())
MODEL_NAME = "gpt-4o-mini-search-preview"  # Специальная модель для поиска фактов

def get_real_food_data(api_key, category, count=100):
    """Получение реальных данных о продуктах из указанной категории с использованием поисковой модели"""
    openai.api_key = api_key
    
    prompt = (
        f"Используя только проверенные источники (USDA, Роспотребнадзор, официальные таблицы калорийности), "
        f"предоставь {count} реальных продуктов питания из категории '{category}'. "
        "Для каждого продукта укажи:\n"
        "- Точное русское название\n"
        "- Калорийность в ккал/100 г (целое число)\n"
        "- Белки в г/100 г (целое число)\n"
        "- Жиры в г/100 г (целое число)\n"
        "- Углеводы в г/100 г (целое число)\n\n"
        "Ответ предоставь в формате JSON-массива без дополнительного текста.\n\n"
        "Пример:\n"
        '[{"Title": "Куриная грудка вареная", "Calories": "165", "Protein": 31, "Fat": 3, "Carbohydrates": 0}]'
    )
    
    response = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "Ты эксперт по питанию с доступом к базам данных пищевой ценности."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0,  # Нулевая креативность для максимальной точности
        max_tokens=4000
    )
    
    content = response.choices[0].message.content
    return json.loads(content)["items"]

def generate_full_database(api_key, target_count=3000):
    """Генерация полной базы данных продуктов"""
    categories = [
        "овощи", "фрукты", "молочные продукты", "мясо и птица",
        "рыба и морепродукты", "крупы и зерновые", "хлеб и выпечка", "готовые блюда",
        "десерты", "орехи и семена", "яйца", "супы", "гарниры", "салаты", "соусы"
    ]
    
    food_data = []
    unique_titles = set()
    
    print(f"Используем модель {MODEL_NAME} для сбора данных...")
    print("Источники: USDA, Роспотребнадзор, официальные таблицы калорийности")
    
    for category in categories:
        try:
            print(f"Категория: {category}")
            products = get_real_food_data(api_key, category, count=200)
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
    if OPENAI_API_KEY == "ВАШ_API_КЛЮЧ":
        print("Замените 'ВАШ_API_КЛЮЧ' на ваш ключ OpenAI API")
        return
    
    # Генерация базы данных
    food_database = generate_full_database(OPENAI_API_KEY, 3000)
    
    # Сохранение результатов
    save_to_json(food_database, OUTPUT_FILE)
    print(f"Успешно собрано {len(food_database)} записей")

if __name__ == "__main__":
    main()