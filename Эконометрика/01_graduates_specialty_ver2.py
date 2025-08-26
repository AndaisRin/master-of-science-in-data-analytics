# requirements:
# geopandas, pandas, numpy, matplotlib, statsmodels, shapely, linearmodels, scipy

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from statsmodels.iolib.summary2 import summary_col
from scipy.stats import shapiro, skew, kurtosis
import geopandas as gpd
from shapely.ops import transform
from functools import partial
import warnings
import logging

# --- Логгирование ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
os.makedirs("figures", exist_ok=True)  # Папка для графиков
prefix = 'figures/'
# Для записи лога в файл (раскомментировать если нужно)
# fh = logging.FileHandler('figures/script.log', encoding='utf-8')
# fh.setLevel(logging.INFO)
# fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
# logger.addHandler(fh)

# --- PanelOLS ---
try:
    from linearmodels import PanelOLS

    PANEL_AVAILABLE = True
    logger.info("linearmodels.PanelOLS доступен.")
except ImportError:
    logger.warning("linearmodels не установлена. Будет использован OLS с фиктивными переменными.")
    PANEL_AVAILABLE = False

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def load_data():
    logger.info("Загрузка данных...")
    specialty = pd.read_csv('data_graduates_specialty_125_v20250127.csv', sep=';', encoding='utf-8')
    area = pd.read_csv('data_graduates_study_area_125_v20250127.csv', sep=';', encoding='utf-8')
    reg_inf = pd.read_csv('geo_1.csv', encoding='utf-8')
    rus_info_df = pd.read_csv('regions-info.csv', encoding='utf-8')
    rus_bnd_gdf = gpd.read_file('geo.json')
    logger.info("Данные успешно загружены.")
    return specialty, area, reg_inf, rus_info_df, rus_bnd_gdf


def preprocess(specialty_df):
    logger.info("Предобработка данных...")
    df = specialty_df.query("object_level == 'Регион' and gender in ['Мужской','Женский']")
    df = df[df['specialty_section'] != 'Оборона и безопасность'].copy()
    df['HigherEdu'] = df['education_level'].isin(['Бакалавриат, специалитет', 'Магистратура']).astype(int)
    df['Female'] = (df['gender'] == 'Женский').astype(int)
    df['year'] = df['year'].astype(int)
    df['Female_HigherEdu'] = df['Female'] * df['HigherEdu']

    df_sal = df.dropna(subset=['average_salary']).copy()
    df_sal['ln_salary'] = np.log(df_sal['average_salary'])
    df_sal['Female_HigherEdu'] = df_sal['Female'] * df_sal['HigherEdu']

    logger.info("Предобработка завершена.")
    return df, df_sal


def descriptive_stats(df, df_sal):
    logger.info("Сохраняю описательную статистику...")
    stats = {
        "percent_employed": df['percent_employed'].describe(),
        "average_salary": df_sal['average_salary'].describe(),
        "ln_salary": df_sal['ln_salary'].describe()
    }
    with open("figures/descriptive_stats.txt", "w", encoding="utf-8") as f:
        for key, val in stats.items():
            f.write(f"{key}:\n{val}\n\n")
        f.write("=== Структура панельных данных ===\n")
        f.write(f"Количество регионов: {df['object_name'].nunique()}\n")
        f.write(f"Количество лет: {df['year'].nunique()}\n")
        f.write(f"Период наблюдений: {df['year'].min()}-{df['year'].max()}\n")
        f.write(f"Общее количество наблюдений: {len(df)}\n")
        f.write(f"Наблюдений с данными о зарплате: {len(df_sal)}\n")
    logger.info("Описательная статистика сохранена в figures/descriptive_stats.txt")


