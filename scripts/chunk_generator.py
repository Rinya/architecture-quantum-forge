import os
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Папка с текстовыми файлами
input_dir = "knowledge_base"

# Параметры разбиения
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = []  # Список для хранения чанков с метаданными

# Обработка каждого файла
for filename in os.listdir(input_dir):
    if filename.endswith(".txt"):
        file_path = os.path.join(input_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Разбиение на чанки
        docs = text_splitter.split_text(text)  # Используем split_text вместо create_documents
        
        # Обрабатываем каждый чанк
        for i, doc_content in enumerate(docs):
            chunk_data = {
                "document_title": filename,
                "file_path": file_path,
                "chunk_id": f"{filename}_chunk_{i+1}",
                "start_position": i * 200,  # Приблизительная позиция
                "content": doc_content
            }
            chunks.append(chunk_data)

# Сохранение чанков в JSON
with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=4)

print(f"Разбиение завершено. Обработано {len(chunks)} чанков, сохранено в chunks.json.")