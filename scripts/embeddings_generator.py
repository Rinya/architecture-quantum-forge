import json
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm  # Для прогресс-бара

# Укажите путь к вашей локальной модели
#model_path = 'paraphrase-multilingual-MiniLM-L12-v2'
model_path = r"C:\yandex-architecture\sprint7\local_models\paraphrase-multilingual-MiniLM-L12-v2"

model = SentenceTransformer(model_path)
print("Модель загружена.")

# Загрузка чанков
with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

embeddings_data = []  # Список для хранения данных с эмбеддингами

# Генерация эмбеддингов для каждого чанка
for chunk in tqdm(chunks, desc="Генерация эмбеддингов"):
    # Получение вектора (эмбеддинга)
    embedding = model.encode(chunk["content"], convert_to_numpy=True)  # Вектор размером 384
    embedding_list = embedding.tolist()  # Преобразуем в список для JSON
    
    # Сохраняем с метаданными (добавляем эмбеддинг к существующим полям)
    chunk_with_embedding = chunk.copy()
    chunk_with_embedding["embedding"] = embedding_list
    embeddings_data.append(chunk_with_embedding)

# Сохранение в JSON
with open("embeddings.json", "w", encoding="utf-8") as f:
    json.dump(embeddings_data, f, ensure_ascii=False, indent=4)

print(f"Эмбеддинги сгенерированы. Сохранено {len(embeddings_data)} элементов в embeddings.json.")
