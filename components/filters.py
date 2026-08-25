import streamlit as st
import pandas as pd
from src.ticket_classifier import classify_tickets
from src.network_classifier import classify_network_component


def render_top_filters(df, key_prefix="default"):
    if df is None or df.empty:
        return df

    df_working = df.copy()

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        date_col = None
        if "date_created_at" in df_working.columns:
            date_col = "date_created_at"
        elif "Date" in df_working.columns:
            date_col = "Date"
        else:
            for col in df_working.columns:
                if str(col).strip().lower() in ["created_at", "created_date", "tanggal", "date"]:
                    date_col = col
                    break
        
        if date_col:
            df_working["datetime_filter"] = pd.to_datetime(
                df_working[date_col], 
                format="%d.%m.%Y %H:%M:%S",
                errors="coerce"
            )
            
            null_mask = df_working["datetime_filter"].isna()
            if null_mask.any():
                df_working.loc[null_mask, "datetime_filter"] = pd.to_datetime(
                    df_working.loc[null_mask, date_col],
                    dayfirst=True,
                    errors="coerce"
                )
            
            df_valid = df_working.dropna(subset=["datetime_filter"]).copy()
            
            if not df_valid.empty:
                df_valid["sort_key"] = df_valid["datetime_filter"].dt.strftime("%Y-%m")
                df_valid["month_fmt"] = df_valid["datetime_filter"].dt.strftime("%B %Y")
                
                unique_months = (
                    df_valid.groupby(["sort_key", "month_fmt"])
                    .size()
                    .reset_index()
                    .sort_values(by="sort_key", ascending=True)["month_fmt"]
                    .unique()
                    .tolist()
                )
                
                month_list = ["All"] + unique_months
                df_working["month_filter_name"] = df_working["datetime_filter"].dt.strftime("%B %Y")
            else:
                month_list = ["All"]
        else:
            month_list = ["All"]
            
        month_key = f"{key_prefix}_f_month"
        if month_key in st.session_state and st.session_state[month_key] not in month_list:
            st.session_state[month_key] = "All"

        selected_month = st.selectbox("Bulan", month_list, key=month_key)

    with col_f2:
        service_col = None
        for col in df_working.columns:
            if str(col).strip().lower() in ["service_name", "service", "nama_layanan", "nama layanan", "layanan"]:
                service_col = col
                break

        service_list = ["All"] + sorted([str(x) for x in df_working[service_col].dropna().unique()]) if service_col else ["All"]
        selected_service = st.selectbox("Nama Layanan", service_list, key=f"{key_prefix}_f_service")

    with col_f3:
        dept_col = None
        for col in df_working.columns:
            if str(col).strip().lower() in ["department", "dept", "nama_department", "nama department"]:
                dept_col = col
                break
        
        department_list = ["All"] + sorted([str(x) for x in df_working[dept_col].dropna().unique()]) if dept_col else ["All"]
        selected_dept = st.selectbox("Nama Department", department_list, key=f"{key_prefix}_f_dept")

    with col_f4:
        unit_col = None
        for col in df_working.columns:
            col_clean = str(col).strip().lower().replace(" ", "_")
            if col_clean in ["unit_name", "unit", "nama_unit", "unitname", "nama unit"]:
                unit_col = col
                break

        unit_list = ["All"] + sorted([str(x) for x in df_working[unit_col].dropna().unique()]) if unit_col else ["All"]
        selected_unit = st.selectbox("Unit Name", unit_list, key=f"{key_prefix}_f_unit")

    filtered_df = df_working.copy()

    if selected_month != "All" and "month_filter_name" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["month_filter_name"] == selected_month]

    if selected_service != "All" and service_col:
        filtered_df = filtered_df[filtered_df[service_col].astype(str) == selected_service]

    if selected_dept != "All" and dept_col:
        filtered_df = filtered_df[filtered_df[dept_col].astype(str) == selected_dept]

    if selected_unit != "All" and unit_col:
        filtered_df = filtered_df[filtered_df[unit_col].astype(str) == selected_unit]

    cols_to_drop = [c for c in ["datetime_filter", "sort_key", "month_filter_name"] if c in filtered_df.columns]
    if cols_to_drop:
        filtered_df = filtered_df.drop(columns=cols_to_drop)

    return filtered_df

