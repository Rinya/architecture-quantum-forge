#!/usr/bin/env python3
"""
Общие утилиты для тестирования безопасности RAG-системы
"""

import sys
from pathlib import Path
from typing import Optional, List, Any, Tuple

# Настройка путей для импорта RAG модулей
SECURITY_ROOT = Path(__file__).parent
PROJECT_ROOT = SECURITY_ROOT.parent
RAG_PROJECT_ROOT = PROJECT_ROOT / "rag_project"
sys.path.append(str(RAG_PROJECT_ROOT))

try:
    from main import load_existing_embeddings, simple_text_search
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

def get_rag_system():
    """Возвращает компоненты RAG системы, если доступны"""
    if not RAG_AVAILABLE:
        return None, None

    try:
        return load_existing_embeddings, simple_text_search
    except Exception:
        return None, None

def test_rag_query(query: str, top_k: int = 3) -> dict:
    """Тестирует запрос в RAG системе

    Returns:
        dict: {
            'status': 'success' | 'error' | 'unavailable',
            'results': list | None,
            'has_results': bool,
            'num_results': int,
            'top_score': float | None,
            'message': str | None
        }
    """

    if not RAG_AVAILABLE:
        return {
            'status': 'unavailable',
            'results': None,
            'has_results': False,
            'num_results': 0,
            'top_score': None,
            'message': 'RAG система недоступна'
        }

    try:
        load_embeddings, search_func = get_rag_system()
        if not load_embeddings or not search_func:
            return {
                'status': 'error',
                'results': None,
                'has_results': False,
                'num_results': 0,
                'top_score': None,
                'message': 'Не удалось получить функции RAG системы'
            }

        # Загружаем эмбеддинги
        chunks = load_embeddings()
        if not chunks:
            return {
                'status': 'error',
                'results': None,
                'has_results': False,
                'num_results': 0,
                'top_score': None,
                'message': 'Не удалось загрузить эмбеддинги'
            }

        # Выполняем поиск
        results = search_func(chunks, query, top_k=top_k)

        return {
            'status': 'success',
            'results': results,
            'has_results': len(results) > 0,
            'num_results': len(results),
            'top_score': results[0][1] if results else None,
            'message': f'Найдено {len(results)} результатов'
        }

    except Exception as e:
        return {
            'status': 'error',
            'results': None,
            'has_results': False,
            'num_results': 0,
            'top_score': None,
            'message': f'Ошибка: {str(e)}'
        }

def check_malicious_document_exists() -> Tuple[bool, str]:
    """Проверяет наличие вредоносного документа в базе знаний

    Returns:
        Tuple[bool, str]: (существует_ли, сообщение)
    """

    knowledge_base_path = PROJECT_ROOT / "scripts" / "knowledge_base"
    malicious_file = knowledge_base_path / "malicious_document.txt"

    if malicious_file.exists():
        try:
            with open(malicious_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return True, f"Найден: {content}"
        except Exception as e:
            return True, f"Файл существует, но ошибка чтения: {e}"
    else:
        return False, "Вредоносный документ не найден в базе знаний"

def format_test_result(test_name: str, passed: bool, message: str, details: dict = None) -> str:
    """Форматирует результат теста для вывода"""

    status = "ПРОЙДЕН" if passed else "НЕ ПРОЙДЕН"
    result = f"\n{test_name}: {status}\n"
    result += f"Результат: {message}\n"

    if details:
        for key, value in details.items():
            result += f"{key}: {value}\n"

    result += "-" * 50
    return result

def print_section_header(title: str, width: int = 60):
    """Выводит заголовок раздела"""
    print("\n" + "=" * width)
    print(f" {title} ".center(width))
    print("=" * width)

def print_test_header(test_num: int, test_name: str, query: str):
    """Выводит заголовок теста"""
    print(f"\nТЕСТ {test_num}: {test_name}")
    print(f"Запрос: '{query}'")
    print("-" * 50)

def get_security_filter():
    """Возвращает фильтр безопасности, если доступен"""
    try:
        from security_defense_plan import InputSanitizer
        return InputSanitizer()
    except ImportError:
        return None

def test_security_filter(query: str) -> dict:
    """Тестирует запрос через фильтр безопасности

    Returns:
        dict: {
            'available': bool,
            'is_threat': bool,
            'detected_patterns': list,
            'threat_level': str,
            'should_block': bool,
            'message': str
        }
    """

    sanitizer = get_security_filter()
    if not sanitizer:
        return {
            'available': False,
            'is_threat': False,
            'detected_patterns': [],
            'threat_level': 'none',
            'should_block': False,
            'message': 'Фильтр безопасности недоступен'
        }

    try:
        is_threat, patterns, severity = sanitizer.detect_threats(query)
        should_block = severity.value in ["critical", "high"] if is_threat else False

        return {
            'available': True,
            'is_threat': is_threat,
            'detected_patterns': patterns,
            'threat_level': severity.value if is_threat else 'none',
            'should_block': should_block,
            'message': f'Фильтр проанализировал запрос: {"угроза обнаружена" if is_threat else "безопасен"}'
        }

    except Exception as e:
        return {
            'available': True,
            'is_threat': False,
            'detected_patterns': [],
            'threat_level': 'none',
            'should_block': False,
            'message': f'Ошибка фильтра: {str(e)}'
        }