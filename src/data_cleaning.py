import re
import pandas as pd

def clean_sensitive_data(df: pd.DataFrame) -> pd.DataFrame:
    """Membersihkan IP, email, merapikan departemen/layanan dari kata SEGMENT, dan data kosong."""
    df_clean = df.copy()
    
    # Fungsi pembersih kata SEGMENT / Segment / angka pemisah
    def clean_segment_name(text):
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

    # 2. Cleaning Department (Menghapus tulisan SEGMENT agar menyatu kyk Foto 2)
    if 'department' in df_clean.columns:
        df_clean['department'] = df_clean['department'].apply(clean_segment_name)
        
    # 3. Format Nama Orang (Maksimal 2 Kata Depan & Title Case)
    def limit_two_words(name):
        if pd.isnull(name) or str(name).strip() in ['nan', 'None', '0', '-']:
            return 'Unknown'
        words = str(name).strip().split()
        return ' '.join(words[:2]).title()

    name_columns = ['created_by_name', 'updated_by_name', 'assigned_to_name', 'customer_name']
    for name_col in name_columns:
        if name_col in df_clean.columns:
            df_clean[name_col] = df_clean[name_col].apply(limit_two_words)

    # 4. Sanitasi Regex IP Address (IPv4)
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    text_columns = ['remark', 'ticket_symptom', 'ticket_summary', 'ticket_rootcouse']
    
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).apply(
                lambda text: re.sub(ip_pattern, '[IP_PROTECTED]', text) if pd.notnull(text) else text
            )
            
    # 5. Masking Customer Email
    if 'customer_email' in df_clean.columns:
        df_clean['customer_email'] = df_clean['customer_email'].astype(str).apply(
            lambda email: re.sub(r'([^@&]+)@([^@&]+)', r'***@\2', email) if '@' in str(email) else email
        )
            
    return df_clean