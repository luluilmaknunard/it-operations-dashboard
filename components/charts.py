import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


# ==============================================================================
# KONFIGURASI WARNA UTAMA (PALETTE SYSTEM)
# ==============================================================================

RED_COLOR = "#D32F2F"
BLUE_COLOR = "#1976D2"
ORANGE_COLOR = "#F57C00"
GREEN_COLOR = "#388E3C"
PURPLE_COLOR = "#7B1FA2"
GREY_COLOR = "#757575"

RED_SEQUENCE = [
    "#B71C1C",
    "#C62828",
    "#D32F2F",
    "#E53935",
    "#EF5350",
    "#E57373",
]

BLUE_SEQUENCE = [
    "#0D47A1",
    "#1565C0",
    "#1976D2",
    "#1E88E5",
    "#42A5F5",
    "#90CAF9",
]


# ==============================================================================
# HELPER
# ==============================================================================

def find_column(df, candidates):
    """
    Mencari kolom pertama yang cocok berdasarkan nama kolom.

    Mendukung:
    - nama kolom persis
    - underscore
    - spasi
    - tanda "-"
    """

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


def pick_best_column(df, candidates):
    """
    Cari kolom pertama dari candidates yang tersedia
    dan benar-benar memiliki data valid.
    """

    if df is None or df.empty:
        return None

    for col in candidates:

        if col not in df.columns:
            continue

        cleaned = (
            df[col]
            .dropna()
            .astype(str)
            .str.strip()
        )

        cleaned = cleaned[
            ~cleaned.str.lower().isin(
                [
                    "",
                    "nan",
                    "none",
                    "null",
                    "-",
                ]
            )
        ]

        if not cleaned.empty:
            return col

    return None


def _clean_category_series(df, col):
    """
    Membersihkan series kategori dari nilai kosong/invalid.
    """

    if df is None or df.empty or col not in df.columns:
        return pd.Series(dtype="object")

    s = (
        df[col]
        .dropna()
        .astype(str)
        .str.strip()
    )

    return s[
        ~s.str.lower().isin(
            [
                "",
                "nan",
                "none",
                "null",
                "-",
            ]
        )
    ]


def _find_ticket_id_column(df):
    """
    Cari kolom ID ticket.
    """

    return find_column(
        df,
        [
            "ticketId",
            "ticket_id",
            "ticketID",
            "ticket",
            "id",
        ]
    )


def _ticket_count(df):
    """
    Menghitung jumlah ticket.

    Jika ID ticket tersedia:
        gunakan nunique()

    Jika tidak:
        gunakan jumlah row.
    """

    if df is None or df.empty:
        return 0

    id_col = _find_ticket_id_column(df)

    if id_col is not None:

        return int(
            df[id_col]
            .dropna()
            .nunique()
        )

    return int(len(df))


def _contains_ticket_type(series, pattern):
    """
    Helper untuk mengenali ticket type.
    """

    return (
        series
        .astype(str)
        .str.strip()
        .str.lower()
        .str.contains(
            pattern,
            regex=True,
            na=False
        )
    )


def _valid_text_mask(series):
    """
    Mask untuk nilai text yang valid.
    """

    return (
        series
        .notna()
        & ~series
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(
            [
                "",
                "nan",
                "none",
                "null",
                "-",
            ]
        )
    )


# ==============================================================================
# 1. CHART DISTRIBUSI & PROPORSI
# ==============================================================================

def chart_distribusi_jenis(df):
    """
    Donut Chart:
    Distribusi Jenis Tiket.
    """

    if df is None or df.empty:
        return None

    col = pick_best_column(
        df,
        [
            "ticket_type",
            "type",
            "ticketType",
            "ticket_type_name",
        ]
    )

    if col is None:
        return None

    data = df.loc[
        _valid_text_mask(df[col])
    ].copy()

    if data.empty:
        return None

    counts = (
        data[col]
        .astype(str)
        .str.strip()
        .value_counts()
        .reset_index()
    )

    counts.columns = [
        "Jenis",
        "Jumlah",
    ]

    fig = px.pie(
        counts,
        values="Jumlah",
        names="Jenis",
        hole=0.55,
        color_discrete_sequence=[
            ORANGE_COLOR,
            BLUE_COLOR,
            GREEN_COLOR,
            RED_COLOR,
        ],
        title="<b>Distribusi Jenis Tiket</b>",
    )

    fig.update_traces(
        textinfo="percent+value",
        textposition="inside",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Jumlah: %{value}<br>"
            "Persentase: %{percent}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=280,
        showlegend=False,
        paper_bgcolor="white",
        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10,
        ),
    )

    return fig


