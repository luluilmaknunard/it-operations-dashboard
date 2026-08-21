import pandas as pd

def transform_data_and_kpi(df: pd.DataFrame) -> pd.DataFrame:
    """Memisah category_name dan menghitung KPI (MTTR, Response Time, SLA)."""
    df_transformed = df.copy()
    
    # 1. Pemisahan Category Name (Sesuai Manual Book Hal 13-14)
    if 'category_name' in df_transformed.columns:
        split_cats = df_transformed['category_name'].astype(str).str.split(' - ', expand=True)
        for i in range(split_cats.shape[1]):
            df_transformed[f'category_split_{i+1}'] = split_cats[i]
            
    # 2. Konversi Kolom Waktu ke Datetime
    time_columns = [
        'date_created_at', 'date_start_interaction', 'date_assigned', 
        'date_pending', 'date_last_update'
    ]
    for col in time_columns:
        if col in df_transformed.columns:
            df_transformed[col] = pd.to_datetime(df_transformed[col], errors='coerce')
            
    # 3. Hitung Response Time (Menit) - (Manual Book Hal 15-16)
    if 'date_assigned' in df_transformed.columns and 'date_start_interaction' in df_transformed.columns:
        df_transformed['response_time_minutes'] = (
            (df_transformed['date_assigned'] - df_transformed['date_start_interaction']).dt.total_seconds() / 60
        )
    
    # 4. Hitung MTTR Minutes (Pending vs Non-Pending) - (Manual Book Hal 15)
    def calculate_mttr(row):
        if pd.notnull(row.get('date_pending')) and pd.notnull(row.get('date_assigned')):
            return (row['date_pending'] - row['date_assigned']).total_seconds() / 60
        elif pd.notnull(row.get('date_last_update')) and pd.notnull(row.get('date_assigned')):
            return (row['date_last_update'] - row['date_assigned']).total_seconds() / 60
        return 0

    df_transformed['mttr_minutes'] = df_transformed.apply(calculate_mttr, axis=1)
    
    # 5. Hitung SLA Status (Comply vs Breach) - (Manual Book Hal 18)
    if 'sla_second' in df_transformed.columns:
        df_transformed['sla_minute'] = df_transformed['sla_second'] / 60
        df_transformed['sla_status'] = df_transformed.apply(
            lambda row: 'Comply' if row['mttr_minutes'] <= row['sla_minute'] else 'Breach', axis=1
        )
        
    # 6. Resolution Time Grouping - (Manual Book Hal 17-18)
    if 'date_created_at' in df_transformed.columns and 'date_last_update' in df_transformed.columns:
        df_transformed['resolution_time_minutes'] = (
            (df_transformed['date_last_update'] - df_transformed['date_created_at']).dt.total_seconds() / 60
        )
        
        def group_resolution_time(minutes):
            if minutes <= 30:
                return "<= 30 Menit"
            elif minutes <= 60:
                return "31-60 Menit"
            elif minutes <= 120:
                return "61-120 Menit"
            elif minutes <= 240:
                return "121-240 Menit"
            else:
                return "> 240 Menit"

        df_transformed['resolution_time_group'] = df_transformed['resolution_time_minutes'].apply(group_resolution_time)

    return df_transformed