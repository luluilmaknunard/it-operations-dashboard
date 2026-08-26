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

RED_SEQUENCE = ["#B71C1C", "#C62828", "#D32F2F", "#E53935", "#EF5350", "#E57373"]
BLUE_SEQUENCE = ["#0D47A1", "#1565C0", "#1976D2", "#1E88E5", "#42A5F5", "#90CAF9"]


# ==============================================================================
# HELPER: pilih kolom kategori terbaik dari daftar kandidat
# ==============================================================================
def pick_best_column(df, candidates):
    """
    Cari kolom pertama dari `candidates` yang ada di df DAN punya isi (bukan cuma NaN/kosong).
    Dipakai supaya chart otomatis pakai kolom hierarki asli (category, subCategory,
    detailSubCategory, detailSubCategory2) kalau tersedia, baru fallback ke
    category_split_N / category_name kalau kolom aslinya tidak ada.
    """
    if df is None or df.empty:
        return None
    for col in candidates:
        if col in df.columns:
            cleaned = df[col].dropna().astype(str).str.strip()
            cleaned = cleaned[~cleaned.isin(["nan", "None", "", "null", "-"])]
            if not cleaned.empty:
                return col
    return None


def _clean_category_series(df, col):
    s = df[col].dropna().astype(str).str.strip()
    return s[~s.isin(["nan", "None", "", "null", "-"])]


# ==============================================================================
# 1. CHART DISTRIBUSI & PROPORSI
# ==============================================================================