def chart_tingkat_dampak_pie(df):
    """
    Pie Chart:
    Distribusi Tingkat Dampak / Impact Level.
    """

    if df is None or df.empty:
        return None

    impact_col = pick_best_column(
        df,
        [
            "impact_name",
            "impact",
            "impact_level",
            "priority",
            "dampak",
            "tingkat_dampak",
        ]
    )

    if impact_col is None:
        return None

    data = df.loc[
        _valid_text_mask(df[impact_col])
    ].copy()

    if data.empty:
        return None

    counts = (
        data[impact_col]
        .astype(str)
        .str.strip()
        .value_counts()
        .reset_index()
    )

    counts.columns = [
        "Dampak",
        "Jumlah",
    ]

    fig = px.pie(
        counts,
        values="Jumlah",
        names="Dampak",
        color_discrete_sequence=[
            GREEN_COLOR,
            ORANGE_COLOR,
            RED_COLOR,
            PURPLE_COLOR,
        ],
        title="<b>Distribusi Tingkat Dampak</b>",
    )

    fig.update_traces(
        textinfo="percent+value",
        hovertemplate=(
            "<b>Dampak: %{label}</b><br>"
            "Total: %{value} (%{percent})"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=280,
        showlegend=False,
        paper_bgcolor="white",
        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10,
        ),
    )

    return fig


# ==============================================================================
# 2. CHART TREN & WAKTU
# ==============================================================================

def chart_trend_harian_multi(df):
    """
    Line Chart:
    Tren jumlah tiket harian.

    Menampilkan:
    - Total Ticket
    - Request
    - Gangguan

    Hari dihitung sejak tanggal paling awal pada
    data yang sudah difilter.
    """

    if df is None or df.empty:
        return None

    date_col = find_column(
        df,
        [
            "date_created_at",
            "created_at",
            "date_created",
            "created_date",
            "tanggal",
            "date",
        ]
    )

    if date_col is None:
        return None

    df_copy = df.copy()

    df_copy["date_dt"] = pd.to_datetime(
        df_copy[date_col],
        errors="coerce",
    )

    df_copy = df_copy[
        df_copy["date_dt"].notna()
    ].copy()

    if df_copy.empty:
        return None

    df_copy["calendar_date"] = (
        df_copy["date_dt"]
        .dt.normalize()
    )

    min_date = df_copy["calendar_date"].min()

    df_copy["day_index"] = (
        (
            df_copy["calendar_date"]
            - min_date
        ).dt.days
        + 1
    )

    all_days = pd.RangeIndex(
        1,
        int(
            df_copy["day_index"].max()
        ) + 1,
    )

    # ------------------------------------------------------------------
    # TOTAL
    # ------------------------------------------------------------------

    id_col = _find_ticket_id_column(
        df_copy
    )

    if id_col is not None:

        daily_total = (
            df_copy
            .groupby("day_index")[id_col]
            .nunique()
            .reindex(
                all_days,
                fill_value=0,
            )
        )

    else:

        daily_total = (
            df_copy
            .groupby("day_index")
            .size()
            .reindex(
                all_days,
                fill_value=0,
            )
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily_total.index,
            y=daily_total.values,
            mode="lines",
            name="Total Ticket",
            line=dict(
                color=RED_COLOR,
                width=2,
                shape="hv",
            ),
            hovertemplate=(
                "Hari ke-%{x}<br>"
                "Total: <b>%{y}</b>"
                "<extra></extra>"
            ),
        )
    )

    # ------------------------------------------------------------------
    # TYPE
    # ------------------------------------------------------------------

    type_col = pick_best_column(
        df_copy,
        [
            "ticket_type",
            "type",
            "ticketType",
            "ticket_type_name",
        ]
    )

    if type_col is not None:

        series_config = [
            (
                "Request",
                r"request|permintaan",
                ORANGE_COLOR,
            ),
            (
                "Gangguan",
                r"gangguan|incident",
                BLUE_COLOR,
            ),
        ]

        for label, pattern, color in series_config:

            mask = _contains_ticket_type(
                df_copy[type_col],
                pattern,
            )

            sub = df_copy.loc[
                mask
            ].copy()

            if sub.empty:
                continue

            if id_col is not None:

                daily_sub = (
                    sub
                    .groupby("day_index")[id_col]
                    .nunique()
                    .reindex(
                        all_days,
                        fill_value=0,
                    )
                )

            else:

                daily_sub = (
                    sub
                    .groupby("day_index")
                    .size()
                    .reindex(
                        all_days,
                        fill_value=0,
                    )
                )

            fig.add_trace(
                go.Scatter(
                    x=daily_sub.index,
                    y=daily_sub.values,
                    mode="lines",
                    name=label,
                    line=dict(
                        color=color,
                        width=1.5,
                        shape="hv",
                    ),
                    hovertemplate=(
                        f"Hari ke-%{{x}}<br>"
                        f"{label}: "
                        f"<b>%{{y}}</b>"
                        "<extra></extra>"
                    ),
                )
            )

    fig.update_layout(
        height=280,
        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10,
        ),
        xaxis_title="Hari Ke-",
        yaxis_title="Jumlah Tiket",
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
    )

    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#F0F0F0",
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor="#F0F0F0",
    )

    return fig


