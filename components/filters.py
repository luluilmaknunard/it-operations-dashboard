import streamlit as st
import pandas as pd

def render_top_filters(df, key_prefix="default"):
    """
    Merender 4 filter dalam 4 kolom sejajar (Bulan, Layanan, Department, Unit Name).
    Menggunakan key_prefix agar unik di setiap halaman dashboard.
    """
    if df is None or df.empty:
        return df

    df_working = df.copy()

    # 4 Kolom Filter Pas
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    # 1. Filter Bulan
    with col_f1:
        date_col = None
        for col in df_working.columns:
            if str(col).strip().lower() in ['date_created_at', 'created_at', 'created_date', 'tanggal', 'date']:
                date_col = col
                break
        
        if date_col:
            df_working['month_name'] = pd.to_datetime(df_working[date_col], errors='coerce').dt.strftime('%B %Y')
            month_list = ["All"] + sorted([m for m in df_working['month_name'].dropna().unique() if str(m) != 'nan'])
        else:
            month_list = ["All"]
        selected_month = st.selectbox("Bulan", month_list, key=f"{key_prefix}_f_month")

    # 2. Filter Nama Layanan
    with col_f2:
        service_col = None
        for col in df_working.columns:
            if str(col).strip().lower() in ['service_name', 'service', 'nama_layanan', 'nama layanan', 'layanan']:
                service_col = col
                break

        service_list = ["All"] + sorted([str(x) for x in df_working[service_col].dropna().unique()]) if service_col else ["All"]
        selected_service = st.selectbox("Nama Layanan", service_list, key=f"{key_prefix}_f_service")

    # 3. Filter Nama Department
    with col_f3:
        dept_col = None
        for col in df_working.columns:
            if str(col).strip().lower() in ['department', 'dept', 'nama_department', 'nama department']:
                dept_col = col
                break
        
        department_list = ["All"] + sorted([str(x) for x in df_working[dept_col].dropna().unique()]) if dept_col else ["All"]
        selected_dept = st.selectbox("Nama Department", department_list, key=f"{key_prefix}_f_dept")

    # 4. Filter Unit Name
    with col_f4:
        unit_col = None
        for col in df_working.columns:
            col_clean = str(col).strip().lower().replace(" ", "_")
            if col_clean in ['unit_name', 'unit', 'nama_unit', 'unitname', 'nama unit']:
                unit_col = col
                break

        unit_list = ["All"] + sorted([str(x) for x in df_working[unit_col].dropna().unique()]) if unit_col else ["All"]
        selected_unit = st.selectbox("Unit Name", unit_list, key=f"{key_prefix}_f_unit")

    # Filtering Logic
    filtered_df = df_working.copy()

    if selected_month != "All" and 'month_name' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['month_name'] == selected_month]

    if selected_service != "All" and service_col:
        filtered_df = filtered_df[filtered_df[service_col].astype(str) == selected_service]

    if selected_dept != "All" and dept_col:
        filtered_df = filtered_df[filtered_df[dept_col].astype(str) == selected_dept]

    if selected_unit != "All" and unit_col:
        filtered_df = filtered_df[filtered_df[unit_col].astype(str) == selected_unit]

    return filtered_df