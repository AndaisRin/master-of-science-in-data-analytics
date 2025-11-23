import sys
import os
import time

# Добавляем текущую директорию в путь (если нужно)
sys.path.append(os.getcwd())

# Правильный импорт функции из модуля
from predict_script import predict_topics_and_clusters


def main():
    """Тестирование функции предсказания"""

    # Путь к входному файлу
    input_file = "input.csv"
    output_file = "output_predictions.csv"

    try:
        print("Начинаем предсказание...")
        start_time = time.time()
        # Вызываем функцию предсказания
        df_with_predictions = predict_topics_and_clusters(
            csv_file_path=input_file,
            output_file_path=output_file
        )
        finish_time = time.time()
        print(f"\n==== Время предсказания модели {finish_time - start_time} сек. ====")
        print("\n=== РЕЗУЛЬТАТЫ ПРЕДСКАЗАНИЯ ===")
        print(f"Обработано записей: {len(df_with_predictions)}")

        # Показываем первые несколько строк
        print("\n=== ПЕРВЫЕ 5 СТРОК ===")
        columns_to_show = ['group_name', 'predicted_topic', 'predicted_cluster']
        if 'topic_confidence' in df_with_predictions.columns:
            columns_to_show.append('topic_confidence')

        print(df_with_predictions[columns_to_show].head())

        # Статистика по кластерам
        print("\n=== РАСПРЕДЕЛЕНИЕ ПО КЛАСТЕРАМ ===")
        cluster_stats = df_with_predictions['predicted_cluster'].value_counts()
        for cluster, count in cluster_stats.items():
            percentage = (count / len(df_with_predictions)) * 100
            print(f"{cluster}: {count} ({percentage:.1f}%)")

        print(f"\nРезультаты сохранены в: {output_file}")

    except FileNotFoundError as e:
        print(f"Ошибка: файл не найден - {e}")
        print("Убедитесь, что:")
        print("1. Файл input_data.csv существует")
        print("2. Папка artefacts/ содержит модель roberta_ru_logreg_tuned.pkl")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
