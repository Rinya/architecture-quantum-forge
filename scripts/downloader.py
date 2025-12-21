import os
import re
import json
import requests
from bs4 import BeautifulSoup
import uuid
import unicodedata
from faker import Faker

# Custom slugify function (Python 3-compatible replacement for the external slugify library)
def slugify(text):
    """
    Convert text to a URL-friendly slug: lowercase, remove accents, replace spaces/special chars with hyphens.
    """
    # Normalize Unicode (remove accents)
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')
    # Remove non-alphanumeric/space chars, replace spaces/multiple hyphens with single hyphens
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-').lower()
    return text

# Инициализация генераторов
faker = Faker()

# Список терминов для замены (ключевые имена, объекты и события из Алпамыша; можно расширить)
terms_to_replace = [
    # Персонажи
    "Алпамыш", "Байбури", "Карлук", "Сандук", "Каракёль", "Барсын-хан", "Телхман", "Ер-Таргын", "Чингисхан",
    # Объекты
    "Конь Байчибар", "Меч Алпамыша", "Дворец Барсына", "Зелье исцеления", "Копьё", "Келинек", "Сандал", "Шатёр", "Амулет",
    "Кольцо",  # Если "или кольцо" - заменить на "Кольцо" для упрощения
    # Технологии (ключевые фразы)
    "Лук и стрелы", "Конная езда", "Джигитовка", "Состязания в борьбе", "Строительство крепостей", "Кузнечное дело",
    "Шаманские ритуалы", "Охота с луком", "Навигация по рекам",
    # События (ключевые фразы для замены на слоганы или имена)
    "Рождение Алпамыша", "Поездка с Конем Байчибаром", "Утечка молока Байбури", "Пленение Алпамыша Калмыками",
    "Битва Алпамыша", "Побег из плена", "Свадьба Алпамыша и Байбури", "Собор Алпамыша", "Смерть и возрождение"
]

# Генерация словаря замен динамически
replacements = {}
for term in terms_to_replace:
    random_word = faker.word()  # Генерируем случайное слово с помощью Faker (замена randomword)
    if " " in term:  # Фразы с пробелами (например, события, объекты, технологии)
        replacements[term] = slugify(f"{random_word} {faker.word()}")  # Slug из случайного слова и фейкового слова
    elif term in ["Алпамыш", "Байбури", "Карлук", "Сандук", "Каракёль", "Барсын-хан", "Телхман", "Ер-Таргын", "Чингисхан"]:
        # Персонажи - генерируем фейковые имена
        replacements[term] = faker.name()
    else:  # Для остальных одиночных терминов (например, "Келинек") - случайное слово с UUID для уникальности
        replacements[term] = f"{random_word}-{str(uuid.uuid4())[:4]}"

