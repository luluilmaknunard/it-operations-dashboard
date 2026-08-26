import streamlit as st
import pandas as pd

from components.filters import render_top_filters

from components.charts import (
    chart_peringkat_penyelesaian,
    chart_tingkat_dampak_bar,
    chart_pending_member,
    chart_waktu_penyelesaian,
    render_problem_table,
    get_sla_achievement,
    get_avg_response,
    find_column,
)


# ============================================================
# HELPER
# ============================================================

def _first_existing_column(df, candidates):
    """
    Mengambil nama kolom pertama yang tersedia.
    """
    if df is None or df.empty:
        return None

    for col in candidates:
        if col in df.columns:
            return col

    return None


def _numeric_mean(df, column):
    """
    Mengambil rata-rata dari kolom numerik.
    """
    if column is None or column not in df.columns:
        return None

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    values = values[
        values.notna()
        & (values >= 0)
    ]

    if values.empty:
        return None

    return float(values.mean())


def _numeric_sum(df, column):
    """
    Menjumlahkan kolom numerik / flag.
    Mendukung nilai 0/1, True/False, dan angka.
    """
    if column is None or column not in df.columns:
        return 0

    series = df[column]

    # Boolean
    if pd.api.types.is_bool_dtype(series):
        return int(series.sum())

    # Numeric
    values = pd.to_numeric(
        series,
        errors="coerce"
    )

    if values.notna().any():
        return int(values.fillna(0).sum())

    # Fallback string flag
    normalized = (
        series
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return int(
        normalized.isin(
            [
                "1",
                "true",
                "yes",
                "y",
                "pending",
                "breach"
            ]
        ).sum()
    )


def _count_unique(df, column):
    """
    Menghitung jumlah ticket unik.
    """
    if df is None or df.empty:
        return 0

    if column is None or column not in df.columns:
        return int(len(df))

    values = df[column].dropna()

    if values.empty:
        return int(len(df))

    return int(values.nunique())


# ============================================================
# KPI CARD
# ============================================================

def render_kpi_card(
    label,
    value,
    suffix=None,
    icon=None
):
    """
    Render KPI menggunakan st.html()
    supaya HTML tidak terbaca sebagai code block.
    """

    display_label = str(label)

    if icon:
        display_label = f"{display_label} {icon}"

    display_value = str(value)

    if suffix:
        display_value = f"{display_value} {suffix}"

    html = f"""
<div class="performance-kpi-card">
    <div class="performance-kpi-label">{display_label}</div>
    <div class="performance-kpi-value">{display_value}</div>
</div>
"""

    st.html(html)


# ============================================================
# CSS KPI
# ============================================================

def render_kpi_css():

    st.html(
        """
<style>
.performance-kpi-card {
    width: 100%;
    box-sizing: border-box;

    background: #ffffff;

    border: 1px solid #d9d9d9;
    border-radius: 14px;

    padding: 18px 20px;
    margin-bottom: 14px;

    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.performance-kpi-label {
    font-size: 14px;
    font-weight: 400;

    color: #333333;

    margin-bottom: 10px;

    line-height: 1.35;
}

.performance-kpi-value {
    font-size: 28px;
    font-weight: 500;

    color: #111111;

    line-height: 1.2;

    word-break: break-word;
}
</style>
"""
    )


# ============================================================
# MAIN RENDER
# ============================================================

def render(df_raw):

    # ========================================================
    # 0. VALIDASI DATA
    # ========================================================

    if df_raw is None or df_raw.empty:

        st.warning(
            "Data raw tidak tersedia. "
            "Silakan upload file terlebih dahulu."
        )

        return

    # ========================================================
    # 1. FILTER MUTLAK
    # PERFORMANCE HANYA UNTUK GANGGUAN / INCIDENT
    # ========================================================

    ticket_col = _first_existing_column(
        df_raw,
        [
            "ticket_type",
            "type",
        ]
    )

    if ticket_col is None:

        st.warning(
            "Kolom ticket_type/type tidak ditemukan."
        )

        return

    df_performance = df_raw[
        df_raw[ticket_col]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.contains(
            "gangguan|incident",
            na=False
        )
    ].copy()

    if df_performance.empty:

        st.warning(
            "Tidak ada data tiket Gangguan/Incident."
        )

        return

    # ========================================================
    # 2. HEADER
    # ========================================================

    st.markdown(
        "## ⚡ IT Performance & SLA"
    )

    # ========================================================
    # 3. FILTER ATAS
    # ========================================================

    df_filtered = render_top_filters(
        df_performance,
        key_prefix="perf"
    )

    if df_filtered is None or df_filtered.empty:

        st.warning(
            "Data tidak tersedia untuk filter yang dipilih."
        )

        return

    # ========================================================
    # 4. SLICER ANGGOTA
    # ========================================================

    member_col = find_column(
        df_filtered,
        [
            "member",
            "member_name",
            "member name",
            "nama member",
            "nama anggota",

            "agent",
            "agent_name",
            "agent name",
            "nama agent",

            "technician",
            "technician_name",
            "technician name",
            "nama teknisi",
            "teknisi",

            "pic",
            "pic_name",
            "nama pic",

            "updated_by_name",
        ]
    )

    selected_member = "All"

    if member_col is not None:

        member_list = (
            df_filtered[member_col]
            .dropna()
            .astype(str)
            .str.strip()
        )

        member_list = sorted(
            [
                x
                for x in member_list.unique().tolist()
                if x
                and x.lower() not in [
                    "nan",
                    "none",
                    "null",
                    "-"
                ]
            ]
        )

        member_options = [
            "All"
        ] + member_list

        selected_member = st.selectbox(
            "Anggota",
            member_options,
            key="performance_member"
        )

        if selected_member != "All":

            df_filtered = df_filtered[
                df_filtered[member_col]
                .astype(str)
                .str.strip()
                == selected_member
            ].copy()

    if df_filtered is None or df_filtered.empty:

        st.warning(
            "Tidak ada data untuk anggota yang dipilih."
        )

        return

    # ========================================================
    # 5. LAYOUT UTAMA
    # ========================================================

    middle, right = st.columns(
        [4.5, 1.5],
        gap="small"
    )

    # ========================================================
    # 6. PANEL KIRI / VISUALISASI
    # ========================================================

    with middle:

        # ====================================================
        # BARIS ATAS
        # ====================================================

        top1, top2, top3 = st.columns(
            [1.25, 1, 1],
            gap="small"
        )

        # ====================================================
        # 6.1 PERINGKAT PENYELESAIAN
        # ====================================================

        with top1:

            fig_rank = chart_peringkat_penyelesaian(
                df_filtered
            )

            if fig_rank is not None:

                fig_rank.update_layout(
                    title=dict(
                        text="Peringkat Penyelesaian Tiket",
                        x=0.5,
                        xanchor="center"
                    ),
                    height=400,
                    margin=dict(
                        l=10,
                        r=30,
                        t=55,
                        b=20
                    )
                )

                st.plotly_chart(
                    fig_rank,
                    use_container_width=True,
                    config={
                        "displayModeBar": False
                    }
                )

            else:

                st.info(
                    "Data peringkat penyelesaian tidak tersedia."
                )

        # ====================================================
        # 6.2 TINGKAT DAMPAK - BAR
        # ====================================================

        with top2:

            fig_impact = chart_tingkat_dampak_bar(
                df_filtered
            )

            if fig_impact is not None:

                fig_impact.update_layout(
                    title=dict(
                        text="Tingkat Dampak",
                        x=0.5,
                        xanchor="center"
                    ),
                    height=400,
                    margin=dict(
                        l=10,
                        r=10,
                        t=55,
                        b=20
                    )
                )

                st.plotly_chart(
                    fig_impact,
                    use_container_width=True,
                    config={
                        "displayModeBar": False
                    }
                )

            else:

                st.info(
                    "Data tingkat dampak tidak tersedia."
                )

        # ====================================================
        # 6.3 TOP 3 MEMBER PENDING
        # ====================================================

        with top3:

            fig_pending = chart_pending_member(
                df_filtered
            )

            if fig_pending is not None:

                fig_pending.update_layout(
                    title=dict(
                        text="Top 3 Anggota Pending",
                        x=0.5,
                        xanchor="center"
                    ),
                    height=400,
                    margin=dict(
                        l=10,
                        r=30,
                        t=55,
                        b=20
                    )
                )

                st.plotly_chart(
                    fig_pending,
                    use_container_width=True,
                    config={
                        "displayModeBar": False
                    }
                )

            else:

                st.info(
                    "Data pending tidak tersedia."
                )

        # ====================================================
        # 6.4 DISTRIBUSI WAKTU PENYELESAIAN
        # ====================================================

        st.markdown(
            "<br>",
            unsafe_allow_html=True
        )

        fig_waktu = chart_waktu_penyelesaian(
            df_filtered
        )

        if fig_waktu is not None:

            fig_waktu.update_layout(
                title=dict(
                    text="Distribusi Waktu Penyelesaian Tiket",
                    x=0.5,
                    xanchor="center"
                ),
                height=300,
                margin=dict(
                    l=10,
                    r=30,
                    t=50,
                    b=30
                )
            )

            st.plotly_chart(
                fig_waktu,
                use_container_width=True,
                config={
                    "displayModeBar": False
                }
            )

        else:

            st.info(
                "Data waktu penyelesaian tidak tersedia."
            )

        # ====================================================
        # 6.5 DESKRIPSI PERMASALAHAN
        # ====================================================

        st.markdown(
            "<br>",
            unsafe_allow_html=True
        )

        render_problem_table(
            df_filtered
        )

    # ========================================================
    # 7. PANEL KANAN / KPI
    # ========================================================

    with right:

        # ====================================================
        # CSS
        # ====================================================

        render_kpi_css()

        # ====================================================
        # CARI ID TICKET
        # ====================================================

        id_col = _first_existing_column(
            df_filtered,
            [
                "ticketId",
                "ticket_id",
                "id",
                "ticket"
            ]
        )

        # ====================================================
        # 1. TOTAL GANGGUAN
        # ====================================================

        total_gangguan = _count_unique(
            df_filtered,
            id_col
        )

        render_kpi_card(
            "Total Gangguan",
            f"{total_gangguan:,}"
        )

        # ====================================================
        # 2. RATA-RATA MTTR
        # ====================================================

        mttr_col = _first_existing_column(
            df_filtered,
            [
                "mttr_minutes",
                "MTTR_minutes",
                "mttr",
                "MTTR"
            ]
        )

        avg_mttr = _numeric_mean(
            df_filtered,
            mttr_col
        )

        render_kpi_card(
            "Rata-rata MTTR",
            (
                f"{avg_mttr:,.2f}"
                if avg_mttr is not None
                else "N/A"
            ),
            suffix="Menit",
            icon="⭐"
        )

        # ====================================================
        # 3. TIKET PENDING
        # ====================================================

        pending_count_col = _first_existing_column(
            df_filtered,
            [
                "pending_flag",
                "is_pending",
                "ticket_pending",
                "pending_count"
            ]
        )

        if pending_count_col is not None:

            pending = _numeric_sum(
                df_filtered,
                pending_count_col
            )

        else:

            # Fallback berdasarkan date_pending
            if "date_pending" in df_filtered.columns:

                pending = int(
                    df_filtered["date_pending"]
                    .notna()
                    .sum()
                )

            # Fallback berdasarkan pending_status
            elif "pending_status" in df_filtered.columns:

                status_values = (
                    df_filtered["pending_status"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                pending = int(
                    status_values
                    .eq("pending")
                    .sum()
                )

            else:

                status_col = find_column(
                    df_filtered,
                    [
                        "ticket_status_name",
                        "ticket_status",
                        "status"
                    ]
                )

                if status_col is not None:

                    status_values = (
                        df_filtered[status_col]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                    )

                    pending = int(
                        status_values
                        .str.contains(
                            "pending",
                            na=False
                        )
                        .sum()
                    )

                else:

                    pending = 0

        render_kpi_card(
            "Tiket Pending",
            f"{pending:,}"
        )

        # ====================================================
        # 4. PENCAPAIAN SLA
        # ====================================================

        sla = get_sla_achievement(
            df_filtered
        )

        render_kpi_card(
            "Pencapaian SLA",
            (
                f"{sla:.2f}%"
                if sla is not None
                else "N/A"
            ),
            icon="⭐"
        )

        # ====================================================
        # 5. TIKET DI LUAR SLA
        # ====================================================

        breach_col = _first_existing_column(
            df_filtered,
            [
                "sla_breach_flag",
                "is_sla_breach",
                "breach_flag",
                "sla_breach",
                "total_breach"
            ]
        )

        if breach_col is not None:

            luar_sla = _numeric_sum(
                df_filtered,
                breach_col
            )

        else:

            sla_col = find_column(
                df_filtered,
                [
                    "sla_status",
                    "SLA_Status",
                    "sla_status_name"
                ]
            )

            if sla_col is not None:

                sla_values = (
                    df_filtered[sla_col]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                luar_sla = int(
                    sla_values
                    .isin(
                        [
                            "breach",
                            "breached",
                            "out sla",
                            "outside sla",
                            "late"
                        ]
                    )
                    .sum()
                )

            else:

                luar_sla = 0

        render_kpi_card(
            "Tiket di Luar SLA",
            f"{luar_sla:,}"
        )

        # ====================================================
        # 6. RATA-RATA WAKTU RESPON
        # ====================================================

        response_col = _first_existing_column(
            df_filtered,
            [
                "response_minutes",
                "avg_response_minutes",
                "response_time_minutes",
                "waktu_respon_menit"
            ]
        )

        avg_response = _numeric_mean(
            df_filtered,
            response_col
        )

        if avg_response is None:

            avg_response = get_avg_response(
                df_filtered
            )

        render_kpi_card(
            "Rata-rata Waktu Respon",
            (
                f"{avg_response:,.2f}"
                if avg_response is not None
                else "N/A"
            ),
            suffix="Menit"
        )

