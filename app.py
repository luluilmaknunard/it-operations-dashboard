"""
Tujuan:
Menjadi titik masuk utama (entry point) untuk aplikasi Streamlit IT Operations Dashboard.
File ini mengatur konfigurasi halaman, memuat CSS global, mengelola state, 
serta merutekan pengguna ke halaman yang sesuai berdasarkan pilihan di sidebar.

Input:
Tidak ada input langsung secara programatik, namun file ini membaca state 
dan merespons input dari komponen sidebar (termasuk unggahan file).

Proses:
    - Mengatur konfigurasi dasar halaman web (judul, ikon, layout).
    - Menyuntikkan custom CSS untuk mempercantik tampilan antarmuka (kartu, sidebar).
    - Memanggil komponen sidebar untuk merender menu dan proses upload data.
    - Mengecek ketersediaan data mentah sebelum merender halaman.
    - Melakukan routing ke halaman spesifik berdasarkan menu yang dipilih pengguna.

Output:
Tampilan antarmuka web interaktif Streamlit di browser pengguna.

Catatan:
Pastikan struktur folder views dan components sudah sesuai agar routing 
halaman dapat berjalan dengan lancar tanpa error ModuleNotFoundError.
"""


import streamlit as st
import pandas as pd
import numpy as np

# 1. Import Komponen Sidebar & Semua View Halaman secara Langsung
from components.sidebar import render_sidebar
from views import (
    page_overview,
    page_incident,
    page_performance,
    page_pending
)

# 2. Konfigurasi Halaman Utama
st.set_page_config(
    page_title="IT Operations Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3. Custom CSS Global
st.markdown("""
    <style>
        .stApp { background-color: #F0F2F5 !important; }
        
        [data-testid="stSidebarCollapseButton"] span,
        [data-testid="stSidebarExpandButton"] span { font-size: 0px !important; }
        [data-testid="stSidebarCollapseButton"]::after,
        [data-testid="stSidebarExpandButton"]::after {
            content: "◀";
            font-size: 16px;
            color: #333;
        }

        div[data-testid="stColumn"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid #E1E4E8 !important;
            border-radius: 10px !important;
            padding: 12px 14px !important;
            box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.03) !important;
        }

        div[data-testid="metric-container"] {
            background-color: #FFFFFF !important;
            border: none !important;
            padding: 4px !important;
            box-shadow: none !important;
            text-align: center;
        }
        div[data-testid="metric-container"] label {
            font-size: 12px !important;
            color: #64748B !important;
            font-weight: 600 !important;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            font-size: 22px !important;
            font-weight: 700 !important;
            color: #111827 !important;
        }

        div[data-baseweb="select"] > div {
            background-color: #F8FAFC !important;
            border-radius: 6px !important;
            border: 1px solid #CBD5E1 !important;
            font-size: 13px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 4. Inisialisasi Session State
# Menyimpan raw data agar tidak hilang dan ter-reset saat halaman direfresh/berpindah

if 'df_raw' not in st.session_state:
    st.session_state['df_raw'] = None

# 5. Render Sidebar (Sekarang mengembalikan 2 variabel)
# Memanggil sidebar untuk memuat menu navigasi dan proses upload data

menu, df_raw = render_sidebar()

# 6. Guard Clause
if df_raw is None:
    st.title(menu)
    st.warning("⚠️ Silakan upload file data tiket terlebih dahulu melalui panel **Upload Data Raw** di sidebar sebelah kiri.")
    st.stop()

# 7. SAFE RENDERER HELPER
def safe_render(module, df, page_name):
    """
    Tujuan:
        Memastikan fungsi render dari modul view dapat dipanggil dengan aman tanpa crash.
        
    Input:
        module (obj): Objek modul Python yang akan dipanggil.
        df (pd.DataFrame): Dataframe mentah yang akan diproses di view.
        page_name (str): Nama halaman untuk keperluan log/pesan error.
        
    Proses:
        - Mengecek apakah modul memiliki fungsi `render()`.
        - Jika tidak ada, fallback mengecek apakah modul memiliki fungsi `main()`.
        - Jika keduanya tidak ada, munculkan pesan error di UI Streamlit.
        
    Output:
        Render UI dari halaman terkait, atau tampilan pesan error.
    """
    if hasattr(module, 'render'):
        module.render(df)
    elif hasattr(module, 'main'):
        module.main(df)
    else:
        st.error(f"❌ Error: Fungsi `render(df_raw)` tidak ditemukan di file `views/{page_name}.py`!")

# 8. Routing Halaman (Langsung kirim df_raw)
# Mengarahkan dan merender pengguna ke komponen tampilan yang sesuai berdasarkan menu
if menu == "Executive Overview":
    safe_render(page_overview, df_raw, "page_overview")
elif menu == "Incident Analytics":
    safe_render(page_incident, df_raw, "page_incident")
elif menu == "IT Performance & SLA":
    safe_render(page_performance, df_raw, "page_performance")
elif menu == "Pending Investigation":
    safe_render(page_pending, df_raw, "page_pending")