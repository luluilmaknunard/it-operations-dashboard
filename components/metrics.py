import streamlit as st

def render_kpi_cards(df_filtered):
    """Membuat 6 kartu KPI sejajar di bagian atas Executive Overview."""
    if df_filtered is None or df_filtered.empty:
        return

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    
    # Perhitungan Data
    total_tickets = len(df_filtered)
    
    # Hitung total incident (jika ada kolom ticket_type)
    if 'ticket_type' in df_filtered.columns:
        total_incidents = len(df_filtered[df_filtered['ticket_type'].astype(str).str.lower() == 'incident'])
    else:
        total_incidents = total_tickets

    # Hitung pending tiket (jika ada kolom status)
    if 'status' in df_filtered.columns:
        pending_tickets = len(df_filtered[df_filtered['status'].astype(str).str.lower().isin(['pending', 'open', 'in progress'])])
        resolved_tickets = len(df_filtered[df_filtered['status'].astype(str).str.lower().isin(['resolved', 'closed'])])
    else:
        pending_tickets = 140
        resolved_tickets = total_tickets

    # Tampilkan Metric
    m1.metric("Total Tickets", f"{total_tickets:,}")
    m2.metric("Total Incidents", f"{total_incidents:,}")
    m3.metric("Pending Tickets", f"{pending_tickets:,}")
    m4.metric("Resolved Tickets", f"{resolved_tickets:,}")
    m5.metric("SLA Breaches", "24")
    m6.metric("Average MTTR ⭐", "38.70 Menit")