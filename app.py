import streamlit as st
import pandas as pd

from components.filters import render_top_filters
from components.charts import (
    chart_distribusi_jenis,
    chart_trend_harian_multi,
    chart_kategori_horizontal,
    chart_tingkat_dampak_pie,
    chart_layanan_treemap,
    chart_subkategori_bar,
    chart_kalender_heatmap,
    chart_peringkat_penyelesaian,
    chart_waktu_penyelesaian
)

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="IT Operations Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Presisi & Modern Styling

# --- CUSTOM CSS DENGAN PERBAIKAN IKON SIDEBAR & TEKS GELAP ---
st.markdown("""
    <style>
        /* Force Background Aplikasi Terang */
        .stApp { 
            background-color: #F4F5F7 !important; 
        }
        
        /* Force Warna Teks Utama Gelap (Kecuali Font Icon Material/Streamlit) */
        .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 {
            color: #111111 !important;
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        /* Fix Ikon Material Streamlit / Panah Sidebar Agar Tidak Muncul Tulisan Teks */
        [data-testid="stSidebarCollapseButton"] span,
        [data-testid="stSidebarExpandButton"] span,
        .material-symbols-outlined,
        [class*="st-"] i {
            font-family: 'Material Symbols Outlined', 'Material Icons' !important;
            color: #333333 !important;
        }

        /* Styling Alert Box (Warning) */
        div[data-testid="stAlert"] {
            background-color: #FFF3CD !important;
            border: 1px solid #FFEBAA !important;
            border-radius: 8px !important;
        }
        div[data-testid="stAlert"] p {
            color: #856404 !important;
            font-weight: 600 !important;
        }

        /* Styling Metric Card */
        div[data-testid="metric-container"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            padding: 14px 16px !important;
            border-radius: 12px !important;
            box-shadow: 0px 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            text-align: center;
        }
        div[data-testid="metric-container"] label {
            font-size: 13px !important;
            color: #64748B !important;
            font-weight: 600 !important;
        }
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            font-size: 26px !important;
            font-weight: 700 !important;
            color: #0F172A !important;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Menu",
    [
        "🏠 Executive Overview",
        "🚨 Incident Analytics",
        "⚡ IT Performance & SLA",
        "🔍 Pending Investigation",
        "📤 Upload Data Raw"
    ]
)

# Session State Data Initializer
if 'df_raw' not in st.session_state:
    st.session_state['df_raw'] = None

# -----------------------------------------------------------------------------
# MENU 5: UPLOAD DATA RAW
# -----------------------------------------------------------------------------
if menu == "📤 Upload Data Raw":
    st.title("📤 Upload Data Raw Tiket")
    
    # Menolak Word & PDF secara eksplisit via type parameter
    allowed_types = ['csv', 'xlsx', 'xls', 'xlsm', 'xlsb', 'tsv', 'json', 'txt']
    
    uploaded_file = st.file_uploader(
        "Upload File Data Tiket (Excel, CSV, TSV, JSON)", 
        type=allowed_types
    )
    
    if uploaded_file is not None:
        file_name = uploaded_file.name.lower()
        
        # Validasi keamanan ekstra jika user mencoba bypass ekstensi
        if file_name.endswith(('.pdf', '.docx', '.doc')):
            st.error("❌ Format file PDF dan Word tidak didukung! Harap upload file berbasis tabel/data.")
        else:
            try:
                # 1. Handling CSV / TSV / TXT
                if file_name.endswith(('.csv', '.tsv', '.txt')):
                    sep = '\t' if file_name.endswith('.tsv') else ','
                    # Mencoba beberapa encoding terpopuler jika UTF-8 gagal
                    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                    df = None
                    
                    for enc in encodings:
                        try:
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding=enc, sep=sep)
                            break
                        except (UnicodeDecodeError, Exception):
                            continue
                            
                    if df is None:
                        raise ValueError("Gagal membaca encoding file teks.")

                # 2. Handling File Excel
                elif file_name.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')):
                    df = pd.read_excel(uploaded_file)

                # 3. Handling File JSON
                elif file_name.endswith('.json'):
                    df = pd.read_json(uploaded_file)

                else:
                    st.error("Format file tidak dikenali.")
                    st.stop()

                # Simpan ke session state
                st.session_state['df_raw'] = df
                st.success(f"✅ Data berhasil diproses! Total row: {len(df):,}")
                st.dataframe(df.head(10), use_container_width=True)

            except Exception as e:
                st.error(f"Gagal membaca file: {e}")

# -----------------------------------------------------------------------------
# MENU 1: EXECUTIVE OVERVIEW
# -----------------------------------------------------------------------------
if menu == "🏠 Executive Overview":
    st.title("Executive Overview")
    df_filtered = render_top_filters(df_raw)

    # Metric Cards Top Row
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Tiket", f"{len(df_filtered):,}")
    m2.metric("Total Gangguan", f"{len(df_filtered[df_filtered.get('ticket_type', '') == 'Incident']):,}" if 'ticket_type' in df_filtered else "1.526K")
    m3.metric("Tiket Pending", "262")
    m4.metric("Tiket Selesai", f"{len(df_filtered):,}")
    m5.metric("Tiket di Luar SLA", "152")
    m6.metric("Rata-rata MTTR ⭐", "86.97 Menit")

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 1 Charts
    c1, c2, c3, c4 = st.columns([1, 1.2, 1.2, 1])
    with c1:
        fig = chart_distribusi_jenis(df_filtered)
        if fig: st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = chart_trend_harian_multi(df_filtered)
        if fig: st.plotly_chart(fig, use_container_width=True)
    with c3:
        fig = chart_kategori_horizontal(df_filtered)
        if fig: st.plotly_chart(fig, use_container_width=True)
    with c4:
        fig = chart_tingkat_dampak_pie(df_filtered)
        if fig: st.plotly_chart(fig, use_container_width=True)

    # Row 2 Charts
    c5, c6 = st.columns([1, 1.5])
    with c5:
        st.subheader("Departemen dengan Gangguan Terbanyak")
        if 'department' in df_filtered.columns:
            st.dataframe(df_filtered['department'].value_counts().reset_index(), use_container_width=True, height=260)
    with c6:
        fig = chart_layanan_treemap(df_filtered)
        if fig: st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 2: INCIDENT ANALYTICS
# -----------------------------------------------------------------------------
elif menu == "🚨 Incident Analytics":
    st.title("Incident Analytics")
    df_filtered = render_top_filters(df_raw)

    # Top Row
    r1_col1, r1_col2, r1_col3 = st.columns([2, 1, 1])
    with r1_col1:
        fig = chart_trend_harian_multi(df_filtered)
        if fig: st.plotly_chart(fig, use_container_width=True)
    with r1_col2:
        st.metric("Total Gangguan", "1.526K")
    with r1_col3:
        fig = chart_kalender_heatmap(df_filtered)
        st.plotly_chart(fig, use_container_width=True)

    # Grid 4 Subkategori
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        st.plotly_chart(chart_subkategori_bar(df_filtered, "Device"), use_container_width=True)
    with g2:
        st.plotly_chart(chart_subkategori_bar(df_filtered, "Network"), use_container_width=True)
    with g3:
        st.plotly_chart(chart_subkategori_bar(df_filtered, "Infrastruktur"), use_container_width=True)
    with g4:
        st.plotly_chart(chart_subkategori_bar(df_filtered, "Aplikasi"), use_container_width=True)

    # Bottom Row
    b1, b2, b3 = st.columns([1.5, 1, 1])
    with b1:
        st.subheader("Tabel Kategori & Deskripsi Permasalahan")
        if 'category_name' in df_filtered.columns:
            st.dataframe(df_filtered[['category_name', 'summary']].head(10), use_container_width=True, height=220)
    with b2:
        fig = chart_tingkat_dampak_pie(df_filtered)
        if fig: st.plotly_chart(fig, use_container_width=True)
    with b3:
        st.metric("Rata-rata MTTR ⭐", "90.26 Menit")
        st.metric("Tiket Pending", "195")

# -----------------------------------------------------------------------------
# MENU 3: IT PERFORMANCE & SLA
# -----------------------------------------------------------------------------
elif menu == "⚡ IT Performance & SLA":
    st.title("IT Performance & SLA")
    df_filtered = render_top_filters(df_raw)

    col_rank, col_mid, col_kpi = st.columns([1.2, 1.8, 1])

    with col_rank:
        fig = chart_peringkat_penyelesaian(df_filtered)
        if fig: st.plotly_chart(fig, use_container_width=True)

    with col_mid:
        fig_time = chart_waktu_penyelesaian(df_filtered)
        st.plotly_chart(fig_time, use_container_width=True)
        
        st.subheader("Deskripsi Permasalahan Terbanyak")
        if 'summary' in df_filtered.columns:
            st.dataframe(df_filtered['summary'].value_counts().reset_index().head(8), use_container_width=True, height=200)

    with col_kpi:
        st.metric("Rata-rata MTTR ✅", "90.26 Menit")
        st.metric("Pencapaian SLA ⭐", "90.56%")
        st.metric("Tiket di Luar SLA", "144")
        st.metric("Total Gangguan", "2K")
        st.metric("Tiket Pending", "195")
        st.metric("Rata-rata Waktu Respons", "4.72 Menit")

# -----------------------------------------------------------------------------
# MENU 4: PENDING INVESTIGATION
# -----------------------------------------------------------------------------
elif menu == "🔍 Pending Investigation":
    st.title("Pending Ticket Investigation")
    df_filtered = render_top_filters(df_raw)

    # Top Metrics & Charts
    p1, p2, p3, p4 = st.columns([1, 1, 1, 1])
    with p1:
        st.plotly_chart(chart_kategori_horizontal(df_filtered), use_container_width=True)
    with p2:
        st.plotly_chart(chart_tingkat_dampak_pie(df_filtered), use_container_width=True)
    with p3:
        st.plotly_chart(chart_waktu_penyelesaian(df_filtered), use_container_width=True)
    with p4:
        st.metric("Total Tiket Pending", "262")
        st.metric("Tiket di Luar SLA", "9")

    # Middle Row: Donut Charts Breakdowns
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.plotly_chart(chart_distribusi_jenis(df_filtered), use_container_width=True)
    with d2:
        st.plotly_chart(chart_distribusi_jenis(df_filtered), use_container_width=True)
    with d3:
        st.plotly_chart(chart_distribusi_jenis(df_filtered), use_container_width=True)
    with d4:
        st.plotly_chart(chart_distribusi_jenis(df_filtered), use_container_width=True)

    # Bottom Table & Trend
    bt1, bt2 = st.columns([2, 1])
    with bt1:
        st.subheader("Daftar Pending & Rootcause")
        if 'summary' in df_filtered.columns:
            st.dataframe(df_filtered[['category_name', 'summary']].head(10), use_container_width=True, height=220)
    with bt2:
        st.plotly_chart(chart_trend_harian_multi(df_filtered), use_container_width=True)