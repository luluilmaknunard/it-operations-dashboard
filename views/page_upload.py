"""
Tujuan:
    Modul antarmuka (view) untuk menangani proses unggah (ingestion) data mentah.
    Halaman ini memungkinkan pengguna mengunggah file tiket IT (CSV/Excel),
    yang kemudian akan dibersihkan, ditransformasi, dan disimpan ke dalam
    Session State serta database Supabase.

Input:
    File CSV atau Excel yang diunggah pengguna melalui komponen st.file_uploader.

Proses:
    - Menerima file unggahan dari pengguna.
    - Menjalankan fungsi pembersihan data (clean_ticket_data).
    - Menjalankan fungsi transformasi & kalkulasi KPI (transform_kpi_data).
    - Menyimpan dataframe final ke st.session_state agar bisa diakses halaman lain.
    - Menyimpan salinan data ke database eksternal (Supabase).

Output:
    Notifikasi sukses (st.success) di UI Streamlit jika pemrosesan berhasil.
"""

import streamlit as st
from src.data_cleaning import clean_ticket_data
from src.data_transformation import transform_kpi_data
from src.database import save_to_supabase

def render():
    """
    Tujuan: Merender elemen-elemen UI untuk halaman Upload Data Raw.
    """

    st.title("📤 Form Ingestion Data Raw")

    # Widget untuk mengunggah file dengan batasan ekstensi yang diizinkan
    uploaded_file = st.file_uploader("Upload File Tiket (CSV/Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        if st.button("Proses Data", type="primary"):
            
            # Menampilkan indikator loading saat pemrosesan berjalan
            with st.spinner("Membersihkan & Mentransformasi Data..."):
                # 1. Cleaning & Transformation
                # Memanggil modul pipeline pemrosesan data
                df_clean = clean_ticket_data(uploaded_file)
                df_transformed = transform_kpi_data(df_clean)
                
                # 2. Save Session & Database
                # Menyimpan hasil akhir ke session state agar reaktif di semua halaman
                st.session_state['df_raw'] = df_transformed
                save_to_supabase(df_transformed)
                
                st.success("✅ Data berhasil diproses dan disimpan!")