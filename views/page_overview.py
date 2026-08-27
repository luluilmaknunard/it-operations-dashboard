import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.filters import render_top_filters
from components.charts import chart_department
from components.metrics import render_kpi_cards


# ============================================================
# HELPER
# ============================================================

def _find_column(df, candidates):
    """
    Mengambil nama kolom pertama yang tersedia.
    """

    if df is None or df.empty:
        return None

    for col in candidates:
        if col in df.columns:
            return col

    return None


# ============================================================
# MAIN RENDER
# ============================================================

def render(df_raw):

    # ========================================================
    # 0. VALIDASI DATA RAW
    # ========================================================

    if df_raw is None or df_raw.empty:

        st.warning(
            "Data raw tidak tersedia. "
            "Silakan upload file terlebih dahulu."
        )

        return

    # ========================================================
    # 1. HEADER
    # DESAIN DISESUAIKAN DENGAN INCIDENT ANALYTICS
    # ========================================================

    st.markdown(
        "## **📊 Executive Overview**"
    )

    # ========================================================
    # 2. TOP FILTER
    # ========================================================

    df_filtered = render_top_filters(
        df_raw,
        key_prefix="overview",
    )

    # ========================================================
    # 3. VALIDASI HASIL FILTER
    # ========================================================

    if df_filtered is None or df_filtered.empty:

        st.warning(
            "Data tidak tersedia untuk filter yang dipilih."
        )

        return

    # ========================================================
    # 4. CARI KOLOM UTAMA
    # ========================================================

    type_col = _find_column(
        df_filtered,
        [
            "ticket_type",
            "type",
            "ticketType",
            "ticket_type_name",
        ]
    )

    id_col = _find_column(
        df_filtered,
        [
            "ticketId",
            "ticket_id",
            "ticketID",
            "id",
            "ticket",
        ]
    )

    # ========================================================
    # 5. SPACING
    # ========================================================

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    # ========================================================
    # 6. SIX SCORECARDS METRICS
    #
    # KPI menggunakan df_filtered sehingga:
    #
    # All Unit
    # -> KPI seluruh data
    #
    # Unit tertentu
    # -> KPI mengikuti unit tersebut
    #
    # Logika MTTR berada di components/metrics.py
    # ========================================================

    render_kpi_cards(
        df_filtered
    )

    # ========================================================
    # 7. SPACING
    # ========================================================

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    # ========================================================
    # 8. BARIS 2
    # 4 VISUALISASI
    # ========================================================

    c1, c2, c3, c4 = st.columns(
        [1, 1.3, 1.2, 1],
        gap="small"
    )

    # ========================================================
    # 8.1 DONUT
    # DISTRIBUSI JENIS TIKET
    # ========================================================

    with c1:

        st.markdown(
            "##### **Distribusi Jenis Tiket**"
        )

        if type_col is not None:

            df_dist = (
                df_filtered[type_col]
                .astype(str)
                .str.strip()
                .replace(
                    {
                        "": "Tidak Diketahui",
                        "nan": "Tidak Diketahui",
                        "None": "Tidak Diketahui",
                    }
                )
                .value_counts()
                .reset_index()
            )

            df_dist.columns = [
                "Jenis",
                "Jumlah"
            ]

            if not df_dist.empty:

                fig_donut = px.pie(
                    df_dist,
                    values="Jumlah",
                    names="Jenis",
                    hole=0.6,
                    color_discrete_sequence=[
                        "#F28E2B",
                        "#4E79A7",
                        "#59A14F",
                        "#E15759",
                    ]
                )

                fig_donut.update_traces(
                    textinfo="percent+label",
                    showlegend=False
                )

                fig_donut.update_layout(
                    margin=dict(
                        l=10,
                        r=10,
                        t=10,
                        b=10
                    ),
                    height=230,
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                )

                st.plotly_chart(
                    fig_donut,
                    use_container_width=True,
                    config={
                        "displayModeBar": False,
                        "responsive": True
                    }
                )

            else:

                st.info(
                    "Data distribusi tiket tidak tersedia."
                )

        else:

            st.info(
                "Kolom ticket_type/type tidak ditemukan."
            )

    # ========================================================
    # 8.2 LINE CHART
    # TREN JUMLAH TIKET HARIAN
    # ========================================================

    with c2:

        st.markdown(
            "##### **Tren Jumlah Tiket Harian**"
        )

        date_col = _find_column(
            df_filtered,
            [
                "date_created_at",
                "created_at",
                "date_created",
                "created_date",
            ]
        )

        if (
            date_col is not None
            and type_col is not None
        ):

            df_trend = df_filtered.copy()

            df_trend["Tanggal"] = pd.to_datetime(
                df_trend[date_col],
                errors="coerce"
            ).dt.date

            df_trend = df_trend[
                df_trend["Tanggal"].notna()
            ].copy()

            if not df_trend.empty:

                daily_total = (
                    df_trend
                    .groupby("Tanggal")
                    .size()
                    .rename("Total Ticket")
                )

                daily_gangguan = (
                    df_trend[
                        df_trend[type_col]
                        .astype(str)
                        .str.contains(
                            "gangguan|incident",
                            case=False,
                            na=False
                        )
                    ]
                    .groupby("Tanggal")
                    .size()
                    .rename("Gangguan")
                )

                daily_request = (
                    df_trend[
                        df_trend[type_col]
                        .astype(str)
                        .str.contains(
                            "request|permintaan",
                            case=False,
                            na=False
                        )
                    ]
                    .groupby("Tanggal")
                    .size()
                    .rename("Request")
                )

                df_daily_all = (
                    pd.concat(
                        [
                            daily_total,
                            daily_gangguan,
                            daily_request,
                        ],
                        axis=1
                    )
                    .fillna(0)
                    .reset_index()
                )

                fig_trend = go.Figure()

                fig_trend.add_trace(
                    go.Scatter(
                        x=df_daily_all["Tanggal"],
                        y=df_daily_all["Total Ticket"],
                        name="Total Ticket",
                        line=dict(
                            color="#D32F2F",
                            width=2
                        )
                    )
                )

                fig_trend.add_trace(
                    go.Scatter(
                        x=df_daily_all["Tanggal"],
                        y=df_daily_all["Gangguan"],
                        name="Gangguan",
                        line=dict(
                            color="#F28E2B",
                            width=2
                        )
                    )
                )

                fig_trend.add_trace(
                    go.Scatter(
                        x=df_daily_all["Tanggal"],
                        y=df_daily_all["Request"],
                        name="Request",
                        line=dict(
                            color="#4E79A7",
                            width=2
                        )
                    )
                )

                fig_trend.update_layout(
                    margin=dict(
                        l=10,
                        r=10,
                        t=10,
                        b=10
                    ),
                    height=230,
                    paper_bgcolor="white",
                    plot_bgcolor="white",

                    xaxis_title=None,
                    yaxis_title="Jumlah",

                    hovermode="x unified"
                )

                st.plotly_chart(
                    fig_trend,
                    use_container_width=True,
                    config={
                        "displayModeBar": False,
                        "responsive": True
                    }
                )

            else:

                st.info(
                    "Tidak ada data tanggal yang valid."
                )

        else:

            st.info(
                "Data tanggal/tipe tidak lengkap."
            )

    # ========================================================
    # 8.3 BAR CHART
    # JUMLAH GANGGUAN PER KATEGORI
    # ========================================================

    with c3:

        st.markdown(
            "##### **Jumlah Gangguan per Kategori**"
        )

        cat4_col = _find_column(
            df_filtered,
            [
                "category_split_4",
                "detailSubCategory2",
                "category_name",
                "category",
            ]
        )

        if cat4_col is not None:

            df_cat4 = (
                df_filtered[cat4_col]
                .dropna()
                .astype(str)
                .str.strip()
            )

            df_cat4 = df_cat4[
                df_cat4 != ""
            ]

            df_cat4 = (
                df_cat4
                .value_counts()
                .head(5)
                .reset_index()
            )

            df_cat4.columns = [
                "Kategori",
                "Jumlah"
            ]

            df_cat4 = df_cat4.sort_values(
                by="Jumlah",
                ascending=True
            )

            if not df_cat4.empty:

                fig_cat4 = px.bar(
                    df_cat4,
                    x="Jumlah",
                    y="Kategori",
                    orientation="h",
                    text="Jumlah"
                )

                fig_cat4.update_traces(
                    marker_color="#D32F2F",
                    textposition="outside"
                )

                fig_cat4.update_layout(
                    margin=dict(
                        l=10,
                        r=25,
                        t=10,
                        b=10
                    ),
                    height=230,
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                    xaxis_title=None,
                    yaxis_title=None
                )

                st.plotly_chart(
                    fig_cat4,
                    use_container_width=True,
                    config={
                        "displayModeBar": False,
                        "responsive": True
                    }
                )

            else:

                st.info(
                    "Tidak ada data kategori."
                )

        else:

            st.info(
                "Kolom kategori tidak ditemukan."
            )

    # ========================================================
    # 8.4 PIE CHART
    # DISTRIBUSI TINGKAT DAMPAK
    # ========================================================

    with c4:

        st.markdown(
            "##### **Distribusi Tingkat Dampak**"
        )

        impact_col = _find_column(
            df_filtered,
            [
                "impact_name",
                "impact",
                "impact_level",
            ]
        )

        if impact_col is not None:

            df_impact = (
                df_filtered[impact_col]
                .astype(str)
                .str.strip()
                .replace(
                    {
                        "": "Tidak Diketahui",
                        "nan": "Tidak Diketahui",
                        "None": "Tidak Diketahui",
                    }
                )
                .value_counts()
                .reset_index()
            )

            df_impact.columns = [
                "Dampak",
                "Jumlah"
            ]

            if not df_impact.empty:

                fig_impact = px.pie(
                    df_impact,
                    values="Jumlah",
                    names="Dampak",
                    color_discrete_sequence=[
                        "#2CA02C",
                        "#FFBB78",
                        "#D62728",
                        "#9467BD",
                    ]
                )

                fig_impact.update_traces(
                    textinfo="percent+label",
                    showlegend=False
                )

                fig_impact.update_layout(
                    margin=dict(
                        l=10,
                        r=10,
                        t=10,
                        b=10
                    ),
                    height=230,
                    paper_bgcolor="white",
                    plot_bgcolor="white",
                )

                st.plotly_chart(
                    fig_impact,
                    use_container_width=True,
                    config={
                        "displayModeBar": False,
                        "responsive": True
                    }
                )

            else:

                st.info(
                    "Data tingkat dampak tidak tersedia."
                )

        else:

            st.info(
                "Kolom impact tidak ditemukan."
            )

    # ========================================================
    # 9. SPACING
    # ========================================================

    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )

    # ========================================================
    # 10. BARIS 3
    # DEPARTMENT + TREEMAP
    # ========================================================

    d1, d2 = st.columns(
        [1.2, 1.8],
        gap="small"
    )

    # ========================================================
    # 10.1 DEPARTMENT DENGAN GANGGUAN TERBANYAK
    # ========================================================

    with d1:

        st.markdown(
            "##### **Department dengan Gangguan**"
        )

        chart_department(
            df_filtered,
            key_prefix="overview"
        )

    # ========================================================
    # 10.2 TREEMAP
    # LAYANAN DENGAN LAPORAN GANGGUAN TERBANYAK
    # ========================================================

    with d2:

        st.markdown(
            "##### **Layanan dengan Laporan Gangguan Terbanyak**"
        )

        service_col = _find_column(
            df_filtered,
            [
                "service_name",
                "service",
                "nama_layanan",
            ]
        )

        if id_col is None:

            st.info(
                "Kolom ID tiket tidak ditemukan."
            )

        elif service_col is not None:

            df_service = (
                df_filtered
                .groupby(service_col)[id_col]
                .nunique()
                .reset_index()
            )

            df_service.columns = [
                "Layanan",
                "Jumlah Kasus"
            ]

            df_service = df_service[
                df_service["Jumlah Kasus"] > 0
            ]

            df_service["Layanan"] = (
                df_service["Layanan"]
                .astype(str)
                .str.strip()
            )

            df_service = df_service[
                ~df_service["Layanan"].isin(
                    [
                        "",
                        "nan",
                        "None",
                        "null",
                        "-"
                    ]
                )
            ]

            if not df_service.empty:

                fig_tree = px.treemap(
                    df_service,
                    path=["Layanan"],
                    values="Jumlah Kasus",
                    color_discrete_sequence=[
                        "#A61C1C",
                        "#D32F2F",
                        "#E53935",
                        "#EF5350"
                    ]
                )

                fig_tree.update_traces(
                    root_color="lightgrey",
                    textinfo="label+value",
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Jumlah Kasus: %{value:,}"
                        "<extra></extra>"
                    )
                )

                fig_tree.update_layout(
                    autosize=True,
                    paper_bgcolor="white",
                    height=420,
                    margin=dict(
                        l=5,
                        r=5,
                        t=5,
                        b=5
                    )
                )

                st.plotly_chart(
                    fig_tree,
                    use_container_width=True,
                    config={
                        "displayModeBar": False,
                        "responsive": True
                    }
                )

            else:

                st.info(
                    "Tidak ada data layanan."
                )

        else:

            st.info(
                "Kolom service_name tidak ditemukan."
            )