def chart_distribusi_jenis(df):
    """Donut Chart: Distribusi Jenis Tiket (Gangguan vs Request)"""
    if df is None or df.empty:
        return None

    col = "ticket_type" if "ticket_type" in df.columns else None
    if not col:
        return None

    counts = df[col].value_counts().reset_index()
    counts.columns = [col, "Jumlah"]

    fig = px.pie(
        counts,
        values="Jumlah",
        names=col,
        hole=0.55,
        color_discrete_sequence=[ORANGE_COLOR, BLUE_COLOR, GREEN_COLOR, RED_COLOR],
        title="<b>Distribusi Jenis Tiket</b>",
    )
    fig.update_traces(
        textinfo="percent+value",
        textposition="inside",
        hovertemplate="<b>%{label}</b><br>Jumlah: %{value}<br>Persentase: %{percent}"
    )
    fig.update_layout(
        height=280,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def chart_tingkat_dampak_pie(df):
    """Pie Chart: Distribusi Tingkat Dampak / Impact Level"""
    if df is None or df.empty:
        return None

    impact_col = "impact_name" if "impact_name" in df.columns else (
        "priority" if "priority" in df.columns else None
    )

    if impact_col and impact_col in df.columns:
        counts = df[impact_col].value_counts().reset_index()
        counts.columns = [impact_col, "Jumlah"]

        fig = px.pie(
            counts,
            values="Jumlah",
            names=impact_col,
            color_discrete_sequence=[GREEN_COLOR, ORANGE_COLOR, RED_COLOR, PURPLE_COLOR],
            title="<b>Distribusi Tingkat Dampak</b>",
        )
        fig.update_traces(
            textinfo="percent+value",
            hovertemplate="<b>Dampak: %{label}</b><br>Total: %{value} (%{percent})"
        )
        fig.update_layout(
            height=280,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(l=10, r=10, t=40, b=10),
        )
        return fig
    return None


# ==============================================================================
# 2. CHART TREN & WAKTU
# ==============================================================================

def chart_trend_harian_multi(df):
    """
    Line Chart: Tren Jumlah Tiket Harian, 3 garis (Total Ticket, Request, Gangguan),
    sumbu-x = hari ke-N dihitung sejak tanggal paling awal pada data yang difilter
    (bukan tanggal kalender 1-31, supaya tetap benar walau data lintas bulan).
    """
    if df is None or df.empty:
        return None

    date_col = None
    for c in ['date_created_at', 'created_at', 'created_date', 'tanggal', 'date']:
        if c in df.columns:
            date_col = c
            break
    if not date_col:
        return None

    df_copy = df.copy()
    df_copy["date_dt"] = pd.to_datetime(df_copy[date_col], errors="coerce")
    df_copy = df_copy.dropna(subset=["date_dt"])
    if df_copy.empty:
        return None

    df_copy["calendar_date"] = df_copy["date_dt"].dt.normalize()
    min_date = df_copy["calendar_date"].min()
    df_copy["day_index"] = (df_copy["calendar_date"] - min_date).dt.days + 1

    all_days = pd.RangeIndex(1, int(df_copy["day_index"].max()) + 1)

    daily_total = df_copy.groupby("day_index").size().reindex(all_days, fill_value=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_total.index, y=daily_total.values,
        mode="lines", name="Total Ticket",
        line=dict(color=RED_COLOR, width=2, shape="hv"),
        hovertemplate="Hari ke-%{x}<br>Total: <b>%{y}</b><extra></extra>",
    ))

    if "ticket_type" in df_copy.columns:
        series_config = [("Request", ORANGE_COLOR), ("Gangguan", BLUE_COLOR)]
        for label, color in series_config:
            sub = df_copy[df_copy["ticket_type"].astype(str).str.strip().str.lower() == label.lower()]
            if sub.empty:
                continue
            daily_sub = sub.groupby("day_index").size().reindex(all_days, fill_value=0)
            fig.add_trace(go.Scatter(
                x=daily_sub.index, y=daily_sub.values,
                mode="lines", name=label,
                line=dict(color=color, width=1.5, shape="hv"),
                hovertemplate=f"Hari ke-%{{x}}<br>{label}: <b>%{{y}}</b><extra></extra>",
            ))

    fig.update_layout(
        title="<b>Tren Jumlah Tiket Harian</b>",
        height=280,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Hari Ke-",
        yaxis_title="Jumlah Tiket",
        plot_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#F0F0F0")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#F0F0F0")
    return fig

def calendar_heatmap(df):
    """
    Calendar heatmap bergaya kalender.
    Kolom  : Senin - Minggu
    Baris  : minggu
    Isi    : jumlah gangguan per hari
    """

    import pandas as pd
    import plotly.graph_objects as go

    if df is None or df.empty:
        return None

    # =========================================================
    # CARI KOLOM TANGGAL
    # =========================================================
    date_col = None

    for col in [
        "date_created_at",
        "created_at",
        "created_date",
        "Date",
        "date"
    ]:
        if col in df.columns:
            date_col = col
            break

    if date_col is None:
        return None

    # =========================================================
    # PARSE TANGGAL
    # =========================================================
    temp = df.copy()

    temp["_cal_date"] = pd.to_datetime(
        temp[date_col],
        dayfirst=True,
        errors="coerce"
    )

    temp = temp.dropna(subset=["_cal_date"])

    if temp.empty:
        return None

    temp["_cal_date"] = temp["_cal_date"].dt.normalize()

    # =========================================================
    # JUMLAH TICKET PER HARI
    # =========================================================
    daily = (
        temp.groupby("_cal_date")
        .size()
        .reset_index(name="Jumlah")
    )

    # =========================================================
    # RANGE KALENDER
    # =========================================================
    min_date = daily["_cal_date"].min()
    max_date = daily["_cal_date"].max()

    # Senin dari minggu pertama
    start_date = (
        min_date - pd.Timedelta(days=min_date.weekday())
    )

    # Minggu dari minggu terakhir
    end_date = (
        max_date + pd.Timedelta(days=6 - max_date.weekday())
    )

    dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    calendar = pd.DataFrame({
        "Tanggal": dates
    })

    calendar = calendar.merge(
        daily,
        left_on="Tanggal",
        right_on="_cal_date",
        how="left"
    )

    calendar["Jumlah"] = (
        calendar["Jumlah"]
        .fillna(0)
        .astype(int)
    )

    # =========================================================
    # POSISI GRID KALENDER
    # =========================================================
    calendar["Hari"] = calendar["Tanggal"].dt.weekday

    calendar["Minggu"] = (
        (calendar["Tanggal"] - start_date).dt.days // 7
    )

    # =========================================================
    # MATRKS JUMLAH
    # =========================================================
    pivot = calendar.pivot(
        index="Minggu",
        columns="Hari",
        values="Jumlah"
    )

    pivot = pivot.reindex(
        index=range(calendar["Minggu"].max() + 1),
        columns=range(7),
        fill_value=0
    )

    # =========================================================
    # TEXT DI DALAM CELL
    # =========================================================
    text_matrix = []

    for minggu in pivot.index:

        row = []

        for hari in pivot.columns:

            jumlah = int(pivot.loc[minggu, hari])

            # Tampilkan angka hanya kalau ada ticket
            if jumlah > 0:
                row.append(str(jumlah))
            else:
                row.append("")

        text_matrix.append(row)

    # =========================================================
    # LABEL MINGGU
    # =========================================================
    week_labels = [
        f"Minggu {i + 1}"
        for i in pivot.index
    ]

    day_labels = [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun"
    ]

    # =========================================================
    # HEATMAP
    # =========================================================
    fig = go.Figure()

    fig.add_trace(
        go.Heatmap(
            z=pivot.values,
            x=day_labels,
            y=week_labels,

            text=text_matrix,
            texttemplate="%{text}",

            textfont=dict(
                size=12
            ),

            hovertemplate=(
                "<b>%{x}</b><br>"
                "<b>%{y}</b><br>"
                "Jumlah Gangguan: %{z}"
                "<extra></extra>"
            ),

            colorscale=[
                [0.00, "#FFF5F5"],
                [0.20, "#FECACA"],
                [0.40, "#F87171"],
                [0.60, "#EF4444"],
                [0.80, "#DC2626"],
                [1.00, "#991B1B"],
            ],

            xgap=2,
            ygap=2,

            showscale=False
        )
    )

    # =========================================================
    # LAYOUT
    # =========================================================
    fig.update_layout(

        height=300,

        margin=dict(
            l=55,
            r=10,
            t=35,
            b=10
        ),

        xaxis=dict(
            side="top",
            fixedrange=True,
            showgrid=False
        ),

        yaxis=dict(
            autorange="reversed",
            fixedrange=True,
            showgrid=False,
            title=""
        ),

        plot_bgcolor="white",
        paper_bgcolor="white",

        font=dict(
            size=11
        )
    )

    return fig

# ==============================================================================
# 3. CHART KATEGORI & BREAKDOWN
# ==============================================================================

def chart_kategori_horizontal(df):
    """
    Horizontal Bar Chart: Jumlah Gangguan per Kategori (Device/Application/Network/
    Infrastructure/...). Prioritas kolom: detailSubCategory2 (bucket bersih dari
    dataset asli) -> category -> category_split_1 -> category_name (fallback lama).
    """
    if df is None or df.empty:
        return None

    cat_col = pick_best_column(df, ["detailSubCategory2", "category", "category_split_1", "category_name"])
    if not cat_col:
        return None

    counts = _clean_category_series(df, cat_col).value_counts().reset_index().head(5)
    counts.columns = [cat_col, "Jumlah"]
    counts = counts.sort_values(by="Jumlah", ascending=True)

    fig = px.bar(
        counts,
        x="Jumlah",
        y=cat_col,
        orientation="h",
        text="Jumlah",
        title="<b>Top 5 Kategori Gangguan</b>",
    )
    fig.update_traces(
        marker_color=RED_COLOR,
        textposition="outside",
        hovertemplate="Kategori: %{y}<br>Jumlah: <b>%{x} Kasus</b>"
    )
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=30, t=40, b=10),
        xaxis_title="Jumlah Kasus",
        yaxis_title="",
        plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F0F0F0")
    return fig

