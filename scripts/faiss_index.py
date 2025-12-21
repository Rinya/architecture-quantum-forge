import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import time  # Импорт модуля для измерения времени

class FAISSIndex:
    def __init__(self, model_path, dimension=384):
        self.model = SentenceTransformer(model_path)
        self.dimension = dimension
        self.index = None
        self.chunks_data = []  # Для хранения метаданных чанков
        self.total_chunks = 0  # Счетчик общего количества чанков
        
    def create_index_from_json(self, embeddings_file):
        """Создание индекса FAISS из JSON файла с эмбеддингами"""
        start_time = time.time()  # Засекаем время начала
        
        print("Загрузка эмбеддингов...")
        with open(embeddings_file, "r", encoding="utf-8") as f:
            chunks_with_embeddings = json.load(f)
        
        # Подсчитываем общее количество чанков
        self.total_chunks = len(chunks_with_embeddings)
        print(f"Найдено чанков: {self.total_chunks}")
        
        # Извлекаем эмбеддинги и метаданные
        embeddings = []
        self.chunks_data = []
        
        for chunk in tqdm(chunks_with_embeddings, desc="Подготовка данных для индекса"):
            embeddings.append(chunk["embedding"])
            # Сохраняем метаданные без самого эмбеддинга для экономии памяти
            chunk_data = chunk.copy()
            del chunk_data["embedding"]
            self.chunks_data.append(chunk_data)
        
        # Проверяем, что данные не пустые
        if len(embeddings) == 0:
            raise ValueError("Не найдено эмбеддингов для создания индекса!")
        
        # Преобразуем в numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Создаем индекс FAISS
        print("Создание индекса FAISS...")
        self.index = faiss.IndexFlatL2(self.dimension)  # L2 расстояние (евклидово)
        self.index.add(embeddings_array)
        
        end_time = time.time()  # Засекаем время окончания
        creation_time = end_time - start_time  # Вычисляем общее время
        
        print(f"Индекс создан. Добавлено {self.index.ntotal} векторов.")
        print(f"Всего обработано чанков: {self.total_chunks}")
        print(f"Время создания индекса: {creation_time:.2f} секунд ({creation_time/60:.2f} минут)")
    
    def save_index(self, index_file):
        """Сохранение индекса в файл"""
        if self.index:
            faiss.write_index(self.index, index_file)
            print(f"Индекс сохранен в {index_file}")
    
    def load_index(self, index_file, embeddings_file):
        """Загрузка индекса и метаданных из файлов"""
        self.index = faiss.read_index(index_file)
        
        # Загружаем метаданные
        with open(embeddings_file, "r", encoding="utf-8") as f:
            chunks_with_embeddings = json.load(f)
        
        self.chunks_data = []
        for chunk in chunks_with_embeddings:
            chunk_data = chunk.copy()
            del chunk_data["embedding"]
            self.chunks_data.append(chunk_data)
        
        self.total_chunks = len(self.chunks_data)
        print(f"Индекс загружен. Векторов: {self.index.ntotal}")
        print(f"Всего чанков в индексе: {self.total_chunks}")
    
    def get_stats(self):
        """Получение статистики по индексу"""
        if not self.index:
            return {"status": "Индекс не загружен"}
        
        return {
            "status": "Индекс загружен",
            "total_vectors": self.index.ntotal,
            "total_chunks": self.total_chunks,
            "dimension": self.dimension
        }
    
    def search(self, query, k=5):
        """Поиск по текстовому запросу"""
        if not self.index:
            raise ValueError("Индекс не загружен!")
        
        # Получаем эмбеддинг для запроса
        query_embedding = self.model.encode([query], convert_to_numpy=True).astype('float32')
        
        # Выполняем поиск
        distances, indices = self.index.search(query_embedding, k)
        
        # Формируем результаты
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx != -1:  # -1 означает отсутствие результата
                result = {
                    "rank": i + 1,
                    "distance": float(distance),
                    "chunk": self.chunks_data[idx]
                }
                results.append(result)
        
        return results
    
    def search_similar(self, embedding, k=5):
        """Поиск по готовому эмбеддингу"""
        if not self.index:
            raise ValueError("Индекс не загружен!")
        
        embedding = np.array([embedding]).astype('float32')
        distances, indices = self.index.search(embedding, k)
        
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx != -1:
                result = {
                    "rank": i + 1,
                    "distance": float(distance),
                    "chunk": self.chunks_data[idx]
                }
                results.append(result)
        
        return results

# Пример использования
if __name__ == "__main__":
    # Конфигурация
    MODEL_PATH = r"C:\yandex-architecture\sprint7\local_models\paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDINGS_FILE = "embeddings.json"
    INDEX_FILE = "faiss_index.bin"
    
    # Инициализация
    faiss_index = FAISSIndex(MODEL_PATH)
    
    # Создание и сохранение индекса (выполнить один раз)
    print("=== СОЗДАНИЕ ИНДЕКСА ===")
    faiss_index.create_index_from_json(EMBEDDINGS_FILE)
    faiss_index.save_index(INDEX_FILE)
    
    # Показать статистику
    stats = faiss_index.get_stats()
    print(f"\nСтатистика индекса:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Альтернативно: загрузка существующего индекса
    # print("=== ЗАГРУЗКА ИНДЕКСА ===")
    # faiss_index.load_index(INDEX_FILE, EMBEDDINGS_FILE)
    
    # Пример поиска
    print("\n=== ПРИМЕР ПОИСКА ===")
    query = "Алпамыш"
    results = faiss_index.search(query, k=3)
    
    print(f"Результаты поиска для: '{query}'")
    for result in results:
        print(f"\n#{result['rank']} (расстояние: {result['distance']:.4f})")
        print(f"Текст: {result['chunk']['content'][:200]}...")  # Первые 200 символов
        print(f"Метаданные: {result['chunk'].get('metadata', {})}")
