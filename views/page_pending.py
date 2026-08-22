import streamlit as st
from components.filters import render_top_filters
from components.metrics import render_kpi_cards

def render(df_raw):
    # 1. Header & Filter Atas
    col_head, col_filters = st.columns([1, 2.5])
    with col_head:
        st.markdown("## **🔍 Pending Investigation**")
    with col_filters:
        # Panggil fungsi filter di sini
        df_filtered = render_top_filters(df_raw, key_prefix="pending")

    st.markdown("<br>", unsafe_allow_html=True)

    if df_filtered is None or df_filtered.empty:
        st.warning("Data tidak tersedia untuk filter yang dipilih.")
        return

    # 2. KPI Cards
    render_kpi_cards(df_filtered)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Filter Spesifik untuk Tiket Pending/Open (jika ada kolom status)
    if "status" in df_filtered.columns:
        df_pending = df_filtered[
            df_filtered["status"]
            .astype(str)
            .str.lower()
            .isin(["pending", "open", "in progress"])
        ]
    else:
        df_pending = df_filtered

    # 4. Tabel Detail Tiket Pending
    st.markdown(f"##### **Daftar Tiket dalam Investigasi ({len(df_pending):,} Tiket)**")
    st.dataframe(df_pending, use_container_width=True)