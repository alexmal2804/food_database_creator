import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('firebase_loader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FirebaseLoader')

def load_environment():
    """Загрузка переменных окружения"""
    try:
        load_dotenv()
        logger.info("Переменные окружения успешно загружены")
        return True
    except Exception as e:
        logger.error(f"Ошибка загрузки переменных окружения: {e}")
        return False

def initialize_firebase():
    """Инициализация Firebase с использованием сервисного аккаунта из .env файла"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        import json
        
        # Путь к файлу .env
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        
        # Создаем словарь с учетными данными напрямую
        service_account = {
        #/////
        }
        
        logger.info("Учетные данные Firebase успешно загружены")
        
        # Инициализируем Firebase с учетными данными
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred, {
                'projectId': service_account.get('project_id')
            })
        
        logger.info("Firebase успешно инициализирован с использованием сервисного аккаунта")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка инициализации Firebase: {e}", exc_info=True)
        return False
        
        # Инициализируем Firebase с учетными данными
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred, {
                'projectId': service_account.get('project_id')
            })
        
        logger.info("Firebase успешно инициализирован с использованием сервисного аккаунта")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка инициализации Firebase: {e}", exc_info=True)
        return False

def load_food_data(file_path):
    """Загрузка данных из JSON-файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Успешно загружено {len(data)} записей из файла")
        return data
    except Exception as e:
        logger.error(f"Ошибка загрузки данных из файла {file_path}: {e}")
        return None

def upload_to_firestore(collection_name, data):
    """Загрузка данных в Firestore с пакетной обработкой"""
    try:
        from firebase_admin import firestore
        import time
        
        db = firestore.client()
        collection_ref = db.collection(collection_name)
        
        total = len(data)
        success = 0
        batch_size = 100  # Уменьшаем размер пакета для надежности
        
        for i in range(0, total, batch_size):
            batch = db.batch()
            batch_data = data[i:i + batch_size]
            
            for item in batch_data:
                try:
                    # Добавляем метаданные
                    item['uploaded_at'] = firestore.SERVER_TIMESTAMP
                    # Создаем новый документ
                    doc_ref = collection_ref.document()
                    batch.set(doc_ref, item)
                except Exception as e:
                    logger.error(f"Ошибка при подготовке документа: {e}")
                    continue
            
            # Пытаемся зафиксировать пакет несколько раз при ошибках
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    batch.commit()
                    success += len(batch_data)
                    logger.info(f"Загружено {min(i + len(batch_data), total)}/{total} документов")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Не удалось загрузить пакет после {max_retries} попыток: {e}")
                    else:
                        wait_time = (attempt + 1) * 2  # Экспоненциальная задержка
                        logger.warning(f"Повторная попытка {attempt + 1}/{max_retries} через {wait_time} сек...")
                        time.sleep(wait_time)
        
        logger.info(f"Загрузка завершена. Успешно загружено {success} из {total} документов")
        return success
        
    except Exception as e:
        logger.error(f"Критическая ошибка при загрузке в Firestore: {e}", exc_info=True)
        return 0

def main():
    """Основная функция загрузчика"""
    logger.info("=" * 50)
    logger.info("Запуск загрузчика данных в Firebase")
    logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Загрузка переменных окружения
    if not load_environment():
        return
    
    # Инициализация Firebase
    if not initialize_firebase():
        return
    
    # Загрузка данных из файла
    data = load_food_data('food_database.json')
    if not data:
        logger.error("Не удалось загрузить данные из файла")
        return
    
    # Загрузка в Firestore
    logger.info("Начало загрузки данных в Firestore...")
    collection_name = 'menu'
    uploaded_count = upload_to_firestore(collection_name, data)
    
    logger.info("=" * 50)
    logger.info("Работа загрузчика завершена")
    logger.info(f"Всего загружено записей: {uploaded_count}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Непредвиденная ошибка: {e}", exc_info=True)