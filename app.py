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
if 'df_raw' not in st.session_state:
    st.session_state['df_raw'] = None

# 5. Render Sidebar (Sekarang mengembalikan 2 variabel)
menu, df_raw = render_sidebar()

# 6. Guard Clause
if df_raw is None:
    st.title(menu)
    st.warning("⚠️ Silakan upload file data tiket terlebih dahulu melalui panel **Upload Data Raw** di sidebar sebelah kiri.")
    st.stop()

# 7. SAFE RENDERER HELPER
def safe_render(module, df, page_name):
    if hasattr(module, 'render'):
        module.render(df)
    elif hasattr(module, 'main'):
        module.main(df)
    else:
        st.error(f"❌ Error: Fungsi `render(df_raw)` tidak ditemukan di file `views/{page_name}.py`!")

# 8. Routing Halaman (Langsung kirim df_raw)
if menu == "Executive Overview":
    safe_render(page_overview, df_raw, "page_overview")
elif menu == "Incident Analytics":
    safe_render(page_incident, df_raw, "page_incident")
elif menu == "IT Performance & SLA":
    safe_render(page_performance, df_raw, "page_performance")
elif menu == "Pending Investigation":
    safe_render(page_pending, df_raw, "page_pending")