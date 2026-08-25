import os
import sys
import pandas as pd
import numpy as np

from src.ticket_classifier import classify_tickets
from src.network_classifier import classify_network_component


def transform_data_and_kpi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Melakukan transformasi data, pemisahan kategori bertingkat, 
    perhitungan KPI, serta Klasifikasi ML (Network Component & Ticket Type).
    """
    if df is None or df.empty:
        return df

    df_transformed = df.copy()

    # =========================================================================
    # TRANSFORMASI NAMA: Mengambil 2 Kata Pertama (created_by_name & updated_by_name)
    # =========================================================================
    def shorten_to_two_words(name):
        if pd.isna(name) or not str(name).strip():
            return name
        
        words = str(name).strip().split()
        if not words:
            return name

        kata_pertama = words[0]

        if kata_pertama.lower() == "muhammad":
            display_name = words[1] if len(words) > 1 else kata_pertama
        else:
            display_name = kata_pertama

        return display_name.upper()

    for name_col in ('created_by_name', 'updated_by_name'):
        if name_col in df_transformed.columns:
            df_transformed[name_col] = df_transformed[name_col].apply(shorten_to_two_words)

    # =========================================================================
    # 1. Pemisahan Category Name Bertingkat
    # =========================================================================
    # Pemisahan Category Name yang lebih aman (menangani '-' dengan atau tanpa spasi)
    if 'category_name' in df_transformed.columns:
            # Regex split fleksibel untuk strip (-), pipe (|), atau (>)
            split_cats = df_transformed['category_name'].astype(str).str.split(r'\s*(?:-|\||>)\s*', expand=True)
            
            for i in range(split_cats.shape[1]):
                col_name = f'category_split_{i+1}'
                df_transformed[col_name] = split_cats[i].str.strip()
                df_transformed[col_name] = df_transformed[col_name].replace(['nan', 'None', '', 'null'], None)


    # =========================================================================
    # 2. Konversi Kolom Waktu ke Datetime
    # =========================================================================
    time_columns = [
        'date_created_at', 'date_start_interaction', 'date_assigned', 
        'date_pending', 'date_last_update'
    ]
    for col in time_columns:
        if col in df_transformed.columns:
            df_transformed[col] = pd.to_datetime(df_transformed[col], errors='coerce')

    # =========================================================================
    # 2. Konversi Kolom Waktu ke Datetime (Dibuat Lebih Fleksibel & Paksa ISO/Format)
    # =========================================================================
    # =========================================================================
    # 2. Konversi Kolom Waktu ke Datetime (Aman dari ArrowTypeError)
    # =========================================================================
    time_columns = [
        'date_created_at', 'date_start_interaction', 'date_assigned', 
        'date_pending', 'date_last_update'
    ]
    
    for col in time_columns:
        if col in df_transformed.columns:
            # Paksa konversi ke datetime64, string aneh diubah jadi NaT (Not a Time)
            df_transformed[col] = pd.to_datetime(df_transformed[col], errors='coerce')
            
    # =========================================================================
    # 3. Hitung MTTR (Memastikan Nilai Terisi & Tipe Data Benar)
    # =========================================================================
    # Tentukan tanggal selesai: utamakan date_last_update, jika kosong gunakan date_created_at/sekarang
    if 'date_last_update' in df_transformed.columns and 'date_assigned' in df_transformed.columns:
        
        # Hitung durasi dasar: date_last_update - date_assigned
        durasi_menit = (df_transformed['date_last_update'] - df_transformed['date_assigned']).dt.total_seconds() / 60
        
        # Jika date_pending terisi, hitung durasi sampai pending: date_pending - date_assigned
        if 'date_pending' in df_transformed.columns:
            durasi_pending = (df_transformed['date_pending'] - df_transformed['date_assigned']).dt.total_seconds() / 60
            
            # Pilih durasi pending jika ada dan valid (>0), jika tidak pakai durasi dasar
            df_transformed['mttr_minutes'] = np.where(
                df_transformed['date_pending'].notna() & (durasi_pending > 0),
                durasi_pending,
                durasi_menit
            )
        else:
            df_transformed['mttr_minutes'] = durasi_menit

        # Konversi ke angka secara paksa & hilangkan NaN
        df_transformed['mttr_minutes'] = pd.to_numeric(df_transformed['mttr_minutes'], errors='coerce').fillna(0)
        df_transformed['mttr_minutes'] = df_transformed['mttr_minutes'].clip(lower=0)
    else:
        df_transformed['mttr_minutes'] = 0.0

    # Status Pending
    if 'date_pending' in df_transformed.columns:
        df_transformed['pending_status'] = np.where(
            df_transformed['date_pending'].notna(), 'Pending', 'Non-Pending'
        )
    else:
        df_transformed['pending_status'] = 'Non-Pending'

    # =========================================================================
    # 4. Hitung Response Time (Menit)
    # =========================================================================
    if 'date_assigned' in df_transformed.columns and 'date_start_interaction' in df_transformed.columns:
        df_transformed['response_time_minutes'] = (
            (df_transformed['date_assigned'] - df_transformed['date_start_interaction']).dt.total_seconds() / 60
        ).clip(lower=0)
    else:
        df_transformed['response_time_minutes'] = 0.0

    # =========================================================================
    # 5. Hitung SLA Status (Comply vs Breach)
    # =========================================================================
    if 'sla_second' in df_transformed.columns:
        df_transformed['sla_minute'] = df_transformed['sla_second'] / 60
        df_transformed['sla_status'] = df_transformed.apply(
            lambda row: 'Comply' if row['mttr_minutes'] <= row.get('sla_minute', 0) else 'Breach', 
            axis=1
        )
    else:
        df_transformed['sla_status'] = 'UNDETERMINED'

    # =========================================================================
    # 6. Resolution Time Grouping
    # =========================================================================
    if 'date_created_at' in df_transformed.columns and 'date_last_update' in df_transformed.columns:
        df_transformed['resolution_time_minutes'] = (
            (df_transformed['date_last_update'] - df_transformed['date_created_at']).dt.total_seconds() / 60
        ).clip(lower=0)
        
        def group_resolution_time(minutes):
            if pd.isna(minutes):
                return "> 240 Menit"
            elif minutes <= 30:
                return "≤ 30 Menit"
            elif minutes <= 60:
                return "31 - 60 Menit"
            elif minutes <= 120:
                return "61 - 120 Menit"
            elif minutes <= 240:
                return "121 - 240 Menit"
            else:
                return "> 240 Menit"

        df_transformed['resolution_time_group'] = df_transformed['resolution_time_minutes'].apply(group_resolution_time)

    # =========================================================================
    # 7 & 8. KLASIFIKASI MODEL MACHINE LEARNING (.pkl)
    # =========================================================================
    # Menjalankan Machine Learning untuk Ticket Type & Network Component
    try:
        df_transformed = classify_tickets(df_transformed)
        df_transformed = classify_network_component(df_transformed)
    except Exception as e:
        print(f"Warning: Gagal mengeksekusi model ML pada data: {e}")

    return df_transformed


def get_nama_display_dax(name):
    if pd.isna(name) or not str(name).strip():
        return name
    words = str(name).strip().split()
    if not words:
        return name

    kata_pertama = words[0]

    if kata_pertama.lower() == "muhammad":
        result = words[1] if len(words) > 1 else kata_pertama
    else:
        result = kata_pertama

    return result.upper()


def transform_category_name(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or 'category_name' not in df.columns:
        return df

    split_categories = df['category_name'].astype(str).str.split(' - ', expand=True)
    num_new_cols = split_categories.shape[1]
    new_category_cols = [f'category_split_{i+1}' for i in range(num_new_cols)]
    df[new_category_cols] = split_categories

    # === TEMPEL DI ATAS RETURN DF_TRANSFORMED ===
    print("\n" + "="*40)
    print("📌 DEBUG DATASET SAYA:")
    print("Daftar Kolom Ada:", list(df_transformed.columns))
    print("Contoh 3 mttr_minutes:", df_transformed['mttr_minutes'].head(3).tolist())
    print("="*40 + "\n")

    return df_transformed

    return df