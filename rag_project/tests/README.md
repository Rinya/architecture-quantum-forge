# Tests

Тестовые модули для RAG системы.

## Файлы

### `test_api.py`
Тесты REST API endpoints:
- Health check
- Search functionality
- Answer generation (Few-shot)
- Chain-of-Thought prompting
- Document listing
- System statistics

**Запуск:**
```bash
# Сначала запустить сервер
python api_server.py

# В отдельном терминале
cd tests
python test_api.py
```

### `test_fewshot.py`
Тесты Few-shot промптинга:
- FewShotPromptGenerator
- ContextualPromptGenerator
- Chain-of-Thought интеграция
- RAG система с промптингом

**Запуск:**
```bash
cd tests
python test_fewshot.py
```

## Структура

```
tests/
├── __init__.py
├── README.md
├── test_api.py        # REST API тесты
└── test_fewshot.py    # Few-shot промптинг тесты
```

## Результаты

Все тесты должны проходить:
- **API тесты**: 6/6 endpoints (100% success)
- **Few-shot тесты**: Промпты генерируются корректно
- **Chain-of-Thought**: Пошаговые рассуждения работают