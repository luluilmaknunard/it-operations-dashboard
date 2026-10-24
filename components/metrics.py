"""
Tujuan:
    Modul komponen untuk menghitung metrik KPI utama (seperti MTTR, Total Tiket, 
    Total Gangguan, Tiket Pending, Tiket Selesai, dan Tiket di Luar SLA), 
    merender kartu KPI (Scorecards) dengan injeksi CSS kustom, serta menyediakan 
    fungsi filter slicer berbasis anggota/teknisi.

Input:
    df (pd.DataFrame): Dataframe tiket yang masuk untuk diolah dan dirender.

Proses:
    - Melakukan pencarian nama kolom secara fleksibel menggunakan fungsi helper _find_column.
    - Menghitung rata-rata Mean Time to Repair (MTTR) berdasarkan kolom durasi.
    - Mengagregasi data untuk 6 kartu KPI utama berdasarkan kondisi *filtered dataframe*.
    - Menyuntikkan style CSS kustom untuk merapikan tampilan kontainer st.metric.
    - Menyediakan dropdown slicer (`render_member_slicer`) untuk menyaring data per teknisi.

Output:
    Komponen UI metrik dirender ke antarmuka Streamlit dan/atau mengembalikan DataFrame terfilter.
"""
import streamlit as st
import pandas as pd


# ============================================================
# HELPER
# ============================================================

def _find_column(df, candidates):
    """
    Tujuan: 
        Mengambil nama kolom pertama yang tersedia di dataframe berdasarkan 
        daftar kandidat yang diberikan (mekanisme fallback).
    """

    if df is None or df.empty:
        return None

    for col in candidates:
        if col in df.columns:
            return col

    return None


# ============================================================
# CALCULATE AVERAGE MTTR
# ============================================================

def calculate_mttr(df):
    """
    Tujuan: 
        Menghitung RATA-RATA MTTR (Mean Time to Repair) berdasarkan data yang diberikan.

    PENTING:
        Fungsi ini TIDAK melakukan filter unit.

        Filter Unit Name dilakukan oleh:
            render_top_filters()

        sehingga:

            Unit Name = All
            -> df berisi seluruh unit
            -> MTTR dihitung seluruh unit

            Unit Name = Unit tertentu
            -> df hanya berisi unit tersebut
            -> MTTR dihitung khusus unit tersebut

        MTTR per ticket harus sudah tersedia pada kolom:
            mttr_minutes

        Fungsi ini hanya melakukan:
            mean(mttr_minutes)

    Output:
        float dalam satuan menit, atau None jika data tidak tersedia.
    """

    if df is None or df.empty:
        return None

    mttr_col = _find_column(
        df,
        [
            "mttr_minutes",
            "MTTR_minutes",
            "mttr",
            "MTTR",
        ]
    )

    if mttr_col is None:
        return None

    mttr = pd.to_numeric(
        df[mttr_col],
        errors="coerce"
    )

    mttr = mttr[
        mttr.notna()
        & (mttr >= 0)
    ]

    if mttr.empty:
        return None

    return float(
        mttr.mean()
    )


# ============================================================
# KPI CARDS
# ============================================================

