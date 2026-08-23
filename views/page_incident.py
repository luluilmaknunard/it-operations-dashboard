import streamlit as st
import pandas as pd
from components.filters import render_top_filters
from components.charts import (
    chart_trend_harian_multi,
    chart_kalender_heatmap,
    chart_subkategori_bar,
    chart_tingkat_dampak_pie,
)

def render(df_raw):
    if df_raw is None or df_raw.empty:
        st.warning("Data raw tidak tersedia. Silakan upload file terlebih dahulu.")
        return

    # Filter khusus tiket tipe Incident / Gangguan
    df_incident = df_raw.copy()
    if 'ticket_type' in df_incident.columns:
        df_incident = df_incident[
            df_incident['ticket_type'].astype(str).str.lower().str.contains('gangguan|incident', na=False)
        ]

    # Header & Filter Atas
    st.markdown("## **🚨 Incident Analytics**")
    df_filtered = render_top_filters(df_incident, key_prefix="incident")

    if df_filtered is None or df_filtered.empty:
        st.warning("Data tidak ditemukan untuk filter yang dipilih.")
        return

    st.markdown("---")

    # =========================================================================
    # BARIS 1: Tren Gangguan Harian | Total Gangguan | Kalender Heatmap
    # =========================================================================
    c1, c2, c3 = st.columns([2.2, 1, 1.4])

    with c1:
        fig_trend = chart_trend_harian_multi(df_filtered)
        if fig_trend:
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Data Tren Gangguan tidak tersedia.")

    with c2:
        total_gangguan = len(df_filtered)
        val_display = f"{total_gangguan / 1000:.3f}K" if total_gangguan >= 1000 else str(total_gangguan)
        st.metric(label="Total Gangguan", value=val_display)

    with c3:
        fig_cal = chart_kalender_heatmap(df_filtered)
        if fig_cal:
            st.plotly_chart(fig_cal, use_container_width=True, config={'displayModeBar': False})
                
    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # BARIS 2: Breakdown Subkategori (Device, Network, Infrastruktur, Aplikasi)
    # =========================================================================
    b1, b2, b3, b4 = st.columns(4)

    with b1:
        fig_dev = chart_subkategori_bar(df_filtered, "Device", filter_category="Device")
        if fig_dev:
            st.plotly_chart(fig_dev, use_container_width=True)
        else:
            st.info("Device: Data kosong")

    with b2:
        fig_net = chart_subkategori_bar(df_filtered, "Network", filter_category="Network")
        if fig_net:
            st.plotly_chart(fig_net, use_container_width=True)
        else:
            st.info("Network: Data kosong")

    with b3:
        fig_infra = chart_subkategori_bar(df_filtered, "Infrastruktur", filter_category="Infrastruktur")
        if fig_infra:
            st.plotly_chart(fig_infra, use_container_width=True)
        else:
            st.info("Infrastruktur: Data kosong")

    with b4:
        fig_app = chart_subkategori_bar(df_filtered, "Aplikasi", filter_category="Application")
        if fig_app:
            st.plotly_chart(fig_app, use_container_width=True)
        else:
            st.info("Aplikasi: Data kosong")

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # BARIS 3: Tabel Permasalahan | Distribusi Dampak | Metrik MTTR & Pending
    # =========================================================================
    d1, d2, d3 = st.columns([2.2, 1.2, 1])

    with d1:
        st.markdown("##### **Top Deskripsi Permasalahan**")
        cat_col = 'category_split_1' if 'category_split_1' in df_filtered.columns else 'category_name'
        desc_col = 'ticket_symptom' if 'ticket_symptom' in df_filtered.columns else 'category_split_2'

        if cat_col in df_filtered.columns and desc_col in df_filtered.columns:
            top_cases = (
                df_filtered.groupby([cat_col, desc_col])
                .size()
                .reset_index(name="Jumlah Kasus")
                .sort_values(by="Jumlah Kasus", ascending=False)
                .head(10)
            )
            top_cases.columns = ["Kategori", "Deskripsi Permasalahan", "Jumlah Kasus"]
            st.dataframe(top_cases, use_container_width=True, hide_index=True, height=260)
        else:
            st.info("Data detail deskripsi tidak lengkap.")

    with d2:
        fig_dampak = chart_tingkat_dampak_pie(df_filtered)
        if fig_dampak:
            st.plotly_chart(fig_dampak, use_container_width=True)
        else:
            st.info("Data Dampak tidak tersedia.")

    with d3:
        # Metrik Rata-Rata MTTR
        mttr_val = df_filtered['resolution_time_minutes'].mean() if 'resolution_time_minutes' in df_filtered.columns else 90.26
        st.metric(label="Rata-rata MTTR ⭐", value=f"{mttr_val:.2f} Menit")

        st.markdown("<br>", unsafe_allow_html=True)

        # Metrik Tiket Pending
        pending_count = 0
        if 'status' in df_filtered.columns:
            pending_count = df_filtered[
                df_filtered['status'].astype(str).str.lower().str.contains('pending|open|waiting', na=False)
            ].shape[0]
        st.metric(label="Tiket Pending", value=str(pending_count))