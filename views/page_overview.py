import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render(df_filtered):
    if df_filtered is None or df_filtered.empty:
        st.warning("Data tidak tersedia untuk ditampilkan.")
        return

    st.markdown("## **📊 Executive Overview**")

    # ============================================================
    # 1. SIX SCORECARDS METRICS
    # ============================================================
    # A. Total Tiket
    id_col = 'ticketId' if 'ticketId' in df_filtered.columns else ('ticket_id' if 'ticket_id' in df_filtered.columns else df_filtered.columns[0])
    total_tiket = df_filtered[id_col].nunique()

    # B. Total Gangguan
    type_col = 'ticket_type' if 'ticket_type' in df_filtered.columns else 'type'
    if type_col in df_filtered.columns:
        df_gangguan = df_filtered[df_filtered[type_col].astype(str).str.contains('gangguan|incident', case=False, na=False)]
        total_gangguan = len(df_gangguan)
    else:
        total_gangguan = 0

    # C. Tiket Pending (dilihat dari date_pending yang tidak kosong)
    pending_col = 'date_pending' if 'date_pending' in df_filtered.columns else 'Pending'
    if pending_col in df_filtered.columns:
        tiket_pending = df_filtered[pending_col].notna().sum()
    else:
        status_col = 'ticket_status_name' if 'ticket_status_name' in df_filtered.columns else 'status'
        tiket_pending = df_filtered[status_col].astype(str).str.contains('pending', case=False, na=False).sum() if status_col in df_filtered.columns else 0

    # D. Tiket Selesai (resolved / closed)
    status_col = 'ticket_status_name' if 'ticket_status_name' in df_filtered.columns else 'status'
    if status_col in df_filtered.columns:
        tiket_selesai = df_filtered[df_filtered[status_col].astype(str).str.contains('resolve|closed|finish', case=False, na=False)][id_col].nunique()
    else:
        tiket_selesai = 0

    # E. Tiket di Luar SLA
    sla_col = 'sla_status' if 'sla_status' in df_filtered.columns else 'sla_status_name'
    if sla_col in df_filtered.columns:
        tiket_luar_sla = df_filtered[df_filtered[sla_col].astype(str).str.contains('breach|over', case=False, na=False)][id_col].nunique()
    else:
        tiket_luar_sla = 0

    # F. Rata-Rata MTTR
    mttr_col = 'mttr_minutes' if 'mttr_minutes' in df_filtered.columns else ('MTTR' if 'MTTR' in df_filtered.columns else 'mttr_no_pending')
    avg_mttr = df_filtered[mttr_col].mean() if mttr_col in df_filtered.columns else 0

    # Display 6 Metric Cards
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Tiket", f"{total_tiket:,}")
    m2.metric("Total Gangguan", f"{total_gangguan:,}")
    m3.metric("Tiket Pending", f"{tiket_pending:,}")
    m4.metric("Tiket Selesai", f"{tiket_selesai:,}")
    m5.metric("Tiket di Luar SLA", f"{tiket_luar_sla:,}")
    m6.metric("Rata-rata MTTR ⭐", f"{avg_mttr:.2f} Menit")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # BARIS 2: VISUALISASI TENGAH (4 CHART)
    # ============================================================
    c1, c2, c3, c4 = st.columns([1, 1.3, 1.2, 1])

    # ------------------------------------------------------------
    # 2. Donut Chart: Distribusi Jenis Tiket
    # ------------------------------------------------------------
    with c1:
        st.markdown("##### **Distribusi Jenis Tiket**")
        if type_col in df_filtered.columns:
            df_dist = df_filtered[type_col].value_counts().reset_index()
            df_dist.columns = ['Jenis', 'Jumlah']
            fig_donut = px.pie(
                df_dist, values='Jumlah', names='Jenis', hole=0.6,
                color_discrete_sequence=['#F28E2B', '#4E79A7']
            )
            fig_donut.update_traces(textinfo='percent+label', showlegend=False)
            fig_donut.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=230)
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Kolom ticket_type tidak ditemukan")

    # ------------------------------------------------------------
    # 3. Line Chart: Tren Jumlah Tiket Harian
    # ------------------------------------------------------------
    with c2:
        st.markdown("##### **Tren Jumlah Tiket Harian**")
        date_col = 'date_created_at' if 'date_created_at' in df_filtered.columns else 'created_at'
        if date_col in df_filtered.columns and type_col in df_filtered.columns:
            df_trend = df_filtered.copy()
            df_trend['Tanggal'] = pd.to_datetime(df_trend[date_col]).dt.date
            
            # Grouping Harian
            daily_total = df_trend.groupby('Tanggal').size().rename('Total Ticket')
            daily_gangguan = df_trend[df_trend[type_col].astype(str).str.contains('gangguan|incident', case=False, na=False)].groupby('Tanggal').size().rename('Gangguan')
            daily_request = df_trend[df_trend[type_col].astype(str).str.contains('request|permintaan', case=False, na=False)].groupby('Tanggal').size().rename('Request')
            
            df_daily_all = pd.concat([daily_total, daily_gangguan, daily_request], axis=1).fillna(0).reset_index()
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=df_daily_all['Tanggal'], y=df_daily_all['Total Ticket'], name='Total Ticket', line=dict(color='#D32F2F', width=2)))
            fig_trend.add_trace(go.Scatter(x=df_daily_all['Tanggal'], y=df_daily_all['Gangguan'], name='Gangguan', line=dict(color='#F28E2B', width=2)))
            fig_trend.add_trace(go.Scatter(x=df_daily_all['Tanggal'], y=df_daily_all['Request'], name='Request', line=dict(color='#4E79A7', width=2)))
            
            fig_trend.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=230,
                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
                xaxis_title=None, yaxis_title="Jumlah"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Data tanggal/tipe tidak lengkap")

    # ------------------------------------------------------------
    # 4. Bar Chart: Jumlah Gangguan per Kategori (Category Split 4)
    # ------------------------------------------------------------
    with c3:
        st.markdown("##### **Jumlah Gangguan per Kategori**")
        cat4_col = 'category_split_4' if 'category_split_4' in df_filtered.columns else ('detailSubCategory2' if 'detailSubCategory2' in df_filtered.columns else 'category_name')
        if cat4_col in df_filtered.columns:
            df_cat4 = df_filtered[cat4_col].dropna().value_counts().head(5).reset_index()
            df_cat4.columns = ['Kategori', 'Jumlah']
            df_cat4 = df_cat4.sort_values(by='Jumlah', ascending=True)
            
            fig_cat4 = px.bar(df_cat4, x='Jumlah', y='Kategori', orientation='h', text='Jumlah')
            fig_cat4.update_traces(marker_color='#D32F2F', textposition='outside')
            fig_cat4.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=230, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_cat4, use_container_width=True)
        else:
            st.info("Kolom category_split_4 tidak ditemukan")

    # ------------------------------------------------------------
    # 5. Pie Chart: Distribusi Tingkat Dampak
    # ------------------------------------------------------------
    with c4:
        st.markdown("##### **Distribusi Tingkat Dampak**")
        impact_col = 'impact_name' if 'impact_name' in df_filtered.columns else ('impact' if 'impact' in df_filtered.columns else 'impact_level')
        if impact_col in df_filtered.columns:
            df_impact = df_filtered[impact_col].value_counts().reset_index()
            df_impact.columns = ['Dampak', 'Jumlah']
            fig_impact = px.pie(
                df_impact, values='Jumlah', names='Dampak',
                color_discrete_sequence=['#2CA02C', '#FFBB78', '#D62728', '#9467BD']
            )
            fig_impact.update_traces(textinfo='percent+label', showlegend=False)
            fig_impact.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=230)
            st.plotly_chart(fig_impact, use_container_width=True)
        else:
            st.info("Kolom impact tidak ditemukan")

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # BARIS 3: DECOMPOSITION TREE & TREEMAP
    # ============================================================
    d1, d2 = st.columns([1.2, 1.8])

    # ------------------------------------------------------------
    # 6. Departemen dengan Gangguan Terbanyak (Decomposition Tree / Horizontal Bar)
    # ------------------------------------------------------------
    with d1:
        st.markdown("##### **Departemen dengan Gangguan Terbanyak**")
        dept_col = 'department_name' if 'department_name' in df_filtered.columns else ('departement' if 'departement' in df_filtered.columns else 'nama_dept')
        
        sort_order = st.radio("Urutan Data:", ["Terbanyak", "Tersedikit"], horizontal=True, key="exec_dept_sort")
        
        if dept_col in df_filtered.columns:
            df_dept = df_filtered.groupby(dept_col)[id_col].nunique().reset_index()
            df_dept.columns = ['Departemen', 'Jumlah Kasus']
            
            is_ascending = True if sort_order == "Tersedikit" else False
            df_dept = df_dept.sort_values(by='Jumlah Kasus', ascending=is_ascending).head(7)
            
            # Mengurutkan ulang untuk Plotly bar horizontal
            df_dept_plot = df_dept.sort_values(by='Jumlah Kasus', ascending=not is_ascending)

            fig_dept = px.bar(df_dept_plot, x='Jumlah Kasus', y='Departemen', orientation='h', text='Jumlah Kasus')
            fig_dept.update_traces(marker_color='#6B1D2F', textposition='outside')
            fig_dept.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=280, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("Kolom departemen tidak ditemukan")

    # ------------------------------------------------------------
    # 7. Treemap: Layanan dengan Laporan Gangguan Terbanyak
    # ------------------------------------------------------------
    with d2:
        st.markdown("##### **Layanan dengan Laporan Gangguan Terbanyak**")
        service_col = 'service_name' if 'service_name' in df_filtered.columns else ('service' if 'service' in df_filtered.columns else 'nama_layanan')
        
        if service_col in df_filtered.columns:
            df_service = df_filtered.groupby(service_col)[id_col].nunique().reset_index()
            df_service.columns = ['Layanan', 'Jumlah Kasus']
            df_service = df_service[df_service['Jumlah Kasus'] > 0]

            fig_tree = px.treemap(
                df_service,
                path=['Layanan'],
                values='Jumlah Kasus',
                color_discrete_sequence=['#A61C1C', '#D32F2F', '#E53935', '#EF5350']
            )
            fig_tree.update_traces(root_color="lightgrey")
            fig_tree.update_layout(margin=dict(l=5, r=5, t=10, b=10), height=280)
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("Kolom service_name tidak ditemukan")