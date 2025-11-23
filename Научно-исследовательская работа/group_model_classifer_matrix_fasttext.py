import pandas as pd
import time, re, nltk, numpy as np, logging
import matplotlib.pyplot as plt
import seaborn as sns

from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split

from sentence_transformers import SentenceTransformer

import fasttext

# Logger
logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Препроцессинг
nltk.download('stopwords')
stop_words = set(stopwords.words('russian'))
stemmer = SnowballStemmer("russian")

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[\W\d_]+', ' ', text)
    tokens = text.split()
    return ' '.join(stemmer.stem(w) for w in tokens if w not in stop_words)


# === Кластеризация тематик ===
logger.info('Определяем кластеры тематик...')

topic_cluster_map = {
    **{k: 'Математика и естественные науки' for k in [
        'популярная наука', 'космос', 'окружающий мир'
    ]},
    **{k: 'Инженерное дело и технологии' for k in [
        'технологии', 'искусственный интеллект', 'авиастроение', 'электроника',
        'инженерные системы', 'программирование', 'техника и авто', 'игры и геймдев',
        'механика', 'робототехника'
    ]},
    **{k: 'Медицина и здоровье' for k in [
        'здоровье', 'уход за собой', 'психология', 'медицинские советы',
        'медицина', 'альтернативная медицина', 'тело и физиология',
        'фитнес и питание', 'спорт'
    ]},
    **{k: 'Сельское хозяйство' for k in [
        'фермерство и агрономия', 'животные и птицы', 'растения',
        'охота и рыбалка', 'сельская жизнь', 'экология'
    ]},
    **{k: 'Социальные науки' for k in [
        'экономика', 'предпринимательство', 'политика и СМИ', 'юриспруденция',
        'урбанистика', 'социология', 'государственная служба',
        'управление', 'благотворительность'
    ]},
    **{k: 'Образование и педагогика' for k in [
        'школьные предметы', 'педагогика', 'подготовка к экзаменам',
        'онлайн-курсы', 'репетиторство', 'образовательные платформы',
        'самообразование', 'методика преподавания', 'образовательная организация'
    ]},
    **{k: 'Гуманитарные науки' for k in [
        'история', 'философия', 'археология', 'лингвистика',
        'религиоведение', 'культурология', 'литература'
    ]},
    **{k: 'Искусство и культура' for k in [
        'музыка', 'театр и кино', 'фото и дизайн', 'фильмы и сериалы',
        'мода и стиль', 'визуальное искусство', 'народное творчество',
        'живопись', 'культура и общество'
    ]},
    **{k: 'Общие интересы' for k in [
        'знакомства', 'лайфстайл', 'мемы', 'хобби и увлечения',
        'развлекательный контент', 'мотивация', 'цитаты и мысли',
        'общение', 'отношения', 'путешествия', 'кулинария и еда',
        'бизнес-страница'
    ]}
}


# Загрузка
df = pd.read_excel('part_123_.xlsx', engine='openpyxl').dropna(subset=['description', 'group_name', 'Тематика'])
df['Кластер тематики'] = df['Тематика'].map(topic_cluster_map)
df = df.dropna(subset=['Кластер тематики'])
counts = df['Кластер тематики'].value_counts()
df = df[df['Кластер тематики'].isin(counts[counts>=2].index)]

# Препроцессинг полей
df['description'] = df['description'].astype(str).apply(preprocess_text)
df['group_name'] = df['group_name'].astype(str).apply(preprocess_text)

X_desc = df['description']; X_group = df['group_name']
y_t = df['Тематика']; y_c = df['Кластер тематики']

# Train/test split
X_desc_tr, X_desc_te, X_group_tr, X_group_te, y_t_tr, y_t_te, y_c_tr, y_c_te = \
    train_test_split(X_desc, X_group, y_t, y_c, test_size=0.2, random_state=42, stratify=y_c)

logger.info(f'Train size: {X_desc_tr.shape[0]}, Test size: {X_desc_te.shape[0]}')

# TF-IDF
tfidf_desc = TfidfVectorizer(max_features=3000); Xd_tr = tfidf_desc.fit_transform(X_desc_tr); Xd_te = tfidf_desc.transform(X_desc_te)
tfidf_group = TfidfVectorizer(max_features=1000); Xg_tr = tfidf_group.fit_transform(X_group_tr); Xg_te = tfidf_group.transform(X_group_te)
X_tf_tr = np.hstack([Xd_tr.toarray(), Xg_tr.toarray()])
X_tf_te = np.hstack([Xd_te.toarray(), Xg_te.toarray()])

