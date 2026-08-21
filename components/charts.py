import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Konfigurasi Warna Utama
RED_COLOR = "#D32F2F"
BLUE_COLOR = "#1976D2"
ORANGE_COLOR = "#F57C00"
GREEN_COLOR = "#388E3C"
RED_SEQUENCE = ["#B71C1C", "#C62828", "#D32F2F", "#E53935", "#EF5350", "#E57373"]

def chart_distribusi_jenis(df):
    """Donut Chart: Distribusi Jenis Tiket"""
    col = 'ticket_type' if 'ticket_type' in df.columns else 'category_split_1'
    if col in df.columns:
        counts = df[col].value_counts().reset_index()
        fig = px.pie(counts, values='count', names=col, hole=0.6,
                     color_discrete_sequence=[ORANGE_COLOR, BLUE_COLOR],
                     title="<b>Distribusi Jenis Tiket</b>")
        fig.update_traces(textinfo='percent+value', textposition='inside')
        fig.update_layout(height=280, showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
        return fig
    return None

def chart_trend_harian_multi(df):
    """Line Chart: Tren Jumlah Tiket Harian Multi-Line"""
    if 'date_created_at' in df.columns:
        df_copy = df.copy()
        df_copy['day'] = pd.to_datetime(df_copy['date_created_at']).dt.day
        daily = df_copy.groupby(['day']).size().reset_index(name='Jumlah Ticket')
        
        fig = px.line(daily, x='day', y='Jumlah Ticket', markers=True,
                      title="<b>Tren Jumlah Tiket Harian</b>")
        fig.update_traces(line_color=RED_COLOR)
        fig.update_layout(
            height=280, margin=dict(l=10, r=10, t=40, b=10),
            xaxis_title="Day", yaxis_title="jumlah ticket/hari",
            plot_bgcolor="white"
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F0F0F0')
        return fig
    return None

def chart_kategori_horizontal(df):
    """Horizontal Bar Chart: Jumlah Gangguan per Kategori"""
    cat_col = 'category_split_1' if 'category_split_1' in df.columns else 'category_name'
    if cat_col in df.columns:
        counts = df[cat_col].value_counts().reset_index().head(5)
        counts = counts.sort_values(by='count', ascending=True)
        
        fig = px.bar(counts, x='count', y=cat_col, orientation='h',
                     title="<b>Jumlah Gangguan per Kategori</b>")
        fig.update_traces(marker_color=RED_COLOR)
        fig.update_layout(
            height=280, margin=dict(l=10, r=10, t=40, b=10),
            xaxis_title="Jumlah Kasus", yaxis_title="", plot_bgcolor="white"
        )
        return fig
    return None

def chart_tingkat_dampak_pie(df):
    """Pie Chart: Distribusi Tingkat Dampak"""
    if 'impact_name' in df.columns:
        counts = df['impact_name'].value_counts().reset_index()
        fig = px.pie(counts, values='count', names='impact_name',
                     color_discrete_sequence=[GREEN_COLOR, "#FBC02D", RED_COLOR],
                     title="<b>Distribusi Tingkat Dampak</b>")
        fig.update_traces(textinfo='percent+value')
        fig.update_layout(height=280, showlegend=False, margin=dict(l=10, r=10, t=40, b=10))
        return fig
    return None

import plotly.express as px

def chart_layanan_treemap(df):
    """Membentuk Treemap Layanan Terbanyak dengan penanganan tipe data campur (str & int)."""
    if df is None or df.empty or 'service_name' not in df.columns:
        return None

    # 1. Buat copy DataFrame agar aman
    df_clean = df.copy()

    # 2. PERBAIKAN: Paksa semua data service_name menjadi String dan hapus nilai kosong (NaN)
    df_clean['service_name'] = df_clean['service_name'].astype(str).str.strip()
    df_clean = df_clean[~df_clean['service_name'].isin(['nan', 'None', '', 'null'])]

    if df_clean.empty:
        return None

    # 3. Hitung jumlah kemunculan per layanan
    counts = df_clean['service_name'].value_counts().reset_index()
    counts.columns = ['service_name', 'count']

    # 4. Render Plotly Treemap
    fig = px.treemap(
        counts, 
        path=['service_name'], 
        values='count', 
        color='count',
        color_continuous_scale=['#FFE5E5', '#FF4D4D', '#B30000'],
        title="<b>Layanan dengan Laporan Gangguan Terbanyak</b>"
    )
    
    fig.update_layout(
        margin=dict(t=40, l=10, r=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def chart_subkategori_bar(df, title_name):
    """Horizontal Bar Chart: Break down Subkategori (Device, Network, dll)"""
    cat_col = 'category_split_2' if 'category_split_2' in df.columns else 'category_name'
    if cat_col in df.columns:
        counts = df[cat_col].value_counts().reset_index().head(5)
        counts = counts.sort_values(by='count', ascending=True)
        fig = px.bar(counts, x='count', y=cat_col, orientation='h',
                     title=f"<b>{title_name}</b>")
        fig.update_traces(marker_color=RED_COLOR)
        fig.update_layout(height=240, margin=dict(l=10, r=10, t=35, b=10),
                          xaxis_title="Jumlah Case", yaxis_title="", plot_bgcolor="white")
        return fig
    return None

def chart_kalender_heatmap(df):
    """Heatmap Kalender Bulanan"""
    fig = go.Figure(data=go.Heatmap(
        z=[[10, 20, 30, 40, 15, 12, 5],
           [40, 27, 30, 37, 33, 14, 10],
           [26, 37, 33, 24, 20, 22, 11]],
        x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        y=['14', '15', '16'],
        colorscale='Reds'
    ))
    fig.update_layout(title="<b>Kalender</b>", height=240, margin=dict(l=10, r=10, t=35, b=10))
    return fig

def chart_peringkat_penyelesaian(df):
    """Bar Chart Peringkat Teknisi/Anggota"""
    if 'assignee' in df.columns:
        counts = df['assignee'].value_counts().reset_index().head(10)
        counts = counts.sort_values(by='count', ascending=True)
        fig = px.bar(counts, x='count', y='assignee', orientation='h',
                     title="<b>Peringkat Penyelesaian Tiket</b>")
        fig.update_traces(marker_color=BLUE_COLOR)
        fig.update_layout(height=480, margin=dict(l=10, r=10, t=35, b=10),
                          xaxis_title="", yaxis_title="", plot_bgcolor="white")
        return fig
    return None

def chart_waktu_penyelesaian(df):
    """Bar Chart Distribusi Waktu Penyelesaian Tiket"""
    categories = ['≤ 30 Menit', '31 - 60 Menit', '61 - 120 Menit', '> 240 Menit']
    values = [650, 320, 190, 210]
    fig = px.bar(x=values, y=categories, orientation='h', title="<b>Distribusi Waktu Penyelesaian Tiket</b>")
    fig.update_traces(marker_color="#E57373")
    fig.update_layout(height=240, margin=dict(l=10, r=10, t=35, b=10),
                      xaxis_title="Jumlah Ticket", yaxis_title="", plot_bgcolor="white")
    return fig