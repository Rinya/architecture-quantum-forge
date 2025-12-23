# 🚀 RAG System REST API Documentation

## Обзор

REST API для системы RAG (Retrieval-Augmented Generation) с поддержкой Few-shot prompting и Chain-of-Thought рассуждений.

### Базовый URL
```
http://localhost:8000
```

### Возможности
- ✅ Семантический поиск по документам
- ✅ Генерация ответов с Few-shot prompting
- ✅ Chain-of-Thought рассуждения
- ✅ Детальные ответы с метаданными
- ✅ Построение контекста для LLM
- ✅ Управление документами
- ✅ Мониторинг системы

---

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install fastapi uvicorn pydantic
```

### 2. Запуск сервера
```bash
# Из корня проекта
python api_server.py

# Или напрямую
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

### 3. Доступ к документации
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

### 4. Тестирование
```bash
python test_api.py
```

---

## 📋 API Endpoints

### 🏥 Health & Monitoring

#### `GET /health`
Проверка состояния сервиса.

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "system_initialized": true,
    "uptime_seconds": 123.45
}
```

#### `GET /stats`
Статистика системы.

**Response:**
```json
{
    "status": "initialized",
    "prompt_generator": "ContextualPromptGenerator",
    "adaptive_prompting": true,
    "total_chunks": 4579,
    "unique_documents": 35,
    "index_type": "flat",
    "total_vectors": 4579
}
```

---

### 🔍 Search Operations

#### `POST /search`
Семантический поиск по всем документам.

**Request:**
```json
{
    "query": "Кто такой Алпамыш?",
    "top_k": 5,
    "min_similarity": 0.5
}
```

**Response:**
```json
{
    "query": "Кто такой Алпамыш?",
    "results": [
        {
            "rank": 1,
            "similarity_score": 0.809,
            "document_title": "Алпамыш_(роман_Юсупова).txt",
            "chunk_id": "chunk_123",
            "text": "Алпамыш — главный герой...",
            "file_path": "/path/to/file.txt"
        }
    ],
    "total_found": 5,
    "processing_time_ms": 156.3
}
```

#### `POST /search/document`
Поиск внутри конкретного документа.

**Request:**
```json
{
    "query": "богатырь",
    "document_title": "Алпамыш_(роман_Юсупова).txt",
    "top_k": 3
}
```

---

### 🤖 Answer Generation

#### `POST /answer`
Генерация ответа с Few-shot prompting.

**Request:**
```json
{
    "query": "Что такое народный эпос?",
    "top_k": 5,
    "max_context_length": 2000,
    "use_fewshot": true
}
```

**Response:**
```json
{
    "query": "Что такое народный эпос?",
    "answer_prompt": "Ты эксперт по фольклору...",
    "query_type": "what",
    "confidence": 0.756,
    "processing_time_ms": 234.7
}
```

#### `POST /answer/cot`
Генерация ответа с Chain-of-Thought рассуждениями.

**Request:**
```json
{
    "query": "Кто такой Алпамыш?",
    "top_k": 5,
    "max_context_length": 2000
}
```

**Response:**
```json
{
    "query": "Кто такой Алпамыш?",
    "answer_prompt": "Ты эксперт по фольклору...\n\nВАЖНО: Следуй этой структуре ответа:\n1. Сначала проанализируй...",
    "query_type": "who",
    "confidence": 0.723,
    "processing_time_ms": 198.1
}
```

#### `POST /answer/detailed`
Детальная генерация ответа с метаданными.

**Request:**
```json
{
    "query": "богатырь",
    "top_k": 5,
    "max_context_length": 2000,
    "use_fewshot": true
}
```

**Response:**
```json
{
    "query": "богатырь",
    "answer_prompt": "Ты эксперт по фольклору...",
    "query_type": "general",
    "confidence": 0.684,
    "sources": [
        {
            "document": "Алпамыш_(роман_Юсупова).txt",
            "chunk_id": "chunk_456",
            "similarity": 0.793,
            "text_preview": "Богатыри в эпосах..."
        }
    ],
    "total_results": 3,
    "structured_data": {...},
    "processing_time_ms": 289.4
}
```

---

### 📄 Context & Documents

#### `POST /context`
Построение контекста для LLM.

**Request:**
```json
{
    "query": "узбекский эпос",
    "top_k": 3,
    "min_similarity": 0.6
}
```

**Response:**
```json
{
    "query": "узбекский эпос",
    "context": "[Document: Алпамыш.txt, Score: 0.856]\\nАлпамыш является...",
    "processing_time_ms": 112.5
}
```

#### `GET /documents`
Получение списка всех документов.

**Response:**
```json
[
    "Алпамыш_(роман_Юсупова).txt",
    "Копьё_из_стали.txt",
    "Народные_эпосы.txt"
]
```

---

## 🛡️ Error Handling

Все ошибки возвращаются в стандартном формате:

```json
{
    "error": "ValidationError",
    "message": "Query length must be between 1 and 1000 characters",
    "details": {
        "field": "query",
        "value": ""
    }
}
```

### HTTP Status Codes

- **200** - Успешный запрос
- **400** - Некорректные данные запроса
- **422** - Ошибка валидации
- **500** - Внутренняя ошибка сервера
- **503** - Сервис недоступен (система не инициализирована)

---

## 🔧 Параметры запросов

### SearchRequest
- `query` (string, обязательный): Поисковый запрос (1-1000 символов)
- `top_k` (integer): Количество результатов (1-20, по умолчанию 5)
- `min_similarity` (float): Минимальный порог схожести (0.0-1.0, по умолчанию 0.5)

### AnswerRequest
- `query` (string, обязательный): Вопрос (1-1000 символов)
- `top_k` (integer): Количество контекстных документов (1-20, по умолчанию 5)
- `max_context_length` (integer): Максимальная длина контекста (500-10000, по умолчанию 2000)
- `use_fewshot` (boolean): Использовать Few-shot prompting (по умолчанию true)

---

## 📊 Мониторинг производительности

Все эндпоинты возвращают время обработки в поле `processing_time_ms`.

### Типичное время отклика
- **Search**: 50-200ms
- **Answer generation**: 100-300ms
- **CoT generation**: 150-350ms
- **Detailed answer**: 200-400ms

---

## 🚀 Примеры использования

### Python (requests)
```python
import requests

