"""
Модуль для интеллектуальной генерации тегов на основе транскрипта.
Специализирован для работы с русским языком.
"""
import re
import logging
import importlib.util
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверяем доступность необходимых модулей
# В Python 3.13 некоторые старые модули и методы могут быть удалены

# Установка совместимости для pymorphy2 с Python 3.13+
if sys.version_info >= (3, 13):
    import inspect
    if not hasattr(inspect, 'getargspec'):
        inspect.getargspec = lambda func: inspect.getfullargspec(func)[:4]

try:
    from nltk.probability import FreqDist
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ImportError:
    logger.warning("NLTK не установлен. Используем базовую функциональность.")
    NLTK_AVAILABLE = False

# Проверяем наличие pymorphy2
try:
    import pymorphy2
    PYMORPHY_AVAILABLE = True
    morph = pymorphy2.MorphAnalyzer()
except ImportError:
    logger.warning("PyMorphy2 не установлен. Используем упрощенную нормализацию слов.")
    PYMORPHY_AVAILABLE = False
except Exception as e:
    logger.error(f"Ошибка при инициализации PyMorphy2: {e}")
    PYMORPHY_AVAILABLE = False

# Проверяем наличие scikit-learn для тематического моделирования
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("Scikit-learn не установлен. Тематическое моделирование недоступно.")
    SKLEARN_AVAILABLE = False

# Расширенный список стоп-слов для русского языка
STOPWORDS = set()
if NLTK_AVAILABLE:
    try:
        STOPWORDS = set(stopwords.words('russian'))
    except:
        logger.warning("Русские стоп-слова NLTK недоступны. Используем базовый список.")

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

# Предопределенные категории и ключевые слова/фразы для них
CATEGORIES = {
    "бизнес": ["проект", "встреча", "клиент", "продажа", "маркетинг", "стратегия", "бюджет", "прибыль", 
               "компания", "бизнес", "партнер", "контракт", "сделка", "переговоры", "презентация"],
    "техническое": ["код", "программирование", "разработка", "баг", "фича", "алгоритм", "система", "технология",
                   "приложение", "сервер", "база данных", "фреймворк", "библиотека", "интеграция", "деплой"],
    "образование": ["обучение", "курс", "студент", "преподаватель", "задание", "экзамен", "лекция", "учеба",
                   "образование", "знание", "навык", "практика", "теория", "учитель", "материал"],
    "личное": ["семья", "друзья", "отпуск", "хобби", "здоровье", "дом", "отдых", "личное", "жизнь", 
               "эмоции", "настроение", "впечатление", "чувства", "отношения"],
    "планирование": ["план", "цель", "задача", "дедлайн", "расписание", "приоритет", "график", "сроки", 
                    "проектирование", "оценка", "распределение", "этапы", "последовательность"],
    "отчет": ["результат", "статус", "прогресс", "отчет", "показатель", "метрика", "анализ", "итоги", 
             "выводы", "сравнение", "измерение", "оценка результатов", "подведение итогов"]
}

# Ключевые индикаторы различных типов назначения разговора
PURPOSE_INDICATORS = {
    "брейншторм": ["идея", "придумать", "обсудить варианты", "мозговой штурм", "креативный", 
                  "давайте подумаем", "как насчет", "предложение", "вариант", "концепция"],
    "обсуждение проблемы": ["проблема", "сложность", "трудность", "решение", "исправить", "ошибка", 
                           "не работает", "сбой", "недостаток", "преодолеть", "устранить"],
    "планирование": ["план", "график", "дедлайн", "сроки", "следующий шаг", "этапы", "распределить", 
                    "запланировать", "календарь", "расписание", "дорожная карта"],
    "принятие решения": ["решение", "выбор", "решить", "определить", "согласовать", "утвердить", 
                        "остановиться на", "выбрать", "предпочтение", "окончательно"],
    "информирование": ["сообщить", "информация", "данные", "отчет", "статус", "новость", 
                      "извещение", "уведомить", "рассказать", "поделиться информацией"],
    "обучение": ["объяснить", "научить", "разобрать", "понять как", "методика", "инструкция", 
                "техника", "обучение", "тренинг", "изучение", "пример"],
    "обратная связь": ["фидбек", "обратная связь", "мнение", "оценка", "как тебе", "что думаешь", 
                      "твое мнение", "впечатление", "комментарий", "отзыв"]
}

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

def normalize_word_improved(word):
    """
    Улучшенная нормализация слова для русского языка с использованием PyMorphy2.
    
    Args:
        word (str): Слово для нормализации
        
    Returns:
        str: Нормализованная форма слова
    """
    if PYMORPHY_AVAILABLE:
        try:
            # Получаем нормальную форму слова (лемму)
            parsed = morph.parse(word)[0]
            return parsed.normal_form
        except Exception as e:
            logger.debug(f"Ошибка при нормализации с PyMorphy2: {e}")
            return normalize_word(word)
    else:
        return normalize_word(word)

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
                # Улучшенная нормализация, если доступна
                normal_form = normalize_word_improved(token)
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