def chart_subkategori_bar(df, title_name="Subkategori", custom_col=None):
    """
    custom_col bisa berupa 1 nama kolom (str) ATAU list kandidat kolom, mis.
    ["detailSubCategory", "category_split_3"] -> otomatis pakai kolom pertama
    yang tersedia & ada isinya (lihat pick_best_column).
    """
    if df is None or df.empty or not custom_col:
        return None

    candidates = custom_col if isinstance(custom_col, (list, tuple)) else [custom_col]
    col = pick_best_column(df, candidates)
    if not col:
        return None

    clean_series = _clean_category_series(df, col)
    if clean_series.empty:
        return None

    counts = clean_series.value_counts().head(5).reset_index()
    counts.columns = ['Kategori', 'Jumlah']
    counts = counts.sort_values(by='Jumlah', ascending=True)

    max_val = counts['Jumlah'].max()
    colors = ['#D32F2F' if val == max_val else '#8E8E8E' for val in counts['Jumlah']]

    fig = px.bar(
        counts,
        x='Jumlah',
        y='Kategori',
        orientation='h',
        text='Jumlah',
        title=f"<b>{title_name}</b>"
    )

    fig.update_traces(
        marker_color=colors,
        textposition='outside',
        cliponaxis=False
    )

    fig.update_layout(
        xaxis_title="Jumlah Kasus",
        yaxis_title=None,
        margin=dict(l=10, r=30, t=40, b=10),
        height=280,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=11),
        title=dict(x=0.5, xanchor='center')
    )

    fig.update_xaxes(showgrid=True, gridcolor="#F0F0F0")

    return fig

