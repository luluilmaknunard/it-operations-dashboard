import os
import joblib
import pandas as pd

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


MODEL_PATH = "models/ticket_classifier.pkl"


# ============================================================
# MEMBUAT TEKS DARI KOLOM FREETEXT
# ============================================================

def prepare_ticket_text(df: pd.DataFrame) -> pd.Series:
    """
    Menggabungkan beberapa kolom freetext tiket
    menjadi satu teks untuk klasifikasi.
    """

    text_cols = [
        "ticket_rootcouse",
        "remark",
        "ticket_summary",
        "ticket_symptom"
    ]

    available_cols = [
        col for col in text_cols
        if col in df.columns
    ]

    if not available_cols:
        return pd.Series([""] * len(df), index=df.index)

    text = (
        df[available_cols]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.strip()
    )

    return text


# ============================================================
# MEMBUAT MODEL
# ============================================================

def create_model():
    """
    Membuat model klasifikasi tiket.

    Menggunakan:
    - Word TF-IDF
    - Character TF-IDF
    - Logistic Regression
    """

    word_vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95,
        sublinear_tf=True
    )

    char_vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        max_df=0.95,
        sublinear_tf=True
    )

    features = FeatureUnion([
        ("word", word_vectorizer),
        ("char", char_vectorizer)
    ])

    model = Pipeline([
        ("features", features),
        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced"
            )
        )
    ])

    return model


# ============================================================
# TRAINING MODEL
# ============================================================

def train_ticket_classifier(
    df: pd.DataFrame,
    label_column="ticket_type"
):
    """
    Melatih model Incident vs Request.
    """

    if df is None or df.empty:
        raise ValueError("Data training kosong.")

    if label_column not in df.columns:
        raise ValueError(
            f"Kolom '{label_column}' tidak ditemukan."
        )

    # Siapkan teks
    texts = prepare_ticket_text(df)

    # Ambil label
    labels = (
        df[label_column]
        .astype(str)
        .str.strip()
        .str.title()
    )

    # Hanya izinkan dua kategori
    valid = labels.isin([
        "Gangguan",
        "Request"
    ])

    texts = texts[valid]
    labels = labels[valid]

    if len(texts) < 20:
        raise ValueError(
            "Data training terlalu sedikit. "
            "Minimal gunakan sekitar 20 tiket."
        )

    if labels.nunique() < 2:
        raise ValueError(
            "Data training harus memiliki "
            "Gangguan DAN Request."
        )

    print("Jumlah data training:", len(texts))
    print("\nDistribusi label:")
    print(labels.value_counts())

    # Buat model
    model = create_model()

    # Training
    model.fit(texts, labels)

    # Buat folder model
    os.makedirs(
        os.path.dirname(MODEL_PATH),
        exist_ok=True
    )

    # Simpan
    joblib.dump(
        model,
        MODEL_PATH
    )

    print(
        f"\nModel berhasil disimpan ke: "
        f"{MODEL_PATH}"
    )

    return model


# ============================================================
# LOAD MODEL
# ============================================================

def load_ticket_classifier():
    """
    Memuat model yang sudah dilatih.
    """

    if not os.path.exists(MODEL_PATH):
        return None

    return joblib.load(MODEL_PATH)


# ============================================================
# KLASIFIKASI TIKET
# ============================================================

def classify_tickets(df: pd.DataFrame):
    """
    Mengklasifikasikan seluruh tiket menggunakan
    model lokal.
    """

    if df is None or df.empty:
        return df

    model = load_ticket_classifier()

    if model is None:
        raise FileNotFoundError(
            f"Model belum tersedia: {MODEL_PATH}"
        )

    df_result = df.copy()

    texts = prepare_ticket_text(df_result)

    # Prediksi
    predictions = model.predict(texts)

    df_result["ticket_type"] = predictions

    # Confidence
    probabilities = model.predict_proba(texts)

    df_result["ticket_confidence"] = (
        probabilities.max(axis=1)
    )

    return df_result