def render_kpi_cards(df_filtered):
    """
    Tujuan: 
        Merender 6 kartu KPI utama secara grid horizontal dengan styling CSS kustom:
        1. Total Tiket
        2. Total Gangguan
        3. Tiket Pending
        4. Tiket Selesai
        5. Tiket di Luar SLA
        6. Rata-rata MTTR

        Semua KPI mengikuti df_filtered hasil filter.
    """

    if df_filtered is None or df_filtered.empty:
        return

    
    # CSS KPI

    st.markdown(
        """
        <style>

        /* ==================================================
           KPI CONTAINER
           ================================================== */

        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e1e5ea;
            border-radius: 10px;
            padding: 10px 14px 11px 14px;
            min-height: 78px;
            box-sizing: border-box;
        }

        /* ==================================================
           LABEL KPI
           ================================================== */

        div[data-testid="stMetricLabel"] {
            font-size: 12px !important;
            font-weight: 500 !important;
            color: #555555 !important;
            margin-bottom: 3px !important;
        }

        div[data-testid="stMetricLabel"] p {
            font-size: 12px !important;
            margin: 0 !important;
        }

        /* ==================================================
           VALUE KPI
           ================================================== */

        div[data-testid="stMetricValue"] {
            font-size: 22px !important;
            font-weight: 600 !important;
            color: #222222 !important;
            line-height: 1.1 !important;
        }

        /* ==================================================
           JARAK ANTAR KOLOM
           ================================================== */

        div[data-testid="stHorizontalBlock"] {
            gap: 10px !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # ========================================================
    # IDENTIFIKASI KOLOM
    # ========================================================

    # ID TICKET

    id_col = _find_column(
        df_filtered,
        [
            "ticketId",
            "ticket_id",
            "ticketID",
            "id",
            "ticket",
        ]
    )

   
    # TICKET TYPE

    type_col = _find_column(
        df_filtered,
        [
            "ticket_type",
            "type",
            "ticketType",
            "ticket_type_name",
        ]
    )

    # STATUS TICKET

    status_col = _find_column(
        df_filtered,
        [
            "ticket_status_name",
            "ticket_status",
            "status",
            "status_name",
        ]
    )

    # SLA STATUS

    sla_col = _find_column(
        df_filtered,
        [
            "sla_status",
            "SLA_Status",
            "sla_status_name",
        ]
    )


    # 1. TOTAL TIKET

    if id_col is not None:

        total_tiket = int(
            df_filtered[id_col]
            .dropna()
            .nunique()
        )

    else:

        total_tiket = len(df_filtered)


    # 2. TOTAL GANGGUAN

    if type_col is not None:

        type_series = (
            df_filtered[type_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        mask_gangguan = type_series.str.contains(
            "gangguan|incident",
            regex=True,
            na=False,
        )

        if id_col is not None:

            total_gangguan = int(
                df_filtered.loc[
                    mask_gangguan,
                    id_col
                ]
                .dropna()
                .nunique()
            )

        else:

            total_gangguan = int(
                mask_gangguan.sum()
            )

    else:

        total_gangguan = 0


    # 3. TIKET PENDING

    if "date_pending" in df_filtered.columns:

        tiket_pending = int(
            pd.to_datetime(
                df_filtered["date_pending"],
                errors="coerce",
            )
            .notna()
            .sum()
        )

    elif "pending_status" in df_filtered.columns:

        pending_series = (
            df_filtered["pending_status"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        mask_pending = pending_series.str.contains(
            "pending",
            regex=True,
            na=False,
        )

        if id_col is not None:

            tiket_pending = int(
                df_filtered.loc[
                    mask_pending,
                    id_col
                ]
                .dropna()
                .nunique()
            )

        else:

            tiket_pending = int(
                mask_pending.sum()
            )

    elif status_col is not None:

        status_series = (
            df_filtered[status_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        mask_pending = status_series.str.contains(
            "pending|waiting",
            regex=True,
            na=False,
        )

        if id_col is not None:

            tiket_pending = int(
                df_filtered.loc[
                    mask_pending,
                    id_col
                ]
                .dropna()
                .nunique()
            )

        else:

            tiket_pending = int(
                mask_pending.sum()
            )

    else:

        tiket_pending = 0


    # 4. TIKET SELESAI

    if status_col is not None:

        status_series = (
            df_filtered[status_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        mask_resolved = status_series.str.contains(
            "resolve|resolved|closed|finish|finished",
            regex=True,
            na=False,
        )

        if id_col is not None:

            tiket_selesai = int(
                df_filtered.loc[
                    mask_resolved,
                    id_col
                ]
                .dropna()
                .nunique()
            )

        else:

            tiket_selesai = int(
                mask_resolved.sum()
            )

    else:

        tiket_selesai = 0


    # 5. TIKET DI LUAR SLA

    if sla_col is not None:

        sla_series = (
            df_filtered[sla_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        mask_breach = sla_series.str.contains(
            "breach|outside|violated",
            regex=True,
            na=False,
        )

        if id_col is not None:

            tiket_luar_sla = int(
                df_filtered.loc[
                    mask_breach,
                    id_col
                ]
                .dropna()
                .nunique()
            )

        else:

            tiket_luar_sla = int(
                mask_breach.sum()
            )

    else:

        tiket_luar_sla = 0


    # 6. RATA-RATA MTTR

    avg_mttr = calculate_mttr(
        df_filtered
    )

    if avg_mttr is not None:

        mttr_display = (
            f"{avg_mttr:,.2f} Menit"
        )

    else:

        mttr_display = "N/A"

    # ========================================================
    # RENDER KPI
    # ========================================================

    m1, m2, m3, m4, m5, m6 = st.columns(
        6,
        gap="small",
    )

    # --------------------------------------------------------
    # TOTAL TIKET
    # --------------------------------------------------------

    with m1:

        st.metric(
            label="Total Tiket",
            value=f"{total_tiket:,}",
        )

    # --------------------------------------------------------
    # TOTAL GANGGUAN
    # --------------------------------------------------------

    with m2:

        st.metric(
            label="Total Gangguan",
            value=f"{total_gangguan:,}",
        )

    # --------------------------------------------------------
    # TIKET PENDING
    # --------------------------------------------------------

    with m3:

        st.metric(
            label="Tiket Pending",
            value=f"{tiket_pending:,}",
        )

    # --------------------------------------------------------
    # TIKET SELESAI
    # --------------------------------------------------------

    with m4:

        st.metric(
            label="Tiket Selesai",
            value=f"{tiket_selesai:,}",
        )

    # --------------------------------------------------------
    # DI LUAR SLA
    # --------------------------------------------------------

    with m5:

        st.metric(
            label="Tiket di Luar SLA",
            value=f"{tiket_luar_sla:,}",
        )

    # --------------------------------------------------------
    # MTTR
    # --------------------------------------------------------

    with m6:

        st.metric(
            label="Rata-rata MTTR",
            value=mttr_display,
        )

# ============================================================
# MEMBER SLICER
# ============================================================

def render_member_slicer(
    df,
    key="member_slicer"
):
    """
    Tujuan: 
        Merender komponen pilihan slicer anggota/teknisi.
        Pilihan anggota disaring secara otomatis mengikuti data yang 
        sudah difilter sebelumnya.
    """

    if df is None or df.empty:
        return df


    member_col = _find_column(
        df,
        [
            "member",
            "member_name",
            "nama_member",
            "nama anggota",
            "anggota",
            "technician",
            "technician_name",
            "nama teknisi",
            "teknisi",
            "assignee",
            "assigned_to",
            "assigned_name",
            "pic",
            "pic_name",
        ]
    )

    # ========================================================
    # KOLOM TIDAK DITEMUKAN
    # ========================================================

    if member_col is None:

        st.warning(
            "Kolom anggota/teknisi tidak ditemukan."
        )

        return df

    # ========================================================
    # DAFTAR ANGGOTA
    # ========================================================

    member_series = (
        df[member_col]
        .dropna()
        .astype(str)
        .str.strip()
    )

    member_list = sorted(
        [
            x
            for x in member_series.unique().tolist()
            if x
            and x.lower() not in [
                "nan",
                "none",
                "null",
                "-"
            ]
        ]
    )

    member_options = [
        "All"
    ] + member_list

    # ========================================================
    # VALIDASI SESSION STATE
    # ========================================================

    if key in st.session_state:

        if st.session_state[key] not in member_options:

            st.session_state[key] = "All"

    # ========================================================
    # SELECTBOX
    # ========================================================

    selected_member = st.selectbox(
        "Anggota",
        member_options,
        key=key
    )

    # ========================================================
    # APPLY FILTER
    # ========================================================

    if selected_member != "All":

        df = df[
            df[member_col]
            .astype(str)
            .str.strip()
            .eq(selected_member)
        ].copy()

    return df

