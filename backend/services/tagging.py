"""
Модуль для автоматической генерации тегов и ключевых фраз из транскрибированного текста.
"""
import os
import sys
import json
import logging
import re
from pathlib import Path
from collections import Counter

# Добавляем корневую директорию в путь импорта
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.core.logger import setup_logger

# Настройка логирования
logger = setup_logger("backend.services.tagging")

# Попытка импорта библиотек для NLP
try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem.snowball import SnowballStemmer
    from nltk.collocations import BigramAssocMeasures, BigramCollocationFinder
    
    # Проверка и загрузка необходимых ресурсов NLTK
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
    
    HAS_NLTK = True
    logger.info("NLTK успешно импортирован и настроен")
except ImportError:
    HAS_NLTK = False
    logger.warning("NLTK не установлен. Будет использован упрощенный алгоритм тегирования.")

# Попытка импорта scikit-learn для более продвинутого анализа
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
    logger.info("scikit-learn успешно импортирован")
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn не установлен. Некоторые функции тегирования будут недоступны.")


class TextAnalyzer:
    """Класс для анализа текста и извлечения ключевых слов и фраз."""
    
    def __init__(self, language='russian'):
        """
        Инициализация анализатора текста.
        
        Args:
            language (str): Язык текста для анализа
        """
        self.language = language
        
        if HAS_NLTK:
            # Настройка стеммера и стоп-слов для русского языка
            self.stemmer = SnowballStemmer(language)
            self.stop_words = set(stopwords.words(language))
            # Добавляем дополнительные стоп-слова для русского языка
            if language == 'russian':
                self.stop_words.update(['это', 'так', 'вот', 'быть', 'как', 'в', 'к', 'на'])
        else:
            # Базовый набор русских стоп-слов
            self.stop_words = {
                'и', 'в', 'на', 'с', 'по', 'для', 'не', 'что', 'это', 'так', 
                'вот', 'быть', 'как', 'а', 'но', 'от', 'к', 'у', 'же', 'за'
            }
    
    def preprocess_text(self, text):
        """
        Предобработка текста: токенизация, удаление стоп-слов и пунктуации.
        
        Args:
            text (str): Исходный текст
            
        Returns:
            list: Список обработанных токенов
        """
        if not text:
            return []
        
        # Приведение к нижнему регистру
        text = text.lower()
        
        if HAS_NLTK:
            # Токенизация с помощью NLTK
            tokens = word_tokenize(text, language=self.language)
            # Удаление пунктуации и стоп-слов
            tokens = [self.stemmer.stem(token) for token in tokens 
                     if token.isalpha() and token not in self.stop_words and len(token) > 2]
        else:
            # Простая токенизация без NLTK
            tokens = re.findall(r'\b\w+\b', text.lower())
            # Удаление стоп-слов и коротких слов
            tokens = [token for token in tokens 
                     if token not in self.stop_words and len(token) > 2]
        
        return tokens
    
    def extract_keywords(self, text, top_n=10):
        """
        Извлечение ключевых слов из текста.
        
        Args:
            text (str): Исходный текст
            top_n (int): Количество ключевых слов для извлечения
            
        Returns:
            list: Список ключевых слов
        """
        tokens = self.preprocess_text(text)
        
        if not tokens:
            return []
        
        # Подсчет частоты слов
        word_freq = Counter(tokens)
        
        # Возвращаем top_n наиболее частых слов
        return [word for word, _ in word_freq.most_common(top_n)]
    
    def extract_keyphrases(self, text, top_n=5):
        """
        Извлечение ключевых фраз из текста.
        
        Args:
            text (str): Исходный текст
            top_n (int): Количество ключевых фраз для извлечения
            
        Returns:
            list: Список ключевых фраз
        """
        if not HAS_NLTK:
            logger.warning("NLTK не установлен. Извлечение ключевых фраз недоступно.")
            return []
        
        if not text:
            return []
        
        try:
            # Токенизация текста
            tokens = word_tokenize(text.lower(), language=self.language)
            
            # Фильтрация токенов
            filtered_tokens = [token for token in tokens 
                              if token.isalpha() and token not in self.stop_words and len(token) > 2]
            
            # Если недостаточно токенов, возвращаем пустой список
            if len(filtered_tokens) < 3:
                return []
            
            # Поиск биграмм
            bigram_measures = BigramAssocMeasures()
            finder = BigramCollocationFinder.from_words(filtered_tokens)
            
            # Фильтрация редких биграмм
            finder.apply_freq_filter(2)
            
            # Получение лучших биграмм по метрике PMI
            keyphrases = finder.nbest(bigram_measures.pmi, top_n)
            
            # Преобразование биграмм в строки
            return [' '.join(phrase) for phrase in keyphrases]
        except Exception as e:
            logger.error(f"Ошибка при извлечении ключевых фраз: {e}")
            return []
    
    def categorize_text(self, text):
        """
        Определение категории текста на основе ключевых слов.
        
        Args:
            text (str): Исходный текст
            
        Returns:
            list: Список категорий
        """
        # Словарь категорий и связанных с ними ключевых слов
        categories = {
            "бизнес": ["проект", "клиент", "продажи", "маркетинг", "бюджет", "стратегия", "рынок"],
            "технический": ["код", "программа", "разработка", "система", "алгоритм", "данные", "сервер"],
            "образовательный": ["обучение", "курс", "студент", "знания", "преподаватель", "образование"],
            "личный": ["семья", "друзья", "отдых", "планы", "здоровье", "дом"]
        }
        
        # Предобработка текста
        tokens = self.preprocess_text(text)
        text_lower = text.lower()
        
        # Определение категорий
        found_categories = []
        
        for category, keywords in categories.items():
            # Проверка наличия ключевых слов в тексте
            if any(keyword in text_lower for keyword in keywords) or \
               any(keyword in tokens for keyword in keywords):
                found_categories.append(category)
        
        return found_categories or ["общий"]  # Если категория не определена, возвращаем "общий"