def plot_bar(df_grouped, title, ylabel, legend_titles, filename, figsize=(10, 6), rotate=45):
    fig, ax = plt.subplots(figsize=figsize)
    df_grouped.plot(kind='bar', ax=ax)
    ax.set_title(title)
    ax.set_xlabel('')
    ax.set_ylabel(ylabel)
    ax.legend(legend_titles, title='Уровень образования')
    plt.xticks(rotation=rotate, ha='right')
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def plot_basic(df, df_sal, prefix=prefix):
    # Средняя зарплата по укрупненным направлениям и уровню образования
    sal_by_area = df_sal.groupby(['study_area', 'HigherEdu'])['average_salary'].mean().unstack()
    plot_bar(sal_by_area, 'Средняя зарплата по укрупнённым направлениям и уровню образования',
             'Средняя зарплата, руб.', ['СПО', 'Высшее образование'],
             'figures/salary_by_area.png')
    sal_by_section = df_sal.groupby(['specialty_section', 'HigherEdu'])['average_salary'].mean().unstack()
    plot_bar(sal_by_section, 'Средняя зарплата по направлениям и уровню образования',
             'Средняя зарплата, руб.', ['СПО', 'Высшее образование'],
             'figures/salary_by_section.png', figsize=(12, 10), rotate=90)
    emp_by_area = df.groupby(['study_area', 'HigherEdu'])['percent_employed'].mean().unstack()
    plot_bar(emp_by_area, 'Доля трудоустроенных по укрупнённым направлениям',
             'Доля трудоустроенных, %', ['СПО', 'Высшее образование'],
             'figures/employed_by_area.png')
    emp_by_section = df.groupby(['specialty_section', 'HigherEdu'])['percent_employed'].mean().unstack()
    plot_bar(emp_by_section, 'Доля трудоустроенных по направлениям',
             'Доля трудоустроенных, %', ['СПО', 'Высшее образование'],
             'figures/employed_by_section.png', figsize=(12, 10), rotate=90)
    # Национальные столбцы по полу
    national_salary = df.groupby('gender')['average_salary'].mean()
    national_salary.plot(kind='bar', figsize=(6, 4))
    plt.title('Средняя зарплата по полу')
    plt.ylabel('Средняя зарплата, руб.')
    plt.xlabel('')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(prefix + 'salary_by_gender.png')
    plt.close()
    national_employ = df.groupby('gender')['percent_employed'].mean()
    national_employ.plot(kind='bar', figsize=(6, 4))
    plt.title('Доля трудоустроенных по полу')
    plt.ylabel('Доля трудоустроенных, %')
    plt.xlabel('')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(prefix + 'employed_by_gender.png')
    plt.close()
    # Тренд по годам и полу
    yearly_trend = df.groupby(['year', 'gender'])['average_salary'].mean().unstack()
    yearly_trend.plot(marker='o', figsize=(8, 5))
    plt.title('Динамика средней зарплаты по полу')
    plt.ylabel('Средняя зарплата, руб.')
    plt.xlabel('Год выпуска')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(prefix + 'salary_trend_gender.png')
    plt.close()


def prepare_gdf(df, reg_inf, rus_info_df, rus_bnd_gdf):
    """Объединение данных и обтекание по долготе."""
    # Средние по региону
    agg_all = df.groupby('object_name', as_index=False).agg(
        percent_employed=('percent_employed', 'mean'),
        average_salary=('average_salary', 'mean')
    )
    agg_m = df.query("gender=='Мужской'").groupby('object_name', as_index=False).agg(
        male_salary=('average_salary', 'mean'))
    agg_f = df.query("gender=='Женский'").groupby('object_name', as_index=False).agg(
        female_salary=('average_salary', 'mean'))

    gdf = (
        rus_bnd_gdf
        .merge(reg_inf, on='region_code', how='left')
        .merge(agg_all, on='object_name', how='left')
        .merge(agg_m, on='object_name', how='left')
        .merge(agg_f, on='object_name', how='left')
    )

    def wrap_lng(x, y, z=None):
        return (x + 360, y) if x < 0 else (x, y)

    wrap_fn = partial(transform, wrap_lng)
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: wrap_fn(geom))
    return gdf


def plot_maps(gdf, prefix=prefix):
    """Построение четырех хлороплетных карт."""
    bounds = gdf.total_bounds
    # Убираем 'ax' из kw — теперь только legend и missing_kwds
    kw = dict(
        legend=True,
        missing_kwds={'color': 'lightgrey', 'label': 'Нет данных'}
    )

    for col, cmap, title in [
        ('percent_employed', 'OrRd', 'Доля трудоустроенных выпускников (%)'),
        ('average_salary', 'YlGn', 'Средняя зарплата выпускников (руб.)'),
        ('male_salary', 'PuBu', 'Средняя зарплата мужчин (руб.)'),
        ('female_salary', 'RdPu', 'Средняя зарплата женщин (руб.)'),
    ]:
        fig, ax = plt.subplots(figsize=(16, 8))
        # Передаём ax явно, а остальные параметры через **kw
        gdf.plot(
            column=col,
            cmap=cmap,
            ax=ax,
            **kw
        )
        ax.set_title(title)
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])
        ax.axis('off')
        plt.tight_layout()
        # plt.show()
        plt.savefig(prefix + col + '.png')
        plt.close(fig)
    logger.info("Графики хлороплетных карт сохранены.")


