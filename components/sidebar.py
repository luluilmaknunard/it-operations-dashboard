import streamlit as st
import pandas as pd
import io

from src.data_cleaning import clean_sensitive_data
from src.ticket_classifier import classify_tickets


def render_sidebar():
    selected_dept = "Semua"

    # ============================================================
    # 1. NAVIGATION
    # ============================================================
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

    # ============================================================
    # 2. UPLOAD DATA
    # ============================================================
    st.sidebar.subheader("📤 Upload Data Raw")
    allowed_types = ["csv", "xlsx", "xls", "xlsm", "xlsb", "tsv", "json", "txt"]
    uploaded_file = st.sidebar.file_uploader("Upload File Tiket", type=allowed_types)

    # ============================================================
    # 3. PROSES FILE (HANYA DILAKUKAN JIKA FILE BARU DI-UPLOAD)
    # ============================================================
    if uploaded_file is not None:
        # Tanda/ID Unik File (Berdasarkan Nama dan Ukuran File)
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        
        # Cek apakah file ini SUDAH PERNAH diproses sebelumnya?
        if st.session_state.get("current_file_id") != file_id:
            try:
                file_name = uploaded_file.name.lower()
                df = None

                # --- BACA FILE ---
                if file_name.endswith((".csv", ".tsv", ".txt")):
                    sep = "\t" if file_name.endswith(".tsv") else ","
                    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
                    for encoding in encodings:
                        try:
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding=encoding, sep=sep)
                            break
                        except Exception:
                            continue
                elif file_name.endswith((".xlsx", ".xls", ".xlsm", ".xlsb")):
                    df = pd.read_excel(uploaded_file)
                elif file_name.endswith(".json"):
                    df = pd.read_json(uploaded_file)

                if df is not None and not df.empty:
                    # --- 1. CLEANING DATA (1x Saja) ---
                    with st.spinner("🧹 Membersihkan data sensitif..."):
                        df_cleaned = clean_sensitive_data(df)

                    # --- 2. CEK & KLASIFIKASI AI (1x Saja) ---
                    has_ticket_type = (
                        "ticket_type" in df_cleaned.columns and
                        df_cleaned["ticket_type"].notna().any()
                    )

                    if not has_ticket_type:
                        with st.spinner("🤖 AI lokal sedang mengklasifikasikan tiket..."):
                            df_cleaned = classify_tickets(df_cleaned)
                    else:
                        df_cleaned["ticket_type"] = (
                            df_cleaned["ticket_type"]
                            .astype(str)
                            .str.strip()
                            .str.title()
                        )

                    # --- 3. SIMPAN HASIL AKHIR KE SESSION STATE & KUNCI ---
                    st.session_state["df_raw"] = df_cleaned
                    st.session_state["current_file_id"] = file_id
                    st.session_state["uploaded_file_name"] = uploaded_file.name

            except Exception as e:
                st.sidebar.error(f"❌ Gagal memproses file:\n{e}")

    # ============================================================
    # 4. AMBIL DATA DARI SESSION STATE
    # ============================================================
    df_raw = st.session_state.get("df_raw", None)

    # ============================================================
    # 5. GLOBAL FILTER UI
    # ============================================================
    if df_raw is not None:
        st.sidebar.success(f"✅ Data Siap: {len(df_raw):,} baris")
        
        # Tampilkan distribusi tiket
        if "ticket_type" in df_raw.columns:
            ticket_counts = df_raw["ticket_type"].value_counts()
            st.sidebar.markdown("**📊 Hasil Klasifikasi**")
            for ticket_type, count in ticket_counts.items():
                st.sidebar.write(f"- {ticket_type}: {count:,}")

        st.sidebar.markdown("---")
        st.sidebar.subheader("🌐 Global Filter")

        # Cari kolom untuk dijadikan filter
        target_col = None
        if "department" in df_raw.columns:
            target_col = "department"
        elif "unit_name" in df_raw.columns:
            target_col = "unit_name"

        if target_col:
            opts = ["Semua"] + sorted(list(df_raw[target_col].dropna().astype(str).unique()))
            selected_dept = st.sidebar.selectbox(
                "Filter Department/Unit:",
                opts,
                key="global_filter_select"
            )

    return menu, df_raw, selected_dept