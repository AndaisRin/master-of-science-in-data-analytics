import re
import pandas as pd
import numpy as np
import joblib
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import StandardScaler
from typing import Any
import logging
import warnings

warnings.filterwarnings("ignore")

# ══════════════════════════ КОНСТАНТЫ И КОНФИГУРАЦИЯ ════════════════════════════
BATCH_SIZE = 16
ARTEFACTS_DIR = Path("artefacts")
MODEL_NAME = "ai-forever/ru-en-RoSBERTa"  # roberta_ru из оригинального кода

# Маппинг тематик в кластеры (из оригинального кода)
TOPIC_CLUSTER_MAP = {
    **{k: "Математика и естественные науки" for k in
       ["механика", "искусственный интеллект", "программирование", "популярная наука", "космос", "окружающий мир"]},
    **{k: "Инженерное дело и технологии" for k in [
        "технологии", "авиастроение", "электроника", "инженерные системы", "техника и авто", "игры и геймдев",
        "робототехника"]},
    **{k: "Медицина и здоровье" for k in [
        "здоровье", "уход за собой", "психология", "медицинские советы", "медицина", "альтернативная медицина",
        "тело и физиология", "фитнес и питание", "спорт"]},
    **{k: "Сельское хозяйство" for k in [
        "фермерство и агрономия", "животные и птицы", "растения", "охота и рыбалка", "сельская жизнь", "экология"]},
    **{k: "Социальные науки" for k in [
        "экономика", "предпринимательство", "политика и СМИ", "юриспруденция", "урбанистика", "социология",
        "государственная служба", "управление", "благотворительность"]},
    **{k: "Образование и педагогика" for k in [
        "школьные предметы", "педагогика", "подготовка к экзаменам", "онлайн-курсы", "репетиторство",
        "образовательные платформы", "самообразование", "методика преподавания", "образовательная организация"]},
    **{k: "Гуманитарные науки" for k in [
        "история", "философия", "археология", "лингвистика", "религиоведение", "культурология", "литература"]},
    **{k: "Искусство и культура" for k in [
        "музыка", "театр и кино", "фото и дизайн", "фильмы и сериалы", "мода и стиль", "визуальное искусство",
        "народное творчество", "живопись", "культура и общество"]},
    **{k: "Общие интересы" for k in [
        "знакомства", "лайфстайл", "мемы", "хобби и увлечения", "развлекательный контент", "мотивация",
        "цитаты и мысли", "общение", "отношения", "путешествия", "кулинария и еда", "бизнес-страница"]},
}

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def clean_text(txt: Any) -> str:
    """Очистка текста"""
    if txt is None or (isinstance(txt, float) and pd.isna(txt)):
        return ""
    txt = re.sub(r"[^а-яё ]", " ", str(txt).lower())
    return " ".join(txt.split())


def map_to_cluster(labels):
    """Маппинг тематик в кластеры"""
    return [TOPIC_CLUSTER_MAP.get(label, "Unknown") for label in labels]