def panel_regression_analysis(df, df_sal):
    logger.info("Построение панельных моделей...")
    if PANEL_AVAILABLE:
        df_panel = df.dropna(subset=['percent_employed']).copy().set_index(['object_name', 'year'])
        df_sal_panel = df_sal.copy().set_index(['object_name', 'year'])

        model_emp = PanelOLS(df_panel['percent_employed'], df_panel[['Female', 'HigherEdu', 'Female_HigherEdu']],
                             entity_effects=True, time_effects=True)
        result_emp = model_emp.fit(cov_type='clustered', cluster_entity=True)

        model_sal = PanelOLS(df_sal_panel['ln_salary'], df_sal_panel[['Female', 'HigherEdu', 'Female_HigherEdu']],
                             entity_effects=True, time_effects=True)
        result_sal = model_sal.fit(cov_type='clustered', cluster_entity=True)

        with open("figures/panel_regression_summary.txt", "w", encoding="utf-8") as f:
            f.write("=== Модель доли трудоустройства ===\n")
            f.write(str(result_emp.summary))
            f.write("\n\n=== Модель логарифма зарплаты ===\n")
            f.write(str(result_sal.summary))
        logger.info("Модели PanelOLS успешно обучены. Summary сохранён в figures/panel_regression_summary.txt.")
        return result_emp, result_sal
    else:
        logger.warning("linearmodels не установлена. Используйте OLS!")
        # Здесь добавьте свой код OLS при необходимости
        return None, None