def chart_department(df, key_prefix="default"):
    """
    Menampilkan horizontal bar chart jumlah gangguan
    berdasarkan Department.
    """

    if df is None or df.empty:
        st.info("Tidak ada data untuk ditampilkan.")
        return

    # ============================================================
    # CARI KOLOM DEPARTMENT
    # ============================================================

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
        st.info("Kolom department tidak ditemukan.")
        return

    # ============================================================
    # HITUNG JUMLAH TICKET PER DEPARTMENT
    # ============================================================

    dept_summary = (
        df
        .dropna(subset=[dept_col])
        .assign(
            department_display=lambda x: (
                x[dept_col]
                .astype(str)
                .str.strip()
            )
        )
        .groupby("department_display")
        .size()
        .reset_index(name="Jumlah Gangguan")
    )

    if dept_summary.empty:
        st.info("Tidak ada data department.")
        return

    # ============================================================
    # SORTING
    # ============================================================

    sort_key = f"{key_prefix}_dept_sort"

    sort_option = st.radio(
        "Urutan Data:",
        ["Terbanyak", "Tersedikit"],
        horizontal=True,
        key=sort_key
    )

    if sort_option == "Terbanyak":
        dept_summary = dept_summary.sort_values(
            "Jumlah Gangguan",
            ascending=False
        )
    else:
        dept_summary = dept_summary.sort_values(
            "Jumlah Gangguan",
            ascending=True
        )

    # ============================================================
    # TOP 10
    # ============================================================

    dept_summary = dept_summary.head(10)

    # Untuk chart:
    # department dengan jumlah terbesar berada di bagian atas
    chart_data = dept_summary.sort_values(
        "Jumlah Gangguan",
        ascending=True
    )

    # ============================================================
    # BUAT HORIZONTAL BAR CHART
    # ============================================================

    fig = px.bar(
        chart_data,
        x="Jumlah Gangguan",
        y="department_display",
        orientation="h",
        text="Jumlah Gangguan"
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Jumlah Gangguan: %{x:,}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        height=420,
        xaxis_title="Jumlah Gangguan",
        yaxis_title="",
        showlegend=False,
        margin=dict(
            l=10,
            r=40,
            t=20,
            b=20
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

def chart_layanan_treemap(df):
    """Treemap: Layanan dengan Tiket Terbanyak"""
    if df is None or df.empty:
        return None

    service_col = None
    for c in ['service_name', 'service', 'nama_layanan', 'layanan']:
        if c in df.columns:
            service_col = c
            break

    if not service_col:
        return None

    df_clean = df.copy()
    df_clean[service_col] = df_clean[service_col].astype(str).str.strip()
    df_clean = df_clean[~df_clean[service_col].isin(["nan", "None", "", "null"])]

    if df_clean.empty:
        return None

    counts = df_clean[service_col].value_counts().reset_index()
    counts.columns = [service_col, "count"]

    fig = px.treemap(
        counts,
        path=[service_col],
        values="count",
        color="count",
        color_continuous_scale=["#FFE5E5", "#FF4D4D", "#B30000"],
        title="<b>Layanan dengan Laporan Terbanyak</b>",
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Total Laporan: %{value}"
    )
    fig.update_layout(
        height=300,
        margin=dict(t=40, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ==============================================================================
# 4. CHART PERFORMA & TEKNISI
# ==============================================================================

def chart_peringkat_penyelesaian(df):
    """Bar Chart Peringkat Teknisi/Assignee Terbanyak"""
    if df is None or df.empty:
        return None

    col = None
    for c in ['updated_by_name']:
        if c in df.columns:
            col = c
            break

    if col and col in df.columns:
        counts = df[col].value_counts().reset_index().head(10)
        counts.columns = [col, "Jumlah"]
        counts = counts.sort_values(by="Jumlah", ascending=True)

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
            textposition="outside",
            hovertemplate="Staf: %{y}<br>Selesai: <b>%{x} Tiket</b>"
        )
        fig.update_layout(
            height=380,
            margin=dict(l=10, r=30, t=35, b=10),
            xaxis_title="Jumlah Tiket",
            yaxis_title="",
            plot_bgcolor="white",
        )
        fig.update_xaxes(showgrid=True, gridcolor="#F0F0F0")
        return fig
    return None

def chart_waktu_penyelesaian(df):

    """Bar Chart Distribusi Durasi Waktu Penyelesaian Tiket (Resolution Time)"""
    if df is None or df.empty or "resolution_time_group" not in df.columns:
        return None

    cat_order = ["≤ 30 Menit", "31 - 60 Menit", "61 - 120 Menit", "121 - 240 Menit", "> 240 Menit"]

    counts = df["resolution_time_group"].value_counts().reset_index()
    counts.columns = ["group", "count"]
    counts["group"] = pd.Categorical(counts["group"], categories=cat_order, ordered=True)
    counts = counts.sort_values("group", ascending=True)

    fig = px.bar(
        counts,
        x="count",
        y="group",
        orientation="h",
        text="count",
        title="<b>Distribusi Waktu Penyelesaian Tiket</b>",
    )
    fig.update_traces(
        marker_color="#E57373",
        textposition="outside"
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=30, t=35, b=10),
        xaxis_title="Jumlah Tiket",
        yaxis_title="",
        plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F0F0F0")
    return fig

def get_avg_response(df):

    response_col = find_column(
        df,
        [
            "response_minutes",
            "response_time",
            "response time",
            "waktu respon",
            "avg_response_time",
            "first_response_minutes"
        ]
    )

    if response_col is None:
        return None

    values = pd.to_numeric(
        df[response_col],
        errors="coerce"
    )

    values = values[
        values.notna() &
        (values >= 0)
    ]

    if values.empty:
        return None

    return values.mean()

def get_sla_achievement(df):

    sla_col = find_column(
        df,
        [
            "sla_status",
            "SLA_Status",
            "sla_status_name"
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

    valid = sla.isin([
        "breach",
        "comply"
    ])

    if valid.sum() == 0:
        return None

    comply = (sla == "comply").sum()

    return comply / valid.sum() * 100

def render_problem_table(df):


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
            "category_split_2"
        ]
    )

    if desc_col is None:
        return

    summary = (
        df[desc_col]
        .dropna()
        .astype(str)
        .str.strip()
        .value_counts()
        .head(10)
        .reset_index()
    )

    summary.columns = [
        "Deskripsi Permasalahan",
        "Jumlah Kasus"
    ]

    st.markdown(
        "### Deskripsi Permasalahan"
    )

    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
        height=250
    )

def find_column(df, candidates):

    """
    Mencari kolom pertama yang cocok berdasarkan nama kolom.
    Bisa menerima nama persis maupun variasi underscore/spasi.
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

def chart_pending_member(df):
    """
    Bar chart Top 3 anggota dengan tiket pending terbanyak.
    """

    if df is None or df.empty:
        return None

    # Cari kolom anggota
    member_col = None

    possible_columns = [
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

    for col in df.columns:

        clean = (
            str(col)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        if clean in [
            x.replace("_", " ")
            for x in possible_columns
        ]:
            member_col = col
            break

    if member_col is None:
        return None

    # Tentukan tiket pending
    if "date_pending" in df.columns:

        pending_mask = df["date_pending"].notna()

    elif "pending_status" in df.columns:

        pending_mask = (
            df["pending_status"]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("pending")
        )

    else:

        status_col = None

        for col in [
            "ticket_status_name",
            "ticket_status",
            "status",
        ]:
            if col in df.columns:
                status_col = col
                break

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

    temp[member_col] = (
        temp[member_col]
        .astype(str)
        .str.strip()
    )

    temp = temp[
        ~temp[member_col]
        .str.lower()
        .isin([
            "",
            "nan",
            "none",
            "null",
            "-",
        ])
    ]

    if temp.empty:
        return None

    # Hitung pending per anggota
    member_count = (
        temp[member_col]
        .value_counts()
        .reset_index()
    )

    member_count.columns = [
        "Anggota",
        "Jumlah",
    ]

    # TOP 3
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
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        height=400,
        margin=dict(
            l=10,
            r=30,
            t=55,
            b=20,
        ),
    )

    return fig

def chart_tingkat_dampak_bar(df):
    """
    Horizontal bar chart TOP 3 Tingkat Dampak.
    """

    if df is None or df.empty:
        return None

    impact_col = find_column(
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
        df[impact_col]
        .dropna()
        .astype(str)
        .str.strip()
        .value_counts()
        .head(3)
    )

    if impact_count.empty:
        return None

    # Terbesar tampil paling atas
    impact_count = impact_count.sort_values(
        ascending=True
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=impact_count.values,
            y=impact_count.index,
            orientation="h",
            text=impact_count.values,
            textposition="outside",
            marker=dict(
                color="#22c55e"
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Jumlah Tiket: %{x}"
                "<extra></extra>"
            )
        )
    )

    fig.update_layout(
        height=170,

        margin=dict(
            l=55,
            r=35,
            t=10,
            b=25
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


