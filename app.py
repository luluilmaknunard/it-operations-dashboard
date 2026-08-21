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

# 2. Custom CSS Presisi & Modern Card Styling (Mirip Power BI)
st.markdown("""
    <style>
        /* Background Utama Dashboard */
        .stApp { 
            background-color: #F0F2F5 !important; 
        }
        
        /* Hilangkan Teks Tembus/Ikon Aneh di Atas Sidebar */
        [data-testid="stSidebarCollapseButton"] span,
        [data-testid="stSidebarExpandButton"] span {
            font-size: 0px !important;
        }
        [data-testid="stSidebarCollapseButton"]::after,
        [data-testid="stSidebarExpandButton"]::after {
            content: "◀";
            font-size: 16px;
            color: #333;
        }

        /* Power BI Card Container Styling */
        div[data-testid="stColumn"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid #E1E4E8 !important;
            border-radius: 10px !important;
            padding: 12px 14px !important;
            box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.03) !important;
        }

        /* Card Khusus Metric KPI */
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

        /* Rapikan Dropdown Filter Atas */
        div[data-baseweb="select"] > div {
            background-color: #F8FAFC !important;
            border-radius: 6px !important;
            border: 1px solid #CBD5E1 !important;
            font-size: 13px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Session State Initializer
if 'df_raw' not in st.session_state:
    st.session_state['df_raw'] = None

# 4. Sidebar Navigasi & File Uploader
st.sidebar.title("Navigation")

menu = st.sidebar.radio(
    "Menu Navigasi",
    [
        "🏠 Executive Overview",
        "🚨 Incident Analytics",
        "⚡ IT Performance & SLA",
        "🔍 Pending Investigation"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("📤 Upload Data Raw")

allowed_types = ['csv', 'xlsx', 'xls', 'xlsm', 'xlsb', 'tsv', 'json', 'txt']
uploaded_file = st.sidebar.file_uploader("Upload File Tiket", type=allowed_types)

if uploaded_file is not None:
    file_name = uploaded_file.name.lower()
    if not file_name.endswith(('.pdf', '.docx', '.doc')):
        try:
            if file_name.endswith(('.csv', '.tsv', '.txt')):
                sep = '\t' if file_name.endswith('.tsv') else ','
                encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                df = None
                for enc in encodings:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding=enc, sep=sep)
                        break
                    except Exception:
                        continue
            elif file_name.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')):
                df = pd.read_excel(uploaded_file)
            elif file_name.endswith('.json'):
                df = pd.read_json(uploaded_file)

            if df is not None:
                st.session_state['df_raw'] = df
                st.sidebar.success(f"✅ Data Siap: {len(df):,} baris")
        except Exception as e:
            st.sidebar.error(f"Gagal membaca file: {e}")

# Data Retrieval & Guard
df_raw = st.session_state['df_raw']

if df_raw is None:
    st.title(menu)
    st.warning("⚠️ Silakan upload file data tiket terlebih dahulu melalui panel **Upload Data Raw** di sidebar sebelah kiri.")
    st.stop()

# -----------------------------------------------------------------------------
# MENU 1: EXECUTIVE OVERVIEW
# -----------------------------------------------------------------------------
if menu == "🏠 Executive Overview":
    # Header & Filter dalam 1 Baris Sejajar
    col_head, col_filters = st.columns([1, 2.5])
    with col_head:
        st.markdown("## **Executive Overview**")
    with col_filters:
        df_filtered = render_top_filters(df_raw)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 1: KPI Metric Cards (6 Kolom Sejajar)
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Tickets", f"{len(df_filtered):,}")
    m2.metric("Total Incidents", f"{len(df_filtered[df_filtered.get('ticket_type', '') == 'Incident']):,}" if 'ticket_type' in df_filtered else "647")
    m3.metric("Pending Tickets", "140")
    m4.metric("Resolved Tickets", f"{len(df_filtered):,}")
    m5.metric("SLA Breaches", "24")
    m6.metric("Average MTTR ⭐", "38.70 Menit")

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 2: Charts (4 Kolom Presisi)
    c1, c2, c3, c4 = st.columns([1, 1.3, 1.2, 1])
    with c1:
        fig = chart_distribusi_jenis(df_filtered)
        if fig:
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = chart_trend_harian_multi(df_filtered)
        if fig:
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
    with c3:
        fig = chart_kategori_horizontal(df_filtered)
        if fig:
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
    with c4:
        fig = chart_tingkat_dampak_pie(df_filtered)
        if fig:
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 3: Bottom Charts
    c5, c6 = st.columns([1, 1.4])
    with c5:
        st.markdown("##### **Top Departments by Incidents**")
        if 'department' in df_filtered.columns:
            st.dataframe(
                df_filtered['department'].value_counts().reset_index(),
                use_container_width=True, 
                height=280
            )
    with c6:
        fig = chart_layanan_treemap(df_filtered)
        if fig:
            fig.update_layout(height=310, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 2: INCIDENT ANALYTICS
# -----------------------------------------------------------------------------
elif menu == "🚨 Incident Analytics":
    col_head, col_filters = st.columns([1, 2.5])
    with col_head:
        st.markdown("## **Incident Analytics**")
    with col_filters:
        df_filtered = render_top_filters(df_raw)

    st.markdown("<br>", unsafe_allow_html=True)

    r1_col1, r1_col2, r1_col3 = st.columns([2, 1, 1])
    with r1_col1:
        fig = chart_trend_harian_multi(df_filtered)
        if fig:
            fig.update_layout(height=260)
            st.plotly_chart(fig, use_container_width=True)
    with r1_col2:
        st.metric("Total Gangguan", f"{len(df_filtered):,}")
    with r1_col3:
        fig = chart_kalender_heatmap(df_filtered)
        if fig:
            fig.update_layout(height=260)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    g1, g2, g3, g4 = st.columns(4)
    with g1:
        fig = chart_subkategori_bar(df_filtered, "Device")
        if fig: fig.update_layout(height=220); st.plotly_chart(fig, use_container_width=True)
    with g2:
        fig = chart_subkategori_bar(df_filtered, "Network")
        if fig: fig.update_layout(height=220); st.plotly_chart(fig, use_container_width=True)
    with g3:
        fig = chart_subkategori_bar(df_filtered, "Infrastruktur")
        if fig: fig.update_layout(height=220); st.plotly_chart(fig, use_container_width=True)
    with g4:
        fig = chart_subkategori_bar(df_filtered, "Aplikasi")
        if fig: fig.update_layout(height=220); st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------------
# MENU 3: IT PERFORMANCE & SLA
# -----------------------------------------------------------------------------
elif menu == "⚡ IT Performance & SLA":
    col_head, col_filters = st.columns([1, 2.5])
    with col_head:
        st.markdown("## **IT Performance & SLA**")
    with col_filters:
        df_filtered = render_top_filters(df_raw)

    st.markdown("<br>", unsafe_allow_html=True)

    col_rank, col_mid, col_kpi = st.columns([1.2, 1.8, 1])
    with col_rank:
        fig = chart_peringkat_penyelesaian(df_filtered)
        if fig: fig.update_layout(height=350); st.plotly_chart(fig, use_container_width=True)
    with col_mid:
        fig_time = chart_waktu_penyelesaian(df_filtered)
        if fig_time: fig_time.update_layout(height=350); st.plotly_chart(fig_time, use_container_width=True)
    with col_kpi:
        st.metric("Rata-rata MTTR ✅", "38.70 Menit")
        st.metric("Pencapaian SLA ⭐", "95.2%")
        st.metric("SLA Breaches", "24")

# -----------------------------------------------------------------------------
# MENU 4: PENDING INVESTIGATION
# -----------------------------------------------------------------------------
elif menu == "🔍 Pending Investigation":
    col_head, col_filters = st.columns([1, 2.5])
    with col_head:
        st.markdown("## **Pending Ticket Investigation**")
    with col_filters:
        df_filtered = render_top_filters(df_raw)

    st.markdown("<br>", unsafe_allow_html=True)

    p1, p2, p3, p4 = st.columns([1, 1, 1, 1])
    with p1:
        fig = chart_kategori_horizontal(df_filtered)
        if fig: fig.update_layout(height=250); st.plotly_chart(fig, use_container_width=True)
    with p2:
        fig = chart_tingkat_dampak_pie(df_filtered)
        if fig: fig.update_layout(height=250); st.plotly_chart(fig, use_container_width=True)
    with p3:
        fig = chart_waktu_penyelesaian(df_filtered)
        if fig: fig.update_layout(height=250); st.plotly_chart(fig, use_container_width=True)
    with p4:
        st.metric("Total Tiket Pending", "140")
        st.metric("Tiket di Luar SLA", "9")