def calendar_heatmap(df):
    """
    Calendar Heatmap.

    Judul otomatis:
        Calendar Heatmap
        <Nama Bulan> <Tahun>
    """

    if df is None or df.empty:
        return None

    date_candidates = [
        "date_created_at",
        "date_created",
        "created_at",
        "created_date",
        "creation_date",
        "date_opened",
        "opened_at",
        "open_date",
        "ticket_created",
        "ticket_created_at",
        "tanggal",
        "tanggal_dibuat",
        "tgl_created",
        "date",
    ]

    date_col = find_column(
        df,
        date_candidates,
    )

    if date_col is None:

        for col in df.columns:

            col_lower = (
                str(col)
                .lower()
            )

            if (
                "date" in col_lower
                or "tanggal" in col_lower
                or "tgl" in col_lower
            ):
                date_col = col
                break

    if date_col is None:
        return None

    data = df.copy()

    data["_calendar_date"] = pd.to_datetime(
        data[date_col],
        errors="coerce",
    )

    data = data[
        data["_calendar_date"].notna()
    ].copy()

    if data.empty:
        return None

    month_periods = (
        data["_calendar_date"]
        .dt.to_period("M")
        .dropna()
        .unique()
    )

    month_names = {
        1: "Januari",
        2: "Februari",
        3: "Maret",
        4: "April",
        5: "Mei",
        6: "Juni",
        7: "Juli",
        8: "Agustus",
        9: "September",
        10: "Oktober",
        11: "November",
        12: "Desember",
    }

    if len(month_periods) == 1:

        selected_period = month_periods[0]

        month_title = (
            f"{month_names[selected_period.month]} "
            f"{selected_period.year}"
        )

    elif len(month_periods) > 1:

        sorted_periods = sorted(
            month_periods
        )

        first_period = sorted_periods[0]
        last_period = sorted_periods[-1]

        first_month = (
            f"{month_names[first_period.month]} "
            f"{first_period.year}"
        )

        last_month = (
            f"{month_names[last_period.month]} "
            f"{last_period.year}"
        )

        month_title = (
            f"{first_month} – {last_month}"
        )

    else:

        month_title = ""

    data["_date_only"] = (
        data["_calendar_date"]
        .dt.normalize()
    )

    id_col = _find_ticket_id_column(
        data
    )

    if id_col is not None:

        daily_count = (
            data
            .groupby("_date_only")[id_col]
            .nunique()
            .reset_index(name="jumlah")
        )

    else:

        daily_count = (
            data
            .groupby("_date_only")
            .size()
            .reset_index(name="jumlah")
        )

    if daily_count.empty:
        return None

    min_date = daily_count["_date_only"].min()
    max_date = daily_count["_date_only"].max()

    min_monday = (
        min_date
        - pd.Timedelta(
            days=min_date.weekday()
        )
    )

    max_sunday = (
        max_date
        + pd.Timedelta(
            days=6 - max_date.weekday()
        )
    )

    all_dates = pd.date_range(
        min_monday,
        max_sunday,
        freq="D",
    )

    calendar_df = pd.DataFrame({
        "_date_only": all_dates,
    })

    calendar_df = calendar_df.merge(
        daily_count,
        on="_date_only",
        how="left",
    )

    calendar_df["jumlah"] = (
        calendar_df["jumlah"]
        .fillna(0)
        .astype(int)
    )

    calendar_df["weekday"] = (
        calendar_df["_date_only"]
        .dt.weekday
    )

    calendar_df["week"] = (
        (
            calendar_df["_date_only"]
            - min_monday
        ).dt.days // 7
    )

    weekday_labels = [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun",
    ]

    max_week = int(
        calendar_df["week"].max()
    )

    z = []
    customdata = []
    text = []

    for weekday in range(7):

        row_z = []
        row_custom = []
        row_text = []

        for week in range(
            max_week + 1
        ):

            match = calendar_df[
                (
                    calendar_df["weekday"]
                    == weekday
                )
                &
                (
                    calendar_df["week"]
                    == week
                )
            ]

            if match.empty:

                row_z.append(None)
                row_custom.append(None)
                row_text.append("")

            else:

                value = int(
                    match.iloc[0]["jumlah"]
                )

                row_z.append(value)

                row_custom.append(
                    match.iloc[0]["_date_only"]
                )

                row_text.append(
                    str(value)
                    if value > 0
                    else ""
                )

        z.append(row_z)
        customdata.append(row_custom)
        text.append(row_text)

    fig = go.Figure()

    fig.add_trace(
        go.Heatmap(
            z=z,
            x=list(
                range(max_week + 1)
            ),
            y=weekday_labels,
            text=text,
            texttemplate="%{text}",
            textfont=dict(
                size=11
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{y}</b>"
                "<br>"
                "Jumlah Tiket: %{z}"
                "<extra></extra>"
            ),
            colorscale=[
                [0.00, "#fff5f5"],
                [0.25, "#fca5a5"],
                [0.50, "#f87171"],
                [0.75, "#ef4444"],
                [1.00, "#b91c1c"],
            ],
            showscale=False,
            xgap=2,
            ygap=2,
        )
    )

    if month_title:

        title_text = (
            "Calendar Heatmap"
            "<br>"
            "<span style="
            "'font-size:13px;"
            "font-weight:400;"
            "color:#7c8597'"
            ">"
            f"{month_title}"
            "</span>"
        )

    else:

        title_text = (
            "Calendar Heatmap"
        )

    fig.update_layout(

        height=330,

        margin=dict(
            l=55,
            r=15,
            t=75,
            b=25,
            pad=0,
        ),

        title=dict(
            text=title_text,
            x=0.5,
            xanchor="center",
            y=0.96,
            yanchor="top",
            font=dict(
                size=17,
                color="#111111",
            ),
        ),

        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",

        xaxis=dict(
            title=None,
            tickmode="array",
            tickvals=list(
                range(max_week + 1)
            ),
            ticktext=[
                ""
                for _ in range(
                    max_week + 1
                )
            ],
            showgrid=False,
            zeroline=False,
            side="top",
            fixedrange=True,
            automargin=False,
        ),

        yaxis=dict(
            title=None,
            autorange="reversed",
            categoryorder="array",
            categoryarray=weekday_labels,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            automargin=False,
        ),
    )

    fig.update_yaxes(
        tickfont=dict(
            size=11,
            color="#7c8597",
        ),
        ticklabelposition="outside",
    )

    fig.update_xaxes(
        tickfont=dict(
            size=11,
            color="#7c8597",
        )
    )

    return fig


