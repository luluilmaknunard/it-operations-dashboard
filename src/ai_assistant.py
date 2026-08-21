import os
import json
import pandas as pd
from google import genai
from google.genai import types

def refine_freetext_with_gemini(df: pd.DataFrame, api_key: str = None) -> pd.DataFrame:
    """
    Menggunakan Gemini API gratis untuk mengklasifikasikan freetext tiket 
    yang masih ambigu atau membutuhkan analisis mendalam.
    """
    if df is None or df.empty:
        return df

    # Ambil API key dari parameter atau environment variable
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        print("API Key Gemini tidak ditemukan. Menggunakan klasifikasi rule-based.")
        return df

    client = genai.Client(api_key=key)
    df_ai = df.copy()

    # Filter baris yang terindikasi butuh klasifikasi AI (contoh: yang masuk 'Network Lainnya')
    mask_ai = df_ai['network_component'] == 'Network Lainnya'
    indices_to_process = df_ai[mask_ai].index

    for idx in indices_to_process:
        row = df_ai.loc[idx]
        
        # Gabungkan teks deskripsi tiket
        symptom = str(row.get('ticket_symptom', ''))
        summary = str(row.get('ticket_summary', ''))
        remark = str(row.get('remark', ''))
        rootcause = str(row.get('ticket_rootcouse', ''))

        text_input = f"Symptom: {symptom} | Summary: {summary} | Remark: {remark} | Rootcause: {rootcause}"

        prompt = f"""
        Analisis teks tiket gangguan/layanan IT berikut:
        "{text_input}"

        Klasifikasikan ke dalam format JSON dengan opsi terbatas:
        1. "ticket_type": Pilih salah satu ["Gangguan", "Request"]
        2. "network_component": Pilih salah satu [
            "LAN Infrastructure", "Internet", "VPN", "IP Address", 
            "DNS", "Router / Mikrotik", "Website Access", 
            "Server / Network Service", "Network Lainnya"
        ]
        """

        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            # Parsing respons JSON dari AI
            res_json = json.loads(response.text)
            
            if 'ticket_type' in res_json:
                df_ai.at[idx, 'ticket_type'] = res_json['ticket_type']
            if 'network_component' in res_json:
                df_ai.at[idx, 'network_component'] = res_json['network_component']

        except Exception as e:
            print(f"Gagal memproses baris {idx} dengan Gemini: {e}")
            continue

    return df_ai