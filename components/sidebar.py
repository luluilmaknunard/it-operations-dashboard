import streamlit as st
import pandas as pd

def render_sidebar():
    st.sidebar.title("Navigation")
    
    menu = st.sidebar.radio(
        "Menu Navigasi",
        [
            "🏠 Executive Overview",
            "🚨 Incident Analytics",
            "⚡ IT Performance & SLA",
            "🔍 Pending Investigation"
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📤 Upload Data Raw")
    
    allowed_types = ['csv', 'xlsx', 'xls', 'xlsm', 'xlsb', 'tsv', 'json', 'txt']
    uploaded_file = st.sidebar.file_uploader("Upload File Tiket", type=allowed_types)
    
    if uploaded_file is not None:
        file_name = uploaded_file.name.lower()
        if not file_name.endswith(('.pdf', '.docx', '.doc')):
            try:
                if file_name.endswith(('.csv', '.tsv', '.txt')):
                    sep = '\t' if file_name.endswith('.tsv') else ','
                    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
                    df = None
                    for enc in encodings:
                        try:
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding=enc, sep=sep)
                            break
                        except Exception:
                            continue
                elif file_name.endswith(('.xlsx', '.xls', '.xlsm', '.xlsb')):
                    df = pd.read_excel(uploaded_file)
                elif file_name.endswith('.json'):
                    df = pd.read_json(uploaded_file)

                if df is not None:
                    st.session_state['df_raw'] = df
                    st.sidebar.success(f"✅ Data Siap: {len(df):,} baris")
            except Exception as e:
                st.sidebar.error(f"Gagal membaca file: {e}")
                
    return menu