def generate_tags(text, note_path):
    """
    Генерация тегов для заметки на основе транскрибированного текста.
    
    Args:
        text (str): Транскрибированный текст
        note_path (str): Путь к файлу заметки
        
    Returns:
        bool: True, если теги успешно сгенерированы и сохранены, иначе False
    """
    if not text or not note_path:
        logger.error("Невозможно сгенерировать теги: отсутствует текст или путь к заметке")
        return False
    
    try:
        logger.info(f"Начало генерации тегов для заметки: {note_path}")
        
        # Создание анализатора текста
        analyzer = TextAnalyzer(language='russian')
        
        # Извлечение ключевых слов
        keywords = analyzer.extract_keywords(text, top_n=10)
        
        # Извлечение ключевых фраз
        keyphrases = analyzer.extract_keyphrases(text, top_n=5)
        
        # Определение категорий
        categories = analyzer.categorize_text(text)
        
        # Загрузка существующей заметки
        with open(note_path, 'r', encoding='utf-8') as f:
            note = json.load(f)
        
        # Обновление заметки
        note['tags'] = keywords
        note['keyphrases'] = keyphrases
        note['categories'] = categories
        
        # Сохранение обновленной заметки
        with open(note_path, 'w', encoding='utf-8') as f:
            json.dump(note, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Теги успешно сгенерированы и сохранены: {note_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при генерации тегов: {e}")
        return False


if __name__ == "__main__":
    # Пример использования
    import sys
    if len(sys.argv) > 2:
        text_path = sys.argv[1]
        note_path = sys.argv[2]
        
        # Чтение текста из файла
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Генерация тегов
        success = generate_tags(text, note_path)
        print(f"Генерация тегов: {'успешно' if success else 'ошибка'}")
    else:
        print("Необходимо указать путь к файлу с текстом и путь к заметке в качестве аргументов") 