import pandas as pd

from src import (
    clean_sensitive_data,
    transform_data_and_kpi,
    refine_freetext_with_gemini,
    get_gemini_api_key,  
)

def run_test():
    print("=== 1. MEMBACA FILE DUMMY ===")
    try:
        df_raw = pd.read_excel("data_sample_test.xlsx")
        print(f"✓ Berhasil membaca 'data_sample_test.xlsx' ({len(df_raw)} baris)\n")
    except FileNotFoundError:
        print("x File 'data_sample_test.xlsx' belum ada. Jalankan 'generate_dummy_data.py' dulu!")
        return

    print("=== 2. PENGUJIAN DATA CLEANING ===")
    df_clean = clean_sensitive_data(df_raw)
    print(f"✓ Jumlah kolom setelah cleaning: {len(df_clean.columns)}\n")

    print("=== 3. PENGUJIAN TRANSFORMASI & KPI ===")
    df_transformed = transform_data_and_kpi(df_clean)
    
    # Cek Pemotongan Nama (Maks 2 Kata)
    print("[Sample Kolom Nama (Maksimal 2 Kata)]")
    print(df_transformed[['created_by_name', 'updated_by_name']].head(5))
    print("-" * 50)

    # Cek Kalkulasi SLA & Waktu
    print("\n[Sample Kalkulasi Waktu & SLA Status]")
    cols_time = ['response_time_minutes', 'resolution_time_minutes', 'sla_status']
    available_cols = [c for c in cols_time if c in df_transformed.columns]
    print(df_transformed[available_cols].head(5))
    print("-" * 50)

    # Cek Rule Classifier
    print("\n[Sample Hasil Rule-Based Classifier]")
    cols_class = ['ticket_type', 'network_component']
    available_class = [c for c in cols_class if c in df_transformed.columns]
    print(df_transformed[available_class].head(5))
    print("-" * 50)

    print("\n=== 4. PENGUJIAN GEMINI AI REFINEMENT ===")
    # Menjalankan AI hanya untuk 3 baris sampel agar hemat token
    df_ai_test = df_transformed.head(3).copy()
    df_final = refine_freetext_with_gemini(df_ai_test)
    
    print("✓ Proses AI Selesai. Hasil Klasifikasi AI:")
    print(df_final[available_class].head(3))
    print("\n🎉 SEMUA PENGUJIAN SELESAI & BERJALAN DENGAN BAIK!")

if __name__ == "__main__":
    run_test()