def interpret_results(result_emp, result_sal):
    logger.info("Выполняется интерпретация результатов регрессии...")
    filename = "figures/regression_interpretation.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("ДЕТАЛИЗИРОВАННАЯ ИНТЕРПРЕТАЦИЯ РЕГРЕССИОННЫХ МОДЕЛЕЙ\n")
        f.write("=" * 80 + "\n\n")

        # ----------- Доля трудоустроенных
        f.write("Модель 1. Доля трудоустроенных выпускников\n")
        f.write("Параметры модели (оценки, 95% доверительный интервал, p-value):\n")
        for var in ['Female', 'HigherEdu', 'Female_HigherEdu']:
            if var in result_emp.params.index:
                coef = result_emp.params[var]
                conf = result_emp.conf_int().loc[var]
                pval = result_emp.pvalues[var]
                significance = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
                f.write(
                    f"  {var:<16}: {coef:8.4f} [{conf[0]:.4f}; {conf[1]:.4f}], p={pval:.4f} {significance}\n"
                )
                if var == 'Female':
                    f.write("      → Женский пол (относительно мужского)\n")
                elif var == 'HigherEdu':
                    f.write("      → Высшее образование (относительно СПО)\n")
                elif var == 'Female_HigherEdu':
                    f.write("      → Взаимодействие: дополнительный эффект высшего образования для женщин\n")
        f.write("\n")
        f.write(f"R² (within): {getattr(result_emp, 'rsquared_within', result_emp.rsquared):.4f}\n")
        f.write(f"R² (between): {getattr(result_emp, 'rsquared_between', float('nan')):.4f}\n")
        f.write(f"R² (overall): {getattr(result_emp, 'rsquared_overall', float('nan')):.4f}\n")
        f.write(f"Общее число наблюдений: {result_emp.nobs}\n\n")

        # ----------- Анализ остатков (занятость)
        res_emp = result_emp.resids.dropna()
        mean_emp = np.mean(res_emp)
        std_emp = np.std(res_emp)
        skew_emp = skew(res_emp)
        kurt_emp = kurtosis(res_emp)
        stat_emp, p_emp = shapiro(res_emp.sample(min(5000, len(res_emp)), random_state=1))
        f.write("Анализ остатков (занятость):\n")
        f.write(f"  Среднее: {mean_emp:.4f}\n")
        f.write(f"  Ст. отклонение: {std_emp:.4f}\n")
        f.write(f"  Коэффициент асимметрии: {skew_emp:.4f}\n")
        f.write(f"  Эксцесс: {kurt_emp:.4f}\n")
        f.write(f"  Тест Шапиро-Уилка (W={stat_emp:.4f}, p={p_emp:.4g})\n")
        f.write("  " + (
            "Остатки близки к нормальному распределению.\n" if p_emp > 0.05 else "Остатки не нормальны (p < 0.05).\n"))
        f.write("\n")

        # ----------- Логарифм зарплаты
        f.write("Модель 2. Логарифм заработной платы выпускников\n")
        f.write("Параметры модели (оценки, 95% доверительный интервал, p-value, % изменение):\n")
        for var in ['Female', 'HigherEdu', 'Female_HigherEdu']:
            if var in result_sal.params.index:
                coef = result_sal.params[var]
                conf = result_sal.conf_int().loc[var]
                pval = result_sal.pvalues[var]
                significance = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
                percent_change = (np.exp(coef) - 1) * 100
                ci_lower = (np.exp(conf[0]) - 1) * 100
                ci_upper = (np.exp(conf[1]) - 1) * 100
                f.write(
                    f"  {var:<16}: {coef:8.4f} [{conf[0]:.4f}; {conf[1]:.4f}], "
                    f"p={pval:.4f} {significance}, Δ% = {percent_change:.2f}% [{ci_lower:.2f}%; {ci_upper:.2f}%]\n"
                )
                if var == 'Female':
                    f.write("      → Женский пол: относительное отличие зарплаты женщин от мужчин.\n")
                elif var == 'HigherEdu':
                    f.write("      → Высшее образование: отличие зарплаты выпускников вуза от СПО.\n")
                elif var == 'Female_HigherEdu':
                    f.write("      → Доп. эффект высшего образования для женщин.\n")
        f.write("\n")
        f.write(f"R² (within): {getattr(result_sal, 'rsquared_within', result_sal.rsquared):.4f}\n")
        f.write(f"R² (between): {getattr(result_sal, 'rsquared_between', float('nan')):.4f}\n")
        f.write(f"R² (overall): {getattr(result_sal, 'rsquared_overall', float('nan')):.4f}\n")
        f.write(f"Общее число наблюдений: {result_sal.nobs}\n\n")

        # ----------- Анализ остатков (зарплата)
        res_sal = result_sal.resids.dropna()
        mean_sal = np.mean(res_sal)
        std_sal = np.std(res_sal)
        skew_sal = skew(res_sal)
        kurt_sal = kurtosis(res_sal)
        stat_sal, p_sal = shapiro(res_sal.sample(min(5000, len(res_sal)), random_state=1))
        f.write("Анализ остатков (логарифм зарплаты):\n")
        f.write(f"  Среднее: {mean_sal:.4f}\n")
        f.write(f"  Ст. отклонение: {std_sal:.4f}\n")
        f.write(f"  Коэффициент асимметрии: {skew_sal:.4f}\n")
        f.write(f"  Эксцесс: {kurt_sal:.4f}\n")
        f.write(f"  Тест Шапиро-Уилка (W={stat_sal:.4f}, p={p_sal:.4g})\n")
        f.write("  " + (
            "Остатки близки к нормальному распределению.\n" if p_sal > 0.05 else "Остатки не нормальны (p < 0.05).\n"))
        f.write("\n")

        f.write("Экономический смысл коэффициентов:\n")
        f.write("- Female: эффект женского пола относительно мужского\n")
        f.write("- HigherEdu: эффект высшего образования относительно СПО\n")
        f.write("- Female_HigherEdu: дополнительный эффект высшего образования для женщин\n\n")
        f.write("Значимость: *** p<0.01, ** p<0.05, * p<0.1\n")
        f.write("Модель контролирует фиксированные эффекты регионов и лет (двунаправленная панель).\n")
        f.write(
            "Это позволяет корректно выделить влияние пола и образования, устранив пространственно-временные искажения.\n")
    logger.info("Интерпретация результатов сохранена в figures/regression_interpretation.txt")