# Поиск
response = requests.post(
    "http://localhost:8000/search",
    json={"query": "Алпамыш", "top_k": 3}
)
results = response.json()

# Генерация ответа
response = requests.post(
    "http://localhost:8000/answer",
    json={
        "query": "Что такое эпос?",
        "max_context_length": 1500
    }
)
answer = response.json()
```

### cURL
```bash
# Health check
curl http://localhost:8000/health

# Поиск
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Алпамыш", "top_k": 3}'

# Chain-of-Thought ответ
curl -X POST http://localhost:8000/answer/cot \
  -H "Content-Type: application/json" \
  -d '{"query": "Кто такой Алпамыш?", "top_k": 3}'
```

### JavaScript (fetch)
```javascript
// Поиск
const searchResponse = await fetch('http://localhost:8000/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        query: 'народный эпос',
        top_k: 5
    })
});
const results = await searchResponse.json();

// Генерация ответа
const answerResponse = await fetch('http://localhost:8000/answer/detailed', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        query: 'Что представляет собой фольклор?',
        max_context_length: 2000
    })
});
const answer = await answerResponse.json();
```

---

## 🔒 Безопасность

### CORS
API настроен с разрешением всех источников для разработки. В продакшене ограничьте `allow_origins`.

### Лимиты
- Максимальная длина запроса: 1000 символов
- Максимальное количество результатов: 20
- Максимальная длина контекста: 10000 символов

### Таймауты
- Инициализация системы: до 30 секунд
- Обработка запросов: до 30 секунд

---

## 🛠️ Разработка

### Локальный запуск
```bash
# Режим разработки с автоперезагрузкой
uvicorn api.server:app --reload --log-level debug

# С настраиваемым хостом и портом
uvicorn api.server:app --host 0.0.0.0 --port 8080
```

### Переменные окружения
- `HOST`: Хост сервера (по умолчанию 0.0.0.0)
- `PORT`: Порт сервера (по умолчанию 8000)
- `LOG_LEVEL`: Уровень логирования (по умолчанию info)

---

## 📚 Интерактивная документация

После запуска сервера доступна автоматически сгенерированная документация:

- **Swagger UI**: http://localhost:8000/docs
  - Интерактивное тестирование API
  - Автоматическая валидация
  - Примеры запросов и ответов

- **ReDoc**: http://localhost:8000/redoc
  - Красивое отображение документации
  - Удобная навигация
  - Детальные описания моделей

---

## 🎯 Заключение

API предоставляет полный доступ к функциональности RAG системы:

1. **Поиск** - семантический поиск по документам
2. **Few-shot prompting** - генерация ответов с примерами
3. **Chain-of-Thought** - пошаговые рассуждения
4. **Мониторинг** - статистика и health checks

Для получения помощи обращайтесь к интерактивной документации по адресу `/docs`.