# Сохранение словаря замен в terms_map.json (исправлено для избежания предупреждения типов)
with open("terms_map.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(replacements, ensure_ascii=False, indent=4) + '\n')

# Функция для извлечения текста определенного раздела по якорю
def extract_section_text(soup, section_id):
    """
    Извлекает текст раздела, начиная с элемента с данным id (якорем), 
    и заканчиваясь перед следующим заголовком того же или меньшего уровня.
    """
    section = soup.find(id=section_id)
    if not section:
        return "Раздел с id '{}' не найден.".format(section_id)
    
    # Определяем уровень заголовка, если это заголовок
    if section.name and section.name.startswith('h'):
        level = int(section.name[1:])
    else:
        # Если не заголовок, берём текст этого элемента и его детей
        return section.get_text(separator=' ', strip=True)
    
    # Собираем текст: от заголовка и далее, пока не следующий заголовок <= level
    text_parts = [section.get_text()]
    current = section.next_sibling
    while current:
        if current.name and current.name.startswith('h') and int(current.name[1:]) <= level:
            break
        if current.name not in ['style', 'script']:
            text_parts.append(current.get_text(separator=' ', strip=True) if hasattr(current, 'get_text') else str(current))
        current = current.next_sibling
    
    # Объединяем и очищаем от множественных пробелов
    text = ' '.join(text_parts).strip()
    text = re.sub(r'\s+', ' ', text)
    return text

# Функция для очистки всего текста страницы (без якоря)
def clean_full_text(soup):
    """
    Извлекает чистый текст из основного контента страницы Википедии.
    """
    content_div = soup.find('div', id='mw-content-text')
    if not content_div:
        content_div = soup.body
    
    text = content_div.get_text(separator=' ', strip=True)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Список сущностей (URL могут содержать якоря)
entities = [
    # Персонажи (около 9)
    ("Алпамыш (главный герой)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Байбури (любовь Алпамыша)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Карлук (отец Алпамыша)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Сандук (слуга Алпамыша)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Каракёль (слуга Байбури)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Барсын-хан (отец Байбури)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Телхман (дворецкий хана)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Ер-Таргын (батрачка)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Чингисхан (в некоторых версиях)", "https://ru.wikipedia.org/wiki/Чингисхан"),
    # Объекты (около 9)
    ("Конь Байчибар", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Меч Алпамыша", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Дворец Барсына", "https://ru.wikipedia.org/wiki/Алпамыш#Алпамыш_и_Байбури"),
    ("Зелье исцеления", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Копьё (орудие)", "https://ru.wikipedia.org/wiki/Алпамыш#Сюжет"),
    ("Келинек (птица-помощница)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Сандал (лодка)", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Шатёр (юрта)", "https://ru.wikipedia.org/wiki/Алпамыш#Бытовые_элементы"),
    ("Амулет или кольцо", "https://ru.wikipedia.org/wiki/Алпамыш"),
    # Технологии (около 8)
    ("Лук и стрелы в эпосе", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Конная езда и джигитовка", "https://ru.wikipedia.org/wiki/Кочевники#Военное_дело"),
    ("Состязания в борьбе", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Строительство крепостей", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Кузнечное дело", "https://ru.wikipedia.org/wiki/Алпамыш#Ремёсла"),
    ("Шаманские ритуалы", "https://ru.wikipedia.org/wiki/Тенгрианство"),
    ("Охота с луком", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Навигация по рекам", "https://ru.wikipedia.org/wiki/Алпамыш"),
    # События (около 9)
    ("Рождение Алпамыша", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Поездка с Конем Байчибаром", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Утечка молока Байбури", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Пленение Алпамыша Калмыками", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Битва Алпамыша", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Побег из плена", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Свадьба Алпамыша и Байбури", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Собор Алпамыша", "https://ru.wikipedia.org/wiki/Алпамыш"),
    ("Смерть и возрождение", "https://ru.wikipedia.org/wiki/Алпамыш"),
]

# Директория для сохранения файлов
output_dir = "knowledge_base"
os.makedirs(output_dir, exist_ok=True)

# User-Agent для имитации браузера
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Группируем сущности по base_url, чтобы управлять кэшем
grouped_entities = {}
for entity, url in entities:
    if '#' in url:
        base_url, anchor = url.split('#', 1)
    else:
        base_url, anchor = url, None
    if base_url not in grouped_entities:
        grouped_entities[base_url] = []
    grouped_entities[base_url].append((entity, anchor))

# Инициализация кэша для страниц (в памяти)
cache = {}

# Основной цикл скачивания и обработки (теперь с кэшем)
for base_url, entity_list in grouped_entities.items():
    soup = None
    # Проверяем кэш
    if base_url in cache:
        soup = cache[base_url]
        print(f"Используем кэшированную страницу для base_url: {base_url}")
    else:
        try:
            response = requests.get(base_url, headers=headers, timeout=10)
            response.raise_for_status()  # Проверяем на ошибки HTTP
            soup = BeautifulSoup(response.content, 'html.parser')
            cache[base_url] = soup  # Сохраняем в кэш
            print(f"Скачано и кэшировано: {base_url}")
        except requests.RequestException as e:
            print(f"Ошибка при скачивании {base_url}: {e}")
            continue
        except Exception as e:
            print(f"Ошибка при обработке {base_url}: {e}")
            continue
    
    # Теперь обрабатываем каждую сущность для этого base_url
    for entity, anchor in entity_list:
        try:
            # Извлекаем текст: раздел или вся страница
            if anchor:
                cleaned_text = extract_section_text(soup, anchor)
            else:
                cleaned_text = clean_full_text(soup)  # Правильно вызываем функцию с аргументом soup
            
            # Добавлено: применяем замены терминов
            for old_term, new_term in replacements.items():
                cleaned_text = cleaned_text.replace(old_term, new_term)
            
            # Создаём имя файла: безопасное для файловой системы, с .txt
            safe_entity_name = re.sub(r'[<>:"/\\|?*]', '', entity).replace(' ', '_')
            file_path = os.path.join(output_dir, f"{safe_entity_name}.txt")
            
            # Сохраняем текст в файл
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            print(f"Сохранено: {file_path}")
        
        # Для обработки ошибок на уровне сущности (например, если якорь не найден)
        except Exception as e:
            print(f"Ошибка при обработке сущности '{entity}' с URL {base_url}#{anchor or 'без_якоря'}: {e}")
            continue  # Продолжаем с следующей сущностью

print("Все операции завершены!")