def classify_conversation(text):
    """
    Классифицирует разговор по предопределенным категориям.
    
    Args:
        text (str): Текст транскрипции
        
    Returns:
        list: Список категорий разговора
    """
    # Очищаем и нормализуем текст
    clean = clean_text(text)
    
    # Определяем категории по наличию ключевых слов/фраз
    matched_categories = set()  # Используем множество для уникальности
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in clean:
                matched_categories.add(category)
                break
    
    return list(matched_categories)

def determine_conversation_purpose(text):
    """
    Определяет назначение разговора.
    
    Args:
        text (str): Текст транскрипции
        
    Returns:
        dict: Вероятность каждого назначения и основное назначение
    """
    # Очищаем текст
    clean = clean_text(text)
    
    # Ищем индикаторы назначения
    scores = {purpose: 0 for purpose in PURPOSE_INDICATORS}
    for purpose, indicators in PURPOSE_INDICATORS.items():
        for indicator in indicators:
            if indicator in clean:
                scores[purpose] += 1
    
    # Нормализуем баллы в проценты для общей суммы 100%
    total_score = sum(scores.values())
    if total_score > 0:
        percentages = {purpose: (score / total_score) * 100 for purpose, score in scores.items()}
    else:
        percentages = {purpose: 0 for purpose in PURPOSE_INDICATORS}
    
    # Определяем основное назначение
    main_purpose = "общее обсуждение"  # По умолчанию
    best_purpose, best_score = max(scores.items(), key=lambda x: x[1])
    if best_score >= 2:
        main_purpose = best_purpose
    
    # Сортируем назначения по вероятности (от большей к меньшей)
    sorted_purposes = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "main_purpose": main_purpose,
        "purpose_probabilities": percentages,
        "sorted_purposes": sorted_purposes
    }

def extract_topics_with_model(text, num_topics=3):
    """
    Извлекает темы из текста с использованием тематического моделирования.
    
    Args:
        text (str): Текст транскрипции
        num_topics (int): Количество тем для извлечения
        
    Returns:
        list: Список тем разговора
    """
    if not SKLEARN_AVAILABLE or len(text) < 200:  # Требуется минимальный объем текста
        return []
    
    try:
        # Очистка текста
        clean = clean_text(text)
        
        # Конвертируем множество стоп-слов в список для совместимости с новыми версиями scikit-learn
        stopwords_list = list(STOPWORDS) if STOPWORDS else None
        
        # Векторизация текста
        vectorizer = TfidfVectorizer(max_features=1000, 
                                     stop_words=stopwords_list)
        X = vectorizer.fit_transform([clean])
        
        # Проверка, достаточно ли у нас слов для моделирования
        if X.shape[1] < 10:
            return []
        
        # Тематическое моделирование
        n_components = min(num_topics, X.shape[1] // 3)  # Не больше 1/3 от числа признаков
        if n_components == 0:
            return []
        
        lda = LatentDirichletAllocation(n_components=n_components, random_state=42)
        lda.fit(X)
        
        # Получение ключевых слов для каждой темы
        feature_names = vectorizer.get_feature_names_out()
        topics = []
        for topic_idx, topic in enumerate(lda.components_):
            top_words = [feature_names[i] for i in topic.argsort()[:-5-1:-1]]
            topics.append(" ".join(top_words))
        
        return topics
    
    except Exception as e:
        logger.error(f"Ошибка при извлечении тем с помощью модели: {e}")
        return []

def generate_tags(text, max_keywords=7, max_phrases=3, classify=True):
    """
    Генерирует теги на основе текста, используя комбинацию ключевых слов, фраз и классификации.
    
    Args:
        text (str): Текст для анализа
        max_keywords (int): Максимальное количество ключевых слов
        max_phrases (int): Максимальное количество ключевых фраз
        classify (bool): Выполнять ли классификацию разговора
    
    Returns:
        dict: Словарь с ключевыми словами, фразами, категориями и темами
    """
    # Проверяем, что у нас есть текст для анализа
    if not text or len(text.strip()) < 10:
        return {
            "keywords": [],
            "keyphrases": [],
            "categories": [],
            "topics": [],
            "purpose": "неизвестно",
            "purpose_details": {},
            "all_tags": []
        }
    
    # Извлекаем ключевые слова и фразы
    keywords = extract_keywords(text, max_tags=max_keywords)
    keyphrases = extract_keyphrases(text, max_phrases=max_phrases)
    
    # Классифицируем разговор, если нужно
    categories = []
    topics = []
    purpose_info = {"main_purpose": "общее обсуждение", "purpose_probabilities": {}}
    
    if classify and len(text) > 100:  # Проверяем, что есть достаточно текста для анализа
        categories = classify_conversation(text)
        topics = extract_topics_with_model(text)
        purpose_info = determine_conversation_purpose(text)
    
    # Формируем и возвращаем теги с дополнительной информацией
    return {
        "keywords": keywords,
        "keyphrases": keyphrases,
        "categories": categories,
        "topics": topics,
        "purpose": purpose_info["main_purpose"],
        "purpose_details": purpose_info,
        "all_tags": keywords + keyphrases + categories
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
    print("Категории:", tags["categories"])
    print("Темы:", tags["topics"])
    print("Назначение:", tags["purpose"]) 