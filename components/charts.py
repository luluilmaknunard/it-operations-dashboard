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
# 1. CHART DISTRIBUSI & PROPORSI
# ==============================================================================

def chart_distribusi_jenis(df):
    """Donut Chart: Distribusi Jenis Tiket (Incident vs Request vs Others)"""
    if df is None or df.empty:
        return None

    col = "ticket_type" if "ticket_type" in df.columns else (
        "category_split_1" if "category_split_1" in df.columns else None
    )
    
    if col and col in df.columns:
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
    return None


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
    """Line Chart: Tren Jumlah Tiket Harian"""
    if df is None or df.empty:
        return None

    date_col = None
    for c in ['date_created_at', 'created_at', 'created_date', 'tanggal', 'date']:
        if c in df.columns:
            date_col = c
            break

    if date_col:
        df_copy = df.copy()
        df_copy["date_dt"] = pd.to_datetime(df_copy[date_col], errors="coerce")
        df_filtered = df_copy.dropna(subset=["date_dt"])

        if df_filtered.empty:
            return None

        # Group per hari tanggal
        df_filtered["day"] = df_filtered["date_dt"].dt.day
        daily = df_filtered.groupby("day").size().reset_index(name="Jumlah Ticket")
        daily["day"] = daily["day"].astype(int)

        fig = px.line(
            daily,
            x="day",
            y="Jumlah Ticket",
            markers=True,
            title="<b>Tren Jumlah Tiket Harian</b>",
        )
        fig.update_traces(
            line=dict(color=RED_COLOR, width=3),
            marker=dict(size=7, color=RED_COLOR),
            hovertemplate="Tanggal %{x}: <b>%{y} Tiket</b>"
        )
        fig.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis_title="Hari Ke-",
            yaxis_title="Jumlah Tiket",
            plot_bgcolor="white",
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#F0F0F0", dtick=1)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#F0F0F0")
        return fig
    return None


def chart_kalender_heatmap(df):
    """
    Heatmap Kalender Persis Power BI:
    - Tanpa error st
    - Margin rapi (judul tidak bertumpuk)
    """
    if df is None or df.empty:
        return None

    df_clean = df.copy()

    # 1. Cari kolom tanggal
    date_col = None
    if 'Date' in df_clean.columns:
        date_col = 'Date'
    else:
        for c in df_clean.columns:
            if str(c).strip().lower() in ['date_created_at', 'created_at', 'created_date', 'tanggal', 'date']:
                date_col = c
                break

    if not date_col:
        return None

    # 2. Parsing tanggal paksa DD/MM/YYYY
    df_clean['Date_Parsed'] = pd.to_datetime(df_clean[date_col], dayfirst=True, errors='coerce')
    df_clean = df_clean.dropna(subset=['Date_Parsed'])

    if df_clean.empty:
        return None

    # 3. Hitung Minggu ke-N dalam bulan
    day_of_month = df_clean['Date_Parsed'].dt.day
    first_day_of_month = df_clean['Date_Parsed'].dt.to_period('M').dt.to_timestamp()
    first_day_weekday = first_day_of_month.dt.weekday
    
    df_clean['Week_In_Month'] = ((day_of_month + first_day_weekday - 1) // 7) + 1
    df_clean['Week_Day'] = df_clean['Date_Parsed'].dt.strftime('%a')

    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # 4. Aggregasi Pivot Table
    heatmap_matrix = df_clean.groupby(['Week_In_Month', 'Week_Day']).size().unstack(fill_value=0)

    for d in days_order:
        if d not in heatmap_matrix.columns:
            heatmap_matrix[d] = 0

    heatmap_matrix = heatmap_matrix[days_order].sort_index(ascending=True)

    if heatmap_matrix.empty:
        return None

    week_labels = [str(int(w)) for w in heatmap_matrix.index]
    z_values = heatmap_matrix.values
    text_values = [[str(val) if val > 0 else "" for val in row] for row in z_values]

    # 5. Render Plotly Heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=z_values,
            x=heatmap_matrix.columns,
            y=week_labels,
            text=text_values,
            texttemplate="%{text}",
            textfont=dict(size=11, color="black"),
            colorscale=[
                [0.0, "#FFEBEE"],
                [0.3, "#FFCDD2"],
                [0.7, "#E53935"],
                [1.0, "#B71C1C"]
            ],
            showscale=False,
            hovertemplate="Hari: <b>%{x}</b><br>Minggu ke-<b>%{y}</b><br>Jumlah: <b>%{z} Kasus</b><extra></extra>",
            xgap=1,
            ygap=1
        )
    )

    fig.update_layout(
        title={
            'text': "<b>Kalender</b>",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=14)
        },
        height=280,
        margin=dict(l=10, r=10, t=55, b=20),
        xaxis=dict(side="top", tickfont=dict(size=11)),
        yaxis=dict(
            autorange="reversed", 
            type="category",
            title=dict(text="Minggu ke-", font=dict(size=11))
        ),
        plot_bgcolor="white"
    )

    return fig 



# ==============================================================================
# 3. CHART KATEGORI & BREAKDOWN
# ==============================================================================

def chart_kategori_horizontal(df):
    """Horizontal Bar Chart: Top 5 Kategori Gangguan"""
    if df is None or df.empty:
        return None

    cat_col = "category_split_1" if "category_split_1" in df.columns else (
        "category_name" if "category_name" in df.columns else None
    )
    
    if cat_col and cat_col in df.columns:
        counts = df[cat_col].value_counts().reset_index().head(5)
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
    return None


def chart_subkategori_bar(df, title_name="Breakdown Subkategori", filter_category=None):
    """Horizontal Bar Chart: Breakdown Subkategori (Support Filter Utama)"""
    if df is None or df.empty:
        return None

    df_filtered = df.copy()
    
    # Filter opsional berdasarkan Kategori Utama
    if filter_category and filter_category != "Semua" and "category_split_1" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["category_split_1"] == filter_category]

    cat_col = "category_split_2" if "category_split_2" in df_filtered.columns else (
        "sub_category" if "sub_category" in df_filtered.columns else "category_name"
    )
    
    if cat_col in df_filtered.columns:
        counts = df_filtered[cat_col].value_counts().reset_index().head(5)
        counts.columns = [cat_col, "Jumlah"]
        counts = counts.sort_values(by="Jumlah", ascending=True)

        if counts.empty:
            return None

        fig = px.bar(
            counts,
            x="Jumlah",
            y=cat_col,
            orientation="h",
            text="Jumlah",
            title=f"<b>{title_name}</b>",
        )
        fig.update_traces(
            marker_color=ORANGE_COLOR,
            textposition="outside",
            hovertemplate="Subkategori: %{y}<br>Jumlah: <b>%{x}</b>"
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
    return None


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

    # UTAMAKAN updated_by_name
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
    if df is None or df.empty:
        return None

    cat_order = ["≤ 30 Menit", "31 - 60 Menit", "61 - 120 Menit", "121 - 240 Menit", "> 240 Menit"]

    if "resolution_time_group" in df.columns:
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
    else:
        # Fallback layout jika kolom resolution_time_group belum di-compute
        fig = px.bar(
            x=[0, 0, 0, 0, 0],
            y=cat_order,
            orientation="h",
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