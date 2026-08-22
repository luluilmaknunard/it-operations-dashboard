import streamlit as st
from components.filters import render_top_filters
from components.metrics import render_kpi_cards
from components.charts import (
    chart_peringkat_penyelesaian,
    chart_waktu_penyelesaian,
)

def render(df_raw):
    # Header & Filter (Kirim key_prefix="perf")
    col_head, col_filters = st.columns([1, 2.5])
    with col_head:
        st.markdown("## **⚡ IT Performance & SLA**")
    with col_filters:
        df_filtered = render_top_filters(df_raw, key_prefix="perf")

    st.markdown("<br>", unsafe_allow_html=True)

    if df_filtered is None or df_filtered.empty:
        st.warning("Data tidak tersedia untuk filter yang dipilih.")
        return

    # KPI Cards
    render_kpi_cards(df_filtered)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        fig_rank = chart_peringkat_penyelesaian(df_filtered)
        if fig_rank is not None:
            st.plotly_chart(fig_rank, use_container_width=True)
        else:
            st.info("Data Peringkat Teknisi tidak tersedia.")

    with c2:
        fig_waktu = chart_waktu_penyelesaian(df_filtered)
        if fig_waktu is not None:
            st.plotly_chart(fig_waktu, use_container_width=True)
        else:
            st.info("Data Waktu Penyelesaian tidak tersedia.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### **Preview Data Performance**")
    st.dataframe(df_filtered.head(10), use_container_width=True)