def save_panel_regression_plots(result_emp, result_sal, prefix=prefix):
    logger.info("Сохраняю графики коэффициентов и остатков PanelOLS...")
    fig, ax = plt.subplots(figsize=(6, 4))
    result_emp.params.plot(kind='bar', yerr=result_emp.std_errors, color='skyblue', ax=ax)
    ax.set_title('Коэффициенты (занятость, PanelOLS)')
    ax.set_ylabel('Оценка коэффициента')
    ax.set_xlabel('')
    plt.tight_layout()
    plt.savefig(prefix + 'panel_emp_coeffs.png')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    result_emp.resids.plot.hist(bins=30, color='coral', ax=ax)
    ax.set_title('Гистограмма остатков (занятость, PanelOLS)')
    ax.set_xlabel('Остатки')
    plt.tight_layout()
    plt.savefig(prefix + 'panel_emp_residuals.png')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    result_sal.params.plot(kind='bar', yerr=result_sal.std_errors, color='lightgreen', ax=ax)
    ax.set_title('Коэффициенты (логарифм зарплаты, PanelOLS)')
    ax.set_ylabel('Оценка коэффициента')
    ax.set_xlabel('')
    plt.tight_layout()
    plt.savefig(prefix + 'panel_sal_coeffs.png')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    result_sal.resids.plot.hist(bins=30, color='orchid', ax=ax)
    ax.set_title('Гистограмма остатков (логарифм зарплаты, PanelOLS)')
    ax.set_xlabel('Остатки')
    plt.tight_layout()
    plt.savefig(prefix + 'panel_sal_residuals.png')
    plt.close(fig)
    logger.info("Графики PanelOLS сохранены.")


def save_ols_regression_plots(result_emp, result_sal, prefix=prefix):
    import statsmodels.api as sm
    logger.info("Сохраняю графики коэффициентов, остатков и Q-Q plots OLS...")
    fig, ax = plt.subplots(figsize=(6, 4))
    result_emp.params.plot(kind='bar', yerr=result_emp.bse, color='skyblue', ax=ax)
    ax.set_title('Коэффициенты (занятость, OLS)')
    ax.set_ylabel('Оценка коэффициента')
    ax.set_xlabel('')
    plt.tight_layout()
    plt.savefig(prefix + 'ols_emp_coeffs.png')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    pd.Series(result_emp.resid).plot.hist(bins=30, color='coral', ax=ax)
    ax.set_title('Гистограмма остатков (занятость, OLS)')
    ax.set_xlabel('Остатки')
    plt.tight_layout()
    plt.savefig(prefix + 'ols_emp_residuals.png')
    plt.close(fig)

    fig = plt.figure(figsize=(6, 4))
    sm.qqplot(result_emp.resid, line='s', ax=plt.gca())
    plt.title('Q-Q plot остатков (занятость, OLS)')
    plt.tight_layout()
    plt.savefig(prefix + 'ols_emp_qqplot.png')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    result_sal.params.plot(kind='bar', yerr=result_sal.bse, color='lightgreen', ax=ax)
    ax.set_title('Коэффициенты (логарифм зарплаты, OLS)')
    ax.set_ylabel('Оценка коэффициента')
    ax.set_xlabel('')
    plt.tight_layout()
    plt.savefig(prefix + 'ols_sal_coeffs.png')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    pd.Series(result_sal.resid).plot.hist(bins=30, color='orchid', ax=ax)
    ax.set_title('Гистограмма остатков (логарифм зарплаты, OLS)')
    ax.set_xlabel('Остатки')
    plt.tight_layout()
    plt.savefig(prefix + 'ols_sal_residuals.png')
    plt.close(fig)

    fig = plt.figure(figsize=(6, 4))
    sm.qqplot(result_sal.resid, line='s', ax=plt.gca())
    plt.title('Q-Q plot остатков (логарифм зарплаты, OLS)')
    plt.tight_layout()
    plt.savefig(prefix + 'ols_sal_qqplot.png')
    plt.close(fig)
    logger.info("Графики OLS сохранены.")


def main():
    logger.info("=== АНАЛИЗ ДАННЫХ О ВЫПУСКНИКАХ С ПАНЕЛЬНОЙ РЕГРЕССИЕЙ ===")
    specialty, area, reg_inf, rus_info_df, rus_bnd_gdf = load_data()
    df, df_sal = preprocess(specialty)
    descriptive_stats(df, df_sal)
    plot_basic(df, df_sal)
    gdf = prepare_gdf(df, reg_inf, rus_info_df, rus_bnd_gdf)
    plot_maps(gdf)
    result_emp, result_sal = panel_regression_analysis(df, df_sal)
    interpret_results(result_emp, result_sal)
    if PANEL_AVAILABLE and result_emp is not None and result_sal is not None:
        save_panel_regression_plots(result_emp, result_sal)
    # Если используется OLS:
    if not PANEL_AVAILABLE and result_emp is not None and result_sal is not None:
        save_ols_regression_plots(result_emp, result_sal)

    logger.info("Анализ завершен! Графики и результаты сохранены в папке figures.")


if __name__ == '__main__':
    main()