model_tf = LogisticRegression(max_iter=1000).fit(X_tf_tr, y_t_tr)
pred_tf = model_tf.predict(X_tf_te)

# SBERT
sbert = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
emb_d_tr = sbert.encode(X_desc_tr.tolist(), show_progress_bar=True)
emb_d_te = sbert.encode(X_desc_te.tolist(), show_progress_bar=True)
emb_g_tr = sbert.encode(X_group_tr.tolist(), show_progress_bar=True)
emb_g_te = sbert.encode(X_group_te.tolist(), show_progress_bar=True)
X_sb_tr = np.hstack([emb_d_tr, emb_g_tr])
X_sb_te = np.hstack([emb_d_te, emb_g_te])

model_sbert_lr = LogisticRegression(max_iter=1000).fit(X_sb_tr, y_t_tr)
pred_sbert_lr = model_sbert_lr.predict(X_sb_te)
model_sbert_svc = LinearSVC().fit(X_sb_tr, y_t_tr)
pred_sbert_svc = model_sbert_svc.predict(X_sb_te)

# fastText — подготовка файлов
def to_ft_file(desc, grp, labels, path):
    with open(path, 'w', encoding='utf-8') as fw:
        for d, g, lab in zip(desc, grp, labels):
            fw.write(f"__label__{lab} {d} {g}\n")
to_ft_file(X_desc_tr, X_group_tr, y_t_tr, 'ft_train.txt')
to_ft_file(X_desc_te, X_group_te, y_t_te, 'ft_valid.txt')

# Автоматический подбор
ft_model = fasttext.train_supervised(
    input='ft_train.txt',
    autotuneValidationFile='ft_valid.txt',
    autotuneDuration=300
)
N, P, R = ft_model.test('ft_valid.txt')
print(f"fastText autotune → P@1={P:.4f}, R@1={R:.4f}")

ft_preds = [lab[0].replace('__label__','') for lab in ft_model.predict(
    (X_desc_te + ' ' + X_group_te).tolist(), k=1)[0]]

# Карта тем → кластер
def to_cluster(arr):
    return [topic_cluster_map.get(x, 'UNK') for x in arr]

preds = {
    'TF-IDF+LR': pred_tf,
    'SBERT+LR': pred_sbert_lr,
    'SBERT+SVC': pred_sbert_svc,
    'fastText': ft_preds
}

# Метрики
results = {}
all_labels = sorted(set(y_c_te))
for name, pr in preds.items():
    cl_pr = to_cluster(pr)
    acc = accuracy_score(y_c_te, cl_pr)
    f1 = f1_score(y_c_te, cl_pr, average='macro')
    cm = confusion_matrix(y_c_te, cl_pr, labels=all_labels)
    results[name] = {'acc': acc, 'f1': f1, 'cm': cm}
    logger.info(f"{name}: acc={acc:.4f}, f1_macro={f1:.4f}")


def plot_confusion_matrices(results, labels, filename_prefix='confusion'):
    """
    results: dict {model_name: {'cm': confusion_matrix, ...}, ...}
    labels: list of cluster labels for оси
    """
    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 6))
    if n == 1:
        axes = [axes]
    for ax, (name, res) in zip(axes, results.items()):
        cm = res['cm']
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                    xticklabels=labels, yticklabels=labels)
        ax.set_title(name, fontsize=14)
        ax.set_xlabel('Предсказано')
        ax.set_ylabel('Истинно')
        ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    # Сохраняем общий и по-модельные
    out_png = f"{filename_prefix}_all.png"
    plt.savefig(out_png, dpi=200)
    logger.info(f"Сохранена матрица ошибок: {out_png}")
    plt.close(fig)

# Собираем метки кластеров для осей
cluster_labels = sorted(set(y_c_te))

# Визуализируем
plot_confusion_matrices(results, cluster_labels, filename_prefix='confusion_clusters')

logger.info('Визуализация матриц ошибок сохранена в "confusion_matrices_clusters.png"')


# Сводная таблица
out = pd.DataFrame([
    {'Модель': nm, 'Accuracy': val['acc'], 'F1_macro': val['f1']}
    for nm, val in results.items()
])
print(out)
out.to_csv('model_comparison.csv', index=False)
logger.info("Сохранено в model_comparison.csv")
