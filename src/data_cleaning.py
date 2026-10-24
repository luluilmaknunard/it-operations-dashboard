"""
Tujuan:
    Modul ini berisi logika utama untuk tahap awal pembersihan data (data cleaning).
    Fungsi-fungsi di sini bertugas membuang karakter yang tidak valid, melakukan
    masking (penyamaran) pada data sensitif (seperti IP Address dan Email), serta
    menyiapkan fitur-fitur komponen tanggal (Calendar Table) untuk visualisasi.

Input:
    DataFrame Pandas mentah (df_raw) yang berisi data dari pembacaan file CSV/Excel.

Proses:
    - Membersihkan substring "SEGMENT" pada teks layanan dan departemen.
    - Memotong nama user/agen maksimal menjadi 2 kata.
    - Melakukan sanitasi pola alamat IP dengan teks placeholder [IP_PROTECTED].
    - Melakukan masking pada karakter string alamat email pengguna/pelanggan.
    - Mengekstrak bagian-bagian waktu (Tahun, Bulan, Kuartal, Minggu) dari kolom tanggal.

Output:
    DataFrame Pandas yang sudah bersih dan kaya akan fitur turunan (feature engineering).

Catatan:
    Logika ekstraksi waktu direplikasi sedemikian rupa agar serupa dengan 
    kemampuan ADDCOLUMNS pada fungsi DAX di Microsoft Power BI.
"""


import re
import pandas as pd

def clean_sensitive_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tujuan:
        Membersihkan IP, email, merapikan departemen/layanan dari kata SEGMENT,
        menangani data kosong, serta mengekstrak fitur tanggal untuk keperluan Heatmap.

    Input:
        df (pd.DataFrame): Dataset tiket mentah yang akan disanitasi.

    Proses:
        - Melakukan deep copy dataset agar referensi variabel asli tidak termutasi.
        - Membersihkan teks operasional khusus (SEGMENT) dari layanan/departemen.
        - Memotong panjang string pada kolom nama.
        - Melakukan masking IP dan Email dengan teknik Regex (Regular Expression).
        - Ekstraksi informasi waktu menjadi kolom terpisah (Year, Month, Quarter, dll).

    Output:
        pd.DataFrame: Data yang sudah dibersihkan secara komprehensif.

    Catatan:
        Fungsi ini akan langsung mengembalikan nilai aslinya jika input berupa 
        DataFrame kosong (empty) atau bernilai None.
    """

    if df is None or df.empty:
        return df

    df_clean = df.copy()

    
    def clean_segment_name(text):
        """
        Tujuan: Menghapus substring "SEGMENT" beserta angka pengikutnya 
        dan menghapus simbol pemisah yang tertinggal di akhir teks.
        """
          
        if pd.isnull(text) or str(text).strip() in ['nan', 'None', '0', '-']:
            return 'Layanan Tidak Diketahui'
        
        # Hapus kata 'SEGMENT' / 'Segment' beserta angka setelahnya
        cleaned = re.sub(r'\s*SEGMENT\s*\d*|\s*Segment\s*\d*', '', str(text), flags=re.IGNORECASE)

        # Hapus pemisah sub-unit seperti - atau / di akhir
        cleaned = re.split(r'\s*[-/]\s*|\s*\(', cleaned)[0].strip()
        return cleaned if cleaned else 'Layanan Tidak Diketahui'

    # 1. Cleaning Service Name (Menghapus tulisan SEGMENT agar menyatu)
    if 'service_name' in df_clean.columns:
        df_clean['service_name'] = df_clean['service_name'].apply(clean_segment_name)

    # 2. Cleaning Department (Menghapus tulisan SEGMENT)
    if 'department' in df_clean.columns:
        df_clean['department'] = df_clean['department'].apply(clean_segment_name)
        
    # 3. Format Nama Orang (Maksimal 2 Kata Depan & Title Case)
    def limit_two_words(name):
        """
        Tujuan: Memotong string nama menjadi maksimal dua kata pertama 
        dengan kapitalisasi Title Case untuk kerapian UI Dashboard.
        """
        if pd.isnull(name) or str(name).strip() in ['nan', 'None', '0', '-']:
            return 'Unknown'
        words = str(name).strip().split()
        return ' '.join(words[:2]).title()

    name_columns = ['created_by_name', 'updated_by_name', 'customer_name']
    for name_col in name_columns:
        if name_col in df_clean.columns:
            df_clean[name_col] = df_clean[name_col].apply(limit_two_words)

    # 4. Sanitasi Regex IP Address (IPv4)
     # Masking semua pola IP yang valid (misal: 192.168.1.1)
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    text_columns = ['remark', 'ticket_symptom', 'ticket_summary', 'ticket_rootcouse']
    
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).apply(
                lambda text: re.sub(ip_pattern, '[IP_PROTECTED]', text) if pd.notnull(text) else text
            )
            
    # 5. Masking Customer Email
    # Sedikit perbaikan dari regex OCR: mencari karakter sebelum & sesudah '@'
    if 'customer_email' in df_clean.columns:
        df_clean['customer_email'] = df_clean['customer_email'].astype(str).apply(
            lambda email: re.sub(r'([^@&]+)@([^@&]+)', r'***@\2', email) if '@' in str(email) else email
        )

    # 6. Ekstraksi Calendar Table (Replikasi DAX Power BI)
    # Menentukan kolom acuan tanggal (prioritas nama kolom umum)
    date_col = None
    for col in df_clean.columns:
        if str(col).strip().lower() in ['date_created_at', 'created_at', 'created_date', 'tanggal', 'date']:
            date_col = col
            break

    if date_col:
        # Konversi ke datetime
        df_clean['Date'] = pd.to_datetime(df_clean[date_col], errors='coerce')
        
        # Ekstraksi atribut waktu (Persis seperti fungsi ADDCOLUMNS DAX)
        df_clean['Year'] = df_clean['Date'].dt.year
        df_clean['Month_Number'] = df_clean['Date'].dt.month
        df_clean['Month'] = df_clean['Date'].dt.strftime('%B')
        df_clean['Quarter'] = 'Q' + df_clean['Date'].dt.quarter.astype(str)
        df_clean['Week_Number'] = df_clean['Date'].dt.isocalendar().week
        df_clean['Week_Day'] = df_clean['Date'].dt.strftime('%a')       # Mon, Tue, Wed
        df_clean['Week_Day_Num'] = df_clean['Date'].dt.dayofweek        # Monday = 0, Sunday = 6
        df_clean['Day'] = df_clean['Date'].dt.day
            
    return df_clean