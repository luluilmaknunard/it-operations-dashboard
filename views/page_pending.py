import streamlit as st
import pandas as pd
import plotly.express as px

from components.filters import render_top_filters

from components.charts import (
    chart_tingkat_dampak_pie,
    chart_tingkat_dampak_bar,
    chart_trend_harian_multi,

    chart_subkategori_pie,
    chart_waktu_penyelesaian,
    render_problem_table,
)


# ==============================================================================
# HELPER
# ==============================================================================

def _find_column(df, candidates):

    if df is None or df.empty:
        return None

    normalized = {}

    for col in df.columns:

        key = (
            str(col)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        normalized[key] = col

    for candidate in candidates:

        key = (
            str(candidate)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        if key in normalized:
            return normalized[key]

    return None


# ==============================================================================
# MATCH BUCKET
# ==============================================================================

def _match_bucket(series, bucket):

    if series is None:
        return pd.Series(dtype=bool)

    bucket = str(bucket).strip().lower()

    return (
        series
        .astype(str)
        .str.strip()
        .str.lower()
        .str.contains(
            bucket,
            regex=False,
            na=False,
        )
    )


# ==============================================================================
# GET PENDING DATAFRAME
# ==============================================================================

def _get_pending_dataframe(df):

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # ==========================================================================
    # PRIORITAS 1
    # date_pending
    # ==========================================================================

    if "date_pending" in df.columns:

        pending_mask = df["date_pending"].notna()

        return df.loc[pending_mask].copy()

    # ==========================================================================
    # PRIORITAS 2
    # pending_status
    # ==========================================================================

    pending_status_col = _find_column(
        df,
        [
            "pending_status",
            "pending status",
            "status_pending",
        ]
    )

    if pending_status_col is not None:

        pending_mask = (
            df[pending_status_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("pending")
        )

        return df.loc[pending_mask].copy()

    # ==========================================================================
    # PRIORITAS 3
    # STATUS TICKET
    # ==========================================================================

    status_col = _find_column(
        df,
        [
            "ticket_status_name",
            "ticket_status",
            "status",
            "status_name",
        ]
    )

    if status_col is not None:

        status = (
            df[status_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        pending_mask = status.str.contains(
            r"\bpending\b",
            regex=True,
            na=False,
        )

        return df.loc[pending_mask].copy()

    # ==========================================================================
    # PRIORITAS 4
    # TICKET TYPE
    # ==========================================================================

    type_col = _find_column(
        df,
        [
            "ticket_type",
            "ticketType",
            "type",
            "ticket_type_name",
        ]
    )

    if type_col is not None:

        ticket_type = (
            df[type_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        pending_mask = ticket_type.str.contains(
            r"\bpending\b",
            regex=True,
            na=False,
        )

        return df.loc[pending_mask].copy()

    return pd.DataFrame()


# ==============================================================================
# TICKET COUNT
# ==============================================================================

def _ticket_count(df):

    if df is None or df.empty:
        return 0

    ticket_col = _find_column(
        df,
        [
            "ticketId",
            "ticket_id",
            "ticketID",
            "ticket",
            "id",
        ]
    )

    if ticket_col is not None:

        return int(
            df[ticket_col]
            .dropna()
            .nunique()
        )

    return int(len(df))


# ==============================================================================
# KPI - HIGH IMPACT
# ==============================================================================

def _get_high_impact_count(df):

    if df is None or df.empty:
        return 0

    impact_col = _find_column(
        df,
        [
            "impact",
            "impact_name",
            "impact_level",
            "dampak",
            "tingkat_dampak",
        ]
    )

    if impact_col is None:
        return 0

    return int(
        df[impact_col]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("high")
        .sum()
    )


# ==============================================================================
# KPI - AVERAGE RESPONSE
# ==============================================================================

def _get_average_response(df):

    if df is None or df.empty:
        return None

    response_col = _find_column(
        df,
        [
            "response_minutes",
            "response_time",
            "response time",
            "waktu respon",
            "avg_response_time",
            "first_response_minutes",
        ]
    )

    if response_col is None:
        return None

    values = pd.to_numeric(
        df[response_col],
        errors="coerce",
    )

    values = values[
        values.notna()
        & (values >= 0)
    ]

    if values.empty:
        return None

    return float(values.mean())


# ==============================================================================
# KPI - AVERAGE MTTR
# ==============================================================================

def _get_average_mttr(df):

    if df is None or df.empty:
        return None

    resolution_col = _find_column(
        df,
        [
            "resolution_minutes",
            "resolution_time",
            "mttr",
            "mttr_minutes",
            "waktu_penyelesaian",
        ]
    )

    if resolution_col is None:
        return None

    values = pd.to_numeric(
        df[resolution_col],
        errors="coerce",
    )

    values = values[
        values.notna()
        & (values >= 0)
    ]

    if values.empty:
        return None

    return float(values.mean())


# ==============================================================================
# KPI - OUTSIDE SLA
# ==============================================================================

def _get_outside_sla_count(df):

    if df is None or df.empty:
        return 0

    resolution_col = _find_column(
        df,
        [
            "resolution_minutes",
            "resolution_time",
            "mttr",
            "mttr_minutes",
            "waktu_penyelesaian",
        ]
    )

    if resolution_col is None:
        return 0

    values = pd.to_numeric(
        df[resolution_col],
        errors="coerce",
    )

    values = values[
        values.notna()
        & (values >= 0)
    ]

    # SLA > 240 menit
    return int(
        (values > 240).sum()
    )


# ==============================================================================
# CUSTOM CATEGORY BAR
# ==============================================================================

def _chart_gangguan_kategori(df):

    if df is None or df.empty:
        return None

    category_col = _find_column(
        df,
        [
            "category_split_4",
            "detailSubCategory2",
            "category_name",
            "category",
        ]
    )

    if category_col is None:
        return None

    temp = (
        df[category_col]
        .dropna()
        .astype(str)
        .str.strip()
    )

    temp = temp[temp != ""]

    if temp.empty:
        return None

    data = (
        temp
        .value_counts()
        .reset_index()
    )

    data.columns = [
        "Kategori",
        "Jumlah",
    ]

    # Samakan nama kategori untuk tampilan
    def normalize_category(value):

        value_lower = value.lower()

        if "application" in value_lower or "aplikasi" in value_lower:
            return "Application"

        if "device" in value_lower:
            return "Device"

        if (
            "infrastructure" in value_lower
            or "infrastruktur" in value_lower
        ):
            return "Infrastructure"

        if "network" in value_lower:
            return "Network"

        return value

    data["Kategori"] = (
        data["Kategori"]
        .apply(normalize_category)
    )

    # Gabungkan apabila setelah normalisasi
    # terdapat kategori yang sama
    data = (
        data
        .groupby("Kategori", as_index=False)["Jumlah"]
        .sum()
    )

    data = data.sort_values(
        "Jumlah",
        ascending=True,
    )

    fig = px.bar(
        data,
        x="Jumlah",
        y="Kategori",
        orientation="h",
        text="Jumlah",
    )

    fig.update_traces(
        marker_color="#D32F2F",
        textposition="outside",
    )

    fig.update_layout(
        margin=dict(
            l=10,
            r=35,
            t=10,
            b=10,
        ),
        height=230,
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
    )

    return fig


# ==============================================================================
# PIE BUCKET
# ==============================================================================

def _render_bucket_pie(
    df,
    bucket,
    title,
    custom_col,
):
    """
    Filter bucket Device / Infrastructure / Network / Application
    kemudian render menggunakan chart_subkategori_pie().
    """

    df_bucket = df.copy()

    has_bucket_col = (
        "detailSubCategory2"
        in df_bucket.columns
    )

    if has_bucket_col:

        df_bucket = df_bucket[
            _match_bucket(
                df_bucket["detailSubCategory2"],
                bucket,
            )
        ]

    if df_bucket.empty:
        st.caption(f"**{title}**")
        st.info("Tidak ada data.")
        return

    # --------------------------------------------------------------------------
    # KHUSUS NETWORK
    # Buang noise aplikasi yang masuk bucket network
    # --------------------------------------------------------------------------

    if bucket == "network":

        if "category" in df_bucket.columns:

            df_bucket = df_bucket[
                ~df_bucket["category"]
                .astype(str)
                .str.lower()
                .isin(
                    [
                        "software non os",
                    ]
                )
            ]

        if "network_component" in df_bucket.columns:

            df_bucket = df_bucket[
                ~df_bucket["network_component"]
                .astype(str)
                .str.lower()
                .isin(
                    [
                        "kendala aplikasi",
                    ]
                )
            ]

    if df_bucket.empty:
        st.caption(f"**{title}**")
        st.info("Tidak ada data.")
        return

    fig = chart_subkategori_pie(
        df_bucket,
        title_name=title,
        custom_col=custom_col,
    )

    if fig is not None:

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={
                "displayModeBar": False,
                "responsive": True,
            },
        )

    else:

        st.caption(f"**{title}**")
        st.info("Tidak ada data.")


# ==============================================================================
# PAGE
# ==============================================================================

def render(df_raw):

    # ==========================================================================
    # 1. VALIDASI DATA
    # ==========================================================================

    if df_raw is None or df_raw.empty:

        st.warning(
            "Data raw tidak tersedia. "
            "Silakan upload file terlebih dahulu."
        )

        return

    # ==========================================================================
    # 2. HEADER
    # ==========================================================================

    st.markdown(
        "## **🔍 Pending Investigation**"
    )

    # ==========================================================================
    # 3. FILTER
    # ==========================================================================

    df_filtered = render_top_filters(
        df_raw,
        key_prefix="pending",
    )

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # 4. VALIDASI HASIL FILTER
    # ==========================================================================

    if (
        df_filtered is None
        or df_filtered.empty
    ):

        st.warning(
            "Data tidak tersedia untuk filter yang dipilih."
        )

        return

    # ==========================================================================
    # 5. FILTER PENDING
    # ==========================================================================

    df_pending = _get_pending_dataframe(
        df_filtered
    )

    if df_pending.empty:

        st.warning(
            "Tidak terdapat tiket pending "
            "pada filter yang dipilih."
        )

        return

    # ==========================================================================
    # KPI
    # ==========================================================================

    total_pending = _ticket_count(
        df_pending
    )

    outside_sla = _get_outside_sla_count(
        df_pending
    )

    avg_response = _get_average_response(
        df_pending
    )

    avg_mttr = _get_average_mttr(
        df_pending
    )

    # ==========================================================================
    # 6. BARIS 1
    #
    # [ Gangguan Kategori ]
    # [ Impact ]
    # [ Resolution ]
    # [ KPI KPI KPI KPI ]
    # ==========================================================================

    col_a, col_b, col_c, col_kpi = st.columns(
        [1.3, 1.3, 1.5, 0.8]
    )

    # --------------------------------------------------------------------------
    # GANGGUAN BERDASARKAN KATEGORI
    # --------------------------------------------------------------------------

    with col_a:

        st.markdown(
            "##### **Gangguan berdasarkan Kategori**"
        )

        fig = _chart_gangguan_kategori(
            df_pending
        )

        if fig is not None:

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                    "responsive": True,
                },
            )

        else:

            st.info(
                "Data kategori tidak tersedia."
            )

    # --------------------------------------------------------------------------
    # IMPACT
    # --------------------------------------------------------------------------

    with col_b:

        st.markdown(
            "##### **Distribusi Tingkat Dampak**"
        )

        fig = chart_tingkat_dampak_bar(
            df_pending
        )

        if fig is not None:

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                    "responsive": True,
                },
            )

        else:

            fig = chart_tingkat_dampak_pie(
                df_pending
            )

            if fig is not None:

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={
                        "displayModeBar": False,
                        "responsive": True,
                    },
                )

            else:

                st.info(
                    "Data impact tidak tersedia."
                )

    # --------------------------------------------------------------------------
    # RESOLUTION TIME
    # --------------------------------------------------------------------------

    with col_c:

        st.markdown(
            "##### **Distribusi Waktu Penyelesaian**"
        )

        fig = chart_waktu_penyelesaian(
            df_pending
        )

        if fig is not None:

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                    "responsive": True,
                },
            )

        else:

            st.info(
                "Data waktu penyelesaian tidak tersedia."
            )

    # --------------------------------------------------------------------------
    # KPI COLUMN
    # --------------------------------------------------------------------------

    with col_kpi:

        # ======================================================================
        # TOTAL PENDING
        # ======================================================================

        st.metric(
            "Total Tiket Pending",
            f"{total_pending:,}",
        )

        # ======================================================================
        # OUTSIDE SLA
        # ======================================================================

        st.metric(
            "Tiket di Luar SLA",
            f"{outside_sla:,}",
        )

        # ======================================================================
        # AVERAGE RESPONSE
        # ======================================================================

        if avg_response is not None:

            response_display = (
                f"{avg_response:.2f} Menit"
            )

        else:

            response_display = "-"

        st.metric(
            "Rata-rata Waktu Respons ⭐",
            response_display,
        )

        # ======================================================================
        # AVERAGE MTTR
        # ======================================================================

        if avg_mttr is not None:

            mttr_display = (
                f"{avg_mttr:.2f} Menit"
            )

        else:

            mttr_display = "-"

        st.metric(
            "Rata-rata MTTR ⭐",
            mttr_display,
        )

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # 7. BARIS 2
    #
    # [ DEVICE ]
    # [ INFRASTRUKTUR ]
    # [ NETWORK ]
    # [ APLIKASI ]
    #
    # SEMUANYA PIE CHART
    # ==========================================================================

    b1, b2, b3, b4 = st.columns(4)

    # --------------------------------------------------------------------------
    # DEVICE
    # --------------------------------------------------------------------------

    with b1:

        _render_bucket_pie(
            df_pending,
            bucket="device",
            title="Device",
            custom_col=[
                "detailSubCategory",
                "category_split_3",
                "category_name",
            ],
        )

    # --------------------------------------------------------------------------
    # INFRASTRUKTUR
    # --------------------------------------------------------------------------

    with b2:

        _render_bucket_pie(
            df_pending,
            bucket="infrastructure",
            title="Infrastruktur",
            custom_col=[
                "detailSubCategory",
                "category_split_3",
                "category_name",
            ],
        )

    # --------------------------------------------------------------------------
    # NETWORK
    # --------------------------------------------------------------------------

    with b3:

        _render_bucket_pie(
            df_pending,
            bucket="network",
            title="Network",
            custom_col=[
                "network_component",
                "detailSubCategory",
                "category_split_3",
            ],
        )

    # --------------------------------------------------------------------------
    # APLIKASI
    # --------------------------------------------------------------------------

    with b4:

        _render_bucket_pie(
            df_pending,
            bucket="application",
            title="Aplikasi",
            custom_col=[
                "category",
                "subCategory",
                "category_split_1",
                "category_split_2",
            ],
        )

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # 8. BARIS 3
    #
    # [ DETAIL TIKET PENDING ] [ TREND HARIAN ]
    # ==========================================================================

    col_table, col_trend = st.columns(
        [1.6, 1]
    )

    # --------------------------------------------------------------------------
    # DETAIL TICKET
    # --------------------------------------------------------------------------

    with col_table:

        st.markdown(
            "##### **Detail Tiket Pending**"
        )

        st.caption(
            f"Menampilkan {total_pending:,} tiket "
            "yang saat ini masuk kategori pending."
        )

        render_problem_table(
            df_pending
        )

    # --------------------------------------------------------------------------
    # TREND
    # --------------------------------------------------------------------------

    with col_trend:

        st.markdown(
            "##### **Tren Tiket Pending Harian**"
        )

        fig = chart_trend_harian_multi(
            df_pending
        )

        if fig is not None:

            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    "displayModeBar": False,
                    "responsive": True,
                },
            )

        else:

            st.info(
                "Data tanggal tidak tersedia."
            )

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # 9. OPTIONAL RAW DATA
    # ==========================================================================

    with st.expander(
        "Lihat seluruh data tiket pending"
    ):

        st.dataframe(
            df_pending,
            use_container_width=True,
            hide_index=True,
        )