def load_embedding_model(model_name: str):
    """Загрузка модели эмбеддингов"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Загружаем модель эмбеддингов: {model_name} на устройстве: {device}")
    model = SentenceTransformer(model_name, device=device)
    return model


def get_embeddings(model, texts, batch_size=BATCH_SIZE):
    """Получение эмбеддингов для текстов"""
    logger.info(f"Получаем эмбеддинги для {len(texts)} текстов")
    return model.encode(list(texts), batch_size=batch_size, show_progress_bar=True)


def predict_topics_and_clusters(csv_file_path: str, output_file_path: str = None):
    """
    Основная функция предсказания тематик и кластеров

    Args:
        csv_file_path: путь к CSV файлу с данными
        output_file_path: путь для сохранения результата (опционально)

    Returns:
        pd.DataFrame: датафрейм с предсказаниями
    """

    # Проверяем наличие необходимых файлов
    model_path = ARTEFACTS_DIR / "roberta_ru_logreg_tuned.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Модель не найдена: {model_path}")

    # Загружаем данные
    logger.info(f"Загружаем данные из: {csv_file_path}")
    df = pd.read_csv(csv_file_path, sep=';')

    # Проверяем наличие необходимых столбцов
    required_columns = ['group_name', 'category', 'description']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.warning(f"Отсутствуют столбцы: {missing_columns}. Заполняем пустыми строками.")
        for col in missing_columns:
            df[col] = ""

    # Подготавливаем текст для предсказания (аналогично обучению)
    logger.info("Подготавливаем тексты...")
    df['text'] = (df['group_name'].fillna('').apply(clean_text) + " " +
                  df['category'].fillna('').apply(clean_text) + " " +
                  df['description'].fillna('').apply(clean_text))

    # Фильтруем пустые тексты
    df = df[df['text'].str.strip() != ''].reset_index(drop=True)

    if len(df) == 0:
        logger.error("Нет данных для предсказания после очистки")
        return df

    # Загружаем модель эмбеддингов
    embedding_model = load_embedding_model(MODEL_NAME)

    # Получаем эмбеддинги
    embeddings = get_embeddings(embedding_model, df['text'])

    # Масштабируем эмбеддинги (важно для модели)
    scaler = StandardScaler()
    embeddings_scaled = scaler.fit_transform(embeddings)

    # Загружаем обученную модель
    logger.info("Загружаем обученную модель классификации...")
    classifier = joblib.load(model_path)

    # Делаем предсказания
    logger.info("Делаем предсказания...")
    predicted_topics = classifier.predict(embeddings_scaled)

    # Получаем вероятности предсказаний (если модель поддерживает)
    try:
        prediction_probas = classifier.predict_proba(embeddings_scaled)
        max_probas = np.max(prediction_probas, axis=1)
        df['topic_confidence'] = max_probas
    except AttributeError:
        logger.warning("Модель не поддерживает predict_proba, пропускаем вероятности")
        df['topic_confidence'] = None

    # Добавляем предсказания в датафрейм
    df['predicted_topic'] = predicted_topics
    df['predicted_cluster'] = map_to_cluster(predicted_topics)

    # Удаляем служебный столбец
    df = df.drop('text', axis=1)

    # Сохраняем результат, если указан путь
    if output_file_path:
        logger.info(f"Сохраняем результаты в: {output_file_path}")
        df.to_csv(output_file_path, sep=';', index=False, encoding='utf-8')

    # Выводим статистику
    logger.info("\n=== СТАТИСТИКА ПРЕДСКАЗАНИЙ ===")
    logger.info(f"Всего обработано записей: {len(df)}")
    logger.info(f"\nРаспределение по кластерам:")
    cluster_counts = df['predicted_cluster'].value_counts()
    for cluster, count in cluster_counts.items():
        logger.info(f"  {cluster}: {count} ({count / len(df) * 100:.1f}%)")

    logger.info(f"\nТоп-10 тематик:")
    topic_counts = df['predicted_topic'].value_counts().head(10)
    for topic, count in topic_counts.items():
        logger.info(f"  {topic}: {count}")

    if 'topic_confidence' in df.columns and df['topic_confidence'].notna().any():
        avg_confidence = df['topic_confidence'].mean()
        logger.info(f"\nСредняя уверенность модели: {avg_confidence:.3f}")

    logger.info("Предсказание завершено!")

    return df


def main():
    """Пример использования"""
    import argparse

    parser = argparse.ArgumentParser(description="Предсказание тематик и кластеров для групп ВК")
    parser.add_argument("input_file", help="Путь к входному CSV файлу")
    parser.add_argument("-o", "--output", help="Путь к выходному CSV файлу")

    args = parser.parse_args()

    try:
        result_df = predict_topics_and_clusters(
            csv_file_path=args.input_file,
            output_file_path=args.output
        )

        if args.output is None:
            print("\n=== ПЕРВЫЕ 5 СТРОК РЕЗУЛЬТАТА ===")
            print(result_df[['group_name', 'predicted_topic', 'predicted_cluster']].head())

    except Exception as e:
        logger.error(f"Ошибка выполнения: {e}")
        raise


if __name__ == "__main__":
    main()