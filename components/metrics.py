import streamlit as st


def render_kpi_cards(df_filtered):
    """Membuat 6 kartu KPI sejajar, dihitung dari data asli (tidak ada angka hardcoded)."""
    if df_filtered is None or df_filtered.empty:
        return

    m1, m2, m3, m4, m5, m6 = st.columns(6)

    total_tickets = len(df_filtered)

    # Total Incidents -> hitung tiket dengan ticket_type == 'Gangguan'
    if "ticket_type" in df_filtered.columns:
        tt = df_filtered["ticket_type"].astype(str).str.strip().str.lower()
        total_incidents = int((tt == "gangguan").sum())
    else:
        total_incidents = total_tickets

    # Pending Tickets -> pakai pending_status hasil transform_data_and_kpi,
    # fallback ke ticket_status_name kalau pending_status belum ada
    if "pending_status" in df_filtered.columns:
        pending_tickets = int((df_filtered["pending_status"] == "Pending").sum())
    elif "ticket_status_name" in df_filtered.columns:
        pending_tickets = int(
            df_filtered["ticket_status_name"]
            .astype(str).str.lower()
            .str.contains("pending|open|waiting", na=False)
            .sum()
        )
    else:
        pending_tickets = 0

    resolved_tickets = max(total_tickets - pending_tickets, 0)

    # SLA Breaches -> dari kolom sla_status ('Breach' vs 'Comply')
    if "sla_status" in df_filtered.columns and (df_filtered["sla_status"] != "UNDETERMINED").any():
        sla_breaches = int((df_filtered["sla_status"] == "Breach").sum())
        sla_display = f"{sla_breaches:,}"
    else:
        sla_display = "N/A"

    # Average MTTR -> rata-rata mttr_minutes
    if "mttr_minutes" in df_filtered.columns and df_filtered["mttr_minutes"].notna().any():
        avg_mttr = df_filtered["mttr_minutes"].mean()
        mttr_display = f"{avg_mttr:.2f} Menit"
    else:
        mttr_display = "N/A"

    m1.metric("Total Tickets", f"{total_tickets:,}")
    m2.metric("Total Incidents", f"{total_incidents:,}")
    m3.metric("Pending Tickets", f"{pending_tickets:,}")
    m4.metric("Resolved Tickets", f"{resolved_tickets:,}")
    m5.metric("SLA Breaches", sla_display)
    m6.metric("Average MTTR", mttr_display)