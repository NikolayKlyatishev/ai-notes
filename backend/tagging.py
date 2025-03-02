"""
Модуль для интеллектуальной генерации тегов на основе транскрипта.
Специализирован для работы с русским языком.
"""
import re
import logging
from nltk.probability import FreqDist
from nltk.corpus import stopwords

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Расширенный список стоп-слов для русского языка
try:
    STOPWORDS = set(stopwords.words('russian'))
except:
    # Если NLTK не установлен или русские стоп-слова недоступны, используем базовый список
    STOPWORDS = set()

# Дополняем список стоп-слов
STOPWORDS.update([
    "это", "так", "вот", "быть", "как", "в", "—", "к", "на", "да", "ты", 
    "не", "наверное", "точно", "просто", "очень", "также", "вообще",  
    "именно", "ещё", "еще", "например", "всегда", "либо", "или", "будет",
    "может", "можно", "также", "какой", "какая", "какое", "какие", "был", "была", "были",
    "который", "которая", "которые", "когда", "только", "можно", "нужно", "такой", "один",
    "и", "а", "но", "что", "то", "с", "по", "за", "от", "из", "у", "о", "об", "я", "мы", "они", "он", "она", "оно",
    "все", "весь", "вся", "меня", "тебя", "его", "её", "нас", "вас", "их", "мой", "твой", "свой", "наш", "ваш"
])

def clean_text(text):
    """Очищает текст от спецсимволов и приводит к нижнему регистру."""
    text = text.lower()
    # Удаляем спецсимволы, но сохраняем дефисы внутри слов
    text = re.sub(r'[^\w\s-]', ' ', text)
    # Заменяем несколько пробелов одним
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_word(word):
    """
    Упрощенная нормализация слова для русского языка.
    Убирает некоторые распространенные окончания.
    """
    # Список распространенных окончаний для русского языка
    suffixes = [
        'ами', 'ами', 'ого', 'его', 'ому', 'ему', 'ыми', 'ими',
        'ой', 'ый', 'ий', 'ая', 'яя', 'ое', 'ее', 'ут', 'ют',
        'ат', 'ят', 'ешь', 'ёшь', 'ишь', 'ем', 'им', 'ете', 'ите',
        'ал', 'ял', 'ыл', 'ил', 'ала', 'яла', 'ыла', 'ила',
        'ть', 'еть', 'ать', 'ять', 'уть', 'ють', 'ить'
    ]
    
    if len(word) > 4:  # Проверяем длину, чтобы не отрезать слишком много
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) - len(suffix) > 3:
                return word[:-len(suffix)]
    
    return word

def extract_keywords(text, max_tags=10, min_word_length=4, min_frequency=1):
    """
    Извлекает ключевые слова из текста для использования в качестве тегов.
    
    Args:
        text (str): Текст для анализа
        max_tags (int): Максимальное количество тегов
        min_word_length (int): Минимальная длина слова для учета
        min_frequency (int): Минимальная частота встречаемости слова
    
    Returns:
        list: Список ключевых слов, отсортированных по релевантности
    """
    try:
        # Очистка и токенизация (просто разбиваем по пробелам)
        clean = clean_text(text)
        tokens = clean.split()
        
        # Фильтрация и нормализация токенов
        filtered_tokens = []
        for token in tokens:
            if (len(token) >= min_word_length and 
                token not in STOPWORDS and 
                not token.isdigit() and
                not all(c == '-' for c in token)):
                # Упрощенная нормализация
                normal_form = normalize_word(token)
                if len(normal_form) >= min_word_length:
                    filtered_tokens.append(normal_form)
        
        # Подсчет частоты слов
        word_freq = {}
        for word in filtered_tokens:
            if word in word_freq:
                word_freq[word] += 1
            else:
                word_freq[word] = 1
        
        # Сортируем по частоте (от большей к меньшей)
        sorted_words = sorted(word_freq.items(), key=lambda item: item[1], reverse=True)
        
        # Отбор наиболее частых слов
        common_words = [word for word, freq in sorted_words if freq >= min_frequency]
        
        # Если у нас мало слов, уменьшим порог частоты
        if len(common_words) < max_tags and min_frequency > 1:
            common_words = [word for word, freq in sorted_words]
        
        # Возвращаем уникальные теги
        return list(dict.fromkeys(common_words[:max_tags]))
    
    except Exception as e:
        logger.error(f"Ошибка при извлечении ключевых слов: {e}")
        return []

def extract_keyphrases(text, max_phrases=5, min_phrase_words=2, max_phrase_words=3):
    """
    Извлекает ключевые фразы из текста.
    
    Args:
        text (str): Текст для анализа
        max_phrases (int): Максимальное количество фраз
        min_phrase_words (int): Минимальное количество слов в фразе
        max_phrase_words (int): Максимальное количество слов в фразе
    
    Returns:
        list: Список ключевых фраз
    """
    try:
        # Очистка текста
        clean = clean_text(text)
        
        # Токенизация (просто разбиваем по пробелам)
        tokens = clean.split()
        
        # Создаем N-граммы (фразы из N слов)
        phrases = []
        for n in range(min_phrase_words, max_phrase_words + 1):
            for i in range(len(tokens) - n + 1):
                phrase = tokens[i:i+n]
                # Проверяем, что фраза содержит только значимые слова
                if all(len(word) >= 3 and word not in STOPWORDS for word in phrase):
                    phrases.append(' '.join(phrase))
        
        # Подсчет частоты фраз
        phrase_freq = {}
        for phrase in phrases:
            if phrase in phrase_freq:
                phrase_freq[phrase] += 1
            else:
                phrase_freq[phrase] = 1
        
        # Сортируем по частоте (от большей к меньшей)
        sorted_phrases = sorted(phrase_freq.items(), key=lambda item: item[1], reverse=True)
        
        # Берем до max_phrases фраз
        common_phrases = [phrase for phrase, freq in sorted_phrases[:max_phrases]]
        
        return common_phrases
    
    except Exception as e:
        logger.error(f"Ошибка при извлечении ключевых фраз: {e}")
        return []

def generate_tags(text, max_keywords=7, max_phrases=3):
    """
    Генерирует теги на основе текста, используя комбинацию ключевых слов и фраз.
    
    Args:
        text (str): Текст для анализа
        max_keywords (int): Максимальное количество ключевых слов
        max_phrases (int): Максимальное количество ключевых фраз
    
    Returns:
        dict: Словарь с ключевыми словами и фразами
    """
    # Извлекаем ключевые слова и фразы
    keywords = extract_keywords(text, max_tags=max_keywords)
    keyphrases = extract_keyphrases(text, max_phrases=max_phrases)
    
    # Формируем и возвращаем теги
    return {
        "keywords": keywords,
        "keyphrases": keyphrases,
        "all_tags": keywords + keyphrases
    }

# Простой тест для проверки работы модуля
if __name__ == "__main__":
    test_text = """
    Искусственный интеллект становится все более важной частью нашей жизни.
    Современные алгоритмы машинного обучения позволяют решать сложные задачи,
    которые раньше требовали участия человека. Нейронные сети успешно применяются
    в медицине, образовании и других областях. В ближайшем будущем технологии
    искусственного интеллекта будут развиваться еще быстрее.
    """
    
    tags = generate_tags(test_text)
    print("Ключевые слова:", tags["keywords"])
    print("Ключевые фразы:", tags["keyphrases"]) 