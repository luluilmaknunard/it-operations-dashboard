import streamlit as st
import pandas as pd


# ============================================================
# CALCULATE AVERAGE MTTR
# ============================================================

def calculate_mttr(df):
    """
    Mengambil RATA-RATA MTTR dari kolom mttr_minutes.

    Perhitungan MTTR per ticket dilakukan di:
        transform_data_and_kpi()

    Rumus di transformation:

    Non-Pending:
        date_last_update - date_assigned

    Pending:
        (date_last_update - date_assigned)
        - (date_last_update - date_pending)

    Di metrics.py:
        Average MTTR = mean(mttr_minutes)

    Output:
        rata-rata MTTR dalam menit
    """

    if df is None or df.empty:
        return None

    # --------------------------------------------------------
    # Pastikan kolom MTTR hasil transformation tersedia
    # --------------------------------------------------------

    if "mttr_minutes" not in df.columns:
        return None

    # --------------------------------------------------------
    # Ambil MTTR per ticket
    # --------------------------------------------------------

    mttr = pd.to_numeric(
        df["mttr_minutes"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Buang nilai invalid
    # --------------------------------------------------------

    mttr = mttr[
        mttr.notna()
        & (mttr >= 0)
    ]

    if mttr.empty:
        return None

    # --------------------------------------------------------
    # RATA-RATA MTTR
    #
    # MTTR sudah dihitung satu per satu per ticket.
    # Di sini hanya dirata-ratakan.
    # --------------------------------------------------------

    return float(mttr.mean())


# ============================================================
# KPI CARDS
# ============================================================

def render_kpi_cards(df_filtered):
    """
    Render 6 KPI utama:

    1. Total Tiket
    2. Total Gangguan
    3. Tiket Pending
    4. Tiket Selesai
    5. Tiket di Luar SLA
    6. Rata-rata MTTR

    MTTR menggunakan kolom mttr_minutes
    yang sudah dihitung pada tahap transformation.
    """

    if df_filtered is None or df_filtered.empty:
        return

    # ========================================================
    # IDENTIFIKASI KOLOM
    # ========================================================

    # --------------------------------------------------------
    # ID Ticket
    # --------------------------------------------------------

    id_col = (
        "ticketId"
        if "ticketId" in df_filtered.columns
        else (
            "ticket_id"
            if "ticket_id" in df_filtered.columns
            else None
        )
    )

    # --------------------------------------------------------
    # Ticket Type
    # --------------------------------------------------------

    type_col = (
        "ticket_type"
        if "ticket_type" in df_filtered.columns
        else (
            "type"
            if "type" in df_filtered.columns
            else None
        )
    )

    # --------------------------------------------------------
    # Status Ticket
    # --------------------------------------------------------

    status_col = (
        "ticket_status_name"
        if "ticket_status_name" in df_filtered.columns
        else (
            "ticket_status"
            if "ticket_status" in df_filtered.columns
            else (
                "status"
                if "status" in df_filtered.columns
                else None
            )
        )
    )

    # --------------------------------------------------------
    # SLA Status
    # --------------------------------------------------------

    sla_col = (
        "sla_status"
        if "sla_status" in df_filtered.columns
        else (
            "SLA_Status"
            if "SLA_Status" in df_filtered.columns
            else (
                "sla_status_name"
                if "sla_status_name" in df_filtered.columns
                else None
            )
        )
    )

    # ========================================================
    # 1. TOTAL TIKET
    # ========================================================

    if id_col:
        total_tiket = int(
            df_filtered[id_col].nunique()
        )
    else:
        total_tiket = len(df_filtered)

    # ========================================================
    # 2. TOTAL GANGGUAN
    # ========================================================

    if type_col:

        total_gangguan = int(
            df_filtered[type_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains(
                "gangguan|incident",
                na=False
            )
            .sum()
        )

    else:

        total_gangguan = 0

    # ========================================================
    # 3. TIKET PENDING
    # ========================================================

    if "date_pending" in df_filtered.columns:

        tiket_pending = int(
            df_filtered["date_pending"]
            .notna()
            .sum()
        )

    elif "pending_status" in df_filtered.columns:

        tiket_pending = int(
            df_filtered["pending_status"]
            .astype(str)
            .str.strip()
            .str.lower()
            .eq("pending")
            .sum()
        )

    elif status_col:

        tiket_pending = int(
            df_filtered[status_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .str.contains(
                "pending|open|waiting",
                na=False
            )
            .sum()
        )

    else:

        tiket_pending = 0

    # ========================================================
    # 4. TIKET SELESAI
    # ========================================================

    if status_col:

        status_series = (
            df_filtered[status_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        mask_resolved = status_series.str.contains(
            "resolve|resolved|closed|finish|finished",
            na=False
        )

        if id_col:

            tiket_selesai = int(
                df_filtered.loc[
                    mask_resolved,
                    id_col
                ].nunique()
            )

        else:

            tiket_selesai = int(
                mask_resolved.sum()
            )

    else:

        tiket_selesai = 0

    # ========================================================
    # 5. TIKET DI LUAR SLA
    # ========================================================

    if sla_col:

        sla_series = (
            df_filtered[sla_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        mask_breach = sla_series.eq("breach")

        if id_col:

            tiket_luar_sla = int(
                df_filtered.loc[
                    mask_breach,
                    id_col
                ].nunique()
            )

        else:

            tiket_luar_sla = int(
                mask_breach.sum()
            )

    else:

        tiket_luar_sla = 0

    # ========================================================
    # 6. RATA-RATA MTTR
    #
    # Tidak menghitung ulang dari tanggal.
    #
    # mttr_minutes sudah dihitung PER TICKET
    # pada transform_data_and_kpi().
    # ========================================================

    if "mttr_minutes" in df_filtered.columns:

        mttr_series = pd.to_numeric(
            df_filtered["mttr_minutes"],
            errors="coerce"
        )

        mttr_series = mttr_series[
            mttr_series.notna()
            & (mttr_series >= 0)
        ]

        avg_mttr = (
            float(mttr_series.mean())
            if not mttr_series.empty
            else None
        )

    else:
        avg_mttr = None

    # ========================================================
    # DISPLAY KPI
    # ========================================================

    m1, m2, m3, m4, m5, m6 = st.columns(6)

    m1.metric(
        "Total Tiket",
        f"{total_tiket:,}"
    )

    m2.metric(
        "Total Gangguan",
        f"{total_gangguan:,}"
    )

    m3.metric(
        "Tiket Pending",
        f"{tiket_pending:,}"
    )

    m4.metric(
        "Tiket Selesai",
        f"{tiket_selesai:,}"
    )

    m5.metric(
        "Tiket di Luar SLA",
        f"{tiket_luar_sla:,}"
    )

    m6.metric(
        "Rata-rata MTTR",
        (
            f"{avg_mttr:,.2f} Menit"
            if avg_mttr is not None
            else "N/A"
        )
    )


# ============================================================
# MEMBER SLICER
# ============================================================

def render_member_slicer(
    df,
    key="member_slicer"
):
    """
    Slicer anggota/teknisi.

    Pilihan anggota mengikuti data yang
    sudah difilter sebelumnya.
    """

    if df is None or df.empty:
        return df

    # --------------------------------------------------------
    # Cari kolom anggota
    # --------------------------------------------------------

    member_col = None

    possible_columns = [
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

    for col in df.columns:

        col_clean = (
            str(col)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        if col_clean in possible_columns:

            member_col = col
            break

    # --------------------------------------------------------
    # Kolom anggota tidak ditemukan
    # --------------------------------------------------------

    if member_col is None:

        st.warning(
            "Kolom anggota/teknisi tidak ditemukan."
        )

        return df

    # --------------------------------------------------------
    # Daftar anggota
    # --------------------------------------------------------

    member_list = (
        df[member_col]
        .dropna()
        .astype(str)
        .str.strip()
    )

    member_list = sorted(
        [
            x
            for x in member_list.unique().tolist()
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

    # --------------------------------------------------------
    # Pastikan session state valid
    # --------------------------------------------------------

    if key in st.session_state:

        if st.session_state[key] not in member_options:

            st.session_state[key] = "All"

    # --------------------------------------------------------
    # Render slicer
    # --------------------------------------------------------

    selected_member = st.selectbox(
        "Anggota",
        member_options,
        key=key
    )

    # --------------------------------------------------------
    # Apply filter
    # --------------------------------------------------------

    if selected_member != "All":

        df = df[
            df[member_col]
            .astype(str)
            .str.strip()
            == selected_member
        ].copy()

    return df