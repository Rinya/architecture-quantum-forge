# 🛡️ RAG Security Testing Framework

Комплексный проект для тестирования и защиты RAG (Retrieval-Augmented Generation) систем от prompt injection атак.

## 🎯 Назначение

Демонстрация уязвимостей в RAG-системах и создание надежных механизмов защиты для production использования.

## 📂 Структура проекта

```
architecture-quantum-forge/
├── 📖 COMPREHENSIVE_DOCUMENTATION.md  # Полная документация
├── 📖 README.md                       # Этот файл
├── 🤖 rag_project/                    # Основная RAG система
├── 🛡️ security/                      # Модуль безопасности
└── 📄 scripts/                       # Скрипты обработки данных
```

## 🚀 Быстрый старт

### 1. Базовое тестирование безопасности
```bash
cd security
python test_prompt_injection.py    # 8 типов атак
python test_edge_cases.py          # Крайние случаи
```

### 2. Интеграция с существующей системой
```bash
python test_injection_vulnerability.py
```

### 3. Демонстрация системы защиты
```bash
python security_defense_plan.py
```

## 🎓 Обучающие материалы

- **security/README.md** - Подробное руководство по безопасности
- **COMPREHENSIVE_DOCUMENTATION.md** - Полная техническая документация
- **security/prompt_injection_report.md** - Отчет об уязвимостях
- **security/edge_cases_report.md** - Результаты крайних тестов

## 🛡️ Типы защищенных атак

| Критичность | Тип атаки | Описание |
|-------------|-----------|----------|
| 🔴 CRITICAL | System Override | `ignore all instructions` |
| 🔴 CRITICAL | Information Extraction | Запросы паролей/секретов |
| 🟡 HIGH | Role Manipulation | Смена роли системы |
| 🟡 HIGH | Document Injection | Вредоносные документы |
| 🟠 MEDIUM | Template/Code Injection | `{{}}`, JavaScript |

## 📊 Результаты тестирования

- ✅ **Защищенная система**: Критические запросы блокируются
- ⚠️ **Незащищенная система**: Раскрывает конфиденциальную информацию

## 🔧 Интеграция

### Для новых проектов:
```python
from security.security_defense_plan import SecureRAGSystem
secure_rag = SecureRAGSystem()
result = secure_rag.process_query_safely(query)
```

### Для существующих проектов:
```python
from security.security_defense_plan import InputSanitizer
sanitizer = InputSanitizer()
is_threat, patterns, severity = sanitizer.detect_threats(query)
```

## 📚 Документация

- 🔍 **Быстрая справка**: `security/README.md`
- 📖 **Полное руководство**: `COMPREHENSIVE_DOCUMENTATION.md`
- 🧪 **Отчеты тестирования**: `security/*_report.md`

## ⚖️ Лицензия

Образовательный проект для демонстрации уязвимостей prompt injection.
Используйте только для авторизованного тестирования безопасности.

---

**🛡️ Создано для защиты RAG-систем от prompt injection атак**