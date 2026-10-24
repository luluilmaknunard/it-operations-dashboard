"""
Tujuan:
    Modul Machine Learning ini didesain secara khusus untuk mengklasifikasikan 
    akar penyebab (root cause) komponen jaringan IT berdasarkan deskripsi freetext.

Input:
    Data numerik dan teks keluhan pengguna dari atribut tiket (symptom, rootcause, dsb).

Proses:
    - Menyiapkan (aggregate) teks mentah menjadi serangkaian token valid.
    - Menggunakan algoritma pemrosesan bahasa (NLP) dengan TF-IDF Vectorizer.
    - Mengkombinasikan level Kata (Word) dan level Karakter (Char) menggunakan FeatureUnion.
    - Melatih Model Regresi Logistik (Logistic Regression) dengan parameter pembobot yang seimbang.
    - Serialisasi/Deserialisasi model lewat library Joblib (.pkl).

Output:
    Kolom baru "network_component" (hasil tebakan model) dan 
    "network_confidence" (persentase/probabilitas akurasi tebakan tersebut).
"""

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
    Tujuan: 
        Menggabungkan beberapa kolom freetext tiket (seperti remark, summary, dan symptom)
        menjadi satu teks utuh untuk inputan klasifikasi model.
    """

    text_cols = [
        "ticket_rootcause",
        "remark",
        "ticket_summary",
        "ticket_symptom"
    ]

    available_cols = [
        col for col in text_cols
        if col in df.columns
    ]

    if not available_cols:
        # Jika kolom acuan tidak ditemukan sama sekali, hasilkan blank series
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


def create_network_model():
    """
    Membuat model klasifikasi Network Component.

    Menggunakan:
    - Word TF-IDF
    - Character TF-IDF
    - Logistic Regression (Multi-class with balanced weights)

    Tujuan: 
        Membuat arsitektur klasifikasi teks hybrid. 
        Menggabungkan representasi unigram/bigram kata dan character-level n-gram 
        agar model tetap tangguh dalam menangani salah ketik (typo).
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

    # Menyatukan matriks dari vektor kata dan vektor karakter
    features = FeatureUnion([
        ("word", word_vectorizer),
        ("char", char_vectorizer)
    ])

    # Mendeklarasikan pipeline pengklasifikasi
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


def train_network_classifier(
    df: pd.DataFrame,
    label_column="network_compo"
):
    """
    Tujuan: 
        Melatih (fit) model Network Component (seperti LAN, Internet, VPN) dengan 
        data Excel berlabel manual, lalu menyimpannya dalam format .pkl lokal.
    """

    if df is None or df.empty:
        raise ValueError("Data training kosong.")

    if label_column not in df.columns:
        raise ValueError(
            f"Kolom '{label_column}' tidak ditemukan."
        )

    # ekstraksi fitur dan label
    texts = prepare_network_text(df)
    labels = (
        df[label_column]
        .astype(str)
        .str.strip()
    )

    #  Membersihkan label invalid yang mungkin ter-record di Excel (seperti NaN / Empty)
    valid = (labels != "") & (labels.str.lower() != "nan") & (labels != "Network Lainnya")

    texts = texts[valid]
    labels = labels[valid]

    # Guard clause minimum ketersediaan data latih
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

    # Build and train model
    model = create_network_model()
    # Training
    model.fit(texts, labels)

    # Buat folder model
    os.makedirs(
        os.path.dirname(MODEL_PATH),
        exist_ok=True
    )

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
    Tujuan: 
    Memuat instance pipeline ML yang sebelumnya sudah dilatih (pre-trained).
    """

    if not os.path.exists(MODEL_PATH):
        return None

    return joblib.load(MODEL_PATH)


# ============================================================
# KLASIFIKASI NETWORK COMPONENT
# ============================================================

def classify_network_component(df: pd.DataFrame):
    """
    Tujuan: 
        Memasukkan dataframe mentah ke dalam model untuk mendapatkan 
        hasil tebakan komponen jaringan beserta confidence score-nya (0.0 - 1.0).
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

    # Inferensi label klasifikasi (contoh: 'VPN', 'LAN', dsb)
    predictions = model.predict(texts)

    df_result["network_component"] = predictions

    # Menyimpan tingkat probabilitas agar bisa ditinjau ulang oleh tim data jika confidence rendah
    probabilities = model.predict_proba(texts)

    df_result["network_confidence"] = (
        probabilities.max(axis=1)
    )

    return df_result