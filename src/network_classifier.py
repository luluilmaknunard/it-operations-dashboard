import os
import joblib
import pandas as pd

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


MODEL_PATH = "models/network_classifier.pkl"


# ============================================================
# MEMBUAT TEKS DARI KOLOM FREETEXT
# ============================================================

def prepare_network_text(df: pd.DataFrame) -> pd.Series:
    """
    Menggabungkan beberapa kolom freetext tiket
    menjadi satu teks untuk klasifikasi network component.
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
        .str.lower()
        .str.strip()
    )

    return text


# ============================================================
# MEMBUAT MODEL
# ============================================================

def create_network_model():
    """
    Membuat model klasifikasi Network Component.

    Menggunakan:
    - Word TF-IDF
    - Character TF-IDF
    - Logistic Regression (Multi-class with balanced weights)
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

def train_network_classifier(
    df: pd.DataFrame,
    label_column="network_compo"
):
    """
    Melatih model Network Component (LAN, Internet, VPN, dll).
    """

    if df is None or df.empty:
        raise ValueError("Data training kosong.")

    if label_column not in df.columns:
        raise ValueError(
            f"Kolom '{label_column}' tidak ditemukan."
        )

    # Siapkan teks
    texts = prepare_network_text(df)

    # Ambil label
    labels = (
        df[label_column]
        .astype(str)
        .str.strip()
    )

    # Filter label yang valid (Abaikan NaN / Empty / Network Lainnya jika ada)
    valid = (labels != "") & (labels.str.lower() != "nan") & (labels != "Network Lainnya")

    texts = texts[valid]
    labels = labels[valid]

    if len(texts) < 10:
        raise ValueError(
            "Data training network terlalu sedikit. "
            "Minimal gunakan sekitar 10 tiket terlabel."
        )

    if labels.nunique() < 2:
        raise ValueError(
            "Data training harus memiliki minimal 2 kategori network yang berbeda."
        )

    print("Jumlah data training Network:", len(texts))
    print("\nDistribusi label Network Component:")
    print(labels.value_counts())

    # Buat model
    model = create_network_model()

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
        f"\nModel Network berhasil disimpan ke: "
        f"{MODEL_PATH}"
    )

    return model


# ============================================================
# LOAD MODEL
# ============================================================

def load_network_classifier():
    """
    Memuat model Network Component yang sudah dilatih.
    """

    if not os.path.exists(MODEL_PATH):
        return None

    return joblib.load(MODEL_PATH)


# ============================================================
# KLASIFIKASI NETWORK COMPONENT
# ============================================================

def classify_network_component(df: pd.DataFrame):
    """
    Mengklasifikasikan seluruh tiket ke dalam Network Component
    menggunakan model lokal yang telah dilatih.
    """

    if df is None or df.empty:
        return df

    model = load_network_classifier()

    if model is None:
        raise FileNotFoundError(
            f"Model belum tersedia: {MODEL_PATH}"
        )

    df_result = df.copy()

    texts = prepare_network_text(df_result)

    # Prediksi
    predictions = model.predict(texts)

    df_result["network_component"] = predictions

    # Confidence Score
    probabilities = model.predict_proba(texts)

    df_result["network_confidence"] = (
        probabilities.max(axis=1)
    )

    return df_result