import streamlit as st
import pandas as pd
from components.filters import render_top_filters
from components.charts import (
    chart_trend_harian_multi,
    chart_kalender_heatmap,
    chart_subkategori_bar,
    chart_tingkat_dampak_pie,
)

def render(df_classified):
    if df_classified is None or df_classified.empty:
        st.warning("Data raw tidak tersedia. Silakan upload file terlebih dahulu.")
        return

    # ============================================================
    # 1. FILTER MUTLAK: TIKET GANGGUAN SAJA
    # ============================================================
    ticket_col = 'ticket_type' if 'ticket_type' in df_classified.columns else ('type' if 'type' in df_classified.columns else None)
    
    if ticket_col and ticket_col in df_classified.columns:
        df_incident = df_classified[
            df_classified[ticket_col].astype(str).str.lower().str.contains('gangguan|incident', na=False)
        ].copy()
    else:
        df_incident = df_classified.copy()

    if df_incident.empty:
        st.warning("Tidak ada data tiket berjenis Gangguan.")
        return

    # Header & Filter Atas
    st.markdown("## **🚨 Incident Analytics**")
    df_filtered = render_top_filters(df_incident, key_prefix="incident")

    if df_filtered is None or df_filtered.empty:
        st.warning("Data tidak ditemukan untuk filter yang dipilih.")
        return

    st.markdown("---")

    # ============================================================
    # BARIS 1: Tren Gangguan Harian | Total Gangguan | Kalender Heatmap
    # ============================================================
    c1, c2, c3 = st.columns([2.2, 1, 1.4])

    with c1:
        fig_trend = chart_trend_harian_multi(df_filtered)
        if fig_trend:
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Data Tren Gangguan tidak tersedia.")

    with c2:
        total_gangguan = len(df_filtered)
        # Format angka 1775 menjadi 1.775K
        val_display = f"{total_gangguan / 1000:.3f}K".replace(".", ",") if total_gangguan >= 1000 else f"{total_gangguan:,}"
        st.metric(label="Total Gangguan", value=val_display)

    with c3:
        fig_cal = chart_kalender_heatmap(df_filtered)
        if fig_cal:
            st.plotly_chart(fig_cal, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Data Kalender tidak tersedia.")
                
    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # BARIS 2: 4 KATEGORI SPESIFIK (BAR CHART SUBKATEGORI)
    # ============================================================
    b1, b2, b3, b4 = st.columns(4)

    # 1. DEVICE
    with b1:
        df_dev = df_filtered.copy()
        target_col = 'category_split_3' if 'category_split_3' in df_dev.columns else 'category_name'
        
        # Filter berdasarkan kata kunci device jika ada
        if 'detailSubCategory2' in df_dev.columns:
            df_dev_filtered = df_dev[df_dev['detailSubCategory2'].astype(str).str.lower().str.contains('device', na=False)]
            if not df_dev_filtered.empty:
                df_dev = df_dev_filtered

        fig_dev = chart_subkategori_bar(df_dev, title_name="Device", custom_col=target_col)
        if fig_dev:
            st.plotly_chart(fig_dev, use_container_width=True)

    # 2. NETWORK COMPONENT
    with b2:
        df_net = df_filtered.copy()
        target_net = 'network_component' if 'network_component' in df_net.columns else ('category_split_3' if 'category_split_3' in df_net.columns else 'category_name')
        
        # Pembersihan outlier spesifik
        if 'category_split_2' in df_net.columns:
            df_net = df_net[~df_net['category_split_2'].astype(str).str.lower().isin(['software non os'])]
        if 'network_component' in df_net.columns:
            df_net = df_net[~df_net['network_component'].astype(str).str.lower().isin(['kendala aplikasi'])]

        fig_net = chart_subkategori_bar(df_net, title_name="Network Component", custom_col=target_net)
        if fig_net:
            st.plotly_chart(fig_net, use_container_width=True)

    # 3. INFRASTRUKTUR
    with b3:
        df_infra = df_filtered.copy()
        target_infra = 'category_split_3' if 'category_split_3' in df_infra.columns else 'category_name'
        
        if 'detailSubCategory2' in df_infra.columns:
            df_infra_filtered = df_infra[df_infra['detailSubCategory2'].astype(str).str.lower().str.contains('infrastructure|infrastruktur', na=False)]
            if not df_infra_filtered.empty:
                df_infra = df_infra_filtered

        fig_infra = chart_subkategori_bar(df_infra, title_name="Infrastruktur", custom_col=target_infra)
        if fig_infra:
            st.plotly_chart(fig_infra, use_container_width=True)

    # 4. APLIKASI
    with b4:
        df_app = df_filtered.copy()
        target_app = 'category_split_2' if 'category_split_2' in df_app.columns else 'category_name'
        
        if 'detailSubCategory2' in df_app.columns:
            df_app_filtered = df_app[df_app['detailSubCategory2'].astype(str).str.lower().str.contains('application|aplikasi', na=False)]
            if not df_app_filtered.empty:
                df_app = df_app_filtered

        fig_app = chart_subkategori_bar(df_app, title_name="Aplikasi", custom_col=target_app)
        if fig_app:
            st.plotly_chart(fig_app, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # BARIS 3: Tabel Permasalahan | Distribusi Dampak | Metrik MTTR & Pending
    # ============================================================
    d1, d2, d3 = st.columns([2.2, 1.2, 1])

    with d1:
        st.markdown("##### **Top Deskripsi Permasalahan**")
        cat_col = 'category_split_1' if 'category_split_1' in df_filtered.columns else 'category_name'
        desc_col = 'ticket_symptom' if 'ticket_symptom' in df_filtered.columns else ('category_split_3' if 'category_split_3' in df_filtered.columns else 'category_split_2')

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
        mttr_col = 'mttr_minutes' if 'mttr_minutes' in df_filtered.columns else ('resolution_time_minutes' if 'resolution_time_minutes' in df_filtered.columns else None)
        mttr_val = df_filtered[mttr_col].mean() if (mttr_col and mttr_col in df_filtered.columns) else 0.0
        st.metric(label="Rata-rata MTTR ⭐", value=f"{mttr_val:.2f} Menit")

        st.markdown("<br>", unsafe_allow_html=True)

        pending_count = 0
        status_col = 'ticket_status_name' if 'ticket_status_name' in df_filtered.columns else ('status' if 'status' in df_filtered.columns else None)
        if status_col and status_col in df_filtered.columns:
            pending_count = df_filtered[
                df_filtered[status_col].astype(str).str.lower().str.contains('pending|waiting', na=False)
            ].shape[0]
        st.metric(label="Tiket Pending", value=f"{pending_count:,}")