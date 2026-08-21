import pandas as pd
import numpy as np

def transform_data_and_kpi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Melakukan transformasi data, pemisahan kategori bertingkat, 
    serta perhitungan KPI (MTTR Pending/Non-Pending, Response Time, SLA, Resolution Group, Network Component, dan Ticket Type).
    """
    if df is None or df.empty:
        return df

    df_transformed = df.copy()

    # =========================================================================
    # 1. Pemisahan Category Name Bertingkat (Sesuai Manual Book & Poin 1)
    #    Mendukung delimiter ' - ' maupun ' > '
    # =========================================================================
    if 'category_name' in df_transformed.columns:
        # Menangani pemisah ' - ' atau ' > ' atau '/'
        split_cats = df_transformed['category_name'].astype(str).str.split(r'\s*(?:-|\||>)\s*', expand=True)
        for i in range(split_cats.shape[1]):
            col_name = f'category_split_{i+1}'
            df_transformed[col_name] = split_cats[i].str.strip()
            # Ganti teks 'nan' atau 'None' dengan None murni
            df_transformed[col_name] = df_transformed[col_name].replace(['nan', 'None', '', 'null'], None)

    # =========================================================================
    # 2. Konversi Kolom Waktu ke Datetime
    # =========================================================================
    time_columns = [
        'date_created_at', 'date_start_interaction', 'date_assigned', 
        'date_pending', 'date_last_update'
    ]
    for col in time_columns:
        if col in df_transformed.columns:
            df_transformed[col] = pd.to_datetime(df_transformed[col], errors='coerce')

    # =========================================================================
    # 3. Hitung MTTR Pending & MTTR Non-Pending (Poin 3)
    #    - MTTR Pending     : date_last_update - date_pending
    #    - MTTR Non-Pending : date_last_update - date_assigned
    #    - Pending Status   : 'Pending' jika date_pending terisi, else 'Non-Pending'
    # =========================================================================
    # MTTR Pending (menit)
    if 'date_last_update' in df_transformed.columns and 'date_pending' in df_transformed.columns:
        df_transformed['mttr_pending_minutes'] = (
            (df_transformed['date_last_update'] - df_transformed['date_pending']).dt.total_seconds() / 60
        ).clip(lower=0)
    else:
        df_transformed['mttr_pending_minutes'] = 0.0

    # MTTR Non-Pending (menit)
    if 'date_last_update' in df_transformed.columns and 'date_assigned' in df_transformed.columns:
        df_transformed['mttr_non_pending_minutes'] = (
            (df_transformed['date_last_update'] - df_transformed['date_assigned']).dt.total_seconds() / 60
        ).clip(lower=0)
    else:
        df_transformed['mttr_non_pending_minutes'] = 0.0

    # Total MTTR Minutes untuk perhitungan SLA (Kombinasi Pending / Non-Pending)
    def calculate_mttr(row):
        if pd.notnull(row.get('date_pending')) and pd.notnull(row.get('date_assigned')):
            val = (row['date_pending'] - row['date_assigned']).total_seconds() / 60
            return max(val, 0)
        elif pd.notnull(row.get('date_last_update')) and pd.notnull(row.get('date_assigned')):
            val = (row['date_last_update'] - row['date_assigned']).total_seconds() / 60
            return max(val, 0)
        return 0.0

    df_transformed['mttr_minutes'] = df_transformed.apply(calculate_mttr, axis=1)

    # Pending Status Flag
    if 'date_pending' in df_transformed.columns:
        df_transformed['pending_status'] = np.where(
            df_transformed['date_pending'].notna(), 'Pending', 'Non-Pending'
        )
    else:
        df_transformed['pending_status'] = 'Non-Pending'

    # =========================================================================
    # 4. Hitung Response Time (Menit) - (Poin 4)
    #    Response Time = date_assigned - date_start_interaction
    # =========================================================================
    if 'date_assigned' in df_transformed.columns and 'date_start_interaction' in df_transformed.columns:
        df_transformed['response_time_minutes'] = (
            (df_transformed['date_assigned'] - df_transformed['date_start_interaction']).dt.total_seconds() / 60
        ).clip(lower=0)
    else:
        df_transformed['response_time_minutes'] = 0.0

    # =========================================================================
    # 5. Hitung SLA Status (Comply vs Breach)
    # =========================================================================
    if 'sla_second' in df_transformed.columns:
        df_transformed['sla_minute'] = df_transformed['sla_second'] / 60
        df_transformed['sla_status'] = df_transformed.apply(
            lambda row: 'Comply' if row['mttr_minutes'] <= row.get('sla_minute', 0) else 'Breach', 
            axis=1
        )

    # =========================================================================
    # 6. Resolution Time Grouping (Poin 5)
    #    Resolution Time = date_last_update - date_created_at
    # =========================================================================
    if 'date_created_at' in df_transformed.columns and 'date_last_update' in df_transformed.columns:
        df_transformed['resolution_time_minutes'] = (
            (df_transformed['date_last_update'] - df_transformed['date_created_at']).dt.total_seconds() / 60
        ).clip(lower=0)
        
        def group_resolution_time(minutes):
            if pd.isna(minutes):
                return "> 240 Menit"
            elif minutes <= 30:
                return "≤ 30 Menit"
            elif minutes <= 60:
                return "31 - 60 Menit"
            elif minutes <= 120:
                return "61 - 120 Menit"
            elif minutes <= 240:
                return "121 - 240 Menit"
            else:
                return "> 240 Menit"

        df_transformed['resolution_time_group'] = df_transformed['resolution_time_minutes'].apply(group_resolution_time)

    # =========================================================================
    # 7. Pengelompokan Network Component Rule-Based (Poin 6 DAX Switch)
    # =========================================================================
    df_transformed['network_component'] = classify_network_component(df_transformed)

    # =========================================================================
    # 8. Pengelompokan Ticket Type (Poin 2 - Gangguan vs Request)
    # =========================================================================
    df_transformed['ticket_type'] = classify_ticket_type_initial(df_transformed)

    return df_transformed


def classify_network_component(df: pd.DataFrame) -> pd.Series:
    """Mengonversi logika DAX PowerBI SWITCH(TRUE()) ke Pandas Vectorized String Search."""
    cols = ['ticket_symptom', 'ticket_summary', 'remark', 'ticket_rootcouse']
    text_data = pd.Series("", index=df.index)

    for col in cols:
        if col in df.columns:
            text_data += " " + df[col].fillna("").astype(str)

    text_data = text_data.str.lower()

    # Define Pattern Rules sesuai SWITCH DAX
    lan_pattern = r'kabel lan|lan|koneksi lan|network pc|network pada pc|port switch|switch|port|patch|rj45|not connected|unplugged|ping|rto|intermitten'
    internet_pattern = r'internet|koneksi internet|internet down|internet tidak stabil|indihome|astinet|backup koneksi|backup connection'
    vpn_pattern = r'vpn|forticlient|pritunel|pritunl'
    ip_pattern = r'ip address|public ip|allow akses ip|allow access|ip public'
    dns_pattern = r'\bdns\b'
    router_pattern = r'mikrotik|router|gateway'
    web_pattern = r'browser|chrome|website|\bweb\b|url|host'
    server_pattern = r'ftp|server|cms|rabbit'

    conditions = [
        text_data.str.contains(lan_pattern, regex=True),
        text_data.str.contains(internet_pattern, regex=True),
        text_data.str.contains(vpn_pattern, regex=True),
        text_data.str.contains(ip_pattern, regex=True),
        text_data.str.contains(dns_pattern, regex=True),
        text_data.str.contains(router_pattern, regex=True),
        text_data.str.contains(web_pattern, regex=True),
        text_data.str.contains(server_pattern, regex=True)
    ]

    choices = [
        "LAN Infrastructure",
        "Internet",
        "VPN",
        "IP Address",
        "DNS",
        "Router / Mikrotik",
        "Website Access",
        "Server / Network Service"
    ]

    return pd.Series(np.select(conditions, choices, default="Network Lainnya"), index=df.index)


def classify_ticket_type_initial(df: pd.DataFrame) -> pd.Series:
    """Klasifikasi awal Gangguan vs Request berbasis kata kunci freetext."""
    cols = ['ticket_rootcouse', 'remark', 'ticket_summary', 'ticket_symptom']
    text_data = pd.Series("", index=df.index)

    for col in cols:
        if col in df.columns:
            text_data += " " + df[col].fillna("").astype(str)

    text_data = text_data.str.lower()

    # Pattern untuk permintaan/request
    req_pattern = r'permintaan|request|rekording|recording|penarikan data|tarik data|minta data|pembukaan|create|pembuatan|akses|permission|minta'
    
    is_request = text_data.str.contains(req_pattern, regex=True)
    return pd.Series(np.where(is_request, 'Request', 'Gangguan'), index=df.index)