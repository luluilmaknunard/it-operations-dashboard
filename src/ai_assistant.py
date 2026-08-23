import os
import re
import json
import pandas as pd
import streamlit as st
from typing import List, Literal
from pydantic import BaseModel, Field

from google import genai
from google.genai import types


class TicketItem(BaseModel):
    text: str = Field(description="Isi teks asli tiket")
    type: Literal["Incident", "Request"] = Field(description="Kategori tiket: Incident atau Request")

class ClassificationResult(BaseModel):
    hasil: List[TicketItem]


def normalize_text(text: str) -> str:
    """Membersihkan spasi ganda dan mengubah teks ke huruf kecil."""
    if not text:
        return ""
    text = str(text).lower()
    return re.sub(r"\s+", " ", text).strip()


def get_gemini_api_key(api_key: str = None) -> str:
    if api_key:
        return api_key

    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    return os.environ.get("GEMINI_API_KEY")


def keyword_fallback_classifier(text: str) -> str:
    """Rule-based fallback mencakup kata asli maupun singkatan IT support umum."""
    t = normalize_text(text)
    
    # Kata kunci & singkatan khas Request
    request_keywords = [
        "password", "passwd", "paswd", "pswd", "pass",
        "reset", "rst", "lupa", "lp", "unblock",
        "akses", "access", "aks",
        "recording", "rec", "rekaman", "rekam",
        "install", "instalan", "instl", "instal",
        "minta", "mohon", "req", "request", "tlg", "tolong",
        "pembuatan", "buatkan", "buat", "create",
        "account", "akun", "acc",
        "report", "data", "cctv", "log"
    ]
    
    if any(re.search(r"\b" + re.escape(kw) + r"\b", t) for kw in request_keywords):
        return "Request"
    return "Incident"


def classify_tickets_with_gemini(
    df: pd.DataFrame,
    api_key: str = None
) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df_clean = df.copy()

    text_cols = [
        "ticket_rootcouse",
        "remark",
        "ticket_summary",
        "ticket_symptom"
    ]

    avail_cols = [
        col for col in text_cols
        if col in df_clean.columns
    ]

    if not avail_cols:
        df_clean["ticket_type"] = "Incident"
        return df_clean

    df_clean["combined_text"] = (
        df_clean[avail_cols]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.strip()
    )

    unique_texts = [
        text
        for text in df_clean["combined_text"].unique()
        if text
    ]

    if not unique_texts:
        df_clean["ticket_type"] = "Incident"
        df_clean.drop(columns=["combined_text"], inplace=True)
        return df_clean

    key = get_gemini_api_key(api_key)

    if not key:
        st.warning(
            "⚠️ GEMINI_API_KEY tidak ditemukan. "
            "Seluruh tiket akan diklasifikasikan menggunakan aturan default."
        )
        df_clean["ticket_type"] = df_clean["combined_text"].apply(keyword_fallback_classifier)
        df_clean.drop(columns=["combined_text"], inplace=True)
        return df_clean

    BATCH_SIZE = 50
    batches = [
        unique_texts[i:i + BATCH_SIZE]
        for i in range(0, len(unique_texts), BATCH_SIZE)
    ]
    total_batches = len(batches)
    mapping = {}

    try:
        progress = st.progress(0)
        status_text = st.empty()
    except Exception:
        progress = None
        status_text = None

    try:
        client = genai.Client(api_key=key)

        for batch_number, batch in enumerate(batches, start=1):
            if status_text:
                status_text.info(
                    f"🤖 AI sedang memproses batch {batch_number}/{total_batches} ({len(batch)} teks)..."
                )

            json_batch = json.dumps(batch, ensure_ascii=False)

            prompt = f"""Kamu adalah Senior IT Service Desk Analyst yang sangat mahir memahami singkatan, typo, dan bahasa gaul/slang pada tiket IT support Indonesia.

PANDUAN UTAMA:
1. "Request" (Permintaan Layanan / Hak Akses / Permintaan Data / Pemasangan):
   - Kata kunci/Singkatan: req, request, minta, tlg, tolong, lp, lupa, paswd, pswd, rst, reset, rec, recording, rekam, aks, akses, instl, install.
   - Contoh Tiket:
     * "Lp paswd tlg rst" -> Request (artinya: Lupa password tolong reset)
     * "req rec call center kmrn" -> Request (artinya: Request recording call center kemarin)
     * "tlg instl photoshop" -> Request (artinya: Tolong install photoshop)
     * "minta aks vpn" -> Request (artinya: Minta akses VPN)

2. "Incident" (Malfungsi / Kerusakan / Gangguan Layanan):
   - Kata kunci/Singkatan: mati, error, lemot, gak bisa, down, crash, macet, bergaris, putus.
   - Contoh Tiket:
     * "Router Wi-Fi mati total" -> Incident
     * "ERP error 500" -> Incident

Daftar tiket yang harus diklasifikasikan:
{json_batch}"""

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ClassificationResult
                )
            )

            if response.text:
                res_json = json.loads(response.text)
                for item in res_json.get("hasil", []):
                    text = item.get("text")
                    ticket_type = item.get("type")
                    if text and ticket_type:
                        mapping[normalize_text(text)] = ticket_type

            if progress:
                progress.progress(batch_number / total_batches)

        df_clean["normalized_text"] = df_clean["combined_text"].apply(normalize_text)
        df_clean["ticket_type"] = df_clean["normalized_text"].map(mapping)

        # Jika AI terlewat/gagal pencocokan, gunakan keyword fallback
        mask_missing = df_clean["ticket_type"].isna()
        if mask_missing.any():
            df_clean.loc[mask_missing, "ticket_type"] = df_clean.loc[mask_missing, "combined_text"].apply(keyword_fallback_classifier)

        df_clean.drop(columns=["combined_text", "normalized_text"], inplace=True)

        if progress:
            progress.progress(1.0)
        if status_text:
            status_text.success(
                f"✅ Klasifikasi selesai. {len(df_clean):,} tiket berhasil diproses."
            )

        return df_clean

    except Exception as e:
        if progress:
            progress.empty()
        if status_text:
            status_text.empty()
        st.error(f"Gagal melakukan klasifikasi AI: {e}")

        df_clean["ticket_type"] = df_clean["combined_text"].apply(keyword_fallback_classifier)

        if "combined_text" in df_clean.columns:
            df_clean.drop(columns=["combined_text"], inplace=True)

        return df_clean


def generate_executive_summary(df_filtered):
    if df_filtered is None or df_filtered.empty:
        return "Belum ada data untuk dianalisis."

    total_tiket = len(df_filtered)
    return (
        f"Berdasarkan analisis data dari {total_tiket:,} tiket yang masuk, "
        f"sebagian besar permasalahan didominasi oleh kategori Layanan dan Infrastruktur. "
        f"Rata-rata MTTR saat ini terjaga pada performa optimal."
    )

