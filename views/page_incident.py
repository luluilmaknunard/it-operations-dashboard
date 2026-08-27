import streamlit as st
import pandas as pd
from components.filters import render_top_filters
from components.charts import (
    chart_trend_harian_multi,
    calendar_heatmap,
    chart_subkategori_bar,
    chart_tingkat_dampak_pie,
    pick_best_column,
)


def _match_bucket(series, keyword):
    """Cocokkan nilai detailSubCategory2 dengan keyword, case & whitespace-insensitive."""
    return series.astype(str).str.strip().str.lower() == keyword


def render(df_classified):
    if df_classified is None or df_classified.empty:
        st.warning("Data raw tidak tersedia. Silakan upload file terlebih dahulu.")
        return

    # ============================================================
    # 1. FILTER MUTLAK: TIKET GANGGUAN SAJA (REQUEST DIKELUARKAN)
    # ============================================================
    ticket_col = 'ticket_type' if 'ticket_type' in df_classified.columns else 'type'

    if ticket_col in df_classified.columns:
        df_incident = df_classified[
            df_classified[ticket_col].astype(str).str.strip().str.lower().str.contains('gangguan|incident', na=False)
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
    # BARIS 1: TREN | 3 KPI | KALENDER
    # ============================================================

    c1, c2, c3 = st.columns([2.2, 0.9, 1.8])

    # ------------------------------------------------------------
    # 1. TREN GANGGUAN HARIAN
    # ------------------------------------------------------------
    with c1:
        fig_trend = chart_trend_harian_multi(df_filtered)

        if fig_trend:
            st.plotly_chart(
                fig_trend,
                use_container_width=True,
                config={"displayModeBar": False}
            )
        else:
            st.info("Data Tren Gangguan tidak tersedia.")


    # ------------------------------------------------------------
    # 2. 3 KPI DI TENGAH - CARD VERTIKAL
    # ------------------------------------------------------------
    with c2:

        # CSS khusus KPI tengah
        st.markdown("""
        <style>
        .kpi-card {
            background-color: white;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 14px 14px;
            margin-bottom: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }

        .kpi-label {
            font-size: 12px;
            color: #333333;
            margin-bottom: 7px;
        }

        .kpi-value {
            font-size: 25px;
            font-weight: 400;
            color: #222222;
            line-height: 1.1;
            white-space: nowrap;
        }

        .kpi-value-small {
            font-size: 22px;
            font-weight: 400;
            color: #222222;
            line-height: 1.1;
            white-space: nowrap;
        }
        </style>
        """, unsafe_allow_html=True)

        # ========================================================
        # TOTAL GANGGUAN
        # ========================================================
        total_gangguan = len(df_filtered)

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Gangguan</div>
                <div class="kpi-value">{total_gangguan:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ========================================================
        # RATA-RATA MTTR
        # ========================================================
        mttr_val = (
            df_filtered["mttr_minutes"].mean()
            if "mttr_minutes" in df_filtered.columns
            else None
        )

        if mttr_val is not None and pd.notna(mttr_val):
            mttr_display = f"{round(mttr_val):,} Menit"
        else:
            mttr_display = "N/A"

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Rata-rata MTTR ⭐</div>
                <div class="kpi-value-small">{mttr_display}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ========================================================
        # TIKET PENDING
        # ========================================================
        pending_count = 0

        if "pending_status" in df_filtered.columns:

            pending_count = int(
                (
                    df_filtered["pending_status"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    == "pending"
                ).sum()
            )

        elif "ticket_status_name" in df_filtered.columns:

            pending_count = int(
                df_filtered[
                    df_filtered["ticket_status_name"]
                    .astype(str)
                    .str.lower()
                    .str.contains(
                        "pending|open|waiting",
                        na=False
                    )
                ].shape[0]
            )

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Tiket Pending</div>
                <div class="kpi-value">{pending_count:,}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ------------------------------------------------------------
        # 3. CALENDAR HEATMAP
        # ------------------------------------------------------------
        with c3:

            fig_cal = calendar_heatmap(
                df_filtered
            )

            if fig_cal is not None:

                fig_cal.update_layout(
                    height=350,
                    margin=dict(
                        l=55,
                        r=15,
                        t=75,
                        b=30
                    )
                )

                st.plotly_chart(
                    fig_cal,
                    use_container_width=True,
                    config={
                        "displayModeBar": False
                    }
                )

            else:

                st.info(
                    "Data kalender tidak tersedia."
                )

        st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # BARIS 2: 4 KATEGORI SPESIFIK (Device / Network / Infrastruktur / Aplikasi)
    #
    # detailSubCategory2 = kolom bucket bersih dari dataset asli (Device,
    # Network, Infrastructure, Application). Item di dalam tiap bucket dipetik
    # dari detailSubCategory (deskripsi masalah spesifik) atau kolom terkait,
    # dengan fallback ke category_split_N kalau kolom aslinya tidak ada.
    # ============================================================
    has_bucket_col = 'detailSubCategory2' in df_filtered.columns

    b1, b2, b3, b4 = st.columns(4)

    # 1. DEVICE
    with b1:
        df_dev = df_filtered.copy()
        if has_bucket_col:
            df_dev = df_dev[_match_bucket(df_dev['detailSubCategory2'], 'device')]

        fig_dev = chart_subkategori_bar(
            df_dev, title_name="Device",
            custom_col=["detailSubCategory", "category_split_3", "category_name"],
        )
        if fig_dev:
            st.plotly_chart(fig_dev, use_container_width=True)
        else:
            st.caption("**Device**")
            st.info("Tidak ada data.")

    # 2. NETWORK COMPONENT (hasil klasifikasi ML network_component)
    with b2:
        df_net = df_filtered.copy()
        if has_bucket_col:
            df_net = df_net[_match_bucket(df_net['detailSubCategory2'], 'network')]

        # Exclude noise (kendala aplikasi yang salah kebucket network)
        if 'category' in df_net.columns:
            df_net = df_net[~df_net['category'].astype(str).str.lower().isin(['software non os'])]
        if 'network_component' in df_net.columns:
            df_net = df_net[~df_net['network_component'].astype(str).str.lower().isin(['kendala aplikasi'])]

        fig_net = chart_subkategori_bar(
            df_net, title_name="Network Component",
            custom_col=["network_component", "detailSubCategory", "category_split_3"],
        )
        if fig_net:
            st.plotly_chart(fig_net, use_container_width=True)
        else:
            st.caption("**Network**")
            st.info("Tidak ada data.")

    # 3. INFRASTRUKTUR
    with b3:
        df_infra = df_filtered.copy()
        if has_bucket_col:
            df_infra = df_infra[_match_bucket(df_infra['detailSubCategory2'], 'infrastructure')]

        fig_infra = chart_subkategori_bar(
            df_infra, title_name="Infrastruktur",
            custom_col=["detailSubCategory", "category_split_3", "category_name"],
        )
        if fig_infra:
            st.plotly_chart(fig_infra, use_container_width=True)
        else:
            st.caption("**Infrastruktur**")
            st.info("Tidak ada data.")

    # 4. APLIKASI
    with b4:
        df_app = df_filtered.copy()
        if has_bucket_col:
            df_app = df_app[_match_bucket(df_app['detailSubCategory2'], 'application')]

        fig_app = chart_subkategori_bar(
            df_app, title_name="Aplikasi",
            custom_col=["category", "subCategory", "category_split_1", "category_split_2"],
        )
        if fig_app:
            st.plotly_chart(fig_app, use_container_width=True)
        else:
            st.caption("**Aplikasi**")
            st.info("Tidak ada data.")

    st.markdown("<br>", unsafe_allow_html=True)

    # BARIS 3: Tabel Permasalahan | Distribusi Dampak | Metrik MTTR & Pending
    d1, d2 = st.columns([3.2, 1.2])

    with d1:
        st.markdown("##### **Top Deskripsi Permasalahan**")
        cat_col = pick_best_column(df_filtered, ["detailSubCategory", "category_split_1", "category_name"])
        desc_col = pick_best_column(df_filtered, ["ticket_symptom", "subCategory", "category_split_2"])

        if cat_col and desc_col:
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