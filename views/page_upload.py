import streamlit as st
from src.data_cleaning import clean_ticket_data
from src.data_transformation import transform_kpi_data
from src.database import save_to_supabase

def render():
    st.title("📤 Form Ingestion Data Raw")
    
    uploaded_file = st.file_uploader("Upload File Tiket (CSV/Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        if st.button("Proses Data", type="primary"):
            with st.spinner("Membersihkan & Mentransformasi Data..."):
                # 1. Cleaning & Transformation
                df_clean = clean_ticket_data(uploaded_file)
                df_transformed = transform_kpi_data(df_clean)
                
                # 2. Save Session & Database
                st.session_state['df_raw'] = df_transformed
                save_to_supabase(df_transformed)
                
                st.success("✅ Data berhasil diproses dan disimpan!")