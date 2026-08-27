import io
import streamlit as st
import pandas as pd

from src.data_cleaning import clean_sensitive_data
from src.data_transformation import transform_data_and_kpi


@st.cache_data(show_spinner=False)
def _process_uploaded_file(file_bytes: bytes, file_name: str):
    """
    Baca + bersihkan + transformasi + klasifikasi ML data mentah.

    Di-cache oleh Streamlit berdasarkan (file_bytes, file_name): selama file
    yang sama diupload, hasilnya dipakai dari cache -> tidak dihitung ulang
    saat user pindah halaman / widget lain berinteraksi (yang memicu Streamlit
    rerun script dari atas). Perhitungan berat (cleaning, KPI, model ML) hanya
    benar-benar jalan sekali per file baru.
    """
    file_name_lower = file_name.lower()
    df = None

    if file_name_lower.endswith((".csv", ".tsv", ".txt")):
        sep = "\t" if file_name_lower.endswith(".tsv") else ","
        for encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding, sep=sep)
                break
            except Exception:
                continue
    elif file_name_lower.endswith((".xlsx", ".xls", ".xlsm", ".xlsb")):
        df = pd.read_excel(io.BytesIO(file_bytes))
    elif file_name_lower.endswith(".json"):
        df = pd.read_json(io.BytesIO(file_bytes))

    if df is None or df.empty:
        return None

    df_cleaned = clean_sensitive_data(df)
    df_final = transform_data_and_kpi(df_cleaned)
    return df_final


def render_sidebar():
    # ============================================================
    # 1. NAVIGATION
    # ============================================================
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio(
        "Menu Navigasi",
        [
            "Executive Overview",
            "Incident Analytics",
            "IT Performance & SLA",
            "Pending Investigation",
        ],
    )

    st.sidebar.markdown("---")

    # ============================================================
    # 2. UPLOAD DATA
    # ============================================================
    st.sidebar.subheader("📤 Upload Data Raw")
    allowed_types = ["csv", "xlsx", "xls", "xlsm", "xlsb", "tsv", "json", "txt"]
    uploaded_file = st.sidebar.file_uploader("Upload File Tiket", type=allowed_types)

    # ============================================================
    # 3. PROSES FILE
    #    - current_file_id: guard supaya blok ini cuma dieksekusi saat file
    #      BARU diupload, bukan setiap kali script Streamlit rerun (misal saat
    #      pindah menu navigasi / filter di halaman lain berubah).
    #    - _process_uploaded_file di-cache Streamlit sebagai lapis kedua: kalau
    #      file yang sama pernah diproses sebelumnya (mis. setelah reset app),
    #      hasilnya diambil dari cache tanpa hitung ulang.
    # ============================================================
    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"

        if st.session_state.get("current_file_id") != file_id:
            try:
                with st.spinner("🧹 Membersihkan data & menghitung KPI..."):
                    file_bytes = uploaded_file.getvalue()
                    df_final = _process_uploaded_file(file_bytes, uploaded_file.name)

                if df_final is not None:
                    st.session_state["df_raw"] = df_final
                    st.session_state["current_file_id"] = file_id
                    st.session_state["uploaded_file_name"] = uploaded_file.name
                else:
                    st.sidebar.error("❌ File kosong atau format tidak didukung.")

            except Exception as e:
                st.sidebar.error(f"❌ Gagal memproses file:\n{e}")

    # ============================================================
    # 4. AMBIL DATA DARI SESSION STATE & TAMPILKAN STATUS
    #    (dipakai ulang di setiap halaman TANPA proses ulang)
    # ============================================================
    df_raw = st.session_state.get("df_raw", None)

    if df_raw is not None:
        st.sidebar.success(f"✅ Data Siap: {len(df_raw):,} baris")

        if "ticket_type" in df_raw.columns:
            ticket_counts = df_raw["ticket_type"].value_counts()
            st.sidebar.markdown("**📊 Hasil Klasifikasi**")
            for ticket_type, count in ticket_counts.items():
                st.sidebar.write(f"- {ticket_type}: {count:,}")

    return menu, df_raw