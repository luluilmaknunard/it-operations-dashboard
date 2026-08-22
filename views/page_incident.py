import streamlit as st
from components.filters import render_top_filters
from components.charts import (
    chart_subkategori_bar,
    chart_trend_harian_multi,
    chart_tingkat_dampak_pie
)

def render(df_raw):
    st.markdown("## **🚨 Incident Analytics**")
    
    if df_raw is None or df_raw.empty:
        st.warning("Data raw tidak tersedia. Silakan upload file terlebih dahulu.")
        return

    # Render Filter
    df_filtered = render_top_filters(df_raw)
    st.markdown("<br>", unsafe_allow_html=True)

    # Baris 1: Subkategori Charts
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # Menghapus 'filter_category' yang menyebabkan TypeError
        fig1 = chart_subkategori_bar(df_filtered, "Device Breakdown")
        if fig1 is not None:
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Data Device tidak tersedia.")

    with c2:
        fig2 = chart_subkategori_bar(df_filtered, "Network Breakdown")
        if fig2 is not None:
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Data Network tidak tersedia.")

    with c3:
        fig3 = chart_subkategori_bar(df_filtered, "Application Breakdown")
        if fig3 is not None:
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Data Application tidak tersedia.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Baris 2: Tren & Dampak
    c4, c5 = st.columns([2, 1])
    with c4:
        fig_trend = chart_trend_harian_multi(df_filtered)
        if fig_trend is not None:
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Data Tren Insiden tidak tersedia.")

    with c5:
        fig_dampak = chart_tingkat_dampak_pie(df_filtered)
        if fig_dampak is not None:
            st.plotly_chart(fig_dampak, use_container_width=True)
        else:
            st.info("Data Tingkat Dampak tidak tersedia.")