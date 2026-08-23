import streamlit as st
from components.filters import render_top_filters
from components.metrics import render_kpi_cards
from components.charts import (
    chart_distribusi_jenis,
    chart_trend_harian_multi,
    chart_kategori_horizontal,
    chart_tingkat_dampak_pie,
    chart_layanan_treemap,
)
from src.ai_assistant import generate_executive_summary


def render(df_raw):
    if df_raw is None or df_raw.empty:
        st.warning("Data raw tidak tersedia. Silakan upload file terlebih dahulu.")
        return

    # 1. Header & Filter Utama
    col_head, col_filters = st.columns([1, 2.5])
    with col_head:
        st.markdown("## **Executive Overview**")
    with col_filters:
        # Menghasilkan dataframe yang sudah terfilter berdasarkan filter atas
        df_filtered = render_top_filters(df_raw, key_prefix="overview")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Metric Cards (KPI)
    # Cukup panggil satu kali dari komponen metrics
    render_kpi_cards(df_filtered)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Row 1 Charts (4 Kolom) dengan Penanganan Aman (Null-Safe)
    c1, c2, c3, c4 = st.columns([1, 1.3, 1.2, 1])

    with c1:
        fig_dist = chart_distribusi_jenis(df_filtered)
        if fig_dist is not None:
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("Data Distribusi Jenis Tiket tidak tersedia.")

    with c2:
        fig_trend = chart_trend_harian_multi(df_filtered)
        if fig_trend is not None:
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Data Tren Harian tidak tersedia.")

    with c3:
        fig_kat = chart_kategori_horizontal(df_filtered)
        if fig_kat is not None:
            st.plotly_chart(fig_kat, use_container_width=True)
        else:
            st.info("Data Kategori Gangguan tidak tersedia.")

    with c4:
        fig_dampak = chart_tingkat_dampak_pie(df_filtered)
        if fig_dampak is not None:
            st.plotly_chart(fig_dampak, use_container_width=True)
        else:
            st.info("Data Tingkat Dampak tidak tersedia.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Row 2: AI Summary & Treemap
    col_ai, col_tree = st.columns([1, 1.4])

    with col_ai:
        st.markdown("##### **🤖 AI Executive Summary**")
        try:
            summary_text = generate_executive_summary(df_filtered)
            st.info(summary_text)
        except Exception as e:
            st.error(f"Gagal memuat ringkasan AI: {e}")

    with col_tree:
        fig_tree = chart_layanan_treemap(df_filtered)
        if fig_tree is not None:
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("Data Treemap Layanan tidak tersedia.")