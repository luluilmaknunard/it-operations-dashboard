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
    # 2. KONVERSI KOLOM WAKTU KE DATETIME
    # =========================================================================
    # Data Excel menggunakan format:
    # DD.MM.YYYY HH:MM:SS
    #
    # Contoh:
    # 01.04.2026 5:23:37
    # = 1 April 2026 pukul 05:23:37
    #
    # dayfirst=True wajib supaya 01.04.2026 tidak dibaca sebagai 4 Januari 2026.

    time_columns = [
        'date_created_at',
        'date_start_interaction',
        'date_assigned',
        'date_pending',
        'date_last_update'
    ]

    for col in time_columns:
        if col in df_transformed.columns:
            df_transformed[col] = pd.to_datetime(
                df_transformed[col],
                errors='coerce',
                dayfirst=True
        )

  # =========================================================================
    # 3. HITUNG MTTR
    # =========================================================================
    #
    # RUMUS:
    #
    # NON-PENDING:
    #     date_last_update - date_assigned
    #
    # PENDING:
    #     (date_last_update - date_assigned)
    #     - (date_last_update - date_pending)
    #
    # Secara matematis:
    #     = date_pending - date_assigned
    #
    # MTTR dihitung PER TIKET terlebih dahulu.
    # Setelah itu rata-rata MTTR dihitung dari kolom mttr_minutes.
    # =========================================================================

    df_transformed['mttr_non_pending_minutes'] = np.nan
    df_transformed['mttr_pending_minutes'] = np.nan
    df_transformed['mttr_minutes'] = np.nan

    required_mttr_cols = {
        'date_assigned',
        'date_last_update'
    }

    if required_mttr_cols.issubset(df_transformed.columns):

        # ---------------------------------------------------------
        # MTTR NON-PENDING
        # date_last_update - date_assigned
        # ---------------------------------------------------------

        durasi_non_pending = (
            df_transformed['date_last_update']
            - df_transformed['date_assigned']
        ).dt.total_seconds() / 60

        df_transformed['mttr_non_pending_minutes'] = (
            durasi_non_pending.where(durasi_non_pending >= 0)
        )

        # ---------------------------------------------------------
        # MTTR PENDING
        #
        # (last_update - assigned)
        # -
        # (last_update - pending)
        #
        # = pending - assigned
        # ---------------------------------------------------------

        if 'date_pending' in df_transformed.columns:

            durasi_total = (
                df_transformed['date_last_update']
                - df_transformed['date_assigned']
            ).dt.total_seconds() / 60

            durasi_pending = (
                df_transformed['date_last_update']
                - df_transformed['date_pending']
            ).dt.total_seconds() / 60

            mttr_pending = (
                durasi_total - durasi_pending
            )

            df_transformed['mttr_pending_minutes'] = (
                mttr_pending.where(mttr_pending >= 0)
            )

            # -----------------------------------------------------
            # MTTR FINAL PER TIKET
            # -----------------------------------------------------

            has_pending = (
                df_transformed['date_pending'].notna()
            )

            df_transformed['mttr_minutes'] = np.where(
                has_pending,
                df_transformed['mttr_pending_minutes'],
                df_transformed['mttr_non_pending_minutes']
            )

        else:

            df_transformed['mttr_minutes'] = (
                df_transformed['mttr_non_pending_minutes']
            )

    # ---------------------------------------------------------
    # Pastikan numeric
    # ---------------------------------------------------------

    for col in [
        'mttr_pending_minutes',
        'mttr_non_pending_minutes',
        'mttr_minutes'
    ]:

        df_transformed[col] = pd.to_numeric(
            df_transformed[col],
            errors='coerce'
        )

        df_transformed[col] = df_transformed[col].where(
            df_transformed[col] >= 0
        )

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

    return df