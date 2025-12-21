# search_demo.py
import json
from faiss_index import FAISSIndex  # Импортируем наш класс

# Конфигурация
MODEL_PATH = r"C:\yandex-architecture\sprint7\local_models\paraphrase-multilingual-MiniLM-L12-v2"
INDEX_FILE = "faiss_index.bin"
EMBEDDINGS_FILE = "embeddings.json"

# Загрузка индекса
print("Загрузка индекса...")
faiss_index = FAISSIndex(MODEL_PATH)
faiss_index.load_index(INDEX_FILE, EMBEDDINGS_FILE)

# Показать статистику
stats = faiss_index.get_stats()
print(f"\nСтатистика индекса:")
for key, value in stats.items():
    print(f"  {key}: {value}")

# Интерактивный поиск
print("\nСистема поиска готова. Введите запрос (или 'exit' для выхода):")
while True:
    query = input("\nПоисковый запрос: ").strip()
    
    if query.lower() == 'exit':
        break
    
    if not query:
        continue
    
    # Выполняем поиск
    results = faiss_index.search(query, k=5)
    
    print(f"\nНайдено результатов: {len(results)}")
    for result in results:
        print(f"\n=== Результат #{result['rank']} (расстояние: {result['distance']:.4f}) ===")
        print(f"Текст: {result['chunk']['content'][:300]}...")
        if 'metadata' in result['chunk']:
            print(f"Метаданные: {result['chunk']['metadata']}")
        print("-" * 80)