# ==============================================================================
# 3. CHART KATEGORI & BREAKDOWN
# ==============================================================================

def chart_kategori_horizontal(df):
    """
    Horizontal Bar Chart:
    Jumlah Gangguan per Kategori.

    Prioritas:
    detailSubCategory2
    category
    category_split_1
    category_name
    """

    if df is None or df.empty:
        return None

    cat_col = pick_best_column(
        df,
        [
            "detailSubCategory2",
            "category",
            "category_split_1",
            "category_name",
        ]
    )

    if cat_col is None:
        return None

    clean = _clean_category_series(
        df,
        cat_col,
    )

    if clean.empty:
        return None

    counts = (
        clean
        .value_counts()
        .head(5)
        .reset_index()
    )

    counts.columns = [
        "Kategori",
        "Jumlah",
    ]

    counts = counts.sort_values(
        by="Jumlah",
        ascending=True,
    )

    fig = px.bar(
        counts,
        x="Jumlah",
        y="Kategori",
        orientation="h",
        text="Jumlah",
        title="<b>Top 5 Kategori Gangguan</b>",
    )

    fig.update_traces(
        marker_color=RED_COLOR,
        textposition="inside",
        cliponaxis=False,
        hovertemplate=(
            "Kategori: %{y}<br>"
            "Jumlah: <b>%{x} Kasus</b>"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=280,
        margin=dict(
            l=10,
            r=30,
            t=40,
            b=10,
        ),
        xaxis_title="Jumlah Kasus",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F0F0F0",
    )

    return fig


def chart_subkategori_bar(
    df,
    title_name="Subkategori",
    custom_col=None,
):
    """
    Horizontal Bar Chart Subkategori.

    custom_col bisa:
    - string
    - list/tuple kandidat kolom
    """

    if (
        df is None
        or df.empty
        or not custom_col
    ):
        return None

    candidates = (
        custom_col
        if isinstance(
            custom_col,
            (list, tuple),
        )
        else [custom_col]
    )

    col = pick_best_column(
        df,
        candidates,
    )

    if col is None:
        return None

    clean_series = _clean_category_series(
        df,
        col,
    )

    if clean_series.empty:
        return None

    counts = (
        clean_series
        .value_counts()
        .head(5)
        .reset_index()
    )

    counts.columns = [
        "Kategori",
        "Jumlah",
    ]

    counts = counts.sort_values(
        by="Jumlah",
        ascending=True,
    )

    max_val = counts["Jumlah"].max()

    colors = [
        RED_COLOR
        if val == max_val
        else "#8E8E8E"
        for val in counts["Jumlah"]
    ]

    fig = px.bar(
        counts,
        x="Jumlah",
        y="Kategori",
        orientation="h",
        text="Jumlah",
        title=f"<b>{title_name}</b>",
    )

    fig.update_traces(
        marker_color=colors,
        textposition="inside",
        cliponaxis=False,
    )

    fig.update_layout(
        xaxis_title="Jumlah Kasus",
        yaxis_title=None,
        margin=dict(
            l=10,
            r=30,
            t=40,
            b=10,
        ),
        height=280,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=11),
        title=dict(
            x=0.5,
            xanchor="center",
        ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F0F0F0",
    )

    return fig


def chart_department(
    df,
    key_prefix="default",
):
    """
    Menampilkan horizontal bar chart jumlah gangguan
    berdasarkan Department.

    Jika ticket ID tersedia:
    jumlah dihitung berdasarkan distinct ticket.
    """

    if df is None or df.empty:

        st.info(
            "Tidak ada data untuk ditampilkan."
        )

        return

    dept_col = None

    for col in df.columns:

        col_clean = (
            str(col)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        if (
            col_clean in [
                "department",
                "dept",
                "nama department",
                "nama dept",
                "department name",
                "dept name",
            ]
            or "department" in col_clean
        ):

            dept_col = col
            break

    if dept_col is None:

        st.info(
            "Kolom department tidak ditemukan."
        )

        return

    data = df.loc[
        _valid_text_mask(df[dept_col])
    ].copy()

    if data.empty:

        st.info(
            "Tidak ada data department."
        )

        return

    data["department_display"] = (
        data[dept_col]
        .astype(str)
        .str.strip()
    )

    id_col = _find_ticket_id_column(
        data
    )

    if id_col is not None:

        dept_summary = (
            data
            .groupby("department_display")[id_col]
            .nunique()
            .reset_index(
                name="Jumlah Gangguan"
            )
        )

    else:

        dept_summary = (
            data
            .groupby("department_display")
            .size()
            .reset_index(
                name="Jumlah Gangguan"
            )
        )

    dept_summary = dept_summary[
        dept_summary["Jumlah Gangguan"] > 0
    ]

    if dept_summary.empty:

        st.info(
            "Tidak ada data department."
        )

        return

    sort_key = (
        f"{key_prefix}_dept_sort"
    )

    sort_option = st.radio(
        "Urutan Data:",
        [
            "Terbanyak",
            "Tersedikit",
        ],
        horizontal=True,
        key=sort_key,
    )

    if sort_option == "Terbanyak":

        dept_summary = (
            dept_summary
            .sort_values(
                "Jumlah Gangguan",
                ascending=False,
            )
        )

    else:

        dept_summary = (
            dept_summary
            .sort_values(
                "Jumlah Gangguan",
                ascending=True,
            )
        )

    dept_summary = (
        dept_summary
        .head(10)
    )

    chart_data = (
        dept_summary
        .sort_values(
            "Jumlah Gangguan",
            ascending=True,
        )
    )

    fig = px.bar(
        chart_data,
        x="Jumlah Gangguan",
        y="department_display",
        orientation="h",
        text="Jumlah Gangguan",
    )

    fig.update_traces(
        textposition="inside",
        cliponaxis=False,
        marker_color=RED_COLOR,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Jumlah Gangguan: %{x:,}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=420,
        xaxis_title="Jumlah Gangguan",
        yaxis_title="",
        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(
            l=10,
            r=40,
            t=20,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


def chart_layanan_treemap(df):
    """
    Treemap:
    Layanan dengan Tiket Terbanyak.

    Jika ticket ID tersedia:
    nilai menggunakan distinct ticket.
    """

    if df is None or df.empty:
        return None

    service_col = pick_best_column(
        df,
        [
            "service_name",
            "service",
            "nama_layanan",
            "layanan",
        ]
    )

    if service_col is None:
        return None

    df_clean = df.copy()

    df_clean[service_col] = (
        df_clean[service_col]
        .astype(str)
        .str.strip()
    )

    df_clean = df_clean[
        ~df_clean[service_col]
        .str.lower()
        .isin(
            [
                "nan",
                "none",
                "",
                "null",
                "-",
            ]
        )
    ]

    if df_clean.empty:
        return None

    id_col = _find_ticket_id_column(
        df_clean
    )

    if id_col is not None:

        counts = (
            df_clean
            .groupby(service_col)[id_col]
            .nunique()
            .reset_index(
                name="count"
            )
        )

    else:

        counts = (
            df_clean[service_col]
            .value_counts()
            .reset_index()
        )

        counts.columns = [
            service_col,
            "count",
        ]

    counts = counts[
        counts["count"] > 0
    ]

    if counts.empty:
        return None

    fig = px.treemap(
        counts,
        path=[service_col],
        values="count",
        color="count",
        color_continuous_scale=[
            "#FFE5E5",
            "#FF4D4D",
            "#B30000",
        ],
        title=(
            "<b>Layanan dengan "
            "Laporan Terbanyak</b>"
        ),
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Total Laporan: %{value:,}"
            "<extra></extra>"
        ),
        textinfo="label+value",
    )

    fig.update_layout(
        height=300,
        margin=dict(
            t=40,
            l=10,
            r=10,
            b=10,
        ),
        paper_bgcolor="white",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def chart_subkategori_pie(
    df,
    title_name="",
    custom_col=None,
):
    """
    Pie Chart untuk penyebaran kasus Pending.

    Logic data dibuat sama dengan chart_subkategori_bar().
    Perbedaannya hanya jenis visualisasi:
    Bar Chart -> Pie Chart
    """

    if (
        df is None
        or df.empty
        or not custom_col
    ):
        return None

    candidates = (
        custom_col
        if isinstance(
            custom_col,
            (list, tuple),
        )
        else [custom_col]
    )

    # --------------------------------------------------------------------------
    # CARI KOLOM
    # --------------------------------------------------------------------------

    col = pick_best_column(
        df,
        candidates,
    )

    if col is None:
        return None

    # --------------------------------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------------------------------

    clean = _clean_category_series(
        df,
        col,
    )

    if clean.empty:
        return None

    # --------------------------------------------------------------------------
    # HITUNG JUMLAH
    # --------------------------------------------------------------------------

    counts = (
        clean
        .value_counts()
        .reset_index()
    )

    counts.columns = [
        "Kategori",
        "Jumlah",
    ]

    counts = counts[
        counts["Jumlah"] > 0
    ]

    if counts.empty:
        return None

    # --------------------------------------------------------------------------
    # PIE CHART
    # --------------------------------------------------------------------------

    fig = px.pie(
        counts,
        values="Jumlah",
        names="Kategori",
        title=f"<b>{title_name}</b>",
    )

    color_scale = [
    "#084594",
    "#2171B5",
    "#4292C6",
    "#6BAED6",
    "#9ECAE1",
    "#C6DBEF",
    "#DEEBF7",
    "#31A354",
    "#74C476",
    "#A1D99B",
    "#FD8D3C",
    "#FDAE6B",
    "#FCBBA1",
    "#E6550D",
    "#756BB1",
]

    fig.update_traces(
         marker=dict(
            colors=color_scale,
            line=dict(
                color="white",
                width=1,
            ),
        ),

        textinfo="value+percent",

        textposition="inside",

        textfont=dict(
            size=10,
        ),

        hovertemplate=(
            "<b>%{label}</b><br>"
            "Jumlah Kasus: %{value}<br>"
            "Persentase: %{percent}"
            "<extra></extra>"
        ),
    )

    # --------------------------------------------------------------------------
    # LAYOUT
    # --------------------------------------------------------------------------

    fig.update_layout(

        height=250,

        margin=dict(
            l=5,
            r=5,
            t=45,
            b=5,
        ),

        showlegend=False,
        paper_bgcolor="white",
        plot_bgcolor="white",

        title=dict(
            x=0.5,
            xanchor="center",
            y=0.95,
            yanchor="top",
            font=dict(
                size=17,
            ),
        ),

        uniformtext=dict(
            minsize=8,
            mode="hide",
        ),

    )

    fig.update_traces(
        domain=dict(
            x=[0.02, 0.98],
            y=[0.02, 0.93],
        )
    )


    return fig


# ==============================================================================
# 4. CHART PERFORMA & TEKNISI
# ==============================================================================

def chart_peringkat_penyelesaian(df):
    """
    Bar Chart:
    Peringkat teknisi / assignee berdasarkan jumlah tiket.
    """

    if df is None or df.empty:
        return None

    col = pick_best_column(
        df,
        [
            "updated_by_name",
            "assignee",
            "assigned_to",
            "assigned_name",
            "technician",
            "technician_name",
            "member",
            "member_name",
        ]
    )

    if col is None:
        return None

    data = df.loc[
        _valid_text_mask(df[col])
    ].copy()

    if data.empty:
        return None

    id_col = _find_ticket_id_column(
        data
    )

    if id_col is not None:

        counts = (
            data
            .groupby(col)[id_col]
            .nunique()
            .reset_index(
                name="Jumlah"
            )
        )

    else:

        counts = (
            data[col]
            .value_counts()
            .reset_index()
        )

        counts.columns = [
            col,
            "Jumlah",
        ]

    counts = (
        counts
        .sort_values(
            by="Jumlah",
            ascending=False,
        )
        .head(10)
        .sort_values(
            by="Jumlah",
            ascending=True,
        )
    )

    if counts.empty:
        return None

    fig = px.bar(
        counts,
        x="Jumlah",
        y=col,
        orientation="h",
        text="Jumlah",
        title="<b>Top 10 Penyelesai Tiket</b>",
    )

    fig.update_traces(
        marker_color=BLUE_COLOR,
        textposition="inside",
        cliponaxis=False,
        hovertemplate=(
            "Staf: %{y}<br>"
            "Selesai: <b>%{x} Tiket</b>"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        height=380,
        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10,
        ),
        xaxis_title="Jumlah Tiket",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F0F0F0",
    )

    return fig


def chart_waktu_penyelesaian(df):
    """
    Bar Chart:
    Distribusi durasi waktu penyelesaian tiket.
    """

    if (
        df is None
        or df.empty
        or "resolution_time_group"
        not in df.columns
    ):
        return None

    cat_order = [
        "≤ 30 Menit",
        "31 - 60 Menit",
        "61 - 120 Menit",
        "121 - 240 Menit",
        "> 240 Menit",
    ]

    data = df.loc[
        _valid_text_mask(
            df["resolution_time_group"]
        )
    ].copy()

    if data.empty:
        return None

    counts = (
        data["resolution_time_group"]
        .value_counts()
        .reset_index()
    )

    counts.columns = [
        "group",
        "count",
    ]

    counts["group"] = pd.Categorical(
        counts["group"],
        categories=cat_order,
        ordered=True,
    )

    counts = counts.sort_values(
        "group",
        ascending=True,
    )

    fig = px.bar(
        counts,
        x="count",
        y="group",
        orientation="h",
        text="count",
        title=(
            "<b>Distribusi Waktu "
            "Penyelesaian Tiket</b>"
        ),
    )

    fig.update_traces(
        marker_color="#E57373",
        textposition="inside",
        cliponaxis=False,
    )

    fig.update_layout(
        height=260,
        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10,
        ),
        xaxis_title="Jumlah Tiket",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F0F0F0",
    )

    return fig


# ==============================================================================
# RESPONSE & SLA
# ==============================================================================

def get_avg_response(df):

    if df is None or df.empty:
        return None

    response_col = find_column(
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

    return float(
        values.mean()
    )


def get_sla_achievement(df):

    if df is None or df.empty:
        return None

    sla_col = find_column(
        df,
        [
            "sla_status",
            "SLA_Status",
            "sla_status_name",
        ]
    )

    if sla_col is None:
        return None

    sla = (
        df[sla_col]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    valid = sla.isin(
        [
            "breach",
            "comply",
        ]
    )

    if valid.sum() == 0:
        return None

    comply = (
        sla.eq("comply")
        .sum()
    )

    return float(
        comply
        / valid.sum()
        * 100
    )


# ==============================================================================
# PROBLEM TABLE
# ==============================================================================

def render_problem_table(df):

    if df is None or df.empty:
        return

    desc_col = find_column(
        df,
        [
            "ticket_symptom",
            "problem description",
            "description",
            "deskripsi permasalahan",
            "detailSubCategory",
            "subcategory",
            "subCategory",
            "category_split_2",
        ]
    )

    if desc_col is None:
        return

    data = df.loc[
        _valid_text_mask(
            df[desc_col]
        )
    ].copy()

    if data.empty:
        return

    summary = (
        data[desc_col]
        .astype(str)
        .str.strip()
        .value_counts()
        .head(10)
        .reset_index()
    )

    summary.columns = [
        "Deskripsi Permasalahan",
        "Jumlah Kasus",
    ]

    st.markdown(
        "### Deskripsi Permasalahan"
    )

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
        height=250,
    )


# ==============================================================================
# PENDING MEMBER
# ==============================================================================

def chart_pending_member(df):
    """
    Bar chart Top 3 anggota dengan tiket pending terbanyak.

    Jika ticket ID tersedia:
    menggunakan distinct ticket.
    """

    if df is None or df.empty:
        return None

    member_col = pick_best_column(
        df,
        [
            "member",
            "member_name",
            "nama_member",
            "nama anggota",
            "anggota",
            "agent",
            "agent_name",
            "technician",
            "technician_name",
            "nama teknisi",
            "teknisi",
            "assignee",
            "assigned_to",
            "assigned_name",
            "pic",
            "pic_name",
            "updated_by_name",
        ]
    )

    if member_col is None:
        return None

    # ------------------------------------------------------------------
    # TENTUKAN PENDING
    # ------------------------------------------------------------------

    if "date_pending" in df.columns:

        pending_mask = (
            df["date_pending"]
            .notna()
        )

    elif "pending_status" in df.columns:

        pending_mask = (
            df["pending_status"]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("pending")
        )

    else:

        status_col = find_column(
            df,
            [
                "ticket_status_name",
                "ticket_status",
                "status",
            ]
        )

        if status_col is None:
            return None

        pending_mask = (
            df[status_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains(
                "pending|open|waiting",
                na=False,
            )
        )

    temp = df.loc[
        pending_mask
    ].copy()

    if temp.empty:
        return None

    temp = temp.loc[
        _valid_text_mask(
            temp[member_col]
        )
    ].copy()

    if temp.empty:
        return None

    temp[member_col] = (
        temp[member_col]
        .astype(str)
        .str.strip()
    )

    id_col = _find_ticket_id_column(
        temp
    )

    if id_col is not None:

        member_count = (
            temp
            .groupby(member_col)[id_col]
            .nunique()
            .reset_index(
                name="Jumlah"
            )
        )

    else:

        member_count = (
            temp[member_col]
            .value_counts()
            .reset_index()
        )

        member_count.columns = [
            "Anggota",
            "Jumlah",
        ]

        member_count = (
            member_count
            .rename(
                columns={
                    member_col: "Anggota"
                }
            )
        )

    if member_count.empty:
        return None

    if "Anggota" not in member_count.columns:

        member_count = (
            member_count
            .rename(
                columns={
                    member_col: "Anggota"
                }
            )
        )

    member_count = (
        member_count
        .sort_values(
            "Jumlah",
            ascending=False,
        )
        .head(3)
        .sort_values(
            "Jumlah",
            ascending=True,
        )
    )

    if member_count.empty:
        return None

    fig = px.bar(
        member_count,
        x="Jumlah",
        y="Anggota",
        orientation="h",
        text="Jumlah",
    )

    fig.update_traces(
        marker_color=ORANGE_COLOR,
        textposition="inside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Tiket Pending: %{x}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        paper_bgcolor="white",
        height=400,
        margin=dict(
            l=10,
            r=30,
            t=55,
            b=20,
        ),
    )

    return fig


# ==============================================================================
# IMPACT BAR
# ==============================================================================

def chart_tingkat_dampak_bar(df):
    """
    Horizontal bar chart TOP 3 Tingkat Dampak.
    """

    if df is None or df.empty:
        return None

    impact_col = pick_best_column(
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
        return None

    impact_count = (
        _clean_category_series(
            df,
            impact_col,
        )
        .value_counts()
        .head(3)
    )

    if impact_count.empty:
        return None

    impact_count = (
        impact_count
        .sort_values(
            ascending=True
        )
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=impact_count.values,
            y=impact_count.index,
            orientation="h",
            text=impact_count.values,
            textposition="inside",
            marker=dict(
                color=GREEN_COLOR
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Jumlah Tiket: %{x}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=170,

        margin=dict(
            l=10,
            r=10,
            t=40,
            b=10,
        ),

        xaxis=dict(
            title=None,
            showgrid=True,
            zeroline=False,
        ),

        yaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            categoryorder="total ascending",
        ),

        showlegend=False,

        plot_bgcolor="white",
        paper_bgcolor="white",

        bargap=0.35,
    )

    return fig

# ==============================================================================
# PENDING CATEGORY
# ==============================================================================

def chart_pending_kategori(df):
    """
    Horizontal bar chart:
    Kategori ticket Pending.

    Menampilkan TOP 5 kategori.
    """

    pending_df = filter_pending_tickets(
        df
    )

    if pending_df.empty:
        return None

    cat_col = pick_best_column(
        pending_df,
        [
            "detailSubCategory2",
            "category",
            "category_split_1",
            "category_name",
        ]
    )

    if cat_col is None:
        return None

    clean = _clean_category_series(
        pending_df,
        cat_col,
    )

    if clean.empty:
        return None

    counts = (
        clean
        .value_counts()
        .head(5)
        .reset_index()
    )

    counts.columns = [
        "Kategori",
        "Jumlah",
    ]

    counts = counts.sort_values(
        "Jumlah",
        ascending=True,
    )

    fig = px.bar(
        counts,
        x="Jumlah",
        y="Kategori",
        orientation="h",
        text="Jumlah",
    )

    fig.update_traces(
        marker_color=RED_COLOR,
        textposition="inside",
        cliponaxis=False,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Ticket Pending: %{x}"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title="<b>Gangguan berdasarkan Kategori</b>",
        height=250,
        margin=dict(
            l=10,
            r=35,
            t=40,
            b=10,
        ),
        xaxis_title=None,
        yaxis_title=None,
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#EAEAEA",
        zeroline=False,
    )

    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
    )

    return fig

def filter_pending_tickets(df):
    """
    Mengambil hanya ticket yang sedang pending/investigasi.

    Prioritas:
    1. date_pending
    2. pending_status
    3. status / ticket_status / ticket_status_name
    """

    if df is None or df.empty:
        return pd.DataFrame()

    # ------------------------------------------------------------
    # PRIORITAS 1: date_pending
    # ------------------------------------------------------------

    date_pending_col = find_column(
        df,
        [
            "date_pending",
            "pending_date",
            "pending_at",
        ]
    )

    if date_pending_col is not None:

        mask = df[date_pending_col].notna()

        result = df.loc[mask].copy()

        if not result.empty:
            return result

    # ------------------------------------------------------------
    # PRIORITAS 2: pending_status
    # ------------------------------------------------------------

    pending_status_col = find_column(
        df,
        [
            "pending_status",
            "pending status",
            "status_pending",
        ]
    )

    if pending_status_col is not None:

        mask = (
            df[pending_status_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("pending")
        )

        result = df.loc[mask].copy()

        if not result.empty:
            return result

    # ------------------------------------------------------------
    # PRIORITAS 3: STATUS TICKET
    # ------------------------------------------------------------

    status_col = find_column(
        df,
        [
            "ticket_status_name",
            "ticket_status",
            "status",
            "status_name",
        ]
    )

    if status_col is None:
        return pd.DataFrame()

    status = (
        df[status_col]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    mask = status.str.contains(
        r"pending|open|waiting",
        regex=True,
        na=False,
    )

    return df.loc[mask].copy()