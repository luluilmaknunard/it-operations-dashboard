import streamlit as st

def render_top_filters(df):
    """Mereset & merender dropdown filter bagian atas"""
    if df is None or df.empty:
        return df

    col_title, col_f1, col_f2, col_f3 = st.columns([2.5, 1, 1, 1])

    with col_f1:
        months = ["All"]
        if 'month' in df.columns:
            months += list(df['month'].dropna().unique())
        selected_month = st.selectbox("Bulan", months, key="filter_month")

    with col_f2:
        services = ["All"]
        if 'service_name' in df.columns:
            services += list(df['service_name'].dropna().unique())
        selected_service = st.selectbox("Nama Layanan", services, key="filter_service")

    with col_f3:
        departments = ["All"]
        if 'department' in df.columns:
            departments += list(df['department'].dropna().unique())
        selected_dept = st.selectbox("Nama Department", departments, key="filter_dept")

    filtered_df = df.copy()

    if selected_month != "All":
        filtered_df = filtered_df[filtered_df['month'] == selected_month]
    if selected_service != "All":
        filtered_df = filtered_df[filtered_df['service_name'] == selected_service]
    if selected_dept != "All":
        filtered_df = filtered_df[filtered_df['department'] == selected_dept]

    return filtered_df