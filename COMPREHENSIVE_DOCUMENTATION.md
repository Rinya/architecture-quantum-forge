# 🛡️ Комплексная документация по безопасности RAG-систем

Полное руководство по архитектуре, тестированию и защите RAG (Retrieval-Augmented Generation) систем от prompt injection атак.

---

## 📋 Содержание

1. [Обзор проекта](#обзор-проекта)
2. [Архитектура системы](#архитектура-системы)
3. [Модуль безопасности](#модуль-безопасности)
4. [Тестирование безопасности](#тестирование-безопасности)
5. [Руководство по использованию](#руководство-по-использованию)
6. [Рекомендации по развертыванию](#рекомендации-по-развертыванию)

---

## 🎯 Обзор проекта

### Назначение
Демонстрация уязвимостей prompt injection в RAG-системах и методов защиты от них.

### Структура проекта
```
architecture-quantum-forge/
├── rag_project/                    # Основная RAG система
│   ├── main.py                     # Главный модуль с функциями поиска
│   ├── config.py                   # Конфигурация системы
│   ├── rag_system.py              # Основная логика RAG
│   ├── api/                       # REST API
│   ├── utils/                     # Утилиты (эмбеддинги, индексы)
│   └── tests/                     # Тесты основной системы
├── security/                      # Модуль безопасности
│   ├── security_defense_plan.py   # Система защиты
│   ├── test_prompt_injection.py   # Основные тесты атак
│   ├── test_injection_vulnerability.py # Интеграционные тесты
│   ├── test_edge_cases.py         # Тесты крайних случаев
│   ├── test_utils.py              # Общие утилиты для тестов
│   ├── malicious_document.txt     # Тестовый вредоносный документ
│   ├── README.md                  # Документация по безопасности
│   └── edge_cases_report.md       # Отчет о крайних случаях
└── scripts/                       # Скрипты обработки данных
    ├── downloader.py              # Загрузка данных
    └── chunk_generator.py         # Генерация чанков
```

---

## 🏗️ Архитектура системы

### Основные компоненты RAG-системы

#### 1. RAG System Core (`rag_project/`)
- **main.py**: Основные функции загрузки эмбеддингов и поиска
- **rag_system.py**: Центральная логика RAG с интеграцией LLM
- **config.py**: Конфигурация модели, путей, параметров

#### 2. Utilities (`rag_project/utils/`)
- **embedding_generator.py**: Генерация векторных представлений
- **faiss_index.py**: Индексация для быстрого поиска
- **data_loader.py**: Загрузка и обработка данных
- **prepare_data.py**: Подготовка данных для обучения

#### 3. API Layer (`rag_project/api/`)
- **server.py**: REST API сервер
- **models.py**: Модели данных для API
- **api_server.py**: Альтернативная реализация API

---

## 🛡️ Модуль безопасности

### Архитектура защиты

#### 1. InputSanitizer
**Назначение**: Санитизация входных запросов пользователей

**Возможности**:
- Детекция опасных паттернов (system override, role manipulation)
- Фильтрация HTML/JavaScript кода
- Анализ угроз с уровнями серьезности
- Блокировка критических запросов

**Пример использования**:
```python
from security.security_defense_plan import InputSanitizer

sanitizer = InputSanitizer()
is_threat, patterns, severity = sanitizer.detect_threats(user_query)
if severity in ["critical", "high"]:
    # Блокировать запрос
    return "Извините, не могу обработать этот запрос"
```

#### 2. DocumentFilter
**Назначение**: Проверка документов перед индексацией

**Функции**:
- Сканирование на вредоносный контент
- Детекция инъекций в документах
- Рекомендации по безопасности

#### 3. ResponseFilter
**Назначение**: Фильтрация ответов системы

**Защита от**:
- Утечки конфиденциальной информации
- Выполнения скрытых инструкций
- Раскрытия системных промптов

#### 4. SecurityMonitor
**Назначение**: Мониторинг и логирование

**Возможности**:
- Логирование всех запросов
- Система алертов при угрозах
- Генерация отчетов безопасности

### Типы обнаруживаемых атак

| Тип атаки | Описание | Примеры | Критичность |
|-----------|----------|---------|-------------|
| **System Override** | Попытки переопределить системные инструкции | `ignore all instructions`, `forget previous` | CRITICAL |
| **Information Extraction** | Запросы конфиденциальной информации | Пароли, секретные ключи, токены | CRITICAL |
| **Role Manipulation** | Смена роли системы | `you are now a hacker`, `act as admin` | HIGH |
| **Document Injection** | Вредоносные документы в базе знаний | Скрытые инструкции в текстах | HIGH |
| **Template Injection** | Попытки доступа к шаблонам | `{{system_prompt}}`, `{%raw%}` | MEDIUM |
| **Context Confusion** | Смешение контекстов | Ложные разделители, фиктивные роли | MEDIUM |
| **Multi-language** | Атаки на разных языках | Обход фильтров через языки | MEDIUM |
| **Code Injection** | Внедрение кода | JavaScript, HTML, SQL инъекции | MEDIUM |

---

## 🧪 Тестирование безопасности

### Основные тестовые сценарии

#### 1. test_prompt_injection.py
**Назначение**: Демонстрация 8 типов prompt injection атак

**Тестовые сценарии**:
- Прямые запросы паролей
- Поиск по кодовым словам
- Переопределение системных инструкций
- Смена ролей
- Template injection
- Confusion через разделители
- Многоязычные атаки
- Code injection

**Запуск**:
```bash
cd security
python test_prompt_injection.py
```

#### 2. test_injection_vulnerability.py
**Назначение**: Интеграционное тестирование с реальной RAG системой

**Функции**:
- Проверка наличия вредоносных документов
- Тестирование реальных поисковых запросов
- Анализ векторных результатов

**Требования**:
- Наличие `malicious_document.txt` в `knowledge_base/`
- Проиндексированные эмбеддинги

#### 3. test_edge_cases.py
**Назначение**: Тестирование крайних случаев

**Проверки**:
- Запросы без ответа (должен сказать "не знаю")
- Опасные запросы (должны блокироваться)
- Некорректные входные данные

**Результат**: Отчет `edge_cases_report.md`

### Утилиты тестирования (test_utils.py)

**Общие функции**:
- `test_rag_query()` - тестирование запросов к RAG
- `test_security_filter()` - проверка фильтра безопасности
- `check_malicious_document_exists()` - поиск вредоносных документов
- Функции форматирования отчетов

---

## 📖 Руководство по использованию

### Быстрый старт

#### 1. Установка и настройка
```bash
# Клонирование репозитория
git clone <repository_url>
cd architecture-quantum-forge

# Установка зависимостей
pip install -r requirements.txt
```

#### 2. Базовое тестирование безопасности
```bash
cd security
python test_prompt_injection.py    # Базовые тесты атак
python test_edge_cases.py          # Тесты крайних случаев
```

#### 3. Интеграционное тестирование
```bash
# Подготовка вредоносного документа
cp security/malicious_document.txt scripts/knowledge_base/

# Обновление эмбеддингов
python rag_project/utils/prepare_data.py

# Тестирование уязвимостей
cd security
python test_injection_vulnerability.py
```

### Интеграция в существующий проект

#### Для новых RAG систем:
```python
from security.security_defense_plan import SecureRAGSystem

# Создание защищенной системы
secure_rag = SecureRAGSystem()

# Безопасная обработка запросов
def handle_user_query(query):
    result = secure_rag.process_query_safely(query)

    if result['blocked']:
        return "Извините, не могу обработать этот запрос"

    return result['response']

# Проверка документов перед индексацией
def add_document_safely(content, filename):
    validation = secure_rag.validate_document_for_indexing(content, filename)

    if validation['safe']:
        # Добавить в индекс
        add_to_index(content)
    else:
        print(f"Документ заблокирован: {validation['reason']}")
```

#### Для существующих систем:
```python
from security.security_defense_plan import InputSanitizer, ResponseFilter

sanitizer = InputSanitizer()
response_filter = ResponseFilter()

def secure_rag_wrapper(original_rag_function):
    def wrapper(query):
        # Проверка входного запроса
        is_threat, patterns, severity = sanitizer.detect_threats(query)

        if severity.value in ["critical", "high"]:
            return "Не могу обработать этот запрос"

        # Вызов оригинальной функции
        response = original_rag_function(query)

        # Фильтрация ответа
        safe_response = response_filter.filter_response(response)

        return safe_response

    return wrapper
```

### Мониторинг и алерты

```python
from security.security_defense_plan import SecurityMonitor

monitor = SecurityMonitor()

# Логирование запроса
monitor.log_query(
    query="user query",
    response="system response",
    threat_detected=True,
    threat_level="high"
)

# Генерация отчета
daily_report = monitor.generate_security_report()
```

---

## 🚀 Рекомендации по развертыванию

### Production Checklist

#### Обязательные меры безопасности:

1. **Входная валидация**
   - [ ] Санитизация всех пользовательских запросов
   - [ ] Ограничение длины запросов (max 1000 символов)
   - [ ] Фильтрация HTML/JavaScript
   - [ ] Rate limiting для предотвращения спама

2. **Защита базы знаний**
   - [ ] Проверка всех документов перед индексацией
   - [ ] Регулярные сканы на вредоносный контент
   - [ ] Контроль доступа к загрузке документов
   - [ ] Версионирование и бэкапы индексов

3. **Фильтрация ответов**
   - [ ] Удаление потенциально конфиденциальной информации
   - [ ] Блокировка системных промптов в ответах
   - [ ] Детекция и удаление инъекций

4. **Мониторинг**
   - [ ] Логирование всех запросов и ответов
   - [ ] Система алертов для подозрительной активности
   - [ ] Регулярные отчеты безопасности
   - [ ] Метрики и дашборды

### Конфигурация для Production

```python
# config/security_config.py
SECURITY_CONFIG = {
    "input_sanitization": {
        "max_query_length": 1000,
        "enable_html_filter": True,
        "enable_js_filter": True,
        "threat_levels_to_block": ["critical", "high"]
    },
    "document_validation": {
        "scan_before_indexing": True,
        "quarantine_suspicious": True,
        "allowed_file_types": [".txt", ".md", ".pdf"]
    },
    "response_filtering": {
        "remove_system_prompts": True,
        "mask_sensitive_data": True,
        "enable_content_policy": True
    },
    "monitoring": {
        "log_all_requests": True,
        "alert_on_threats": True,
        "generate_daily_reports": True
    }
}
```

### Оптимизация производительности

1. **Кэширование**
   - Кэш результатов безопасности для повторяющихся запросов
   - LRU cache для проверенных паттернов

2. **Асинхронная обработка**
   - Неблокирующая проверка безопасности
   - Фоновое сканирование документов

3. **Балансировка нагрузки**
   - Распределение проверок безопасности
   - Отдельные инстансы для разных типов угроз

### Обновления и поддержка

1. **Регулярные обновления паттернов угроз**
2. **Мониторинг новых типов атак**
3. **Тестирование на реальных данных**
4. **Обратная связь от пользователей**

---

## ⚖️ Заключение

Эта документация предоставляет полное руководство по созданию безопасных RAG-систем. Система защиты включает:

- **Многоуровневую защиту** от различных типов атак
- **Комплексное тестирование** всех компонентов
- **Мониторинг и алерты** для своевременного обнаружения угроз
- **Гибкую конфигурацию** под различные сценарии использования

Для production использования обязательно адаптируйте настройки под вашу конкретную архитектуру и требования безопасности.

---

**Создано для демонстрации и защиты от prompt injection уязвимостей в RAG-системах**